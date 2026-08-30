import unittest

from attribute_normalization import normalise_attribute
from main import _merged_custom_value, _provider_results_text
from providers.provider_result import ProviderResult
from multi_provider_summary import ProviderEvidence


def ev(provider, status="success", match=False, temp="", message=""):
    profile = {"identity_match": match, "attributes": {}}
    if temp:
        profile["attributes"]["Operating Temperature"] = temp
    return ProviderEvidence(provider=provider, execution_status=status, message=message, part_profile=profile)


class TestAttributeNormalisation471b(unittest.TestCase):
    def test_temperature_formats_compare_equal(self):
        a = normalise_attribute("-55°C ~ 125°C", "Operating Temperature")
        b = normalise_attribute("-55.0 to 125.0 C", "Operating Temperature")
        self.assertEqual(a[0], b[0])
        self.assertEqual(a[1], "-55°C to 125°C")

    def test_equivalent_provider_values_collapse(self):
        evidence = [ev("DigiKey", match=True, temp="-55°C ~ 125°C"), ev("TME", match=True, temp="-55.0 to 125.0 C")]
        value = _merged_custom_value(evidence, lambda p: p["attributes"].get("Operating Temperature"), "Operating Temperature")
        self.assertEqual(value, "-55°C to 125°C")

    def test_real_difference_is_exception(self):
        evidence = [ev("DigiKey", match=True, temp="-55°C ~ 125°C"), ev("TME", match=True, temp="-40 to 125 C")]
        value = _merged_custom_value(evidence, lambda p: p["attributes"].get("Operating Temperature"), "Operating Temperature")
        self.assertTrue(value.startswith("EXCEPTION — "))
        self.assertIn("DigiKey:", value)
        self.assertIn("TME:", value)

    def test_provider_results_are_counts(self):
        evidence = [
            ev("P1", match=True), ev("P2", match=True),
            ev("P3", status="no_match"), ev("P4", status="error", message="timeout")
        ]
        self.assertEqual(_provider_results_text(evidence), "2 matched; 1 not listed; 1 error")

    def test_success_without_identity_is_unconfirmed(self):
        self.assertEqual(_provider_results_text([ev("P1", status="success", match=False)]), "1 unconfirmed")


if __name__ == "__main__":
    unittest.main()
