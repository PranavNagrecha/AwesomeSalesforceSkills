# Examples — Data Loader Batch Window Sizing

Three realistic load-sizing decisions with the failure modes that drove the choice.

---

## Example 1: Account 5M load with row-skew on a single Owner

### Context

A B2B services org migrating 5,000,000 Accounts from a legacy CRM. The org is **Private OWD** for Account, has a 6-level role hierarchy, three sharing rules based on `Industry`, two record-triggered Flows on Account `before insert` (territory tagging, region assignment), and a custom AccountTrigger handler running about 250ms of per-record validation work. About **40,000 of the 5M accounts** have `OwnerId` pointing at a single migration-service user (`migration@acme.com`) — a row-skew shape inherited from how the legacy system staged data.

### Problem

The first attempt used **Bulk API V2 parallel mode at batch=2,000**. Within the first 30 minutes:

- About 18% of records failed with `UNABLE_TO_LOCK_ROW`. The lock contention was on the `User` record for `migration@acme.com` — every parallel batch tried to update implicit-share rows for that user simultaneously.
- Two batches hit `CPU_TIME_LIMIT_EXCEEDED` because the Flow + trigger combination on a 2,000-record batch exceeded the 60-second synchronous CPU window.
- The job appeared to finish in 4 hours, but the **async sharing recalculation tail ran for another 11 hours**, during which list views on Account were unusable for the sales team.

### Solution

Replanned the load with serial mode, smaller batches, deferred sharing, and a trigger bypass.

```yaml
# Sizing decision
object: Account
record_count: 5_000_000
batch_size: 200
mode: Bulk API V2 serial
trigger_bypass: TriggerControl__mdt → Bypass_Account__c = true (for migration user only)
defer_sharing_calculations: true            # Setup → Sharing Settings, ON for the window
load_window: Saturday 22:00 – Sunday 14:00 UTC (16-hour maintenance window)
load_user: dedicated migration user, NOT system admin
external_id: Legacy_Account_Id__c (Unique, Case-Insensitive) — upsert, not insert
post_load_jobs:
  - re-enable triggers (clear CMDT bypass)
  - Batch Apex AccountTerritoryEnrichBatch (500 scope) to backfill territory assignment
  - Batch Apex AccountIndustrySharingBackfillBatch to recompute the 3 sharing-rule shares
  - re-enable sharing calculations (deferred → on)
estimated_runtime: 9–12 hours
expected_api_calls: 25_000 batches × ~2 calls = ~50_000 daily quota consumption
```

### Why it works

- **Serial mode** eliminates the row-skew lock contention on the migration user — only one batch runs at a time, so there is no parallel claim on the same implicit-share rows.
- **Batch=200** keeps the per-batch CPU well under the 60s sync limit even with all triggers on; with the bypass, it leaves a comfortable headroom for upsert overhead.
- **Defer Sharing Calculations** + **post-load sharing backfill** decouples the 11-hour async tail from the load itself — the tail now runs as a controllable Batch Apex job we can monitor and pause, not as an opaque platform recalc.
- **External Id upsert** makes the load re-runnable. If something fails at hour 7, restarting from the failure point does not create duplicates.

---

## Example 2: Opportunity load with Territory Management 2.0

### Context

A 1,200,000-row Opportunity load for a sales-org consolidation. The org has **Territory Management 2.0** active, with assignment rules driven by `Account.BillingCountry` and `Opportunity.Amount__c`. Each Opportunity insert fires the territory assignment engine, which evaluates rules and creates `OpportunityShare` rows for the assigned territories.

### Problem

The first attempt used Bulk V2 parallel at batch=500. Symptoms:

- Territory assignment ran on every record, but parallel batches hit lock contention on the **`__Territory2`** assignment rows when multiple Opportunities mapped to the same territory landed in the same wall-clock second. Result: ~6% `UNABLE_TO_LOCK_ROW` errors clustered around high-volume territories (US-West, EMEA-DACH).
- Even successful records had delayed territory assignment because the engine queued recomputation; reports showed Opportunities without territories for 30+ minutes after the load finished.

### Solution

