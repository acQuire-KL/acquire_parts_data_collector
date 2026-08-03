"""Lossless seed import from a legacy XLSX Parts Master into PDC staging.

Sprint 4.4 Patch 1 performs no provider queries, AIPN allocation, or automatic
approval.  The legacy workbook remains unchanged.  Imported identities are
staged as ``Imported - Pending Verification`` and every source row is retained
in the trace output.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
import zipfile
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence
from xml.etree import ElementTree as ET


MANUFACTURER_ALIASES = ("Manufacturer Name", "Manufacturer", "MFG", "MF", "Mfr")
MPN_ALIASES = ("Manufacturer Part Number", "MPN", "Mfr Part Number", "ManufacturerPartNumber")
AIPN_ALIASES = ("AIPN",)
OLD_AIPN_ALIASES = ("AIPN - OLD", "Old AIPN", "Legacy AIPN")
DESCRIPTION_ALIASES = ("Description", "Part Description")
FAMILY_ALIASES = ("Family", "Category")
DATASHEET_ALIASES = ("Datasheet", "Datasheet URL", "Data Sheet")

STATUS_IMPORTED = "Imported - Pending Verification"
_INVALID_CELL_VALUES = {"#n/a", "#value!", "#ref!", "#name?", "false", "none", "null"}


class PartsMasterImportError(ValueError):
    """Raised when the legacy workbook cannot be imported safely."""


def clean_text(value: object) -> str:
    text = " ".join(str(value or "").strip().split())
    return "" if text.casefold() in _INVALID_CELL_VALUES else text


def identity_text(value: object) -> str:
    """Conservative identity normalisation for comparison only."""
    return clean_text(value).casefold()


def manufacturer_alias_key(value: object) -> str:
    """Return a conservative key for spelling/case/diacritic variants.

    This intentionally does not equate abbreviations such as ``TI`` with
    ``Texas Instruments``; those require human approval.
    """
    text = unicodedata.normalize("NFKD", clean_text(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return re.sub(r"[^a-z0-9]+", "", text)


def mpn_key(value: object) -> str:
    """Normalise only whitespace and case; punctuation remains significant."""
    return identity_text(value)


def _normalised_header(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean_text(value).casefold())


def resolve_header(headers: Sequence[str], aliases: Sequence[str], *, required: bool = False) -> str | None:
    lookup = {_normalised_header(header): header for header in headers}
    for alias in aliases:
        match = lookup.get(_normalised_header(alias))
        if match is not None:
            return match
    if required:
        raise PartsMasterImportError(
            f"Required column not found. Expected one of: {', '.join(aliases)}. "
            f"Available columns: {', '.join(headers)}"
        )
    return None


def _column_index(cell_reference: str) -> int:
    letters = "".join(ch for ch in cell_reference if ch.isalpha()).upper()
    index = 0
    for letter in letters:
        index = index * 26 + (ord(letter) - ord("A") + 1)
    return index - 1


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    values: list[str] = []
    for item in root.findall("m:si", ns):
        values.append("".join(node.text or "" for node in item.findall(".//m:t", ns)))
    return values


def _sheet_path(archive: zipfile.ZipFile, sheet_name: str) -> str:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    package_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    rel_targets = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in relationships.findall(f"{{{package_ns}}}Relationship")
    }
    for sheet in workbook.findall(f".//{{{main_ns}}}sheet"):
        if sheet.attrib.get("name") == sheet_name:
            rel_id = sheet.attrib.get(f"{{{rel_ns}}}id")
            target = rel_targets.get(rel_id or "")
            if not target:
                break
            target = target.lstrip("/")
            return target if target.startswith("xl/") else f"xl/{target}"
    raise PartsMasterImportError(f"Worksheet not found: {sheet_name}")


def read_xlsx_rows(path: Path | str, sheet_name: str = "My Lists Worksheet") -> tuple[list[str], list[OrderedDict[str, str]]]:
    """Read a simple tabular XLSX worksheet using the Python standard library."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    with zipfile.ZipFile(source) as archive:
        shared = _shared_strings(archive)
        sheet_xml = ET.fromstring(archive.read(_sheet_path(archive, sheet_name)))
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    matrix: list[list[str]] = []
    for row in sheet_xml.findall(".//m:sheetData/m:row", ns):
        values: dict[int, str] = {}
        max_index = -1
        for cell in row.findall("m:c", ns):
            index = _column_index(cell.attrib.get("r", "A1"))
            max_index = max(max_index, index)
            cell_type = cell.attrib.get("t", "")
            if cell_type == "inlineStr":
                text = "".join(node.text or "" for node in cell.findall(".//m:t", ns))
            else:
                value_node = cell.find("m:v", ns)
                raw = value_node.text if value_node is not None and value_node.text is not None else ""
                if cell_type == "s" and raw:
                    try:
                        text = shared[int(raw)]
                    except (ValueError, IndexError):
                        text = raw
                elif cell_type == "b":
                    text = "TRUE" if raw == "1" else "FALSE"
                else:
                    text = raw
            values[index] = clean_text(text)
        matrix.append([values.get(index, "") for index in range(max_index + 1)])
    if not matrix:
        raise PartsMasterImportError("Worksheet contains no rows")
    headers = [clean_text(value) or f"Unnamed_{index + 1}" for index, value in enumerate(matrix[0])]
    rows: list[OrderedDict[str, str]] = []
    for values in matrix[1:]:
        padded = values + [""] * (len(headers) - len(values))
        record = OrderedDict((header, clean_text(padded[index])) for index, header in enumerate(headers))
        if any(record.values()):
            rows.append(record)
    return headers, rows


