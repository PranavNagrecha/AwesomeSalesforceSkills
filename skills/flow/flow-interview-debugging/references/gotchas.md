# Gotchas — Flow Interview Debugging

## Gotcha 1: Fault on 'no results'

**What happens:** Flow errors when Get returns 0.

**When it occurs:** Fault assumed on empty.

**How to avoid:** 0 rows is not a fault; use Decision.


---

## Gotcha 2: Email to owner only

**What happens:** No one notices in prod.

**When it occurs:** Default config.

**How to avoid:** Set shared alias in Process Automation Settings.


---

## Gotcha 3: Async not in Debug

**What happens:** Only sync path works in panel.

**When it occurs:** Scheduled path testing.

**How to avoid:** Test async in sandbox with real async execution.

