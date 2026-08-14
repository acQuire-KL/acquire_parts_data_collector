from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping
from uuid import uuid4


class ReviewDecision(str, Enum):
    """Permitted human review outcomes for a 4.6.2a candidate proposal."""

    PENDING = "Pending"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    NEEDS_VERIFICATION = "Needs Verification"
    NO_SUITABLE_CANDIDATE = "No Suitable Candidate"


FINAL_DECISIONS = {
    ReviewDecision.ACCEPTED,
    ReviewDecision.REJECTED,
    ReviewDecision.NO_SUITABLE_CANDIDATE,
}


@dataclass(frozen=True)
class CandidateSnapshot:
    """
    Immutable snapshot of a candidate returned by Sprint 4.6.2a.

    The original candidate dictionary is never modified.  Unknown 4.6.2a
    fields are retained in raw_candidate so the review record remains useful
    as the matcher evolves.
    """

    manufacturer: str = ""
    mpn: str = ""
    aipn: str = ""
    score: float | None = None
    matched_attributes: tuple[str, ...] = ()
    differences: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    justification: str = ""
    raw_candidate: Mapping[str, Any] | None = None

    @classmethod
    def from_mapping(cls, candidate: Mapping[str, Any]) -> "CandidateSnapshot":
        return cls(
            manufacturer=_pick_text(
                candidate,
                "manufacturer",
                "manufacturer_name",
                "mfg",
                "Manufacturer",
                "MFG",
            ),
            mpn=_pick_text(
                candidate,
                "mpn",
                "manufacturer_part_number",
                "part_number",
                "MPN",
                "Manufacturer Part Number",
            ),
            aipn=_pick_text(candidate, "aipn", "AIPN"),
            score=_pick_float(candidate, "score", "match_score", "confidence_score"),
            matched_attributes=_pick_tuple(
                candidate,
                "matched_attributes",
                "matches",
                "matched",
            ),
            differences=_pick_tuple(
                candidate,
                "differences",
                "mismatches",
                "different_attributes",
            ),
            warnings=_pick_tuple(
                candidate,
                "warnings",
                "verification_warnings",
                "data_quality_warnings",
            ),
            justification=_pick_text(
                candidate,
                "justification",
                "reason",
                "explanation",
            ),
            raw_candidate=dict(candidate),
        )

    @property
    def identity(self) -> str:
        """Stable human-readable identity for the candidate."""
        if self.aipn:
            return self.aipn
        if self.manufacturer or self.mpn:
            return " | ".join(x for x in (self.manufacturer, self.mpn) if x)
        return "UNIDENTIFIED_CANDIDATE"


@dataclass(frozen=True)
class ReviewRecord:
    review_id: str
    review_key: str
    bom_item_key: str
    decision: ReviewDecision
    candidate: CandidateSnapshot | None
    reviewer: str
    comment: str
    reviewed_at_utc: str
    source: str = "PDC Sprint 4.6.2b"
    schema_version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["decision"] = self.decision.value
        return data


