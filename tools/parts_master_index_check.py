"""CLI check/build utility for Sprint 4.6.1.1 Parts Master Index."""
from __future__ import annotations

import argparse
from pathlib import Path

from parts_master_index import DEFAULT_INDEX_PATH, build_parts_master_index, write_parts_master_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the structured PDC Parts Master Index from the source Parts Master XLSX.")
    parser.add_argument("source", help="Source Parts Master .xlsx")
    parser.add_argument("--output", default=str(DEFAULT_INDEX_PATH), help="Output JSON path")
    parser.add_argument("--sheet", default="My Lists Worksheet", help="Source worksheet name")
    args = parser.parse_args()

    index = build_parts_master_index(Path(args.source), source_sheet=args.sheet)
    output = write_parts_master_index(index, args.output)
    summary = index["index_summary"]

    print(f"Parts Master Index: {output}")
    print(f"Source rows: {index['source']['source_rows']}")
    print(f"Part records: {summary['part_records']}")
    print(f"Records with AIPN: {summary['records_with_aipn']}")
    print(f"Records without AIPN: {summary['records_without_aipn']}")
    print(f"Duplicate identity groups: {summary['duplicate_identity_groups']}")
    print(f"Groups with source conflicts: {summary['groups_with_source_conflicts']}")
    print("Automatic approvals: 0")
    print("New AIPNs allocated: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
