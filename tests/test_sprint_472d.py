import unittest
from identity_recovery import family_search_variants, normalise_mpn
from main import _provider_consensus_count, _promote_recovered_consensus, _provider_results_text
from multi_provider_summary import ProviderEvidence

def ev(provider, mfg, mpn, match=True, status="success"):
    return ProviderEvidence(provider, status, part_profile={
        "manufacturer": mfg,
        "manufacturer_part_number": mpn,
        "identity_match": match,
    })

class Sprint472dTests(unittest.TestCase):
    def test_two_provider_exact_consensus(self):
        evidence = [
            ev("DigiKey", "Abracon", "AOTA-N160808S-2R2MT"),
            ev("Mouser", "Abracon", "AOTA-N160808S-2R2MT"),
            ProviderEvidence("TME", "no_match", "Not listed"),
        ]
        self.assertEqual(2, _provider_consensus_count(evidence))
        self.assertEqual("2 matched; 1 not listed", _provider_results_text(evidence))

    def test_hirose_recovered_consensus_promotes_two_providers(self):
        recovered = "BM28B0.6-6DP_2-0.35V_51_"
        corrected = "BM28B0.6-6DP/2-0.35V(51)"
        evidence = [
            ev("DigiKey", "Hirose Electric Co Ltd", corrected, match=False),
            ev("Mouser", "Hirose Electric Co Ltd", corrected, match=False),
            ProviderEvidence("TME", "no_match", "Not listed"),
        ]
        promoted, providers = _promote_recovered_consensus(
            evidence, "Hirose Electric Co Ltd", recovered
        )
        self.assertEqual(2, sum(1 for item in promoted if item.identity_match))
        self.assertIn("DigiKey", providers)
        self.assertIn("Mouser", providers)

    def test_family_reduction_never_exceeds_25_percent(self):
        variants = family_search_variants("BM28B0.6-6DP_2-0.35V_51_")
        self.assertTrue(variants)
        self.assertLessEqual(max(v.reduction_percent for v in variants), 25)

    def test_short_mpn_has_no_family_broadening(self):
        self.assertEqual([], family_search_variants("ABC123"))

if __name__ == "__main__":
    unittest.main()
