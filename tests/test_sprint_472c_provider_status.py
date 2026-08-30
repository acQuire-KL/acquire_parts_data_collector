import unittest
from main import _normalised_provider_status, _concise_provider_status, _provider_results_text
from multi_provider_summary import ProviderEvidence

class Sprint472cProviderStatusTests(unittest.TestCase):
    def test_provider_no_listing_is_not_error(self):
        item = ProviderEvidence("TME", "no_match", "No product listing")
        self.assertEqual("not listed", _concise_provider_status(item))

    def test_not_listed_count_is_distinct_from_error(self):
        evidence = [
            ProviderEvidence("DigiKey", "success", part_profile={"identity_match": True}),
            ProviderEvidence("Mouser", "success", part_profile={"identity_match": True}),
            ProviderEvidence("TME", "no_match", "No product listing"),
        ]
        self.assertEqual("2 matched; 1 not listed", _provider_results_text(evidence))

    def test_no_results_error_message_maps_to_no_match(self):
        self.assertEqual("no_match", _normalised_provider_status("error", "No results returned"))

    def test_real_provider_failure_remains_error(self):
        item = ProviderEvidence("TME", "error", "Connection timeout")
        self.assertEqual("provider error", _concise_provider_status(item))

if __name__ == "__main__":
    unittest.main()
