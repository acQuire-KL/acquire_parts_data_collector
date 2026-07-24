import argparse
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook, load_workbook

from config import Settings
from digikey_client import DigiKeyClient
from manufacturer_resolver import names_equivalent, resolve_manufacturer
from excel_formatter import add_group_headers, format_reference_sheet, format_review_sheet
from workbook_layout import enriched_parts_columns

APP_VERSION = "0.2.3"

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
    variations = list((profile or {}).get("variations") or [])
    if not variations:
        return {}
    for preferred in ("Cut Tape", "Loose", "Tube", "Tray", "Reel", "DigiReel"):
        for variation in variations:
            if variation.get("pack_format") == preferred:
                return variation
    return variations[0]


def price_break_summary(variation):
    """Return a compact multiline summary with quantities padded for aligned @ symbols."""
    breaks = list((variation or {}).get("standard_price_breaks") or [])
    if not breaks:
        return ""
    breaks.sort(key=lambda item: _numeric_sort(item.get("break_quantity")))
    quantity_texts = []
    for item in breaks:
        value = item.get("break_quantity")
        try:
            quantity_texts.append(f"{int(float(value)):,}")
        except (TypeError, ValueError):
            quantity_texts.append(str(value or ""))
    width = max((len(value) for value in quantity_texts), default=1)
    lines = []
    for quantity, item in zip(quantity_texts, breaks):
        price = item.get("unit_price")
        try:
            price_text = f"{float(price):,.5f}"
        except (TypeError, ValueError):
            price_text = str(price or "")
        lines.append(f"{quantity:>{width}} @ {price_text}")
    return "\n".join(lines)


def first_additional_charge(variation):
    charges = list((variation or {}).get("additional_charges") or [])
    return charges[0] if charges else {}


def commercial_analysis_rows(result, profile):
    rows = []
    for variation in (profile or {}).get("variations") or []:
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
        ("Provider Part Number", primary_offer.get("provider_part_number", "")),
        ("Currency", commercial_profile.get("provider_currency", "")),
        ("Pack Format", primary_offer.get("pack_format", "")),
        ("Packaging Code", primary_offer.get("packaging_code", primary_offer.get("package_type", ""))),
        ("Minimum Order Quantity", primary_offer.get("minimum_order_quantity", "")),
        ("Pack Quantity", primary_offer.get("pack_quantity", "")),
        ("Quantity Available", primary_offer.get("quantity_available", commercial_profile.get("product_quantity_available", ""))),
        ("Manufacturer Lead Weeks", commercial_profile.get("manufacturer_lead_weeks", "")),
        ("Additional Charge", additional_charge.get("amount", "")),
        ("Additional Charge Description", additional_charge.get("description", "")),
        ("Price Breaks", price_break_summary(primary_offer)),
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
    for group, heading, source, notes in columns:
        applicability = "Universal" if heading in universal else "Where available / commodity-specific"
        ws.append([group, heading, source, sample_values.get(heading, ""), applicability, notes])
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
    print(f"PDC v{APP_VERSION}: loaded {len(input_rows)} parts; DigiKey site={settings.site}, currency={settings.currency}")
    if args.validate_only:
        return

    client = DigiKeyClient(settings)
    results = []
    attributes = []
    commercial_rows = []
    manufacturer_catalogue = client.manufacturers(args.force_refresh)

    for index, (row_number, manufacturer, mpn) in enumerate(input_rows, 1):
        print(f"[{index}/{len(input_rows)}] {manufacturer} {mpn}")
        try:
            resolved = resolve_manufacturer(manufacturer, manufacturer_catalogue)
            if resolved.manufacturer_id is None:
                raise RuntimeError(
                    f"Manufacturer resolution {resolved.status}: {resolved.reason} "
                    f"(best={resolved.matched_name!r}, confidence={resolved.confidence:.2f})"
                )
            print(
                f"    Manufacturer: {manufacturer} -> {resolved.matched_name} "
                f"(ID {resolved.manufacturer_id}, confidence {resolved.confidence:.2f})"
            )
            record = client.details(
                mpn,
                resolved.manufacturer_id,
                args.force_refresh,
                input_manufacturer=manufacturer,
                resolved_manufacturer=resolved.matched_name,
            )
            payload = record.provider_response
            p = product(payload)
            pa = params(p)
            result = build_result(row_number, manufacturer, mpn, p, pa, record, resolved)
            results.append(result)
            commercial_rows.extend(commercial_analysis_rows(result, record.commercial_profile))
            for path, value in flatten(payload):
                attributes.append([row_number, manufacturer, mpn, path, value, "DigiKey Product Information V4"])
        except Exception as error:
            failure = OrderedDict((heading, "") for _, heading, _, _ in enriched_columns())
            failure.update({
                "Source Row": row_number,
                "Requested Manufacturer": manufacturer,
                "Requested MPN": mpn,
                "Match Status": classify_failure_status(error),
                "Reason": str(error),
                "Captured At UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                "Data Source Mode": "error",
                "Data Provider": "DigiKey",
            })
            results.append(failure)

    columns = enriched_columns()
    headings = [heading for _, heading, _, _ in columns]
    reason_column = ("Input & Match", "Reason", "PDC derived", "Detailed diagnostics retained for investigation")
    review_columns = columns[:4] + [reason_column] + columns[4:]
    review_headings = [heading for _, heading, _, _ in review_columns]
    output = Workbook()
    enriched = output.active
    enriched.title = "Enriched Parts"
    add_group_headers(enriched, columns)
    enriched.append(headings)

    sample_values = {}
    for result in results:
        enriched.append([result.get(heading, "") for heading in headings])
        if result.get("Match Status") == "Matched":
            for heading, value in result.items():
                if heading not in sample_values and value not in ("", None):
                    sample_values[heading] = value

    all_attributes = output.create_sheet("All Attributes")
    all_attributes.append(["Source Row", "Requested Manufacturer", "Requested MPN", "Attribute Path", "Attribute Value", "Source"])
    for item in attributes:
        all_attributes.append(item)

    review = output.create_sheet("Review Required")
    add_group_headers(review, review_columns)
    review.append(review_headings)
    for result in results:
        if result.get("Match Status") != "Matched":
            review.append([result.get(heading, "") for heading in review_headings])

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

    add_mapping_sheet(output, columns, sample_values)

    format_review_sheet(enriched, headings)
    format_review_sheet(review, review_headings)
    format_reference_sheet(all_attributes)
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
