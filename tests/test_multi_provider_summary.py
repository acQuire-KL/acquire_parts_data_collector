import unittest

from multi_provider_summary import (
    ProviderEvidence,
    engineering_confirmation,
    evidence_status,
    provider_identity_match,
)


class MultiProviderSummaryTests(unittest.TestCase):
    def test_any_exact_provider_identity_match_confirms_component(self):
        evidence = [
            ProviderEvidence("DigiKey", "success", part_profile={"identity_match": False}),
            ProviderEvidence("Mouser", "success", part_profile={"identity_match": True}),
        ]
        status, reason = evidence_status(evidence)
        self.assertEqual("Matched", status)
        self.assertIn("Mouser", reason)

    def test_provider_failure_does_not_override_other_provider_match(self):
        evidence = [
            ProviderEvidence("DigiKey", "error", "API unavailable"),
            ProviderEvidence("Mouser", "success", part_profile={"identity_match": True}),
        ]
        status, _ = evidence_status(evidence)
        self.assertEqual("Matched", status)

    def test_identity_requires_manufacturer_and_mpn(self):
        profile = {"manufacturer": "Microchip Technology", "manufacturer_part_number": "MCP1711T-25I/OT"}
        self.assertTrue(provider_identity_match("Microchip", "MCP1711T-25I/OT", profile))
        self.assertFalse(provider_identity_match("Microchip", "MCP1711T-33I/OT", profile))

    def test_engineering_confirmation_reports_agreement_without_preference(self):
        evidence = [
            ProviderEvidence("DigiKey", "success", part_profile={
                "identity_match": True, "package": "SOT-23-5", "mounting_type": "SMD"
            }),
            ProviderEvidence("Mouser", "success", part_profile={
                "identity_match": True, "package": "SOT-23-5", "mounting_type": "SMD"
            }),
        ]
        self.assertEqual("Confirmed across providers (2 common fields)", engineering_confirmation(evidence))


if __name__ == "__main__":
    unittest.main()
