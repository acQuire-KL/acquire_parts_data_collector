import unittest

from config import TmeSettings
from knowledge_base_manager import KnowledgeRecord
from providers.tme.provider import TmeProvider


class _NoListingClient:
    def __init__(self):
        self.calls = []

    def access_token(self):
        self.calls.append(("token", None))
        return "TOKEN"

    def search_products(self, mpn, access_token=None):
        self.calls.append(("search", mpn))
        return {"data": {"products": {"elements": []}}}

    def get_product_data(self, symbol, access_token=None):
        self.calls.append(("data", symbol))
        raise AssertionError("Product Data must not be called when TME search returns no product")

    def get_product_parameters(self, symbol, access_token=None):
        self.calls.append(("parameters", symbol))
        raise AssertionError("Product Parameters must not be called when TME search returns no product")


class _KB:
    def save_raw_provider_response(self, **kwargs):
        return KnowledgeRecord(
            provider_response=kwargs["provider_response"],
            metadata={
                "provider": kwargs["provider"],
                "captured_at_utc": "2026-08-31T00:00:00Z",
            },
            commercial_profile={},
            part_profile=None,
        )


class Sprint472fTmeNotListedTests(unittest.TestCase):
    def test_zero_search_results_are_successful_not_listed_evidence(self):
        client = _NoListingClient()
        provider = TmeProvider(
            TmeSettings(token="x", application_secret="y"),
            knowledge_base=_KB(),
            client=client,
        )
        record = provider.details("NOT-LISTED", input_manufacturer="Example MFG")

        self.assertEqual({}, record.part_profile)
        self.assertEqual({}, record.commercial_profile)
        self.assertEqual("not_listed", record.metadata.get("provider_listing_status"))
        self.assertEqual(
            [("token", None), ("search", "NOT-LISTED")],
            client.calls,
        )

    def test_empty_search_response_has_no_symbol(self):
        self.assertEqual(
            "",
            TmeProvider._first_symbol({"data": {"products": {"elements": []}}}),
        )


if __name__ == "__main__":
    unittest.main()
