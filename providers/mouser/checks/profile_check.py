"""Build and inspect a normalised Mouser PDCPartProfile from the Knowledge Base."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from providers.mouser.normalizer import build_mouser_pdc_part_profile


def _safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("_")


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalise a current Mouser record into one PDCPartProfile.")
    parser.add_argument("mpn", nargs="?", default="MCP1711T-25I/OT")
    parser.add_argument("--manufacturer", default="Microchip Technology")
    parser.add_argument("--knowledge-base", default="Knowledge_Base")
    parser.add_argument("--output", default="output/provider_profiles")
    args = parser.parse_args()

    folder = Path(args.knowledge_base) / "Current" / "Mouser" / "Part_Number_Search"
    path = folder / f"{_safe(args.manufacturer)}__{_safe(args.mpn)}.json"
    if not path.exists():
        matches = list(folder.glob(f"*__{_safe(args.mpn)}.json"))
        path = matches[0] if matches else path
    if not path.exists():
        raise FileNotFoundError(f"Required Mouser capture not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        record = json.load(handle)
    profile = build_mouser_pdc_part_profile(
        record,
        raw_references={"part_number_search": str(path)},
    ).to_dict()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"MOUSER__{_safe(profile['identity']['manufacturer'])}__{_safe(args.mpn)}.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(profile, handle, indent=2, ensure_ascii=False)

    print("MOUSER NORMALISED PDC PART PROFILE")
    print("Manufacturer :", profile["identity"]["manufacturer"])
    print("MPN          :", profile["identity"]["manufacturer_part_number"])
    print("Offers       :", len(profile["commercial"]["offers"]))
    print("Price breaks :", len(profile["commercial"]["price_breaks"]))
    print("Saved profile:", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
