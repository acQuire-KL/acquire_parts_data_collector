from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from knowledge_promotion import promote_review, validate_review_rows, write_knowledge_outputs


class KnowledgePromotionTests(unittest.TestCase):
    def accepted_rows(self):
        base = {
            "Review ID": "REV-ADS", "Record ID": "PMR-000006", "Provider": "DigiKey",
            "Source Manufacturer": "TI", "Source MPN": "ADS1232IPW",
            "Candidate Manufacturer": "Texas Instruments", "Candidate Rank": "1",
            "Description": "ADC", "Product URL": "https://example",
            "Evidence": "Candidate found by fallback", "Review Decision": "Accept",
            "Approved Manufacturer": "Texas Instruments", "Procurement Variant Group": "",
            "Engineer Notes": "Packaging difference only", "Reviewed By": "Ken", "Reviewed Date": "04-Aug",
        }
        first = dict(base, **{"Candidate MPN": "ADS1232IPW", "Approved MPN": "ADS1232IPW"})
        second = dict(base, **{"Candidate Rank": "2", "Candidate MPN": "ADS1232IPWR", "Approved MPN": "ADS1232IPWR"})
        return [first, second]

    def test_acceptance_extracts_alias_and_variants(self):
        result = promote_review(self.accepted_rows())
        self.assertEqual(len(result["manufacturer_aliases"]), 1)
        self.assertEqual(result["manufacturer_aliases"][0]["Manufacturer Alias"], "TI")
        self.assertEqual(len(result["procurement_variants"]), 2)
        self.assertEqual(len({row["Procurement Variant Group"] for row in result["procurement_variants"]}), 1)

    def test_approved_additions_are_one_per_approved_mfg_mpn(self):
        result = promote_review(self.accepted_rows())
        self.assertEqual(len(result["approved_additions"]), 2)
        self.assertTrue(all(row["Approval Status"] == "Approved for Parts Master release review" for row in result["approved_additions"]))

    def test_blank_decision_is_blocking(self):
        row = self.accepted_rows()[0]
        row["Review Decision"] = ""
        issues = validate_review_rows([row])
        self.assertEqual(issues[0]["Severity"], "Error")

    def test_outputs_do_not_modify_source(self):
        rows = self.accepted_rows()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "RUN__CANDIDATE_REVIEW.csv"
            with source.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader(); writer.writerows(rows)
            before = source.read_bytes()
            outputs = write_knowledge_outputs(source)
            self.assertEqual(before, source.read_bytes())
            self.assertTrue(outputs["approved_additions"].exists())
            summary = json.loads(outputs["summary"].read_text(encoding="utf-8"))
            self.assertFalse(summary["parts_master_modified"])
            self.assertEqual(summary["aipns_allocated"], 0)


if __name__ == "__main__":
    unittest.main()
