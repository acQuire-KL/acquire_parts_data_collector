from __future__ import annotations

from typing import Any

from digikey_client import DigiKeyClient
from knowledge_base_manager import KnowledgeBaseManager, KnowledgeRecord
from providers.base_provider import BaseProvider


class DigiKeyProvider(BaseProvider):
    """PDC provider adapter for DigiKey Product Information V4."""

    NAME = "DigiKey"
    ATTRIBUTE_SOURCE = "DigiKey Product Information V4"

    def __init__(
        self,
        settings,
        knowledge_base: KnowledgeBaseManager | None = None,
        *,
        client: DigiKeyClient | None = None,
    ):
        self.settings = settings
        self.client = client or DigiKeyClient(settings, knowledge_base)

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def attribute_source(self) -> str:
        return self.ATTRIBUTE_SOURCE

    def manufacturers(self, force: bool = False) -> Any:
        return self.client.manufacturers(force)

    def details(
        self,
        mpn: str,
        manufacturer_id: Any = None,
        force: bool = False,
        *,
        input_manufacturer: str = "",
        resolved_manufacturer: str = "",
    ) -> KnowledgeRecord:
        return self.client.details(
            mpn,
            manufacturer_id,
            force,
            input_manufacturer=input_manufacturer,
            resolved_manufacturer=resolved_manufacturer,
        )
