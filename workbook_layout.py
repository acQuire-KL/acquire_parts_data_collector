"""Workbook column layout definitions for PDC outputs.

The workbook writer consumes these declarative definitions instead of owning
column order itself.  This keeps presentation changes separate from data
collection and result-building logic.
"""

from __future__ import annotations


# Each entry is: (section, workbook heading, JSON path/source, notes).
# The order below is the displayed order on Enriched Parts and Review Required.
ENRICHED_PARTS_COLUMNS = [
    # Status
    ("Status", "Source Row", "Input workbook row", "Input row number"),
    ("Status", "Requested Manufacturer", "Input.Manufacturer", "Manufacturer supplied by the user"),
    ("Status", "Requested MPN", "Input.MPN", "MPN supplied by the user"),
    ("Status", "Match Status", "PDC derived", "Matched, Review Required, Multiple Matches or Not Found"),

    # Identity
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

    # Engineering: physical and electrical attributes are presented together.
    ("Engineering", "Mounting Type", "Product.Parameters[Mounting Type]", "Mounting method"),
    ("Engineering", "Package / Case", "Product.Parameters[Package / Case]", "Generic package or case"),
    ("Engineering", "Supplier Device Package", "Product.Parameters[Supplier Device Package]", "Supplier package designation"),
    ("Engineering", "Size / Dimension", "Product.Parameters[Size / Dimension]", "Overall package dimensions"),
    ("Engineering", "Height - Seated (Max)", "Product.Parameters[Height - Seated (Max)]", "Maximum seated height"),
    ("Engineering", "Operating Temperature", "Product.Parameters[Operating Temperature]", "Rated operating temperature range"),
    ("Engineering", "Pin / Position Count", "Product.Parameters[Number of Positions|Number of Pins]", "Connector positions or device pins when available"),
    ("Engineering", "Tolerance", "Product.Parameters[Tolerance|Frequency Tolerance]", "General tolerance or frequency tolerance"),
    ("Engineering", "Voltage Rating", "Product.Parameters[Voltage - Rated|Voltage Rating]", "Rated voltage where applicable"),
    ("Engineering", "Current Rating", "Product.Parameters[Current Rating|Current - Output|Current - Continuous Drain]", "Rated or output current where applicable"),
    ("Engineering", "Power Rating", "Product.Parameters[Power (Watts)|Power - Max|Power Dissipation]", "Rated power where applicable"),

    # Commercial
    ("Commercial", "Provider", "commercial_profile.provider", "Commercial data provider"),
    ("Commercial", "Provider Part Number", "commercial_profile.offers[].provider_part_number", "Ordering reference for the primary offer"),
    ("Commercial", "Currency", "commercial_profile.provider_currency", "Original provider currency; never overwritten"),
    ("Commercial", "Pack Format", "commercial_profile.offers[].pack_format", "Normalised packaging format for the primary offer"),
    ("Commercial", "Packaging Code", "commercial_profile.offers[].packaging_code", "Provider packaging description"),
    ("Commercial", "Minimum Order Quantity", "commercial_profile.offers[].minimum_order_quantity", "MOQ for the primary offer"),
    ("Commercial", "Pack Quantity", "commercial_profile.offers[].pack_quantity", "Standard pack quantity for the primary offer"),
    ("Commercial", "Quantity Available", "commercial_profile.offers[].quantity_available", "Availability for the primary packaging offer"),
    ("Commercial", "Manufacturer Lead Weeks", "commercial_profile.manufacturer_lead_weeks", "Manufacturer lead time reported by the provider"),
    ("Commercial", "Additional Charge", "commercial_profile.offers[].additional_charges[].amount", "Fixed charge such as Digi-Reel service fee"),
    ("Commercial", "Additional Charge Description", "commercial_profile.offers[].additional_charges[].description", "Description of the fixed commercial charge"),
    ("Commercial", "Price Breaks", "commercial_profile.offers[].standard_price_breaks", "One price break per line for the primary offer"),

    # Traceability
    ("Traceability", "Captured At UTC", "knowledge_base_metadata.captured_at_utc", "Capture timestamp"),
    ("Traceability", "Data Source Mode", "knowledge_base_metadata.source_mode", "live_api, knowledge_base_current or legacy_cache_migration"),
    ("Traceability", "Data Provider", "knowledge_base_metadata.provider", "Provider used to collect the record"),

    # Documentation
    ("Documentation", "Datasheet URL", "Product.DatasheetUrl", "Manufacturer or distributor-hosted manufacturer datasheet"),
    ("Documentation", "Product URL", "Product.ProductUrl", "DigiKey product page"),
    ("Documentation", "Product Image URL", "Product.PhotoUrl", "Primary product image"),
    ("Documentation", "Primary Video URL", "Product.PrimaryVideoUrl", "Product video when available"),

    # Compliance
    ("Compliance", "RoHS Status", "Product.Classifications.RohsStatus", "RoHS classification"),
    ("Compliance", "REACH Status", "Product.Classifications.ReachStatus", "REACH classification"),
    ("Compliance", "Moisture Sensitivity Level", "Product.Classifications.MoistureSensitivityLevel", "MSL classification"),
    ("Compliance", "ECCN", "Product.Classifications.ExportControlClassNumber", "Export Control Classification Number"),
    ("Compliance", "HTSUS Code", "Product.Classifications.HtsusCode", "US tariff classification"),
]


def enriched_parts_columns() -> list[tuple[str, str, str, str]]:
    """Return a copy so callers cannot mutate the canonical layout."""
    return list(ENRICHED_PARTS_COLUMNS)
