"""
JSON-based storage (NDJSON format)
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Set, Optional
import logging

from .base import BaseStorage


class JSONStorage(BaseStorage):
    """
    Stores crawled pages in NDJSON file (newline-delimited JSON)
    Each line is one JSON object
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
        """Create output directory if it doesn't exist"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # If file exists, load visited URLs
        if self.filepath.exists():
            self.logger.info(f"Resuming existing crawl: {self.filepath}")
            await self._load_existing_urls()
        else:
            self.logger.info(f"Creating new file: {self.filepath}")

    async def _load_existing_urls(self):
        """Load visited URLs from existing file"""
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

            self.logger.info(f"Loaded {len(self._visited_urls)} previously crawled pages")
        except Exception as e:
            self.logger.error(f"Error loading previous URLs: {e}")

    async def save_page(self, page_data: Dict[str, Any]):
        """Save page to NDJSON file"""
        try:
            # Add to visited set
            self._visited_urls.add(page_data['url'])

            # Update stats
            self._stats['total_pages'] += 1
            if page_data.get('error'):
                self._stats['errors'] += 1
            else:
                self._stats['successful'] += 1

            # Write to file (append mode)
            with open(self.filepath, 'a', encoding='utf-8') as f:
                json.dump(page_data, f, ensure_ascii=False)
                f.write('\n')

        except Exception as e:
            self.logger.error(f"Error saving page {page_data.get('url', 'unknown')}: {e}")

    async def get_visited_urls(self) -> set:
        """Return all visited URLs"""
        return self._visited_urls.copy()

    async def close(self):
        """Nothing to do for NDJSON"""
        self.logger.info(f"JSON storage complete: {self.filepath}")
        self.logger.info(f"Statistics: {self._stats}")

    async def get_stats(self) -> Dict[str, Any]:
        """Return statistics"""
        return self._stats.copy()

    def load_all_pages(self) -> list:
        """
        Helper function: Load all pages from file (for post-processing)

        Returns:
            List of dictionaries
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
