import argparse
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook, load_workbook

from config import Settings, MouserSettings
from providers import ProviderManager
from providers.digikey import DigiKeyProvider
from providers.mouser import MouserProvider
from manufacturer_resolver import names_equivalent, resolve_manufacturer
from excel_formatter import add_group_headers, format_reference_sheet, format_review_sheet
from workbook_layout import WorkbookColumn, column_keys, display_headings, enriched_parts_columns
from commercial_profile import commercial_offers
from knowledge_base_manager import KnowledgeBaseManager
from multi_provider_summary import (
    ProviderEvidence, engineering_confirmation, evidence_status, merged_value,
    provider_availability, provider_identity_match,
)

APP_VERSION = "0.2.7"

MFG = {"manufacturer", "mfg", "mfr", "manufacturer name"}
MPN = {"mpn", "manufacturer part number", "mfg part number", "manufacturer_part_number"}


def clean(value):
    return " ".join(str(value or "").strip().lower().replace("_", " ").split())


def norm(value):
    return "".join(c for c in str(value or "").upper() if c.isalnum())


def ci(data, *names):
    if not isinstance(data, dict):
        return ""
    lookup = {str(k).lower(): v for k, v in data.items()}
    for item in names:
        if item.lower() in lookup:
            return lookup[item.lower()]
    return ""


def name(value):
    if isinstance(value, dict):
        return str(ci(value, "Name", "Value", "ProductDescription", "Description") or "")
    return str(value or "")


def product(payload):
    return payload.get("Product") or payload.get("product") or payload


def descriptions(p):
    description = ci(p, "Description")
    if isinstance(description, dict):
        return (
            str(ci(description, "ProductDescription", "Description") or ""),
            str(ci(description, "DetailedDescription", "DetailedProductDescription") or ""),
        )
    return name(description), name(ci(p, "DetailedDescription", "DetailedProductDescription"))


def params(p):
    result = {}
    for item in (p.get("Parameters") or p.get("parameters") or []):
        if isinstance(item, dict):
            key = name(ci(item, "ParameterText", "Parameter", "Name")).strip().lower()
            value = name(ci(item, "ValueText", "Value"))
            if key:
                result[key] = value
    return result


def parameter_value(parameters, *aliases):
    for alias in aliases:
        value = parameters.get(alias.lower(), "")
        if value not in ("", "-"):
            return value
    return ""


def category_names(category):
    """Return top-level category and the deepest available child category."""
    if not isinstance(category, dict):
        return "", ""
    top = str(category.get("Name") or "")
    deepest = top
    current = category
    while isinstance(current, dict):
        children = current.get("ChildCategories") or []
        if not children or not isinstance(children[0], dict):
            break
        current = children[0]
        deepest = str(current.get("Name") or deepest)
    return top, deepest


def normalise_url(value):
    text = str(value or "").strip()
    if text.startswith("//"):
        return "https:" + text
    return text


