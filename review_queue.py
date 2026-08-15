from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

from candidate_review import CandidateReviewStore, ReviewDecision, ReviewRecord


ATTENTION_DECISIONS = {
    ReviewDecision.PENDING,
    ReviewDecision.NEEDS_VERIFICATION,
}


@dataclass(frozen=True)
class ReviewQueueCandidate:
    """Current review state for one candidate proposal."""

    bom_item_key: str
    candidate_identity: str
    manufacturer: str
    mpn: str
    aipn: str
    score: float | None
    decision: str
    matched_attributes: tuple[str, ...]
    differences: tuple[str, ...]
    warnings: tuple[str, ...]
    justification: str
    reviewer: str
    comment: str
    reviewed_at_utc: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["matched_attributes"] = list(self.matched_attributes)
        data["differences"] = list(self.differences)
        data["warnings"] = list(self.warnings)
        return data


@dataclass(frozen=True)
class ReviewQueueItem:
    """Current review state for one BOM item."""

    bom_item_key: str
    candidates: tuple[ReviewQueueCandidate, ...]
    no_suitable_candidate: bool
    multiple_acceptances: bool
    needs_attention: bool
    item_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "bom_item_key": self.bom_item_key,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "no_suitable_candidate": self.no_suitable_candidate,
            "multiple_acceptances": self.multiple_acceptances,
            "needs_attention": self.needs_attention,
            "item_status": self.item_status,
        }


def build_review_queue(
    source: CandidateReviewStore | Iterable[ReviewRecord],
) -> list[ReviewQueueItem]:
    """
    Build a deterministic current-state review queue.

    Only the latest record for each review_key contributes to current state.
    Earlier decisions remain in the append-only 4.6.2b history but are not
    duplicated in the queue.

    Ordering:
      1. Items needing attention
      2. Multiple-acceptance conflicts
      3. All other resolved items
      4. Stable lexical BOM-item order within each group
    """
    records = _records_from_source(source)
    latest = _latest_by_review_key(records)

    by_bom: dict[str, list[ReviewRecord]] = defaultdict(list)
    for record in latest.values():
        by_bom[record.bom_item_key].append(record)

    items: list[ReviewQueueItem] = []
    for bom_item_key, item_records in by_bom.items():
        no_suitable = any(
            record.decision == ReviewDecision.NO_SUITABLE_CANDIDATE
            for record in item_records
        )

        candidate_rows = [
            _candidate_row(record)
            for record in item_records
            if record.candidate is not None
        ]
        candidate_rows.sort(key=_candidate_sort_key)

        accepted_count = sum(
            1
            for record in item_records
            if record.candidate is not None
            and record.decision == ReviewDecision.ACCEPTED
        )
        multiple_acceptances = accepted_count > 1

        has_attention_candidate = any(
            record.candidate is not None
            and record.decision in ATTENTION_DECISIONS
            for record in item_records
        )
        needs_attention = has_attention_candidate or multiple_acceptances

        item_status = _derive_item_status(
            item_records=item_records,
            no_suitable_candidate=no_suitable,
            multiple_acceptances=multiple_acceptances,
        )

        items.append(
            ReviewQueueItem(
                bom_item_key=bom_item_key,
                candidates=tuple(candidate_rows),
                no_suitable_candidate=no_suitable,
                multiple_acceptances=multiple_acceptances,
                needs_attention=needs_attention,
                item_status=item_status,
            )
        )

    items.sort(key=_queue_item_sort_key)
    return items


def build_review_summary(
    source: CandidateReviewStore | Iterable[ReviewRecord],
) -> dict[str, Any]:
    """
    Summarise current engineering review state by BOM item and candidate.

    Counts are current-state counts, not historical event counts.
    """
    queue = build_review_queue(source)

    candidate_decisions = Counter()
    total_candidates = 0
    for item in queue:
        for candidate in item.candidates:
            candidate_decisions[candidate.decision] += 1
            total_candidates += 1

    item_statuses = Counter(item.item_status for item in queue)

    return {
        "total_bom_items": len(queue),
        "total_candidates": total_candidates,
        "bom_items_needing_attention": sum(1 for item in queue if item.needs_attention),
        "multiple_acceptance_conflicts": sum(
            1 for item in queue if item.multiple_acceptances
        ),
        "no_suitable_candidate_items": sum(
            1 for item in queue if item.no_suitable_candidate
        ),
        "item_status_counts": dict(sorted(item_statuses.items())),
        "candidate_decision_counts": {
            decision.value: candidate_decisions.get(decision.value, 0)
            for decision in ReviewDecision
            if decision != ReviewDecision.NO_SUITABLE_CANDIDATE
        },
    }


