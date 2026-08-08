"""Promote candidate-review decisions into one immutable Knowledge History.

Sprint 4.5 Patch 2b removes the overlapping Promoted Knowledge and Review
History outputs introduced during the earlier knowledge-promotion prototypes.
There is now one permanent event history.  Current aliases, approved parts,
procurement-variant groups and review outcomes are *views derived from that
history* rather than separately stored copies of the same knowledge.

No Parts Master is modified, no AIPN is allocated, and no engineering approval
is made by this module.  PDC records only decisions already made by the user.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ALLOWED_DECISIONS = {"Accept", "Reject", "Defer"}

# Human-review fields come first.  The Knowledge History is permanent data,
# but it must also be comfortable for an engineer to open years later.
# Internal record/lifecycle fields deliberately sit to the right.
HISTORY_FIELDS = [
    "Original Manufacturer",
    "Original MPN",
    "Candidate Manufacturer",
    "Candidate MPN",
    "Decision",
    "PDC Justification",
    "Engineer Comment",
    "Product URL",
    "Provider",
    "Knowledge Type",
    "Relationship Type",
    "Relationship Group",
    "Manufacturer Alias",
    "Source Manufacturer Record",
    "Source MPN Record",
    "Knowledge ID",
    "Review ID",
    "Record ID",
    "Effective From",
    "Recorded At UTC",
    "Supersedes",
    "Reviewed By",
    "Reviewed Date",
]

VALIDATION_FIELDS = ["CSV Row", "Review ID", "Record ID", "Severity", "Issue"]


def _text(value: object) -> str:
    return str(value or "").strip()


def _fold(value: object) -> str:
    return _text(value).casefold()


def _stable_id(prefix: str, *values: object) -> str:
    seed = "|".join(_fold(value) for value in values)
    return f"{prefix}-{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:10].upper()}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
    # All candidates from one review/record share the same relationship group.
    return _stable_id("PVG", row.get("Record ID"), row.get("Review ID"))



def _part_event(row: dict[str, str], recorded: str) -> OrderedDict[str, str]:
    decision = _text(row.get("Review Decision"))
    accepted = decision == "Accept"
    standard_name = _text(row.get("Approved Manufacturer")) if accepted else _text(row.get("Candidate Manufacturer"))
    mpn = _text(row.get("Approved MPN")) if accepted else _text(row.get("Candidate MPN"))
    prefix = {"Accept": "AP", "Reject": "RJ", "Defer": "DF"}[decision]
    knowledge_id = _stable_id(
        prefix,
        row.get("Review ID"), row.get("Record ID"), row.get("Candidate Manufacturer"),
        row.get("Candidate MPN"), decision, row.get("Approved Manufacturer"),
        row.get("Approved MPN"), row.get("Reviewed Date"), row.get("Engineer Notes"),
    )
    if accepted:
        knowledge_type = "Approved Part"
        relationship_type = "Procurement Variant"
        relationship_group = _group_name(row)
    else:
        knowledge_type = "Candidate Review"
        relationship_type = ""
        relationship_group = ""

    return OrderedDict([
        ("Knowledge ID", knowledge_id),
        ("Knowledge Type", knowledge_type),
        ("Decision", decision),
        ("Recorded At UTC", recorded),
        ("Effective From", _text(row.get("Reviewed Date"))),
        ("Supersedes", _text(row.get("Supersedes Knowledge ID"))),
        ("Review ID", _text(row.get("Review ID"))),
        ("Record ID", _text(row.get("Record ID"))),
        ("Original Manufacturer", _text(row.get("Source Manufacturer"))),
        ("Original MPN", _text(row.get("Source MPN"))),
        ("Candidate Manufacturer", _text(row.get("Candidate Manufacturer"))),
        ("Candidate MPN", _text(row.get("Candidate MPN"))),
        ("Manufacturer Alias", ""),
        ("Relationship Type", relationship_type),
        ("Relationship Group", relationship_group),
        ("Provider", _text(row.get("Provider"))),
        ("PDC Justification", _text(row.get("Evidence"))),
        ("Engineer Comment", _text(row.get("Engineer Notes"))),
        ("Reviewed By", _text(row.get("Reviewed By"))),
        ("Reviewed Date", _text(row.get("Reviewed Date"))),
        ("Product URL", _text(row.get("Product URL"))),
        ("Source Manufacturer Record", _text(row.get("Source Manufacturer"))),
        ("Source MPN Record", _text(row.get("Source MPN"))),
    ])



def build_knowledge_events(
    rows: Iterable[dict[str, str]],
    recorded_at_utc: str | None = None,
) -> list[OrderedDict[str, str]]:
    """Build one event stream from review decisions.

    Each reviewed candidate creates exactly one knowledge event.  Manufacturer
    alias knowledge is derived from accepted part rows when Original and
    Candidate manufacturer names differ; no separate alias event is stored.
    Reject/Defer outcomes are retained as review knowledge so future learning
    can use the engineer's comment without treating the candidate as approved.
    """
    recorded = recorded_at_utc or _utc_now()
    events: dict[str, OrderedDict[str, str]] = {}
    for row in rows:
        decision = _text(row.get("Review Decision"))
        if decision not in ALLOWED_DECISIONS:
            continue
        part = _part_event(row, recorded)
        events[part["Knowledge ID"]] = part

    return _sort_history_rows(list(events.values()))


def _source_identity(row: dict[str, str]) -> tuple[str, str]:
    """Return the full source identity, including migrated older history rows."""
    manufacturer = _text(row.get("Source Manufacturer Record")) or _text(row.get("Original Manufacturer"))
    mpn = _text(row.get("Source MPN Record")) or _text(row.get("Original MPN"))
    return manufacturer, mpn


def _history_group_key(row: dict[str, str]) -> tuple[str, str]:
    """Stable review subject key used to reconstruct conversation blocks."""
    review_id = _text(row.get("Review ID"))
    record_id = _text(row.get("Record ID"))
    return review_id, record_id


def _repair_source_context(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Repair/migrate source identity before presenting Knowledge History.

    Earlier Patch 2b presentations blanked repeated Original MFG/MPN cells.
    Some later rewrites then inherited the previous visible row, which could
    attach a derived Manufacturer Alias row to the wrong conversation.  The
    immutable knowledge events already carry Review ID + Record ID, so use
    that relationship to rebuild the source identity for *every* row.

    Approved Part / Candidate Review rows are treated as the strongest source
    of the original BOM identity.  This lets an existing history created by an
    older patch be repaired without deleting or recreating any Knowledge IDs.
    """
    source_by_group: dict[tuple[str, str], tuple[str, str]] = {}

    # Pass 1: prefer part/review events because they directly represent the
    # source BOM item.  Visible Original fields are preferred over migrated
    # record fields when both are available.
    for row in rows:
        if _text(row.get("Knowledge Type")) not in {"Approved Part", "Candidate Review"}:
            continue
        group = _history_group_key(row)
        visible = (_text(row.get("Original Manufacturer")), _text(row.get("Original MPN")))
        stored = (_text(row.get("Source Manufacturer Record")), _text(row.get("Source MPN Record")))
        candidates = [candidate for candidate in (visible, stored) if candidate != ("", "")]
        if candidates:
            candidate = max(candidates, key=lambda value: int(bool(value[0])) + 2 * int(bool(value[1])))
            current = source_by_group.get(group, ("", ""))
            if (int(bool(candidate[0])) + 2 * int(bool(candidate[1]))) > (int(bool(current[0])) + 2 * int(bool(current[1]))):
                source_by_group[group] = candidate

    # Pass 2: fall back to any row for legacy histories that predate the
    # Approved Part fields, but never replace the stronger mapping above.
    for row in rows:
        group = _history_group_key(row)
        if group in source_by_group:
            continue
        visible = (_text(row.get("Original Manufacturer")), _text(row.get("Original MPN")))
        stored = (_text(row.get("Source Manufacturer Record")), _text(row.get("Source MPN Record")))
        candidate = visible if visible != ("", "") else stored
        if candidate != ("", ""):
            source_by_group[group] = candidate

    repaired: list[dict[str, str]] = []
    for original in rows:
        row = OrderedDict(original)
        group = _history_group_key(row)
        source = source_by_group.get(group)
        if source:
            row["Source Manufacturer Record"] = source[0]
            row["Source MPN Record"] = source[1]
        repaired.append(row)
    return repaired


