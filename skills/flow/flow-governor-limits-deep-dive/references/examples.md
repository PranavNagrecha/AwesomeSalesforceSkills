# Examples — Flow Governor Limits Deep Dive

## Example 1: SOQL-in-loop breach

**Context:** Record-triggered Flow on Account, batch size 200. Inside a Loop over Contacts, a Get Records fetches the matching Case.

**Math:** 200 accounts × avg 5 contacts = 1000 iterations. 1 SOQL per iteration = 1000 SOQL. Limit = 100. Breach at iteration 100.

**Fix:** Hoist Get Records outside the loop with an IN-clause over all needed Ids. Single SOQL, map result by key, access inside loop.

---

## Example 2: Shared transaction budget

**Context:** Opportunity save fires: 2 After-Save Flows, 1 Validation Rule, 1 Apex trigger. Each needs its share of the 100-SOQL budget.

**Allocation (200-record batch):**
- Apex trigger: 15 SOQL
- VR: 3 SOQL
- Flow A: 4 SOQL
- Flow B: 4 SOQL
- Total: 26 SOQL

Headroom: 74 SOQL. Safe to add a fifth automation consuming up to ~50 SOQL (with buffer).

---

## Example 3: CPU timeout tuning

**Context:** Flow with 15 Decisions and 5 Assignments inside a Loop over 500 records. Times out at 10,000ms CPU.

**Fix:**
- Pre-compute the Decision branch outside the loop where possible.
- Replace nested Loop with a single Loop + Map lookup.
- Move heavy Formula evaluations out of inner Decisions.

Result: 8500ms → 3200ms.

---

## Example 4: Async offload

**Context:** After-Save flow needs 10 enrichment Get Records per record. At 200 records: 2000 SOQL. Fresh-transaction via Scheduled Path +0 gets fresh 100 SOQL per batch.

**Fix:** Add Scheduled Path with 0-minute delay. Same business logic, but async execution. Trade-off: 1-5 minute delivery lag.

---

## Anti-Pattern: Adding a flow without shared-budget math

Team adds Flow #6 to a busy Account stack. Tests pass in sandbox (no concurrent data). Production fires it alongside 5 other automations; 101 SOQL; silent breach. Fix: shared-budget forecast before deployment.
