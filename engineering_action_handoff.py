from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping
from uuid import uuid4

from candidate_review import CandidateReviewStore, ReviewDecision, ReviewRecord


class EngineeringAction(str, Enum):
    """Permitted proposed engineering handoff actions."""

    PROPOSE_AVL_ADDITION = "Propose AVL Addition"
    PROPOSE_BOM_CHANGE = "Propose BOM Change"
    TEMPORARY_CONCESSION_DEVIATION = "Temporary Concession/Deviation Required"
    NO_ACTION_REFERENCE_ONLY = "No Action / Reference Only"
    NEEDS_ENGINEERING_CLASSIFICATION = "Needs Engineering Classification"


@dataclass(frozen=True)
class EngineeringActionProposal:
    proposal_id: str
    proposal_key: str
    bom_item_key: str
    candidate_identity: str
    manufacturer: str
    mpn: str
    aipn: str
    match_score: float | None
    review_id: str
    review_decision: str
    review_reviewer: str
    review_comment: str
    review_warnings: tuple[str, ...]
    review_justification: str
    proposed_action: EngineeringAction
    action_reason: str
    action_context: Mapping[str, Any]
    created_at_utc: str
    source: str = "PDC Sprint 4.6.2d"
    schema_version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["proposed_action"] = self.proposed_action.value
        data["review_warnings"] = list(self.review_warnings)
        data["action_context"] = dict(self.action_context)
        return data


def propose_engineering_action(
    *,
    accepted_review: ReviewRecord,
    action: EngineeringAction | str | None = None,
    action_context: Mapping[str, Any] | None = None,
    action_reason: str = "",
    created_at_utc: str | None = None,
) -> EngineeringActionProposal:
    """
    Convert one currently Accepted candidate review into a controlled proposal.

    This function does not modify Parts Master, BOM, AVL, AIPN, ECO,
    concession or deviation data.

    Automatic classification is deliberately conservative.  Only explicit
    context can produce an AVL/BOM/concession classification.  Otherwise the
    proposal is "Needs Engineering Classification".
    """
    _validate_accepted_review(accepted_review)

    context = dict(action_context or {})
    proposed_action = (
        _normalise_action(action)
        if action is not None
        else classify_engineering_action(context)
    )

    candidate = accepted_review.candidate
    assert candidate is not None

    reason = str(action_reason or "").strip()
    if not reason:
        reason = _default_reason(proposed_action, context)

    proposal_key = make_proposal_key(
        accepted_review.bom_item_key,
        candidate.identity,
        accepted_review.review_id,
        proposed_action,
    )

    return EngineeringActionProposal(
        proposal_id=str(uuid4()),
        proposal_key=proposal_key,
        bom_item_key=accepted_review.bom_item_key,
        candidate_identity=candidate.identity,
        manufacturer=candidate.manufacturer,
        mpn=candidate.mpn,
        aipn=candidate.aipn,
        match_score=candidate.score,
        review_id=accepted_review.review_id,
        review_decision=accepted_review.decision.value,
        review_reviewer=accepted_review.reviewer,
        review_comment=accepted_review.comment,
        review_warnings=tuple(candidate.warnings),
        review_justification=candidate.justification,
        proposed_action=proposed_action,
        action_reason=reason,
        action_context=context,
        created_at_utc=created_at_utc or _utc_now(),
    )


def classify_engineering_action(
    action_context: Mapping[str, Any] | None,
) -> EngineeringAction:
    """
    Conservative classification from explicit engineering context.

    Recognised booleans:
      reference_only
      temporary_use
      existing_bom_mpn_replacement
      add_to_existing_avl

    Precedence intentionally favours temporary controlled use, then a direct
    BOM replacement, then an AVL addition. Ambiguous/no context is not guessed.
    """
    context = dict(action_context or {})

    if _truthy(context.get("reference_only")):
        return EngineeringAction.NO_ACTION_REFERENCE_ONLY
    if _truthy(context.get("temporary_use")):
        return EngineeringAction.TEMPORARY_CONCESSION_DEVIATION
    if _truthy(context.get("existing_bom_mpn_replacement")):
        return EngineeringAction.PROPOSE_BOM_CHANGE
    if _truthy(context.get("add_to_existing_avl")):
        return EngineeringAction.PROPOSE_AVL_ADDITION

    return EngineeringAction.NEEDS_ENGINEERING_CLASSIFICATION


