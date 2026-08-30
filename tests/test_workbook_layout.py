import unittest

from workbook_layout import column_keys, display_headings, enriched_parts_columns


class WorkbookLayoutTests(unittest.TestCase):
    def test_section_order(self):
        columns = enriched_parts_columns()
        section_order = []
        for column in columns:
            if not section_order or section_order[-1] != column.group:
                section_order.append(column.group)
        self.assertEqual(
            ["Status", "BOM Context", "Local Knowledge", "Identity", "Engineering", "Provider #1", "Provider #2", "Provider #3", "Documentation", "Compliance"],
            section_order,
        )

    def test_data_keys_are_unique(self):
        keys = column_keys(enriched_parts_columns())
        self.assertEqual(len(keys), len(set(keys)))

    def test_provider_dashboard_uses_position_based_blocks(self):
        columns = enriched_parts_columns()
        for position in (1, 2, 3):
            provider_columns = [column for column in columns if column.group == f"Provider #{position}"]
            self.assertEqual(
                ["Provider Name", "Available", "Lead Time (Weeks)", "Currency", "Price Breaks"],
                [column.heading for column in provider_columns],
            )

    def test_display_headings_may_repeat_across_provider_blocks(self):
        headings = display_headings(enriched_parts_columns())
        self.assertEqual(3, headings.count("Provider Name"))
        self.assertEqual(3, headings.count("Price Breaks"))

    def test_returned_layout_is_a_copy(self):
        first = enriched_parts_columns()
        first.pop()
        self.assertNotEqual(len(first), len(enriched_parts_columns()))


if __name__ == "__main__":
    unittest.main()
