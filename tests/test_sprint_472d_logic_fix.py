import unittest
from identity_recovery import discover_payload_candidates
from main import _provider_consensus_count
from multi_provider_summary import ProviderEvidence

class LogicFixTests(unittest.TestCase):
    def test_digikey_search_retains_formatting_equivalent_hirose(self):
        payload = {"Products": [{
            "ManufacturerProductNumber": "BM28B0.6-6DP/2-0.35V(51)",
            "Manufacturer": {"Name": "Hirose Electric Co Ltd"},
        }]}
        found = discover_payload_candidates(
            "DigiKey", payload,
            requested_manufacturer="Hirose Electric Co Ltd",
            reference_mpn="BM28B0.6-6DP_2-0.35V_51_",
        )
        self.assertEqual(1, len(found))
        self.assertEqual("BM28B0.6-6DP/2-0.35V(51)", found[0].mpn)
        self.assertEqual("Formatting-normalised identity candidate", found[0].relationship)

    def test_two_provider_matches_stop_discovery_even_if_mfg_spellings_differ(self):
        a = ProviderEvidence("DigiKey", "success", part_profile={"identity_match": True, "manufacturer":"Abracon LLC", "manufacturer_part_number":"AOTA-N160808S-2R2MT"})
        b = ProviderEvidence("Mouser", "success", part_profile={"identity_match": True, "manufacturer":"Abracon", "manufacturer_part_number":"AOTA-N160808S-2R2MT"})
        c = ProviderEvidence("TME", "no_match", "Not listed")
        self.assertEqual(2, _provider_consensus_count([a,b,c]))

if __name__ == "__main__":
    unittest.main()
