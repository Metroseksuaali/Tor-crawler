"""
Abstract storage class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseStorage(ABC):
    """
    Abstract base class for storage modules
    """

    @abstractmethod
    async def initialize(self):
        """Initialize storage (create files/tables)"""
        pass

    @abstractmethod
    async def save_page(self, page_data: Dict[str, Any]):
        """
        Save single page data

        Args:
            page_data: Dict containing:
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
        """Return all visited URLs"""
        pass

    @abstractmethod
    async def close(self):
        """Close storage"""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Return statistics (page count, errors, etc.)"""
        pass
