import unittest

from openpyxl import Workbook

from excel_formatter import ENRICHED_PARTS_FREEZE_PANES, format_review_sheet


class ReviewSheetFreezePaneTests(unittest.TestCase):
    def test_review_sheet_freezes_headers_and_first_four_columns(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["Input & Match"] * 5)
        sheet.append(["MFG", "MPN", "Match Status", "Matched", "Description"])
        sheet.append(["Example", "ABC123", "Matched", "Yes", "Example part"])

        format_review_sheet(
            sheet,
            ["MFG", "MPN", "Match Status", "Matched", "Description"],
        )

        self.assertEqual("E3", ENRICHED_PARTS_FREEZE_PANES)
        self.assertEqual("E3", sheet.freeze_panes)


if __name__ == "__main__":
    unittest.main()
