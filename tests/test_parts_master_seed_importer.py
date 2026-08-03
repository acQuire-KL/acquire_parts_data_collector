import csv
import json
import tempfile
import unittest
from collections import OrderedDict
from pathlib import Path

from parts_master_seed_importer import (
    STATUS_IMPORTED,
    build_seed_import,
    manufacturer_alias_key,
    write_seed_outputs,
)


HEADERS = [
    "AIPN", "Family", "Description", "Manufacturer Name",
    "Manufacturer Part Number", "AIPN - OLD", "Datasheet",
]


class PartsMasterSeedImporterTests(unittest.TestCase):
    def test_imports_complete_identity_as_pending_verification(self):
        rows = [{
            "AIPN": "RES-00010-00", "Family": "RES", "Description": "10k resistor",
            "Manufacturer Name": "Yageo", "Manufacturer Part Number": "RC0603FR-0710KL",
            "AIPN - OLD": "RES-0603-10k-00", "Datasheet": "https://example.test/data.pdf",
        }]
        result = build_seed_import(HEADERS, rows)
        record = result.staging_records[0].clean_record("PMR-000001", "legacy.xlsx", "My Lists Worksheet")
        self.assertEqual(record["Record Status"], STATUS_IMPORTED)
        self.assertEqual(record["Manufacturer"], "Yageo")
        self.assertEqual(record["Manufacturer Part Number"], "RC0603FR-0710KL")

    def test_duplicate_identity_is_one_staging_record_with_all_source_rows(self):
        rows = [
            {"Manufacturer Name": "Yageo", "Manufacturer Part Number": "RC0603FR-0710KL", "Description": "A"},
            {"Manufacturer Name": "Yageo", "Manufacturer Part Number": "RC0603FR-0710KL", "Description": "B"},
        ]
        result = build_seed_import(HEADERS, rows)
        self.assertEqual(len(result.staging_records), 1)
        self.assertEqual(len(result.staging_records[0].source_rows), 2)
        result.validate_lossless()

    def test_missing_identity_is_not_approved_or_silently_dropped(self):
        rows = [{"Manufacturer Name": "Yageo", "Manufacturer Part Number": "", "Description": "Unknown"}]
        result = build_seed_import(HEADERS, rows)
        self.assertEqual(len(result.staging_records), 0)
        self.assertEqual(len(result.incomplete_rows), 1)
        result.validate_lossless()

    def test_diacritic_and_case_variants_are_reported_as_alias_group(self):
        rows = [
            {"Manufacturer Name": "Wurth", "Manufacturer Part Number": "A"},
            {"Manufacturer Name": "Würth", "Manufacturer Part Number": "B"},
        ]
        result = build_seed_import(HEADERS, rows)
        self.assertEqual(manufacturer_alias_key("Wurth"), manufacturer_alias_key("Würth"))
        self.assertEqual(len(result.manufacturer_alias_groups), 1)

    def test_abbreviations_are_not_automatically_equated(self):
        self.assertNotEqual(manufacturer_alias_key("TI"), manufacturer_alias_key("Texas Instruments"))

    def test_outputs_preserve_trace_and_never_approve(self):
        rows = [
            {"Manufacturer Name": "Yageo", "Manufacturer Part Number": "A", "Description": "One"},
            {"Manufacturer Name": "", "Manufacturer Part Number": "B", "Description": "Two"},
        ]
        result = build_seed_import(HEADERS, rows)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "legacy.xlsx"
            source.write_bytes(b"placeholder")
            outputs = write_seed_outputs(result, source, Path(folder) / "out")
            summary = json.loads(outputs["summary_json"].read_text(encoding="utf-8"))
            self.assertEqual(summary["automatic_approvals"], 0)
            self.assertEqual(summary["new_aipns_allocated"], 0)
            self.assertEqual(summary["lossless_traceability_check"], "PASS")
            with outputs["staging_csv"].open(encoding="utf-8-sig", newline="") as handle:
                staged = list(csv.DictReader(handle))
            self.assertEqual(staged[0]["Record Status"], STATUS_IMPORTED)
            self.assertTrue(outputs["issues_csv"].exists())
            self.assertTrue(outputs["trace_json"].exists())


if __name__ == "__main__":
    unittest.main()
