"""Provider-neutral commercial data model.

The provider response remains the authoritative captured evidence. This module
creates a normalised commercial profile for workbook generation and later PIE
analysis without altering the source response.

Schema 1.2 introduces ``offers`` as the canonical collection. The legacy
``variations`` key is retained as a compatibility alias during the v0.2.4
transition so existing workbook code continues to behave exactly as before.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable


COMMERCIAL_PROFILE_SCHEMA_VERSION = "1.2"


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
    """Return a concise provider-neutral pack format while preserving raw text."""
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
        breaks.append(
            {
                "break_quantity": quantity,
                "unit_price": unit_price,
                "total_price": total_price,
            }
        )

    def sort_key(item: dict[str, Any]) -> tuple[int, float | str]:
        value = item.get("break_quantity")
        try:
            return (0, float(value))
        except (TypeError, ValueError):
            return (1, str(value or ""))

    return sorted(breaks, key=sort_key)


def commercial_offers(profile: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return all offers from current or legacy commercial profile structures."""
    if not isinstance(profile, dict):
        return []
    values = profile.get("offers")
    if not isinstance(values, list):
        values = profile.get("variations")
    return [item for item in (values or []) if isinstance(item, dict)]


def ensure_current_commercial_profile(profile: dict[str, Any] | None) -> dict[str, Any]:
    """Upgrade a stored profile in memory while preserving backwards compatibility."""
    upgraded = deepcopy(profile) if isinstance(profile, dict) else {}
    offers = commercial_offers(upgraded)
    upgraded["commercial_profile_schema_version"] = COMMERCIAL_PROFILE_SCHEMA_VERSION
    upgraded["offer_count"] = len(offers)
    upgraded["offers"] = offers
    # Compatibility alias for v0.2.3 workbook code. Remove in a later schema migration.
    upgraded["variation_count"] = len(offers)
    upgraded["variations"] = offers
    return upgraded


def _build_offer(variation: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    package_type = _ci(variation, "PackageType")
    package_name = _name(package_type)
    standard_pricing = _price_breaks(_ci(variation, "StandardPricing"))
    customer_pricing = _price_breaks(_ci(variation, "MyPricing"))

    digireel_fee = _ci(variation, "DigiReelFee")
    additional_charges: list[dict[str, Any]] = []
    if digireel_fee not in (None, "", 0, 0.0, "0", "0.0"):
        additional_charges.append(
            {
                "charge_type": "packaging_service",
                "description": "Digi-Reel service charge",
                "amount": digireel_fee,
                "currency": str(metadata.get("currency") or ""),
                "application": "per_order_line",
            }
        )

    return {
        "provider_part_number": str(_ci(variation, "DigiKeyProductNumber") or ""),
        "supplier": _name(_ci(variation, "Supplier")),
        "package_type_id": _ci(package_type, "Id") if isinstance(package_type, dict) else None,
        "package_type": package_name,
        "packaging_code": package_name,
        "pack_format": normalise_pack_format(package_name),
        "minimum_order_quantity": _ci(variation, "MinimumOrderQuantity"),
        "pack_quantity": _ci(variation, "StandardPackage"),
        "quantity_available": _ci(
            variation,
            "QuantityAvailableforPackageType",
            "QuantityAvailableForPackageType",
            "QuantityAvailable",
        ),
        "maximum_distribution_quantity": _ci(variation, "MaxQuantityForDistribution"),
        "marketplace": _ci(variation, "MarketPlace"),
        "tariff_active": _ci(variation, "TariffActive"),
        "additional_charges": additional_charges,
        "standard_price_breaks": standard_pricing,
        "customer_price_breaks": customer_pricing,
    }


def build_commercial_profile(
    provider_response: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a provider-neutral commercial profile from a DigiKey response."""
    metadata = metadata or {}
    product = _product(provider_response)
    offers = [
        _build_offer(variation, metadata)
        for variation in product.get("ProductVariations") or []
        if isinstance(variation, dict)
    ]

    offers.sort(
        key=lambda item: (
            str(item.get("pack_format") or ""),
            str(item.get("provider_part_number") or ""),
        )
    )

    profile = {
        "commercial_profile_schema_version": COMMERCIAL_PROFILE_SCHEMA_VERSION,
        "provider": str(metadata.get("provider") or "DigiKey"),
        "provider_currency": str(metadata.get("currency") or ""),
        "captured_at_utc": str(metadata.get("captured_at_utc") or ""),
        "manufacturer_part_number": str(
            _ci(product, "ManufacturerProductNumber", "ManufacturerPartNumber") or ""
        ),
        "product_quantity_available": _ci(product, "QuantityAvailable"),
        "manufacturer_public_quantity": _ci(product, "ManufacturerPublicQuantity"),
        "manufacturer_lead_weeks": _ci(product, "ManufacturerLeadWeeks"),
        "product_unit_price": _ci(product, "UnitPrice"),
        "offer_count": len(offers),
        "offers": offers,
    }
    return ensure_current_commercial_profile(profile)
