from __future__ import annotations

from typing import Any

from config import MouserSettings
from providers.base_provider import BaseProvider
from providers.mouser.client import MouserClient


class MouserProvider(BaseProvider):
    """PDC provider adapter for Mouser Search API connectivity.

    Step 3B.1 deliberately preserves the raw Mouser response. Mapping into the
    common Knowledge Base structures is deferred to Step 3B.2.
    """

    NAME = "Mouser"
    ATTRIBUTE_SOURCE = "Mouser Search API"
    REQUIRED_ENVIRONMENT_VARIABLES = ("MOUSER_API_KEY",)

    def __init__(
        self,
        settings: MouserSettings,
        *,
        client: MouserClient | None = None,
    ):
        self.settings = settings
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
        del force  # Mouser caching is not introduced during connectivity testing.
        return self.client.manufacturers()

    def details(
        self,
        mpn: str,
        manufacturer_id: Any = None,
        force: bool = False,
        *,
        input_manufacturer: str = "",
        resolved_manufacturer: str = "",
    ) -> dict[str, Any]:
        del manufacturer_id, force, input_manufacturer, resolved_manufacturer
        return self.search_part_number(mpn)
