"""
SQLite-based storage
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, Set, Optional
import logging

from .base import BaseStorage


class SQLiteStorage(BaseStorage):
    """
    Stores crawled pages in SQLite database
    """

    def __init__(self, output_dir: str, filename: str, logger: Optional[logging.Logger] = None):
        self.output_dir = Path(output_dir)
        self.filepath = self.output_dir / filename
        self.logger = logger or logging.getLogger(__name__)
        self.conn: Optional[sqlite3.Connection] = None
        self._visited_urls: Set[str] = set()

    async def initialize(self):
        """Create database and tables"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.filepath))
        self.conn.row_factory = sqlite3.Row

        # Create tables
        self._create_tables()

        # Load visited URLs
        await self._load_visited_urls()

        self.logger.info(f"SQLite database initialized: {self.filepath}")

    def _create_tables(self):
        """Create database tables"""
        cursor = self.conn.cursor()

        # Main pages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                status INTEGER,
                title TEXT,
                depth INTEGER,
                timestamp TEXT,
                text_preview TEXT,
                error TEXT,
                meta TEXT,  -- JSON format
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Links table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT NOT NULL,
                target_url TEXT NOT NULL,
                FOREIGN KEY (source_url) REFERENCES pages(url)
            )
        ''')

        # Indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pages_url ON pages(url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pages_status ON pages(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_url)')

        self.conn.commit()

    async def _load_visited_urls(self):
        """Load visited URLs from database"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT url FROM pages')
        self._visited_urls = {row[0] for row in cursor.fetchall()}
        self.logger.info(f"Loaded {len(self._visited_urls)} previously crawled pages")

    async def save_page(self, page_data: Dict[str, Any]):
        """Save page to SQLite database"""
        try:
            cursor = self.conn.cursor()

            # Save main page
            cursor.execute('''
                INSERT OR REPLACE INTO pages
                (url, status, title, depth, timestamp, text_preview, error, meta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                page_data['url'],
                page_data.get('status', 0),
                page_data.get('title', ''),
                page_data.get('depth', 0),
                page_data.get('timestamp', ''),
                page_data.get('text_preview', ''),
                page_data.get('error'),
                json.dumps(page_data.get('meta', {}))
            ))

            # Save links
            for link in page_data.get('links', []):
                cursor.execute('''
                    INSERT INTO links (source_url, target_url)
                    VALUES (?, ?)
                ''', (page_data['url'], link))

            self.conn.commit()

            # Add to visited set
            self._visited_urls.add(page_data['url'])

        except sqlite3.IntegrityError as e:
            self.logger.debug(f"Page already in database: {page_data['url']}")
        except Exception as e:
            self.logger.error(f"Error saving page {page_data.get('url', 'unknown')}: {e}")

    async def get_visited_urls(self) -> set:
        """Return all visited URLs"""
        return self._visited_urls.copy()

    async def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.logger.info(f"SQLite connection closed: {self.filepath}")

    async def get_stats(self) -> Dict[str, Any]:
        """Return statistics"""
        cursor = self.conn.cursor()

        # Total count
        cursor.execute('SELECT COUNT(*) FROM pages')
        total = cursor.fetchone()[0]

        # Successful
        cursor.execute('SELECT COUNT(*) FROM pages WHERE error IS NULL')
        successful = cursor.fetchone()[0]

        # Errors
        cursor.execute('SELECT COUNT(*) FROM pages WHERE error IS NOT NULL')
        errors = cursor.fetchone()[0]

        # Links
        cursor.execute('SELECT COUNT(*) FROM links')
        total_links = cursor.fetchone()[0]

        return {
            'total_pages': total,
            'successful': successful,
            'errors': errors,
            'total_links': total_links
        }

    def query_pages(self, where_clause: str = "1=1", params: tuple = ()) -> list:
        """
        Helper function: Query pages from database

        Args:
            where_clause: SQL WHERE condition (e.g. "status = 200")
            params: Parameters for prepared statement

        Returns:
            List of dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute(f'SELECT * FROM pages WHERE {where_clause}', params)

        pages = []
        for row in cursor.fetchall():
            pages.append(dict(row))

        return pages
