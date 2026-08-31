from __future__ import annotations

import json
from pathlib import Path

from config import Settings
from knowledge_base_manager import KnowledgeBaseManager
from manufacturer_resolver import resolve_manufacturer
from providers.digikey import DigiKeyProvider


SEARCHES = [
    "BM28B0.6-6DS_2-0.35V_51_",
    "BM28B066DS2035V51",
    "BM28B0.6-6DP/2-0.35V(51)",
]


def walk_products(payload):
    """Yield likely DigiKey product dictionaries from any nested response."""
    stack = [payload]
    seen = set()
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            mpn = (
                item.get("ManufacturerProductNumber")
                or item.get("ManufacturerPartNumber")
                or item.get("MfrPartNumber")
            )
            if mpn:
                mfg = item.get("Manufacturer") or item.get("manufacturer")
                if isinstance(mfg, dict):
                    mfg = mfg.get("Name") or mfg.get("name")
                dkpn = (
                    item.get("DigiKeyPartNumber")
                    or item.get("DigiKeyProductNumber")
                    or item.get("ProductNumber")
                )
                key = (str(mfg or ""), str(mpn), str(dkpn or ""))
                if key not in seen:
                    seen.add(key)
                    yield {
                        "manufacturer": mfg or "",
                        "mpn": mpn,
                        "digikey_part_number": dkpn or "",
                    }
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)


def main():
    settings = Settings.from_env()
    kb = KnowledgeBaseManager()
    provider = DigiKeyProvider(settings, kb)

    print("DigiKey-only diagnostic")
    print(f"Site={settings.site}  Currency={settings.currency}")
    print()

    print("1) Manufacturer resolution")
    try:
        catalogue = provider.manufacturers(True)
        resolved = resolve_manufacturer("Hirose", catalogue)
        print(f"   Input: Hirose")
        print(f"   Status: {resolved.status}")
        print(f"   Matched name: {resolved.matched_name!r}")
        print(f"   Manufacturer ID: {resolved.manufacturer_id!r}")
        print(f"   Confidence: {resolved.confidence:.3f}")
        print(f"   Reason: {resolved.reason}")
    except Exception as exc:
        print(f"   ERROR: {type(exc).__name__}: {exc}")
        resolved = None

    print()
    print("2) Keyword searches")
    for query in SEARCHES:
        print()
        print("=" * 78)
        print(f"SEARCH: {query}")
        try:
            payload, rate = provider.keyword_search(query, record_count=25)
            products = list(walk_products(payload))
            print(f"API: success")
            print(f"Products found in returned JSON: {len(products)}")
            for idx, part in enumerate(products[:20], 1):
                print(
                    f"{idx:02d}. MFG={part['manufacturer']}  "
                    f"MPN={part['mpn']}  DigiKeyPN={part['digikey_part_number']}"
                )
            if not products:
                print("No product identity records found in the returned JSON.")
                print("Top-level keys:", list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__)
        except Exception as exc:
            print(f"API ERROR: {type(exc).__name__}: {exc}")

    print()
    print("3) Direct corrected-MPN detail lookup")
    corrected = "BM28B0.6-6DP/2-0.35V(51)"
    if resolved is None or resolved.manufacturer_id is None:
        print("Skipped because manufacturer resolution did not return an ID.")
    else:
        try:
            record = provider.details(
                corrected,
                resolved.manufacturer_id,
                True,
                input_manufacturer="Hirose",
                resolved_manufacturer=resolved.matched_name,
            )
            profile = record.part_profile or {}
            print("API: success")
            print("Returned Manufacturer:", profile.get("manufacturer", ""))
            print("Returned MPN:", profile.get("manufacturer_part_number", ""))
            print("Source mode:", getattr(record, "source_mode", ""))
        except Exception as exc:
            print(f"API ERROR: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
