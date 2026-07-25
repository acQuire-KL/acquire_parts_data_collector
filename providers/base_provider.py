from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from knowledge_base_manager import KnowledgeRecord


class ProviderConfigurationError(RuntimeError):
    """Raised when a provider cannot run because its configuration is absent."""


class BaseProvider(ABC):
    """Common contract implemented by every PDC data provider.

    Providers own authentication, collection and source-specific translation.
    The manager can orchestrate them without importing provider API clients.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name used in output and Knowledge Base records."""

    @property
    @abstractmethod
    def attribute_source(self) -> str:
        """Return the stable source label used for provider evidence and diagnostics."""

    @property
    @abstractmethod
    def required_environment_variables(self) -> tuple[str, ...]:
        """Return environment variables required to configure this provider."""

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
