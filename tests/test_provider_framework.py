import unittest
from unittest.mock import Mock

from providers.base_provider import BaseProvider
from providers.digikey import DigiKeyProvider


class ProviderFrameworkTests(unittest.TestCase):
    def setUp(self):
        self.settings = Mock()
        self.client = Mock()
        self.provider = DigiKeyProvider(self.settings, client=self.client)

    def test_digikey_provider_implements_base_provider(self):
        self.assertIsInstance(self.provider, BaseProvider)

    def test_provider_exposes_stable_metadata(self):
        self.assertEqual("DigiKey", self.provider.name)
        self.assertEqual("DigiKey Product Information V4", self.provider.attribute_source)

    def test_provider_declares_required_environment_variables(self):
        self.assertEqual(
            ("DIGIKEY_CLIENT_ID", "DIGIKEY_CLIENT_SECRET"),
            self.provider.required_environment_variables,
        )

    def test_manufacturer_collection_is_delegated_to_client(self):
        expected = {"Manufacturers": [{"Id": 1, "Name": "Example"}]}
        self.client.manufacturers.return_value = expected

        actual = self.provider.manufacturers(force=True)

        self.assertIs(expected, actual)
        self.client.manufacturers.assert_called_once_with(True)

    def test_product_details_are_delegated_without_data_changes(self):
        expected = Mock()
        self.client.details.return_value = expected

        actual = self.provider.details(
            "ABC123",
            42,
            True,
            input_manufacturer="Input Mfg",
            resolved_manufacturer="Resolved Mfg",
        )

        self.assertIs(expected, actual)
        self.client.details.assert_called_once_with(
            "ABC123",
            42,
            True,
            input_manufacturer="Input Mfg",
            resolved_manufacturer="Resolved Mfg",
        )


if __name__ == "__main__":
    unittest.main()
