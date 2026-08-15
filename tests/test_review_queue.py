from pathlib import Path
import tempfile
import unittest

from candidate_review import CandidateReviewStore
from review_queue import build_review_queue, build_review_summary, review_queue_rows


def candidate(mpn, score=90.0, warnings=None):
    return {
        "manufacturer": "Example MFG",
        "mpn": mpn,
        "aipn": "",
        "match_score": score,
        "matched_attributes": ["value", "footprint"],
        "differences": [],
        "warnings": warnings or [],
        "justification": "Local engineering candidate.",
    }


class ReviewQueueTests(unittest.TestCase):
    def test_latest_decision_is_used_without_losing_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "reviews.jsonl")
            store.record_candidate_decision(
                bom_item="ROW-1",
                candidate=candidate("A"),
                decision="Needs Verification",
                reviewed_at_utc="2026-08-15T09:00:00Z",
            )
            store.record_candidate_decision(
                bom_item="ROW-1",
                candidate=candidate("A"),
                decision="Accepted",
                reviewed_at_utc="2026-08-15T10:00:00Z",
            )

            self.assertEqual(len(store.history()), 2)

            queue = build_review_queue(store)
            self.assertEqual(len(queue), 1)
            self.assertEqual(len(queue[0].candidates), 1)
            self.assertEqual(queue[0].candidates[0].decision, "Accepted")
            self.assertEqual(queue[0].item_status, "Accepted")

    def test_pending_and_needs_verification_require_attention(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "reviews.jsonl")
            store.record_candidate_decision(
                bom_item="ROW-PENDING",
                candidate=candidate("P"),
                decision="Pending",
            )
            store.record_candidate_decision(
                bom_item="ROW-VERIFY",
                candidate=candidate("V"),
                decision="Needs Verification",
            )

            queue = {item.bom_item_key: item for item in build_review_queue(store)}
            self.assertTrue(queue["ROW-PENDING"].needs_attention)
            self.assertEqual(queue["ROW-PENDING"].item_status, "Pending")
            self.assertTrue(queue["ROW-VERIFY"].needs_attention)
            self.assertEqual(
                queue["ROW-VERIFY"].item_status,
                "Needs Verification",
            )

    def test_multiple_acceptances_are_flagged_not_silently_selected(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "reviews.jsonl")
            store.record_candidate_decision(
                bom_item="ROW-1",
                candidate=candidate("A", 95.0),
                decision="Accepted",
            )
            store.record_candidate_decision(
                bom_item="ROW-1",
                candidate=candidate("B", 93.0),
                decision="Accepted",
            )

            item = build_review_queue(store)[0]
            self.assertTrue(item.multiple_acceptances)
            self.assertTrue(item.needs_attention)
            self.assertEqual(item.item_status, "Conflict - Multiple Accepted")
            self.assertEqual(
                [row.mpn for row in item.candidates],
                ["A", "B"],
            )

    def test_no_suitable_candidate_is_visible_as_item_level_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "reviews.jsonl")
            store.record_no_suitable_candidate(
                bom_item="ROW-NONE",
                comment="No candidate met hard constraints.",
            )

            item = build_review_queue(store)[0]
            self.assertTrue(item.no_suitable_candidate)
            self.assertFalse(item.multiple_acceptances)
            self.assertFalse(item.needs_attention)
            self.assertEqual(item.item_status, "No Suitable Candidate")
            self.assertEqual(item.candidates, ())

            rows = review_queue_rows(store)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["decision"], "No Suitable Candidate")

    def test_all_rejected_is_distinguished_from_no_suitable_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "reviews.jsonl")
            store.record_candidate_decision(
                bom_item="ROW-REJECT",
                candidate=candidate("A"),
                decision="Rejected",
            )
            store.record_candidate_decision(
                bom_item="ROW-REJECT",
                candidate=candidate("B"),
                decision="Rejected",
            )

            item = build_review_queue(store)[0]
            self.assertEqual(item.item_status, "All Candidates Rejected")
            self.assertFalse(item.no_suitable_candidate)
            self.assertFalse(item.needs_attention)

    def test_summary_counts_current_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "reviews.jsonl")

            store.record_candidate_decision(
                bom_item="ROW-ACCEPT",
                candidate=candidate("A"),
                decision="Accepted",
            )
            store.record_candidate_decision(
                bom_item="ROW-PENDING",
                candidate=candidate("B"),
                decision="Pending",
            )
            store.record_candidate_decision(
                bom_item="ROW-CONFLICT",
                candidate=candidate("C"),
                decision="Accepted",
            )
            store.record_candidate_decision(
                bom_item="ROW-CONFLICT",
                candidate=candidate("D"),
                decision="Accepted",
            )
            store.record_no_suitable_candidate(bom_item="ROW-NONE")

            summary = build_review_summary(store)

            self.assertEqual(summary["total_bom_items"], 4)
            self.assertEqual(summary["total_candidates"], 4)
            self.assertEqual(summary["bom_items_needing_attention"], 2)
            self.assertEqual(summary["multiple_acceptance_conflicts"], 1)
            self.assertEqual(summary["no_suitable_candidate_items"], 1)
            self.assertEqual(
                summary["candidate_decision_counts"]["Accepted"],
                3,
            )
            self.assertEqual(
                summary["candidate_decision_counts"]["Pending"],
                1,
            )

    def test_queue_prioritises_conflicts_then_attention(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "reviews.jsonl")
            store.record_candidate_decision(
                bom_item="Z-RESOLVED",
                candidate=candidate("A"),
                decision="Accepted",
            )
            store.record_candidate_decision(
                bom_item="Y-PENDING",
                candidate=candidate("B"),
                decision="Pending",
            )
            store.record_candidate_decision(
                bom_item="X-CONFLICT",
                candidate=candidate("C"),
                decision="Accepted",
            )
            store.record_candidate_decision(
                bom_item="X-CONFLICT",
                candidate=candidate("D"),
                decision="Accepted",
            )

            keys = [item.bom_item_key for item in build_review_queue(store)]
            self.assertEqual(
                keys,
                ["X-CONFLICT", "Y-PENDING", "Z-RESOLVED"],
            )

    def test_flat_rows_preserve_review_explanation_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "reviews.jsonl")
            store.record_candidate_decision(
                bom_item="ROW-1",
                candidate=candidate(
                    "A",
                    score=97.5,
                    warnings=["datasheet verification required"],
                ),
                decision="Needs Verification",
                comment="Check manufacturer evidence.",
            )

            row = review_queue_rows(store)[0]
            self.assertEqual(row["mpn"], "A")
            self.assertEqual(row["score"], 97.5)
            self.assertEqual(row["warnings"], ["datasheet verification required"])
            self.assertEqual(row["comment"], "Check manufacturer evidence.")


if __name__ == "__main__":
    unittest.main()
