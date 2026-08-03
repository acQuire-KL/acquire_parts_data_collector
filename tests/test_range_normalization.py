import unittest

from provider_profiles.normalization import RangeValidationError, range_values
from providers.digikey.normalizer import build_digikey_provider_part_profile
from providers.tme.normalizer import build_tme_provider_part_profile


class RangeNormalizationTests(unittest.TestCase):
    def test_supported_signed_range_formats(self):
        self.assertEqual(range_values("-40...85°C", target_unit="C"), (-40.0, 85.0))
        self.assertEqual(range_values("-40°C ~ 85°C", target_unit="C"), (-40.0, 85.0))
        self.assertEqual(range_values("1.4...6V"), (1.4, 6.0))
        self.assertEqual(range_values("-55 V to -5 V"), (-55.0, -5.0))

    def test_fahrenheit_is_normalised_to_celsius(self):
        self.assertEqual(range_values("-40°F to 185°F", target_unit="C"), (-40.0, 85.0))

    def test_invalid_or_duplicated_range_is_rejected(self):
        with self.assertRaises(RangeValidationError):
            range_values("-40°C ~ -40°C", target_unit="C")
        with self.assertRaises(RangeValidationError):
            range_values("6V to 1.4V")

    def test_single_value_is_not_silently_turned_into_a_range(self):
        self.assertEqual(range_values("6V"), (None, None))
        self.assertEqual(range_values("6V", allow_single=True), (6.0, None))

    def test_digikey_and_tme_temperature_formats_correlate(self):
        self.assertEqual(
            range_values("-40°C ~ 85°C", target_unit="C"),
            range_values("-40...85°C", target_unit="C"),
        )


class ProviderRangeRegressionTests(unittest.TestCase):
    def test_digikey_operating_temperature_range(self):
        record = {
            "knowledge_base_metadata": {
                "provider": "DigiKey",
                "currency": "EUR",
                "locale": "IE",
                "captured_at_utc": "2026-01-01T00:00:00Z",
            },
            "provider_response": {
                "Product": {
                    "Description": {},
                    "Manufacturer": {"Name": "Microchip Technology"},
                    "ManufacturerProductNumber": "MCP1711T-25I/OT",
                    "ProductStatus": {},
                    "Classifications": {},
                    "ProductVariations": [],
                    "Parameters": [
                        {
                            "ParameterText": "Operating Temperature",
                            "ValueText": "-40°C ~ 85°C",
                        }
                    ],
                }
            },
        }
        profile = build_digikey_provider_part_profile(record)
        self.assertEqual(profile.technical.operating_temperature_min_c, -40.0)
        self.assertEqual(profile.technical.operating_temperature_max_c, 85.0)


if __name__ == "__main__":
    unittest.main()
