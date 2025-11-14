"""
HTML-parsinta ja linkkien eristäminen
"""

from bs4 import BeautifulSoup
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse
import logging

from .utils import normalize_url, is_onion_url, sanitize_html_text


class HTMLParser:
    """
    Parsii HTML-sivuja ja eristää .onion-linkit
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def parse(self, html: str, base_url: str) -> dict:
        """
        Parsii HTML:n ja palauttaa rakenteisen datan

        Args:
            html: HTML-sisältö
            base_url: Sivun URL (linkkien normalisointiin)

        Returns:
            Dict sisältäen:
                - title: str - sivun otsikko
                - links: List[str] - löydetyt linkit
                - text_preview: str - tekstin esikatselu
                - meta: dict - meta-tiedot
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Eristä otsikko
            title = self._extract_title(soup)

            # Eristä linkit
            links = self._extract_links(soup, base_url)

            # Eristä tekstin esikatselu
            text_preview = self._extract_text_preview(soup)

            # Meta-tiedot
            meta = self._extract_meta(soup)

            return {
                'title': title,
                'links': links,
                'text_preview': text_preview,
                'meta': meta
            }

        except Exception as e:
            self.logger.error(f"HTML-parsinta epäonnistui: {e}")
            return {
                'title': '',
                'links': [],
                'text_preview': '',
                'meta': {}
            }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Eristää sivun otsikon"""
        title_tag = soup.find('title')
        if title_tag:
            return sanitize_html_text(title_tag.get_text(), max_length=200)

        # Kokeile h1:stä jos title puuttuu
        h1_tag = soup.find('h1')
        if h1_tag:
            return sanitize_html_text(h1_tag.get_text(), max_length=200)

        return "Ei otsikkoa"

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Eristää kaikki linkit sivulta

        Returns:
            Lista normalisoituja URL:eja
        """
        links: Set[str] = set()

        # Etsi kaikki <a href="..."> -tagit
        for tag in soup.find_all('a', href=True):
            href = tag['href']

            # Normalisoi URL
            normalized = normalize_url(href, base_url)
            if normalized:
                links.add(normalized)

        return list(links)

    def filter_onion_links(
        self,
        links: List[str],
        allowed_domains: Optional[List[str]] = None,
        follow_external: bool = True,
        base_domain: Optional[str] = None
    ) -> List[str]:
        """
        Suodattaa .onion-linkit

        Args:
            links: Lista URL:eja
            allowed_domains: Lista sallittuja .onion-domaineja (None = kaikki)
            follow_external: Sallitaanko muut .onion-domainit
            base_domain: Lähtödomain (jos follow_external=False, vain tämä sallitaan)

        Returns:
            Suodatettu lista .onion-URL:eja
        """
        filtered = []

        for link in links:
            # Tarkista että on .onion
            if not is_onion_url(link):
                continue

            # Jos allowed_domains määritelty, tarkista että domain on listalla
            if allowed_domains:
                domain = urlparse(link).hostname
                if domain not in allowed_domains:
                    continue

            # Jos ei seurata ulkoisia ja domain eroaa
            if not follow_external and base_domain:
                domain = urlparse(link).hostname
                if domain != base_domain:
                    continue

            filtered.append(link)

        return filtered

    def _extract_text_preview(self, soup: BeautifulSoup, max_length: int = 500) -> str:
        """Eristää sivun tekstin esikatselun"""
        # Poista script ja style -tagit
        for script in soup(["script", "style"]):
            script.decompose()

        # Ota body-teksti
        text = soup.get_text()
        return sanitize_html_text(text, max_length=max_length)

    def _extract_meta(self, soup: BeautifulSoup) -> dict:
        """Eristää meta-tiedot (description, keywords, jne.)"""
        meta = {}

        # Meta description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag and desc_tag.get('content'):
            meta['description'] = sanitize_html_text(desc_tag['content'], max_length=300)

        # Meta keywords
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag and keywords_tag.get('content'):
            meta['keywords'] = sanitize_html_text(keywords_tag['content'], max_length=200)

        # Meta author
        author_tag = soup.find('meta', attrs={'name': 'author'})
        if author_tag and author_tag.get('content'):
            meta['author'] = sanitize_html_text(author_tag['content'], max_length=100)

        return meta
