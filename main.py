import argparse
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook, load_workbook

from config import Settings
from digikey_client import DigiKeyClient
from manufacturer_resolver import names_equivalent, resolve_manufacturer
from excel_formatter import add_group_headers, format_reference_sheet, format_review_sheet

APP_VERSION = "0.2.2"

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
    return [
        ("Input & Match", "Source Row", "Input workbook row", "Input row number"),
        ("Input & Match", "Requested Manufacturer", "Input.Manufacturer", "Manufacturer supplied by the user"),
        ("Input & Match", "Requested MPN", "Input.MPN", "MPN supplied by the user"),
        ("Input & Match", "Match Status", "PDC derived", "Matched, Review Required, Multiple Matches or Not Found"),
        ("Identity", "Manufacturer", "Product.Manufacturer.Name", "Resolved manufacturer returned by DigiKey"),
        ("Identity", "Manufacturer Part Number", "Product.ManufacturerProductNumber", "Canonical MPN returned by DigiKey"),
        ("Identity", "DigiKey Part Number", "Product.ProductVariations[0].DigiKeyProductNumber", "Distributor ordering reference where available"),
        ("Identity", "Description", "Product.Description.ProductDescription", "Short product description"),
        ("Identity", "Detailed Description", "Product.Description.DetailedDescription", "Longer description with key technical attributes"),
        ("Identity", "Product Category", "Product.Category.Name", "Top-level DigiKey category"),
        ("Identity", "Product Family", "Deepest Product.Category.ChildCategories[].Name", "Most specific category returned"),
        ("Identity", "Series", "Product.Series.Name", "Manufacturer product series"),
        ("Identity", "Base Product Number", "Product.BaseProductNumber", "DigiKey base product reference"),
        ("Identity", "Product Status", "Product.ProductStatus.Status", "Lifecycle status reported by DigiKey"),
        ("Identity", "Last Buy Date", "Product.DateLastBuyChance", "Last-buy date when supplied"),
        ("Documentation", "Datasheet URL", "Product.DatasheetUrl", "Manufacturer or distributor-hosted manufacturer datasheet"),
        ("Documentation", "Product URL", "Product.ProductUrl", "DigiKey product page"),
        ("Documentation", "Product Image URL", "Product.PhotoUrl", "Primary product image"),
        ("Documentation", "Primary Video URL", "Product.PrimaryVideoUrl", "Product video when available"),
        ("Compliance", "RoHS Status", "Product.Classifications.RohsStatus", "RoHS classification"),
        ("Compliance", "REACH Status", "Product.Classifications.ReachStatus", "REACH classification"),
        ("Compliance", "Moisture Sensitivity Level", "Product.Classifications.MoistureSensitivityLevel", "MSL classification"),
        ("Compliance", "ECCN", "Product.Classifications.ExportControlClassNumber", "Export Control Classification Number"),
        ("Compliance", "HTSUS Code", "Product.Classifications.HtsusCode", "US tariff classification"),
        ("Physical", "Mounting Type", "Product.Parameters[Mounting Type]", "Mounting method"),
        ("Physical", "Package / Case", "Product.Parameters[Package / Case]", "Generic package or case"),
        ("Physical", "Supplier Device Package", "Product.Parameters[Supplier Device Package]", "Supplier package designation"),
        ("Physical", "Size / Dimension", "Product.Parameters[Size / Dimension]", "Overall package dimensions"),
        ("Physical", "Height - Seated (Max)", "Product.Parameters[Height - Seated (Max)]", "Maximum seated height"),
        ("Physical", "Operating Temperature", "Product.Parameters[Operating Temperature]", "Rated operating temperature range"),
        ("Physical", "Pin / Position Count", "Product.Parameters[Number of Positions|Number of Pins]", "Connector positions or device pins when available"),
        ("Electrical", "Tolerance", "Product.Parameters[Tolerance|Frequency Tolerance]", "General tolerance or frequency tolerance"),
        ("Electrical", "Voltage Rating", "Product.Parameters[Voltage - Rated|Voltage Rating]", "Rated voltage where applicable"),
        ("Electrical", "Current Rating", "Product.Parameters[Current Rating|Current - Output|Current - Continuous Drain]", "Rated or output current where applicable"),
        ("Electrical", "Power Rating", "Product.Parameters[Power (Watts)|Power - Max|Power Dissipation]", "Rated power where applicable"),
        ("Commercial (Existing)", "Quantity Available", "Product.QuantityAvailable", "Existing commercial field; deeper work deferred"),
        ("Commercial (Existing)", "Manufacturer Lead Weeks", "Product.ManufacturerLeadWeeks", "Existing commercial field; deeper work deferred"),
        ("Commercial (Existing)", "Minimum Order Quantity", "Product.ProductVariations[].MinimumOrderQuantity", "Existing commercial field; deeper work deferred"),
        ("Traceability", "Captured At UTC", "knowledge_base_metadata.captured_at_utc", "Capture timestamp"),
        ("Traceability", "Data Source Mode", "knowledge_base_metadata.source_mode", "live_api, knowledge_base_current or legacy_cache_migration"),
        ("Traceability", "Data Provider", "knowledge_base_metadata.provider", "Provider used to collect the record"),
    ]


def first_variation_value(p, *names):
    variations = p.get("ProductVariations") or []
    for variation in variations:
        if not isinstance(variation, dict):
            continue
        value = ci(variation, *names)
        if value not in ("", None):
            return value
    return ""


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
        ("Quantity Available", ci(p, "QuantityAvailable")),
        ("Manufacturer Lead Weeks", ci(p, "ManufacturerLeadWeeks")),
        ("Minimum Order Quantity", first_variation_value(p, "MinimumOrderQuantity")),
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

    add_mapping_sheet(output, columns, sample_values)

    format_review_sheet(enriched, headings)
    format_review_sheet(review, review_headings)
    format_reference_sheet(all_attributes)

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
