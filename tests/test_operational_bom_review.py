import json
from pathlib import Path
import tempfile
import unittest

from main import build_combined_result
from multi_provider_summary import ProviderEvidence
from operational_bom_review import (
    LocalPartContext,
    PartsMasterLookup,
    provider_review_observation,
    summary_rows,
)


class OperationalBomReviewTests(unittest.TestCase):
    def test_parts_master_lookup_returns_exact_identity_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "parts_master_index.json"
            path.write_text(json.dumps({"parts": [{
                "Manufacturer": "Texas Instruments",
                "MPN": "TXU0304DTRR",
                "AIPN": "IC-00100-00",
                "Description": "Translator",
                "Product_Status": "Active",
                "datasheet_status": "Manufacturer Verified",
                "datasheet_active_url": "https://ti.example/txu0304.pdf",
                "datasheet_local_file": "TI/TXU0304/static.pdf",
            }]}), encoding="utf-8")
            context = PartsMasterLookup(path).find("Texas Instruments", "TXU0304DTRR")
            self.assertEqual("Parts Master Match", context.status)
            self.assertEqual("IC-00100-00", context.aipn)
            self.assertEqual("Manufacturer Verified", context.datasheet_status)

    def test_parts_master_lookup_requires_mpn(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "parts_master_index.json"
            path.write_text('{"parts": []}', encoding="utf-8")
            context = PartsMasterLookup(path).find("Example", "")
            self.assertEqual("No MPN for Parts Master lookup", context.status)

    def test_two_provider_consensus_does_not_require_review_for_third_provider_gap(self):
        text = provider_review_observation(
            match_status="Matched",
            providers_queried="DigiKey=success; Mouser=success; TME=skipped",
            providers_matched="DigiKey, Mouser",
            local_context=LocalPartContext(),
        )
        self.assertEqual("No immediate review exception identified", text)

    def test_review_observation_flags_lifecycle_risk(self):
        text = provider_review_observation(
            match_status="Matched",
            providers_queried="DigiKey=success; Mouser=success; TME=success",
            providers_matched="DigiKey, Mouser, TME",
            local_context=LocalPartContext(),
            lifecycle="NRND",
        )
        self.assertIn("Lifecycle risk indicated", text)

    def test_summary_rows_counts_attention(self):
        rows = dict(summary_rows([
            {"Match Status": "Matched", "Local Knowledge Status": "Parts Master Match", "Review Observation": "No immediate review exception identified"},
            {"Match Status": "Review Required", "Local Knowledge Status": "Not in Parts Master", "Review Observation": "Identity requires review"},
        ]))
        self.assertEqual(2, rows["BOM Rows Reviewed"])
        self.assertEqual(1, rows["Rows Requiring Attention"])
        self.assertEqual(1, rows["Match Status - Matched"])
        self.assertEqual(1, rows["Match Status - Review Required"])

    def test_combined_result_exposes_all_three_provider_positions(self):
        evidence = []
        for provider in ("DigiKey", "Mouser", "TME"):
            profile = {
                "identity_match": True,
                "manufacturer": "Example MFG",
                "manufacturer_part_number": "ABC123",
                "description": "Example",
                "package": "0603",
                "mounting_type": "SMD",
            }
            commercial = {
                "provider": provider,
                "provider_currency": "EUR",
                "product_quantity_available": 100,
                "offers": [],
            }
            evidence.append(ProviderEvidence(
                provider,
                "success",
                part_profile=profile,
                commercial_profile=commercial,
            ))
        result = build_combined_result(
            2, "Example MFG", "ABC123", evidence,
            bom_context={"description": "10uF", "quantity": 4, "dnp": "No"},
            local_context=LocalPartContext(status="Parts Master Match", aipn="CAP-00010-00"),
        )
        self.assertEqual("DigiKey", result["Provider #1 Name"])
        self.assertEqual("Mouser", result["Provider #2 Name"])
        self.assertEqual("TME", result["Provider #3 Name"])
        self.assertEqual(100, result["Provider #3 Available"])

    def test_combined_result_preserves_bom_context_including_dnp(self):
        result = build_combined_result(
            7, "Example", "ABC123", [],
            bom_context={"description": "CAP CER 10UF", "quantity": 3, "dnp": "DNP"},
            local_context=LocalPartContext(),
        )
        self.assertEqual("CAP CER 10UF", result["BOM Description"])
        self.assertEqual(3, result["BOM Quantity"])
        self.assertEqual("DNP", result["BOM DNP"])

    def test_combined_result_surfaces_local_datasheet_evidence(self):
        local = LocalPartContext(
            status="Parts Master Match",
            aipn="IC-12345-00",
            datasheet_status="Manufacturer Verified",
            datasheet_active_url="https://mfg.test/abc.pdf",
            datasheet_local_file="MFG/ABC123/static.pdf",
        )
        result = build_combined_result(
            2, "Example", "ABC123", [], local_context=local
        )
        self.assertEqual("Manufacturer Verified", result["Datasheet Evidence Status"])
        self.assertEqual("MFG/ABC123/static.pdf", result["Static Datasheet"])
        self.assertEqual("https://mfg.test/abc.pdf", result["Datasheet URL"])


if __name__ == "__main__":
    unittest.main()
