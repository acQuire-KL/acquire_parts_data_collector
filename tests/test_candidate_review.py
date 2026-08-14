from pathlib import Path
import tempfile
import unittest

from candidate_review import (
    CandidateReviewStore,
    ReviewDecision,
    review_candidates,
)


def sample_candidate():
    return {
        "manufacturer": "Samsung Electro-Mechanics",
        "mpn": "CL10A106MP8NNNC",
        "aipn": "CAP-00010-00",
        "match_score": 96.5,
        "matched_attributes": ["capacitance=10uF", "package=0603"],
        "differences": ["tolerance: BOM unspecified, candidate ±20%"],
        "warnings": ["voltage source needs verification"],
        "justification": "10uF 0603 capacitor meeting known BOM constraints.",
    }


class CandidateReviewTests(unittest.TestCase):
    def test_review_projection_does_not_modify_candidate(self):
        candidate = sample_candidate()
        original = dict(candidate)

        rows = review_candidates(
            bom_item={"VTPN": "70001234"},
            candidates=[candidate],
        )

        self.assertEqual(candidate, original)
        self.assertEqual(rows[0]["review_decision"], "Pending")
        self.assertEqual(rows[0]["mpn"], "CL10A106MP8NNNC")
        self.assertEqual(rows[0]["score"], 96.5)

    def test_accept_candidate_is_persisted(self):
        candidate = sample_candidate()

        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "candidate_reviews.jsonl")

            record = store.record_candidate_decision(
                bom_item={"VTPN": "70001234"},
                candidate=candidate,
                decision=ReviewDecision.ACCEPTED,
                reviewer="KL",
                comment="Checked against drawing and datasheet.",
                reviewed_at_utc="2026-08-14T12:00:00Z",
            )

            self.assertEqual(record.decision, ReviewDecision.ACCEPTED)

            accepted = store.accepted_candidates({"VTPN": "70001234"})
            self.assertEqual(len(accepted), 1)
            self.assertEqual(accepted[0].candidate.mpn, "CL10A106MP8NNNC")

    def test_new_decision_preserves_history_but_changes_current_state(self):
        candidate = sample_candidate()

        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "candidate_reviews.jsonl")

            first = store.record_candidate_decision(
                bom_item="BOM-ROW-17",
                candidate=candidate,
                decision="Needs Verification",
                reviewed_at_utc="2026-08-14T12:00:00Z",
            )
            second = store.record_candidate_decision(
                bom_item="BOM-ROW-17",
                candidate=candidate,
                decision="Rejected",
                comment="Voltage rating inadequate after verification.",
                reviewed_at_utc="2026-08-14T13:00:00Z",
            )

            history = store.history()
            current = store.latest_for_bom_item("BOM-ROW-17")

            self.assertEqual(len(history), 2)
            self.assertEqual(first.review_key, second.review_key)
            self.assertEqual(len(current), 1)
            self.assertEqual(current[0].decision, ReviewDecision.REJECTED)
            self.assertEqual(store.accepted_candidates("BOM-ROW-17"), [])

    def test_no_suitable_candidate_is_a_bom_level_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "candidate_reviews.jsonl")

            record = store.record_no_suitable_candidate(
                bom_item={"AIPN": "CAP-00420-00"},
                reviewer="KL",
                comment="No candidate met package and voltage constraints.",
            )

            self.assertEqual(
                record.decision,
                ReviewDecision.NO_SUITABLE_CANDIDATE,
            )
            self.assertIsNone(record.candidate)

    def test_no_suitable_candidate_cannot_be_attached_to_specific_candidate(self):
        candidate = sample_candidate()

        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "candidate_reviews.jsonl")

            with self.assertRaises(ValueError):
                store.record_candidate_decision(
                    bom_item="ROW-1",
                    candidate=candidate,
                    decision="No Suitable Candidate",
                )

    def test_unknown_decision_is_rejected(self):
        candidate = sample_candidate()

        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "candidate_reviews.jsonl")

            with self.assertRaises(ValueError):
                store.record_candidate_decision(
                    bom_item="ROW-1",
                    candidate=candidate,
                    decision="Auto Approved",
                )

    def test_original_candidate_snapshot_is_retained(self):
        candidate = sample_candidate()

        with tempfile.TemporaryDirectory() as tmp:
            store = CandidateReviewStore(Path(tmp) / "candidate_reviews.jsonl")

            store.record_candidate_decision(
                bom_item="ROW-1",
                candidate=candidate,
                decision="Accepted",
            )

            restored = store.history()[0]
            self.assertEqual(restored.candidate.raw_candidate["match_score"], 96.5)
            self.assertEqual(
                restored.candidate.raw_candidate["warnings"],
                ["voltage source needs verification"],
            )


if __name__ == "__main__":
    unittest.main()
