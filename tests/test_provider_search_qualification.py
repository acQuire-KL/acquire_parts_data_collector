import unittest

from provider_search_qualification import (
    STATUS_ALIAS_MATCH,
    STATUS_MULTIPLE_CANDIDATES,
    extract_digikey_candidates,
    qualification_status,
)


class ProviderSearchQualificationTests(unittest.TestCase):
    def test_candidates_rank_source_manufacturer_first_without_discarding_others(self):
        payload = {
            "Products": [
                {
                    "Manufacturer": {"Name": "Vishay", "Id": 1},
                    "ManufacturerProductNumber": "1N4148",
                    "DigiKeyProductNumber": "1N4148-VISHAY-ND",
                },
                {
                    "Manufacturer": {"Name": "Diotec Semiconductor", "Id": 2},
                    "ManufacturerProductNumber": "1N4148",
                    "DigiKeyProductNumber": "1N4148-DIOTEC-ND",
                },
                {
                    "Manufacturer": {"Name": "onsemi", "Id": 3},
                    "ManufacturerProductNumber": "1N4148",
                    "DigiKeyProductNumber": "1N4148-ON-ND",
                },
            ]
        }
        candidates = extract_digikey_candidates(payload, "Diotec Semi", "1N4148")
        self.assertEqual(3, len(candidates))
        self.assertEqual("Diotec Semiconductor", candidates[0].returned_manufacturer)
        self.assertTrue(candidates[0].manufacturer_equivalent or candidates[0].manufacturer_score > 0.7)
        self.assertEqual([1, 2, 3], [item.rank for item in candidates])
        self.assertEqual(STATUS_MULTIPLE_CANDIDATES, qualification_status(candidates))

    def test_single_equivalent_candidate_is_alias_match(self):
        payload = {
            "Products": [{
                "Manufacturer": {"Name": "Würth Elektronik", "Id": 100},
                "ManufacturerProductNumber": "ABC-123",
            }]
        }
        candidates = extract_digikey_candidates(payload, "Wurth", "ABC123")
        self.assertEqual(STATUS_ALIAS_MATCH, qualification_status(candidates))

    def test_no_candidates_is_not_found(self):
        candidates = extract_digikey_candidates({"Products": []}, "MFG", "MPN")
        self.assertEqual([], candidates)


if __name__ == "__main__":
    unittest.main()
