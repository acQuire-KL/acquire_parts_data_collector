"""Operational BOM review helpers for Sprint 4.7.1.

This module joins the existing PDC building blocks into a practical BOM-review
view without adding any automatic approval.  It deliberately keeps provider
results neutral and uses local Parts Master evidence only as additional context.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from manufacturer_resolver import names_equivalent


def _norm_mpn(value: Any) -> str:
    return "".join(ch for ch in str(value or "").upper() if ch.isalnum())


def _text(value: Any) -> str:
    return str(value or "").strip()


@dataclass(frozen=True)
class LocalPartContext:
    status: str = "Not in Parts Master"
    aipn: str = ""
    manufacturer: str = ""
    mpn: str = ""
    description: str = ""
    lifecycle: str = ""
    datasheet_status: str = ""
    datasheet_active_url: str = ""
    datasheet_local_file: str = ""


class PartsMasterLookup:
    """Small read-only MFG+MPN lookup over parts_master_index.json."""

    def __init__(self, index_path: str | Path = "Parts_Master/parts_master_index.json"):
        self.index_path = Path(index_path)
        self.records: list[dict[str, Any]] = []
        if self.index_path.exists():
            payload = json.loads(self.index_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                self.records = [dict(x) for x in payload.get("parts", []) if isinstance(x, dict)]
            elif isinstance(payload, list):
                self.records = [dict(x) for x in payload if isinstance(x, dict)]

    def find(self, manufacturer: str, mpn: str) -> LocalPartContext:
        requested = _norm_mpn(mpn)
        if not requested:
            return LocalPartContext(status="No MPN for Parts Master lookup")

        candidates = [r for r in self.records if _norm_mpn(r.get("MPN")) == requested]
        compatible = [
            r for r in candidates
            if names_equivalent(manufacturer, _text(r.get("Manufacturer")))
        ]
        if len(compatible) != 1:
            if len(compatible) > 1:
                return LocalPartContext(status="Multiple Parts Master Matches")
            return LocalPartContext(status="Not in Parts Master")

        record = compatible[0]
        return LocalPartContext(
            status="Parts Master Match",
            aipn=_text(record.get("AIPN")),
            manufacturer=_text(record.get("Manufacturer")),
            mpn=_text(record.get("MPN")),
            description=_text(record.get("Description")),
            lifecycle=_text(record.get("Product_Status")),
            datasheet_status=_text(record.get("datasheet_status")),
            datasheet_active_url=_text(record.get("datasheet_active_url")) or _text(record.get("Datasheet")),
            datasheet_local_file=_text(record.get("datasheet_local_file")),
        )


def provider_review_observation(
    *,
    match_status: str,
    providers_queried: str,
    providers_matched: str,
    local_context: LocalPartContext,
    lifecycle: str = "",
) -> str:
    """Return a concise engineering-review observation, never an approval."""
    observations: list[str] = []
    if match_status != "Matched":
        observations.append("Identity requires review")
    if not providers_matched:
        observations.append("No provider identity match confirmed")
    if "error" in providers_queried.casefold() or "skipped" in providers_queried.casefold():
        observations.append("Provider collection incomplete")
    if local_context.status == "Parts Master Match":
        observations.append("Existing Parts Master identity")
    elif local_context.status == "Multiple Parts Master Matches":
        observations.append("Ambiguous Parts Master identity")
    lifecycle_text = _text(lifecycle).casefold()
    if any(token in lifecycle_text for token in ("obsolete", "eol", "end of life", "nrnd", "not recommended")):
        observations.append("Lifecycle risk indicated")
    if local_context.datasheet_status and local_context.datasheet_status != "Manufacturer Verified":
        observations.append(f"Datasheet: {local_context.datasheet_status}")
    if not observations:
        observations.append("No immediate review exception identified")
    return "; ".join(observations)


def summary_rows(results: Iterable[Mapping[str, Any]]) -> list[tuple[str, Any]]:
    """Build compact workbook summary metrics from final review rows."""
    items = list(results)
    statuses = Counter(_text(r.get("Match Status")) or "Blank" for r in items)
    local = Counter(_text(r.get("Local Knowledge Status")) or "Blank" for r in items)
    attention = sum(1 for r in items if _text(r.get("Review Observation")) != "No immediate review exception identified")
    rows: list[tuple[str, Any]] = [
        ("BOM Rows Reviewed", len(items)),
        ("Rows Requiring Attention", attention),
    ]
    for status, count in sorted(statuses.items()):
        rows.append((f"Match Status - {status}", count))
    for status, count in sorted(local.items()):
        rows.append((f"Local Knowledge - {status}", count))
    return rows
