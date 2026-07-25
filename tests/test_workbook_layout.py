import unittest

from workbook_layout import enriched_parts_columns


class WorkbookLayoutTests(unittest.TestCase):
    def test_section_order(self):
        columns = enriched_parts_columns()
        section_order = []
        for section, *_ in columns:
            if not section_order or section_order[-1] != section:
                section_order.append(section)
        self.assertEqual(
            ["Status", "Identity", "Engineering", "DigiKey", "Mouser", "Documentation", "Compliance"],
            section_order,
        )

    def test_headings_are_unique(self):
        headings = [heading for _, heading, _, _ in enriched_parts_columns()]
        self.assertEqual(len(headings), len(set(headings)))

    def test_enriched_parts_has_compact_provider_dashboard(self):
        headings = [heading for _, heading, _, _ in enriched_parts_columns()]
        for provider in ("DigiKey", "Mouser"):
            self.assertIn(f"{provider} Available", headings)
            self.assertIn(f"{provider} Lead Time", headings)
            self.assertIn(f"{provider} Price Breaks", headings)
        self.assertNotIn("Provider Part Number", headings)
        self.assertNotIn("Pack Format", headings)
        self.assertNotIn("Minimum Order Quantity", headings)

    def test_returned_layout_is_a_copy(self):
        first = enriched_parts_columns()
        first.pop()
        self.assertNotEqual(len(first), len(enriched_parts_columns()))


if __name__ == "__main__":
    unittest.main()
