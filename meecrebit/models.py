from dataclasses import dataclass, asdict
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Transaction:
    id: str
    amount: Decimal
    kind: str
    merchant: str
    category: str
    occurred_on: date
    source: str = "sms"

    @property
    def is_expense(self) -> bool:
        return self.kind == "debit"

    def to_dict(self) -> dict:
        value = asdict(self)
        value["amount"] = str(self.amount)
        value["occurred_on"] = self.occurred_on.isoformat()
        return value

    @classmethod
    def from_dict(cls, value: dict) -> "Transaction":
        return cls(
            id=value["id"],
            amount=Decimal(value["amount"]),
            kind=value["kind"],
            merchant=value["merchant"],
            category=value["category"],
            occurred_on=date.fromisoformat(value["occurred_on"]),
            source=value.get("source", "sms"),
        )


@dataclass(frozen=True)
class Budget:
    month: str
    category: str
    limit: Decimal

    def to_dict(self) -> dict:
        return {"month": self.month, "category": self.category, "limit": str(self.limit)}


@dataclass(frozen=True)
class MonthlyStatement:
    month: str
    income: Decimal
    spending: Decimal
    by_category: dict
    transaction_count: int

