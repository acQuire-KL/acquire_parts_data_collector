import csv
import json
import tempfile
import unittest
from pathlib import Path

from bom_normalizer import (
    BOMNormalisationError,
    combine_references,
    normalise_dnp,
    normalise_rows,
    write_outputs,
)


HEADERS = ["Reference", "MF", "MPN", "Value", "Datasheet", "Footprint", "Qty", "DNP"]


class BOMNormalizerTests(unittest.TestCase):
    def test_natural_reference_sort(self):
        self.assertEqual(combine_references(["D10", "D2", "D1", "D11"]), "D1, D2, D10, D11")

    def test_groups_same_mfg_mpn_and_sums_quantity(self):
        rows = [
            {"Reference": "R2", "MF": "Yageo", "MPN": "RC0603", "Value": "10k", "Footprint": "0603", "Qty": "1", "DNP": ""},
            {"Reference": "R10", "MF": "Yageo", "MPN": "RC0603", "Value": "10k", "Footprint": "0603", "Qty": "2", "DNP": "No"},
        ]
        result = normalise_rows(rows, HEADERS)
        self.assertEqual(result.source_row_count, 2)
        self.assertEqual(result.normalised_row_count, 1)
        record = result.normalised_rows[0].as_output_record()
        self.assertEqual(record["Reference"], "R2, R10")
        self.assertEqual(record["Quantity"], 3)

    def test_dnp_and_fitted_are_separate_groups(self):
        rows = [
            {"Reference": "R1", "MF": "Yageo", "MPN": "RC0603", "Value": "10k", "Footprint": "0603", "Qty": "1", "DNP": ""},
            {"Reference": "R2", "MF": "Yageo", "MPN": "RC0603", "Value": "10k", "Footprint": "0603", "Qty": "1", "DNP": "DNP"},
        ]
        result = normalise_rows(rows, HEADERS)
        self.assertEqual(result.normalised_row_count, 2)
        self.assertEqual({group.as_output_record()["DNP"] for group in result.normalised_rows}, {"Yes", "No"})

    def test_blank_mpn_uses_value_footprint_and_dnp(self):
        rows = [
            {"Reference": "C1", "MF": "", "MPN": "", "Value": "100nF", "Footprint": "0402", "Qty": "1", "DNP": ""},
            {"Reference": "C2", "MF": "", "MPN": "", "Value": "100nF", "Footprint": "0402", "Qty": "1", "DNP": ""},
            {"Reference": "C3", "MF": "", "MPN": "", "Value": "100nF", "Footprint": "0603", "Qty": "1", "DNP": ""},
        ]
        result = normalise_rows(rows, HEADERS)
        self.assertEqual(result.normalised_row_count, 2)
        grouped = [group.as_output_record() for group in result.normalised_rows]
        self.assertEqual(grouped[0]["Reference"], "C1, C2")
        self.assertIn("MPN blank", grouped[0]["Grouping Basis"])

    def test_complete_source_data_is_retained(self):
        rows = [{
            "Reference": "U1", "MF": "Texas Instruments", "MPN": "ABC123", "Value": "ABC123",
            "Datasheet": "https://example.test/abc.pdf", "Footprint": "BGA", "Qty": "1", "DNP": "",
        }]
        result = normalise_rows(rows, HEADERS)
        record = result.normalised_rows[0].as_output_record()
        source_data = json.loads(record["Source Data JSON"])
        self.assertEqual(source_data[0]["values"], rows[0])
        result.validate_lossless()

    def test_unknown_dnp_value_is_not_guessed(self):
        with self.assertRaises(BOMNormalisationError):
            normalise_dnp("maybe")

    def test_clean_output_excludes_debug_columns(self):
        rows = [{"Reference": "R1", "MF": "Yageo", "MPN": "RC0603", "Value": "10k", "Datasheet": "", "Footprint": "0603", "Qty": "1", "DNP": ""}]
        result = normalise_rows(rows, HEADERS)
        clean = result.normalised_rows[0].as_clean_output_record()
        self.assertNotIn("Grouping Basis", clean)
        self.assertNotIn("Source Rows", clean)
        self.assertNotIn("Source Data JSON", clean)

    def test_debug_output_retains_trace_columns(self):
        rows = [{"Reference": "R1", "MF": "Yageo", "MPN": "RC0603", "Value": "10k", "Datasheet": "", "Footprint": "0603", "Qty": "1", "DNP": ""}]
        result = normalise_rows(rows, HEADERS)
        debug = result.normalised_rows[0].as_debug_output_record()
        self.assertIn("Grouping Basis", debug)
        self.assertIn("Source Rows", debug)
        self.assertIn("Source Data JSON", debug)

    def test_clean_and_debug_outputs_are_sorted_by_first_reference(self):
        rows = [
            {"Reference": "R10", "MF": "Yageo", "MPN": "R10PART", "Value": "10k", "Datasheet": "", "Footprint": "0603", "Qty": "1", "DNP": ""},
            {"Reference": "C2", "MF": "Murata", "MPN": "C2PART", "Value": "100nF", "Datasheet": "", "Footprint": "0402", "Qty": "1", "DNP": ""},
            {"Reference": "R2", "MF": "Yageo", "MPN": "R2PART", "Value": "1k", "Datasheet": "", "Footprint": "0603", "Qty": "1", "DNP": ""},
            {"Reference": "C10", "MF": "Murata", "MPN": "C10PART", "Value": "1uF", "Datasheet": "", "Footprint": "0603", "Qty": "1", "DNP": ""},
        ]
        result = normalise_rows(rows, HEADERS)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.csv"
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=HEADERS)
                writer.writeheader()
                writer.writerows(rows)
            outputs = write_outputs(result, source, Path(folder) / "out")

            for key in ("normalised_csv", "normalised_debug_csv"):
                with outputs[key].open("r", encoding="utf-8-sig", newline="") as handle:
                    references = [row["Reference"] for row in csv.DictReader(handle)]
                self.assertEqual(references, ["C2", "C10", "R2", "R10"])

    def test_group_sort_uses_first_reference_in_combined_group(self):
        rows = [
            {"Reference": "R20", "MF": "Yageo", "MPN": "GROUPA", "Value": "10k", "Datasheet": "", "Footprint": "0603", "Qty": "1", "DNP": ""},
            {"Reference": "R3", "MF": "Yageo", "MPN": "GROUPA", "Value": "10k", "Datasheet": "", "Footprint": "0603", "Qty": "1", "DNP": ""},
            {"Reference": "R10", "MF": "Yageo", "MPN": "GROUPB", "Value": "1k", "Datasheet": "", "Footprint": "0603", "Qty": "1", "DNP": ""},
        ]
        result = normalise_rows(rows, HEADERS)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.csv"
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=HEADERS)
                writer.writeheader()
                writer.writerows(rows)
            outputs = write_outputs(result, source, Path(folder) / "out")
            with outputs["normalised_csv"].open("r", encoding="utf-8-sig", newline="") as handle:
                references = [row["Reference"] for row in csv.DictReader(handle)]
            self.assertEqual(references, ["R3, R20", "R10"])

    def test_outputs_include_source_copy_clean_debug_trace_and_summary(self):
        rows = [{"Reference": "R1", "MF": "Yageo", "MPN": "RC0603", "Value": "10k", "Datasheet": "", "Footprint": "0603", "Qty": "1", "DNP": ""}]
        result = normalise_rows(rows, HEADERS)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.csv"
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=HEADERS)
                writer.writeheader()
                writer.writerows(rows)
            outputs = write_outputs(result, source, Path(folder) / "out")
            self.assertTrue(all(path.exists() for path in outputs.values()))
            self.assertIn("normalised_debug_csv", outputs)

            with outputs["normalised_csv"].open("r", encoding="utf-8-sig", newline="") as handle:
                clean_headers = next(csv.reader(handle))
            self.assertNotIn("Grouping Basis", clean_headers)
            self.assertNotIn("Source Rows", clean_headers)
            self.assertNotIn("Source Data JSON", clean_headers)

            with outputs["normalised_debug_csv"].open("r", encoding="utf-8-sig", newline="") as handle:
                debug_headers = next(csv.reader(handle))
            self.assertIn("Grouping Basis", debug_headers)
            self.assertIn("Source Rows", debug_headers)
            self.assertIn("Source Data JSON", debug_headers)

            summary = json.loads(outputs["summary_json"].read_text(encoding="utf-8"))
            self.assertEqual(summary["lossless_traceability_check"], "PASS")


if __name__ == "__main__":
    unittest.main()
