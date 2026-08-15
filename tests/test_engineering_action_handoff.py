from pathlib import Path
import tempfile
import unittest

from candidate_review import CandidateReviewStore
from engineering_action_handoff import (
    EngineeringAction,
    EngineeringActionProposalStore,
    classify_engineering_action,
    propose_engineering_action,
    proposals_from_current_acceptances,
)


def candidate(mpn="ALT-001", score=94.0, warnings=None):
    return {
        "manufacturer": "Example MFG",
        "mpn": mpn,
        "aipn": "CAP-00100-00",
        "match_score": score,
        "matched_attributes": ["value", "package", "voltage"],
        "differences": [],
        "warnings": warnings or [],
        "justification": "Candidate meets all known hard constraints.",
    }


def accepted_review(store, bom_item="ROW-1", mpn="ALT-001", **kwargs):
    return store.record_candidate_decision(
        bom_item=bom_item,
        candidate=candidate(mpn=mpn, **kwargs),
        decision="Accepted",
        reviewer="KL",
        comment="Engineering candidate reviewed.",
        reviewed_at_utc="2026-08-15T10:00:00Z",
    )


class EngineeringActionHandoffTests(unittest.TestCase):
    def test_only_accepted_review_can_be_handed_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "reviews.jsonl")
            rejected = store.record_candidate_decision(
                bom_item="ROW-1",
                candidate=candidate(),
                decision="Rejected",
            )

            with self.assertRaises(ValueError):
                propose_engineering_action(
                    accepted_review=rejected,
                    action="Propose AVL Addition",
                )

    def test_explicit_avl_handoff_preserves_review_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "reviews.jsonl")
            review = accepted_review(
                store,
                warnings=["Manufacturer datasheet verification recommended"],
            )

            proposal = propose_engineering_action(
                accepted_review=review,
                action="Propose AVL Addition",
                action_reason="Add as approved alternative after governance review.",
                created_at_utc="2026-08-15T11:00:00Z",
            )

            self.assertEqual(
                proposal.proposed_action,
                EngineeringAction.PROPOSE_AVL_ADDITION,
            )
            self.assertEqual(proposal.review_id, review.review_id)
            self.assertEqual(proposal.review_decision, "Accepted")
            self.assertEqual(proposal.mpn, "ALT-001")
            self.assertEqual(
                proposal.review_warnings,
                ("Manufacturer datasheet verification recommended",),
            )

    def test_temporary_use_classifies_to_concession_deviation(self):
        action = classify_engineering_action({"temporary_use": True})
        self.assertEqual(
            action,
            EngineeringAction.TEMPORARY_CONCESSION_DEVIATION,
        )

    def test_bom_replacement_classifies_to_bom_change(self):
        action = classify_engineering_action(
            {"existing_bom_mpn_replacement": True}
        )
        self.assertEqual(action, EngineeringAction.PROPOSE_BOM_CHANGE)

    def test_existing_avl_context_classifies_to_avl_addition(self):
        action = classify_engineering_action({"add_to_existing_avl": True})
        self.assertEqual(action, EngineeringAction.PROPOSE_AVL_ADDITION)

    def test_reference_only_context_proposes_no_change(self):
        action = classify_engineering_action({"reference_only": True})
        self.assertEqual(
            action,
            EngineeringAction.NO_ACTION_REFERENCE_ONLY,
        )

    def test_missing_context_is_not_guessed(self):
        action = classify_engineering_action({})
        self.assertEqual(
            action,
            EngineeringAction.NEEDS_ENGINEERING_CLASSIFICATION,
        )

    def test_current_acceptances_exclude_stale_historical_accept(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "reviews.jsonl")
            accepted_review(store, bom_item="ROW-STALE", mpn="A")
            store.record_candidate_decision(
                bom_item="ROW-STALE",
                candidate=candidate(mpn="A"),
                decision="Rejected",
                reviewed_at_utc="2026-08-15T12:00:00Z",
            )
            accepted_review(store, bom_item="ROW-CURRENT", mpn="B")

            proposals = proposals_from_current_acceptances(
                review_store=store,
            )

            self.assertEqual(len(proposals), 1)
            self.assertEqual(proposals[0].bom_item_key, "ROW-CURRENT")
            self.assertEqual(proposals[0].mpn, "B")

    def test_action_proposal_store_is_append_only_and_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            review_store = CandidateReviewStore(Path(tmp) / "reviews.jsonl")
            review = accepted_review(review_store)
            proposal = propose_engineering_action(
                accepted_review=review,
                action="Propose BOM Change",
                created_at_utc="2026-08-15T11:00:00Z",
            )

            proposal_store = EngineeringActionProposalStore(
                Path(tmp) / "engineering_action_proposals.jsonl"
            )
            proposal_store.append(proposal)
            restored = proposal_store.history()

            self.assertEqual(len(restored), 1)
            self.assertEqual(restored[0].proposal_id, proposal.proposal_id)
            self.assertEqual(
                restored[0].proposed_action,
                EngineeringAction.PROPOSE_BOM_CHANGE,
            )

    def test_handoff_does_not_mutate_review_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "reviews.jsonl")
            review = accepted_review(store)
            before = store.path.read_text(encoding="utf-8")

            propose_engineering_action(
                accepted_review=review,
                action="Reference Only",
            )

            after = store.path.read_text(encoding="utf-8")
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
