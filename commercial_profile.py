"""Provider-neutral commercial data model.

The provider response remains the authoritative captured evidence. This module
creates a normalised commercial profile for workbook generation and later PIE
analysis without altering the source response.
"""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any


COMMERCIAL_PROFILE_SCHEMA_VERSION = "1.3"


def _ci(data: dict[str, Any] | None, *names: str) -> Any:
    if not isinstance(data, dict):
        return None
    lookup = {str(key).lower(): value for key, value in data.items()}
    for name in names:
        if name.lower() in lookup:
            return lookup[name.lower()]
    return None


def _name(value: Any) -> str:
    if isinstance(value, dict):
        return str(_ci(value, "Name", "Value", "Description") or "")
    return str(value or "")


def _product(provider_response: dict[str, Any]) -> dict[str, Any]:
    product = provider_response.get("Product") or provider_response.get("product")
    return product if isinstance(product, dict) else provider_response


def normalise_pack_format(package_name: str) -> str:
    text = str(package_name or "").strip()
    lowered = text.lower()
    if "digi-reel" in lowered or "digireel" in lowered:
        return "DigiReel"
    if "cut tape" in lowered:
        return "Cut Tape"
    if "tape & reel" in lowered or "tape and reel" in lowered or lowered == "reel":
        return "Reel"
    if "tube" in lowered:
        return "Tube"
    if "tray" in lowered:
        return "Tray"
    if "bag" in lowered:
        return "Bag"
    if "box" in lowered:
        return "Box"
    if "bulk" in lowered or "loose" in lowered:
        return "Loose"
    return text


def _number(value: Any) -> Any:
    if isinstance(value, (int, float)):
        return value
    text = str(value or "").strip().replace(",", "")
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if not match:
        return value
    number = float(match.group(0))
    return int(number) if number.is_integer() else number


def _currency_from_price(value: Any) -> str:
    text = str(value or "")
    if "€" in text:
        return "EUR"
    if "£" in text:
        return "GBP"
    if "$" in text:
        return "USD"
    return ""


def _price_breaks(items: Any) -> list[dict[str, Any]]:
    breaks: list[dict[str, Any]] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        quantity = _ci(item, "BreakQuantity", "Quantity")
        unit_price = _ci(item, "UnitPrice", "Price")
        total_price = _ci(item, "TotalPrice")
        if quantity in (None, "") and unit_price in (None, ""):
            continue
        breaks.append({
            "break_quantity": _number(quantity),
            "unit_price": _number(unit_price),
            "total_price": _number(total_price) if total_price not in (None, "") else None,
        })
    return sorted(breaks, key=lambda item: (0, float(item["break_quantity"])) if isinstance(item.get("break_quantity"), (int, float)) else (1, str(item.get("break_quantity") or "")))


