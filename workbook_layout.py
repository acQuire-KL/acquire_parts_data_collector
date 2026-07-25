"""Declarative workbook layout for the PDC review dashboard."""
from __future__ import annotations

ENRICHED_PARTS_COLUMNS = [
    ("Status", "Source Row", "Input workbook row", "Input row number"),
    ("Status", "Requested Manufacturer", "Input.Manufacturer", "Manufacturer supplied by the user"),
    ("Status", "Requested MPN", "Input.MPN", "MPN supplied by the user"),
    ("Status", "Match Status", "PDC combined provider evidence", "Identity match after all enabled providers are reviewed"),
    ("Status", "Providers Queried", "PDC provider execution", "Provider-level search outcomes"),
    ("Status", "Providers Matched", "PDC identity confirmation", "Providers matching manufacturer and MPN"),
    ("Status", "Engineering Confirmation", "PDC cross-provider comparison", "Agreement only; no provider preference or recommendation"),

    ("Identity", "Manufacturer", "Common part profiles", "Manufacturer returned by matching providers"),
    ("Identity", "Manufacturer Part Number", "Common part profiles", "MPN returned by matching providers"),
    ("Identity", "Description", "Common part profiles", "Short product description"),
    ("Identity", "Detailed Description", "Common part profiles", "Detailed product description"),
    ("Identity", "Product Status", "Common part profiles", "Lifecycle status reported by providers"),

    ("Engineering", "Mounting Type", "Common part profiles", "Mounting method"),
    ("Engineering", "Package / Case", "Common part profiles", "Package or case"),
    ("Engineering", "Operating Temperature", "Common attributes", "Operating temperature where available"),
    ("Engineering", "Pin / Position Count", "Common attributes", "Pin or position count where available"),
    ("Engineering", "Tolerance", "Common attributes", "Tolerance where available"),
    ("Engineering", "Voltage Rating", "Common attributes", "Voltage rating where available"),
    ("Engineering", "Current Rating", "Common attributes", "Current rating where available"),
    ("Engineering", "Power Rating", "Common attributes", "Power rating where available"),

    ("DigiKey", "DigiKey Available", "DigiKey commercial profile", "Availability snapshot"),
    ("DigiKey", "DigiKey Lead Time", "DigiKey commercial profile", "Manufacturer lead time reported by DigiKey"),
    ("DigiKey", "DigiKey Price Breaks", "DigiKey commercial profile", "Price ladders; detailed offers remain in Commercial Analysis"),

    ("Mouser", "Mouser Available", "Mouser commercial profile", "Availability snapshot"),
    ("Mouser", "Mouser Lead Time", "Mouser commercial profile", "Manufacturer lead time reported by Mouser"),
    ("Mouser", "Mouser Price Breaks", "Mouser commercial profile", "Price ladders; detailed offers remain in Commercial Analysis"),

    ("Documentation", "Datasheet URL", "Common part profiles", "Manufacturer datasheet URL where available"),
    ("Documentation", "Product URL", "Common part profiles", "Provider product page where available"),
    ("Documentation", "Product Image URL", "Common part profiles", "Product image where available"),

    ("Compliance", "RoHS Status", "Common part profiles", "RoHS status"),
    ("Compliance", "REACH Status", "Common compliance profiles", "REACH status where available"),
    ("Compliance", "ECCN", "Common compliance profiles", "Export classification where available"),
    ("Compliance", "HTSUS Code", "Common compliance profiles", "Tariff classification where available"),
]


def enriched_parts_columns() -> list[tuple[str, str, str, str]]:
    return list(ENRICHED_PARTS_COLUMNS)