@dataclass
class SourcePartRow:
    source_row: int
    values: OrderedDict[str, str]
    manufacturer: str
    mpn: str
    aipn: str = ""
    old_aipn: str = ""
    description: str = ""
    family: str = ""
    datasheet: str = ""

    @property
    def complete_identity(self) -> bool:
        return bool(self.manufacturer and self.mpn)

    def trace_record(self) -> OrderedDict[str, object]:
        return OrderedDict([("source_row", self.source_row), ("values", self.values)])


@dataclass
class StagingPartRecord:
    identity_key: tuple[str, str]
    source_rows: list[SourcePartRow] = field(default_factory=list)

    def append(self, row: SourcePartRow) -> None:
        self.source_rows.append(row)

    def clean_record(self, record_id: str, import_source: str, source_sheet: str) -> OrderedDict[str, object]:
        rows = sorted(self.source_rows, key=lambda row: row.source_row)
        first = rows[0]
        return OrderedDict([
            ("Record ID", record_id),
            ("Record Status", STATUS_IMPORTED),
            ("Manufacturer", first.manufacturer),
            ("Manufacturer Part Number", first.mpn),
            ("Legacy AIPN", _combine_unique(row.aipn for row in rows)),
            ("Legacy AIPN Old", _combine_unique(row.old_aipn for row in rows)),
            ("Legacy Description", _combine_unique(row.description for row in rows)),
            ("Legacy Family", _combine_unique(row.family for row in rows)),
            ("Legacy Datasheet", _combine_unique(row.datasheet for row in rows)),
            ("Import Source", import_source),
            ("Source Sheet", source_sheet),
            ("Duplicate Source Rows", "Yes" if len(rows) > 1 else "No"),
        ])

    def debug_record(self, record_id: str, import_source: str, source_sheet: str) -> OrderedDict[str, object]:
        record = self.clean_record(record_id, import_source, source_sheet)
        record.update([
            ("Identity Key", " | ".join(self.identity_key)),
            ("Source Rows", ", ".join(str(row.source_row) for row in sorted(self.source_rows, key=lambda row: row.source_row))),
            ("Source Data JSON", json.dumps([row.trace_record() for row in self.source_rows], ensure_ascii=False, separators=(",", ":"))),
        ])
        return record


