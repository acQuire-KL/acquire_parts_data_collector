from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import quote

import requests

from knowledge_base_manager import KnowledgeBaseManager, KnowledgeRecord


class DigiKeyClient:
    PROVIDER = "DigiKey"
    PRODUCT_ENDPOINT = "Product_Details"

    def __init__(self, settings, knowledge_base: KnowledgeBaseManager | None = None):
        self.s = settings
        self.session = requests.Session()
        self.token = None
        self.expires = 0
        self.knowledge_base = knowledge_base or KnowledgeBaseManager()
        self.legacy_cache = Path("cache")

    def _get_token(self):
        if self.token and time.time() < self.expires - 30:
            return self.token
        response = self.session.post(
            self.s.base_url + "/v1/oauth2/token",
            data={
                "client_id": self.s.client_id,
                "client_secret": self.s.client_secret,
                "grant_type": "client_credentials",
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        self.expires = time.time() + int(data.get("expires_in", 600))
        return self.token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "X-DIGIKEY-Client-Id": self.s.client_id,
            "X-DIGIKEY-Locale-Site": self.s.site,
            "X-DIGIKEY-Locale-Language": self.s.language,
            "X-DIGIKEY-Locale-Currency": self.s.currency,
            "Accept": "application/json",
        }

    @staticmethod
    def _safe(value):
        return "".join(c if c.isalnum() else "_" for c in str(value))[:120]

    @staticmethod
    def _rate_limit(response: requests.Response) -> dict[str, str]:
        result = {}
        for key, value in response.headers.items():
            if "ratelimit" in key.lower() or "rate-limit" in key.lower():
                result[key] = value
        return result

    def _get_json(self, path, params=None):
        response = self.session.get(
            self.s.base_url + path,
            headers=self._headers(),
            params=params,
            timeout=30,
        )
        if not response.ok:
            raise RuntimeError(f"DigiKey {response.status_code}: {response.text[:1000]}")
        return response.json(), self._rate_limit(response)

    def manufacturers(self, force=False):
        if not force:
            current = self.knowledge_base.load_reference_data(self.PROVIDER, "Manufacturers")
            if current:
                return current.provider_response

            legacy = self.legacy_cache / "_manufacturers.json"
            if legacy.exists():
                response = json.loads(legacy.read_text(encoding="utf-8"))
                self.knowledge_base.save_reference_data(
                    provider=self.PROVIDER,
                    dataset="Manufacturers",
                    provider_response=response,
                    locale=self.s.site,
                    currency=self.s.currency,
                )
                return response

        data, rate_limit = self._get_json("/products/v4/search/manufacturers")
        self.knowledge_base.save_reference_data(
            provider=self.PROVIDER,
            dataset="Manufacturers",
            provider_response=data,
            locale=self.s.site,
            currency=self.s.currency,
            rate_limit=rate_limit,
        )
        return data

    def details(
        self,
        mpn,
        manufacturer_id=None,
        force=False,
        *,
        input_manufacturer="",
        resolved_manufacturer="",
    ) -> KnowledgeRecord:
        storage_manufacturer = resolved_manufacturer or input_manufacturer or f"MFG_{manufacturer_id}"

        if not force:
            current = self.knowledge_base.load_current(
                self.PROVIDER, self.PRODUCT_ENDPOINT, storage_manufacturer, mpn
            )
            if current:
                return current

            safe_mpn = self._safe(mpn)
            suffix = f"_MFG_{manufacturer_id}" if manufacturer_id is not None else ""
            legacy = self.legacy_cache / f"{safe_mpn}{suffix}.json"
            migrated = self.knowledge_base.migrate_legacy_file(
                legacy,
                provider=self.PROVIDER,
                endpoint=self.PRODUCT_ENDPOINT,
                manufacturer=storage_manufacturer,
                mpn=mpn,
                input_manufacturer=input_manufacturer,
                resolved_manufacturer=resolved_manufacturer,
                manufacturer_id=manufacturer_id,
                locale=self.s.site,
                currency=self.s.currency,
            )
            if migrated:
                return migrated

        path = "/products/v4/search/" + quote(mpn, safe="") + "/productdetails"
        params = {"manufacturerId": manufacturer_id} if manufacturer_id is not None else None
        data, rate_limit = self._get_json(path, params=params)
        return self.knowledge_base.save_live_response(
            provider=self.PROVIDER,
            endpoint=self.PRODUCT_ENDPOINT,
            manufacturer=storage_manufacturer,
            mpn=mpn,
            provider_response=data,
            input_manufacturer=input_manufacturer,
            resolved_manufacturer=resolved_manufacturer,
            manufacturer_id=manufacturer_id,
            locale=self.s.site,
            currency=self.s.currency,
            rate_limit=rate_limit,
        )
