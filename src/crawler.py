"""
Tor Crawlerin ydinlogiikka
"""

import asyncio
from collections import deque
from datetime import datetime
from typing import Set, Dict, Any, Optional
from urllib.parse import urlparse
import logging

from .config import Config
from .tor_client import TorClient
from .parser import HTMLParser
from .storage.base import BaseStorage
from .storage import JSONStorage, SQLiteStorage
from .utils import extract_domain, setup_logger


class TorCrawler:
    """
    Pääcrawler-luokka, joka toteuttaa BFS-pohjaisen crawlauksen
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logger("TorCrawler", config.log_level)

        # Komponentit
        self.tor_client: Optional[TorClient] = None
        self.parser = HTMLParser(logger=self.logger)
        self.storage: Optional[BaseStorage] = None

        # Crawlauksen tila
        self.visited_urls: Set[str] = set()
        self.queue: deque = deque()
        self.domain_counters: Dict[str, int] = {}  # Domain -> sivumäärä
        self.total_crawled = 0
        self.start_domain: Optional[str] = None

    async def initialize(self):
        """Alustaa crawlerin komponentit"""
        self.logger.info("=" * 80)
        self.logger.info("TOR CRAWLER - Alustus")
        self.logger.info("=" * 80)

        # Alusta Tor-yhteys
        self.tor_client = TorClient(self.config.tor, logger=self.logger)
        await self.tor_client.initialize()

        # Alusta tallennus
        if self.config.storage.storage_type == "json":
            self.storage = JSONStorage(
                self.config.storage.output_dir,
                self.config.storage.json_filename,
                logger=self.logger
            )
        elif self.config.storage.storage_type == "sqlite":
            self.storage = SQLiteStorage(
                self.config.storage.output_dir,
                self.config.storage.sqlite_filename,
                logger=self.logger
            )
        else:
            raise ValueError(f"Tuntematon storage_type: {self.config.storage.storage_type}")

        await self.storage.initialize()

        # Lataa aiemmin käydyt URL:t
        self.visited_urls = await self.storage.get_visited_urls()

        # Lisää aloitus-URL jonoon
        self.start_domain = extract_domain(self.config.crawler.start_url)
        self.queue.append((self.config.crawler.start_url, 0))  # (url, depth)

        self.logger.info(f"✓ Crawleri alustettu")
        self.logger.info(f"  Aloitus-URL: {self.config.crawler.start_url}")
        self.logger.info(f"  Maksimisyvyys: {self.config.crawler.max_depth}")
        self.logger.info(f"  Maksimisivuja: {self.config.crawler.max_pages}")
        self.logger.info(f"  Tallennus: {self.config.storage.storage_type}")
        self.logger.info(f"  Aiemmin käytyjä: {len(self.visited_urls)}")
        self.logger.info("=" * 80)

    async def crawl(self):
        """Pääcrawlaus-silmukka (BFS)"""
        try:
            while self.queue and self.total_crawled < self.config.crawler.max_pages:
                # Ota seuraava URL jonosta
                url, depth = self.queue.popleft()

                # Tarkista onko jo käyty
                if url in self.visited_urls:
                    continue

                # Tarkista syvyys
                if depth > self.config.crawler.max_depth:
                    continue

                # Tarkista domain-rajat
                domain = extract_domain(url)
                if domain:
                    if self.domain_counters.get(domain, 0) >= self.config.crawler.max_pages_per_domain:
                        self.logger.debug(f"Domain-raja saavutettu: {domain}")
                        continue

                # Crawl sivu
                await self._crawl_page(url, depth)

                # Rate limiting
                if self.config.crawler.request_delay > 0:
                    await asyncio.sleep(self.config.crawler.request_delay)

                # Tilastot
                if self.total_crawled % 10 == 0:
                    await self._log_progress()

            # Lopputilastot
            await self._log_final_stats()

        except KeyboardInterrupt:
            self.logger.warning("\n⚠ Crawlaus keskeytetty käyttäjän toimesta")
            await self._log_final_stats()

        except Exception as e:
            self.logger.error(f"Kriittinen virhe crawlauksessa: {e}", exc_info=True)

        finally:
            await self.close()

    async def _crawl_page(self, url: str, depth: int):
        """Crawlaa yhden sivun"""
        self.logger.info(f"[{self.total_crawled + 1}/{self.config.crawler.max_pages}] "
                        f"Syvyys {depth}: {url}")

        # Merkitse käydyksi
        self.visited_urls.add(url)
        self.total_crawled += 1

        # Päivitä domain-laskuri
        domain = extract_domain(url)
        if domain:
            self.domain_counters[domain] = self.domain_counters.get(domain, 0) + 1

        # Hae sivu
        headers = {'User-Agent': self.config.crawler.user_agent}
        response = await self.tor_client.fetch(
            url,
            headers=headers,
            timeout=self.config.crawler.request_timeout
        )

        # Parsoi sivu
        page_data = {
            'url': url,
            'status': response['status'],
            'depth': depth,
            'timestamp': datetime.utcnow().isoformat(),
            'error': response.get('error')
        }

        if response['status'] == 200 and response['content']:
            # Parsoi HTML
            parsed = self.parser.parse(response['content'], url)
            page_data.update({
                'title': parsed['title'],
                'text_preview': parsed['text_preview'],
                'meta': parsed['meta']
            })

            # Suodata .onion-linkit
            onion_links = self.parser.filter_onion_links(
                parsed['links'],
                allowed_domains=self.config.crawler.allowed_domains,
                follow_external=self.config.crawler.follow_external_onion,
                base_domain=self.start_domain
            )

            page_data['links'] = onion_links

            # Lisää uudet linkit jonoon
            for link in onion_links:
                if link not in self.visited_urls:
                    self.queue.append((link, depth + 1))

            self.logger.info(f"  ✓ {response['status']} - {parsed['title'][:50]} - {len(onion_links)} linkkiä")

        else:
            page_data.update({
                'title': '',
                'text_preview': '',
                'meta': {},
                'links': []
            })
            self.logger.warning(f"  ✗ {response['status']} - Virhe: {response.get('error', 'Unknown')}")

        # Tallenna
        await self.storage.save_page(page_data)

    async def _log_progress(self):
        """Tulostaa edistymistilastot"""
        stats = await self.storage.get_stats()
        self.logger.info(
            f"--- Edistyminen: {self.total_crawled}/{self.config.crawler.max_pages} sivua, "
            f"{len(self.queue)} jonossa, {len(self.domain_counters)} domainia ---"
        )

    async def _log_final_stats(self):
        """Tulostaa lopputilastot"""
        stats = await self.storage.get_stats()

        self.logger.info("=" * 80)
        self.logger.info("CRAWLAUS VALMIS")
        self.logger.info("=" * 80)
        self.logger.info(f"Crawlatut sivut yhteensä: {stats.get('total_pages', 0)}")
        self.logger.info(f"Onnistuneet: {stats.get('successful', 0)}")
        self.logger.info(f"Virheet: {stats.get('errors', 0)}")
        self.logger.info(f"Eri domaineja: {len(self.domain_counters)}")

        if self.config.storage.storage_type == "json":
            self.logger.info(f"Data tallennettu: {self.config.storage.output_dir}/{self.config.storage.json_filename}")
        else:
            self.logger.info(f"Data tallennettu: {self.config.storage.output_dir}/{self.config.storage.sqlite_filename}")

        self.logger.info("=" * 80)

    async def close(self):
        """Sulkee crawlerin ja vapauttaa resurssit"""
        if self.tor_client:
            await self.tor_client.close()

        if self.storage:
            await self.storage.close()

        self.logger.info("Crawler suljettu")
