import csv
import json
import tempfile
import unittest
from pathlib import Path

from bom_intake_classifier import (
    CLASS_INSUFFICIENT,
    CLASS_MFG_MPN,
    CLASS_VALUE_FOOTPRINT,
    classify_result,
    classify_source_bom,
    write_classification_outputs,
)
from bom_normalizer import normalise_rows


HEADERS = ["Reference", "MF", "MPN", "Value", "Datasheet", "Footprint", "Qty", "DNP"]


class BOMIntakeClassifierTests(unittest.TestCase):
    def _classify_one(self, row):
        result = normalise_rows([row], HEADERS)
        return classify_result(result)[0]

    def test_mfg_mpn_is_identity_path(self):
        item = self._classify_one({
            "Reference": "U1", "MF": "Texas Instruments", "MPN": "ADS1232IPW",
            "Value": "", "Datasheet": "", "Footprint": "TSSOP-24", "Qty": "1", "DNP": "",
        })
        self.assertEqual(item.classification, CLASS_MFG_MPN)
        self.assertEqual(item.next_action, "Parts Master MFG + MPN lookup")

    def test_blank_mpn_with_value_and_footprint_is_descriptive_path(self):
        item = self._classify_one({
            "Reference": "R1", "MF": "", "MPN": "", "Value": "10k",
            "Datasheet": "", "Footprint": "0402", "Qty": "1", "DNP": "",
        })
        self.assertEqual(item.classification, CLASS_VALUE_FOOTPRINT)
        self.assertEqual(item.next_action, "Parts Master Value + Footprint lookup")

    def test_mpn_without_manufacturer_is_not_guessed_as_descriptive(self):
        item = self._classify_one({
            "Reference": "U1", "MF": "", "MPN": "ABC123", "Value": "ABC123",
            "Datasheet": "", "Footprint": "QFN", "Qty": "1", "DNP": "",
        })
        self.assertEqual(item.classification, CLASS_INSUFFICIENT)
        self.assertIn("Manufacturer", item.classification_reason)

    def test_missing_footprint_is_insufficient(self):
        item = self._classify_one({
            "Reference": "C1", "MF": "", "MPN": "", "Value": "100nF",
            "Datasheet": "", "Footprint": "", "Qty": "1", "DNP": "",
        })
        self.assertEqual(item.classification, CLASS_INSUFFICIENT)
        self.assertIn("Footprint", item.classification_reason)

    def test_source_is_normalised_fresh_and_all_unique_items_are_classified(self):
        rows = [
            {"Reference": "R1", "MF": "", "MPN": "", "Value": "10k", "Datasheet": "", "Footprint": "0402", "Qty": "1", "DNP": ""},
            {"Reference": "R2", "MF": "", "MPN": "", "Value": "10k", "Datasheet": "", "Footprint": "0402", "Qty": "1", "DNP": ""},
            {"Reference": "U1", "MF": "TI", "MPN": "ABC123", "Value": "", "Datasheet": "", "Footprint": "QFN", "Qty": "1", "DNP": ""},
        ]
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "bom.csv"
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=HEADERS)
                writer.writeheader()
                writer.writerows(rows)
            result, records = classify_source_bom(source)
            self.assertEqual(result.source_row_count, 3)
            self.assertEqual(result.normalised_row_count, 2)
            self.assertEqual(len(records), 2)
            self.assertEqual({r.classification for r in records}, {CLASS_MFG_MPN, CLASS_VALUE_FOOTPRINT})

    def test_classification_output_follows_natural_reference_order(self):
        rows = [
            {"Reference": "R10", "MF": "Yageo", "MPN": "R10PART", "Value": "10k", "Datasheet": "", "Footprint": "0603", "Qty": "1", "DNP": ""},
            {"Reference": "C2", "MF": "", "MPN": "", "Value": "100nF", "Datasheet": "", "Footprint": "0402", "Qty": "1", "DNP": ""},
            {"Reference": "R2", "MF": "Yageo", "MPN": "R2PART", "Value": "1k", "Datasheet": "", "Footprint": "0603", "Qty": "1", "DNP": ""},
        ]
        result = normalise_rows(rows, HEADERS)
        records = classify_result(result)
        self.assertEqual([r.normalised_record["Reference"] for r in records], ["C2", "R2", "R10"])

    def test_outputs_are_complete_and_report_no_lookup_or_provider_activity(self):
        rows = [
            {"Reference": "C1", "MF": "", "MPN": "", "Value": "100nF", "Datasheet": "", "Footprint": "0402", "Qty": "2", "DNP": ""},
            {"Reference": "U1", "MF": "TI", "MPN": "ABC123", "Value": "", "Datasheet": "", "Footprint": "QFN", "Qty": "1", "DNP": ""},
        ]
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "bom.csv"
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=HEADERS)
                writer.writeheader()
                writer.writerows(rows)
            result, records = classify_source_bom(source)
            outputs = write_classification_outputs(source, result, records, Path(folder) / "out")
            with outputs["classification_csv"].open("r", encoding="utf-8-sig", newline="") as handle:
                output_rows = list(csv.DictReader(handle))
            self.assertEqual(len(output_rows), 2)
            self.assertEqual(output_rows[0]["Classification"], CLASS_VALUE_FOOTPRINT)
            summary = json.loads(outputs["summary_json"].read_text(encoding="utf-8"))
            self.assertEqual(summary["classified_rows"], 2)
            self.assertEqual(summary["parts_master_lookups"], 0)
            self.assertEqual(summary["provider_calls"], 0)
            self.assertEqual(summary["automatic_approvals"], 0)


if __name__ == "__main__":
    unittest.main()
