# meeCrebit-FinTrack

meeCrebit is a dependency-free, offline-first finance core. Bank SMS messages are
parsed and categorized locally; no network client, telemetry, or cloud storage is
used. The local JSON store is selected by the host application and can remain on
the device.

## Use

```python
from decimal import Decimal
from meecrebit import FinanceTracker
from meecrebit.storage import LocalStore

tracker = FinanceTracker(LocalStore("meecrebit-data.json"))
tracker.record_sms("Rs. 850 debited at Swiggy on 14/11/2026")
tracker.set_budget("2026-11", "food", Decimal("5000"))
print(tracker.statement("2026-11"))
print(tracker.budget_status("2026-11"))
print(tracker.analytics("2026-11"))
```

The SMS text is used only to create a transaction; it is not stored. Duplicate
messages are ignored by a deterministic local identifier. Run tests with:

```bash
python -m unittest discover -s tests
```
