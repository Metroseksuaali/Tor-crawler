"""
SQLite-pohjainen tallennus
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, Set, Optional
import logging

from .base import BaseStorage


class SQLiteStorage(BaseStorage):
    """
    Tallentaa crawlatut sivut SQLite-tietokantaan
    """

    def __init__(self, output_dir: str, filename: str, logger: Optional[logging.Logger] = None):
        self.output_dir = Path(output_dir)
        self.filepath = self.output_dir / filename
        self.logger = logger or logging.getLogger(__name__)
        self.conn: Optional[sqlite3.Connection] = None
        self._visited_urls: Set[str] = set()

    async def initialize(self):
        """Luo tietokanta ja taulut"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.filepath))
        self.conn.row_factory = sqlite3.Row

        # Luo taulut
        self._create_tables()

        # Lataa käydyt URL:t
        await self._load_visited_urls()

        self.logger.info(f"SQLite-tietokanta alustettu: {self.filepath}")

    def _create_tables(self):
        """Luo tietokantataulut"""
        cursor = self.conn.cursor()

        # Pääsivu-taulu
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
                meta TEXT,  -- JSON-muodossa
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Linkit-taulu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT NOT NULL,
                target_url TEXT NOT NULL,
                FOREIGN KEY (source_url) REFERENCES pages(url)
            )
        ''')

        # Indeksit suorituskyvyn parantamiseksi
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pages_url ON pages(url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pages_status ON pages(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_url)')

        self.conn.commit()

    async def _load_visited_urls(self):
        """Lataa käydyt URL:t tietokannasta"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT url FROM pages')
        self._visited_urls = {row[0] for row in cursor.fetchall()}
        self.logger.info(f"Ladattu {len(self._visited_urls)} aiemmin crawlattua sivua")

    async def save_page(self, page_data: Dict[str, Any]):
        """Tallentaa sivun SQLite-tietokantaan"""
        try:
            cursor = self.conn.cursor()

            # Tallenna pääsivu
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

            # Tallenna linkit
            for link in page_data.get('links', []):
                cursor.execute('''
                    INSERT INTO links (source_url, target_url)
                    VALUES (?, ?)
                ''', (page_data['url'], link))

            self.conn.commit()

            # Lisää visited-settiin
            self._visited_urls.add(page_data['url'])

        except sqlite3.IntegrityError as e:
            self.logger.debug(f"Sivu jo tietokannassa: {page_data['url']}")
        except Exception as e:
            self.logger.error(f"Virhe tallennettaessa sivua {page_data.get('url', 'unknown')}: {e}")

    async def get_visited_urls(self) -> set:
        """Palauttaa kaikki käydyt URL:t"""
        return self._visited_urls.copy()

    async def close(self):
        """Sulkee tietokantayhteyden"""
        if self.conn:
            self.conn.close()
            self.logger.info(f"SQLite-yhteys suljettu: {self.filepath}")

    async def get_stats(self) -> Dict[str, Any]:
        """Palauttaa tilastot"""
        cursor = self.conn.cursor()

        # Kokonaismäärä
        cursor.execute('SELECT COUNT(*) FROM pages')
        total = cursor.fetchone()[0]

        # Onnistuneet
        cursor.execute('SELECT COUNT(*) FROM pages WHERE error IS NULL')
        successful = cursor.fetchone()[0]

        # Virheet
        cursor.execute('SELECT COUNT(*) FROM pages WHERE error IS NOT NULL')
        errors = cursor.fetchone()[0]

        # Linkit
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
        Apufunktio: Kyselee sivuja tietokannasta

        Args:
            where_clause: SQL WHERE-ehto (esim. "status = 200")
            params: Parametrit prepared statementtiin

        Returns:
            Lista dictionaryja
        """
        cursor = self.conn.cursor()
        cursor.execute(f'SELECT * FROM pages WHERE {where_clause}', params)

        pages = []
        for row in cursor.fetchall():
            pages.append(dict(row))

        return pages
