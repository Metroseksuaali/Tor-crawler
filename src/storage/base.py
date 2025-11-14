"""
Abstrakti tallennusluokka
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseStorage(ABC):
    """
    Abstrakti perusluokka tallennusmoduuleille
    """

    @abstractmethod
    async def initialize(self):
        """Alustaa tallennuksen (luo tiedostot/taulut)"""
        pass

    @abstractmethod
    async def save_page(self, page_data: Dict[str, Any]):
        """
        Tallentaa yhden sivun tiedot

        Args:
            page_data: Dict sisältäen:
                - url: str
                - status: int
                - title: str
                - depth: int
                - timestamp: str
                - links: List[str]
                - text_preview: str
                - meta: dict
                - error: Optional[str]
        """
        pass

    @abstractmethod
    async def get_visited_urls(self) -> set:
        """Palauttaa kaikki käydyt URL:t"""
        pass

    @abstractmethod
    async def close(self):
        """Sulkee tallennuksen"""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Palauttaa tilastot (sivumäärä, virheet, jne.)"""
        pass
