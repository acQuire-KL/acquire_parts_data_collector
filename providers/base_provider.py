from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from knowledge_base_manager import KnowledgeRecord


class BaseProvider(ABC):
    """Common contract implemented by every PDC data provider.

    Providers own the provider-specific collection mechanism. The rest of PDC
    can request reference data and product details without importing the
    provider's API client directly.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name used in output and Knowledge Base records."""

    @property
    @abstractmethod
    def attribute_source(self) -> str:
        """Return the source label used on the All Attributes worksheet."""

    @abstractmethod
    def manufacturers(self, force: bool = False) -> Any:
        """Return the provider's manufacturer reference catalogue."""

    @abstractmethod
    def details(
        self,
        mpn: str,
        manufacturer_id: Any = None,
        force: bool = False,
        *,
        input_manufacturer: str = "",
        resolved_manufacturer: str = "",
    ) -> KnowledgeRecord:
        """Return a provider-backed Knowledge Base record for one part."""