def flatten(value, prefix=""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from flatten(item, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from flatten(item, f"{prefix}[{index}]")
    else:
        yield prefix, value


def locate_columns(headers):
    manufacturer_column = mpn_column = None
    for index, header in enumerate(headers, 1):
        value = clean(header)
        if value in MFG:
            manufacturer_column = index
        if value in MPN:
            mpn_column = index
    if not manufacturer_column or not mpn_column:
        raise ValueError(f"Could not identify Manufacturer and MPN columns: {headers}")
    return manufacturer_column, mpn_column


def enriched_columns():
    """Return the configured Enriched Parts workbook layout."""
    return enriched_parts_columns()


def first_variation_value(p, *names):
    variations = p.get("ProductVariations") or []
    for variation in variations:
        if not isinstance(variation, dict):
            continue
        value = ci(variation, *names)
        if value not in ("", None):
            return value
    return ""




def _numeric_sort(value):
    try:
        return (0, float(value))
    except (TypeError, ValueError):
        return (1, str(value or ""))


def primary_commercial_offer(profile):
    """Choose a review-friendly offer while retaining every offer in Commercial Analysis."""
    variations = commercial_offers(profile)
    if not variations:
        return {}
    for preferred in ("Cut Tape", "Loose", "Tube", "Tray", "Reel", "DigiReel"):
        for variation in variations:
            if variation.get("pack_format") == preferred:
                return variation
    return variations[0]


def _price_break_texts(breaks):
    """Return sorted, formatted quantity/price pairs for one price ladder."""
    items = list(breaks or [])
    items.sort(key=lambda item: _numeric_sort(item.get("break_quantity")))
    formatted = []
    for item in items:
        quantity = item.get("break_quantity")
        price = item.get("unit_price")
        try:
            quantity_text = f"{int(float(quantity)):,}"
        except (TypeError, ValueError):
            quantity_text = str(quantity or "")
        try:
            price_text = f"{float(price):,.5f}"
        except (TypeError, ValueError):
            price_text = str(price or "")
        formatted.append((quantity_text, price_text))
    return formatted


def price_break_summary(variation, quantity_width=None, price_width=None):
    """Return an aligned multiline price ladder without a currency symbol."""
    formatted = _price_break_texts((variation or {}).get("standard_price_breaks") or [])
    if not formatted:
        return ""
    quantity_width = quantity_width or max(len(quantity) for quantity, _ in formatted)
    price_width = price_width or max(len(price) for _, price in formatted)
    return "\n".join(
        f"{quantity:>{quantity_width}}  {price:>{price_width}}"
        for quantity, price in formatted
    )


def first_additional_charge(variation):
    charges = list((variation or {}).get("additional_charges") or [])
    return charges[0] if charges else {}


def commercial_analysis_rows(result, profile):
    rows = []
    for variation in commercial_offers(profile):
        charge = first_additional_charge(variation)
        price_breaks = variation.get("standard_price_breaks") or []
        if not price_breaks:
            price_breaks = [{}]
        for price_break in price_breaks:
            rows.append(OrderedDict([
                ("Source Row", result.get("Source Row", "")),
                ("Manufacturer", result.get("Manufacturer", "")),
                ("Manufacturer Part Number", result.get("Manufacturer Part Number", "")),
                ("Provider", profile.get("provider", "")),
                ("Provider Part Number", variation.get("provider_part_number", "")),
                ("Currency", profile.get("provider_currency", "")),
                ("Pack Format", variation.get("pack_format", "")),
                ("Packaging Code", variation.get("packaging_code", variation.get("package_type", ""))),
                ("Minimum Order Quantity", variation.get("minimum_order_quantity", "")),
                ("Pack Quantity", variation.get("pack_quantity", "")),
                ("Quantity Available", variation.get("quantity_available", "")),
                ("Manufacturer Lead Weeks", profile.get("manufacturer_lead_weeks", "")),
                ("Break Quantity", price_break.get("break_quantity", "")),
                ("Unit Price", price_break.get("unit_price", "")),
                ("Extended Price", price_break.get("total_price", "")),
                ("Additional Charge", charge.get("amount", "")),
                ("Additional Charge Currency", charge.get("currency", profile.get("provider_currency", ""))),
                ("Additional Charge Description", charge.get("description", "")),
                ("Additional Charge Application", charge.get("application", "")),
                ("Captured At UTC", profile.get("captured_at_utc", "")),
            ]))
    return rows


def offer_value_summary(profile, field, fallback_field=""):
    """Return one labelled line per commercial offer for a selected field."""
    lines = []
    for offer in commercial_offers(profile):
        label = offer.get("pack_format") or offer.get("package_type") or "Offer"
        value = offer.get(field)
        if value in (None, "") and fallback_field:
            value = offer.get(fallback_field)
        if value not in (None, ""):
            lines.append(f"{label}: {value}")
    return "\n".join(lines)


def all_additional_charges_summary(profile, field):
    lines = []
    for offer in commercial_offers(profile):
        label = offer.get("pack_format") or offer.get("package_type") or "Offer"
        for charge in offer.get("additional_charges") or []:
            value = charge.get(field)
            if value not in (None, ""):
                lines.append(f"{label}: {value}")
    return "\n".join(lines)


def all_price_breaks_summary(profile):
    """Return all offer ladders aligned to common quantity and price widths."""
    offers = []
    all_pairs = []
    for offer in commercial_offers(profile):
        pairs = _price_break_texts(offer.get("standard_price_breaks") or [])
        if pairs:
            offers.append((offer, pairs))
            all_pairs.extend(pairs)
    if not all_pairs:
        return ""

    quantity_width = max(len(quantity) for quantity, _ in all_pairs)
    price_width = max(len(price) for _, price in all_pairs)
    sections = []
    for offer, _ in offers:
        label = offer.get("pack_format") or offer.get("package_type") or "Offer"
        summary = price_break_summary(offer, quantity_width, price_width)
        sections.append(f"{label}\n{summary}")
    return "\n\n".join(sections)


def build_result(row, requested_mfg, requested_mpn, p, pa, record, resolved):
    returned_mfg = name(ci(p, "Manufacturer"))
    returned_mpn = str(ci(p, "ManufacturerProductNumber", "ManufacturerPartNumber", "MfrPartNumber") or "")
    mpn_match = norm(requested_mpn) == norm(returned_mpn)
    returned_mfg_id = ci(ci(p, "Manufacturer"), "Id")
    id_match = bool(returned_mfg_id) and str(returned_mfg_id) == str(resolved.manufacturer_id)
    name_match = names_equivalent(resolved.matched_name, returned_mfg) or names_equivalent(requested_mfg, returned_mfg)
    manufacturer_match = id_match or name_match
    status = "Matched" if mpn_match and manufacturer_match else "Review Required"

    if status == "Matched":
        verification = "manufacturer ID" if id_match else "normalised manufacturer name"
        reason = (
            f"Exact normalised MPN; manufacturer verified by {verification}. "
            f"Input {requested_mfg!r} resolved to {returned_mfg!r}."
        )
    elif not mpn_match:
        reason = f"Returned MPN {returned_mpn!r} differs from requested MPN {requested_mpn!r}."
    else:
        reason = (
            f"Returned manufacturer {returned_mfg!r} does not match resolved manufacturer "
            f"{resolved.matched_name!r} (DigiKey ID {resolved.manufacturer_id})."
        )

    short_description, detailed_description = descriptions(p)
    category, family = category_names(ci(p, "Category"))
    classifications = ci(p, "Classifications")
    product_status = ci(p, "ProductStatus", "Status")
    commercial_profile = record.commercial_profile or {}
    primary_offer = primary_commercial_offer(commercial_profile)
    additional_charge = first_additional_charge(primary_offer)

    values = OrderedDict([
        ("Source Row", row),
        ("Requested Manufacturer", requested_mfg),
        ("Requested MPN", requested_mpn),
        ("Match Status", status),
        ("Reason", reason),
        ("Manufacturer", returned_mfg),
        ("Manufacturer Part Number", returned_mpn),
        ("DigiKey Part Number", first_variation_value(p, "DigiKeyProductNumber", "DigiKeyPartNumber", "ProductNumber")),
        ("Description", short_description),
        ("Detailed Description", detailed_description),
        ("Product Category", category),
        ("Product Family", family),
        ("Series", name(ci(p, "Series"))),
        ("Base Product Number", name(ci(p, "BaseProductNumber"))),
        ("Product Status", name(ci(product_status, "Status", "Name", "Value"))),
        ("Last Buy Date", str(ci(p, "DateLastBuyChance") or "")),
        ("Datasheet URL", normalise_url(ci(p, "DatasheetUrl", "DatasheetURL"))),
        ("Product URL", normalise_url(ci(p, "ProductUrl", "ProductURL"))),
        ("Product Image URL", normalise_url(ci(p, "PhotoUrl", "PhotoURL"))),
        ("Primary Video URL", normalise_url(ci(p, "PrimaryVideoUrl", "PrimaryVideoURL"))),
        ("RoHS Status", name(ci(classifications, "RohsStatus", "RoHSStatus"))),
        ("REACH Status", name(ci(classifications, "ReachStatus", "REACHStatus"))),
        ("Moisture Sensitivity Level", name(ci(classifications, "MoistureSensitivityLevel"))),
        ("ECCN", name(ci(classifications, "ExportControlClassNumber"))),
        ("HTSUS Code", name(ci(classifications, "HtsusCode", "HTSUSCode"))),
        ("Mounting Type", parameter_value(pa, "mounting type")),
        ("Package / Case", parameter_value(pa, "package / case", "package/case")),
        ("Supplier Device Package", parameter_value(pa, "supplier device package")),
        ("Size / Dimension", parameter_value(pa, "size / dimension", "size/dimension")),
        ("Height - Seated (Max)", parameter_value(pa, "height - seated (max)", "height (max)")),
        ("Operating Temperature", parameter_value(pa, "operating temperature")),
        ("Pin / Position Count", parameter_value(pa, "number of positions", "number of pins", "pin count")),
        ("Tolerance", parameter_value(pa, "tolerance", "frequency tolerance")),
        ("Voltage Rating", parameter_value(pa, "voltage - rated", "voltage rating", "voltage - dc reverse (vr) (max)", "drain to source voltage (vdss)")),
        ("Current Rating", parameter_value(pa, "current rating (amps)", "current rating", "current - output", "current - continuous drain (id) @ 25°c")),
        ("Power Rating", parameter_value(pa, "power (watts)", "power - max", "power dissipation (max)")),
        ("Provider", commercial_profile.get("provider", "")),
        ("Offer Count", len(commercial_offers(commercial_profile))),
        ("Provider Part Number", offer_value_summary(commercial_profile, "provider_part_number")),
        ("Currency", commercial_profile.get("provider_currency", "")),
        ("Pack Format", offer_value_summary(commercial_profile, "pack_format")),
        ("Packaging Code", offer_value_summary(commercial_profile, "packaging_code", "package_type")),
        ("Minimum Order Quantity", offer_value_summary(commercial_profile, "minimum_order_quantity")),
        ("Pack Quantity", offer_value_summary(commercial_profile, "pack_quantity")),
        ("Quantity Available", offer_value_summary(commercial_profile, "quantity_available")),
        ("Manufacturer Lead Weeks", commercial_profile.get("manufacturer_lead_weeks", "")),
        ("Additional Charge", all_additional_charges_summary(commercial_profile, "amount")),
        ("Additional Charge Description", all_additional_charges_summary(commercial_profile, "description")),
        ("Price Breaks", all_price_breaks_summary(commercial_profile)),
        ("Captured At UTC", record.captured_at_utc),
        ("Data Source Mode", record.source_mode),
        ("Data Provider", str(record.metadata.get("provider", "DigiKey"))),
    ])
    return values



def add_mapping_sheet(workbook, columns, sample_values):
    ws = workbook.create_sheet("Attribute Mapping")
    ws.append(["Group", "Workbook Column", "JSON Path / Source", "Sample Value", "Applicability", "Notes"])
    universal = {
        "Manufacturer", "Manufacturer Part Number", "Description", "Detailed Description",
        "Product Category", "Product Family", "Product Status", "Datasheet URL",
        "Product URL", "Product Image URL", "RoHS Status", "REACH Status", "ECCN",
        "HTSUS Code", "Captured At UTC", "Data Source Mode", "Data Provider",
    }
    for column in columns:
        applicability = "Universal" if column.key in universal else "Where available / commodity-specific"
        ws.append([
            column.group, column.heading, column.source, sample_values.get(column.key, ""),
            applicability, column.notes,
        ])
    format_reference_sheet(ws)
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 52
    ws.column_dimensions["D"].width = 60
    ws.column_dimensions["E"].width = 34
    ws.column_dimensions["F"].width = 60



def classify_failure_status(error: Exception) -> str:
    """Map collection failures onto the four user-facing review states."""
    text = str(error).lower()
    if any(term in text for term in ("ambiguous", "multiple match", "multiple candidate")):
        return "Multiple Matches"
    if any(term in text for term in ("404", "not found", "no product", "no match")):
        return "Not Found"
    return "Review Required"

def _profile_attribute(profile, *aliases):
    attributes = (profile or {}).get("attributes") or {}
    lookup = {clean(key): value for key, value in attributes.items()}
    for alias in aliases:
        value = lookup.get(clean(alias))
        if value not in (None, "", "-"):
            return str(value)
    return ""


def _profile_compliance(profile, *aliases):
    compliance = (profile or {}).get("compliance") or {}
    lookup = {clean(key): value for key, value in compliance.items()}
    for alias in aliases:
        value = lookup.get(clean(alias))
        if value not in (None, "", "-"):
            return str(value)
    return ""


def _merged_custom_value(evidence, getter):
    values = []
    for item in evidence:
        if not item.identity_match:
            continue
        value = str(getter(item.part_profile or {}) or "").strip()
        if value:
            values.append((item.provider, value))
    if not values:
        return ""
    if len({clean(value) for _, value in values}) == 1:
        return values[0][1]
    return "\n".join(f"{provider}: {value}" for provider, value in values)


def _provider_evidence_text(evidence):
    return "\n".join(
        f"{item.provider}: {item.execution_status}"
        + (f" - {item.message}" if item.message else "")
        for item in evidence
    )


def _provider_price_summary(profile):
    return all_price_breaks_summary(profile) if profile else ""


def _provider_profile(evidence, provider_name):
    for item in evidence:
        if item.provider.casefold() == provider_name.casefold():
            return item.commercial_profile or {}
    return {}


def build_combined_result(row, requested_mfg, requested_mpn, evidence):
    status, reason = evidence_status(evidence)
    matched = [item.provider for item in evidence if item.identity_match]
    digikey = _provider_profile(evidence, "DigiKey")
    mouser = _provider_profile(evidence, "Mouser")

    values = OrderedDict((column.key, "") for column in enriched_columns())
    values.update({
        "Source Row": row,
        "Requested Manufacturer": requested_mfg,
        "Requested MPN": requested_mpn,
        "Match Status": status,
        "Reason": reason,
        "Providers Queried": _provider_evidence_text(evidence),
        "Providers Matched": ", ".join(matched),
        "Engineering Confirmation": engineering_confirmation(evidence),
        "Manufacturer": merged_value(evidence, "manufacturer"),
        "Manufacturer Part Number": merged_value(evidence, "manufacturer_part_number"),
        "Description": merged_value(evidence, "description"),
        "Detailed Description": merged_value(evidence, "detailed_description"),
        "Product Status": merged_value(evidence, "lifecycle_status"),
        "Mounting Type": merged_value(evidence, "mounting_type"),
        "Package / Case": merged_value(evidence, "package"),
        "Operating Temperature": _merged_custom_value(evidence, lambda p: _profile_attribute(p, "Operating Temperature")),
        "Pin / Position Count": _merged_custom_value(evidence, lambda p: _profile_attribute(p, "Number of Positions", "Number of Pins", "Pin Count")),
        "Tolerance": _merged_custom_value(evidence, lambda p: _profile_attribute(p, "Tolerance", "Frequency Tolerance")),
        "Voltage Rating": _merged_custom_value(evidence, lambda p: _profile_attribute(p, "Voltage - Rated", "Voltage Rating", "Voltage - DC Reverse (Vr) (Max)")),
        "Current Rating": _merged_custom_value(evidence, lambda p: _profile_attribute(p, "Current Rating", "Current - Output", "Current - Continuous Drain")),
        "Power Rating": _merged_custom_value(evidence, lambda p: _profile_attribute(p, "Power (Watts)", "Power - Max", "Power Dissipation")),
        "Provider #1 Name": "DigiKey",
        "Provider #1 Available": provider_availability(digikey),
        "Provider #1 Lead Time": digikey.get("manufacturer_lead_weeks", ""),
        "Provider #1 Currency": digikey.get("provider_currency", ""),
        "Provider #1 Price Breaks": _provider_price_summary(digikey),
        "Provider #2 Name": "Mouser",
        "Provider #2 Available": provider_availability(mouser),
        "Provider #2 Lead Time": mouser.get("manufacturer_lead_weeks", ""),
        "Provider #2 Currency": mouser.get("provider_currency", ""),
        "Provider #2 Price Breaks": _provider_price_summary(mouser),
        "Datasheet URL": merged_value(evidence, "datasheet_url"),
        "Product URL": merged_value(evidence, "product_url"),
        "Product Image URL": merged_value(evidence, "image_url"),
        "RoHS Status": merged_value(evidence, "rohs_status"),
        "REACH Status": _merged_custom_value(evidence, lambda p: _profile_compliance(p, "REACH", "REACH Status")),
        "ECCN": _merged_custom_value(evidence, lambda p: _profile_compliance(p, "ECCN", "Export Control Class Number")),
        "HTSUS Code": _merged_custom_value(evidence, lambda p: _profile_compliance(p, "HTSUS", "HTSUS Code")),
    })
    return values


def run(args):
    source = load_workbook(args.input, data_only=False)
    input_sheet = source[args.sheet] if args.sheet else source.active
    headers = [cell.value for cell in input_sheet[1]]
    manufacturer_column, mpn_column = locate_columns(headers)

    input_rows = []
    for row_number in range(max(2, args.start_row), input_sheet.max_row + 1):
        manufacturer = str(input_sheet.cell(row_number, manufacturer_column).value or "").strip()
        mpn = str(input_sheet.cell(row_number, mpn_column).value or "").strip()
        if manufacturer or mpn:
            input_rows.append((row_number, manufacturer, mpn))
        if args.max_parts and len(input_rows) >= args.max_parts:
            break

    settings = Settings.from_env()
    knowledge_base = KnowledgeBaseManager()
    digikey = DigiKeyProvider(settings, knowledge_base)
    mouser = MouserProvider(MouserSettings.from_env(), knowledge_base)
    provider_manager = ProviderManager([digikey, mouser])
    print(
        f"PDC v{APP_VERSION}: loaded {len(input_rows)} parts; "
        f"providers={', '.join(provider_manager.names)}; "
        f"DigiKey site={settings.site}, currency={settings.currency}"
    )
    if args.validate_only:
        return

    results = []
    commercial_rows = []
    manufacturer_result = provider_manager.execute(digikey, "manufacturers", args.force_refresh)
    manufacturer_catalogue = manufacturer_result.data if manufacturer_result.succeeded else None

    for index, (row_number, manufacturer, mpn) in enumerate(input_rows, 1):
        print(f"[{index}/{len(input_rows)}] {manufacturer} {mpn}")
        evidence = []
        resolved = None

        if manufacturer_catalogue is not None:
            try:
                resolved = resolve_manufacturer(manufacturer, manufacturer_catalogue)
                if resolved.manufacturer_id is None:
                    raise RuntimeError(
                        f"Manufacturer resolution {resolved.status}: {resolved.reason} "
                        f"(best={resolved.matched_name!r}, confidence={resolved.confidence:.2f})"
                    )
                provider_result = provider_manager.execute(
                    digikey, "details", mpn, resolved.manufacturer_id, args.force_refresh,
                    input_manufacturer=manufacturer,
                    resolved_manufacturer=resolved.matched_name,
                )
            except Exception as error:
                provider_result = None
                evidence.append(ProviderEvidence("DigiKey", "error", str(error)))
        else:
            provider_result = manufacturer_result

        if provider_result is not None:
            if provider_result.succeeded:
                record = provider_result.data
                profile = dict(record.part_profile or {})
                profile["identity_match"] = provider_identity_match(manufacturer, mpn, profile)
                execution_status = "success" if profile.get("manufacturer_part_number") else "no_match"
                item = ProviderEvidence(
                    "DigiKey", execution_status, part_profile=profile,
                    commercial_profile=record.commercial_profile,
                    captured_at_utc=record.captured_at_utc, source_mode=record.source_mode,
                )
                evidence.append(item)
                commercial_rows.extend(commercial_analysis_rows(
                    {"Source Row": row_number, "Manufacturer": profile.get("manufacturer", ""),
                     "Manufacturer Part Number": profile.get("manufacturer_part_number", "")},
                    record.commercial_profile,
                ))
            else:
                evidence.append(ProviderEvidence("DigiKey", provider_result.status.value, provider_result.message or ""))

        mouser_result = provider_manager.execute(
            mouser, "details", mpn, None, args.force_refresh,
            input_manufacturer=manufacturer,
            resolved_manufacturer=(resolved.matched_name if resolved else manufacturer),
        )
        if mouser_result.succeeded:
            record = mouser_result.data
            profile = dict(record.part_profile or {})
            profile["identity_match"] = provider_identity_match(manufacturer, mpn, profile)
            execution_status = "success" if profile.get("manufacturer_part_number") else "no_match"
            evidence.append(ProviderEvidence(
                "Mouser", execution_status, part_profile=profile,
                commercial_profile=record.commercial_profile,
                captured_at_utc=record.captured_at_utc, source_mode=record.source_mode,
            ))
            commercial_rows.extend(commercial_analysis_rows(
                {"Source Row": row_number, "Manufacturer": profile.get("manufacturer", ""),
                 "Manufacturer Part Number": profile.get("manufacturer_part_number", "")},
                record.commercial_profile,
            ))
        else:
            evidence.append(ProviderEvidence("Mouser", mouser_result.status.value, mouser_result.message or ""))

        result = build_combined_result(row_number, manufacturer, mpn, evidence)
        results.append(result)
        knowledge_base.save_part_summary(
            manufacturer=manufacturer,
            mpn=mpn,
            summary={
                "match_status": result.get("Match Status", ""),
                "reason": result.get("Reason", ""),
                "providers_matched": [item.provider for item in evidence if item.identity_match],
                "engineering_confirmation": result.get("Engineering Confirmation", ""),
                "providers": [
                    {
                        "provider": item.provider,
                        "execution_status": item.execution_status,
                        "identity_match": item.identity_match,
                        "message": item.message,
                        "captured_at_utc": item.captured_at_utc,
                        "source_mode": item.source_mode,
                    }
                    for item in evidence
                ],
            },
        )

    columns = enriched_columns()
    keys = column_keys(columns)
    headings = display_headings(columns)
    reason_column = WorkbookColumn(
        "Status", "Reason", "Reason",
        "PDC combined provider evidence", "Detailed provider evidence"
    )
    review_columns = columns[:4] + [reason_column] + columns[4:]
    review_keys = column_keys(review_columns)
    review_headings = display_headings(review_columns)

    output = Workbook()
    enriched = output.active
    enriched.title = "Enriched Parts"
    add_group_headers(enriched, columns)
    enriched.append(headings)
    for result in results:
        enriched.append([result.get(key, "") for key in keys])

    review = output.create_sheet("Review Required")
    add_group_headers(review, review_columns)
    review.append(review_headings)
    for result in results:
        if result.get("Match Status") != "Matched":
            review.append([result.get(key, "") for key in review_keys])

    commercial = output.create_sheet("Commercial Analysis")
    commercial_headings = [
        "Source Row", "Manufacturer", "Manufacturer Part Number", "Provider",
        "Provider Part Number", "Currency", "Pack Format", "Packaging Code",
        "Minimum Order Quantity", "Pack Quantity", "Quantity Available",
        "Manufacturer Lead Weeks", "Break Quantity", "Unit Price",
        "Extended Price", "Additional Charge", "Additional Charge Currency",
        "Additional Charge Description", "Additional Charge Application",
        "Captured At UTC",
    ]
    commercial.append(commercial_headings)
    commercial_rows.sort(key=lambda row: (
        str(row.get("Manufacturer", "")).upper(),
        str(row.get("Manufacturer Part Number", "")).upper(),
        str(row.get("Provider", "")).upper(),
        str(row.get("Pack Format", "")).upper(),
        _numeric_sort(row.get("Break Quantity")),
    ))
    for row in commercial_rows:
        commercial.append([row.get(heading, "") for heading in commercial_headings])

    format_review_sheet(enriched, headings)
    format_review_sheet(review, review_headings)
    format_reference_sheet(commercial)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    output.save(args.output)
    print("Created", args.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="output/AIPN_Enriched.xlsx")
    parser.add_argument("--sheet")
    parser.add_argument("--start-row", type=int, default=2)
    parser.add_argument("--max-parts", type=int)
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    run(parser.parse_args())
