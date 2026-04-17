# Gotchas — Dynamic Sharing Recalculation

## Gotcha 1: Defer never requested

**What happens:** Support takes weeks to enable; deadline missed.

**When it occurs:** First large migration.

**How to avoid:** File the request at project kick-off, not the week before go-live.


---

## Gotcha 2: Re-enable forgotten

**What happens:** Sharing stays deferred, new records have no access.

**When it occurs:** Post-load cleanup.

**How to avoid:** Include re-enable step in runbook and confirm queue empty before closing.


---

## Gotcha 3: Apex Managed Sharing inserts still happen

**What happens:** Defer flag does not block your __Share DML; inconsistency.

**When it occurs:** Custom Apex runs during the load.

**How to avoid:** Disable relevant triggers in addition to deferring platform recalc.

