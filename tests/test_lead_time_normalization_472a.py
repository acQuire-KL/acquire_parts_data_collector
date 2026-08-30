import unittest
from datetime import date

from lead_time_normalization import lead_time_display, normalise_lead_time


class LeadTimeNormalisation472aTests(unittest.TestCase):
    def test_days_round_up_to_whole_weeks(self):
        self.assertEqual("10 weeks", lead_time_display("67 Days"))
        self.assertEqual("1 week", lead_time_display("1 Day"))

    def test_fractional_weeks_round_up(self):
        self.assertEqual("10 weeks", lead_time_display(9.1))
        self.assertEqual("10 weeks", lead_time_display("9.57143"))

    def test_zero_does_not_imply_immediate_availability(self):
        self.assertEqual("Request Delivery Quote", lead_time_display("0 Days"))
        self.assertEqual("Request Delivery Quote", lead_time_display(0))

    def test_request_quote_is_preserved(self):
        self.assertEqual("Request Delivery Quote", lead_time_display("Request Delivery Quote"))

    def test_calendar_week_is_not_interpreted_as_duration(self):
        result = normalise_lead_time("Week 45", today=date(2026, 8, 28))
        self.assertEqual(10, result.weeks)
        self.assertEqual("calendar_week", result.interpretation)
        self.assertIn("delivery Week 45", result.display)
        self.assertIn("02 Nov 2026", result.display)

    def test_past_calendar_week_rolls_to_next_year(self):
        result = normalise_lead_time("Week 1", today=date(2026, 8, 28))
        self.assertGreater(result.weeks, 10)
        self.assertIn("2027", result.display)


if __name__ == "__main__":
    unittest.main()
