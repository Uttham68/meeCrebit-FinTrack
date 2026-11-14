from collections import defaultdict
from decimal import Decimal
from typing import Optional

from .models import Budget, MonthlyStatement, Transaction
from .parser import parse_sms
from .storage import LocalStore


class FinanceTracker:
    """The application service: all processing is local and deterministic."""

    def __init__(self, store: Optional[LocalStore] = None):
        self.store = store
        self.transactions, self.budgets = store.load() if store else ([], [])

    def record_sms(self, message: str, **kwargs) -> Transaction:
        transaction = parse_sms(message, **kwargs)
        if not any(item.id == transaction.id for item in self.transactions):
            self.transactions.append(transaction)
            self._save()
        return transaction

    def set_budget(self, month: str, category: str, limit: Decimal) -> None:
        budget = Budget(month, category, Decimal(limit))
        self.budgets = [item for item in self.budgets if (item.month, item.category) != (month, category)]
        self.budgets.append(budget)
        self._save()

    def statement(self, month: str) -> MonthlyStatement:
        items = [item for item in self.transactions if item.occurred_on.strftime("%Y-%m") == month]
        by_category = defaultdict(Decimal)
        income = sum((item.amount for item in items if item.kind == "credit"), Decimal())
        spending = sum((item.amount for item in items if item.is_expense), Decimal())
        for item in items:
            if item.is_expense:
                by_category[item.category] += item.amount
        return MonthlyStatement(month, income, spending, dict(by_category), len(items))

    def budget_status(self, month: str) -> dict[str, dict[str, Decimal]]:
        statement = self.statement(month)
        spent = statement.by_category
        return {
            budget.category: {
                "limit": budget.limit,
                "spent": spent.get(budget.category, Decimal()),
                "remaining": budget.limit - spent.get(budget.category, Decimal()),
            }
            for budget in self.budgets
            if budget.month == month
        }

    def analytics(self, month: str) -> dict:
        statement = self.statement(month)
        expenses = [
            item for item in self.transactions
            if item.is_expense and item.occurred_on.strftime("%Y-%m") == month
        ]
        largest = max(
            expenses,
            key=lambda item: item.amount,
            default=None,
        )
        return {
            "average_expense": (statement.spending / len(expenses) if expenses else Decimal(0)),
            "top_category": max(statement.by_category, key=statement.by_category.get, default=None),
            "largest_expense": largest.amount if largest else Decimal(0),
        }

    def _save(self) -> None:
        if self.store:
            self.store.save(self.transactions, self.budgets)