def _sort_history_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Group Knowledge History into one visible conversation per source MPN.

    The user's rule is intentionally simple: Original MFG + MPN appear once
    on the first row of a block; every row below belongs to that conversation
    until the next Original MPN appears.  We therefore group by repaired source
    identity, retain the existing part/candidate order inside each conversation,
    and retain only the actual candidate decisions. Manufacturer aliases are
    derived from accepted rows rather than stored as extra history rows.
    """
    repaired = _repair_source_context(rows)
    indexed = list(enumerate(repaired))
    type_order = {"Approved Part": 0, "Candidate Review": 0}

    def key(item):
        index, row = item
        source_mfg, source_mpn = _source_identity(row)
        return (
            _fold(source_mfg),
            _fold(source_mpn),
            type_order.get(_text(row.get("Knowledge Type")), 0),
            index,
        )

    return [row for _, row in sorted(indexed, key=key)]


def _presentation_rows(rows: list[dict[str, str]]) -> list[OrderedDict[str, str]]:
    """Blank repeated visible source identity while retaining it in record fields."""
    presented: list[OrderedDict[str, str]] = []
    previous: tuple[str, str] | None = None
    for original in _sort_history_rows(rows):
        row = OrderedDict((field, _text(original.get(field))) for field in HISTORY_FIELDS)
        source = _source_identity(original)
        row["Source Manufacturer Record"] = source[0]
        row["Source MPN Record"] = source[1]
        if previous == source:
            row["Original Manufacturer"] = ""
            row["Original MPN"] = ""
        else:
            row["Original Manufacturer"] = source[0]
            row["Original MPN"] = source[1]
            previous = source
        presented.append(row)
    return presented


def _write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv_if_present(path: Path) -> list[OrderedDict[str, str]]:
    if not path.exists():
        return []
    rows: list[OrderedDict[str, str]] = []
    previous_source = ("", "")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            row = OrderedDict((key, _text(value)) for key, value in raw.items())
            source_mfg = _text(row.get("Source Manufacturer Record"))
            source_mpn = _text(row.get("Source MPN Record"))
            if not source_mfg and not source_mpn:
                visible = (_text(row.get("Original Manufacturer")), _text(row.get("Original MPN")))
                if visible != ("", ""):
                    previous_source = visible
                source_mfg, source_mpn = previous_source
            row["Source Manufacturer Record"] = source_mfg
            row["Source MPN Record"] = source_mpn
            rows.append(row)
    return rows


def _decision_key(row: dict[str, str]) -> tuple[str, str, str]:
    """Identity of a review subject for automatic supersession linking."""
    if _text(row.get("Knowledge Type")) == "Manufacturer Alias":
        return ("alias", _fold(row.get("Candidate Manufacturer")), _fold(row.get("Manufacturer Alias")))
    return (
        "candidate",
        _fold(row.get("Review ID")),
        _fold(row.get("Candidate Manufacturer")) + "|" + _fold(row.get("Candidate MPN")),
    )


def _append_events(path: Path, new_rows: list[OrderedDict[str, str]]) -> tuple[int, list[OrderedDict[str, str]]]:
    """Append immutable events and link changed decisions by Supersedes.

    Existing rows are never edited.  If a later event for the same review
    subject differs, the new row points back to the latest earlier event.
    Current state is therefore derived from the event graph rather than stored
    by mutating old rows.
    """
    existing = [
        row for row in _read_csv_if_present(path)
        if _text(row.get("Knowledge Type")) != "Manufacturer Alias"
    ]

    # Correction 7: older Patch 2b rewrites could preserve the immutable
    # Knowledge ID while losing the visible Candidate MFG/MPN fields.  The
    # current review file still contains the candidate conversation, so use
    # the freshly rebuilt event with the *same Knowledge ID* to rehydrate
    # presentation/evidence fields.  This is a schema/presentation repair, not
    # a new engineering decision: lifecycle identity, original Knowledge ID
    # and supersession history are preserved.
    incoming_by_id = {_text(row.get("Knowledge ID")): row for row in new_rows}
    repair_fields = [
        "Original Manufacturer", "Original MPN",
        "Candidate Manufacturer", "Candidate MPN",
        "Relationship Type", "Relationship Group",
        "Provider", "PDC Justification", "Engineer Comment",
        "Reviewed By", "Reviewed Date", "Product URL",
        "Source Manufacturer Record", "Source MPN Record",
    ]
    repaired_existing: list[OrderedDict[str, str]] = []
    for old_row in existing:
        row = OrderedDict(old_row)
        fresh = incoming_by_id.get(_text(row.get("Knowledge ID")))
        if fresh is not None:
            for field in repair_fields:
                fresh_value = _text(fresh.get(field))
                if fresh_value:
                    row[field] = fresh_value
        repaired_existing.append(row)
    existing = repaired_existing

    known_ids = {_text(row.get("Knowledge ID")) for row in existing}
    latest_by_key: dict[tuple[str, str, str], str] = {}
    for row in existing:
        latest_by_key[_decision_key(row)] = _text(row.get("Knowledge ID"))

    additions: list[OrderedDict[str, str]] = []
    for incoming in new_rows:
        if incoming["Knowledge ID"] in known_ids:
            continue
        row = OrderedDict(incoming)
        key = _decision_key(row)
        if not _text(row.get("Supersedes")) and key in latest_by_key:
            row["Supersedes"] = latest_by_key[key]
        additions.append(row)
        latest_by_key[key] = row["Knowledge ID"]
        known_ids.add(row["Knowledge ID"])

    combined = existing + additions

    # The Knowledge History is immutable at the record level, but its CSV
    # presentation/schema is allowed to evolve.  Always rewrite the file using
    # the current HISTORY_FIELDS order, even when this run adds no new events.
    # This preserves every existing knowledge row while applying presentation
    # corrections (for example engineer-first column ordering) without asking
    # the user to delete history first.
    _write_csv(path, _presentation_rows(combined), HISTORY_FIELDS)
    return len(additions), combined


def derive_current_knowledge(history: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    """Return the current view without storing a second overlapping file."""
    rows = list(history)
    superseded = {_text(row.get("Supersedes")) for row in rows if _text(row.get("Supersedes"))}
    return [row for row in rows if _text(row.get("Knowledge ID")) not in superseded]


def current_approved_parts(history: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row for row in derive_current_knowledge(history)
        if _text(row.get("Knowledge Type")) == "Approved Part" and _text(row.get("Decision")) == "Accept"
    ]


def current_manufacturer_aliases(history: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    """Derive approved manufacturer aliases from accepted part decisions.

    An accepted row where the Original Manufacturer differs from the Candidate
    Manufacturer already contains the approved relationship.  Storing another
    Manufacturer Alias event would duplicate that same decision.
    """
    aliases: dict[tuple[str, str], OrderedDict[str, str]] = {}
    for row in current_approved_parts(history):
        original = _text(row.get("Source Manufacturer Record")) or _text(row.get("Original Manufacturer"))
        candidate = _text(row.get("Candidate Manufacturer"))
        if not original or not candidate or _fold(original) == _fold(candidate):
            continue
        key = (_fold(candidate), _fold(original))
        aliases.setdefault(key, OrderedDict([
            ("Standard Manufacturer Name", candidate),
            ("Manufacturer Alias", original),
            ("Review ID", _text(row.get("Review ID"))),
            ("Knowledge ID", _text(row.get("Knowledge ID"))),
        ]))
    return list(aliases.values())


def write_knowledge_outputs(review_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Path]:
    source = Path(review_path)
    rows = load_review(source)
    issues = validate_review_rows(rows)
    blocking = [issue for issue in issues if issue["Severity"] == "Error"]
    if blocking:
        details = "; ".join(f"row {item['CSV Row']}: {item['Issue']}" for item in blocking[:5])
        raise ValueError(f"Review file contains blocking validation errors: {details}")

    target_dir = Path(output_dir) if output_dir else source.parent / "knowledge_promotion"
    target_dir.mkdir(parents=True, exist_ok=True)
    stem = source.stem.replace("__CANDIDATE_REVIEW", "")

    paths: dict[str, Path] = {
        "knowledge_history": target_dir / f"{stem}__KNOWLEDGE_HISTORY.csv",
        "summary": target_dir / f"{stem}__SUMMARY.json",
    }
    validation_path = target_dir / f"{stem}__VALIDATION.csv"

    events = build_knowledge_events(rows)
    appended, history = _append_events(paths["knowledge_history"], events)

    if issues:
        paths["validation"] = validation_path
        _write_csv(validation_path, issues, VALIDATION_FIELDS)
    elif validation_path.exists():
        validation_path.unlink()

    current = derive_current_knowledge(history)
    type_counts: dict[str, int] = {}
    for item in history:
        typ = _text(item.get("Knowledge Type"))
        type_counts[typ] = type_counts.get(typ, 0) + 1

    summary = {
        "source_review_file": str(source),
        "generated_at_utc": _utc_now(),
        "review_rows": len(rows),
        "accepted_rows": sum(_text(row.get("Review Decision")) == "Accept" for row in rows),
        "rejected_rows": sum(_text(row.get("Review Decision")) == "Reject" for row in rows),
        "deferred_rows": sum(_text(row.get("Review Decision")) == "Defer" for row in rows),
        "knowledge_events_generated_this_run": len(events),
        "knowledge_history_rows_appended": appended,
        "knowledge_history_total_rows": len(history),
        "knowledge_type_counts": type_counts,
        "current_knowledge_records": len(current),
        "current_approved_parts": len(current_approved_parts(history)),
        "current_manufacturer_aliases": len(current_manufacturer_aliases(history)),
        "validation_warnings": sum(issue["Severity"] == "Warning" for issue in issues),
        "validation_file_created": bool(issues),
        "principles": [
            "Store engineering knowledge once and derive views when needed.",
            "Manufacturer aliases are derived from accepted Original-to-Candidate manufacturer relationships, not duplicated as separate history rows.",
            "Approved engineering knowledge is never deleted or overwritten; later events supersede it.",
            "No part is automatically approved or added to the Parts Master.",
        ],
        "parts_master_modified": False,
        "aipns_allocated": 0,
    }
    paths["summary"].write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return paths
