from __future__ import annotations

from typing import Any

from config import MouserSettings
from knowledge_base_manager import KnowledgeBaseManager, KnowledgeRecord
from providers.base_provider import BaseProvider
from providers.mouser.client import MouserClient


class MouserProvider(BaseProvider):
    """PDC provider adapter for the Mouser Search API."""

    NAME = "Mouser"
    ATTRIBUTE_SOURCE = "Mouser Search API"
    REQUIRED_ENVIRONMENT_VARIABLES = ("MOUSER_API_KEY",)
    ENDPOINT = "Part_Number_Search"

    def __init__(
        self,
        settings: MouserSettings,
        knowledge_base: KnowledgeBaseManager | None = None,
        *,
        client: MouserClient | None = None,
    ):
        self.settings = settings
        self.knowledge_base = knowledge_base or KnowledgeBaseManager()
        self.client = client or MouserClient(settings)

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def attribute_source(self) -> str:
        return self.ATTRIBUTE_SOURCE

    @property
    def required_environment_variables(self) -> tuple[str, ...]:
        return self.REQUIRED_ENVIRONMENT_VARIABLES

    def search_part_number(self, mpn: str, *, part_search_options: str = "None") -> dict[str, Any]:
        return self.client.search_part_number(mpn, part_search_options=part_search_options)

    def manufacturers(self, force: bool = False) -> dict[str, Any]:
        del force
        return self.client.manufacturers()

    @staticmethod
    def _returned_manufacturer(payload: dict[str, Any]) -> str:
        results = payload.get("SearchResults") or payload.get("searchResults") or {}
        parts = results.get("Parts") or results.get("parts") or []
        first = parts[0] if parts and isinstance(parts[0], dict) else {}
        return str(first.get("Manufacturer") or first.get("manufacturer") or "")

    def details(
        self,
        mpn: str,
        manufacturer_id: Any = None,
        force: bool = False,
        *,
        input_manufacturer: str = "",
        resolved_manufacturer: str = "",
    ) -> KnowledgeRecord:
        del force
        payload = self.search_part_number(mpn)
        returned_manufacturer = self._returned_manufacturer(payload)
        resolved = resolved_manufacturer or returned_manufacturer or input_manufacturer
        return self.knowledge_base.save_live_response(
            provider=self.name,
            endpoint=self.ENDPOINT,
            manufacturer=resolved or "Unknown",
            mpn=mpn,
            provider_response=payload,
            input_manufacturer=input_manufacturer,
            resolved_manufacturer=resolved,
            manufacturer_id=manufacturer_id,
            locale="en-US",
            currency="",
            rate_limit={},
        )
