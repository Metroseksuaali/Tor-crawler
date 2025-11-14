"""
JSON-pohjainen tallennus (NDJSON-formaatti)
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Set
import logging

from .base import BaseStorage


class JSONStorage(BaseStorage):
    """
    Tallentaa crawlatut sivut NDJSON-tiedostoon (newline-delimited JSON)
    Jokainen rivi on yksi JSON-objekti
    """

    def __init__(self, output_dir: str, filename: str, logger: Optional[logging.Logger] = None):
        self.output_dir = Path(output_dir)
        self.filepath = self.output_dir / filename
        self.logger = logger or logging.getLogger(__name__)
        self._visited_urls: Set[str] = set()
        self._stats = {
            'total_pages': 0,
            'successful': 0,
            'errors': 0
        }

    async def initialize(self):
        """Luo output-hakemiston jos ei ole olemassa"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Jos tiedosto on olemassa, lataa käydyt URL:t
        if self.filepath.exists():
            self.logger.info(f"Jatketaan olemassa olevaa crawlausta: {self.filepath}")
            await self._load_existing_urls()
        else:
            self.logger.info(f"Luodaan uusi tiedosto: {self.filepath}")

    async def _load_existing_urls(self):
        """Lataa käydyt URL:t olemassa olevasta tiedostosta"""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        self._visited_urls.add(data.get('url', ''))
                        self._stats['total_pages'] += 1
                        if data.get('error'):
                            self._stats['errors'] += 1
                        else:
                            self._stats['successful'] += 1
                    except json.JSONDecodeError:
                        continue

            self.logger.info(f"Ladattu {len(self._visited_urls)} aiemmin crawlattua sivua")
        except Exception as e:
            self.logger.error(f"Virhe ladattaessa aiempia URL:eja: {e}")

    async def save_page(self, page_data: Dict[str, Any]):
        """Tallentaa sivun NDJSON-tiedostoon"""
        try:
            # Lisää visited-settiin
            self._visited_urls.add(page_data['url'])

            # Päivitä tilastot
            self._stats['total_pages'] += 1
            if page_data.get('error'):
                self._stats['errors'] += 1
            else:
                self._stats['successful'] += 1

            # Kirjoita tiedostoon (append mode)
            with open(self.filepath, 'a', encoding='utf-8') as f:
                json.dump(page_data, f, ensure_ascii=False)
                f.write('\n')

        except Exception as e:
            self.logger.error(f"Virhe tallennettaessa sivua {page_data.get('url', 'unknown')}: {e}")

    async def get_visited_urls(self) -> set:
        """Palauttaa kaikki käydyt URL:t"""
        return self._visited_urls.copy()

    async def close(self):
        """Ei tarvitse tehdä mitään NDJSON:lla"""
        self.logger.info(f"JSON-tallennus valmis: {self.filepath}")
        self.logger.info(f"Tilastot: {self._stats}")

    async def get_stats(self) -> Dict[str, Any]:
        """Palauttaa tilastot"""
        return self._stats.copy()

    def load_all_pages(self) -> list:
        """
        Apufunktio: Lataa kaikki sivut tiedostosta (jatkokäsittelyä varten)

        Returns:
            Lista dictionaryja
        """
        pages = []
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        pages.append(data)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass

        return pages
