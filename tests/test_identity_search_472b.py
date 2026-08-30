import unittest
from identity_recovery import search_variants, family_search_variants

class IdentitySearch472bTests(unittest.TestCase):
    def test_source_is_preserved_and_alphanumeric_variant_added(self):
        items = search_variants("BM28B0.6-6DP_2-0.35V_51_")
        self.assertEqual("BM28B0.6-6DP_2-0.35V_51_", items[0].text)
        self.assertEqual("Source Search Text", items[0].kind)
        self.assertEqual("BM28B066DP2035V51", items[1].text)
        self.assertEqual("Alphanumeric Search Key", items[1].kind)

    def test_family_search_is_right_truncated_and_bounded(self):
        items = family_search_variants("BM28B0.6-6DP_2-0.35V_51_")
        self.assertTrue(items)
        full = "BM28B066DP2035V51"
        self.assertTrue(all(full.startswith(item.text) for item in items))
        self.assertTrue(all(item.reduction_percent <= 50 for item in items))

    def test_short_mpn_is_not_aggressively_truncated(self):
        self.assertEqual([], family_search_variants("ABC123"))

if __name__ == "__main__":
    unittest.main()