class CandidateReviewStore:
    """
    Append-only JSONL store for candidate review decisions.

    Design rules:
      * 4.6.2a matching results are treated as proposals only.
      * A review record never mutates Parts Master or candidate data.
      * Every change of decision creates a new history record.
      * The latest record for a review_key is the current decision.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def record_candidate_decision(
        self,
        *,
        bom_item: Mapping[str, Any] | str,
        candidate: Mapping[str, Any],
        decision: ReviewDecision | str,
        reviewer: str = "",
        comment: str = "",
        reviewed_at_utc: str | None = None,
    ) -> ReviewRecord:
        normalised_decision = _normalise_decision(decision)
        if normalised_decision == ReviewDecision.NO_SUITABLE_CANDIDATE:
            raise ValueError(
                "NO_SUITABLE_CANDIDATE is a BOM-item decision; "
                "use record_no_suitable_candidate()."
            )

        snapshot = CandidateSnapshot.from_mapping(candidate)
        bom_key = bom_item_identity(bom_item)
        review_key = make_review_key(bom_key, snapshot.identity)
        record = ReviewRecord(
            review_id=str(uuid4()),
            review_key=review_key,
            bom_item_key=bom_key,
            decision=normalised_decision,
            candidate=snapshot,
            reviewer=str(reviewer or "").strip(),
            comment=str(comment or "").strip(),
            reviewed_at_utc=reviewed_at_utc or _utc_now(),
        )
        self._append(record)
        return record

    def record_no_suitable_candidate(
        self,
        *,
        bom_item: Mapping[str, Any] | str,
        reviewer: str = "",
        comment: str = "",
        reviewed_at_utc: str | None = None,
    ) -> ReviewRecord:
        bom_key = bom_item_identity(bom_item)
        review_key = make_review_key(bom_key, "NO_SUITABLE_CANDIDATE")
        record = ReviewRecord(
            review_id=str(uuid4()),
            review_key=review_key,
            bom_item_key=bom_key,
            decision=ReviewDecision.NO_SUITABLE_CANDIDATE,
            candidate=None,
            reviewer=str(reviewer or "").strip(),
            comment=str(comment or "").strip(),
            reviewed_at_utc=reviewed_at_utc or _utc_now(),
        )
        self._append(record)
        return record

    def history(self) -> list[ReviewRecord]:
        if not self.path.exists():
            return []

        records: list[ReviewRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(_record_from_dict(json.loads(line)))
                except Exception as exc:
                    raise ValueError(
                        f"Invalid review record at {self.path}:{line_number}: {exc}"
                    ) from exc
        return records

    def latest_by_review_key(self) -> dict[str, ReviewRecord]:
        latest: dict[str, ReviewRecord] = {}
        for record in self.history():
            latest[record.review_key] = record
        return latest

    def latest_for_bom_item(
        self, bom_item: Mapping[str, Any] | str
    ) -> list[ReviewRecord]:
        bom_key = bom_item_identity(bom_item)
        return [
            record
            for record in self.latest_by_review_key().values()
            if record.bom_item_key == bom_key
        ]

    def accepted_candidates(
        self, bom_item: Mapping[str, Any] | str
    ) -> list[ReviewRecord]:
        return [
            record
            for record in self.latest_for_bom_item(bom_item)
            if record.decision == ReviewDecision.ACCEPTED
        ]

    def _append(self, record: ReviewRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def bom_item_identity(bom_item: Mapping[str, Any] | str) -> str:
    """
    Return a stable BOM-item identity.

    Preference order deliberately favours explicit engineering identifiers.
    The fallback is a deterministic hash of the supplied mapping.
    """
    if isinstance(bom_item, str):
        value = bom_item.strip()
        if not value:
            raise ValueError("BOM item identity cannot be blank")
        return value

    preferred_keys = (
        "aipn",
        "AIPN",
        "vtpn",
        "VTPN",
        "lnpn",
        "LNPN",
        "item_number",
        "Item Number",
        "part_number",
        "Part Number",
        "reference_designator",
        "refdes",
        "RefDes",
    )
    for key in preferred_keys:
        value = bom_item.get(key)
        if value is not None and str(value).strip():
            return f"{key}:{str(value).strip()}"

    canonical = json.dumps(dict(bom_item), sort_keys=True, default=str, ensure_ascii=False)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"BOM_ITEM:{digest}"


def make_review_key(bom_item_key: str, candidate_identity: str) -> str:
    text = f"{bom_item_key}::{candidate_identity}".encode("utf-8")
    return hashlib.sha256(text).hexdigest()[:24]


def review_candidates(
    *,
    bom_item: Mapping[str, Any] | str,
    candidates: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """
    Convert 4.6.2a candidates into a review-friendly structure.

    This function is intentionally read-only.  It does not approve, reject,
    re-score or alter the supplied candidates.
    """
    bom_key = bom_item_identity(bom_item)
    output: list[dict[str, Any]] = []
    for rank, candidate in enumerate(candidates, start=1):
        snapshot = CandidateSnapshot.from_mapping(candidate)
        output.append(
            {
                "rank": rank,
                "bom_item_key": bom_key,
                "candidate_identity": snapshot.identity,
                "manufacturer": snapshot.manufacturer,
                "mpn": snapshot.mpn,
                "aipn": snapshot.aipn,
                "score": snapshot.score,
                "matched_attributes": list(snapshot.matched_attributes),
                "differences": list(snapshot.differences),
                "warnings": list(snapshot.warnings),
                "justification": snapshot.justification,
                "review_decision": ReviewDecision.PENDING.value,
            }
        )
    return output


def _normalise_decision(decision: ReviewDecision | str) -> ReviewDecision:
    if isinstance(decision, ReviewDecision):
        return decision

    text = str(decision or "").strip().lower().replace("_", " ")
    aliases = {
        "pending": ReviewDecision.PENDING,
        "accepted": ReviewDecision.ACCEPTED,
        "accept": ReviewDecision.ACCEPTED,
        "rejected": ReviewDecision.REJECTED,
        "reject": ReviewDecision.REJECTED,
        "needs verification": ReviewDecision.NEEDS_VERIFICATION,
        "need verification": ReviewDecision.NEEDS_VERIFICATION,
        "verify": ReviewDecision.NEEDS_VERIFICATION,
        "no suitable candidate": ReviewDecision.NO_SUITABLE_CANDIDATE,
        "none suitable": ReviewDecision.NO_SUITABLE_CANDIDATE,
    }
    if text not in aliases:
        allowed = ", ".join(x.value for x in ReviewDecision)
        raise ValueError(f"Unknown review decision {decision!r}. Allowed: {allowed}")
    return aliases[text]


def _pick_text(mapping: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = mapping.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _pick_float(mapping: Mapping[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = mapping.get(key)
        if value is None or value == "":
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    return None


def _pick_tuple(mapping: Mapping[str, Any], *keys: str) -> tuple[str, ...]:
    for key in keys:
        value = mapping.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            return (value,) if value else ()
        if isinstance(value, Mapping):
            return tuple(f"{k}: {v}" for k, v in value.items())
        try:
            return tuple(str(item) for item in value)
        except TypeError:
            return (str(value),)
    return ()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _record_from_dict(data: Mapping[str, Any]) -> ReviewRecord:
    candidate_data = data.get("candidate")
    candidate = None
    if candidate_data is not None:
        raw_candidate = candidate_data.get("raw_candidate")
        candidate = CandidateSnapshot(
            manufacturer=str(candidate_data.get("manufacturer") or ""),
            mpn=str(candidate_data.get("mpn") or ""),
            aipn=str(candidate_data.get("aipn") or ""),
            score=candidate_data.get("score"),
            matched_attributes=tuple(candidate_data.get("matched_attributes") or ()),
            differences=tuple(candidate_data.get("differences") or ()),
            warnings=tuple(candidate_data.get("warnings") or ()),
            justification=str(candidate_data.get("justification") or ""),
            raw_candidate=raw_candidate,
        )

    return ReviewRecord(
        review_id=str(data["review_id"]),
        review_key=str(data["review_key"]),
        bom_item_key=str(data["bom_item_key"]),
        decision=_normalise_decision(data["decision"]),
        candidate=candidate,
        reviewer=str(data.get("reviewer") or ""),
        comment=str(data.get("comment") or ""),
        reviewed_at_utc=str(data["reviewed_at_utc"]),
        source=str(data.get("source") or "PDC Sprint 4.6.2b"),
        schema_version=str(data.get("schema_version") or "1.0"),
    )
