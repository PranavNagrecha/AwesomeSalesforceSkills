# Examples — Dynamic Sharing Recalculation

## Example 1: Migrating 10M Opportunity records into a Private org

**Context:** ETL inserts nightly for a week.

**Problem:** Each night recalc starts and does not finish before business hours; sales users missing records.

**Solution:**

Turn on Defer Sharing Calculations before the window, ingest, turn off after the last load. Monitor Sharing Recalculation queue; only reopen reports once empty.

**Why it works:** Avoids repeated partial recalc cycles; one clean rebuild at the end.


---

## Example 2: Role reorg 1200 users

**Context:** New regional structure.

**Problem:** Recalc runs 6+ hours and hits peak load.

**Solution:**

Schedule the role transfer for Saturday 02:00; defer sharing on affected objects first; bulk-move users with the Role Hierarchy API; re-enable sharing last.

**Why it works:** Role hierarchy changes cascade into every role-shared object; deferring compresses the rebuild.

