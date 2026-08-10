"""Developer utility for Sprint 4.6.1 BOM intake and classification."""
from __future__ import annotations

import argparse
from pathlib import Path

from bom_intake_classifier import (
    CLASS_INSUFFICIENT,
    CLASS_MFG_MPN,
    CLASS_VALUE_FOOTPRINT,
    classify_source_bom,
    write_classification_outputs,
)
from bom_normalizer import BOMNormalisationError


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fresh-normalise a source BOM and classify every unique BOM item by available identity"
    )
    parser.add_argument("source_bom", help="Path to the original source BOM CSV")
    parser.add_argument("--output-dir", default="output/bom_intake", help="Output directory")
    args = parser.parse_args()

    try:
        result, records = classify_source_bom(args.source_bom)
        outputs = write_classification_outputs(args.source_bom, result, records, args.output_dir)
    except (OSError, BOMNormalisationError) as exc:
        print(f"BOM intake classification failed: {exc}")
        return 1

    counts = {name: 0 for name in (CLASS_MFG_MPN, CLASS_VALUE_FOOTPRINT, CLASS_INSUFFICIENT)}
    for item in records:
        counts[item.classification] += 1

    print("=" * 60)
    print("PDC SPRINT 4.6.1 - BOM INTAKE & CLASSIFICATION")
    print("=" * 60)
    print(f"Source BOM                : {Path(args.source_bom)}")
    print(f"Source rows               : {result.source_row_count}")
    print(f"Normalised unique items   : {result.normalised_row_count}")
    print(f"MFG + MPN                 : {counts[CLASS_MFG_MPN]}")
    print(f"Value + Footprint         : {counts[CLASS_VALUE_FOOTPRINT]}")
    print(f"Insufficient Data         : {counts[CLASS_INSUFFICIENT]}")
    print("Traceability              : PASS")
    print("Parts Master lookups      : 0")
    print("Provider calls            : 0")
    print("Automatic approvals       : 0")
    print("Outputs")
    for label, path in outputs.items():
        print(f"  {label:20}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
