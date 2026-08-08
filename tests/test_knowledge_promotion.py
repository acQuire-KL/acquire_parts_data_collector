from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from knowledge_promotion import (
    build_knowledge_events,
    current_approved_parts,
    current_manufacturer_aliases,
    derive_current_knowledge,
    validate_review_rows,
    write_knowledge_outputs,
)


class KnowledgePromotionTests(unittest.TestCase):
    def accepted_rows(self):
        base = {
            "Review ID": "REV-ADS", "Record ID": "PMR-000006", "Provider": "DigiKey",
            "Source Manufacturer": "TI", "Source MPN": "ADS1232IPW",
            "Candidate Manufacturer": "Texas Instruments", "Candidate Rank": "1",
            "Description": "ADC", "Product URL": "https://example",
            "Evidence": "Candidate found by MPN-only fallback", "Review Decision": "Accept",
            "Approved Manufacturer": "Texas Instruments", "Procurement Variant Group": "",
            "Engineer Notes": "Packaging difference only", "Reviewed By": "Ken", "Reviewed Date": "04-Aug",
        }
        first = dict(base, **{"Candidate MPN": "ADS1232IPW", "Approved MPN": "ADS1232IPW"})
        second = dict(base, **{"Candidate Rank": "2", "Candidate MPN": "ADS1232IPWR", "Approved MPN": "ADS1232IPWR"})
        return [first, second]

    def test_accepted_mpn_is_stored_once_not_as_variant_plus_addition(self):
        events = build_knowledge_events(self.accepted_rows(), recorded_at_utc="2026-08-05T12:00:00Z")
        approved = [row for row in events if row["Knowledge Type"] == "Approved Part"]
        self.assertEqual(len(approved), 2)
        self.assertEqual({r["Candidate MPN"] for r in approved}, {"ADS1232IPW", "ADS1232IPWR"})
        self.assertFalse(any(r["Knowledge Type"] == "Manufacturer Alias" for r in events))
        self.assertFalse(any(r["Knowledge Type"] == "Approved Addition" for r in events))

    def test_alias_is_derived_from_accepted_part_without_extra_history_row(self):
        events = build_knowledge_events(self.accepted_rows(), recorded_at_utc="2026-08-05T12:00:00Z")
        aliases = current_manufacturer_aliases(events)
        self.assertEqual(len(aliases), 1)
        self.assertEqual(aliases[0]["Standard Manufacturer Name"], "Texas Instruments")
        self.assertEqual(aliases[0]["Manufacturer Alias"], "TI")

    def test_procurement_variants_share_relationship_group(self):
        events = build_knowledge_events(self.accepted_rows(), recorded_at_utc="2026-08-05T12:00:00Z")
        approved = [row for row in events if row["Knowledge Type"] == "Approved Part"]
        self.assertEqual(len({row["Relationship Group"] for row in approved}), 1)
        self.assertTrue(all(row["Relationship Type"] == "Procurement Variant" for row in approved))

    def test_original_and_candidate_identity_are_always_preserved_for_review(self):
        events = build_knowledge_events(self.accepted_rows(), recorded_at_utc="2026-08-05T12:00:00Z")
        exact = next(row for row in events if row["Knowledge Type"] == "Approved Part" and row["Candidate MPN"] == "ADS1232IPW")
        variant = next(row for row in events if row["Knowledge Type"] == "Approved Part" and row["Candidate MPN"] == "ADS1232IPWR")
        self.assertEqual(exact["Original Manufacturer"], "TI")
        self.assertEqual(exact["Original MPN"], "ADS1232IPW")
        self.assertEqual(exact["Candidate Manufacturer"], "Texas Instruments")
        self.assertEqual(exact["Candidate MPN"], "ADS1232IPW")
        self.assertEqual(variant["Original MPN"], "ADS1232IPW")
        self.assertEqual(variant["Candidate MPN"], "ADS1232IPWR")

    def test_knowledge_history_column_order_is_engineer_first(self):
        from knowledge_promotion import HISTORY_FIELDS
        self.assertEqual(HISTORY_FIELDS[:4], [
            "Original Manufacturer", "Original MPN",
            "Candidate Manufacturer", "Candidate MPN",
        ])
        self.assertLess(HISTORY_FIELDS.index("Decision"), HISTORY_FIELDS.index("Knowledge ID"))
        self.assertLess(HISTORY_FIELDS.index("PDC Justification"), HISTORY_FIELDS.index("Knowledge ID"))
        self.assertNotIn("Standard Manufacturer Name", HISTORY_FIELDS)
        self.assertNotIn("Manufacturer Part Number", HISTORY_FIELDS)

    def test_reject_is_retained_as_review_knowledge_for_future_learning(self):
        row = self.accepted_rows()[0]
        row["Review Decision"] = "Reject"
        row["Approved Manufacturer"] = ""
        row["Approved MPN"] = ""
        row["Engineer Notes"] = "Different temperature grade"
        events = build_knowledge_events([row], recorded_at_utc="2026-08-05T12:00:00Z")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["Knowledge Type"], "Candidate Review")
        self.assertEqual(events[0]["Decision"], "Reject")
        self.assertEqual(events[0]["Engineer Comment"], "Different temperature grade")

    def test_blank_decision_is_blocking(self):
        row = self.accepted_rows()[0]
        row["Review Decision"] = ""
        issues = validate_review_rows([row])
        self.assertEqual(issues[0]["Severity"], "Error")

    def test_output_is_single_history_plus_summary_on_clean_run(self):
        rows = self.accepted_rows()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "RUN__CANDIDATE_REVIEW.csv"
            with source.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader(); writer.writerows(rows)
            outputs = write_knowledge_outputs(source)
            self.assertEqual(set(outputs), {"knowledge_history", "summary"})
            self.assertTrue(outputs["knowledge_history"].exists())
            summary = json.loads(outputs["summary"].read_text(encoding="utf-8"))
            self.assertEqual(summary["knowledge_events_generated_this_run"], 2)
            self.assertEqual(summary["current_approved_parts"], 2)
            self.assertEqual(summary["current_manufacturer_aliases"], 1)
            self.assertFalse(summary["parts_master_modified"])

    def test_rerun_does_not_duplicate_history(self):
        rows = self.accepted_rows()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "RUN__CANDIDATE_REVIEW.csv"
            with source.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader(); writer.writerows(rows)
            outputs = write_knowledge_outputs(source)
            first = json.loads(outputs["summary"].read_text(encoding="utf-8"))
            self.assertEqual(first["knowledge_history_rows_appended"], 2)
            outputs = write_knowledge_outputs(source)
            second = json.loads(outputs["summary"].read_text(encoding="utf-8"))
            self.assertEqual(second["knowledge_history_rows_appended"], 0)
            with outputs["knowledge_history"].open("r", encoding="utf-8-sig", newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 2)


    def test_rerun_rewrites_existing_history_using_current_column_order(self):
        rows = self.accepted_rows()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "RUN__CANDIDATE_REVIEW.csv"
            with source.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader(); writer.writerows(rows)

            outputs = write_knowledge_outputs(source)
            history_path = outputs["knowledge_history"]

            # Simulate an older presentation of the same immutable records by
            # rewriting the file with internal fields first.  A rerun of the
            # identical review must not append knowledge, but it must upgrade
            # the CSV presentation to the current engineer-first schema.
            with history_path.open("r", encoding="utf-8-sig", newline="") as handle:
                existing = list(csv.DictReader(handle))
            old_fields = [
                "Knowledge ID", "Knowledge Type", "Decision", "Review ID",
                "Record ID", "Original Manufacturer", "Original MPN",
                "Candidate Manufacturer", "Candidate MPN",
            ]
            with history_path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=old_fields, extrasaction="ignore")
                writer.writeheader(); writer.writerows(existing)

            outputs = write_knowledge_outputs(source)
            summary = json.loads(outputs["summary"].read_text(encoding="utf-8"))
            self.assertEqual(summary["knowledge_history_rows_appended"], 0)

            from knowledge_promotion import HISTORY_FIELDS
            with history_path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                rewritten = list(reader)
                self.assertEqual(reader.fieldnames, HISTORY_FIELDS)
            self.assertEqual(len(rewritten), len(existing))
            self.assertEqual(rewritten[0]["Knowledge ID"], existing[0]["Knowledge ID"])

    def test_changed_decision_appends_and_supersedes_without_editing_old_row(self):
        rows = self.accepted_rows()[:1]
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "RUN__CANDIDATE_REVIEW.csv"
            def save(data):
                with source.open("w", encoding="utf-8-sig", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(data[0].keys()))
                    writer.writeheader(); writer.writerows(data)
            save(rows)
            outputs = write_knowledge_outputs(source)
            with outputs["knowledge_history"].open("r", encoding="utf-8-sig", newline="") as handle:
                initial = list(csv.DictReader(handle))
            original_part = next(r for r in initial if r["Knowledge Type"] == "Approved Part")

            changed = [dict(rows[0])]
            changed[0]["Review Decision"] = "Reject"
            changed[0]["Approved Manufacturer"] = ""
            changed[0]["Approved MPN"] = ""
            changed[0]["Engineer Notes"] = "Later review reversed the earlier acceptance"
            changed[0]["Reviewed Date"] = "05-Aug"
            save(changed)
            outputs = write_knowledge_outputs(source)
            with outputs["knowledge_history"].open("r", encoding="utf-8-sig", newline="") as handle:
                history = list(csv.DictReader(handle))

            # The original event remains byte-for-byte as an event row; the new
            # row points backwards rather than rewriting it.
            old_after = next(r for r in history if r["Knowledge ID"] == original_part["Knowledge ID"])
            self.assertEqual(old_after["Supersedes"], original_part["Supersedes"])
            rejection = next(r for r in history if r["Knowledge Type"] == "Candidate Review")
            self.assertEqual(rejection["Supersedes"], original_part["Knowledge ID"])
            current = derive_current_knowledge(history)
            self.assertNotIn(original_part["Knowledge ID"], {r["Knowledge ID"] for r in current})

    def test_derived_views_require_no_duplicate_output_file(self):
        events = build_knowledge_events(self.accepted_rows(), recorded_at_utc="2026-08-05T12:00:00Z")
        self.assertEqual(len(current_approved_parts(events)), 2)
        self.assertEqual(len(current_manufacturer_aliases(events)), 1)

    def test_validation_file_only_created_when_needed(self):
        row = self.accepted_rows()[0]
        row["Reviewed By"] = ""
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "RUN__CANDIDATE_REVIEW.csv"
            with source.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
                writer.writeheader(); writer.writerow(row)
            outputs = write_knowledge_outputs(source)
            self.assertIn("validation", outputs)
            self.assertTrue(outputs["validation"].exists())

    def test_history_presentation_groups_rows_as_one_source_mpn_conversation(self):
        rows = self.accepted_rows()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "RUN__CANDIDATE_REVIEW.csv"
            with source.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader(); writer.writerows(rows)
            outputs = write_knowledge_outputs(source)
            with outputs["knowledge_history"].open("r", encoding="utf-8-sig", newline="") as handle:
                history = list(csv.DictReader(handle))

            # One source identity starts the conversation block.  Subsequent
            # rows are visually inherited until a new source MPN begins.
            self.assertEqual(history[0]["Original Manufacturer"], "TI")
            self.assertEqual(history[0]["Original MPN"], "ADS1232IPW")
            self.assertTrue(all(row["Original Manufacturer"] == "" for row in history[1:]))
            self.assertTrue(all(row["Original MPN"] == "" for row in history[1:]))

            # The exact returned MPN is shown first and variants follow.
            # No extra Manufacturer Alias row is stored.
            self.assertEqual(history[0]["Candidate MPN"], "ADS1232IPW")
            self.assertEqual(history[1]["Candidate MPN"], "ADS1232IPWR")
            self.assertTrue(all(row["Knowledge Type"] != "Manufacturer Alias" for row in history))

            # Full source identity remains stored in right-hand record fields.
            self.assertTrue(all(row["Source Manufacturer Record"] == "TI" for row in history))
            self.assertTrue(all(row["Source MPN Record"] == "ADS1232IPW" for row in history))

    def test_rerun_can_read_grouped_presentation_without_losing_source_identity(self):
        rows = self.accepted_rows()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "RUN__CANDIDATE_REVIEW.csv"
            with source.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader(); writer.writerows(rows)
            outputs = write_knowledge_outputs(source)
            outputs = write_knowledge_outputs(source)
            summary = json.loads(outputs["summary"].read_text(encoding="utf-8"))
            self.assertEqual(summary["knowledge_history_rows_appended"], 0)
            with outputs["knowledge_history"].open("r", encoding="utf-8-sig", newline="") as handle:
                history = list(csv.DictReader(handle))
            self.assertEqual(len(history), 2)
            self.assertEqual(history[0]["Original MPN"], "ADS1232IPW")
            self.assertEqual(history[1]["Original MPN"], "")

    def test_rerun_rehydrates_all_candidate_variants_when_legacy_history_candidates_are_blank(self):
        rows = self.accepted_rows()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "RUN__CANDIDATE_REVIEW.csv"
            with source.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader(); writer.writerows(rows)

            outputs = write_knowledge_outputs(source)
            history_path = outputs["knowledge_history"]

            # Simulate the Correction 6 symptom: immutable history rows remain,
            # but Candidate Manufacturer/MPN were lost during a schema rewrite.
            with history_path.open("r", encoding="utf-8-sig", newline="") as handle:
                legacy = list(csv.DictReader(handle))
            for row in legacy:
                row["Candidate Manufacturer"] = ""
                row["Candidate MPN"] = ""
            with history_path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=legacy[0].keys())
                writer.writeheader(); writer.writerows(legacy)

            outputs = write_knowledge_outputs(source)
            summary = json.loads(outputs["summary"].read_text(encoding="utf-8"))
            self.assertEqual(summary["knowledge_history_rows_appended"], 0)

            with history_path.open("r", encoding="utf-8-sig", newline="") as handle:
                repaired = list(csv.DictReader(handle))

            self.assertEqual([r["Candidate MPN"] for r in repaired], [
                "ADS1232IPW", "ADS1232IPWR"
            ])
            self.assertTrue(all(r["Candidate Manufacturer"] == "Texas Instruments" for r in repaired))
            self.assertEqual(repaired[0]["Original MPN"], "ADS1232IPW")
            self.assertEqual(repaired[1]["Original MPN"], "")

    def test_rerun_removes_legacy_derived_alias_rows_without_losing_alias_knowledge(self):
        rows = self.accepted_rows()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "RUN__CANDIDATE_REVIEW.csv"
            with source.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader(); writer.writerows(rows)
            outputs = write_knowledge_outputs(source)
            history_path = outputs["knowledge_history"]

            # Inject a legacy derived Manufacturer Alias row from older Patch 2b
            # output. The next run must migrate it away because the accepted
            # part row already stores the Original -> Candidate relationship.
            with history_path.open("r", encoding="utf-8-sig", newline="") as handle:
                history = list(csv.DictReader(handle))
            legacy = dict(history[0])
            legacy["Knowledge ID"] = "MA-LEGACY"
            legacy["Knowledge Type"] = "Manufacturer Alias"
            legacy["Candidate MPN"] = ""
            legacy["Manufacturer Alias"] = "TI"
            legacy["PDC Justification"] = "Approved review establishes a manufacturer alias"
            with history_path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=history[0].keys())
                writer.writeheader(); writer.writerows(history + [legacy])

            write_knowledge_outputs(source)
            with history_path.open("r", encoding="utf-8-sig", newline="") as handle:
                migrated = list(csv.DictReader(handle))

            self.assertEqual(len(migrated), 2)
            self.assertTrue(all(row["Knowledge Type"] != "Manufacturer Alias" for row in migrated))
            aliases = current_manufacturer_aliases(migrated)
            self.assertEqual(len(aliases), 1)
            self.assertEqual(aliases[0]["Standard Manufacturer Name"], "Texas Instruments")
            self.assertEqual(aliases[0]["Manufacturer Alias"], "TI")


if __name__ == "__main__":
    unittest.main()
