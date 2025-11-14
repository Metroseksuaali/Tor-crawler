"""
Tor Crawler core logic
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
    Main crawler class implementing BFS-based crawling
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logger("TorCrawler", config.log_level)

        # Components
        self.tor_client: Optional[TorClient] = None
        self.parser = HTMLParser(logger=self.logger)
        self.storage: Optional[BaseStorage] = None

        # Crawl state
        self.visited_urls: Set[str] = set()
        self.queue: deque = deque()
        self.domain_counters: Dict[str, int] = {}  # Domain -> page count
        self.total_crawled = 0
        self.start_domain: Optional[str] = None

    async def initialize(self):
        """Initialize crawler components"""
        self.logger.info("=" * 80)
        self.logger.info("TOR CRAWLER - Initialization")
        self.logger.info("=" * 80)

        # Initialize Tor connection
        self.tor_client = TorClient(self.config.tor, logger=self.logger)
        await self.tor_client.initialize()

        # Initialize storage
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
            raise ValueError(f"Unknown storage_type: {self.config.storage.storage_type}")

        await self.storage.initialize()

        # Load previously visited URLs
        self.visited_urls = await self.storage.get_visited_urls()

        # Add start URL to queue
        self.start_domain = extract_domain(self.config.crawler.start_url)
        self.queue.append((self.config.crawler.start_url, 0))  # (url, depth)

        self.logger.info(f"✓ Crawler initialized")
        self.logger.info(f"  Start URL: {self.config.crawler.start_url}")
        self.logger.info(f"  Max depth: {self.config.crawler.max_depth}")
        self.logger.info(f"  Max pages: {self.config.crawler.max_pages}")
        self.logger.info(f"  Storage: {self.config.storage.storage_type}")
        self.logger.info(f"  Previously visited: {len(self.visited_urls)}")
        self.logger.info("=" * 80)

    async def crawl(self):
        """Main crawl loop (BFS)"""
        try:
            while self.queue and self.total_crawled < self.config.crawler.max_pages:
                # Get next URL from queue
                url, depth = self.queue.popleft()

                # Check if already visited
                if url in self.visited_urls:
                    continue

                # Check depth
                if depth > self.config.crawler.max_depth:
                    continue

                # Check domain limits
                domain = extract_domain(url)
                if domain:
                    if self.domain_counters.get(domain, 0) >= self.config.crawler.max_pages_per_domain:
                        self.logger.debug(f"Domain limit reached: {domain}")
                        continue

                # Crawl page
                await self._crawl_page(url, depth)

                # Rate limiting
                if self.config.crawler.request_delay > 0:
                    await asyncio.sleep(self.config.crawler.request_delay)

                # Statistics
                if self.total_crawled % 10 == 0:
                    await self._log_progress()

            # Final statistics
            await self._log_final_stats()

        except KeyboardInterrupt:
            self.logger.warning("\n⚠ Crawling interrupted by user")
            await self._log_final_stats()

        except Exception as e:
            self.logger.error(f"Critical error during crawl: {e}", exc_info=True)

        finally:
            await self.close()

    async def _crawl_page(self, url: str, depth: int):
        """Crawl single page"""
        self.logger.info(f"[{self.total_crawled + 1}/{self.config.crawler.max_pages}] "
                        f"Depth {depth}: {url}")

        # Mark as visited
        self.visited_urls.add(url)
        self.total_crawled += 1

        # Update domain counter
        domain = extract_domain(url)
        if domain:
            self.domain_counters[domain] = self.domain_counters.get(domain, 0) + 1

        # Fetch page
        headers = {'User-Agent': self.config.crawler.user_agent}
        response = await self.tor_client.fetch(
            url,
            headers=headers,
            timeout=self.config.crawler.request_timeout
        )

        # Parse page
        page_data = {
            'url': url,
            'status': response['status'],
            'depth': depth,
            'timestamp': datetime.utcnow().isoformat(),
            'error': response.get('error')
        }

        if response['status'] == 200 and response['content']:
            # Parse HTML
            parsed = self.parser.parse(response['content'], url)
            page_data.update({
                'title': parsed['title'],
                'text_preview': parsed['text_preview'],
                'meta': parsed['meta']
            })

            # Filter .onion links
            onion_links = self.parser.filter_onion_links(
                parsed['links'],
                allowed_domains=self.config.crawler.allowed_domains,
                follow_external=self.config.crawler.follow_external_onion,
                base_domain=self.start_domain
            )

            page_data['links'] = onion_links

            # Add new links to queue
            for link in onion_links:
                if link not in self.visited_urls:
                    self.queue.append((link, depth + 1))

            self.logger.info(f"  ✓ {response['status']} - {parsed['title'][:50]} - {len(onion_links)} links")

        else:
            page_data.update({
                'title': '',
                'text_preview': '',
                'meta': {},
                'links': []
            })
            self.logger.warning(f"  ✗ {response['status']} - Error: {response.get('error', 'Unknown')}")

        # Save
        await self.storage.save_page(page_data)

    async def _log_progress(self):
        """Log progress statistics"""
        stats = await self.storage.get_stats()
        self.logger.info(
            f"--- Progress: {self.total_crawled}/{self.config.crawler.max_pages} pages, "
            f"{len(self.queue)} in queue, {len(self.domain_counters)} domains ---"
        )

    async def _log_final_stats(self):
        """Log final statistics"""
        stats = await self.storage.get_stats()

        self.logger.info("=" * 80)
        self.logger.info("CRAWL COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"Total pages crawled: {stats.get('total_pages', 0)}")
        self.logger.info(f"Successful: {stats.get('successful', 0)}")
        self.logger.info(f"Errors: {stats.get('errors', 0)}")
        self.logger.info(f"Unique domains: {len(self.domain_counters)}")

        if self.config.storage.storage_type == "json":
            self.logger.info(f"Data saved to: {self.config.storage.output_dir}/{self.config.storage.json_filename}")
        else:
            self.logger.info(f"Data saved to: {self.config.storage.output_dir}/{self.config.storage.sqlite_filename}")

        self.logger.info("=" * 80)

    async def close(self):
        """Close crawler and release resources"""
        if self.tor_client:
            await self.tor_client.close()

        if self.storage:
            await self.storage.close()

        self.logger.info("Crawler closed")
