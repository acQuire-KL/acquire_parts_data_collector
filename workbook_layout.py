"""Declarative workbook layout for the PDC review dashboard."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkbookColumn:
    """One workbook column with separate data key and displayed heading."""

    group: str
    key: str
    heading: str
    source: str
    notes: str


def _column(group: str, heading: str, source: str, notes: str, *, key: str | None = None) -> WorkbookColumn:
    return WorkbookColumn(group, key or heading, heading, source, notes)


ENRICHED_PARTS_COLUMNS = [
    _column("Status", "Source Row", "Input workbook row", "Input row number"),
    _column("Status", "Requested Manufacturer", "Input.Manufacturer", "Manufacturer supplied by the user"),
    _column("Status", "Requested MPN", "Input.MPN", "MPN supplied by the user"),
    _column("Status", "Match Status", "PDC combined provider evidence", "Identity match after all enabled providers are reviewed"),
    _column("Status", "Providers Queried", "PDC provider execution", "Provider-level search outcomes"),
    _column("Status", "Providers Matched", "PDC identity confirmation", "Providers matching manufacturer and MPN"),
    _column("Status", "Engineering Confirmation", "PDC cross-provider comparison", "Agreement only; no provider preference or recommendation"),
    _column("Status", "Review Observation", "PDC operational BOM review", "Concise exception/attention summary; not an approval"),

    _column("BOM Context", "BOM Description", "Input BOM", "Original BOM description where available"),
    _column("BOM Context", "BOM Quantity", "Input BOM", "Original BOM quantity where available"),
    _column("BOM Context", "BOM DNP", "Input BOM", "Original DNP/fit state; DNP rows are still reviewed"),

    _column("Local Knowledge", "Local Knowledge Status", "Parts_Master/parts_master_index.json", "Exact local MFG+MPN status"),
    _column("Local Knowledge", "AIPN", "Parts_Master/parts_master_index.json", "Existing AIPN where allocated"),
    _column("Local Knowledge", "Local Lifecycle", "Parts_Master/parts_master_index.json", "Lifecycle stored in Parts Master"),
    _column("Local Knowledge", "Datasheet Evidence Status", "Parts_Master/parts_master_index.json", "Current datasheet evidence quality"),
    _column("Local Knowledge", "Static Datasheet", "Parts_Master/parts_master_index.json", "Local static evidence path where available"),

    _column("Identity", "Manufacturer", "Common part profiles", "Manufacturer returned by matching providers"),
    _column("Identity", "Manufacturer Part Number", "Common part profiles", "MPN returned by matching providers"),
    _column("Identity", "Description", "Common part profiles", "Short product description"),
    _column("Identity", "Detailed Description", "Common part profiles", "Detailed product description"),
    _column("Identity", "Product Status", "Common part profiles", "Lifecycle status reported by providers"),

    _column("Engineering", "Mounting Type", "Common part profiles", "Mounting method"),
    _column("Engineering", "Package / Case", "Common part profiles", "Package or case"),
    _column("Engineering", "Operating Temperature", "Common attributes", "Operating temperature where available"),
    _column("Engineering", "Pin / Position Count", "Common attributes", "Pin or position count where available"),
    _column("Engineering", "Tolerance", "Common attributes", "Tolerance where available"),
    _column("Engineering", "Voltage Rating", "Common attributes", "Voltage rating where available"),
    _column("Engineering", "Current Rating", "Common attributes", "Current rating where available"),
    _column("Engineering", "Power Rating", "Common attributes", "Power rating where available"),

    _column("Provider #1", "Provider Name", "DigiKey commercial profile", "Provider occupying dashboard position 1", key="Provider #1 Name"),
    _column("Provider #1", "Available", "DigiKey commercial profile", "Availability snapshot", key="Provider #1 Available"),
    _column("Provider #1", "Lead Time", "DigiKey commercial profile", "Manufacturer lead time reported by the provider", key="Provider #1 Lead Time"),
    _column("Provider #1", "Currency", "DigiKey commercial profile", "Currency applying to the provider price ladder", key="Provider #1 Currency"),
    _column("Provider #1", "Price Breaks", "DigiKey commercial profile", "Price ladders; detailed offers remain in Commercial Analysis", key="Provider #1 Price Breaks"),

    _column("Provider #2", "Provider Name", "Mouser commercial profile", "Provider occupying dashboard position 2", key="Provider #2 Name"),
    _column("Provider #2", "Available", "Mouser commercial profile", "Availability snapshot", key="Provider #2 Available"),
    _column("Provider #2", "Lead Time", "Mouser commercial profile", "Manufacturer lead time reported by the provider", key="Provider #2 Lead Time"),
    _column("Provider #2", "Currency", "Mouser commercial profile", "Currency applying to the provider price ladder", key="Provider #2 Currency"),
    _column("Provider #2", "Price Breaks", "Mouser commercial profile", "Price ladders; detailed offers remain in Commercial Analysis", key="Provider #2 Price Breaks"),

    _column("Provider #3", "Provider Name", "TME commercial profile", "Provider occupying dashboard position 3", key="Provider #3 Name"),
    _column("Provider #3", "Available", "TME commercial profile", "Availability snapshot", key="Provider #3 Available"),
    _column("Provider #3", "Lead Time", "TME commercial profile", "Manufacturer lead time reported by the provider", key="Provider #3 Lead Time"),
    _column("Provider #3", "Currency", "TME commercial profile", "Currency applying to the provider price ladder", key="Provider #3 Currency"),
    _column("Provider #3", "Price Breaks", "TME commercial profile", "Price ladders; detailed offers remain in Commercial Analysis", key="Provider #3 Price Breaks"),

    _column("Documentation", "Datasheet URL", "Common part profiles", "Manufacturer datasheet URL where available"),
    _column("Documentation", "Product URL", "Common part profiles", "Provider product page where available"),
    _column("Documentation", "Product Image URL", "Common part profiles", "Product image where available"),

    _column("Compliance", "RoHS Status", "Common part profiles", "RoHS status"),
    _column("Compliance", "REACH Status", "Common compliance profiles", "REACH status where available"),
    _column("Compliance", "ECCN", "Common compliance profiles", "Export classification where available"),
    _column("Compliance", "HTSUS Code", "Common compliance profiles", "Tariff classification where available"),
]


def enriched_parts_columns() -> list[WorkbookColumn]:
    return list(ENRICHED_PARTS_COLUMNS)


def column_keys(columns: list[WorkbookColumn]) -> list[str]:
    return [column.key for column in columns]


def display_headings(columns: list[WorkbookColumn]) -> list[str]:
    return [column.heading for column in columns]
