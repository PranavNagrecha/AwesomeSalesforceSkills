# Gotchas — Data Loader Batch Window Sizing

Non-obvious Salesforce platform behaviors that ruin loads even when the batch size looks right on paper.

---

## Gotcha 1: Sharing recalculation runs asynchronously AFTER the load reports "complete"

**What happens:** the load job finishes — Bulk API V2 reports `JobComplete`, the row count matches, CSV success file looks clean. But the org is unusable for the next several hours: list views are slow, reports time out, parallel admin operations queue up. The cause is the **asynchronous sharing recalculation** that Salesforce kicked off when 100K Private OWD records landed in an org with role hierarchy. The visible insert is fast; the implicit-share-row recalculation across the role hierarchy is a slow background job that does not show up in the Bulk API job status.

**When it occurs:** any time you load >100K records of a Private OWD SObject in an org with a non-trivial role hierarchy. Worst on Account, Opportunity, Contact (because they own the implicit-share fan-out for child objects too).

**How to avoid:** enable **Defer Sharing Calculations** before the load (Setup → Sharing Settings → Defer Sharing Calculations). Run the load. Re-enable sharing calculations during a controlled window. Communicate the async tail explicitly in the runbook — "load lands at T+1h, sharing recalc completes at T+5h, reports usable at T+5h" — so business stakeholders do not declare success at T+1h.

---

## Gotcha 2: Bulk API V2 parallel mode + row-skewed parent = guaranteed `UNABLE_TO_LOCK_ROW`

**What happens:** a load that runs cleanly in dev (where one Account has 5 children) fails 10–20% of the time in production (where one Account has 10,000 children) because parallel batches each try to lock the same parent Account row to update implicit shares or rollup fields.

**When it occurs:** any object with a parent lookup where one parent has a disproportionate number of children. Common shapes: a single integration-service Account that owns thousands of imported Contacts; a single migration user who owns thousands of legacy records; a single "Unassigned" queue with thousands of Cases.

**How to avoid:** before kicking off the load, run a count query: `SELECT ParentId, COUNT(Id) FROM ChildObject GROUP BY ParentId ORDER BY COUNT(Id) DESC LIMIT 50`. Any parent with >10,000 children is row-skewed. **Switch to Bulk API V2 serial mode** for that load. Do not try to "fix" parallel mode by retrying — the failure is structural, not transient. If the row-skew is on `OwnerId`, distribute ownership across multiple users before the load.

---

## Gotcha 3: Trigger CPU limit hits at batch=200 on objects with rich automation

**What happens:** the Data Loader UI default of 200 sounds safe, but on an Account with 6 record-triggered Flows, 1 trigger handler doing roll-up calculation, and 4 validation rules, a single 200-record batch consumes 50–55 seconds of CPU and either hits `CPU_TIME_LIMIT_EXCEEDED` or completes at 95% governor pressure. One additional record-triggered Flow added in a later release pushes it over the limit, surfacing as a "load that worked last quarter is now failing."

**When it occurs:** complex standard objects (Account, Opportunity, Case) in mature orgs that have accumulated automation over years. The failure is sensitive to the order automation fires in (because each predecessor consumes CPU the next one needs).

**How to avoid:** for one-time historical loads, use a **Custom Metadata trigger bypass** (e.g., `TriggerControl__mdt.Bypass_Account__c`) for the load user, then run a separate post-load enrich job. For recurring loads, lower batch size to 50–100, or split the automation: move expensive recalculations to async (Queueable / Batch Apex) so the synchronous trigger path does cheap-only work.

---

## Gotcha 4: Field history tracking creates 1 history row per tracked field per changed record

**What happens:** mass-updating 1,000,000 Accounts to fix one field value silently writes 1,000,000 `AccountHistory` rows (and more, if multiple tracked fields are touched in the same update). Storage spikes; data storage limits get hit; the Account feed fills with low-value history entries that drown real audit trails. The load itself looks fine — the explosion is in the side-table.

**When it occurs:** any mass-update on an object where field history tracking is enabled on a field that the load is changing. Especially painful on Account, Opportunity, Case (high default tracking) and on objects in regulated industries (Health Cloud, Financial Services Cloud) where compliance-driven tracking is the default.

**How to avoid:** disable field history tracking on the specific fields the load will change for the duration of the load (Setup → Object Manager → Object → Set History Tracking → uncheck the affected field), run the load, re-enable. Alternatively, route the update through a Batch Apex job that explicitly skips history-row creation for the migration user. Do NOT delete `*History` rows after the fact to "clean up" — those rows are immutable in production and their deletion paths are limited.

---

## Gotcha 5: Loading as System Administrator creates wrong sharing implications

**What happens:** the load runs cleanly with the System Administrator's credentials because admin has Modify All Data and skips most validation. The data lands. Two days later, sales reps report they cannot see records they expected to see, because `OwnerId` was not mapped — every record landed owned by the admin, and the role hierarchy / sharing rules are computed against admin's role, not the intended owners. Re-parenting 1M records later triggers the entire sharing recalc again.

