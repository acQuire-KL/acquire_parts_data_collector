from __future__ import annotations

from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from config import TmeSettings
from providers.base_provider import ProviderConfigurationError


class TmeApiError(RuntimeError):
    """Raised when TME returns an API-level error or an unexpected payload."""


class TmeClient:
    """Minimal TME Product API v2 client used for connectivity diagnostics."""

    def __init__(self, settings: TmeSettings, *, session: Any = None):
        self.settings = settings
        self.session = session or requests.Session()

    def _require_configuration(self) -> None:
        missing: list[str] = []
        if not self.settings.token:
            missing.append("TME_TOKEN")
        if not self.settings.application_secret:
            missing.append("TME_APPLICATION_SECRET")
        if missing:
            raise ProviderConfigurationError(
                "TME configuration is incomplete: " + ", ".join(missing)
            )

    def _url(self, path: str) -> str:
        normalised = path if path.startswith("/") else "/" + path
        return f"{self.settings.base_url}{normalised}"

    @staticmethod
    def _json_or_error(response: Any, operation: str) -> dict[str, Any]:
        if not 200 <= response.status_code < 300:
            body = (response.text or "").strip()
            raise TmeApiError(
                f"TME {operation} failed: HTTP {response.status_code}. "
                f"Response: {body[:2000] or '<empty>'}"
            )
        try:
            payload = response.json()
        except ValueError as error:
            raise TmeApiError(f"TME {operation} returned a non-JSON response") from error
        if not isinstance(payload, dict):
            raise TmeApiError(f"TME {operation} returned an unexpected non-object response")
        return payload

    def obtain_access_token(self) -> dict[str, Any]:
        """Exchange the portal token and application secret for an access token."""
        self._require_configuration()
        response = self.session.post(
            self._url(self.settings.auth_path),
            headers={"Accept": "application/json"},
            data={"grant_type": "client_credentials"},
            auth=HTTPBasicAuth(self.settings.token, self.settings.application_secret),
            timeout=self.settings.timeout_seconds,
        )
        return self._json_or_error(response, "authentication")

    @staticmethod
    def _extract_access_token(payload: dict[str, Any]) -> str:
        candidates: list[Any] = [
            payload.get("access_token"),
            payload.get("accessToken"),
            payload.get("token"),
        ]
        data = payload.get("data")
        if isinstance(data, dict):
            candidates.extend(
                [data.get("access_token"), data.get("accessToken"), data.get("token")]
            )
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        raise TmeApiError(
            "TME authentication succeeded, but no access token was found in the response"
        )

    def search_products(self, query: str, *, anonymous: bool = False) -> dict[str, Any]:
        """Authenticate, search TME for one phrase, and return the raw JSON payload."""
        clean_query = str(query or "").strip()
        if not clean_query:
            raise ValueError("MPN is required for a TME product search")

        auth_payload = self.obtain_access_token()
        access_token = self._extract_access_token(auth_payload)

        headers = {
            "Accept": "application/json",
            "Accept-Language": self.settings.language,
            "Authorization": f"Bearer {access_token}",
        }
        if anonymous:
            headers["request-context"] = "anonymous"

        response = self.session.get(
            self._url(self.settings.search_path),
            params=[
                ("country", self.settings.country),
                ("scope[]", "products"),
                ("phrase", clean_query),
            ],
            headers=headers,
            timeout=self.settings.timeout_seconds,
        )
        return self._json_or_error(response, "product search")
