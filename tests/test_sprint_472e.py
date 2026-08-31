import unittest

from identity_recovery import (
    RecoveryCandidate,
    consolidate_candidates,
    normalise_mpn,
)
from operational_bom_review import LocalPartContext, provider_review_observation
from manufacturer_resolver import names_equivalent


class Sprint472eTests(unittest.TestCase):
    def test_hirose_short_name_matches_distributor_manufacturer_name(self):
        self.assertTrue(names_equivalent("Hirose", "Hirose Electric Co Ltd"))

    def test_hirose_ds_and_dp_are_distinct_identies(self):
        ds = "BM28B0.6-6DS/2-0.35V(51)"
        dp = "BM28B0.6-6DP/2-0.35V(51)"
        self.assertNotEqual(normalise_mpn(ds), normalise_mpn(dp))

    def test_provider_formatting_is_preferred_over_raw_bom_representation(self):
        items = [
            RecoveryCandidate(
                manufacturer="Hirose Electric Co Ltd",
                mpn="BM28B0.6-6DS_2-0.35V_51_",
                relationship="Recovered MPN candidate",
                sources=("BOM Value",),
            ),
            RecoveryCandidate(
                manufacturer="Hirose Electric Co Ltd",
                mpn="BM28B0.6-6DS/2-0.35V(51)",
                relationship="Formatting-normalised identity candidate",
                sources=("DigiKey",),
            ),
        ]
        result = consolidate_candidates(items)
        self.assertEqual(1, len(result))
        self.assertEqual("BM28B0.6-6DS/2-0.35V(51)", result[0].mpn)
        self.assertIn("DigiKey", result[0].sources)

    def test_two_provider_consensus_suppresses_missing_mpn_and_third_provider_error_review(self):
        observation = provider_review_observation(
            match_status="Matched",
            provider_results="2 matched; 1 error",
            providers_matched="DigiKey, Mouser",
            local_context=LocalPartContext(),
            requested_mpn="",
            recovered_mpn="BM28B0.6-6DS_2-0.35V_51_",
            candidate_count=0,
        )
        self.assertEqual("No immediate review exception identified", observation)

    def test_one_provider_match_still_requires_review(self):
        observation = provider_review_observation(
            match_status="Matched",
            provider_results="1 matched; 1 not listed; 1 error",
            providers_matched="Mouser",
            local_context=LocalPartContext(),
            requested_mpn="",
            recovered_mpn="BM28B0.6-6DS_2-0.35V_51_",
            candidate_count=1,
        )
        self.assertIn("MPN missing", observation)
        self.assertIn("Provider collection incomplete", observation)


if __name__ == "__main__":
    unittest.main()
