"""Provider-neutral identity, documentation and engineering profile.

The raw provider response remains the captured evidence.  This module creates a
small common profile which the workbook and PIE can consume without knowing the
shape of each distributor API.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PART_PROFILE_SCHEMA_VERSION = "1.0"


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


def _normalise_mpn(value: Any) -> str:
    return "".join(character for character in str(value or "").upper() if character.isalnum())


def _mouser_parts(provider_response: dict[str, Any]) -> list[dict[str, Any]]:
    results = _ci(provider_response, "SearchResults") or {}
    parts = _ci(results, "Parts") or []
    return [part for part in parts if isinstance(part, dict)]


def _select_mouser_part(provider_response: dict[str, Any], requested_mpn: str = "") -> dict[str, Any]:
    parts = _mouser_parts(provider_response)
    requested = _normalise_mpn(requested_mpn)
    if requested:
        for part in parts:
            returned = _normalise_mpn(_ci(part, "ManufacturerPartNumber"))
            if returned == requested:
                return part
    return parts[0] if parts else {}


def _attribute_map(items: Any, *, name_fields: tuple[str, ...], value_fields: tuple[str, ...]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in items or []:
        if not isinstance(item, dict):
            continue
        key = _name(_ci(item, *name_fields)).strip()
        value = _name(_ci(item, *value_fields)).strip()
        if key:
            result[key] = value
    return result


def _digikey_profile(provider_response: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    product = _ci(provider_response, "Product")
    if not isinstance(product, dict):
        product = provider_response
    description = _ci(product, "Description")
    if isinstance(description, dict):
        short_description = _name(_ci(description, "ProductDescription", "Description"))
        detailed_description = _name(
            _ci(description, "DetailedDescription", "DetailedProductDescription")
        )
    else:
        short_description = _name(description)
        detailed_description = _name(_ci(product, "DetailedDescription"))

    attributes = _attribute_map(
        _ci(product, "Parameters") or [],
        name_fields=("ParameterText", "Parameter", "Name"),
        value_fields=("ValueText", "Value"),
    )
    manufacturer = _ci(product, "Manufacturer")
    return {
        "part_profile_schema_version": PART_PROFILE_SCHEMA_VERSION,
        "provider": str(metadata.get("provider") or "DigiKey"),
        "captured_at_utc": str(metadata.get("captured_at_utc") or ""),
        "manufacturer": _name(manufacturer),
        "manufacturer_part_number": _name(
            _ci(product, "ManufacturerProductNumber", "ManufacturerPartNumber")
        ),
        "provider_part_number": _name(_ci(product, "DigiKeyProductNumber")),
        "description": short_description,
        "detailed_description": detailed_description,
        "datasheet_url": _name(_ci(product, "DatasheetUrl", "DatasheetURL")),
        "product_url": _name(_ci(product, "ProductUrl", "ProductURL")),
        "image_url": _name(_ci(product, "PhotoUrl", "PrimaryPhoto", "ImageUrl")),
        "lifecycle_status": _name(_ci(product, "ProductStatus", "Status")),
        "rohs_status": _name(_ci(product, "RoHsStatus", "RoHSStatus")),
        "package": attributes.get("Package / Case", ""),
        "mounting_type": attributes.get("Mounting Type", ""),
        "attributes": attributes,
        "compliance": {},
    }


def _mouser_profile(provider_response: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    part = _select_mouser_part(provider_response, str(metadata.get("input_mpn") or ""))
    attributes = _attribute_map(
        _ci(part, "ProductAttributes") or [],
        name_fields=("AttributeName", "Name"),
        value_fields=("AttributeValue", "Value"),
    )
    compliance = _attribute_map(
        _ci(part, "ProductCompliance") or [],
        name_fields=("ComplianceName", "Name"),
        value_fields=("ComplianceValue", "Value"),
    )
    package = (
        attributes.get("Package / Case")
        or attributes.get("Package")
        or attributes.get("Case/Package")
        or ""
    )
    mounting = attributes.get("Mounting Style") or attributes.get("Mounting Type") or ""
    return {
        "part_profile_schema_version": PART_PROFILE_SCHEMA_VERSION,
        "provider": str(metadata.get("provider") or "Mouser"),
        "captured_at_utc": str(metadata.get("captured_at_utc") or ""),
        "manufacturer": _name(_ci(part, "Manufacturer")),
        "manufacturer_part_number": _name(_ci(part, "ManufacturerPartNumber")),
        "provider_part_number": _name(_ci(part, "MouserPartNumber")),
        "description": _name(_ci(part, "Description")),
        "detailed_description": _name(_ci(part, "Description")),
        "datasheet_url": _name(_ci(part, "DataSheetUrl", "DatasheetUrl")),
        "product_url": _name(_ci(part, "ProductDetailUrl", "ProductUrl")),
        "image_url": _name(_ci(part, "ImagePath", "ImageUrl")),
        "lifecycle_status": _name(_ci(part, "LifecycleStatus")),
        "rohs_status": _name(_ci(part, "ROHSStatus", "RoHSStatus")),
        "package": package,
        "mounting_type": mounting,
        "attributes": attributes,
        "compliance": compliance,
    }


def build_part_profile(
    provider_response: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = metadata or {}
    provider = str(metadata.get("provider") or "").strip().lower()
    if provider == "mouser" or _ci(provider_response, "SearchResults") is not None:
        return _mouser_profile(provider_response, metadata)
    return _digikey_profile(provider_response, metadata)


def ensure_current_part_profile(profile: dict[str, Any] | None) -> dict[str, Any]:
    upgraded = deepcopy(profile) if isinstance(profile, dict) else {}
    upgraded["part_profile_schema_version"] = PART_PROFILE_SCHEMA_VERSION
    upgraded.setdefault("attributes", {})
    upgraded.setdefault("compliance", {})
    return upgraded
