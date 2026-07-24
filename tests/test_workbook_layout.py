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
            section_order,
            [
                "Status",
                "Identity",
                "Engineering",
                "Commercial",
                "Traceability",
                "Documentation",
                "Compliance",
            ],
        )

    def test_headings_are_unique(self):
        headings = [heading for _, heading, _, _ in enriched_parts_columns()]
        self.assertEqual(len(headings), len(set(headings)))

    def test_commercial_precedes_documentation_and_compliance(self):
        columns = enriched_parts_columns()
        groups = [section for section, *_ in columns]
        self.assertLess(groups.index("Commercial"), groups.index("Documentation"))
        self.assertLess(groups.index("Commercial"), groups.index("Compliance"))

    def test_returned_layout_is_a_copy(self):
        first = enriched_parts_columns()
        first.pop()
        self.assertNotEqual(len(first), len(enriched_parts_columns()))


if __name__ == "__main__":
    unittest.main()
