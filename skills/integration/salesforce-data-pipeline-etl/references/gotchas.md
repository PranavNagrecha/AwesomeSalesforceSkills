# Gotchas — Salesforce Data Pipeline / ETL

## Gotcha 1: CDC retention exceeded

**What happens:** Consumer offline >3 days; events lost.

**When it occurs:** Holiday outage.

**How to avoid:** Trigger re-snapshot on lag threshold.


---

## Gotcha 2: Missing GAP_FILL

**What happens:** Silently lose records.

**When it occurs:** Handler ignores event type.

**How to avoid:** Treat GAP_FILL as re-query trigger.


---

## Gotcha 3: SOQL polling fallback

**What happens:** Eats API allocation.

**When it occurs:** CDC misconfigured.

**How to avoid:** Fix CDC; polling is last resort.

