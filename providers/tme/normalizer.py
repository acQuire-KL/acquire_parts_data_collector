"""Map TME Search, Data and Parameters responses to PDCPartProfile."""

from __future__ import annotations

from typing import Any

from provider_profiles.pdc_part_profile import (
    AttributeEvidence,
    CommercialProfile,
    IdentityProfile,
    LogisticsProfile,
    MediaProfile,
    LifecycleProfile,
    RegulatoryProfile,
    ProviderMetadata,
    PDCPartProfile,
    TechnicalProfile,
)
from provider_profiles.normalization import (
    normalise_mounting,
    normalise_pack_format,
    normalise_package,
    normalise_url,
    number,
    range_values,
)

PROVIDER = "TME"


def _unwrap(record: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    record = record or {}
    response = record.get("provider_response")
    metadata = record.get("knowledge_base_metadata")
    return (
        response if isinstance(response, dict) else record,
        metadata if isinstance(metadata, dict) else {},
    )


def _elements(payload: dict[str, Any], *path: str) -> list[dict[str, Any]]:
    value: Any = payload
    for key in path:
        if not isinstance(value, dict):
            return []
        value = value.get(key)
    if isinstance(value, dict):
        value = value.get("elements")
    return [item for item in (value or []) if isinstance(item, dict)]


def _first(items: list[dict[str, Any]]) -> dict[str, Any]:
    return items[0] if items else {}


def _parameter_map(payload: dict[str, Any]) -> dict[str, list[str]]:
    item = _first(_elements(payload, "data"))
    parameters = _elements(item, "parameters")
    result: dict[str, list[str]] = {}
    for parameter in parameters:
        name = str(parameter.get("name") or "").strip()
        values = [
            str(value.get("value") or "").strip()
            for value in parameter.get("values") or []
            if isinstance(value, dict) and str(value.get("value") or "").strip()
        ]
        if name:
            result[name] = values
    return result


def _one(parameters: dict[str, list[str]], name: str) -> str:
    values = parameters.get(name) or []
    return values[0] if values else ""


def build_tme_pdc_part_profile(
    search_record: dict[str, Any],
    data_record: dict[str, Any],
    parameters_record: dict[str, Any],
    *,
    raw_references: dict[str, str] | None = None,
) -> PDCPartProfile:
    search, search_meta = _unwrap(search_record)
    data, data_meta = _unwrap(data_record)
    parameters_payload, parameters_meta = _unwrap(parameters_record)

    search_item = _first(_elements(search, "data", "products"))
    data_item = _first(_elements(data, "data"))
    parameters = _parameter_map(parameters_payload)

    manufacturer_obj = search_item.get("manufacturer") or {}
    manufacturer = str(
        (manufacturer_obj.get("name") if isinstance(manufacturer_obj, dict) else manufacturer_obj)
        or _one(parameters, "Manufacturer")
    ).strip()
    mpn = str(search_item.get("symbol") or data_item.get("symbol") or "").strip()

    category = search_item.get("category") or {}
    category_name = str(category.get("name") if isinstance(category, dict) else category or "")
    assets = search_item.get("assets") or {}
    primary_photo = assets.get("primary_photo") if isinstance(assets, dict) else {}
    primary_photo = primary_photo if isinstance(primary_photo, dict) else {}

    package_raw = _one(parameters, "Case")
    mounting_raw = _one(parameters, "Mounting")
    output_voltage_raw = _one(parameters, "Output voltage")
    output_current_raw = _one(parameters, "Output current")
    input_voltage_raw = _one(parameters, "Input voltage")
    temperature_raw = _one(parameters, "Operating temperature")
    tolerance_raw = _one(parameters, "Tolerance")
    standard_pack_raw = _one(parameters, "Manufacturer standard package")

    input_min, input_max = range_values(input_voltage_raw)
    temp_min, temp_max = range_values(temperature_raw, target_unit="C")

    prices = data_item.get("prices") or {}
    prices = prices if isinstance(prices, dict) else {}
    price_breaks = [
        {
            "break_quantity": number(item.get("amount")),
            "unit_price": number(item.get("price")),
            "special": bool(item.get("special", False)),
        }
        for item in _elements(prices)
    ]
    price_breaks.sort(key=lambda item: item.get("break_quantity") or 0)

    tax = prices.get("tax") or {}
    tax = tax if isinstance(tax, dict) else {}
    packing = _elements(search_item, "packing")
    listed_pack_quantity = number(packing[0].get("amount")) if packing else None
    pack_formats = [normalise_pack_format(value) for value in parameters.get("Kind of package", [])]
    pack_formats = list(dict.fromkeys(value for value in pack_formats if value))

    captured_values = [
        str(meta.get("captured_at_utc") or "")
        for meta in (search_meta, data_meta, parameters_meta)
        if meta.get("captured_at_utc")
    ]
    captured_at = max(captured_values) if captured_values else ""
    locale = str(search_meta.get("locale") or data_meta.get("locale") or parameters_meta.get("locale") or "")
    request_context = str(
        search_meta.get("request_context")
        or data_meta.get("request_context")
        or parameters_meta.get("request_context")
        or ""
    )

    profile = PDCPartProfile(
        identity=IdentityProfile(
            manufacturer=manufacturer,
            manufacturer_part_number=mpn,
            provider_part_number=mpn,
            description=str(search_item.get("description") or ""),
            detailed_description=str(search_item.get("description") or ""),
            category=category_name,
            ean=str(search_item.get("ean") or ""),
        ),
        technical=TechnicalProfile(
            component_type=_one(parameters, "Type of integrated circuit"),
            regulator_type=parameters.get("Kind of voltage regulator", []),
            manufacturer_series=_one(parameters, "Manufacturer series"),
            package=normalise_package(package_raw),
            mounting_type=normalise_mounting(mounting_raw),
            output_voltage_v=float(number(output_voltage_raw)) if number(output_voltage_raw) is not None else None,
            output_current_a=float(number(output_current_raw)) if number(output_current_raw) is not None else None,
            input_voltage_min_v=input_min,
            input_voltage_max_v=input_max,
            operating_temperature_min_c=temp_min,
            operating_temperature_max_c=temp_max,
            tolerance_percent=float(number(tolerance_raw)) if number(tolerance_raw) is not None else None,
            channel_count=int(number(_one(parameters, "Number of channels"))) if number(_one(parameters, "Number of channels")) is not None else None,
            additional_attributes={
                key: values for key, values in parameters.items()
                if key not in {
                    "Manufacturer", "Type of integrated circuit", "Kind of voltage regulator",
                    "Output voltage", "Output current", "Case", "Mounting",
                    "Manufacturer series", "Kind of package", "Operating temperature",
                    "Tolerance", "Number of channels", "Input voltage",
                    "Manufacturer standard package",
                }
            },
        ),
        commercial=CommercialProfile(
            currency=str(prices.get("currency") or data_meta.get("currency") or ""),
            price_type=str(prices.get("type") or ""),
            tax_type=str(tax.get("type") or ""),
            tax_rate_percent=float(number(tax.get("rate"))) if number(tax.get("rate")) is not None else None,
            supplier_moq=number(search_item.get("minimal_amount")),
            order_multiple=number(search_item.get("multiples")),
            stock_quantity=number(data_item.get("stock_quantity")),
            price_breaks=price_breaks,
        ),
        logistics=LogisticsProfile(
            sales_unit=str((search_item.get("unit") or {}).get("short_name") or "") if isinstance(search_item.get("unit"), dict) else "",
            listed_pack_quantity=listed_pack_quantity,
            manufacturer_standard_pack_quantity=number(standard_pack_raw),
            pack_formats=pack_formats,
            weight_value=float(number((search_item.get("weight") or {}).get("value"))) if isinstance(search_item.get("weight"), dict) and number((search_item.get("weight") or {}).get("value")) is not None else None,
            weight_unit=str((search_item.get("weight") or {}).get("unit") or "") if isinstance(search_item.get("weight"), dict) else "",
            deliveries=data_item.get("deliveries"),
        ),
        lifecycle=LifecycleProfile(provider_status=[str(value) for value in search_item.get("product_status") or []]),
        regulatory=RegulatoryProfile(),
        media=MediaProfile(
            primary_image_url=normalise_url(primary_photo.get("prime")),
            thumbnail_url=normalise_url(primary_photo.get("thumbnail")),
            high_resolution_image_url=normalise_url(primary_photo.get("high_resolution")),
        ),
        provider_metadata=ProviderMetadata(
            provider=PROVIDER,
            locale=locale,
            currency=str(prices.get("currency") or data_meta.get("currency") or ""),
            request_context=request_context,
            captured_at_utc=captured_at,
            source_endpoints=["Product_Search", "Product_Data", "Product_Parameters"],
        ),
        raw_references=raw_references or {},
    )

    def evidence(path: str, endpoint: str, raw_name: str, raw_value: Any, normalised_value: Any, unit: str = "") -> None:
        profile.provenance[path] = AttributeEvidence(
            provider=PROVIDER,
            endpoint=endpoint,
            raw_name=raw_name,
            raw_value=raw_value,
            normalised_value=normalised_value,
            unit=unit,
            captured_at_utc=captured_at,
        )

    evidence("identity.manufacturer", "Product_Search", "manufacturer.name", manufacturer, manufacturer)
    evidence("identity.manufacturer_part_number", "Product_Search", "symbol", mpn, mpn)
    evidence("identity.description", "Product_Search", "description", search_item.get("description"), profile.identity.description)
    evidence("technical.package", "Product_Parameters", "Case", package_raw, profile.technical.package)
    evidence("technical.mounting_type", "Product_Parameters", "Mounting", mounting_raw, profile.technical.mounting_type)
    evidence("technical.output_voltage_v", "Product_Parameters", "Output voltage", output_voltage_raw, profile.technical.output_voltage_v, "V")
    evidence("technical.output_current_a", "Product_Parameters", "Output current", output_current_raw, profile.technical.output_current_a, "A")
    evidence("technical.input_voltage", "Product_Parameters", "Input voltage", input_voltage_raw, {"min": input_min, "max": input_max}, "V")
    evidence("technical.operating_temperature", "Product_Parameters", "Operating temperature", temperature_raw, {"min": temp_min, "max": temp_max}, "°C")
    evidence("commercial.supplier_moq", "Product_Search", "minimal_amount", search_item.get("minimal_amount"), profile.commercial.supplier_moq, profile.logistics.sales_unit)
    evidence("commercial.stock_quantity", "Product_Data", "stock_quantity", data_item.get("stock_quantity"), profile.commercial.stock_quantity, profile.logistics.sales_unit)
    evidence("commercial.price_breaks", "Product_Data", "prices.elements", prices.get("elements"), profile.commercial.price_breaks, profile.commercial.currency)
    evidence("logistics.listed_pack_quantity", "Product_Search", "packing.elements[0].amount", packing[0].get("amount") if packing else None, listed_pack_quantity, profile.logistics.sales_unit)
    evidence("logistics.manufacturer_standard_pack_quantity", "Product_Parameters", "Manufacturer standard package", standard_pack_raw, profile.logistics.manufacturer_standard_pack_quantity, profile.logistics.sales_unit)

    return profile


# Backward-compatible alias; remove only in a future breaking release.
build_tme_provider_part_profile = build_tme_pdc_part_profile
