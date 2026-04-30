# Examples — Mass Transfer Ownership

## Example 1: Sales rep terminated — same-day reassignment

**Context:** Rep "Jamie" leaves the company at 5pm. Manager needs all open Accounts, Opportunities, Cases, and custom Quotes assigned to her by 6pm so deactivation can complete.

**Problem:** Jamie owns 1,200 Accounts, 380 Opportunities, 47 open Cases, and 110 Quote__c records. Mass Transfer Records won't touch the custom object.

**Solution:**

```text
1. Setup → Mass Transfer Records → Transfer Accounts
   From: Jamie     To: Manager
   Tick: Transfer open opportunities not owned by source user
         Transfer cases
   (Children cascade in-tool; one click.)

2. Data Loader → Update on Quote__c
   Query: SELECT Id FROM Quote__c WHERE OwnerId = '005...JamieId'
   Map: Id, OwnerId(=Manager Id) — single column overwrite
   Settings: Continue on error; capture success.csv as audit

3. Setup → Users → Jamie → Deactivate
```

**Why it works:** Built-in cascade handles standard objects in one pass; Data Loader covers the custom-object gap. The success.csv from step 2 is the rollback artifact.

---

## Example 2: Territory realignment — 30 → 18 territories

**Context:** Q4 territory cut. 18 new owners, 30 old owners, 47k Accounts and 110k Opportunities to remap.

**Problem:** Many-to-many mapping; Mass Transfer doesn't support a CSV.

**Solution:**

```text
1. Build mapping CSV: OldOwnerId, NewOwnerId  (30 rows)

2. Pre-cut: request Defer Sharing Calculations from Salesforce Support
   (110k OwnerId changes will trigger 100k+ sharing recalc rows)

3. Apex Anonymous (or scripted SOQL → Excel join → Data Loader):
   Map record Id → NewOwnerId per object
   Update via Data Loader with batch size 200 (avoids row-lock on
   parallel sharing recalc)

4. Maintenance window: re-enable sharing recalc, monitor
   Setup → Background Jobs until "Sharing Rule Recalculation" empties.

5. Validate: SELECT COUNT() FROM Account WHERE OwnerId IN (oldOwners) → 0
```

**Why it works:** Deferred recalc decouples the mass write from the long sharing rebuild. Batch size 200 plus Data Loader's serial mode (not parallel) avoids `UNABLE_TO_LOCK_ROW` collisions.

---

## Anti-Pattern: running a 250k-record Data Loader update during business hours with parallel mode on

**What practitioners do:** Open Data Loader, accept defaults, point at a 250k-row CSV, run.

**What goes wrong:** Parallel mode launches multiple workers updating the same parent records (or share table rows). `UNABLE_TO_LOCK_ROW` failures pepper the error log; sharing recalc runs concurrently with active reps' work and locks reads. Reps see intermittent "you don't have access to this record" for an hour.

**Correct approach:** Switch to serial mode, batch size 200, and request Defer Sharing Calculations beforehand for any volume above ~100k.
