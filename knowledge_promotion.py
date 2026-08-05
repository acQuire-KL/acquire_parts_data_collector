"""Promote completed candidate reviews into reusable engineering knowledge.

Sprint 4.5 Patch 2 reads a human-completed candidate review file and creates
knowledge artefacts only. It never edits the Staging Parts Master, creates an
Approved Parts Master, allocates AIPNs, or makes approval decisions.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import OrderedDict, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ALLOWED_DECISIONS = {"Accept", "Reject", "Defer"}


def _text(value: object) -> str:
    return str(value or "").strip()


def _fold(value: object) -> str:
    return _text(value).casefold()


def _stable_id(prefix: str, *values: object) -> str:
    seed = "|".join(_fold(value) for value in values)
    return f"{prefix}-{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:10].upper()}"


def load_review(path: str | Path) -> list[OrderedDict[str, str]]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "Review ID", "Record ID", "Provider", "Source Manufacturer", "Source MPN",
            "Candidate Manufacturer", "Candidate MPN", "Review Decision",
            "Approved Manufacturer", "Approved MPN", "Engineer Notes",
            "Reviewed By", "Reviewed Date",
        }
        missing = sorted(required.difference(reader.fieldnames or []))
        if missing:
            raise ValueError(f"Review file is missing columns: {', '.join(missing)}")
        return [OrderedDict((key, _text(value)) for key, value in row.items()) for row in reader]


def validate_review_rows(rows: Iterable[dict[str, str]]) -> list[OrderedDict[str, str]]:
    issues: list[OrderedDict[str, str]] = []
    for number, row in enumerate(rows, start=2):
        decision = _text(row.get("Review Decision"))
        if not decision:
            issues.append(OrderedDict([
                ("CSV Row", str(number)), ("Review ID", _text(row.get("Review ID"))),
                ("Record ID", _text(row.get("Record ID"))), ("Severity", "Error"),
                ("Issue", "Review Decision is blank"),
            ]))
            continue
        if decision not in ALLOWED_DECISIONS:
            issues.append(OrderedDict([
                ("CSV Row", str(number)), ("Review ID", _text(row.get("Review ID"))),
                ("Record ID", _text(row.get("Record ID"))), ("Severity", "Error"),
                ("Issue", f"Unsupported Review Decision: {decision}"),
            ]))
        if decision == "Accept":
            if not _text(row.get("Approved Manufacturer")):
                issues.append(OrderedDict([
                    ("CSV Row", str(number)), ("Review ID", _text(row.get("Review ID"))),
                    ("Record ID", _text(row.get("Record ID"))), ("Severity", "Error"),
                    ("Issue", "Accepted candidate has no Approved Manufacturer"),
                ]))
            if not _text(row.get("Approved MPN")):
                issues.append(OrderedDict([
                    ("CSV Row", str(number)), ("Review ID", _text(row.get("Review ID"))),
                    ("Record ID", _text(row.get("Record ID"))), ("Severity", "Error"),
                    ("Issue", "Accepted candidate has no Approved MPN"),
                ]))
            if not _text(row.get("Reviewed By")):
                issues.append(OrderedDict([
                    ("CSV Row", str(number)), ("Review ID", _text(row.get("Review ID"))),
                    ("Record ID", _text(row.get("Record ID"))), ("Severity", "Warning"),
                    ("Issue", "Accepted candidate has no reviewer name"),
                ]))
            if not _text(row.get("Reviewed Date")):
                issues.append(OrderedDict([
                    ("CSV Row", str(number)), ("Review ID", _text(row.get("Review ID"))),
                    ("Record ID", _text(row.get("Record ID"))), ("Severity", "Warning"),
                    ("Issue", "Accepted candidate has no review date"),
                ]))
    return issues


def _group_name(row: dict[str, str]) -> str:
    explicit = _text(row.get("Procurement Variant Group"))
    if explicit:
        return explicit
    # A stable proposed group derived from the reviewed source record. This is
    # an internal relationship identifier, not an AIPN and not an approval.
    return _stable_id("PVG", row.get("Record ID"), row.get("Review ID"))


def promote_review(rows: Iterable[dict[str, str]]) -> dict[str, list[OrderedDict[str, str]]]:
    materialised = list(rows)
    accepted = [row for row in materialised if _text(row.get("Review Decision")) == "Accept"]

    aliases: dict[tuple[str, str], OrderedDict[str, str]] = {}
    variants: dict[tuple[str, str, str], OrderedDict[str, str]] = {}
    additions: dict[tuple[str, str], OrderedDict[str, str]] = {}
    history: list[OrderedDict[str, str]] = []

    accepted_by_review: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in accepted:
        accepted_by_review[_text(row.get("Review ID"))].append(row)

    for row in materialised:
        decision = _text(row.get("Review Decision"))
        history.append(OrderedDict([
            ("Review ID", _text(row.get("Review ID"))),
            ("Record ID", _text(row.get("Record ID"))),
            ("Provider", _text(row.get("Provider"))),
            ("Source Manufacturer", _text(row.get("Source Manufacturer"))),
            ("Source MPN", _text(row.get("Source MPN"))),
            ("Candidate Rank", _text(row.get("Candidate Rank"))),
            ("Candidate Manufacturer", _text(row.get("Candidate Manufacturer"))),
            ("Candidate MPN", _text(row.get("Candidate MPN"))),
            ("Review Decision", decision),
            ("Approved Manufacturer", _text(row.get("Approved Manufacturer"))),
            ("Approved MPN", _text(row.get("Approved MPN"))),
            ("Procurement Variant Group", _text(row.get("Procurement Variant Group"))),
            ("Engineer Notes", _text(row.get("Engineer Notes"))),
            ("Reviewed By", _text(row.get("Reviewed By"))),
            ("Reviewed Date", _text(row.get("Reviewed Date"))),
            ("Evidence", _text(row.get("Evidence"))),
            ("Product URL", _text(row.get("Product URL"))),
        ]))

        if decision != "Accept":
            continue

        standard_name = _text(row.get("Approved Manufacturer"))
        alias_candidates = {
            _text(row.get("Source Manufacturer")),
            _text(row.get("Candidate Manufacturer")),
        }
        for alias in sorted(alias_candidates):
            if alias and _fold(alias) != _fold(standard_name):
                key = (_fold(standard_name), _fold(alias))
                aliases[key] = OrderedDict([
                    ("Standard Manufacturer Name", standard_name),
                    ("Manufacturer Alias", alias),
                    ("Review ID", _text(row.get("Review ID"))),
                    ("Record ID", _text(row.get("Record ID"))),
                    ("Approved By", _text(row.get("Reviewed By"))),
                    ("Approved Date", _text(row.get("Reviewed Date"))),
                    ("Evidence", "Accepted engineering review"),
                ])

        group = _group_name(row)
        variant_key = (_fold(group), _fold(standard_name), _fold(row.get("Approved MPN")))
        variants[variant_key] = OrderedDict([
            ("Procurement Variant Group", group),
            ("Standard Manufacturer Name", standard_name),
            ("Procurement Variant MPN", _text(row.get("Approved MPN"))),
            ("Source MPN", _text(row.get("Source MPN"))),
            ("Relationship", "Approved procurement variant"),
            ("Review ID", _text(row.get("Review ID"))),
            ("Record ID", _text(row.get("Record ID"))),
            ("Engineering Evidence", _text(row.get("Engineer Notes")) or _text(row.get("Evidence"))),
            ("Approved By", _text(row.get("Reviewed By"))),
            ("Approved Date", _text(row.get("Reviewed Date"))),
        ])

        addition_key = (_fold(standard_name), _fold(row.get("Approved MPN")))
        additions[addition_key] = OrderedDict([
            ("Standard Manufacturer Name", standard_name),
            ("Manufacturer Part Number", _text(row.get("Approved MPN"))),
            ("Procurement Variant Group", group),
            ("Source Record ID", _text(row.get("Record ID"))),
            ("Source Manufacturer", _text(row.get("Source Manufacturer"))),
            ("Source MPN", _text(row.get("Source MPN"))),
            ("Description", _text(row.get("Description"))),
            ("Approval Status", "Approved for Parts Master release review"),
            ("Review ID", _text(row.get("Review ID"))),
            ("Approved By", _text(row.get("Reviewed By"))),
            ("Approved Date", _text(row.get("Reviewed Date"))),
            ("Engineer Notes", _text(row.get("Engineer Notes"))),
            ("Provider", _text(row.get("Provider"))),
            ("Product URL", _text(row.get("Product URL"))),
        ])

    return {
        "manufacturer_aliases": sorted(aliases.values(), key=lambda r: (_fold(r["Standard Manufacturer Name"]), _fold(r["Manufacturer Alias"]))),
        "procurement_variants": sorted(variants.values(), key=lambda r: (_fold(r["Procurement Variant Group"]), _fold(r["Procurement Variant MPN"]))),
        "approved_additions": sorted(additions.values(), key=lambda r: (_fold(r["Standard Manufacturer Name"]), _fold(r["Manufacturer Part Number"]))),
        "review_history": history,
    }


def _write_csv(path: Path, rows: list[OrderedDict[str, str]], fallback_fields: list[str]) -> None:
    fields = list(rows[0].keys()) if rows else fallback_fields
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_knowledge_outputs(review_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Path]:
    source = Path(review_path)
    rows = load_review(source)
    issues = validate_review_rows(rows)
    blocking = [issue for issue in issues if issue["Severity"] == "Error"]
    if blocking:
        details = "; ".join(f"row {item['CSV Row']}: {item['Issue']}" for item in blocking[:5])
        raise ValueError(f"Review file contains blocking validation errors: {details}")

    knowledge = promote_review(rows)
    target_dir = Path(output_dir) if output_dir else source.parent / "knowledge_promotion"
    target_dir.mkdir(parents=True, exist_ok=True)
    stem = source.stem.replace("__CANDIDATE_REVIEW", "")

    paths = {
        "manufacturer_aliases": target_dir / f"{stem}__MANUFACTURER_ALIASES.csv",
        "procurement_variants": target_dir / f"{stem}__PROCUREMENT_VARIANTS.csv",
        "approved_additions": target_dir / f"{stem}__APPROVED_ADDITIONS.csv",
        "review_history": target_dir / f"{stem}__REVIEW_HISTORY.csv",
        "validation": target_dir / f"{stem}__VALIDATION.csv",
        "summary": target_dir / f"{stem}__SUMMARY.json",
    }
    _write_csv(paths["manufacturer_aliases"], knowledge["manufacturer_aliases"], [
        "Standard Manufacturer Name", "Manufacturer Alias", "Review ID", "Record ID", "Approved By", "Approved Date", "Evidence"
    ])
    _write_csv(paths["procurement_variants"], knowledge["procurement_variants"], [
        "Procurement Variant Group", "Standard Manufacturer Name", "Procurement Variant MPN", "Source MPN", "Relationship", "Review ID", "Record ID", "Engineering Evidence", "Approved By", "Approved Date"
    ])
    _write_csv(paths["approved_additions"], knowledge["approved_additions"], [
        "Standard Manufacturer Name", "Manufacturer Part Number", "Procurement Variant Group", "Source Record ID", "Source Manufacturer", "Source MPN", "Description", "Approval Status", "Review ID", "Approved By", "Approved Date", "Engineer Notes", "Provider", "Product URL"
    ])
    _write_csv(paths["review_history"], knowledge["review_history"], list(knowledge["review_history"][0].keys()) if knowledge["review_history"] else ["Review ID"])
    _write_csv(paths["validation"], issues, ["CSV Row", "Review ID", "Record ID", "Severity", "Issue"])

    summary = {
        "source_review_file": str(source),
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "review_rows": len(rows),
        "accepted_rows": sum(_text(row.get("Review Decision")) == "Accept" for row in rows),
        "rejected_rows": sum(_text(row.get("Review Decision")) == "Reject" for row in rows),
        "deferred_rows": sum(_text(row.get("Review Decision")) == "Defer" for row in rows),
        "manufacturer_aliases": len(knowledge["manufacturer_aliases"]),
        "procurement_variants": len(knowledge["procurement_variants"]),
        "approved_additions": len(knowledge["approved_additions"]),
        "validation_warnings": sum(issue["Severity"] == "Warning" for issue in issues),
        "parts_master_modified": False,
        "aipns_allocated": 0,
    }
    paths["summary"].write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return paths
