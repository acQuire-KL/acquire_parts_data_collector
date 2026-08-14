from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from parts_master_index import build_parts_master_index, write_parts_master_index
from parts_master_seed_importer import read_xlsx_rows


class PartsMasterIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path("input/AIPN Parts Master.xlsx")
        cls.index = build_parts_master_index(cls.source)

    def test_one_record_per_unique_mfg_mpn(self):
        _, rows = read_xlsx_rows(self.source)
        identities = {
            (str(row.get("Manufacturer Name", "")).strip().casefold(), str(row.get("Manufacturer Part Number", "")).strip().casefold())
            for row in rows
            if str(row.get("Manufacturer Name", "")).strip() and str(row.get("Manufacturer Part Number", "")).strip()
        }
        self.assertEqual(len(self.index["parts"]), len(identities))

    def test_current_baseline_counts(self):
        summary = self.index["index_summary"]
        self.assertEqual(summary["part_records"], 260)
        self.assertEqual(summary["duplicate_identity_groups"], 3)
        self.assertEqual(summary["automatic_approvals"], 0)
        self.assertEqual(summary["new_aipns_allocated"], 0)

    def test_missing_aipn_does_not_block_record(self):
        record = next(part for part in self.index["parts"] if part["MPN"] == "ADS1232IPW")
        self.assertIsNone(record["AIPN"])
        self.assertEqual(record["Identity_Basis"], "MFG+MPN")
        self.assertEqual(record["Manufacturer"], "TI")

    def test_known_fields_are_structured(self):
        record = next(part for part in self.index["parts"] if part["MPN"] == "MCP3202T-CI/SN")
        self.assertEqual(record["Family"], "ADC")
        self.assertEqual(record["Value_Nominal"], "12")
        self.assertEqual(record["Footprint"], "SOIC-8")
        self.assertEqual(record["Product_Status"], "Active")

    def test_description_is_preserved_not_parsed(self):
        record = next(part for part in self.index["parts"] if part["MPN"] == "ADS1232IPW")
        self.assertIn("24 Bit Analog to Digital Converter", record["Description"])
        self.assertNotIn("Technology", record)

    def test_source_traceability_is_preserved(self):
        for record in self.index["parts"]:
            self.assertTrue(record["Source_Rows"])
            self.assertTrue(record["Source_File"])
            self.assertTrue(record["Source_Sheet"])

    def test_write_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_parts_master_index(self.index, Path(tmp) / "index.json")
            loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(loaded["index_summary"]["part_records"], 260)
        self.assertEqual(len(loaded["parts"]), 260)


if __name__ == "__main__":
    unittest.main()
