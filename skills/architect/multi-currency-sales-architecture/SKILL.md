---
name: multi-currency-sales-architecture
description: "Use when designing or reviewing multi-currency behavior in Sales Cloud: advanced currency management (ACM), dated exchange rates, converted amount field behavior, roll-up summary currency handling, and reporting currency implications. Triggers: 'multi-currency reporting wrong amounts', 'dated exchange rates architecture', 'ACM converted amount fields'. NOT for initial multi-currency enablement or basic currency admin setup."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Operational Excellence
triggers:
  - "converted amounts on opportunities are showing the wrong values after exchange rate changes"
  - "should we enable advanced currency management or stick with standard multi-currency"
  - "roll-up summary fields are not reflecting the correct currency conversion on parent records"
  - "reports show different converted amounts depending on who runs them"
tags:
  - multi-currency-sales-architecture
  - advanced-currency-management
  - dated-exchange-rates
  - currency-conversion
  - sales-cloud
  - reporting-currency
inputs:
  - "whether advanced currency management (ACM) is already enabled or under consideration"
  - "which objects carry currency fields (Opportunity, Quote, custom objects)"
  - "how exchange rates are maintained — manual entry, integration, or third-party feed"
  - "reporting requirements around historical vs. current conversion rates"
outputs:
  - "architecture decision record for standard multi-currency vs. ACM"
  - "currency conversion behavior matrix for Amount, ConvertedAmount, and roll-up summary fields"
  - "reporting guidance for currency display rules and running-user implications"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Multi-Currency Sales Architecture

Use this skill when an org already has multi-currency enabled and needs to make architectural decisions about advanced currency management, dated exchange rates, reporting currency behavior, or converted amount field semantics. The highest-value move is usually to understand the irreversible nature of ACM enablement and to map every currency field to its conversion rule before building reports or roll-ups.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is multi-currency already enabled? Is advanced currency management (ACM) already enabled? ACM cannot be disabled once turned on.
- Which objects carry currency fields — standard (Opportunity, OpportunityLineItem, Quote) and custom? Each has different conversion behavior.
- How are exchange rates maintained today — manual updates in Setup, nightly integration from a treasury system, or a third-party AppExchange package?

---

## Core Concepts

Three concepts govern how currency values behave in a multi-currency Sales Cloud org: the CurrencyType object model, the difference between standard and dated exchange rates, and how converted amount fields derive their values.

### CurrencyType and DatedConversionRate Objects

Salesforce stores exchange rates in the `CurrencyType` sObject. Each active currency has a single conversion rate relative to the corporate currency. When advanced currency management is enabled, a second object — `DatedConversionRate` — stores time-ranged exchange rates. Each row has a `StartDate` and an `IsoCode`; the platform uses the rate whose date range covers the record's `CloseDate` (for Opportunities) or the relevant date field for other objects. The `CurrencyType` rate still exists and serves as the fallback for objects that do not support dated rates.

### Standard Multi-Currency vs. Advanced Currency Management

Standard multi-currency uses a single static rate per currency stored in `CurrencyType`. Every converted amount field recalculates whenever an admin changes that rate — retroactively affecting all historical records. Advanced currency management (ACM) introduces dated exchange rates so that an Opportunity closed on 2025-03-15 uses the rate that was effective on that date, not today's rate. This is critical for revenue recognition and financial reconciliation. However, ACM is irreversible: once enabled, it cannot be turned off. ACM also does not apply to all objects — custom objects and some standard objects still fall back to the static `CurrencyType` rate unless they explicitly support dated rates.

### Converted Amount Fields and Their Rules

Currency fields on Salesforce records come in pairs. For example, `Opportunity.Amount` stores the value in the record's currency (`CurrencyIsoCode`), while `Opportunity.ConvertedAmount` stores the value converted to the running user's currency (or the corporate currency in API contexts). In standard multi-currency, `ConvertedAmount` uses the single `CurrencyType` rate. With ACM enabled, `ConvertedAmount` on supported objects uses the dated rate matching the record's close date. Roll-up summary fields on the parent always convert child values to the parent record's currency — using the parent's static `CurrencyType` rate, not dated rates, even when ACM is on. This is a frequent source of reconciliation errors.

---

## Common Patterns

### Dated Rate Integration Pipeline

**When to use:** The org has ACM enabled and exchange rates change frequently (daily or weekly) based on a corporate treasury feed.

**How it works:**
1. An external system publishes daily rates to a middleware layer (MuleSoft, custom API).
2. Middleware calls the Salesforce REST API to upsert `DatedConversionRate` records with the appropriate `StartDate` and rate values.
3. A scheduled Apex job or Flow verifies that rate gaps do not exist — every business day must be covered for each active currency.
4. Monitoring alerts fire if a currency's most recent `DatedConversionRate.StartDate` is more than two business days old.

**Why not the alternative:** Manually entering dated rates in Setup does not scale past a handful of currencies and introduces human error. Missing a date range causes Salesforce to silently fall back to the static rate, producing incorrect conversions with no warning.

### Report Currency Override Strategy

**When to use:** Stakeholders in different regions need reports in their local currency, but some reports must always show corporate currency for finance.