class EngineeringActionProposalStore:
    """
    Append-only JSONL evidence store for 4.6.2d action proposals.

    A proposal is a handoff artefact only.  Persistence here is not execution
    or authorisation of the proposed engineering change.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, proposal: EngineeringActionProposal) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(proposal.to_dict(), ensure_ascii=False, sort_keys=True)
            )
            handle.write("\n")

    def history(self) -> list[EngineeringActionProposal]:
        if not self.path.exists():
            return []

        proposals: list[EngineeringActionProposal] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    proposals.append(_proposal_from_dict(json.loads(line)))
                except Exception as exc:
                    raise ValueError(
                        f"Invalid engineering action proposal at "
                        f"{self.path}:{line_number}: {exc}"
                    ) from exc
        return proposals


def proposals_from_current_acceptances(
    *,
    review_store: CandidateReviewStore,
    action_by_review_key: Mapping[str, EngineeringAction | str] | None = None,
    context_by_review_key: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[EngineeringActionProposal]:
    """
    Create proposals only for candidates whose *current* review state is Accepted.

    This protects the handoff from stale historical Accept decisions that were
    subsequently changed to Rejected or Needs Verification.
    """
    actions = dict(action_by_review_key or {})
    contexts = dict(context_by_review_key or {})
    proposals: list[EngineeringActionProposal] = []

    current = review_store.latest_by_review_key().values()
    for review in current:
        if review.decision != ReviewDecision.ACCEPTED:
            continue
        if review.candidate is None:
            continue

        proposals.append(
            propose_engineering_action(
                accepted_review=review,
                action=actions.get(review.review_key),
                action_context=contexts.get(review.review_key, {}),
            )
        )

    proposals.sort(
        key=lambda proposal: (
            proposal.bom_item_key.casefold(),
            proposal.candidate_identity.casefold(),
        )
    )
    return proposals


def make_proposal_key(
    bom_item_key: str,
    candidate_identity: str,
    review_id: str,
    action: EngineeringAction,
) -> str:
    text = (
        f"{bom_item_key}::{candidate_identity}::{review_id}::{action.value}"
    ).encode("utf-8")
    return hashlib.sha256(text).hexdigest()[:24]


def _validate_accepted_review(review: ReviewRecord) -> None:
    if review.decision != ReviewDecision.ACCEPTED:
        raise ValueError(
            "Engineering action handoff requires an Accepted review decision."
        )
    if review.candidate is None:
        raise ValueError(
            "Engineering action handoff requires a specific accepted candidate."
        )


def _normalise_action(action: EngineeringAction | str) -> EngineeringAction:
    if isinstance(action, EngineeringAction):
        return action

    text = str(action or "").strip().lower().replace("_", " ")
    aliases = {
        "propose avl addition": EngineeringAction.PROPOSE_AVL_ADDITION,
        "avl addition": EngineeringAction.PROPOSE_AVL_ADDITION,
        "propose bom change": EngineeringAction.PROPOSE_BOM_CHANGE,
        "bom change": EngineeringAction.PROPOSE_BOM_CHANGE,
        "temporary concession/deviation required":
            EngineeringAction.TEMPORARY_CONCESSION_DEVIATION,
        "temporary concession deviation required":
            EngineeringAction.TEMPORARY_CONCESSION_DEVIATION,
        "concession": EngineeringAction.TEMPORARY_CONCESSION_DEVIATION,
        "deviation": EngineeringAction.TEMPORARY_CONCESSION_DEVIATION,
        "no action / reference only": EngineeringAction.NO_ACTION_REFERENCE_ONLY,
        "reference only": EngineeringAction.NO_ACTION_REFERENCE_ONLY,
        "no action": EngineeringAction.NO_ACTION_REFERENCE_ONLY,
        "needs engineering classification":
            EngineeringAction.NEEDS_ENGINEERING_CLASSIFICATION,
    }
    if text not in aliases:
        allowed = ", ".join(item.value for item in EngineeringAction)
        raise ValueError(f"Unknown engineering action {action!r}. Allowed: {allowed}")
    return aliases[text]


def _default_reason(
    action: EngineeringAction,
    context: Mapping[str, Any],
) -> str:
    reasons = {
        EngineeringAction.PROPOSE_AVL_ADDITION:
            "Accepted candidate is proposed for controlled AVL addition review.",
        EngineeringAction.PROPOSE_BOM_CHANGE:
            "Accepted candidate is proposed for controlled BOM change review.",
        EngineeringAction.TEMPORARY_CONCESSION_DEVIATION:
            "Accepted candidate is proposed for temporary controlled use; "
            "concession/deviation governance is required.",
        EngineeringAction.NO_ACTION_REFERENCE_ONLY:
            "Accepted candidate is retained as engineering reference only; "
            "no master-data change is proposed.",
        EngineeringAction.NEEDS_ENGINEERING_CLASSIFICATION:
            "Accepted candidate requires an engineer to classify the appropriate "
            "next governance action.",
    }
    return reasons[action]


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _proposal_from_dict(data: Mapping[str, Any]) -> EngineeringActionProposal:
    return EngineeringActionProposal(
        proposal_id=str(data["proposal_id"]),
        proposal_key=str(data["proposal_key"]),
        bom_item_key=str(data["bom_item_key"]),
        candidate_identity=str(data["candidate_identity"]),
        manufacturer=str(data.get("manufacturer") or ""),
        mpn=str(data.get("mpn") or ""),
        aipn=str(data.get("aipn") or ""),
        match_score=data.get("match_score"),
        review_id=str(data["review_id"]),
        review_decision=str(data["review_decision"]),
        review_reviewer=str(data.get("review_reviewer") or ""),
        review_comment=str(data.get("review_comment") or ""),
        review_warnings=tuple(data.get("review_warnings") or ()),
        review_justification=str(data.get("review_justification") or ""),
        proposed_action=_normalise_action(data["proposed_action"]),
        action_reason=str(data.get("action_reason") or ""),
        action_context=dict(data.get("action_context") or {}),
        created_at_utc=str(data["created_at_utc"]),
        source=str(data.get("source") or "PDC Sprint 4.6.2d"),
        schema_version=str(data.get("schema_version") or "1.0"),
    )
