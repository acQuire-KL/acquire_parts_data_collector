"""Build and inspect a normalised TME PDCPartProfile from the Knowledge Base."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from providers.tme.normalizer import build_tme_pdc_part_profile


def _safe_part(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("_")


def _record_path(root: Path, endpoint: str, manufacturer: str, mpn: str) -> Path:
    return root / "Current" / "TME" / endpoint / f"{_safe_part(manufacturer)}__{_safe_part(mpn)}.json"


def _load(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Required TME capture not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _display(profile: dict) -> None:
    identity = profile["identity"]
    technical = profile["technical"]
    commercial = profile["commercial"]
    logistics = profile["logistics"]
    media = profile["media"]

    print("=" * 64)
    print("TME NORMALISED PROVIDER PART PROFILE")
    print("=" * 64)
    print("\nIdentity")
    print("-" * 64)
    print(f"Manufacturer             : {identity['manufacturer']}")
    print(f"Manufacturer part number : {identity['manufacturer_part_number']}")
    print(f"Description              : {identity['description']}")
    print(f"Category                 : {identity['category']}")

    print("\nTechnical")
    print("-" * 64)
    print(f"Component type           : {technical['component_type']}")
    print(f"Regulator type           : {', '.join(technical['regulator_type'])}")
    print(f"Output voltage           : {technical['output_voltage_v']} V")
    print(f"Output current           : {technical['output_current_a']} A")
    print(f"Input voltage            : {technical['input_voltage_min_v']} to {technical['input_voltage_max_v']} V")
    print(f"Package                  : {technical['package']}")
    print(f"Mounting                 : {technical['mounting_type']}")
    print(f"Operating temperature    : {technical['operating_temperature_min_c']} to {technical['operating_temperature_max_c']} °C")
    print(f"Tolerance                : ±{technical['tolerance_percent']} %")

    print("\nCommercial and logistics")
    print("-" * 64)
    print(f"Supplier MOQ             : {commercial['supplier_moq']}")
    print(f"Order multiple           : {commercial['order_multiple']}")
    print(f"Stock                    : {commercial['stock_quantity']} {logistics['sales_unit']}")
    print(f"Listed pack quantity     : {logistics['listed_pack_quantity']}")
    print(f"Manufacturer std. pack   : {logistics['manufacturer_standard_pack_quantity']}")
    print(f"Pack formats             : {', '.join(logistics['pack_formats'])}")
    print(f"Price breaks             : {len(commercial['price_breaks'])} ({commercial['currency']})")

    print("\nMedia and traceability")
    print("-" * 64)
    print(f"Primary image            : {'Yes' if media['primary_image_url'] else 'No'}")
    print(f"Provenance entries       : {len(profile['provenance'])}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalise the three current TME records into one PDCPartProfile."
    )
    parser.add_argument("mpn", nargs="?", default="MCP1711T-25I/OT")
    parser.add_argument("--manufacturer", default="MICROCHIP TECHNOLOGY")
    parser.add_argument("--knowledge-base", default="Knowledge_Base")
    parser.add_argument("--output", default="output/provider_profiles")
    args = parser.parse_args()

    root = Path(args.knowledge_base)
    paths = {
        "search": _record_path(root, "Product_Search", args.manufacturer, args.mpn),
        "data": _record_path(root, "Product_Data", args.manufacturer, args.mpn),
        "parameters": _record_path(root, "Product_Parameters", args.manufacturer, args.mpn),
    }

    profile = build_tme_pdc_part_profile(
        _load(paths["search"]),
        _load(paths["data"]),
        _load(paths["parameters"]),
        raw_references={name: str(path) for name, path in paths.items()},
    )
    result = profile.to_dict()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"TME__{_safe_part(args.manufacturer)}__{_safe_part(args.mpn)}.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)

    _display(result)
    print(f"\nSaved profile            : {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
