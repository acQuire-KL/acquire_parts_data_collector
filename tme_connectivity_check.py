"""Run a live TME Product API v2 authentication and search check."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from config import TmeSettings
from knowledge_base_manager import KnowledgeBaseManager
from providers.tme import TmeClient


TME_PROVIDER_NAME = "TME"
TME_SEARCH_ENDPOINT = "Product_Search"


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


def _returned_manufacturer(payload: dict[str, Any]) -> str:
    items = _find_items(payload)
    if not items:
        return ""
    return _value(items[0], "manufacturer", "brand")


def _save_to_knowledge_base(
    payload: dict[str, Any],
    *,
    mpn: str,
    manufacturer: str,
    settings: TmeSettings,
    anonymous: bool,
    knowledge_base_root: Path,
) -> Path:
    knowledge_base = KnowledgeBaseManager(knowledge_base_root)
    resolved_manufacturer = manufacturer or "Unknown"
    knowledge_base.save_raw_provider_response(
        provider=TME_PROVIDER_NAME,
        endpoint=TME_SEARCH_ENDPOINT,
        manufacturer=resolved_manufacturer,
        mpn=mpn,
        provider_response=payload,
        input_manufacturer="",
        locale=f"{settings.language}-{settings.country}",
        currency="",
        request_context="anonymous" if anonymous else "customer-linked",
    )
    return knowledge_base.current_path(
        TME_PROVIDER_NAME,
        TME_SEARCH_ENDPOINT,
        resolved_manufacturer,
        mpn,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify TME Product API v2 connectivity.")
    parser.add_argument("mpn", nargs="?", default="MCP1711T-25I/OT")
    parser.add_argument("--anonymous", action="store_true")
    parser.add_argument("--knowledge-base", default="Knowledge_Base")
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

    items = _find_items(payload)
    manufacturer = _returned_manufacturer(payload)
    path = _save_to_knowledge_base(
        payload,
        mpn=args.mpn,
        manufacturer=manufacturer,
        settings=settings,
        anonymous=args.anonymous,
        knowledge_base_root=Path(args.knowledge_base),
    )

    print("\nAuthentication and product request succeeded.")
    print(f"Results returned: {len(items)}")
    if items:
        first = items[0]
        print(f"Manufacturer : {_value(first, 'manufacturer', 'brand')}")
        print(f"MPN          : {_value(first, 'mpn', 'manufacturerPartNumber')}")
        print(f"TME symbol   : {_value(first, 'symbol', 'tmeSymbol')}")
        print(f"Description  : {_value(first, 'description', 'name')}")
    else:
        print("The call succeeded; inspect the saved response for its exact structure.")
    print(f"Knowledge Base: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
