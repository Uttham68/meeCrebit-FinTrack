"""Parsing for common bank SMS formats. The raw message is never persisted."""

import hashlib
import re
from datetime import date
from decimal import Decimal
from typing import Optional

from .models import Transaction

_AMOUNT = re.compile(r"(?:rs\.?|inr|₹)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", re.I)
_DATE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b")
_DEBIT_WORDS = ("debited", "spent", "purchase", "withdrawn", "paid", "debit")
_CREDIT_WORDS = ("credited", "received", "deposit", "salary", "credit")


def categorize(merchant: str) -> str:
    text = merchant.lower()
    categories = {
        "groceries": ("grocery", "supermarket", "mart", "reliance fresh"),
        "transport": ("uber", "ola", "metro", "fuel", "petrol", "diesel"),
        "food": ("restaurant", "cafe", "swiggy", "zomato", "food"),
        "shopping": ("amazon", "flipkart", "mall", "shopping"),
        "bills": ("electricity", "utility", "recharge", "airtel", "vodafone"),
        "housing": ("rent", "landlord"),
    }
    return next((name for name, words in categories.items() if any(word in text for word in words)), "other")


def parse_sms(message: str, *, received_on: Optional[date] = None) -> Transaction:
    """Convert one bank SMS into a transaction without sending it anywhere."""
    if not isinstance(message, str) or not message.strip():
        raise ValueError("SMS message must be a non-empty string")
    match = _AMOUNT.search(message)
    if not match:
        raise ValueError("SMS does not contain a supported amount")
    lower = message.lower()
    debit = any(word in lower for word in _DEBIT_WORDS)
    credit = any(word in lower for word in _CREDIT_WORDS)
    if debit == credit:
        raise ValueError("SMS does not clearly identify a debit or credit")

    date_match = _DATE.search(message)
    occurred_on = received_on or date.today()
    if date_match:
        year = int(date_match.group(3))
        occurred_on = date(year + 2000 if year < 100 else year, int(date_match.group(2)), int(date_match.group(1)))
    merchant_match = re.search(
        r"(?i)\b(?:at|from|to|via)\s+([a-z][a-z0-9 &.'-]{1,60}?)(?=\s+\bon\b|\s+\b(?:for|ref)\b|[,.]|$)",
        message[match.end():],
    )
    if merchant_match:
        merchant = merchant_match.group(1).strip(" -:,.")
    else:
        remainder = message[:match.start()].strip(" -:") or "Bank account"
        merchant = re.sub(r"(?i)\b(?:debited|credited|spent|withdrawn|purchase|received|from|via|at|on)\b", " ", remainder)
        merchant = re.sub(r"\s+", " ", merchant).strip(" -:,.")
    merchant = merchant or "Bank account"
    kind = "debit" if debit else "credit"
    digest = hashlib.sha256(f"{message}|{occurred_on.isoformat()}".encode()).hexdigest()[:16]
    return Transaction(digest, Decimal(match.group(1).replace(",", "")), kind, merchant, categorize(merchant), occurred_on)
