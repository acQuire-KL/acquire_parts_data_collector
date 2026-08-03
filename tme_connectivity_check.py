"""Capture the core TME Product API responses for one part."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable

from config import TmeSettings
from knowledge_base_manager import KnowledgeBaseManager
from providers.tme import TmeClient

TME_PROVIDER_NAME = "TME"
ENDPOINT_FOLDERS = {
    "search": "Product_Search",
    "data": "Product_Data",
    "parameters": "Product_Parameters",
}


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


def _save(knowledge_base: KnowledgeBaseManager, payload: dict[str, Any], *,
          endpoint: str, manufacturer: str, mpn: str, settings: TmeSettings,
          anonymous: bool) -> Path:
    knowledge_base.save_raw_provider_response(
        provider=TME_PROVIDER_NAME,
        endpoint=endpoint,
        manufacturer=manufacturer or "Unknown",
        mpn=mpn,
        provider_response=payload,
        input_manufacturer="",
        locale=f"{settings.language}-{settings.country}",
        currency=settings.currency if endpoint == ENDPOINT_FOLDERS["data"] else "",
        request_context="anonymous" if anonymous else "customer-linked",
    )
    return knowledge_base.current_path(
        TME_PROVIDER_NAME, endpoint, manufacturer or "Unknown", mpn
    )


def _save_to_knowledge_base(
    payload: dict[str, Any],
    *,
    mpn: str,
    manufacturer: str,
    settings: TmeSettings,
    anonymous: bool,
    knowledge_base_root: Path,
) -> Path:
    """Compatibility wrapper for the original Product Search capture test."""
    return _save(
        KnowledgeBaseManager(knowledge_base_root),
        payload,
        endpoint=ENDPOINT_FOLDERS["search"],
        manufacturer=manufacturer,
        mpn=mpn,
        settings=settings,
        anonymous=anonymous,
    )


def _run_endpoint(label: str, operation: Callable[[], Path]) -> tuple[bool, Path | None, str]:
    try:
        return True, operation(), ""
    except Exception as error:  # Connectivity utility: report each endpoint independently.
        return False, None, f"{type(error).__name__}: {error}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture TME search, product data and technical parameters."
    )
    parser.add_argument("mpn", nargs="?", default="MCP1711T-25I/OT")
    parser.add_argument("--anonymous", action="store_true")
    parser.add_argument("--knowledge-base", default="Knowledge_Base")
    parser.add_argument(
        "--only", choices=("all", "search", "data", "parameters"), default="all",
        help="Capture all endpoints or one endpoint. Data/parameters use the given MPN as the TME symbol if search is not run or fails.",
    )
    parser.add_argument(
        "--data-scope",
        action="append",
        dest="data_scopes",
        help="TME /products/data scope. Repeat for multiple scopes. Defaults to prices and stock.",
    )
    args = parser.parse_args()

    settings = TmeSettings.from_env()
    client = TmeClient(settings)
    knowledge_base = KnowledgeBaseManager(Path(args.knowledge_base))

    print("=" * 58)
    print("TME Core Product Data Capture")
    print("=" * 58)
    print(f"Part            : {args.mpn}")
    print(f"Country         : {settings.country}")
    print(f"Language        : {settings.language}")
    print(f"Currency        : {settings.currency}")
    print(f"Context         : {'anonymous' if args.anonymous else 'customer-linked'}")
    print(f"Data scopes     : {', '.join(args.data_scopes or TmeClient.DEFAULT_DATA_SCOPES)}")

    try:
        auth_payload = client.obtain_access_token()
        access_token = client._extract_access_token(auth_payload)
    except Exception as error:
        print("\nAuthentication ............. FAIL")
        print(f"    {type(error).__name__}: {error}")
        return 1

    print("\nAuthentication ............. PASS")

    manufacturer = "Unknown"
    symbol = args.mpn
    results: list[tuple[str, bool, Path | None, str]] = []

    if args.only in ("all", "search"):
        def capture_search() -> Path:
            nonlocal manufacturer, symbol
            payload = client.search_products(
                args.mpn, anonymous=args.anonymous, access_token=access_token
            )
            items = _find_items(payload)
            if items:
                manufacturer = _value(items[0], "manufacturer", "brand") or manufacturer
                symbol = _value(items[0], "symbol", "tmeSymbol", "mpn") or symbol
            return _save(
                knowledge_base, payload,
                endpoint=ENDPOINT_FOLDERS["search"], manufacturer=manufacturer,
                mpn=args.mpn, settings=settings, anonymous=args.anonymous,
            )

        ok, path, error = _run_endpoint("Product Search", capture_search)
        results.append(("Product Search", ok, path, error))

    if args.only in ("all", "data"):
        def capture_data() -> Path:
            payload = client.get_product_data(
                symbol,
                scopes=args.data_scopes,
                anonymous=args.anonymous,
                access_token=access_token,
            )
            return _save(
                knowledge_base, payload,
                endpoint=ENDPOINT_FOLDERS["data"], manufacturer=manufacturer,
                mpn=args.mpn, settings=settings, anonymous=args.anonymous,
            )

        ok, path, error = _run_endpoint("Product Data", capture_data)
        results.append(("Product Data", ok, path, error))

    if args.only in ("all", "parameters"):
        def capture_parameters() -> Path:
            payload = client.get_product_parameters(
                symbol, anonymous=args.anonymous, access_token=access_token
            )
            return _save(
                knowledge_base, payload,
                endpoint=ENDPOINT_FOLDERS["parameters"], manufacturer=manufacturer,
                mpn=args.mpn, settings=settings, anonymous=args.anonymous,
            )

        ok, path, error = _run_endpoint("Product Parameters", capture_parameters)
        results.append(("Product Parameters", ok, path, error))

    print("\n" + "-" * 58)
    print("Endpoint Summary")
    print("-" * 58)
    for label, ok, path, error in results:
        print(f"{label:<26} {'PASS' if ok else 'FAIL'}")
        if path:
            print(f"    Saved: {path}")
        if error:
            print(f"    {error}")

    return 0 if all(ok for _, ok, _, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
