"""
Tor-yhteyden hallinta ja SOCKS5-proxy-integraatio
"""

import aiohttp
import asyncio
from typing import Optional, Dict, Any
from aiohttp_socks import ProxyConnector
import logging

try:
    from stem import Signal
    from stem.control import Controller
    STEM_AVAILABLE = True
except ImportError:
    STEM_AVAILABLE = False

from .config import TorConfig
from .utils import setup_logger


class TorClient:
    """
    Hallitsee Tor-yhteyden ja HTTP-pyynnöt SOCKS5-proxyn kautta
    """

    def __init__(self, config: TorConfig, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or setup_logger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[ProxyConnector] = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def initialize(self):
        """Alustaa Tor-yhteyden ja HTTP-session"""
        proxy_url = f"socks5://{self.config.proxy_host}:{self.config.proxy_port}"

        self.logger.info(f"Alustetaan Tor-yhteys: {proxy_url}")

        # Luo SOCKS5-proxy connector
        self._connector = ProxyConnector.from_url(proxy_url)

        # Luo aiohttp session
        timeout = aiohttp.ClientTimeout(total=60, connect=30, sock_connect=30)
        self.session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=timeout
        )

        # Testaa yhteys
        try:
            await self._test_connection()
            self.logger.info("✓ Tor-yhteys toimii")
        except Exception as e:
            self.logger.error(f"✗ Tor-yhteyden testaus epäonnistui: {e}")
            raise ConnectionError(
                f"Tor-yhteyttä ei voitu muodostaa. Varmista että Tor on käynnissä portissa {self.config.proxy_port}. "
                f"Virhe: {e}"
            )

    async def _test_connection(self):
        """Testaa Tor-yhteyden toimivuuden"""
        # Yritä yksinkertainen pyyntö (voi epäonnistua jos ei nettiä, mutta tarkistaa proxyn)
        try:
            async with self.session.get(
                'https://check.torproject.org/api/ip',
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('IsTor', False):
                        self.logger.info(f"✓ Tor-yhteys vahvistettu. IP: {data.get('IP', 'unknown')}")
                    else:
                        self.logger.warning("⚠ Yhteys toimii, mutta ei Tor-verkon kautta!")
        except asyncio.TimeoutError:
            self.logger.warning("⚠ Tor-testaus aikakatkaisu (tämä voi olla normaalia Tor-verkossa)")
        except Exception as e:
            # Jos check.torproject.org ei vastaa, kokeillaan vain että proxy ottaa vastaan
            self.logger.debug(f"Tor-testaus virhe (voi olla normaalia): {e}")

    async def fetch(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        allow_redirects: bool = True
    ) -> Dict[str, Any]:
        """
        Hakee sivun Tor-verkon kautta

        Returns:
            Dict sisältäen:
                - url: str - lopullinen URL (redirectien jälkeen)
                - status: int - HTTP status code
                - headers: dict - response headers
                - content: str - HTML-sisältö
                - error: Optional[str] - virheviesti jos epäonnistui
        """
        if not self.session:
            raise RuntimeError("TorClient ei ole alustettu. Käytä async with -kontekstia.")

        try:
            async with self.session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
                allow_redirects=allow_redirects,
                ssl=False  # .onion-sivuilla ei SSL-validointia
            ) as response:
                # Lue sisältö
                try:
                    content = await response.text(errors='ignore')
                except Exception as e:
                    self.logger.warning(f"Sisällön lukeminen epäonnistui {url}: {e}")
                    content = ""

                return {
                    'url': str(response.url),
                    'status': response.status,
                    'headers': dict(response.headers),
                    'content': content,
                    'error': None
                }

        except asyncio.TimeoutError:
            self.logger.warning(f"Aikakatkaisu: {url}")
            return {
                'url': url,
                'status': 0,
                'headers': {},
                'content': '',
                'error': 'Timeout'
            }

        except aiohttp.ClientError as e:
            self.logger.warning(f"HTTP-virhe {url}: {e}")
            return {
                'url': url,
                'status': 0,
                'headers': {},
                'content': '',
                'error': f'ClientError: {str(e)}'
            }

        except Exception as e:
            self.logger.error(f"Odottamaton virhe {url}: {e}")
            return {
                'url': url,
                'status': 0,
                'headers': {},
                'content': '',
                'error': f'Exception: {str(e)}'
            }

    async def renew_tor_circuit(self) -> bool:
        """
        Uusii Tor-piirin saadakseen uuden IP-osoitteen (vaatii stem-kirjaston)

        Returns:
            True jos onnistui, False jos stem ei käytössä tai epäonnistui
        """
        if not self.config.use_stem or not STEM_AVAILABLE:
            self.logger.debug("Tor-piirin uusiminen ei käytössä (stem ei asennettu tai ei konfiguroitu)")
            return False

        try:
            with Controller.from_port(port=self.config.control_port) as controller:
                if self.config.control_password:
                    controller.authenticate(password=self.config.control_password)
                else:
                    controller.authenticate()

                controller.signal(Signal.NEWNYM)
                self.logger.info("✓ Tor-piiri uusittu (uusi IP)")

                # Odota hetki että uusi piiri muodostuu
                await asyncio.sleep(5)
                return True

        except Exception as e:
            self.logger.error(f"Tor-piirin uusiminen epäonnistui: {e}")
            return False

    async def close(self):
        """Sulkee HTTP-session"""
        if self.session:
            await self.session.close()
            self.logger.info("Tor-yhteys suljettu")
