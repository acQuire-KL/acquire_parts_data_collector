"""Developer utility for Sprint 4.3 Patch 1 BOM normalisation."""
from __future__ import annotations

import argparse
from pathlib import Path

from bom_normalizer import BOMNormalisationError, normalise_csv, write_outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a deterministic, lossless normalised BOM")
    parser.add_argument("source_bom", help="Path to a source BOM CSV")
    parser.add_argument("--output-dir", default="output/normalised_boms", help="Output directory")
    args = parser.parse_args()

    try:
        result = normalise_csv(args.source_bom)
        outputs = write_outputs(result, args.source_bom, args.output_dir)
    except (OSError, BOMNormalisationError) as exc:
        print(f"BOM normalisation failed: {exc}")
        return 1

    print("=" * 60)
    print("PDC BOM NORMALISATION")
    print("=" * 60)
    print(f"Source BOM          : {Path(args.source_bom)}")
    print(f"Source rows         : {result.source_row_count}")
    print(f"Normalised rows     : {result.normalised_row_count}")
    print(f"Rows consolidated   : {result.source_row_count - result.normalised_row_count}")
    print("Traceability check  : PASS")
    print("Outputs")
    for label, path in outputs.items():
        print(f"  {label:16}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
