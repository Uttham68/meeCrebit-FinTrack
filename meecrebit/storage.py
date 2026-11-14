"""Small JSON store kept at a caller-selected local path."""

import json
from pathlib import Path
from decimal import Decimal
from typing import Iterable

from .models import Budget, Transaction


class LocalStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> tuple[list[Transaction], list[Budget]]:
        if not self.path.exists():
            return [], []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        transactions = [Transaction.from_dict(item) for item in data.get("transactions", [])]
        budgets = [
            Budget(item["month"], item["category"], Decimal(item["limit"]))
            for item in data.get("budgets", [])
        ]
        return transactions, budgets

    def save(self, transactions: Iterable[Transaction], budgets: Iterable[Budget]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "transactions": [item.to_dict() for item in transactions],
            "budgets": [item.to_dict() for item in budgets],
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
