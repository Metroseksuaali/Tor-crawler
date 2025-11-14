"""
Apufunktiot Tor Crawlerille
"""

import logging
import re
from urllib.parse import urlparse, urljoin, urldefrag
from typing import Optional


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Luo ja konfiguroi logger"""
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
    """Tarkistaa, onko URL .onion-osoite"""
    try:
        parsed = urlparse(url)
        return parsed.hostname and parsed.hostname.endswith('.onion')
    except Exception:
        return False


def normalize_url(url: str, base_url: Optional[str] = None) -> Optional[str]:
    """
    Normalisoi URL:n:
    - Poistaa fragmentit (#)
    - Muuttaa suhteelliset URL:t absoluuttisiksi
    - Poistaa trailing slashin
    """
    try:
        # Jos suhteellinen URL ja base_url annettu
        if base_url:
            url = urljoin(base_url, url)

        # Poista fragmentti
        url, _ = urldefrag(url)

        # Poista trailing slash (paitsi root)
        parsed = urlparse(url)
        if parsed.path and parsed.path != '/' and parsed.path.endswith('/'):
            url = url.rstrip('/')

        return url
    except Exception:
        return None


def extract_domain(url: str) -> Optional[str]:
    """Eristää domainin URL:sta"""
    try:
        parsed = urlparse(url)
        return parsed.hostname
    except Exception:
        return None


def sanitize_html_text(text: str, max_length: int = 1000) -> str:
    """Puhdistaa HTML-tekstin ja rajoittaa pituuden"""
    if not text:
        return ""

    # Poista ylimääräiset välilyönnit ja rivinvaihdot
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # Rajoita pituus
    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text


def is_valid_url_scheme(url: str) -> bool:
    """Tarkistaa, että URL käyttää HTTP tai HTTPS -skeemaa"""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ['http', 'https']
    except Exception:
        return False
