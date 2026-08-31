import unittest

from identity_recovery import discover_payload_candidates, normalise_mpn


class Sprint472gDigiKeyIndependentFirstTests(unittest.TestCase):
    def test_clean_exact_digikey_keyword_result_is_retained(self):
        payload = {"Products": [{
            "ManufacturerProductNumber": "AOTA-N160808S-2R2MT",
            "Manufacturer": {"Name": "Abracon LLC"},
        }]}
        found = discover_payload_candidates(
            "DigiKey", payload,
            requested_manufacturer="Abracon",
            reference_mpn="AOTA-N160808S-2R2MT",
        )
        self.assertEqual(1, len(found))
        self.assertEqual("AOTA-N160808S-2R2MT", found[0].mpn)
        self.assertEqual("Exact identity", found[0].relationship)

    def test_hirose_source_text_is_independently_normalised_by_digikey_result(self):
        source = "BM28B0.6-6DS_2-0.35V_51_"
        returned = "BM28B0.6-6DS/2-0.35V(51)"
        payload = {"Products": [{
            "ManufacturerProductNumber": returned,
            "Manufacturer": {"Name": "Hirose Electric Co Ltd"},
        }]}
        found = discover_payload_candidates(
            "DigiKey", payload,
            requested_manufacturer="Hirose",
            reference_mpn=source,
        )
        self.assertEqual(1, len(found))
        self.assertEqual(returned, found[0].mpn)
        self.assertEqual(
            "Formatting-normalised identity candidate",
            found[0].relationship,
        )
        self.assertEqual(normalise_mpn(source), normalise_mpn(returned))

    def test_hirose_dp_is_not_identity_for_ds_source(self):
        found = discover_payload_candidates(
            "DigiKey",
            {"Products": [{
                "ManufacturerProductNumber": "BM28B0.6-6DP/2-0.35V(51)",
                "Manufacturer": {"Name": "Hirose Electric Co Ltd"},
            }]},
            requested_manufacturer="Hirose",
            reference_mpn="BM28B0.6-6DS_2-0.35V_51_",
        )
        self.assertEqual(1, len(found))
        self.assertNotEqual(
            normalise_mpn("BM28B0.6-6DS_2-0.35V_51_"),
            normalise_mpn(found[0].mpn),
        )
        self.assertNotIn(
            found[0].relationship,
            ("Exact identity", "Formatting-normalised identity candidate"),
        )


if __name__ == "__main__":
    unittest.main()