def commercial_offers(profile: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(profile, dict):
        return []
    values = profile.get("offers")
    if not isinstance(values, list):
        values = profile.get("variations")
    return [item for item in (values or []) if isinstance(item, dict)]


def ensure_current_commercial_profile(profile: dict[str, Any] | None) -> dict[str, Any]:
    upgraded = deepcopy(profile) if isinstance(profile, dict) else {}
    offers = commercial_offers(upgraded)
    upgraded["commercial_profile_schema_version"] = COMMERCIAL_PROFILE_SCHEMA_VERSION
    upgraded["offer_count"] = len(offers)
    upgraded["offers"] = offers
    upgraded["variation_count"] = len(offers)
    upgraded["variations"] = offers
    return upgraded


def _build_digikey_offer(variation: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    package_type = _ci(variation, "PackageType")
    package_name = _name(package_type)
    additional_charges: list[dict[str, Any]] = []
    digireel_fee = _ci(variation, "DigiReelFee")
    if digireel_fee not in (None, "", 0, 0.0, "0", "0.0"):
        additional_charges.append({
            "charge_type": "packaging_service",
            "description": "Digi-Reel service charge",
            "amount": digireel_fee,
            "currency": str(metadata.get("currency") or ""),
            "application": "per_order_line",
        })
    return {
        "provider_part_number": str(_ci(variation, "DigiKeyProductNumber") or ""),
        "supplier": _name(_ci(variation, "Supplier")),
        "package_type_id": _ci(package_type, "Id") if isinstance(package_type, dict) else None,
        "package_type": package_name,
        "packaging_code": package_name,
        "pack_format": normalise_pack_format(package_name),
        "minimum_order_quantity": _ci(variation, "MinimumOrderQuantity"),
        "pack_quantity": _ci(variation, "StandardPackage"),
        "quantity_available": _ci(variation, "QuantityAvailableforPackageType", "QuantityAvailableForPackageType", "QuantityAvailable"),
        "maximum_distribution_quantity": _ci(variation, "MaxQuantityForDistribution"),
        "marketplace": _ci(variation, "MarketPlace"),
        "tariff_active": _ci(variation, "TariffActive"),
        "additional_charges": additional_charges,
        "standard_price_breaks": _price_breaks(_ci(variation, "StandardPricing")),
        "customer_price_breaks": _price_breaks(_ci(variation, "MyPricing")),
    }


def _build_digikey_profile(provider_response: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    product = _product(provider_response)
    offers = [_build_digikey_offer(item, metadata) for item in product.get("ProductVariations") or [] if isinstance(item, dict)]
    offers.sort(key=lambda item: (str(item.get("pack_format") or ""), str(item.get("provider_part_number") or "")))
    return {
        "commercial_profile_schema_version": COMMERCIAL_PROFILE_SCHEMA_VERSION,
        "provider": str(metadata.get("provider") or "DigiKey"),
        "provider_currency": str(metadata.get("currency") or ""),
        "captured_at_utc": str(metadata.get("captured_at_utc") or ""),
        "manufacturer_part_number": str(_ci(product, "ManufacturerProductNumber", "ManufacturerPartNumber") or ""),
        "product_quantity_available": _ci(product, "QuantityAvailable"),
        "manufacturer_public_quantity": _ci(product, "ManufacturerPublicQuantity"),
        "manufacturer_lead_weeks": _ci(product, "ManufacturerLeadWeeks"),
        "product_unit_price": _ci(product, "UnitPrice"),
        "offers": offers,
    }


def _mouser_parts(provider_response: dict[str, Any]) -> list[dict[str, Any]]:
    results = _ci(provider_response, "SearchResults") or {}
    return [part for part in (_ci(results, "Parts") or []) if isinstance(part, dict)]


def _normalise_mpn(value: Any) -> str:
    return "".join(character for character in str(value or "").upper() if character.isalnum())


def _select_mouser_parts(provider_response: dict[str, Any], requested_mpn: str) -> list[dict[str, Any]]:
    parts = _mouser_parts(provider_response)
    requested = _normalise_mpn(requested_mpn)
    exact = [part for part in parts if _normalise_mpn(_ci(part, "ManufacturerPartNumber")) == requested]
    return exact or parts


def _mouser_currency(parts: list[dict[str, Any]], metadata: dict[str, Any]) -> str:
    configured = str(metadata.get("currency") or "")
    if configured:
        return configured
    for part in parts:
        for item in _ci(part, "PriceBreaks") or []:
            if not isinstance(item, dict):
                continue
            currency = str(_ci(item, "Currency") or "").strip().upper()
            if currency:
                return currency
            inferred = _currency_from_price(_ci(item, "Price"))
            if inferred:
                return inferred
    return ""


def _build_mouser_profile(provider_response: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    parts = _select_mouser_parts(provider_response, str(metadata.get("input_mpn") or ""))
    currency = _mouser_currency(parts, metadata)
    offers: list[dict[str, Any]] = []
    for part in parts:
        packaging = _name(_ci(part, "Packaging", "PackagingChoice"))
        offers.append({
            "provider_part_number": _name(_ci(part, "MouserPartNumber")),
            "supplier": "Mouser",
            "package_type_id": None,
            "package_type": packaging,
            "packaging_code": packaging,
            "pack_format": normalise_pack_format(packaging),
            "minimum_order_quantity": _number(_ci(part, "Min", "MinimumOrderQuantity")),
            "pack_quantity": _number(_ci(part, "Mult", "PackageQuantity", "StandardPackage")),
            "quantity_available": _number(_ci(part, "AvailabilityInStock", "Availability")),
            "maximum_distribution_quantity": None,
            "marketplace": False,
            "tariff_active": None,
            "additional_charges": [],
            "standard_price_breaks": _price_breaks(_ci(part, "PriceBreaks")),
            "customer_price_breaks": [],
        })
    primary = parts[0] if parts else {}
    profile = {
        "commercial_profile_schema_version": COMMERCIAL_PROFILE_SCHEMA_VERSION,
        "provider": str(metadata.get("provider") or "Mouser"),
        "provider_currency": currency,
        "captured_at_utc": str(metadata.get("captured_at_utc") or ""),
        "manufacturer_part_number": _name(_ci(primary, "ManufacturerPartNumber")),
        "product_quantity_available": _number(_ci(primary, "AvailabilityInStock", "Availability")),
        "manufacturer_public_quantity": _number(_ci(primary, "FactoryStock")),
        "manufacturer_lead_weeks": _name(_ci(primary, "LeadTime")),
        "product_unit_price": None,
        "offers": offers,
    }
    if offers and offers[0]["standard_price_breaks"]:
        profile["product_unit_price"] = offers[0]["standard_price_breaks"][0]["unit_price"]
    return profile


def build_commercial_profile(provider_response: dict[str, Any], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata = metadata or {}
    provider = str(metadata.get("provider") or "").strip().lower()
    if provider == "mouser" or _ci(provider_response, "SearchResults") is not None:
        return ensure_current_commercial_profile(_build_mouser_profile(provider_response, metadata))
    return ensure_current_commercial_profile(_build_digikey_profile(provider_response, metadata))