def review_queue_rows(
    source: CandidateReviewStore | Iterable[ReviewRecord],
) -> list[dict[str, Any]]:
    """
    Flatten the review queue for console, CSV, workbook or future GUI use.

    No output file is written here; presentation remains a separate concern.
    """
    rows: list[dict[str, Any]] = []
    for item in build_review_queue(source):
        if not item.candidates:
            rows.append(
                {
                    "bom_item_key": item.bom_item_key,
                    "item_status": item.item_status,
                    "needs_attention": item.needs_attention,
                    "multiple_acceptances": item.multiple_acceptances,
                    "candidate_identity": "",
                    "manufacturer": "",
                    "mpn": "",
                    "aipn": "",
                    "score": None,
                    "decision": ReviewDecision.NO_SUITABLE_CANDIDATE.value
                    if item.no_suitable_candidate
                    else "",
                    "warnings": [],
                    "comment": "",
                }
            )
            continue

        for candidate in item.candidates:
            rows.append(
                {
                    "bom_item_key": item.bom_item_key,
                    "item_status": item.item_status,
                    "needs_attention": item.needs_attention,
                    "multiple_acceptances": item.multiple_acceptances,
                    "candidate_identity": candidate.candidate_identity,
                    "manufacturer": candidate.manufacturer,
                    "mpn": candidate.mpn,
                    "aipn": candidate.aipn,
                    "score": candidate.score,
                    "decision": candidate.decision,
                    "warnings": list(candidate.warnings),
                    "comment": candidate.comment,
                }
            )
    return rows


def _records_from_source(
    source: CandidateReviewStore | Iterable[ReviewRecord],
) -> list[ReviewRecord]:
    if isinstance(source, CandidateReviewStore):
        return source.history()
    return list(source)


def _latest_by_review_key(
    records: Sequence[ReviewRecord],
) -> dict[str, ReviewRecord]:
    latest: dict[str, ReviewRecord] = {}
    for record in records:
        latest[record.review_key] = record
    return latest


def _candidate_row(record: ReviewRecord) -> ReviewQueueCandidate:
    if record.candidate is None:
        raise ValueError("Candidate row requested for a BOM-level review record")

    candidate = record.candidate
    return ReviewQueueCandidate(
        bom_item_key=record.bom_item_key,
        candidate_identity=candidate.identity,
        manufacturer=candidate.manufacturer,
        mpn=candidate.mpn,
        aipn=candidate.aipn,
        score=candidate.score,
        decision=record.decision.value,
        matched_attributes=tuple(candidate.matched_attributes),
        differences=tuple(candidate.differences),
        warnings=tuple(candidate.warnings),
        justification=candidate.justification,
        reviewer=record.reviewer,
        comment=record.comment,
        reviewed_at_utc=record.reviewed_at_utc,
    )


def _candidate_sort_key(candidate: ReviewQueueCandidate) -> tuple[Any, ...]:
    decision_priority = {
        ReviewDecision.PENDING.value: 0,
        ReviewDecision.NEEDS_VERIFICATION.value: 1,
        ReviewDecision.ACCEPTED.value: 2,
        ReviewDecision.REJECTED.value: 3,
    }
    score_sort = -(candidate.score if candidate.score is not None else float("-inf"))
    return (
        decision_priority.get(candidate.decision, 99),
        score_sort,
        candidate.candidate_identity.casefold(),
    )


def _derive_item_status(
    *,
    item_records: Sequence[ReviewRecord],
    no_suitable_candidate: bool,
    multiple_acceptances: bool,
) -> str:
    candidate_decisions = [
        record.decision for record in item_records if record.candidate is not None
    ]

    if multiple_acceptances:
        return "Conflict - Multiple Accepted"
    if ReviewDecision.PENDING in candidate_decisions:
        return "Pending"
    if ReviewDecision.NEEDS_VERIFICATION in candidate_decisions:
        return "Needs Verification"
    if no_suitable_candidate:
        return "No Suitable Candidate"
    if ReviewDecision.ACCEPTED in candidate_decisions:
        return "Accepted"
    if candidate_decisions and all(
        decision == ReviewDecision.REJECTED for decision in candidate_decisions
    ):
        return "All Candidates Rejected"
    if not candidate_decisions:
        return "No Review Candidates"
    return "Reviewed"


def _queue_item_sort_key(item: ReviewQueueItem) -> tuple[int, str]:
    if item.multiple_acceptances:
        priority = 0
    elif item.needs_attention:
        priority = 1
    else:
        priority = 2
    return priority, item.bom_item_key.casefold()
