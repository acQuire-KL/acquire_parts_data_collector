import json
import unittest
from pathlib import Path

from commercial_profile import build_commercial_profile, commercial_offers
from main import all_price_breaks_summary, offer_value_summary


class MultipleCommercialOffersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cache = Path(__file__).resolve().parents[1] / "cache" / "MCP1711T_25I_OT_MFG_150.json"
        cls.response = json.loads(cache.read_text(encoding="utf-8"))
        cls.profile = build_commercial_profile(
            cls.response,
            {"provider": "DigiKey", "currency": "EUR", "captured_at_utc": "2026-07-24T00:00:00Z"},
        )

    def test_all_packaging_offers_are_preserved(self):
        offers = commercial_offers(self.profile)
        self.assertEqual(3, len(offers))
        self.assertEqual({"Cut Tape", "DigiReel", "Reel"}, {offer["pack_format"] for offer in offers})

    def test_enriched_parts_summary_contains_every_provider_part_number(self):
        summary = offer_value_summary(self.profile, "provider_part_number")
        self.assertIn("MCP1711T-25I/OTCT-ND", summary)
        self.assertIn("MCP1711T-25I/OTDKR-ND", summary)
        self.assertIn("MCP1711T-25I/OTTR-ND", summary)

    def test_price_summary_groups_price_ladders_by_offer(self):
        summary = all_price_breaks_summary(self.profile)
        self.assertIn("Cut Tape", summary)
        self.assertIn("DigiReel", summary)
        self.assertIn("Reel", summary)
        self.assertIn("1 @", summary)
        self.assertIn("3,000 @", summary)


if __name__ == "__main__":
    unittest.main()
