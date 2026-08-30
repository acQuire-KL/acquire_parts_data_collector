import unittest

from main import build_combined_result, _provider_dashboard_profiles
from multi_provider_summary import ProviderEvidence
from operational_bom_review import LocalPartContext


def ev(provider, commercial, *, match=True):
    return ProviderEvidence(
        provider=provider,
        execution_status="success",
        part_profile={"identity_match": match, "manufacturer": "MFG", "manufacturer_part_number": "ABC"},
        commercial_profile=commercial,
    )


class ProviderDashboard472aTests(unittest.TestCase):
    def test_empty_provider_does_not_consume_dashboard_position(self):
        evidence = [
            ev("DigiKey", {"provider": "DigiKey"}),
            ev("Mouser", {"provider": "Mouser", "product_quantity_available": 250, "manufacturer_lead_weeks": "8 Weeks"}),
            ev("TME", {"provider": "TME", "product_quantity_available": 100}),
        ]
        dashboard = _provider_dashboard_profiles(evidence)
        self.assertEqual(["Mouser", "TME"], [name for name, _ in dashboard])

    def test_provider_positions_are_result_driven_per_row(self):
        evidence = [
            ev("DigiKey", {}),
            ev("Mouser", {"product_quantity_available": 250, "manufacturer_lead_weeks": "67 Days", "provider_currency": "EUR"}),
        ]
        result = build_combined_result(
            38, "MFG", "ABC", evidence,
            local_context=LocalPartContext(), bom_context={}
        )
        self.assertEqual("Mouser", result["Provider #1 Name"])
        self.assertEqual(250, result["Provider #1 Available"])
        self.assertEqual(10, result["Provider #1 Lead Time"])
        self.assertEqual("", result["Provider #2 Name"])

    def test_zero_lead_time_is_conservative(self):
        evidence = [ev("Mouser", {"manufacturer_lead_weeks": "0 Days", "provider_currency": "EUR"})]
        result = build_combined_result(1, "MFG", "ABC", evidence, local_context=LocalPartContext(), bom_context={})
        self.assertEqual("Request Delivery Quote", result["Provider #1 Lead Time"])


if __name__ == "__main__":
    unittest.main()
