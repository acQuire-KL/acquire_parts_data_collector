"""Deterministic, lossless source-BOM normalisation.

Sprint 4.3 Patch 1 deliberately performs no provider lookup, matching,
recommendation, or Parts Master update.  It reorganises source rows while
retaining a complete audit trail back to every original value.
"""
from __future__ import annotations

import csv
import json
import re
import shutil
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence


MFG_ALIASES = ("MFG", "MF", "Manufacturer", "Mfr", "Manufacturer Name")
MPN_ALIASES = ("MPN", "Manufacturer Part Number", "Mfr Part Number", "ManufacturerPartNumber")
REFERENCE_ALIASES = ("Reference", "RefDes", "Reference Designator", "References")
VALUE_ALIASES = ("Value", "Description", "Part Value")
FOOTPRINT_ALIASES = ("Footprint", "Package", "Package / Case")
QUANTITY_ALIASES = ("Qty", "Quantity", "QTY")
DNP_ALIASES = ("DNP", "Do Not Populate", "Do Not Place", "Fitted")
DATASHEET_ALIASES = ("Datasheet", "Datasheet URL", "Data Sheet")

_TRUE_DNP = {"1", "y", "yes", "true", "dnp", "do not populate", "do not place", "not fitted", "nf"}
_FALSE_DNP = {"0", "n", "no", "false", "fitted", "fit", "populate", ""}
_REF_TOKEN = re.compile(r"^\s*([A-Za-z]+)(\d+)(.*)\s*$")


class BOMNormalisationError(ValueError):
    """Raised when a source BOM cannot be normalised safely."""


