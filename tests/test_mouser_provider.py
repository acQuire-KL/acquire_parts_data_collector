import unittest
from unittest.mock import Mock

from config import MouserSettings
from providers.base_provider import BaseProvider, ProviderConfigurationError
from providers.mouser import MouserProvider
from providers.provider_manager import ProviderManager
from providers.provider_result import ProviderStatus


class MouserProviderTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        self.provider = MouserProvider(MouserSettings(api_key="test-key"), client=self.client)

    def test_mouser_provider_implements_base_provider(self):
        self.assertIsInstance(self.provider, BaseProvider)

    def test_provider_exposes_stable_metadata(self):
        self.assertEqual("Mouser", self.provider.name)
        self.assertEqual("Mouser Search API", self.provider.attribute_source)
        self.assertEqual(("MOUSER_API_KEY",), self.provider.required_environment_variables)

    def test_search_is_delegated_without_modifying_response(self):
        expected = {"SearchResults": {"Parts": [{"ManufacturerPartNumber": "ABC123"}]}}
        self.client.search_part_number.return_value = expected

        actual = self.provider.search_part_number("ABC123", part_search_options="Exact")

        self.assertIs(expected, actual)
        self.client.search_part_number.assert_called_once_with("ABC123", part_search_options="Exact")

    def test_manager_marks_missing_configuration_as_skipped(self):
        self.client.search_part_number.side_effect = ProviderConfigurationError(
            "MOUSER_API_KEY is not configured"
        )
        manager = ProviderManager([self.provider])

        result = manager.execute(self.provider, "search_part_number", "ABC123")

        self.assertEqual(ProviderStatus.SKIPPED, result.status)
        self.assertEqual("MOUSER_API_KEY is not configured", result.message)


if __name__ == "__main__":
    unittest.main()
