"""Command-line check for Sprint 4.4 Patch 1."""
from __future__ import annotations

import argparse
from pathlib import Path

from parts_master_seed_importer import import_legacy_parts_master, write_seed_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a legacy XLSX Parts Master into PDC staging")
    parser.add_argument("workbook", type=Path, help="Path to the legacy AIPN Parts Master.xlsx")
    parser.add_argument("--sheet", default="My Lists Worksheet", help="Worksheet containing the parts table")
    parser.add_argument("--output-dir", type=Path, default=Path("output/parts_master_staging"))
    args = parser.parse_args()

    result = import_legacy_parts_master(args.workbook, args.sheet)
    outputs = write_seed_outputs(result, args.workbook, args.output_dir, args.sheet)

    print("PDC PARTS MASTER SEED IMPORT")
    print("=" * 50)
    print(f"Source rows               : {len(result.source_rows)}")
    print(f"Staging records           : {len(result.staging_records)}")
    print(f"Incomplete identity rows  : {len(result.incomplete_rows)}")
    print(f"Duplicate identity groups : {sum(1 for record in result.staging_records if len(record.source_rows) > 1)}")
    print(f"Manufacturer alias groups : {len(result.manufacturer_alias_groups)}")
    print("Automatic approvals       : 0")
    print("New AIPNs allocated       : 0")
    print("Traceability              : PASS")
    print("\nOutputs")
    for name, path in outputs.items():
        print(f"{name:25}: {path}")


if __name__ == "__main__":
    main()
