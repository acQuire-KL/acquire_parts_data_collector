import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from parts_master_attribute_enricher import _merge_attribute, enrich_index, build_provider_attribute_bank


class AttributeMergeTests(unittest.TestCase):
    def test_provider_verified_normalises_formatting(self):
        r = _merge_attribute({"DigiKey":"10 µF", "TME":"10µF"})
        self.assertEqual(r["Verification"], "Provider Verified")
        self.assertIsNotNone(r["Value"])

    def test_single_provider(self):
        r = _merge_attribute({"DigiKey":"X5R"})
        self.assertEqual(r, {"Value":"X5R", "Verification":"Single Provider"})

    def test_conflict_needs_verification_and_no_value(self):
        r = _merge_attribute({"DigiKey":"10V", "TME":"6.3V"})
        self.assertEqual(r["Verification"], "Needs Verification")
        self.assertIsNone(r["Value"])
        self.assertEqual(set(r["Observed_Values"]), {"10V","6.3V"})

    def test_real_samsung_capacitor_provider_agreement(self):
        kb = Path(__file__).resolve().parents[1] / "Knowledge_Base"
        bank = build_provider_attribute_bank(kb)
        attrs = bank.get("CL10A106MP8NNNC", {})
        self.assertIn("DigiKey", attrs)
        self.assertIn("TME", attrs)
        index = {"parts":[{"MPN":"CL10A106MP8NNNC"}]}
        enriched = enrich_index(index, kb)
        ta = enriched["parts"][0]["Technical_Attributes"]
        self.assertEqual(ta["Capacitance"]["Verification"], "Provider Verified")
        self.assertEqual(ta["Voltage_Rated"]["Verification"], "Provider Verified")
        self.assertEqual(ta["Dielectric"]["Verification"], "Provider Verified")
        self.assertEqual(ta["Tolerance"]["Verification"], "Provider Verified")


if __name__ == '__main__': unittest.main()
