---
name: usage-based-pricing-setup
description: "Usage-based pricing in Revenue Cloud: metered billing, usage records, rating, tiering, consumption schedules. NOT for CPQ flat-rate discounts (use revenue-cloud-cpq-setup). NOT for legacy Salesforce Billing-only implementations (use revenue-cloud-legacy-billing)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
  - Operational Excellence
tags:
  - usage-based-pricing
  - metered-billing
  - consumption-schedule
  - revenue-cloud
  - rating
  - tiering
  - invoicing
triggers:
  - "how do i configure usage based pricing in revenue cloud"
  - "metered billing and consumption schedules salesforce"
  - "tiered usage pricing with overage"
  - "usage record ingestion from product telemetry"
  - "rating engine for consumption pricing"
  - "prepaid vs postpaid usage billing"
inputs:
  - Revenue Cloud edition and usage-based pricing entitlement
  - Product catalog pricing model (tiered, volume, overage, prepaid pool)
  - Telemetry source (product platform, external meter, manual import)
  - Billing cadence and invoice consolidation requirements
outputs:
  - Consumption schedule + price rule configuration
  - Usage record ingestion pipeline spec
  - Rating + invoice generation validation plan
  - Customer-facing usage visibility scaffold
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Usage-Based Pricing Setup

Activate when configuring Revenue Cloud usage-based (consumption / metered) pricing: products billed by API calls, gigabytes, seats-per-day, kWh, or any consumed unit. Distinct from CPQ flat-rate discounting — usage-based pricing calculates charges from post-sale telemetry and runs rating on top of raw usage records.

## Before Starting

- **Confirm Revenue Cloud + usage-based entitlement.** Consumption Schedules, Usage Summary, and rating are part of Revenue Cloud, not base CPQ. License the correct SKU.
- **Identify the telemetry source.** Usage records arrive from: product platform (most common), external metering service (Stripe Metering, Chargebee), data warehouse, or manual CSV. Schema and cadence define the ingestion.
- **Define the rating model.** Tiered (different price per tier), volume (all units at the tier's price), overage (flat to cap, then per-unit), prepaid pool (drawdown) each have distinct configuration and testing needs.

## Core Concepts

### Consumption Schedule

A `ConsumptionSchedule` defines the rating rule: `Type` (Range or Slab), `RatingMethod` (Tier or Volume), and `ConsumptionRate` children with `LowerBound`, `UpperBound`, `Price`, `PricingMethod`. Attached to a `Product2`.

### Usage records

`UsageTransaction` or `UsageRecord` (naming depends on release) carries quantity, timestamp, product, subscription. Rated into `BilledUsage` or an equivalent object on a scheduled cadence.

### Rating and invoicing

Scheduled rating evaluates unrated usage against the Consumption Schedule, writes priced usage records, and feeds the invoice engine. Idempotency matters — re-running rating must not double-charge.

### Prepaid pools

For "buy 1M API calls, drawn down monthly," a prepaid pool tracks balance. Usage decrements the pool; overage triggers a different rate. Uses `SubscriptionUsageEntitlement` patterns depending on release.

## Common Patterns

### Pattern: Tiered pricing with monthly invoice

Product has a Consumption Schedule with three tiers. Usage ingested daily from product telemetry via REST API. Nightly rating job converts unrated usage to priced usage. Month-end invoice run aggregates, posts, and emails.

### Pattern: Prepaid pool with overage

Customer purchases a 10M-call annual bundle. Usage drains the pool across the year. At 100% consumption, overage rate kicks in. End of term: any unused balance is forfeited or carries forward per contract.

### Pattern: Real-time usage visibility for customers

Customer portal LWC shows current month usage, remaining pool, and projected overage. Data comes from the aggregated `UsageSummary` object, not raw `UsageRecord` — same reason as rebate snapshots: performance and stability.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Flat per-unit pricing | Simple Consumption Schedule, Range type | Simplest, well-supported |
| Discount tiers with cumulative volume | Volume rating method | All units priced at top tier |
| Commit + overage | Prepaid pool with overage rate | Matches common SaaS contracts |
| Real-time customer dashboard | UsageSummary rollup, not raw records | Performance |
| Usage from external meter | Integration via Bulk API or Platform Events | Decouples rating from source |

## Recommended Workflow

1. Confirm Revenue Cloud license and usage-based entitlement; ensure Consumption Schedule objects are exposed.
2. Model the product catalog: identify each metered product, its rating method, and pricing tiers.
3. Build Consumption Schedules and attach to Product2 records; include effective-dated schedules for future price changes.
4. Design the usage ingestion pipeline: schema, volume, cadence, idempotency, retry policy.
5. Validate end-to-end with sample usage: ingest → rate → invoice → verify amounts against contract math.
6. Build `UsageSummary` rollups; expose in customer portal with real-time (or near-real-time) totals.
7. Build reconciliation and finance controls: invoice approval, GL mapping, dispute handling.

## Review Checklist

- [ ] Consumption Schedules validated against contract math
- [ ] Usage ingestion idempotent across retries
- [ ] Rating job tested with month-end volume
- [ ] Overage and prepaid pool logic tested with edge cases
- [ ] Customer-facing dashboard shows accurate usage vs entitlement
- [ ] Finance approval and GL mapping in place
- [ ] Dispute/credit process documented

## Salesforce-Specific Gotchas

1. **Re-rating is easy to fire twice.** Rating jobs that do not check `IsRated` / `Rated` flags will create duplicate priced records on retry; design idempotency explicitly.
2. **Consumption Schedule effective dating is strict.** A mid-month price change requires a new schedule version with proper effective dates; retroactive changes re-rate the whole period.
3. **High-volume usage can overrun storage.** Millions of `UsageRecord` rows balloon Salesforce storage; plan for archival (big objects or external warehouse) before go-live.

## Output Artifacts

| Artifact | Description |
|---|---|
| Consumption schedule catalog | Per-product rating rules and effective dates |
| Ingestion pipeline spec | Source, schema, cadence, idempotency controls |
| Rating + invoice runbook | Monthly cycle procedure |
| Customer visibility component | LWC reading from UsageSummary |

## Related Skills

- `admin/revenue-cloud-cpq-setup` — upstream deal structure
- `integration/integration-pattern-selection` — usage ingestion
- `data/big-objects-and-archival` — long-term usage archive
