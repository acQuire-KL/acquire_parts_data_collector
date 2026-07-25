import unittest
from unittest.mock import Mock

from config import MouserSettings
from providers.base_provider import ProviderConfigurationError
from providers.mouser.client import MouserApiError, MouserClient


class MouserClientTests(unittest.TestCase):
    def setUp(self):
        self.session = Mock()
        self.settings = MouserSettings(api_key="test-key")
        self.client = MouserClient(self.settings, session=self.session)

    def test_part_number_search_uses_official_endpoint_and_request_shape(self):
        response = Mock()
        response.json.return_value = {"SearchResults": {"NumberOfResult": 1, "Parts": []}}
        self.session.post.return_value = response

        actual = self.client.search_part_number(" ABC123 ")

        self.assertEqual(response.json.return_value, actual)
        self.session.post.assert_called_once_with(
            "https://api.mouser.com/api/v1/search/partnumber",
            params={"apiKey": "test-key"},
            json={
                "SearchByPartRequest": {
                    "mouserPartNumber": "ABC123",
                    "partSearchOptions": "string",
                    "mouserPaysCustomsAndDuties": False,
                }
            },
            timeout=30.0,
        )
        response.raise_for_status.assert_called_once_with()

    def test_missing_api_key_is_reported_as_configuration_error(self):
        client = MouserClient(MouserSettings(api_key=""), session=self.session)

        with self.assertRaisesRegex(ProviderConfigurationError, "MOUSER_API_KEY"):
            client.search_part_number("ABC123")

        self.session.post.assert_not_called()

    def test_empty_mpn_is_rejected_before_api_call(self):
        with self.assertRaisesRegex(ValueError, "MPN is required"):
            self.client.search_part_number("  ")

        self.session.post.assert_not_called()

    def test_api_error_payload_raises_controlled_error(self):
        response = Mock()
        response.json.return_value = {"Errors": [{"Code": "BadRequest", "Message": "Invalid API key"}]}
        self.session.post.return_value = response

        with self.assertRaisesRegex(MouserApiError, "Invalid API key"):
            self.client.search_part_number("ABC123")

    def test_manufacturer_list_uses_v2_endpoint(self):
        response = Mock()
        response.json.return_value = {"MouserManufacturerList": []}
        self.session.get.return_value = response

        actual = self.client.manufacturers()

        self.assertEqual(response.json.return_value, actual)
        self.session.get.assert_called_once_with(
            "https://api.mouser.com/api/v2/search/manufacturerlist",
            params={"apiKey": "test-key"},
            timeout=30.0,
        )


if __name__ == "__main__":
    unittest.main()
