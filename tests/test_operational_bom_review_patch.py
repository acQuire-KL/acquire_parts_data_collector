from pathlib import Path
import tempfile
import unittest

from main import (
    _provider_evidence_text,
    load_input_workbook,
    locate_columns,
    build_combined_result,
)
from multi_provider_summary import ProviderEvidence, mpn_identity_equivalent, provider_identity_match
from operational_bom_review import LocalPartContext, provider_review_observation


class OperationalBomReviewCorrectivePatchTests(unittest.TestCase):
    def test_csv_input_loads_into_workbook(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bom.csv"
            path.write_text(
                "Reference,MF,MPN,Value,Footprint,Qty,DNP\n"
                "C1,Example MFG,ABC123,10uF,0603,1,No\n",
                encoding="utf-8",
            )
            workbook = load_input_workbook(path)
            sheet = workbook.active
            self.assertEqual("MF", sheet.cell(1, 2).value)
            self.assertEqual("ABC123", sheet.cell(2, 3).value)

    def test_mf_header_is_recognised_as_manufacturer(self):
        mfg_col, mpn_col = locate_columns(["Reference", "MF", "MPN", "Value"])
        self.assertEqual(2, mfg_col)
        self.assertEqual(3, mpn_col)

    def test_digikey_404_is_concise_not_raw_payload(self):
        evidence = [
            ProviderEvidence(
                "DigiKey",
                "error",
                'DigiKey 404: {"type":"https://tools.ietf.org/html/rfc7231#section-6.5.4","detail":"Requested Product not found"}',
            ),
            ProviderEvidence("Mouser", "success"),
            ProviderEvidence("TME", "no_match"),
        ]
        text = _provider_evidence_text(evidence)
        self.assertIn("DigiKey: not found", text)
        self.assertIn("Mouser: success", text)
        self.assertIn("TME: not found", text)
        self.assertNotIn("tools.ietf.org", text)
        self.assertNotIn("Requested Product", text)

    def test_provider_error_is_concise(self):
        text = _provider_evidence_text([
            ProviderEvidence("DigiKey", "error", "unexpected internal transport failure stack trace")
        ])
        self.assertEqual("DigiKey: provider error", text)

    def test_rate_limit_is_concise(self):
        text = _provider_evidence_text([
            ProviderEvidence("Mouser", "error", "HTTP 429 Too Many Requests")
        ])
        self.assertEqual("Mouser: rate limited", text)

    def test_ordering_suffix_r_is_identity_equivalent(self):
        self.assertTrue(mpn_identity_equivalent("TPS628438YKA", "TPS628438YKAR"))

    def test_ordering_suffix_t_is_identity_equivalent(self):
        self.assertTrue(mpn_identity_equivalent("MAX40203ANS", "MAX40203ANS+T"))

    def test_arbitrary_prefix_is_not_identity_equivalent(self):
        self.assertFalse(mpn_identity_equivalent("ABC123", "ABC123XYZ"))

    def test_provider_identity_accepts_ordering_suffix_with_same_manufacturer(self):
        profile = {
            "manufacturer": "Texas Instruments",
            "manufacturer_part_number": "TPS628438YKAR",
        }
        self.assertTrue(
            provider_identity_match("Texas Instruments", "TPS628438YKA", profile)
        )

    def test_bom_value_and_footprint_are_preserved(self):
        result = build_combined_result(
            2,
            "Example MFG",
            "ABC123",
            [],
            bom_context={
                "description": "CAP CER",
                "value": "10uF 10V",
                "footprint": "0603",
                "quantity": 2,
                "dnp": "No",
            },
            local_context=LocalPartContext(),
        )
        self.assertEqual("10uF 10V", result["BOM Value"])
        self.assertEqual("0603", result["BOM Footprint"])

    def test_missing_mpn_has_explicit_review_observation(self):
        text = provider_review_observation(
            match_status="Review Required",
            providers_queried="DigiKey: skipped - MPN missing",
            providers_matched="",
            local_context=LocalPartContext(),
            requested_mpn="",
        )
        self.assertIn("MPN missing - provider lookup skipped", text)


if __name__ == "__main__":
    unittest.main()
