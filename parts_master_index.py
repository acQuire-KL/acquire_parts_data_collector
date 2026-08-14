"""Build the PDC Parts Master Index from the current Parts Master source.

Sprint 4.6.1.1 establishes a machine-native, structured Parts Master dataset.
The index contains one record per unique Manufacturer + MPN identity.  AIPN is
optional: where it is not yet allocated the record remains valid and is
identified externally by Manufacturer + MPN.

This module deliberately does not call providers, allocate AIPNs, approve
parts, or infer engineering attributes from free-text descriptions.
"""
from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from parts_master_seed_importer import (
    build_seed_import,
    clean_text,
    read_xlsx_rows,
)

DEFAULT_SOURCE_SHEET = "My Lists Worksheet"
DEFAULT_INDEX_PATH = Path("Parts_Master/parts_master_index.json")
SCHEMA_VERSION = "1.0"


def _none_if_blank(value: object):
    text = clean_text(value)
    return text if text else None


def _unique_values(rows: Iterable[Mapping[str, object]], field: str) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for row in rows:
        value = clean_text(row.get(field, ""))
        marker = value.casefold()
        if value and marker not in seen:
            seen.add(marker)
            values.append(value)
    return values


def _first_value(rows: Sequence[Mapping[str, object]], field: str):
    for row in rows:
        value = _none_if_blank(row.get(field, ""))
        if value is not None:
            return value
    return None


def _conflicts(rows: Sequence[Mapping[str, object]], fields: Sequence[str]) -> OrderedDict[str, list[str]]:
    result: OrderedDict[str, list[str]] = OrderedDict()
    for field in fields:
        values = _unique_values(rows, field)
        if len(values) > 1:
            result[field] = values
    return result


def _record_from_group(record_id: str, staging_record, source_file: str, source_sheet: str) -> OrderedDict:
    source_rows = sorted(staging_record.source_rows, key=lambda item: item.source_row)
    rows = [row.values for row in source_rows]

    aipns = _unique_values(rows, "AIPN")
    legacy_old = _unique_values(rows, "AIPN - OLD")

    # Every field below is sourced directly from the current Parts Master.
    # No description parsing or provider inference occurs in this foundation step.
    record = OrderedDict([
        ("Record_ID", record_id),
        ("AIPN", aipns[0] if len(aipns) == 1 else None),
        ("Manufacturer", source_rows[0].manufacturer),
        ("MPN", source_rows[0].mpn),
        ("Family", _first_value(rows, "Family")),
        ("Description", _first_value(rows, "Description")),
        ("Value_Nominal", _first_value(rows, "Value")),
        ("Footprint", _first_value(rows, "Case")),
        ("Package_Secondary", _first_value(rows, "Case2")),
        ("Mounting_Type", _first_value(rows, "Case3")),
        ("Package_Display", _first_value(rows, "Case Displayed as")),
        ("Product_Status", _first_value(rows, "Lifecycle")),
        ("Lead_Time_Weeks", _first_value(rows, "Leadtime(WKS)")),
        ("Datasheet", _first_value(rows, "Datasheet")),
        ("Image", _first_value(rows, "Image")),
        ("RoHS_Status", _first_value(rows, "RoHS Status")),
        ("MSL", _first_value(rows, "Moisture Sensitivity Level (MSL)")),
        ("ECCN", _first_value(rows, "ECCN")),
        ("HTSUS", _first_value(rows, "HTSUS")),
        ("Country_of_Origin", _first_value(rows, "Country of Origin")),
        ("Legacy_AIPN", aipns[0] if len(aipns) == 1 else None),
        ("Legacy_AIPN_Old", " | ".join(legacy_old) if legacy_old else None),
        ("Legacy_Parameters", OrderedDict([
            ("Param_1", _first_value(rows, "Param #1")),
            ("Param_2", _first_value(rows, "Param #2")),
            ("Param_3", _first_value(rows, "Param #3")),
            ("Param_4", _first_value(rows, "Param #4")),
            ("Revision", _first_value(rows, "Rev")),
        ])),
        ("Identity_Basis", "AIPN" if len(aipns) == 1 else "MFG+MPN"),
        ("Source_File", source_file),
        ("Source_Sheet", source_sheet),
        ("Source_Rows", [row.source_row for row in source_rows]),
        ("Duplicate_Source_Rows", len(source_rows) > 1),
    ])

    # Duplicate source rows are preserved as one part identity.  Any differing
    # source attributes are surfaced rather than silently discarded.
    conflicts = _conflicts(rows, [
        "AIPN", "Family", "Value", "Case", "Description", "Lifecycle",
        "Leadtime(WKS)", "Case2", "Case3", "Case Displayed as",
        "Param #1", "Param #2", "Param #3", "Param #4", "Datasheet",
        "RoHS Status", "Moisture Sensitivity Level (MSL)", "ECCN", "HTSUS",
        "Country of Origin",
    ])
    record["Source_Conflicts"] = conflicts
    return record


def build_parts_master_index(source_path: str | Path, *, source_sheet: str = DEFAULT_SOURCE_SHEET) -> OrderedDict:
    source = Path(source_path)
    headers, rows = read_xlsx_rows(source, sheet_name=source_sheet)
    seed = build_seed_import(headers, rows)
    seed.validate_lossless()

    records = [
        _record_from_group(
            f"PMR-{index:06d}",
            staging_record,
            source.name,
            source_sheet,
        )
        for index, staging_record in enumerate(seed.staging_records, start=1)
    ]

    with_aipn = sum(1 for record in records if record["AIPN"])
    without_aipn = len(records) - with_aipn
    duplicate_groups = sum(1 for record in records if record["Duplicate_Source_Rows"])
    conflict_groups = sum(1 for record in records if record["Source_Conflicts"])

    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("source", OrderedDict([
            ("file", source.name),
            ("sheet", source_sheet),
            ("source_rows", len(seed.source_rows)),
        ])),
        ("index_summary", OrderedDict([
            ("part_records", len(records)),
            ("records_with_aipn", with_aipn),
            ("records_without_aipn", without_aipn),
            ("duplicate_identity_groups", duplicate_groups),
            ("groups_with_source_conflicts", conflict_groups),
            ("automatic_approvals", 0),
            ("new_aipns_allocated", 0),
        ])),
        ("parts", records),
    ])


def write_parts_master_index(index: Mapping, output_path: str | Path = DEFAULT_INDEX_PATH) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output
