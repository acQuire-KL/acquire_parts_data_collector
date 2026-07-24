import json
import tempfile
import unittest
from pathlib import Path

from commercial_profile import (
    COMMERCIAL_PROFILE_SCHEMA_VERSION,
    build_commercial_profile,
    commercial_offers,
    ensure_current_commercial_profile,
)
from knowledge_base_manager import KnowledgeBaseManager, KNOWLEDGE_BASE_SCHEMA_VERSION


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CommercialProfileTests(unittest.TestCase):
    def _raw_response(self, pattern: str) -> dict:
        matches = sorted((PROJECT_ROOT / "raw_responses").glob(pattern))
        self.assertTrue(matches, f"No raw response matched {pattern}")
        return json.loads(matches[-1].read_text(encoding="utf-8"))

    def test_multiple_digikey_variations_become_offers(self):
        response = self._raw_response("MCP1711T_25I_OT_MFG_*.json")
        profile = build_commercial_profile(
            response,
            {"provider": "DigiKey", "currency": "EUR", "captured_at_utc": "2026-07-01T00:00:00Z"},
        )
        offers = commercial_offers(profile)
        self.assertEqual(profile["commercial_profile_schema_version"], COMMERCIAL_PROFILE_SCHEMA_VERSION)
        self.assertGreaterEqual(len(offers), 2)
        self.assertEqual(profile["offer_count"], len(offers))
        self.assertEqual(profile["variation_count"], len(offers))
        self.assertEqual(profile["offers"], profile["variations"])

    def test_legacy_variations_profile_is_upgraded(self):
        legacy = {
            "commercial_profile_schema_version": "1.1",
            "provider": "DigiKey",
            "variations": [{"provider_part_number": "ABC-CT"}],
        }
        upgraded = ensure_current_commercial_profile(legacy)
        self.assertEqual(upgraded["offers"][0]["provider_part_number"], "ABC-CT")
        self.assertEqual(upgraded["offer_count"], 1)

    def test_existing_knowledge_record_without_profile_loads(self):
        source = PROJECT_ROOT / "Knowledge_Base" / "Current" / "DigiKey" / "Product_Details" / "Microchip_Technology__MCP1711T-25I_OT.json"
        self.assertTrue(source.exists())
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "Knowledge_Base"
            target = root / "Current" / "DigiKey" / "Product_Details" / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            manager = KnowledgeBaseManager(root)
            record = manager.load_current("DigiKey", "Product_Details", "Microchip Technology", "MCP1711T-25I/OT")
            self.assertIsNotNone(record)
            assert record is not None
            self.assertGreaterEqual(len(commercial_offers(record.commercial_profile)), 2)
            manifest = json.loads((root / "Manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], KNOWLEDGE_BASE_SCHEMA_VERSION)


if __name__ == "__main__":
    unittest.main()
