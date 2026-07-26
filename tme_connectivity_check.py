"""Run a live TME Product API v2 authentication and search check."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import TmeSettings
from providers.tme import TmeClient


def _find_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[Any] = [payload.get("products"), payload.get("data")]
    for candidate in candidates:
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]
        if isinstance(candidate, dict):
            products = candidate.get("products")
            if isinstance(products, list):
                return [item for item in products if isinstance(item, dict)]
            if isinstance(products, dict):
                for key in ("items", "elements", "products"):
                    nested = products.get(key)
                    if isinstance(nested, list):
                        return [item for item in nested if isinstance(item, dict)]
    return []


def _value(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            if isinstance(value, dict):
                for nested_key in ("name", "value", "symbol"):
                    nested = value.get(nested_key)
                    if nested not in (None, ""):
                        return str(nested)
            return str(value)
    return ""


def _save_raw(payload: dict[str, Any], mpn: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_mpn = "".join(char if char.isalnum() else "_" for char in mpn).strip("_")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"TME_{safe_mpn}_{timestamp}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify TME Product API v2 connectivity.")
    parser.add_argument("mpn", nargs="?", default="MCP1711T-25I/OT")
    parser.add_argument("--anonymous", action="store_true")
    parser.add_argument("--output-dir", default="raw_responses")
    args = parser.parse_args()

    settings = TmeSettings.from_env()
    client = TmeClient(settings)

    print("=" * 50)
    print("TME Connectivity Check")
    print("=" * 50)
    print(f"Auth endpoint   : {settings.base_url}{settings.auth_path}")
    print(f"Search endpoint : {settings.base_url}{settings.search_path}")
    print(f"Country         : {settings.country}")
    print(f"Language        : {settings.language}")
    print(f"Context         : {'anonymous' if args.anonymous else 'customer-linked'}")
    print(f"Searching       : {args.mpn}")

    try:
        payload = client.search_products(args.mpn, anonymous=args.anonymous)
    except Exception as error:
        print("\nConnectivity check failed.")
        print(f"{type(error).__name__}: {error}")
        return 1

    path = _save_raw(payload, args.mpn, Path(args.output_dir))
    items = _find_items(payload)

    print("\nAuthentication and product request succeeded.")
    print(f"Results returned: {len(items)}")
    if items:
        first = items[0]
        print(f"Manufacturer : {_value(first, 'manufacturer', 'brand')}")
        print(f"MPN          : {_value(first, 'mpn', 'manufacturerPartNumber')}")
        print(f"TME symbol   : {_value(first, 'symbol', 'tmeSymbol')}")
        print(f"Description  : {_value(first, 'description', 'name')}")
    else:
        print("The call succeeded; inspect the saved raw response for its exact structure.")
    print(f"Raw response : {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
