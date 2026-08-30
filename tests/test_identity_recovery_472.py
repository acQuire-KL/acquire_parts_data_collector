import unittest

from identity_recovery import (
    RecoveryCandidate,
    classify_mpn_relationship,
    consolidate_candidates,
    discover_payload_candidates,
    footprint_consistency,
    looks_like_mpn,
    recover_mpn_from_bom,
)
from operational_bom_review import LocalPartContext, provider_review_observation


class IdentityRecovery472Tests(unittest.TestCase):
    def test_passive_value_is_not_treated_as_mpn(self):
        self.assertFalse(looks_like_mpn("10uF"))
        self.assertFalse(looks_like_mpn("10k"))
        self.assertFalse(looks_like_mpn("3.3V"))

    def test_hirose_style_value_can_be_recovered_as_candidate(self):
        candidate = recover_mpn_from_bom(
            "Hirose", "", {"value": "DF13A-2P-1.25H(20)", "description": "Connector"}
        )
        self.assertIsNotNone(candidate)
        self.assertEqual("DF13A-2P-1.25H(20)", candidate.mpn)
        self.assertEqual("Recovered MPN candidate", candidate.relationship)
        self.assertIn("BOM Value", candidate.sources)

    def test_recovery_does_not_override_existing_mpn(self):
        self.assertIsNone(recover_mpn_from_bom(
            "Hirose", "DF13A-2P-1.25H(20)", {"value": "OTHER123"}
        ))

    def test_t_suffix_is_variant_candidate_not_identity(self):
        self.assertEqual(
            "Orderable suffix variant candidate",
            classify_mpn_relationship("MAX40024ANL+", "MAX40024ANL+T"),
        )

    def test_r_suffix_is_variant_candidate_not_identity(self):
        self.assertEqual(
            "Orderable suffix variant candidate",
            classify_mpn_relationship("TPS628438YKA", "TPS628438YKAR"),
        )

    def test_near_mpn_one_character_is_candidate(self):
        self.assertEqual(
            "Near MPN candidate",
            classify_mpn_relationship("ABC12345", "ABC1234X"),
        )

    def test_footprint_can_confirm_when_mpn_embedded(self):
        result = footprint_consistency(
            "Connector_Hirose:Hirose_DF13A-2P-1.25H_1x02_P1.25mm_Horizontal",
            "",
            "DF13A-2P-1.25H",
        )
        self.assertTrue(result.startswith("Consistent"))

    def test_absence_of_package_token_is_not_called_conflict(self):
        self.assertEqual(
            "Not assessed",
            footprint_consistency("Package_DFN_QFN:WSON-6", "6-WDFN Exposed Pad", "ABC123"),
        )

    def test_candidates_are_consolidated_across_providers(self):
        candidates = consolidate_candidates([
            RecoveryCandidate("Analog Devices", "MAX40024ANL+T", "Orderable suffix variant candidate", ("Mouser",)),
            RecoveryCandidate("Analog Devices", "MAX40024ANL+T", "Orderable suffix variant candidate", ("DigiKey",)),
        ])
        self.assertEqual(1, len(candidates))
        self.assertEqual(("Mouser", "DigiKey"), candidates[0].sources)

    def test_mouser_payload_discovers_multiple_variants(self):
        payload = {
            "SearchResults": {
                "Parts": [
                    {
                        "Manufacturer": "Analog Devices",
                        "ManufacturerPartNumber": "MAX40024ANL+T",
                        "DataSheetUrl": "https://example.test/max40024.pdf",
                        "AlternatePackagings": [{"APMfrPN": "MAX40024ANL+"}],
                    }
                ]
            }
        }
        candidates = discover_payload_candidates(
            "Mouser", payload,
            requested_manufacturer="Analog Devices",
            reference_mpn="MAX40024ANL+",
            bom_footprint="",
        )
        self.assertEqual(1, len(candidates))
        self.assertEqual("MAX40024ANL+T", candidates[0].mpn)
        self.assertEqual("Orderable suffix variant candidate", candidates[0].relationship)

    def test_tme_payload_discovers_manufacturer_symbols(self):
        payload = {
            "status": "OK",
            "data": {"products": {"elements": [{
                "manufacturer": {"name": "Texas Instruments"},
                "symbol": "TPS628438YKAR",
                "manufacturer_symbols": ["TPS628438YKAR"],
            }]}}
        }
        candidates = discover_payload_candidates(
            "TME", payload,
            requested_manufacturer="Texas Instruments",
            reference_mpn="TPS628438YKA",
        )
        self.assertEqual(1, len(candidates))
        self.assertEqual("TPS628438YKAR", candidates[0].mpn)

    def test_review_observation_reports_recovered_candidate(self):
        text = provider_review_observation(
            match_status="Review Required", provider_results="2 unconfirmed; 1 not listed",
            providers_matched="", local_context=LocalPartContext(), requested_mpn="",
            recovered_mpn="DF13A-2P-1.25H(20)", candidate_count=1,
        )
        self.assertIn("candidate recovered", text)
        self.assertIn("1 identity/variant candidate(s) discovered", text)


if __name__ == "__main__":
    unittest.main()
