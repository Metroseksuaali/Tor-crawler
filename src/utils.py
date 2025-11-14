"""
Utility functions for Tor Crawler
"""

import logging
import re
from urllib.parse import urlparse, urljoin, urldefrag
from typing import Optional


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Create and configure logger"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Console handler
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, level.upper()))

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


def is_onion_url(url: str) -> bool:
    """Check if URL is a .onion address"""
    try:
        parsed = urlparse(url)
        return parsed.hostname and parsed.hostname.endswith('.onion')
    except Exception:
        return False


def normalize_url(url: str, base_url: Optional[str] = None) -> Optional[str]:
    """
    Normalize URL:
    - Remove fragments (#)
    - Convert relative URLs to absolute
    - Remove trailing slash
    """
    try:
        # If relative URL and base_url provided
        if base_url:
            url = urljoin(base_url, url)

        # Remove fragment
        url, _ = urldefrag(url)

        # Remove trailing slash (except root)
        parsed = urlparse(url)
        if parsed.path and parsed.path != '/' and parsed.path.endswith('/'):
            url = url.rstrip('/')

        return url
    except Exception:
        return None


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.hostname
    except Exception:
        return None


def sanitize_html_text(text: str, max_length: int = 1000) -> str:
    """Sanitize HTML text and limit length"""
    if not text:
        return ""

    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # Limit length
    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text


def is_valid_url_scheme(url: str) -> bool:
    """Check that URL uses HTTP or HTTPS scheme"""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ['http', 'https']
    except Exception:
        return False
