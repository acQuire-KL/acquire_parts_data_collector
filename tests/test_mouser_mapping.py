import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from commercial_profile import build_commercial_profile
from config import MouserSettings
from knowledge_base_manager import KnowledgeBaseManager
from part_profile import build_part_profile
from providers.mouser import MouserProvider


SAMPLE = {
    "SearchResults": {
        "NumberOfResult": 1,
        "Parts": [
            {
                "Manufacturer": "Microchip Technology",
                "ManufacturerPartNumber": "MCP1711T-25I/OT",
                "MouserPartNumber": "579-MCP1711T-25I/OT",
                "Description": "LDO Voltage Regulators",
                "DataSheetUrl": "https://example.test/datasheet.pdf",
                "ProductDetailUrl": "https://example.test/product",
                "ImagePath": "https://example.test/image.jpg",
                "LifecycleStatus": "Active",
                "ROHSStatus": "RoHS Compliant",
                "Availability": "12,345 In Stock",
                "FactoryStock": "20000",
                "LeadTime": "12 Weeks",
                "Min": "1",
                "Mult": "1",
                "Packaging": "Cut Tape",
                "PriceBreaks": [
                    {"Quantity": 1, "Price": "€0.650", "Currency": "EUR"},
                    {"Quantity": 100, "Price": "€0.420", "Currency": "EUR"},
                ],
                "ProductAttributes": [
                    {"AttributeName": "Package / Case", "AttributeValue": "SOT-23-5"},
                    {"AttributeName": "Mounting Style", "AttributeValue": "SMD/SMT"},
                ],
                "ProductCompliance": [
                    {"ComplianceName": "REACH", "ComplianceValue": "Compliant"}
                ],
            }
        ],
    }
}


class MouserPartProfileTests(unittest.TestCase):
    def setUp(self):
        self.metadata = {
            "provider": "Mouser",
            "input_mpn": "MCP1711T-25I/OT",
            "captured_at_utc": "2026-07-25T12:00:00Z",
        }

    def test_identity_and_provider_part_number_are_mapped(self):
        profile = build_part_profile(SAMPLE, self.metadata)
        self.assertEqual("Microchip Technology", profile["manufacturer"])
        self.assertEqual("MCP1711T-25I/OT", profile["manufacturer_part_number"])
        self.assertEqual("579-MCP1711T-25I/OT", profile["provider_part_number"])

    def test_documentation_urls_are_mapped(self):
        profile = build_part_profile(SAMPLE, self.metadata)
        self.assertEqual("https://example.test/datasheet.pdf", profile["datasheet_url"])
        self.assertEqual("https://example.test/product", profile["product_url"])
        self.assertEqual("https://example.test/image.jpg", profile["image_url"])

    def test_lifecycle_and_rohs_are_mapped(self):
        profile = build_part_profile(SAMPLE, self.metadata)
        self.assertEqual("Active", profile["lifecycle_status"])
        self.assertEqual("RoHS Compliant", profile["rohs_status"])

    def test_package_and_mounting_are_mapped_from_attributes(self):
        profile = build_part_profile(SAMPLE, self.metadata)
        self.assertEqual("SOT-23-5", profile["package"])
        self.assertEqual("SMD/SMT", profile["mounting_type"])

    def test_compliance_is_preserved(self):
        profile = build_part_profile(SAMPLE, self.metadata)
        self.assertEqual("Compliant", profile["compliance"]["REACH"])


class MouserCommercialProfileTests(unittest.TestCase):
    def setUp(self):
        self.metadata = {
            "provider": "Mouser",
            "input_mpn": "MCP1711T-25I/OT",
            "captured_at_utc": "2026-07-25T12:00:00Z",
        }

    def test_offer_identity_packaging_and_moq_are_mapped(self):
        profile = build_commercial_profile(SAMPLE, self.metadata)
        offer = profile["offers"][0]
        self.assertEqual("579-MCP1711T-25I/OT", offer["provider_part_number"])
        self.assertEqual("Cut Tape", offer["pack_format"])
        self.assertEqual(1, offer["minimum_order_quantity"])

    def test_stock_text_is_converted_to_numeric_quantity(self):
        profile = build_commercial_profile(SAMPLE, self.metadata)
        self.assertEqual(12345, profile["product_quantity_available"])
        self.assertEqual(12345, profile["offers"][0]["quantity_available"])

    def test_currency_and_price_breaks_are_mapped(self):
        profile = build_commercial_profile(SAMPLE, self.metadata)
        self.assertEqual("EUR", profile["provider_currency"])
        self.assertEqual(0.65, profile["offers"][0]["standard_price_breaks"][0]["unit_price"])
        self.assertEqual(100, profile["offers"][0]["standard_price_breaks"][1]["break_quantity"])

    def test_factory_stock_and_lead_time_are_preserved(self):
        profile = build_commercial_profile(SAMPLE, self.metadata)
        self.assertEqual(20000, profile["manufacturer_public_quantity"])
        self.assertEqual("12 Weeks", profile["manufacturer_lead_weeks"])


class MouserKnowledgeRecordTests(unittest.TestCase):
    def test_details_returns_common_knowledge_record(self):
        with tempfile.TemporaryDirectory() as folder:
            client = Mock()
            client.search_part_number.return_value = SAMPLE
            provider = MouserProvider(
                MouserSettings(api_key="test-key"),
                KnowledgeBaseManager(Path(folder)),
                client=client,
            )
            record = provider.details(
                "MCP1711T-25I/OT",
                input_manufacturer="Microchip",
                resolved_manufacturer="Microchip Technology",
            )
            self.assertEqual("Mouser", record.metadata["provider"])
            self.assertEqual("Microchip Technology", record.part_profile["manufacturer"])
            self.assertEqual(1, record.commercial_profile["offer_count"])

    def test_raw_mouser_payload_is_preserved_as_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            client = Mock()
            client.search_part_number.return_value = SAMPLE
            provider = MouserProvider(
                MouserSettings(api_key="test-key"),
                KnowledgeBaseManager(Path(folder)),
                client=client,
            )
            record = provider.details("MCP1711T-25I/OT")
            self.assertIs(SAMPLE, record.provider_response)

    def test_saved_current_record_contains_both_common_profiles(self):
        with tempfile.TemporaryDirectory() as folder:
            client = Mock()
            client.search_part_number.return_value = SAMPLE
            manager = KnowledgeBaseManager(Path(folder))
            provider = MouserProvider(MouserSettings(api_key="test-key"), manager, client=client)
            provider.details("MCP1711T-25I/OT", resolved_manufacturer="Microchip Technology")
            loaded = manager.load_current(
                "Mouser", "Part_Number_Search", "Microchip Technology", "MCP1711T-25I/OT"
            )
            self.assertIsNotNone(loaded)
            self.assertEqual("579-MCP1711T-25I/OT", loaded.part_profile["provider_part_number"])
            self.assertEqual("EUR", loaded.commercial_profile["provider_currency"])


if __name__ == "__main__":
    unittest.main()
