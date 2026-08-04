from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from candidate_review import build_review_rows, load_candidates, write_review_file


class CandidateReviewTests(unittest.TestCase):
    def sample(self):
        return [
            {
                "Record ID": "PMR-000009", "Provider": "DigiKey",
                "Source Manufacturer": "Texas Instruments", "Source MPN": "ADS1234IPW",
                "Candidate Rank": "2", "Returned Manufacturer": "Texas Instruments",
                "Returned MPN": "ADS1234IPWR", "Provider Part Number": "296-123-ND",
                "Description": "ADC", "Product URL": "https://example/2",
                "Source Stage": "MPN-only fallback", "MPN Exact": "False",
                "Manufacturer Equivalent": "True", "Manufacturer Score": "1.0",
            },
            {
                "Record ID": "PMR-000009", "Provider": "DigiKey",
                "Source Manufacturer": "Texas Instruments", "Source MPN": "ADS1234IPW",
                "Candidate Rank": "1", "Returned Manufacturer": "Texas Instruments",
                "Returned MPN": "ADS1234IPW", "Provider Part Number": "296-122-ND",
                "Description": "ADC", "Product URL": "https://example/1",
                "Source Stage": "MPN-only fallback", "MPN Exact": "True",
                "Manufacturer Equivalent": "True", "Manufacturer Score": "1.0",
            },
        ]

    def test_rows_are_grouped_and_rank_sorted(self):
        rows = build_review_rows(self.sample())
        self.assertEqual([row["Candidate Rank"] for row in rows], ["1", "2"])
        self.assertEqual(rows[0]["Candidate Count"], 2)
        self.assertEqual(rows[0]["Review ID"], rows[1]["Review ID"])

    def test_decision_fields_are_blank(self):
        row = build_review_rows(self.sample())[0]
        self.assertEqual(row["Review Decision"], "")
        self.assertEqual(row["Approved Manufacturer"], "")
        self.assertEqual(row["Approved MPN"], "")

    def test_evidence_is_explanatory(self):
        row = build_review_rows(self.sample())[0]
        self.assertIn("Returned MPN matches", row["Evidence"])
        self.assertIn("manufacturer matches", row["Evidence"])

    def test_write_review_does_not_change_source(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "RUN__CANDIDATES.csv"
            fields = list(self.sample()[0].keys())
            with source.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader(); writer.writerows(self.sample())
            before = source.read_bytes()
            target = write_review_file(source)
            self.assertTrue(target.exists())
            self.assertEqual(before, source.read_bytes())
            self.assertEqual(len(load_candidates(source)), 2)


if __name__ == "__main__":
    unittest.main()
