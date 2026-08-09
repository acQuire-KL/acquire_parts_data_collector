from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from knowledge_base_population import (
    ProviderOutcome,
    STATUS_CACHED,
    STATUS_DOWNLOADED,
    STATUS_FAILED,
    STATUS_PROVIDER_ERROR,
    STATUS_SKIPPED,
    load_staging_records,
    populate_knowledge_base,
    write_population_outputs,
)
from providers.base_provider import ProviderConfigurationError


class FakeProvider:
    def __init__(self, name="Fake", *, status=STATUS_DOWNLOADED, failure=None):
        self.name = name
        self.status = status
        self.failure = failure
        self.calls = []

    def collect(self, record_id, manufacturer, mpn, *, force=False):
        self.calls.append((record_id, manufacturer, mpn, force))
        if self.failure:
            raise self.failure
        return ProviderOutcome(record_id, manufacturer, mpn, self.name, self.status)


def write_staging(path: Path, rows):
    fields = ["Record ID", "Manufacturer", "Manufacturer Part Number"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class KnowledgeBasePopulationTests(unittest.TestCase):
    def test_load_requires_identity_columns(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.csv"
            path.write_text("Record ID,Manufacturer\nREC-1,ABC\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_staging_records(path)

    def test_processes_each_record_against_each_provider(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "staging.csv"
            write_staging(path, [
                {"Record ID": "REC-1", "Manufacturer": "MFG1", "Manufacturer Part Number": "P1"},
                {"Record ID": "REC-2", "Manufacturer": "MFG2", "Manufacturer Part Number": "P2"},
            ])
            first = FakeProvider("DigiKey")
            second = FakeProvider("TME", status=STATUS_CACHED)
            run = populate_knowledge_base(path, [first, second], progress=False)
            self.assertEqual(4, len(run.outcomes))
            self.assertEqual(2, len(first.calls))
            self.assertEqual(2, len(second.calls))
            self.assertEqual(2, run.summary()["status_counts"][STATUS_DOWNLOADED])
            self.assertEqual(2, run.summary()["status_counts"][STATUS_CACHED])

    def test_limit_is_applied_before_provider_calls(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "staging.csv"
            write_staging(path, [
                {"Record ID": f"REC-{index}", "Manufacturer": "MFG", "Manufacturer Part Number": f"P{index}"}
                for index in range(1, 4)
            ])
            provider = FakeProvider()
            run = populate_knowledge_base(path, [provider], limit=1, progress=False)
            self.assertEqual(1, run.selected_records)
            self.assertEqual(1, len(provider.calls))

    def test_incomplete_identity_is_skipped_without_call(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "staging.csv"
            write_staging(path, [{"Record ID": "REC-1", "Manufacturer": "", "Manufacturer Part Number": "P1"}])
            provider = FakeProvider()
            run = populate_knowledge_base(path, [provider], progress=False)
            self.assertEqual(STATUS_SKIPPED, run.outcomes[0].status)
            self.assertEqual([], provider.calls)

    def test_configuration_and_runtime_errors_are_isolated(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "staging.csv"
            write_staging(path, [{"Record ID": "REC-1", "Manufacturer": "MFG", "Manufacturer Part Number": "P1"}])
            missing = FakeProvider("Missing", failure=ProviderConfigurationError("key absent"))
            broken = FakeProvider("Broken", failure=RuntimeError("network"))
            run = populate_knowledge_base(path, [missing, broken], progress=False)
            self.assertEqual(STATUS_SKIPPED, run.outcomes[0].status)
            self.assertEqual(STATUS_PROVIDER_ERROR, run.outcomes[1].status)
            self.assertIn("network", run.outcomes[1].message)

    def test_outputs_include_summary_failures_and_skips(self):
        with tempfile.TemporaryDirectory() as folder:
            run_path = Path(folder) / "out"
            from knowledge_base_population import PopulationRun
            run = PopulationRun("source.csv", "start", "finish", [
                ProviderOutcome("REC-1", "MFG", "P1", "A", STATUS_DOWNLOADED),
                ProviderOutcome("REC-2", "MFG", "P2", "A", STATUS_FAILED, "error"),
                ProviderOutcome("REC-3", "MFG", "P3", "B", STATUS_SKIPPED, "missing key"),
            ], total_staging_records=3, selected_records=3)
            paths = write_population_outputs(run, run_path)
            self.assertTrue(all(path.exists() for path in paths.values()))
            summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
            self.assertEqual(3, summary["provider_operations"])
            self.assertEqual(1, summary["status_counts"][STATUS_FAILED])
            self.assertEqual(2, len(paths["failures"].read_text(encoding="utf-8-sig").splitlines()))
            self.assertEqual(2, len(paths["skipped"].read_text(encoding="utf-8-sig").splitlines()))
            self.assertEqual("KB_POPULATION__RESULTS.csv", paths["results"].name)
            self.assertEqual("KB_POPULATION__SUMMARY.json", paths["summary"].name)

    def test_outputs_replace_legacy_dated_working_set_but_preserve_review(self):
        with tempfile.TemporaryDirectory() as folder:
            run_path = Path(folder) / "out"
            run_path.mkdir()
            legacy_result = run_path / "KB_POPULATION_20260803_201341__RESULTS.csv"
            legacy_summary = run_path / "KB_POPULATION_20260803_201341__SUMMARY.json"
            legacy_review = run_path / "KB_POPULATION_20260804_205122__CANDIDATE_REVIEW.csv"
            legacy_result.write_text("old", encoding="utf-8")
            legacy_summary.write_text("{}", encoding="utf-8")
            legacy_review.write_text("human decisions", encoding="utf-8")

            from knowledge_base_population import PopulationRun
            run = PopulationRun("source.csv", "start", "finish", [
                ProviderOutcome("REC-1", "MFG", "P1", "A", STATUS_DOWNLOADED),
            ], total_staging_records=1, selected_records=1)
            paths = write_population_outputs(run, run_path)

            self.assertFalse(legacy_result.exists())
            self.assertFalse(legacy_summary.exists())
            self.assertTrue(legacy_review.exists())
            self.assertTrue(paths["results"].exists())
            self.assertEqual("KB_POPULATION__RESULTS.csv", paths["results"].name)


if __name__ == "__main__":
    unittest.main()
