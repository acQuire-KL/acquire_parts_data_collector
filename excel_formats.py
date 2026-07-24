"""Central Excel field-format definitions for PDC outputs.

Every workbook field is assigned a semantic format type here.  The workbook
writer supplies values; ``excel_formatter.py`` applies the presentation rules.
Identifiers such as MPNs are deliberately treated as text, even when they look
numeric.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExcelFormat:
    horizontal: str = "left"
    vertical: str = "top"
    number_format: str = "General"
    wrap_text: bool = False
    width: int | None = None
    hyperlink: bool = False
    coerce_numeric: bool = False


FORMAT_TYPES = {
    "text": ExcelFormat(horizontal="left"),
    "description": ExcelFormat(horizontal="left", wrap_text=True, width=36),
    "detailed_description": ExcelFormat(horizontal="left", wrap_text=True, width=48),
    "integer": ExcelFormat(
        horizontal="right",
        number_format="#,##0",
        coerce_numeric=True,
    ),
    "price": ExcelFormat(
        horizontal="right",
        number_format="#,##0.00000",
        coerce_numeric=True,
    ),
    "exchange_rate": ExcelFormat(
        horizontal="right",
        number_format="0.000000",
        coerce_numeric=True,
    ),
    "lead_time": ExcelFormat(
        horizontal="center",
        number_format="0",
        coerce_numeric=True,
    ),
    "status": ExcelFormat(horizontal="center"),
    "date": ExcelFormat(horizontal="center", number_format="yyyy-mm-dd"),
    "datetime": ExcelFormat(horizontal="center", number_format="yyyy-mm-dd hh:mm:ss"),
    "url": ExcelFormat(horizontal="left", width=42, hyperlink=True),
    "reason": ExcelFormat(horizontal="left", wrap_text=True, width=60),
}


# Explicit format assignment for every field currently written to Enriched
# Parts or Review Required.  Future commercial fields are included now so the
# formatter is ready when the Commercial profile is expanded.
FIELD_FORMAT_TYPES = {
    # Input & Match
    "Source Row": "integer",
    "Requested Manufacturer": "text",
    "Requested MPN": "text",
    "Match Status": "status",
    "Reason": "reason",

    # Identity
    "Manufacturer": "text",
    "Manufacturer Part Number": "text",
    "DigiKey Part Number": "text",
    "Description": "description",
    "Detailed Description": "detailed_description",
    "Product Category": "text",
    "Product Family": "text",
    "Series": "text",
    "Base Product Number": "text",
    "Product Status": "text",
    "Last Buy Date": "date",

    # Documentation
    "Datasheet URL": "url",
    "Product URL": "url",
    "Product Image URL": "url",
    "Primary Video URL": "url",

    # Compliance
    "RoHS Status": "text",
    "REACH Status": "text",
    "Moisture Sensitivity Level": "text",
    "ECCN": "text",
    "HTSUS Code": "text",

    # Physical
    "Mounting Type": "text",
    "Package / Case": "text",
    "Supplier Device Package": "text",
    "Size / Dimension": "text",
    "Height - Seated (Max)": "text",
    "Operating Temperature": "text",
    "Pin / Position Count": "text",

    # Electrical
    "Tolerance": "text",
    "Voltage Rating": "text",
    "Current Rating": "text",
    "Power Rating": "text",

    # Commercial - current
    "Quantity Available": "integer",
    "Availability Quantity": "integer",
    "Manufacturer Lead Weeks": "lead_time",
    "Lead Time": "lead_time",
    "Lead Time (Weeks)": "lead_time",
    "Minimum Order Quantity": "integer",
    "MOQ": "integer",

    # Commercial - planned
    "Pack Quantity": "integer",
    "Pack Qty": "integer",
    "Pack Format": "text",
    "Packaging Code": "text",
    "Provider": "text",
    "Provider Currency": "text",
    "Currency": "text",
    "Unit Price": "price",
    "Provider Unit Price": "price",
    "EUR Unit Price": "price",
    "Break Quantity": "integer",
    "Break Price": "price",
    "Exchange Rate": "exchange_rate",
    "Exchange Rate Date": "date",

    # Traceability
    "Captured At UTC": "datetime",
    "Data Source Mode": "text",
    "Data Provider": "text",
}


def format_for_heading(heading: str) -> ExcelFormat:
    """Return the declared format for a field, defaulting safely to text."""
    format_type = FIELD_FORMAT_TYPES.get(heading, "text")
    return FORMAT_TYPES[format_type]
