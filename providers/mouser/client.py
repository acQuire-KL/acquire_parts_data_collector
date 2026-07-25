from __future__ import annotations

from typing import Any

import requests

from config import MouserSettings
from providers.base_provider import ProviderConfigurationError


class MouserApiError(RuntimeError):
    """Raised when Mouser returns an API-level error payload."""


class MouserClient:
    """Minimal Mouser Search API client used for Step 3B.1 connectivity."""

    PART_NUMBER_PATH = "/api/v1/search/partnumber"
    MANUFACTURER_LIST_PATH = "/api/v2/search/manufacturerlist"

    def __init__(self, settings: MouserSettings, *, session: Any = None):
        self.settings = settings
        self.session = session or requests.Session()

    def _require_configuration(self) -> None:
        if not self.settings.api_key:
            raise ProviderConfigurationError("MOUSER_API_KEY is not configured")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._require_configuration()
        response = self.session.post(
            f"{self.settings.base_url}{path}",
            params={"apiKey": self.settings.api_key},
            json=payload,
            timeout=self.settings.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        self._raise_for_api_errors(data)
        return data

    def _get(self, path: str) -> dict[str, Any]:
        self._require_configuration()
        response = self.session.get(
            f"{self.settings.base_url}{path}",
            params={"apiKey": self.settings.api_key},
            timeout=self.settings.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        self._raise_for_api_errors(data)
        return data

    @staticmethod
    def _raise_for_api_errors(data: Any) -> None:
        if not isinstance(data, dict):
            raise MouserApiError("Mouser returned an unexpected non-object response")

        errors = data.get("Errors") or data.get("errors") or []
        if not errors:
            return

        messages: list[str] = []
        for error in errors:
            if isinstance(error, dict):
                message = (
                    error.get("Message")
                    or error.get("message")
                    or error.get("Code")
                    or error.get("code")
                )
                messages.append(str(message or error))
            else:
                messages.append(str(error))
        raise MouserApiError("; ".join(messages))

    def search_part_number(self, mpn: str, *, part_search_options: str = "string") -> dict[str, Any]:
        """Search Mouser by part number and return the unmodified JSON payload."""
        clean_mpn = str(mpn or "").strip()
        if not clean_mpn:
            raise ValueError("MPN is required for a Mouser part-number search")

        payload = {
            "SearchByPartRequest": {
                "mouserPartNumber": clean_mpn,
                "partSearchOptions": part_search_options,
                "mouserPaysCustomsAndDuties": False,
            }
        }
        return self._post(self.PART_NUMBER_PATH, payload)

    def manufacturers(self) -> dict[str, Any]:
        """Return Mouser's manufacturer reference catalogue."""
        return self._get(self.MANUFACTURER_LIST_PATH)
