"""Map a Mouser Part Number Search Knowledge Base record to PDCPartProfile."""
from __future__ import annotations

import re
from typing import Any

from provider_profiles.pdc_part_profile import (
    AttributeEvidence,
    CommercialProfile,
    IdentityProfile,
    LifecycleProfile,
    LogisticsProfile,
    MediaProfile,
    PDCPartProfile,
    ProviderMetadata,
    RegulatoryProfile,
    TechnicalProfile,
)
from provider_profiles.normalization import normalise_pack_format, normalise_url, number

PROVIDER = "Mouser"
ENDPOINT = "Part_Number_Search"


def _unwrap(record: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    record = record or {}
    response = record.get("provider_response")
    metadata = record.get("knowledge_base_metadata")
    return (
        response if isinstance(response, dict) else record,
        metadata if isinstance(metadata, dict) else {},
    )


def _first_part(response: dict[str, Any]) -> dict[str, Any]:
    results = response.get("SearchResults") or response.get("searchResults") or {}
    parts = results.get("Parts") or results.get("parts") or []
    return parts[0] if parts and isinstance(parts[0], dict) else {}


def _named_values(items: Any, name_key: str, value_key: str) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for item in items or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get(name_key) or "").strip()
        value = str(item.get(value_key) or "").strip()
        if name and value:
            values.setdefault(name, []).append(value)
    return values


def _first(values: dict[str, list[str]], name: str) -> str:
    candidates = values.get(name) or []
    return candidates[0] if candidates else ""


def _int(value: Any) -> int | None:
    parsed = number(value)
    return int(parsed) if parsed is not None else None


def _float(value: Any) -> float | None:
    parsed = number(value)
    return float(parsed) if parsed is not None else None


def _price(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").replace(",", "")
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else None


def _days_to_weeks(value: Any) -> float | None:
    text = str(value or "").strip()
    parsed = _float(text)
    if parsed is None:
        return None
    if "day" in text.lower():
        return round(parsed / 7.0, 5)
    if "week" in text.lower():
        return parsed
    return None


def _pack_formats(attributes: dict[str, list[str]]) -> list[str]:
    result: list[str] = []
    for raw in attributes.get("Packaging") or []:
        normalised = normalise_pack_format(raw)
        # Keep Mouser's branded re-reeling service distinguishable without
        # leaking it into the PDCPartProfile field names.
        if raw.lower().replace(" ", "") == "mousereel":
            normalised = "MouseReel"
        if normalised and normalised not in result:
            result.append(normalised)
    return result


def _mousereel_charge(product_attributes: Any) -> dict[str, Any] | None:
    for item in product_attributes or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("AttributeValue") or "").lower().replace(" ", "") != "mousereel":
            continue
        raw = str(item.get("AttributeCost") or "")
        amount = _price(raw)
        if amount is None:
            return None
        return {
            "charge_type": "packaging_service",
            "description": "MouseReel service charge",
            "amount": amount,
            "currency": "EUR" if "€" in raw or "eur" in raw.lower() else "",
            "application": "per_order_line",
            "raw_description": raw,
        }
    return None


