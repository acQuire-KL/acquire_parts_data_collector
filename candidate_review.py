"""Generate a human-editable engineering review file from provider candidates.

Sprint 4.5 Patch 1 captures review decisions only.  It never modifies the
Parts Master, allocates AIPNs, approves a candidate automatically, or changes
provider evidence.
"""
from __future__ import annotations

import csv
import hashlib
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Iterable

DECISION_VALUES = ("", "Accept", "Reject", "Defer")


def _text(value: object) -> str:
    return str(value or "").strip()


def _truth(value: object) -> bool:
    return _text(value).casefold() in {"true", "1", "yes", "y"}


def _review_id(record_id: str, provider: str, source_mpn: str) -> str:
    seed = "|".join((_text(record_id).casefold(), _text(provider).casefold(), _text(source_mpn).casefold()))
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10].upper()
    return f"REV-{digest}"


def _evidence(row: dict[str, str]) -> str:
    evidence: list[str] = []
    if _truth(row.get("MPN Exact")):
        evidence.append("Returned MPN matches source MPN")
    if _truth(row.get("Manufacturer Equivalent")):
        evidence.append("Returned manufacturer matches or aliases source manufacturer")
    score = _text(row.get("Manufacturer Score"))
    if score:
        evidence.append(f"Manufacturer similarity score {score}")
    stage = _text(row.get("Source Stage"))
    if stage:
        evidence.append(f"Candidate found by {stage}")
    return "; ".join(evidence)


def load_candidates(path: str | Path) -> list[OrderedDict[str, str]]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "Record ID", "Provider", "Source Manufacturer", "Source MPN",
            "Candidate Rank", "Returned Manufacturer", "Returned MPN",
        }
        missing = sorted(required.difference(reader.fieldnames or []))
        if missing:
            raise ValueError(f"Candidate file is missing columns: {', '.join(missing)}")
        return [OrderedDict((key, _text(value)) for key, value in row.items()) for row in reader]


def build_review_rows(candidates: Iterable[dict[str, str]]) -> list[OrderedDict[str, object]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in candidates:
        key = (_text(row.get("Record ID")), _text(row.get("Provider")), _text(row.get("Source MPN")))
        grouped[key].append(row)

    output: list[OrderedDict[str, object]] = []
    for (record_id, provider, source_mpn), rows in grouped.items():
        ordered = sorted(rows, key=lambda row: int(_text(row.get("Candidate Rank")) or 999999))
        group_id = _review_id(record_id, provider, source_mpn)
        count = len(ordered)
        for row in ordered:
            output.append(OrderedDict([
                ("Review ID", group_id),
                ("Record ID", record_id),
                ("Provider", provider),
                ("Source Manufacturer", _text(row.get("Source Manufacturer"))),
                ("Source MPN", source_mpn),
                ("Candidate Count", count),
                ("Candidate Rank", _text(row.get("Candidate Rank"))),
                ("Candidate Manufacturer", _text(row.get("Returned Manufacturer"))),
                ("Candidate MPN", _text(row.get("Returned MPN"))),
                ("Provider Part Number", _text(row.get("Provider Part Number"))),
                ("Description", _text(row.get("Description"))),
                ("Product URL", _text(row.get("Product URL"))),
                ("Evidence", _evidence(row)),
                ("Review Decision", ""),
                ("Approved Manufacturer", ""),
                ("Approved MPN", ""),
                ("Procurement Variant Group", ""),
                ("Engineer Notes", ""),
                ("Reviewed By", ""),
                ("Reviewed Date", ""),
            ]))
    return output


def write_review_file(candidate_path: str | Path, output_path: str | Path | None = None) -> Path:
    source = Path(candidate_path)
    target = Path(output_path) if output_path else source.with_name(source.name.replace("__CANDIDATES.csv", "__CANDIDATE_REVIEW.csv"))
    if target == source:
        target = source.with_name(source.stem + "__REVIEW.csv")
    rows = build_review_rows(load_candidates(source))
    fields = list(rows[0].keys()) if rows else [
        "Review ID", "Record ID", "Provider", "Source Manufacturer", "Source MPN",
        "Candidate Count", "Candidate Rank", "Candidate Manufacturer", "Candidate MPN",
        "Provider Part Number", "Description", "Product URL", "Evidence", "Review Decision",
        "Approved Manufacturer", "Approved MPN", "Procurement Variant Group", "Engineer Notes",
        "Reviewed By", "Reviewed Date",
    ]
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return target