def _clean_text(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def _normalised_key_text(value: object) -> str:
    return _clean_text(value).casefold()


def _header_lookup(fieldnames: Sequence[str]) -> dict[str, str]:
    return {_normalised_key_text(name): name for name in fieldnames}


def _resolve_header(fieldnames: Sequence[str], aliases: Sequence[str], *, required: bool = False) -> str | None:
    lookup = _header_lookup(fieldnames)
    for alias in aliases:
        actual = lookup.get(_normalised_key_text(alias))
        if actual is not None:
            return actual
    if required:
        raise BOMNormalisationError(
            f"Required column not found. Expected one of: {', '.join(aliases)}. "
            f"Available columns: {', '.join(fieldnames)}"
        )
    return None


def normalise_dnp(value: object, *, source_header: str | None = None) -> bool:
    """Return True for DNP and False for fitted.

    A column explicitly named ``Fitted`` has inverse semantics.
    Unknown non-blank values are rejected rather than silently guessed.
    """
    text = _normalised_key_text(value)
    inverse = _normalised_key_text(source_header) == "fitted"
    if text in _TRUE_DNP:
        result = True
    elif text in _FALSE_DNP:
        result = False
    else:
        raise BOMNormalisationError(f"Unrecognised DNP value: {value!r}")
    return not result if inverse else result


def parse_quantity(value: object) -> float:
    text = _clean_text(value)
    if not text:
        return 1.0
    try:
        number = float(text)
    except ValueError as exc:
        raise BOMNormalisationError(f"Invalid quantity: {value!r}") from exc
    if number < 0:
        raise BOMNormalisationError(f"Quantity cannot be negative: {value!r}")
    return number


def _format_quantity(value: float) -> int | float:
    return int(value) if float(value).is_integer() else value


def split_references(value: object) -> list[str]:
    text = _clean_text(value)
    if not text:
        return []
    # Accept the common separators without splitting suffixes such as R1-R3.
    return [item.strip() for item in re.split(r"[,;\n]+", text) if item.strip()]


def natural_reference_key(reference: str) -> tuple:
    match = _REF_TOKEN.match(reference)
    if not match:
        return (reference.casefold(), -1, "")
    prefix, number, suffix = match.groups()
    return (prefix.casefold(), int(number), suffix.casefold())




def normalised_row_reference_key(group: "NormalisedBOMRow") -> tuple:
    """Sort a normalised group by its first natural Reference Designator.

    Groups without a Reference Designator are placed after referenced groups.
    The complete combined reference and first source row provide deterministic
    tie-breakers without changing grouping behaviour.
    """
    references = [
        reference
        for row in group.source_rows
        for reference in split_references(row.reference)
    ]
    if not references:
        first_source_row = min((row.source_row for row in group.source_rows), default=0)
        return (1, ("", -1, ""), "", first_source_row)
    ordered = sorted(references, key=natural_reference_key)
    first = ordered[0]
    combined = ", ".join(ordered)
    first_source_row = min((row.source_row for row in group.source_rows), default=0)
    return (0, natural_reference_key(first), combined.casefold(), first_source_row)

def combine_references(values: Iterable[object]) -> str:
    unique: dict[str, str] = {}
    for value in values:
        for reference in split_references(value):
            unique.setdefault(reference.casefold(), reference)
    return ", ".join(sorted(unique.values(), key=natural_reference_key))


def _combine_unique(values: Iterable[object], separator: str = " | ") -> str:
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _clean_text(value)
        marker = text.casefold()
        if text and marker not in seen:
            seen.add(marker)
            unique.append(text)
    return separator.join(unique)


@dataclass
class SourceRow:
    source_row: int
    values: OrderedDict[str, str]
    manufacturer: str
    mpn: str
    reference: str
    value: str
    footprint: str
    datasheet: str
    quantity: float
    dnp: bool

    def as_trace_record(self) -> OrderedDict[str, object]:
        return OrderedDict([
            ("source_row", self.source_row),
            ("values", self.values),
        ])


@dataclass
class NormalisedBOMRow:
    group_key: tuple[str, ...]
    grouping_basis: str
    source_rows: list[SourceRow] = field(default_factory=list)

    def append(self, row: SourceRow) -> None:
        self.source_rows.append(row)

    def as_clean_output_record(self) -> OrderedDict[str, object]:
        """Return the engineer-facing normalised BOM row.

        Development-only grouping and trace fields are deliberately excluded.
        Full traceability remains available in the debug CSV and TRACE.json.
        """
        rows = sorted(self.source_rows, key=lambda item: item.source_row)
        return OrderedDict([
            ("MFG", _combine_unique(row.manufacturer for row in rows)),
            ("MPN", _combine_unique(row.mpn for row in rows)),
            ("Value", _combine_unique(row.value for row in rows)),
            ("Datasheet", _combine_unique(row.datasheet for row in rows)),
            ("Footprint", _combine_unique(row.footprint for row in rows)),
            ("Quantity", _format_quantity(sum(row.quantity for row in rows))),
            ("Reference", combine_references(row.reference for row in rows)),
            ("DNP", "Yes" if rows[0].dnp else "No"),
        ])

    def as_debug_output_record(self) -> OrderedDict[str, object]:
        """Return the normalised row plus development trace fields."""
        rows = sorted(self.source_rows, key=lambda item: item.source_row)
        record = self.as_clean_output_record()
        record.update([
            ("Grouping Basis", self.grouping_basis),
            ("Source Rows", ", ".join(str(row.source_row) for row in rows)),
            ("Source Data JSON", json.dumps([row.as_trace_record() for row in rows], ensure_ascii=False, separators=(",", ":"))),
        ])
        return record

    def as_output_record(self) -> OrderedDict[str, object]:
        """Backward-compatible alias for the detailed development record."""
        return self.as_debug_output_record()


@dataclass
class BOMNormalisationResult:
    source_headers: list[str]
    source_rows: list[SourceRow]
    normalised_rows: list[NormalisedBOMRow]

    @property
    def source_row_count(self) -> int:
        return len(self.source_rows)

    @property
    def normalised_row_count(self) -> int:
        return len(self.normalised_rows)

    def validate_lossless(self) -> None:
        expected = [row.source_row for row in self.source_rows]
        actual = [row.source_row for group in self.normalised_rows for row in group.source_rows]
        if sorted(expected) != sorted(actual):
            raise BOMNormalisationError("Source-row traceability check failed: rows were lost or duplicated")
        if len(actual) != len(set(actual)):
            raise BOMNormalisationError("Source-row traceability check failed: a source row contributed more than once")


def _build_group_key(row: SourceRow) -> tuple[tuple[str, ...], str]:
    dnp_key = "dnp" if row.dnp else "fitted"
    manufacturer = _normalised_key_text(row.manufacturer)
    mpn = _normalised_key_text(row.mpn)
    if mpn:
        return ("mfg_mpn", manufacturer, mpn, dnp_key), "MFG + MPN + DNP"
    return (
        "fallback",
        manufacturer,
        _normalised_key_text(row.value),
        _normalised_key_text(row.footprint),
        dnp_key,
    ), "MFG + Value + Footprint + DNP (MPN blank)"


def normalise_rows(rows: Sequence[Mapping[str, object]], fieldnames: Sequence[str], *, first_data_row: int = 2) -> BOMNormalisationResult:
    mfg_col = _resolve_header(fieldnames, MFG_ALIASES)
    mpn_col = _resolve_header(fieldnames, MPN_ALIASES)
    reference_col = _resolve_header(fieldnames, REFERENCE_ALIASES, required=True)
    value_col = _resolve_header(fieldnames, VALUE_ALIASES)
    footprint_col = _resolve_header(fieldnames, FOOTPRINT_ALIASES)
    quantity_col = _resolve_header(fieldnames, QUANTITY_ALIASES)
    dnp_col = _resolve_header(fieldnames, DNP_ALIASES)
    datasheet_col = _resolve_header(fieldnames, DATASHEET_ALIASES)

    source_rows: list[SourceRow] = []
    grouped: OrderedDict[tuple[str, ...], NormalisedBOMRow] = OrderedDict()

    for offset, raw in enumerate(rows):
        source_row_number = first_data_row + offset
        values = OrderedDict((header, str(raw.get(header, "") or "")) for header in fieldnames)
        if not any(_clean_text(value) for value in values.values()):
            continue
        source = SourceRow(
            source_row=source_row_number,
            values=values,
            manufacturer=_clean_text(raw.get(mfg_col, "")) if mfg_col else "",
            mpn=_clean_text(raw.get(mpn_col, "")) if mpn_col else "",
            reference=_clean_text(raw.get(reference_col, "")),
            value=_clean_text(raw.get(value_col, "")) if value_col else "",
            footprint=_clean_text(raw.get(footprint_col, "")) if footprint_col else "",
            datasheet=_clean_text(raw.get(datasheet_col, "")) if datasheet_col else "",
            quantity=parse_quantity(raw.get(quantity_col, "")) if quantity_col else 1.0,
            dnp=normalise_dnp(raw.get(dnp_col, ""), source_header=dnp_col) if dnp_col else False,
        )
        source_rows.append(source)
        key, basis = _build_group_key(source)
        grouped.setdefault(key, NormalisedBOMRow(key, basis)).append(source)

    result = BOMNormalisationResult(list(fieldnames), source_rows, list(grouped.values()))
    result.validate_lossless()
    return result


def normalise_csv(source_path: str | Path) -> BOMNormalisationResult:
    path = Path(source_path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise BOMNormalisationError("Source BOM has no header row")
        return normalise_rows(list(reader), reader.fieldnames)


def write_outputs(result: BOMNormalisationResult, source_path: str | Path, output_dir: str | Path) -> dict[str, Path]:
    source = Path(source_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    stem = source.stem

    source_copy = destination / f"{stem}__SOURCE.csv"
    normalised_csv = destination / f"{stem}__NORMALISED.csv"
    normalised_debug_csv = destination / f"{stem}__NORMALISED_DEBUG.csv"
    trace_json = destination / f"{stem}__TRACE.json"
    summary_json = destination / f"{stem}__SUMMARY.json"

    shutil.copyfile(source, source_copy)

    output_groups = sorted(result.normalised_rows, key=normalised_row_reference_key)

    clean_records = [group.as_clean_output_record() for group in output_groups]
    clean_headers = list(clean_records[0].keys()) if clean_records else [
        "MFG", "MPN", "Value", "Datasheet", "Footprint", "Quantity", "Reference", "DNP",
    ]
    with normalised_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=clean_headers)
        writer.writeheader()
        writer.writerows(clean_records)

    debug_records = [group.as_debug_output_record() for group in output_groups]
    debug_headers = list(debug_records[0].keys()) if debug_records else [
        "MFG", "MPN", "Value", "Datasheet", "Footprint", "Quantity", "Reference",
        "DNP", "Grouping Basis", "Source Rows", "Source Data JSON",
    ]
    with normalised_debug_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=debug_headers)
        writer.writeheader()
        writer.writerows(debug_records)

    trace = OrderedDict([
        ("source_file", source.name),
        ("source_headers", result.source_headers),
        ("source_rows", [row.as_trace_record() for row in result.source_rows]),
        ("normalised_groups", [
            OrderedDict([
                ("grouping_basis", group.grouping_basis),
                ("group_key", list(group.group_key)),
                ("source_rows", [row.source_row for row in group.source_rows]),
            ])
            for group in result.normalised_rows
        ]),
    ])
    trace_json.write_text(json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8")

    fallback_count = sum(1 for group in result.normalised_rows if group.grouping_basis.startswith("MFG + Value"))
    dnp_count = sum(1 for group in result.normalised_rows if group.source_rows and group.source_rows[0].dnp)
    summary = OrderedDict([
        ("source_file", source.name),
        ("source_rows", result.source_row_count),
        ("normalised_rows", result.normalised_row_count),
        ("rows_consolidated", result.source_row_count - result.normalised_row_count),
        ("groups_with_mpn", result.normalised_row_count - fallback_count),
        ("groups_without_mpn", fallback_count),
        ("dnp_groups", dnp_count),
        ("lossless_traceability_check", "PASS"),
    ])
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return {
        "source_copy": source_copy,
        "normalised_csv": normalised_csv,
        "normalised_debug_csv": normalised_debug_csv,
        "trace_json": trace_json,
        "summary_json": summary_json,
    }
