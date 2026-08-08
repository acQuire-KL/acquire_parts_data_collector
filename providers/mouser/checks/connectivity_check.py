"""Run a live Mouser Search API connectivity check without changing workbooks."""

from __future__ import annotations

import argparse

from config import MouserSettings
from providers import ProviderManager
from providers.mouser import MouserProvider


def _parts(payload):
    search_results = (payload or {}).get("SearchResults") or (payload or {}).get("searchResults") or {}
    return search_results.get("Parts") or search_results.get("parts") or []


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Mouser Search API connectivity for one MPN.")
    parser.add_argument("mpn", help="Manufacturer or Mouser part number to search")
    args = parser.parse_args()

    provider = MouserProvider(MouserSettings.from_env())
    manager = ProviderManager([provider])
    result = manager.execute(provider, "search_part_number", args.mpn)

    print(f"Mouser connectivity: {result.status.value}")
    if result.message:
        print(result.message)
        return 1

    parts = _parts(result.data)
    print(f"Results returned: {len(parts)}")
    if parts:
        first = parts[0]
        print(f"Manufacturer: {first.get('Manufacturer', '')}")
        print(f"Manufacturer Part Number: {first.get('ManufacturerPartNumber', '')}")
        print(f"Mouser Part Number: {first.get('MouserPartNumber', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
