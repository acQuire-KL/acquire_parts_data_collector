from __future__ import annotations

from typing import Any

from config import TmeSettings
from knowledge_base_manager import KnowledgeBaseManager, KnowledgeRecord, utc_text
from providers.base_provider import BaseProvider
from providers.tme.client import TmeClient
from providers.tme.normalizer import build_tme_pdc_part_profile


class TmeProvider(BaseProvider):
    """Operational TME adapter for the PDC provider-neutral workflow."""

    NAME = "TME"
    ATTRIBUTE_SOURCE = "TME Product API v2"
    REQUIRED_ENVIRONMENT_VARIABLES = ("TME_TOKEN", "TME_APPLICATION_SECRET")

    def __init__(
        self,
        settings: TmeSettings,
        knowledge_base: KnowledgeBaseManager | None = None,
        *,
        client: TmeClient | None = None,
    ):
        self.settings = settings
        self.knowledge_base = knowledge_base or KnowledgeBaseManager()
        self.client = client or TmeClient(settings)

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def attribute_source(self) -> str:
        return self.ATTRIBUTE_SOURCE

    @property
    def required_environment_variables(self) -> tuple[str, ...]:
        return self.REQUIRED_ENVIRONMENT_VARIABLES

    def manufacturers(self, force: bool = False) -> dict[str, Any]:
        del force
        return {}

    def details(
        self,
        mpn: str,
        manufacturer_id: Any = None,
        force: bool = False,
        *,
        input_manufacturer: str = "",
        resolved_manufacturer: str = "",
    ) -> KnowledgeRecord:
        del manufacturer_id, force
        manufacturer = resolved_manufacturer or input_manufacturer or "Unknown"

        # Reuse one authentication token across the three TME endpoints.  Prior
        # behaviour authenticated separately for Search, Data and Parameters.
        access_token = self.client.access_token()
        search = self.client.search_products(mpn, access_token=access_token)
        # Search result symbol is the safest product key for subsequent TME endpoints.
        symbol = self._first_symbol(search) or mpn
        data = self.client.get_product_data(symbol, access_token=access_token)
        parameters = self.client.get_product_parameters(symbol, access_token=access_token)

        search_record = self.knowledge_base.save_raw_provider_response(
            provider=self.name, endpoint="Product_Search", manufacturer=manufacturer,
            mpn=mpn, provider_response=search, input_manufacturer=input_manufacturer,
            locale=self.settings.language, currency=self.settings.currency,
        )
        data_record = self.knowledge_base.save_raw_provider_response(
            provider=self.name, endpoint="Product_Data", manufacturer=manufacturer,
            mpn=mpn, provider_response=data, input_manufacturer=input_manufacturer,
            locale=self.settings.language, currency=self.settings.currency,
        )
        parameter_record = self.knowledge_base.save_raw_provider_response(
            provider=self.name, endpoint="Product_Parameters", manufacturer=manufacturer,
            mpn=mpn, provider_response=parameters, input_manufacturer=input_manufacturer,
            locale=self.settings.language, currency=self.settings.currency,
        )

        profile = build_tme_pdc_part_profile(
            self._record_dict(search_record), self._record_dict(data_record),
            self._record_dict(parameter_record)
        )
        part_profile = self._flat_part_profile(profile)
        commercial_profile = self._flat_commercial_profile(profile)
        metadata = {
            "provider": self.name,
            "captured_at_utc": profile.provider_metadata.captured_at_utc or utc_text(),
            "source_mode": "live_api",
            "input_manufacturer": input_manufacturer,
            "input_mpn": mpn,
            "resolved_manufacturer": manufacturer,
            "locale": self.settings.language,
            "currency": self.settings.currency,
        }
        return KnowledgeRecord(
            provider_response={"search": search, "data": data, "parameters": parameters},
            metadata=metadata,
            commercial_profile=commercial_profile,
            part_profile=part_profile,
        )

    @staticmethod
    def _record_dict(record: KnowledgeRecord) -> dict[str, Any]:
        return {
            "knowledge_base_metadata": record.metadata,
            "provider_response": record.provider_response,
        }

    @staticmethod
    def _first_symbol(payload: dict[str, Any]) -> str:
        data = payload.get("data") or {}
        products = data.get("products") or {}
        elements = products.get("elements") if isinstance(products, dict) else []
        if isinstance(elements, list) and elements and isinstance(elements[0], dict):
            return str(elements[0].get("symbol") or "").strip()
        return ""

    @staticmethod
    def _flat_part_profile(profile) -> dict[str, Any]:
        t = profile.technical
        attrs = dict(t.additional_attributes or {})
        def one(value):
            if isinstance(value, list):
                return ", ".join(str(x) for x in value)
            return value
        attrs = {key: one(value) for key, value in attrs.items()}
        if t.operating_temperature_min_c is not None or t.operating_temperature_max_c is not None:
            attrs.setdefault("Operating Temperature", f"{t.operating_temperature_min_c} to {t.operating_temperature_max_c} C")
        if t.tolerance_percent is not None:
            attrs.setdefault("Tolerance", f"{t.tolerance_percent}%")
        if t.output_current_a is not None:
            attrs.setdefault("Current Rating", f"{t.output_current_a} A")
        if t.output_voltage_v is not None:
            attrs.setdefault("Voltage Rating", f"{t.output_voltage_v} V")
        return {
            "part_profile_schema_version": "1.0",
            "provider": "TME",
            "captured_at_utc": profile.provider_metadata.captured_at_utc,
            "manufacturer": profile.identity.manufacturer,
            "manufacturer_part_number": profile.identity.manufacturer_part_number,
            "provider_part_number": profile.identity.provider_part_number,
            "description": profile.identity.description,
            "detailed_description": profile.identity.detailed_description,
            "datasheet_url": profile.media.datasheet_url,
            "product_url": profile.media.product_url,
            "image_url": profile.media.primary_image_url,
            "lifecycle_status": profile.lifecycle.status,
            "rohs_status": profile.regulatory.rohs_status,
            "package": profile.technical.package,
            "mounting_type": profile.technical.mounting_type,
            "attributes": attrs,
            "compliance": {
                "REACH": profile.regulatory.reach_status,
                "ECCN": profile.regulatory.eccn,
                "HTSUS": profile.regulatory.hts_code,
            },
        }

    @staticmethod
    def _flat_commercial_profile(profile) -> dict[str, Any]:
        c = profile.commercial
        l = profile.logistics
        offers = list(c.offers or [])
        if not offers and (c.price_breaks or c.stock_quantity is not None):
            offers = [{
                "provider_part_number": profile.identity.provider_part_number,
                "pack_format": (l.pack_formats[0] if l.pack_formats else ""),
                "minimum_order_quantity": c.supplier_moq,
                "pack_quantity": l.listed_pack_quantity,
                "quantity_available": c.stock_quantity,
                "standard_price_breaks": list(c.price_breaks or []),
                "additional_charges": [],
            }]
        return {
            "provider": "TME",
            "provider_currency": c.currency or profile.provider_metadata.currency,
            "manufacturer_lead_weeks": c.manufacturer_lead_time_weeks,
            "product_quantity_available": c.stock_quantity,
            "offers": offers,
        }
