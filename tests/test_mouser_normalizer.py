import unittest

from providers.mouser.normalizer import build_mouser_pdc_part_profile


class MouserNormalizerTests(unittest.TestCase):
    def test_maps_mouser_record_to_pdc_part_profile_without_losing_commercial_data(self):
        record = {
            "knowledge_base_metadata": {
                "provider": "Mouser",
                "endpoint": "Part_Number_Search",
                "captured_at_utc": "2026-01-01T00:00:00Z",
                "source_mode": "live_api",
                "locale": "en-US",
            },
            "provider_response": {
                "Errors": [],
                "SearchResults": {
                    "NumberOfResult": 1,
                    "Parts": [{
                        "Availability": "3608 In Stock",
                        "AvailabilityInStock": "3608",
                        "DataSheetUrl": "https://example.test/data.pdf",
                        "Description": "LDO Voltage Regulators",
                        "FactoryStock": "0",
                        "ImagePath": "https://example.test/image.jpg",
                        "Category": "LDO Voltage Regulators",
                        "LeadTime": "140 Days",
                        "LifecycleStatus": None,
                        "Manufacturer": "Microchip Technology",
                        "ManufacturerPartNumber": "MCP1711T-25I/OT",
                        "Min": "1",
                        "Mult": "1",
                        "MouserPartNumber": "579-MCP1711T-25I/OT",
                        "ProductAttributes": [
                            {"AttributeName": "Packaging", "AttributeValue": "Reel"},
                            {"AttributeName": "Packaging", "AttributeValue": "Cut Tape"},
                            {"AttributeName": "Packaging", "AttributeValue": "MouseReel", "AttributeCost": "A MouseReel fee of €5.00 will be added. All MouseReel orders are non-cancellable and non-returnable."},
                            {"AttributeName": "Standard Pack Qty", "AttributeValue": "3000"},
                        ],
                        "PriceBreaks": [
                            {"Quantity": 1, "Price": "€0.43", "Currency": "EUR"},
                            {"Quantity": 3000, "Price": "€0.31", "Currency": "EUR"},
                        ],
                        "ProductDetailUrl": "https://example.test/product",
                        "ROHSStatus": "RoHS Compliant",
                        "SuggestedReplacement": "MCP1711T-25I/OT-A",
                        "UnitWeightKg": {"UnitWeight": 0.0000063},
                        "ProductCompliance": [
                            {"ComplianceName": "USHTS", "ComplianceValue": "8542390090"},
                            {"ComplianceName": "ECCN", "ComplianceValue": "EAR99"},
                        ],
                        "TradeCompliance": [
                            {"ComplianceName": "Country of Origin", "ComplianceValue": "Japan"},
                        ],
                    }],
                },
            },
        }

        profile = build_mouser_pdc_part_profile(record).to_dict()
        self.assertEqual(profile["schema_version"], "0.2")
        self.assertEqual(profile["provider_metadata"]["provider"], "Mouser")
        self.assertEqual(profile["identity"]["manufacturer_part_number"], "MCP1711T-25I/OT")
        self.assertEqual(profile["commercial"]["stock_quantity"], 3608)
        self.assertEqual(profile["commercial"]["manufacturer_lead_time_weeks"], 20.0)
        self.assertEqual(len(profile["commercial"]["price_breaks"]), 2)
        self.assertEqual(profile["commercial"]["offers"][0]["additional_charges"][0]["amount"], 5.0)
        self.assertEqual(profile["logistics"]["manufacturer_standard_pack_quantity"], 3000)
        self.assertEqual(profile["logistics"]["pack_formats"], ["Reel", "Cut Tape", "MouseReel"])
        self.assertAlmostEqual(profile["logistics"]["weight_value"], 0.0063)
        self.assertEqual(profile["regulatory"]["eccn"], "EAR99")
        self.assertEqual(profile["regulatory"]["hts_code"], "8542390090")
        self.assertEqual(profile["regulatory"]["country_of_origin"], "Japan")
        self.assertEqual(profile["lifecycle"]["suggested_replacement"], "MCP1711T-25I/OT-A")
        self.assertIn("commercial.price_breaks", profile["provenance"])

    def test_no_match_produces_empty_but_valid_profile(self):
        profile = build_mouser_pdc_part_profile({"provider_response": {"SearchResults": {"Parts": []}}}).to_dict()
        self.assertEqual(profile["provider_metadata"]["provider"], "Mouser")
        self.assertEqual(profile["identity"]["manufacturer_part_number"], "")
        self.assertEqual(profile["commercial"]["offers"], [])


if __name__ == "__main__":
    unittest.main()