**How it works:**
1. By default, Salesforce reports display converted amounts in the running user's personal currency (set in their user record).
2. For finance reports that must always show corporate currency, use the "Show > Currencies" option in the report builder and select the corporate currency explicitly.
3. For dashboard snapshots consumed by mixed audiences, pin the dashboard running user to a service account whose personal currency is the corporate currency.
4. Document which reports use overridden currency and which use running-user currency to prevent confusion during audits.

**Why not the alternative:** Relying solely on running-user currency means the same report shows different numbers to different people, which causes reconciliation disputes. Pinning all reports to corporate currency frustrates regional managers who need local-currency views.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org needs historical accuracy for revenue recognition | Enable ACM with dated exchange rates | Standard multi-currency retroactively changes all converted amounts when rates update |
| Only 1-2 currencies, rates rarely change | Standard multi-currency is sufficient | ACM adds complexity and is irreversible; low currency volume does not justify it |
| Roll-up summaries must match dated-rate conversions | Build Apex or Flow-based aggregation instead of declarative roll-ups | Native roll-up summaries always use the parent's static rate, ignoring dated rates |
| Custom objects need dated rate conversions | Implement conversion logic in Apex using DatedConversionRate queries | Custom objects do not automatically use dated rates even with ACM enabled |
| Finance team requires point-in-time snapshots | Store converted amounts in custom fields at close time via trigger | Relying on live conversion means values shift as rates change |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on multi-currency architecture:

1. **Audit current state** — Confirm whether multi-currency and ACM are enabled. Query `SELECT IsoCode, ConversionRate, IsActive FROM CurrencyType` and check for `DatedConversionRate` records. Document which currencies are active.
2. **Map currency fields to objects** — For every object that carries currency data (Opportunity, Quote, OpportunityLineItem, custom objects), list which fields are amount fields, which have converted counterparts, and whether the object supports dated rates.
3. **Decide on ACM** — If the org requires historical rate accuracy for reporting or revenue recognition, plan ACM enablement. Document that this is irreversible and schedule the enablement during a low-activity window.
4. **Design the rate maintenance process** — Define who or what system updates exchange rates, how often, and how gaps are detected. If using ACM, build or configure the `DatedConversionRate` integration pipeline.
5. **Address roll-up summary gaps** — Identify all roll-up summary fields that aggregate currency amounts. For each, determine whether the static-rate conversion is acceptable or whether a custom Apex/Flow aggregation is needed.
6. **Configure reporting currency rules** — Set the corporate currency display for finance reports, document running-user currency behavior for regional reports, and pin dashboard service accounts where needed.
7. **Validate end-to-end** — Create test Opportunities in at least two non-corporate currencies with different close dates, update exchange rates, and verify that Amount, ConvertedAmount, roll-up values, and report totals all match expected values.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] ACM enablement decision is documented with rationale and stakeholder sign-off (irreversible change)
- [ ] All active currencies have current exchange rates — no gaps in DatedConversionRate date ranges if ACM is on
- [ ] Roll-up summary fields have been audited for static-rate-only conversion behavior
- [ ] Reports that must show corporate currency are explicitly overridden (not relying on running-user default)
- [ ] Custom objects with currency fields have documented conversion logic (dated rates do not apply automatically)
- [ ] Rate maintenance process is automated or has a documented manual SOP with monitoring
- [ ] End-to-end test confirms converted amounts match expected values across currencies and close dates

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **ACM is irreversible** — Once advanced currency management is enabled, it cannot be disabled. This is a one-way door. Enabling it in a sandbox first is essential, but the production decision must be treated as permanent.
2. **Roll-up summaries ignore dated rates** — Roll-up summary fields on parent objects always use the static `CurrencyType` rate, not dated exchange rates. This means an Account's rolled-up Opportunity amount will not match the sum of its child Opportunities' `ConvertedAmount` values when ACM is enabled and rates have changed.
3. **Custom objects fall back to static rates** — Even with ACM enabled, custom objects do not use `DatedConversionRate`. They always use the single static rate from `CurrencyType`. Any custom object needing dated conversion must implement it in Apex.
4. **Report currency depends on the running user** — Converted amounts in reports use the personal currency of the user running the report. Two users in different regions will see different numbers in the same report. This is not a bug but is frequently reported as one.
5. **Changing a static rate retroactively changes all non-ACM conversions** — Updating the `ConversionRate` on a `CurrencyType` record immediately recalculates every `ConvertedAmount` field on every record using that currency — for all objects that do not use dated rates. There is no versioning or undo.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| ACM decision record | Architecture decision documenting whether to enable ACM, with rationale, tradeoffs, and stakeholder approval |
| Currency field mapping | Spreadsheet or table mapping every currency field to its object, conversion rule (static vs. dated), and reporting behavior |
| Rate maintenance runbook | Operational document describing who updates rates, how often, what integration is used, and how gaps are monitored |
| Report currency matrix | Table of key reports with their currency display setting (running-user vs. explicit override) and intended audience |

---

## Related Skills

- high-volume-sales-data-architecture — Use when multi-currency intersects with large data volumes and query performance on converted amount fields
- sales-cloud-architecture — Use for broader Sales Cloud design decisions that include but are not limited to currency handling

---

## Official Sources Used

- Salesforce Help: Manage Multiple Currencies — https://help.salesforce.com/s/articleView?id=sf.admin_currency.htm
- Salesforce Object Reference: CurrencyType — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_currencytype.htm