**When it occurs:** any load run by an admin user without explicit `OwnerId` mapping in the source CSV. Common shape: "we'll just load it and re-assign later" — the re-assignment turns out to be a multi-hour share-recompute job.

**How to avoid:** always populate `OwnerId` (or `Owner.External_Id__c` via upsert) with the correct intended owner from row 1. Use a dedicated **load user** with explicit permissions for the load — not a personal admin account, not "the migration user from last project." Document the load user's role placement in the hierarchy because it determines the implicit shares the load will create.

---

## Gotcha 6: Bulk API V2 batch size of 10,000 does NOT bypass per-200 trigger CPU envelope

**What happens:** a load engineer reads "Bulk API V2 supports up to 10,000 records per batch" and sets batch size to 10,000 expecting bigger batches = fewer transactions = less CPU pressure. The load fails with `CPU_TIME_LIMIT_EXCEEDED` at the same rate as a 5,000-batch attempt because the platform internally chunks the upload to **200-row server transactions** for trigger evaluation regardless of the upload batch size.

**When it occurs:** anyone optimising for API call count without understanding the internal-chunking behaviour. The 10,000 limit is about **upload payload size**, not about transaction size.

**How to avoid:** treat 200 as the **trigger CPU planning unit** even when you upload in larger batches. The upload batch size mainly affects API call consumption and Bulk job overhead; per-record platform behaviour (triggers, rules, sharing) is paid in 200-row server chunks. Plan triggers as if every 200 records is one synchronous transaction.

---

## Gotcha 7: Parallel `UNABLE_TO_LOCK_ROW` is NOT auto-retried by Bulk API V2 for skew shapes

**What happens:** Bulk API V2 documentation describes automatic retry for transient failures, leading load engineers to assume row-lock errors will eventually retry-succeed. They do not — for **row-skew** shapes (one parent with thousands of children), the retry hits the same lock contention and fails again. The failed records end up in the job's error CSV, requiring a manual second pass.

**When it occurs:** any parallel-mode load against a row-skewed parent. The failure rate is correlated with how many children the skewed parent has and how many parallel workers Salesforce assigns.

**How to avoid:** detect row-skew before the load (see Gotcha 2). Use serial mode for known-skewed shapes. If row-skew was missed and the first attempt produced a failure CSV, **re-run the failure CSV in serial mode** — do not retry it in parallel mode hoping for better luck.

---

## Gotcha 8: Defer Sharing Calculations does not defer EVERYTHING

**What happens:** "Defer Sharing Calculations" is enabled, the load runs, the visible job finishes — but the org is still slow because account-team shares, opportunity-team shares, territory shares, and manual shares were created synchronously despite the defer setting. The defer flag covers **group-membership recalc and sharing-rule recalc**, but not all implicit-share creation paths.

**When it occurs:** loads against Account/Opportunity in orgs with active Account Teams, Opportunity Teams, or Territory Management 2.0. Loads that include explicit `*Share` row inserts (manual shares).

**How to avoid:** read the **Defer Sharing Calculations** documentation carefully (see Official Sources in `well-architected.md`). Plan around what it does NOT cover: account/opportunity/case team shares, territory assignment shares, manual shares. For territory-managed orgs, plan for the territory-assignment runtime as a separate non-deferrable cost.

---

## Gotcha 9: Loading parents in parallel and children in parallel causes parent-lock contention even with External Id

**What happens:** a load engineer uses External Id deferred linkage thinking it side-steps ordering issues, then runs both parent and child uploads in parallel mode at the same time. The child upserts try to look up the parent External Id while the parent upserts are still rewriting the same Account rows; lock contention surfaces as `UNABLE_TO_LOCK_ROW` on the parents themselves.

**When it occurs:** ETL pipelines that try to maximise throughput by running parent and child loads concurrently.

**How to avoid:** External Id deferred linkage solves the **ordering** problem, not the **concurrency** problem. Run **parent upsert first to completion**, then start child upsert. Within each pass, parallel mode is fine if the per-pass shape is not row-skewed; across passes, do not overlap.

---

## Gotcha 10: API call budget burns through faster than batch math suggests

**What happens:** a 5,000,000-record load at batch=200 = 25,000 batches, but the daily API consumption shows 60,000+ calls used. The discrepancy is **job state polling** — Bulk V2 clients poll the job status every few seconds, and each poll is an API call. A 9-hour load polling every 30 seconds is 1,080 polls — adds up across multiple parallel jobs.

**When it occurs:** any sustained high-volume load, especially when the client polls aggressively. Worst when multiple Bulk jobs run concurrently and each is polled independently.

**How to avoid:** check the daily API consumption mid-load via the Setup → Company Information → API Requests Last 24 Hours counter (or via `LimitsResource`). Tune polling intervals down (30 seconds → 2 minutes) for long-running jobs. Coordinate with other automated integrations during the load window — a Marketing Cloud sync that consumes 40K daily calls plus a 60K-call data load can exhaust an Enterprise org's 100K daily quota before noon.
