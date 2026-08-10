"""Sprint 4.6.1 BOM intake classification.

Classifies every *normalised* BOM row by the identity information already
present in the source BOM.  This stage performs no Parts Master lookup,
provider search, recommendation, or approval.

The classifier intentionally works from a freshly normalised source BOM so
that generated output from an earlier run is never used as source data.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from bom_normalizer import BOMNormalisationResult, NormalisedBOMRow, normalise_csv, normalised_row_reference_key


CLASS_MFG_MPN = "MFG + MPN"
CLASS_VALUE_FOOTPRINT = "Value + Footprint"
CLASS_INSUFFICIENT = "Insufficient Data"


@dataclass(frozen=True)
class BOMIntakeRecord:
    classification: str
    classification_reason: str
    next_action: str
    normalised_record: OrderedDict[str, object]

    def as_output_record(self) -> OrderedDict[str, object]:
        record: OrderedDict[str, object] = OrderedDict()
        record["Classification"] = self.classification
        record["Classification Reason"] = self.classification_reason
        record["Next Action"] = self.next_action
        # Preserve the existing engineer-facing normalised BOM column order.
        record.update(self.normalised_record)
        return record


def _clean(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def classify_normalised_row(row: NormalisedBOMRow) -> BOMIntakeRecord:
    record = row.as_clean_output_record()
    manufacturer = _clean(record.get("MFG"))
    mpn = _clean(record.get("MPN"))
    value = _clean(record.get("Value"))
    footprint = _clean(record.get("Footprint"))

    if manufacturer and mpn:
        return BOMIntakeRecord(
            classification=CLASS_MFG_MPN,
            classification_reason="Manufacturer and Manufacturer Part Number are present.",
            next_action="Parts Master MFG + MPN lookup",
            normalised_record=record,
        )

    # Descriptive identification is used only where the MPN is absent.  An MPN
    # without a manufacturer is intentionally not guessed into this path.
    if not mpn and value and footprint:
        return BOMIntakeRecord(
            classification=CLASS_VALUE_FOOTPRINT,
            classification_reason="MPN is blank; Value and Footprint are available for descriptive matching.",
            next_action="Parts Master Value + Footprint lookup",
            normalised_record=record,
        )

    missing: list[str] = []
    if mpn and not manufacturer:
        missing.append("Manufacturer")
    elif manufacturer and not mpn and not (value and footprint):
        missing.append("MPN or complete Value + Footprint")
    else:
        if not value:
            missing.append("Value")
        if not footprint:
            missing.append("Footprint")
        if not mpn and not manufacturer and not missing:
            missing.append("identity data")

    detail = ", ".join(missing) if missing else "usable identity data"
    return BOMIntakeRecord(
        classification=CLASS_INSUFFICIENT,
        classification_reason=f"Insufficient identity for the current matching paths; missing {detail}.",
        next_action="Engineer review / additional source information",
        normalised_record=record,
    )


def classify_result(result: BOMNormalisationResult) -> list[BOMIntakeRecord]:
    result.validate_lossless()
    return [classify_normalised_row(row) for row in sorted(result.normalised_rows, key=normalised_row_reference_key)]


def classify_source_bom(source_bom: str | Path) -> tuple[BOMNormalisationResult, list[BOMIntakeRecord]]:
    result = normalise_csv(source_bom)
    return result, classify_result(result)


def write_classification_outputs(
    source_bom: str | Path,
    result: BOMNormalisationResult,
    records: Iterable[BOMIntakeRecord],
    output_dir: str | Path = "output/bom_intake",
) -> dict[str, Path]:
    source_path = Path(source_bom)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    stem = source_path.stem

    records_list = list(records)
    csv_path = destination / f"{stem}__BOM_INTAKE.csv"
    summary_path = destination / f"{stem}__BOM_INTAKE_SUMMARY.json"

    fieldnames = [
        "Classification",
        "Classification Reason",
        "Next Action",
        "MFG",
        "MPN",
        "Value",
        "Datasheet",
        "Footprint",
        "Quantity",
        "Reference",
        "DNP",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for item in records_list:
            writer.writerow(item.as_output_record())

    counts = Counter(item.classification for item in records_list)
    summary = OrderedDict([
        ("source_bom", str(source_path)),
        ("source_rows", result.source_row_count),
        ("normalised_rows", result.normalised_row_count),
        ("classified_rows", len(records_list)),
        ("classification_counts", OrderedDict([
            (CLASS_MFG_MPN, counts.get(CLASS_MFG_MPN, 0)),
            (CLASS_VALUE_FOOTPRINT, counts.get(CLASS_VALUE_FOOTPRINT, 0)),
            (CLASS_INSUFFICIENT, counts.get(CLASS_INSUFFICIENT, 0)),
        ])),
        ("traceability_check", "PASS"),
        ("provider_calls", 0),
        ("parts_master_lookups", 0),
        ("automatic_approvals", 0),
    ])
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {"classification_csv": csv_path, "summary_json": summary_path}
