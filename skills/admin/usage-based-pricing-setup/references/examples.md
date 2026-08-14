# Examples — Usage-Based Pricing Setup

## Example 1: Mapping a commercial term onto the usage data model

**Context:** A contract reads: *"Includes 1,000,000 API calls per month. Unused calls roll over for one month. Calls beyond the entitlement are billed at $0.002 each. Billed monthly in arrears."*

**Problem:** That is four separate behaviours — a grant, a rollover rule, an overage rate, and a billing cadence — and teams routinely try to model all four as tiers on one pricing record. The behaviours that have nowhere to live then get implemented in custom Apex, which duplicates platform function and diverges from it at the first release.

**Solution:** Decompose the clause onto the objects that own each behaviour before configuring anything.

| Contract clause | Object that owns it | Documented purpose |
|---|---|---|
| "API calls" as a metered thing | `UsageResource` | "Represents an entitlement granted to a user or party by a provider, such as data storage, computing power, bandwidth, or any other product or service" |
| counted in calls, not bytes | `UnitOfMeasure` / `UnitOfMeasureClass` | "Defines the units and systems of units used to account for quantities of a usage resource" |
| "Includes 1,000,000 per month" | `UsageEntitlementBucket` → `UsageEntitlementEntry` | "Represents the usage entitlement details, such as the usage consumption, rollovers, and details of expired units for each tenure" |
| granted with the purchased product | `TransactionUsageEntitlement` | "Represents the details of each usage entitlement that's granted with the purchased sellable product" |
| "Unused calls roll over for one month" | `UsageGrantRolloverPolicy` | "Represents a policy about the rollover of a usage grant" |
| "beyond the entitlement" | `UsageOveragePolicy` | "Represents the set of rules that determine the management of usage resource's units consumed beyond the granted limit" |
| "at $0.002 each" | `RateCard` → `RateCardEntry` | "Rule determining the charge rate for using a product's resource" |
| "billed monthly in arrears" | `UsageResourceBillingPolicy` + `RatingFrequencyPolicy` | "how usage is accumulated before rating a usage resource"; "Policy defining rating trigger frequency" |

**Why it works:** Every clause has exactly one owner, and the owner is a configuration record rather than code. Anything left without an owner after this exercise is either a term the platform does not model — which is a scoping decision to escalate, not a coding task to absorb — or a sign the clause was ambiguous and needs the commercial team, not the build team.

---

## Example 2: The ingestion payload and the diagnostic query chain

**Context:** The product platform emits per-tenant API-call counts every 15 minutes. The pipeline must land them as raw consumption and must be safe to replay after a partial failure.

**Problem:** The integration writes to exactly one object — `TransactionJournal`, "consumption details of a usage resource that are recorded for creating usage summaries". Everything downstream is produced by the platform. Teams that write to `UsageSummary` directly, or invent a `UsageRecord` object, get an `INVALID_TYPE` failure at best and a double-counted invoice at worst.

**Solution:** An **upsert keyed on an external id**, so a replayed window updates the existing row rather than adding a second one.

Two things to settle before writing the payload, and this package deliberately does not guess either:

1. **Which API.** A Bulk API 2.0 ingest job is the right shape for high-volume, fire-and-forget windows — but its ingest jobs take **CSV**, not JSON, so the column header row is where the external-id field name goes. If you want a JSON body, that is the composite sObject Collections upsert (`PATCH /composite/sobjects/TransactionJournal/<ExternalIdField>`), which is capped far lower per call. Pick one; do not mix the two payload shapes.
2. **Which fields.** Add a custom external-id field to `TransactionJournal` yourself (e.g. `External_Meter_Id__c`) and read the object's own field list in Object Manager for the quantity, timestamp, resource and unit-of-measure fields. Their API names are not asserted here — see the "not verified" note in `well-architected.md`.

The external id is the idempotency key: `tenant | resource | window-start`, e.g. `tenant-4471|api_calls|2026-08-14T09:00:00Z`. Replaying the 09:00 window upserts the same row instead of adding a second one — which is the only defence against double billing, because nothing downstream can distinguish a genuine second batch of usage from a replayed one.

The triage query chain, for when an invoice looks wrong. **The object names below are verified against the Usage Management standard-object list; the field names are illustrative placeholders — substitute the real ones from Object Manager before running these.**

```sql
-- 1. Did the raw usage land at all?
SELECT Id, Quantity, TransactionDateTime
FROM TransactionJournal
WHERE External_Meter_Id__c LIKE 'tenant-4471|api_calls|2026-08-14%'
ORDER BY TransactionDateTime

-- 2. Did it aggregate?
SELECT Id, StartDate, EndDate, Quantity
FROM UsageSummary
WHERE UsageEntitlementBucketId = :bucketId
  AND StartDate >= 2026-08-01

-- 3. Did rating produce a billable line?
SELECT Id, Amount, Quantity
FROM UsageBillingPeriodItem
WHERE UsageEntitlementBucketId = :bucketId
```

**Why it works:** Each step isolates one stage of the documented chain — `TransactionJournal` → `UsageSummary` ("Represents the aggregation of the entries in the transaction journal for a usage entitlement for a specified period") → `UsageRatableSummary` ("Represents the aggregation of the usage summaries that are used to calculate the rate at which the overages are charged") → `UsageBillingPeriodItem` ("Represents the calculated overages for the usage entitlement and the amount that's charged for these overages"). The first query that returns nothing tells you which stage failed, in one pass, instead of debugging the rate card for an hour when the real problem was that ingestion never ran.

For the rating stage itself, the Rate Management business API's **Rating Waterfall** resource returns "the persisted rating waterfall that stores the process logs" and "provides insights into the internal rating process" — use it before reverse-engineering the arithmetic by hand.

---

## Anti-Pattern: Custom Apex that reads raw usage and computes charges

**What practitioners do:** Write a scheduled Batch class that queries `TransactionJournal`, applies tier arithmetic in Apex, and writes charge records to a custom object — usually because the platform rating job "didn't produce anything" during the first week of the build.

**What goes wrong:** Three failures compound. The custom job has no idempotency guarantee, so a retried batch double-charges. It bypasses the policy objects, so contractual rollover and commitment terms that *are* configured are silently ignored — the configuration and the behaviour now disagree, and only the configuration is visible to the admin. And it will not survive a platform upgrade to the rating engine, because it re-implements the thing being upgraded.

**Correct approach:** Land raw usage in `TransactionJournal` and let the platform rate it. If rating produced nothing, that is a configuration defect to diagnose through the four-step chain above, not a signal to build a parallel engine. Reserve Apex for the genuinely custom edges — normalising a vendor's telemetry format on the way in, or presenting aggregated figures to a customer portal from `UsageSummary` rather than from raw journal rows.