def build_mouser_pdc_part_profile(
    record: dict[str, Any],
    *,
    raw_references: dict[str, str] | None = None,
) -> PDCPartProfile:
    response, metadata = _unwrap(record)
    part = _first_part(response)
    captured_at = str(metadata.get("captured_at_utc") or "")

    product_attributes = part.get("ProductAttributes") or []
    attributes = _named_values(product_attributes, "AttributeName", "AttributeValue")
    compliance = _named_values(part.get("ProductCompliance"), "ComplianceName", "ComplianceValue")
    trade = _named_values(part.get("TradeCompliance"), "ComplianceName", "ComplianceValue")

    formats = _pack_formats(attributes)
    standard_pack = _int(_first(attributes, "Standard Pack Qty"))
    stock = _int(part.get("AvailabilityInStock"))
    if stock is None:
        stock = _int(part.get("Availability"))
    moq = _int(part.get("Min"))
    multiple = _int(part.get("Mult"))
    factory_stock = _int(part.get("FactoryStock"))

    raw_breaks = [item for item in (part.get("PriceBreaks") or []) if isinstance(item, dict)]
    currency = next((str(item.get("Currency") or "") for item in raw_breaks if item.get("Currency")), "")
    price_breaks: list[dict[str, Any]] = []
    for item in raw_breaks:
        quantity = _int(item.get("Quantity"))
        unit_price = _price(item.get("Price"))
        if quantity is None or unit_price is None:
            continue
        price_breaks.append(
            {
                "break_quantity": quantity,
                "unit_price": unit_price,
                "total_price": round(quantity * unit_price, 5),
                "provider_part_number": str(part.get("MouserPartNumber") or ""),
                "pack_format": "",
            }
        )

    extra_charge = _mousereel_charge(product_attributes)
    offer = {
        "provider_part_number": str(part.get("MouserPartNumber") or ""),
        "supplier": PROVIDER,
        "package_type_id": None,
        "package_type": "",
        "packaging_code": "",
        "pack_format": "",
        "available_pack_formats": formats,
        "minimum_order_quantity": moq,
        "order_multiple": multiple,
        "pack_quantity": standard_pack,
        "quantity_available": stock,
        "maximum_distribution_quantity": None,
        "marketplace": False,
        "tariff_active": None,
        "additional_charges": [extra_charge] if extra_charge else [],
        "standard_price_breaks": [
            {
                "break_quantity": item["break_quantity"],
                "unit_price": item["unit_price"],
                "total_price": item["total_price"],
            }
            for item in price_breaks
        ],
        "customer_price_breaks": [],
    }

    weight_kg = None
    unit_weight = part.get("UnitWeightKg")
    if isinstance(unit_weight, dict):
        weight_kg = _float(unit_weight.get("UnitWeight"))
    elif unit_weight is not None:
        weight_kg = _float(unit_weight)

    lifecycle_raw = str(part.get("LifecycleStatus") or "")
    suggested_replacement = str(part.get("SuggestedReplacement") or "")
    additional_compliance = {
        name: values[0]
        for name, values in compliance.items()
        if values and name not in {"ECCN", "USHTS"}
    }
    for name, values in trade.items():
        if values and name != "Country of Origin":
            additional_compliance[name] = values[0]

    profile = PDCPartProfile(
        identity=IdentityProfile(
            manufacturer=str(part.get("Manufacturer") or ""),
            manufacturer_part_number=str(part.get("ManufacturerPartNumber") or ""),
            provider_part_number=str(part.get("MouserPartNumber") or ""),
            description=str(part.get("Description") or ""),
            detailed_description=str(part.get("Description") or ""),
            category=str(part.get("Category") or ""),
        ),
        technical=TechnicalProfile(),
        commercial=CommercialProfile(
            currency=currency,
            supplier_moq=moq,
            order_multiple=multiple,
            stock_quantity=stock,
            manufacturer_public_quantity=factory_stock,
            manufacturer_lead_time_weeks=_days_to_weeks(part.get("LeadTime")),
            unit_price=price_breaks[0]["unit_price"] if price_breaks else None,
            price_breaks=price_breaks,
            offers=[offer] if part else [],
        ),
        logistics=LogisticsProfile(
            sales_unit="pcs",
            manufacturer_standard_pack_quantity=standard_pack,
            pack_formats=formats,
            weight_value=round(weight_kg * 1000.0, 9) if weight_kg is not None else None,
            weight_unit="g" if weight_kg is not None else "",
            deliveries=part.get("AvailabilityOnOrder"),
        ),
        lifecycle=LifecycleProfile(
            status=lifecycle_raw,
            provider_status=[lifecycle_raw] if lifecycle_raw else [],
            non_cancellable_non_returnable=None,
            suggested_replacement=suggested_replacement,
        ),
        regulatory=RegulatoryProfile(
            rohs_status=str(part.get("ROHSStatus") or ""),
            eccn=_first(compliance, "ECCN"),
            hts_code=_first(compliance, "USHTS"),
            country_of_origin=_first(trade, "Country of Origin"),
            additional_compliance=additional_compliance,
        ),
        media=MediaProfile(
            primary_image_url=normalise_url(part.get("ImagePath")),
            datasheet_url=normalise_url(part.get("DataSheetUrl")),
            product_url=normalise_url(part.get("ProductDetailUrl")),
        ),
        provider_metadata=ProviderMetadata(
            provider=PROVIDER,
            locale=str(metadata.get("locale") or ""),
            currency=currency or str(metadata.get("currency") or ""),
            request_context=str(metadata.get("source_mode") or ""),
            captured_at_utc=captured_at,
            source_endpoints=[ENDPOINT],
        ),
        raw_references=raw_references or {},
    )

    def evidence(path: str, raw_name: str, raw_value: Any, normalised_value: Any, unit: str = "") -> None:
        profile.provenance[path] = AttributeEvidence(
            provider=PROVIDER,
            endpoint=ENDPOINT,
            raw_name=raw_name,
            raw_value=raw_value,
            normalised_value=normalised_value,
            unit=unit,
            captured_at_utc=captured_at,
        )

    evidence("identity.manufacturer", "Manufacturer", part.get("Manufacturer"), profile.identity.manufacturer)
    evidence("identity.manufacturer_part_number", "ManufacturerPartNumber", part.get("ManufacturerPartNumber"), profile.identity.manufacturer_part_number)
    evidence("commercial.stock_quantity", "AvailabilityInStock", part.get("AvailabilityInStock"), stock, "pcs")
    evidence("commercial.price_breaks", "PriceBreaks", raw_breaks, price_breaks, currency)
    evidence("commercial.offers", "ProductAttributes + PriceBreaks", {"ProductAttributes": product_attributes, "PriceBreaks": raw_breaks}, [offer] if part else [], currency)
    evidence("commercial.manufacturer_lead_time_weeks", "LeadTime", part.get("LeadTime"), profile.commercial.manufacturer_lead_time_weeks, "weeks")
    evidence("logistics.manufacturer_standard_pack_quantity", "Standard Pack Qty", _first(attributes, "Standard Pack Qty"), standard_pack, "pcs")
    evidence("regulatory.rohs_status", "ROHSStatus", part.get("ROHSStatus"), profile.regulatory.rohs_status)
    evidence("regulatory.eccn", "ProductCompliance.ECCN", _first(compliance, "ECCN"), profile.regulatory.eccn)
    evidence("regulatory.country_of_origin", "TradeCompliance.Country of Origin", _first(trade, "Country of Origin"), profile.regulatory.country_of_origin)
    return profile


# Compatibility alias during the 4.2.5 transition.
build_mouser_provider_part_profile = build_mouser_pdc_part_profile
