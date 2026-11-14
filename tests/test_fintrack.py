import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from meecrebit import FinanceTracker
from meecrebit.storage import LocalStore


class FinanceTrackerTests(unittest.TestCase):
    def test_sms_is_categorized_and_duplicate_is_ignored(self):
        tracker = FinanceTracker()
        message = "HDFC Bank: Rs. 1,250 debited at Swiggy on 14/11/2026"
        first = tracker.record_sms(message, received_on=date(2026, 11, 14))
        tracker.record_sms(message, received_on=date(2026, 11, 14))
        self.assertEqual(first.category, "food")
        self.assertEqual(len(tracker.transactions), 1)

    def test_statement_budget_and_analytics(self):
        tracker = FinanceTracker()
        tracker.record_sms("Rs 100 debited at Amazon on 01/11/2026")
        tracker.record_sms("Rs 500 credited as salary on 02/11/2026")
        tracker.set_budget("2026-11", "shopping", Decimal("150"))
        statement = tracker.statement("2026-11")
        self.assertEqual(statement.income, Decimal("500"))
        self.assertEqual(statement.spending, Decimal("100"))
        self.assertEqual(tracker.budget_status("2026-11")["shopping"]["remaining"], Decimal("50"))
        self.assertEqual(tracker.analytics("2026-11")["top_category"], "shopping")

    def test_store_round_trip_is_local_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            tracker = FinanceTracker(LocalStore(path))
            tracker.record_sms("Rs 25 debited at Cafe on 03/11/2026")
            tracker.set_budget("2026-11", "food", Decimal("50"))
            restored = FinanceTracker(LocalStore(path))
            self.assertEqual(restored.transactions[0].amount, Decimal("25"))
            self.assertEqual(restored.budget_status("2026-11")["food"]["remaining"], Decimal("25"))
            self.assertEqual(path.read_text(encoding="utf-8").count("Cafe"), 1)


if __name__ == "__main__":
    unittest.main()
