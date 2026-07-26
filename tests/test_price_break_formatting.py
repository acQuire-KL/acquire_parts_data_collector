import unittest

from main import all_price_breaks_summary, price_break_summary


class PriceBreakFormattingTests(unittest.TestCase):
    def test_price_breaks_use_five_decimals_and_two_space_separator(self):
        offer = {
            "standard_price_breaks": [
                {"break_quantity": 1, "unit_price": 0.43},
                {"break_quantity": 3000, "unit_price": 12.2875},
                {"break_quantity": 100, "unit_price": 123.3525},
            ]
        }
        lines = price_break_summary(offer).splitlines()
        self.assertEqual("    1    0.43000", lines[0])
        self.assertEqual("  100  123.35250", lines[1])
        self.assertEqual("3,000   12.28750", lines[2])
        self.assertNotIn("€", "\n".join(lines))
        self.assertNotIn("@", "\n".join(lines))

    def test_all_offers_share_the_widest_quantity_and_price_columns(self):
        profile = {
            "offers": [
                {
                    "pack_format": "Cut Tape",
                    "standard_price_breaks": [{"break_quantity": 1, "unit_price": 0.1}],
                },
                {
                    "pack_format": "Reel",
                    "standard_price_breaks": [{"break_quantity": 10000, "unit_price": 1234.5}],
                },
            ]
        }
        summary = all_price_breaks_summary(profile)
        self.assertIn("     1      0.10000", summary)
        self.assertIn("10,000  1,234.50000", summary)


if __name__ == "__main__":
    unittest.main()
