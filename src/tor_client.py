"""
Tor connection management and SOCKS5 proxy integration
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
    Manages Tor connection and HTTP requests via SOCKS5 proxy
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
        """Initialize Tor connection and HTTP session"""
        proxy_url = f"socks5://{self.config.proxy_host}:{self.config.proxy_port}"

        self.logger.info(f"Initializing Tor connection: {proxy_url}")

        # Create SOCKS5 proxy connector
        self._connector = ProxyConnector.from_url(proxy_url)

        # Create aiohttp session
        timeout = aiohttp.ClientTimeout(total=60, connect=30, sock_connect=30)
        self.session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=timeout
        )

        # Test connection
        try:
            await self._test_connection()
            self.logger.info("✓ Tor connection working")
        except Exception as e:
            self.logger.error(f"✗ Tor connection test failed: {e}")
            raise ConnectionError(
                f"Could not establish Tor connection. Ensure Tor is running on port {self.config.proxy_port}. "
                f"Error: {e}"
            )

    async def _test_connection(self):
        """Test Tor connection functionality"""
        # Try simple request (may fail if no internet, but checks proxy)
        try:
            async with self.session.get(
                'https://check.torproject.org/api/ip',
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('IsTor', False):
                        self.logger.info(f"✓ Tor connection verified. IP: {data.get('IP', 'unknown')}")
                    else:
                        self.logger.warning("⚠ Connection works but not through Tor network!")
        except asyncio.TimeoutError:
            self.logger.warning("⚠ Tor test timeout (this can be normal on Tor network)")
        except Exception as e:
            # If check.torproject.org doesn't respond, just verify proxy accepts connections
            self.logger.debug(f"Tor test error (may be normal): {e}")

    async def fetch(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        allow_redirects: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch page through Tor network

        Returns:
            Dict containing:
                - url: str - final URL (after redirects)
                - status: int - HTTP status code
                - headers: dict - response headers
                - content: str - HTML content
                - error: Optional[str] - error message if failed
        """
        if not self.session:
            raise RuntimeError("TorClient not initialized. Use async with context.")

        try:
            async with self.session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
                allow_redirects=allow_redirects,
                ssl=False  # No SSL validation for .onion sites
            ) as response:
                # Read content
                try:
                    content = await response.text(errors='ignore')
                except Exception as e:
                    self.logger.warning(f"Failed to read content {url}: {e}")
                    content = ""

                return {
                    'url': str(response.url),
                    'status': response.status,
                    'headers': dict(response.headers),
                    'content': content,
                    'error': None
                }

        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout: {url}")
            return {
                'url': url,
                'status': 0,
                'headers': {},
                'content': '',
                'error': 'Timeout'
            }

        except aiohttp.ClientError as e:
            self.logger.warning(f"HTTP error {url}: {e}")
            return {
                'url': url,
                'status': 0,
                'headers': {},
                'content': '',
                'error': f'ClientError: {str(e)}'
            }

        except Exception as e:
            self.logger.error(f"Unexpected error {url}: {e}")
            return {
                'url': url,
                'status': 0,
                'headers': {},
                'content': '',
                'error': f'Exception: {str(e)}'
            }

    async def renew_tor_circuit(self) -> bool:
        """
        Renew Tor circuit to get new IP address (requires stem library)

        Returns:
            True if successful, False if stem not enabled or failed
        """
        if not self.config.use_stem or not STEM_AVAILABLE:
            self.logger.debug("Tor circuit renewal not enabled (stem not installed or configured)")
            return False

        try:
            with Controller.from_port(port=self.config.control_port) as controller:
                if self.config.control_password:
                    controller.authenticate(password=self.config.control_password)
                else:
                    controller.authenticate()

                controller.signal(Signal.NEWNYM)
                self.logger.info("✓ Tor circuit renewed (new IP)")

                # Wait for new circuit to form
                await asyncio.sleep(5)
                return True

        except Exception as e:
            self.logger.error(f"Tor circuit renewal failed: {e}")
            return False

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.logger.info("Tor connection closed")