def _combine_unique(values: Iterable[object], separator: str = " | ") -> str:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = clean_text(value)
        marker = text.casefold()
        if text and marker not in seen:
            seen.add(marker)
            result.append(text)
    return separator.join(result)


@dataclass
class SeedImportResult:
    source_headers: list[str]
    source_rows: list[SourcePartRow]
    staging_records: list[StagingPartRecord]
    incomplete_rows: list[SourcePartRow]
    manufacturer_alias_groups: list[list[str]]

    def validate_lossless(self) -> None:
        expected = sorted(row.source_row for row in self.source_rows)
        actual = sorted(
            [row.source_row for record in self.staging_records for row in record.source_rows]
            + [row.source_row for row in self.incomplete_rows]
        )
        if expected != actual:
            raise PartsMasterImportError("Source-row traceability failed: rows were lost or duplicated")


def build_seed_import(headers: Sequence[str], rows: Sequence[Mapping[str, object]]) -> SeedImportResult:
    manufacturer_header = resolve_header(headers, MANUFACTURER_ALIASES, required=True)
    mpn_header = resolve_header(headers, MPN_ALIASES, required=True)
    aipn_header = resolve_header(headers, AIPN_ALIASES)
    old_aipn_header = resolve_header(headers, OLD_AIPN_ALIASES)
    description_header = resolve_header(headers, DESCRIPTION_ALIASES)
    family_header = resolve_header(headers, FAMILY_ALIASES)
    datasheet_header = resolve_header(headers, DATASHEET_ALIASES)

    source_rows: list[SourcePartRow] = []
    groups: OrderedDict[tuple[str, str], StagingPartRecord] = OrderedDict()
    incomplete: list[SourcePartRow] = []
    manufacturer_variants: defaultdict[str, set[str]] = defaultdict(set)

    for offset, source in enumerate(rows, start=2):
        values = OrderedDict((header, clean_text(source.get(header, ""))) for header in headers)
        row = SourcePartRow(
            source_row=offset,
            values=values,
            manufacturer=clean_text(values.get(manufacturer_header or "", "")),
            mpn=clean_text(values.get(mpn_header or "", "")),
            aipn=clean_text(values.get(aipn_header or "", "")),
            old_aipn=clean_text(values.get(old_aipn_header or "", "")),
            description=clean_text(values.get(description_header or "", "")),
            family=clean_text(values.get(family_header or "", "")),
            datasheet=clean_text(values.get(datasheet_header or "", "")),
        )
        source_rows.append(row)
        if row.manufacturer:
            manufacturer_variants[manufacturer_alias_key(row.manufacturer)].add(row.manufacturer)
        if not row.complete_identity:
            incomplete.append(row)
            continue
        key = (manufacturer_alias_key(row.manufacturer), mpn_key(row.mpn))
        groups.setdefault(key, StagingPartRecord(identity_key=key)).append(row)

    aliases = [sorted(values, key=str.casefold) for values in manufacturer_variants.values() if len(values) > 1]
    result = SeedImportResult(
        source_headers=list(headers),
        source_rows=source_rows,
        staging_records=list(groups.values()),
        incomplete_rows=incomplete,
        manufacturer_alias_groups=sorted(aliases, key=lambda group: group[0].casefold()),
    )
    result.validate_lossless()
    return result


def import_legacy_parts_master(path: Path | str, sheet_name: str = "My Lists Worksheet") -> SeedImportResult:
    headers, rows = read_xlsx_rows(path, sheet_name)
    return build_seed_import(headers, rows)


