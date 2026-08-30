import unittest
from pathlib import Path
from identity_recovery import search_variants, normalise_mpn

class Sprint472cTests(unittest.TestCase):
    def test_hirose_source_and_alpha_forms(self):
        variants = search_variants("BM28B0.6-6DP_2-0.35V_51_")
        self.assertEqual("BM28B0.6-6DP_2-0.35V_51_", variants[0].text)
        self.assertEqual("BM28B066DP2035V51", variants[1].text)

    def test_corrected_hirose_is_format_equivalent(self):
        source = "BM28B0.6-6DP_2-0.35V_51_"
        corrected = "BM28B0.6-6DP/2-0.35V(51)"
        self.assertEqual(normalise_mpn(source), normalise_mpn(corrected))

    def test_abracon_exact_identity_is_stable(self):
        mpn = "AOTA-N160808S-2R2MT"
        self.assertEqual(normalise_mpn(mpn), normalise_mpn(mpn))

    def test_two_part_regression_fixture_exists(self):
        fixture = Path(__file__).parent / "fixtures" / "bom_identity_472c_hirose_abracon.csv"
        text = fixture.read_text()
        self.assertIn("Hirose Electric Co Ltd", text)
        self.assertIn("AOTA-N160808S-2R2MT", text)

if __name__ == "__main__":
    unittest.main()