```yaml
# Sizing decision
object: Opportunity
record_count: 1_200_000
batch_size: 200
mode: Bulk API V2 serial          # mandatory under Territory Management 2.0
trigger_bypass: NO — territory assignment must run live (it IS the work)
parent_load_first: true           # Account upsert must complete before Opportunity
external_id: Legacy_Opp_Id__c (Unique) — upsert
load_window: Sunday 02:00–14:00 UTC
estimated_runtime: 7–9 hours
note: |
  Do NOT bypass territory assignment via CMDT — territory rows ARE the
  point of the load. Run the load slow and serial; let the engine assign
  per-record.
```

### Why it works

Territory Management 2.0 is one of the canonical "must run serial" cases. Parallel mode is structurally unsafe because territory rule evaluation creates contention on the same `Territory2Model` and `UserTerritory2Association` rows that other batches need to read. Serial mode pays a wall-clock cost (single-batch-at-a-time) but eliminates the entire failure class.

The same logic applies to **Account Teams**, **Opportunity Teams**, **Case Teams**, and **role-hierarchy implicit shares** for Private OWD objects: any feature that creates implicit share rows synchronously during DML is a serial-mode object.

---

## Example 3: Case mass-update with field history tracking

### Context

A Service Cloud org needs to mass-update 800,000 Cases to set a new `Resolution_Code__c` value driven by an offline analysis. The Case object has **field history tracking enabled on 12 fields**, including `Resolution_Code__c`. The org is Public R/W on Case, no sharing rules, three Case triggers but only one fires on `before update` (a status synchronisation rule).

### Problem

The first dry-run at batch=2,000 parallel completed the **DML** in 22 minutes — looks great. But:

- Field history tracking generated **800,000 `CaseHistory` rows** for the single field change. Storage on the org jumped by ~140MB, and the Case feed became cluttered with 800K "Resolution Code changed" entries.
- A second pass two weeks later (correcting a mapping error) generated another 800,000 rows. Storage now had 1.6M low-value history rows competing with real audit trails.

### Solution

```yaml
# Sizing decision
object: Case
record_count: 800_000
batch_size: 2_000
mode: Bulk API V2 parallel        # Public R/W, no sharing recalc, no row-skew on Case
trigger_bypass: optional — the one before-update trigger is cheap; leave it on
field_history_tracking: TEMPORARILY DISABLE for Resolution_Code__c during the load
feed_tracking: leave on — Case feed is an audit channel
external_id: existing Salesforce Id (upsert by Id, not external)
load_window: business hours OK — Case is high-volume and forgiving
estimated_runtime: 25–40 minutes
post_load_steps:
  - re-enable field history tracking on Resolution_Code__c
  - DO NOT backfill history rows for the load itself (that is the point — it's a bulk admin correction, not a business-meaningful change)
```

### Why it works

The right lever here was **field history tracking**, not batch size. Disabling history tracking for the field being mass-updated removed the 800K history-row write amplification entirely; storage stayed flat; the Case feed stayed clean.

Batch size at 2,000 is fine for Case in this org because: Public R/W (no sharing recalc), no row-skew on Case (no skewed parent), only one cheap before-update trigger. Going smaller would just multiply API calls without buying anything.

---

## Anti-Pattern: "We hit a CPU error, let's increase the batch size"

### What practitioners do

A 200-record batch fails with `CPU_TIME_LIMIT_EXCEEDED`. The load engineer reasons "we are running too many batches; let's reduce the batch count by raising batch size to 1,000" and re-runs.

### What goes wrong

CPU time is **per server transaction**, not per batch upload. Raising the batch size from 200 to 1,000 multiplies per-batch CPU consumption by 5x. The job hits the CPU limit on every batch, not just some of them. The fix is the opposite direction: lower batch size, or bypass the trigger work that is consuming the CPU budget.

### Correct approach

When CPU errors appear:
1. Drop batch size (200 → 100 → 50) and retry.
2. If errors persist, profile the trigger / record-triggered Flow with debug logs to find the per-record CPU consumer.
3. For one-time loads, bypass the expensive automation via CMDT and run a separate post-load enrich job at a sane batch size (Batch Apex with `scope=200`).
4. Only raise batch size when CPU headroom is documented to be ample (typically simple custom-object loads with no triggers).
