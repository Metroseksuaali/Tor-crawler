"""
HTML parsing and link extraction
"""

from bs4 import BeautifulSoup
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse
import logging

from .utils import normalize_url, is_onion_url, sanitize_html_text


class HTMLParser:
    """
    Parses HTML pages and extracts .onion links
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def parse(self, html: str, base_url: str) -> dict:
        """
        Parse HTML and return structured data

        Args:
            html: HTML content
            base_url: Page URL (for link normalization)

        Returns:
            Dict containing:
                - title: str - page title
                - links: List[str] - discovered links
                - text_preview: str - text preview
                - meta: dict - meta information
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Extract title
            title = self._extract_title(soup)

            # Extract links
            links = self._extract_links(soup, base_url)

            # Extract text preview
            text_preview = self._extract_text_preview(soup)

            # Meta information
            meta = self._extract_meta(soup)

            return {
                'title': title,
                'links': links,
                'text_preview': text_preview,
                'meta': meta
            }

        except Exception as e:
            self.logger.error(f"HTML parsing failed: {e}")
            return {
                'title': '',
                'links': [],
                'text_preview': '',
                'meta': {}
            }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return sanitize_html_text(title_tag.get_text(), max_length=200)

        # Try h1 if title is missing
        h1_tag = soup.find('h1')
        if h1_tag:
            return sanitize_html_text(h1_tag.get_text(), max_length=200)

        return "No title"

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract all links from page

        Returns:
            List of normalized URLs
        """
        links: Set[str] = set()

        # Find all <a href="..."> tags
        for tag in soup.find_all('a', href=True):
            href = tag['href']

            # Normalize URL
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
        Filter .onion links

        Args:
            links: List of URLs
            allowed_domains: List of allowed .onion domains (None = all)
            follow_external: Whether to allow other .onion domains
            base_domain: Source domain (if follow_external=False, only this is allowed)

        Returns:
            Filtered list of .onion URLs
        """
        filtered = []

        for link in links:
            # Check that it's .onion
            if not is_onion_url(link):
                continue

            # If allowed_domains defined, check that domain is in list
            if allowed_domains:
                domain = urlparse(link).hostname
                if domain not in allowed_domains:
                    continue

            # If not following external and domain differs
            if not follow_external and base_domain:
                domain = urlparse(link).hostname
                if domain != base_domain:
                    continue

            filtered.append(link)

        return filtered

    def _extract_text_preview(self, soup: BeautifulSoup, max_length: int = 500) -> str:
        """Extract page text preview"""
        # Remove script and style tags
        for script in soup(["script", "style"]):
            script.decompose()

        # Get body text
        text = soup.get_text()
        return sanitize_html_text(text, max_length=max_length)

    def _extract_meta(self, soup: BeautifulSoup) -> dict:
        """Extract meta information (description, keywords, etc.)"""
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