def _write_csv(path: Path, records: Sequence[Mapping[str, object]], headers: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(headers or (records[0].keys() if records else []))
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def write_seed_outputs(
    result: SeedImportResult,
    source_path: Path | str,
    output_dir: Path | str = "output/parts_master_staging",
    sheet_name: str = "My Lists Worksheet",
) -> dict[str, Path]:
    source = Path(source_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    stem = source.stem.replace(" ", "_")

    staging = target / f"{stem}__STAGING.csv"
    debug = target / f"{stem}__STAGING_DEBUG.csv"
    issues = target / f"{stem}__IMPORT_ISSUES.csv"
    duplicates = target / f"{stem}__DUPLICATES.csv"
    aliases = target / f"{stem}__MANUFACTURER_ALIASES.csv"
    trace = target / f"{stem}__TRACE.json"
    summary = target / f"{stem}__SUMMARY.json"

    clean_records: list[OrderedDict[str, object]] = []
    debug_records: list[OrderedDict[str, object]] = []
    duplicate_records: list[OrderedDict[str, object]] = []
    trace_records: list[OrderedDict[str, object]] = []

    for index, record in enumerate(result.staging_records, start=1):
        record_id = f"PMR-{index:06d}"
        clean = record.clean_record(record_id, source.name, sheet_name)
        detailed = record.debug_record(record_id, source.name, sheet_name)
        clean_records.append(clean)
        debug_records.append(detailed)
        trace_records.append(OrderedDict([
            ("record_id", record_id),
            ("identity_key", list(record.identity_key)),
            ("source_rows", [row.trace_record() for row in record.source_rows]),
        ]))
        if len(record.source_rows) > 1:
            duplicate_records.append(detailed)

    issue_records = [OrderedDict([
        ("Source Row", row.source_row),
        ("Issue", "Missing Manufacturer" if not row.manufacturer else "Missing Manufacturer Part Number"),
        ("Manufacturer", row.manufacturer),
        ("Manufacturer Part Number", row.mpn),
        ("Legacy AIPN", row.aipn),
        ("Legacy Description", row.description),
        ("Source Data JSON", json.dumps(row.trace_record(), ensure_ascii=False, separators=(",", ":"))),
    ]) for row in result.incomplete_rows]

    alias_records: list[OrderedDict[str, object]] = []
    for group in result.manufacturer_alias_groups:
        preferred = max(group, key=lambda value: (len(value), value.casefold()))
        for variant in group:
            alias_records.append(OrderedDict([
                ("Alias Key", manufacturer_alias_key(variant)),
                ("Observed Manufacturer", variant),
                ("Suggested Preferred Name", preferred),
                ("Status", "Review Required"),
            ]))

    _write_csv(staging, clean_records)
    _write_csv(debug, debug_records)
    _write_csv(issues, issue_records, ["Source Row", "Issue", "Manufacturer", "Manufacturer Part Number", "Legacy AIPN", "Legacy Description", "Source Data JSON"])
    _write_csv(duplicates, duplicate_records, list(debug_records[0].keys()) if debug_records else [])
    _write_csv(aliases, alias_records, ["Alias Key", "Observed Manufacturer", "Suggested Preferred Name", "Status"])
    trace.write_text(json.dumps({
        "source_file": source.name,
        "source_sheet": sheet_name,
        "records": trace_records,
        "incomplete_source_rows": [row.trace_record() for row in result.incomplete_rows],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    summary.write_text(json.dumps({
        "source_file": source.name,
        "source_sheet": sheet_name,
        "source_rows": len(result.source_rows),
        "staging_records": len(result.staging_records),
        "incomplete_identity_rows": len(result.incomplete_rows),
        "duplicate_identity_groups": sum(1 for record in result.staging_records if len(record.source_rows) > 1),
        "manufacturer_alias_groups": len(result.manufacturer_alias_groups),
        "record_status": STATUS_IMPORTED,
        "automatic_approvals": 0,
        "new_aipns_allocated": 0,
        "lossless_traceability_check": "PASS",
    }, indent=2), encoding="utf-8")

    return {
        "staging_csv": staging,
        "staging_debug_csv": debug,
        "issues_csv": issues,
        "duplicates_csv": duplicates,
        "manufacturer_aliases_csv": aliases,
        "trace_json": trace,
        "summary_json": summary,
    }
