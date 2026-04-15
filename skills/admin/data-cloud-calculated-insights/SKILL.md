---
name: data-cloud-calculated-insights
description: "Guides creation, design, and maintenance of Calculated Insights in Data Cloud: SQL authoring, dimension/measure definition, scheduling, streaming insights, and insight configuration tradeoffs. Trigger keywords: calculated insight, CI SQL, insight measure, insight dimension, streaming insight, insight schedule, Data Cloud metric, insight refresh. NOT for standard formula fields on sObjects, CRM Analytics SAQL metrics, or Data Cloud segment filter conditions that do not persist as insights."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Operational Excellence
tags:
  - data-cloud
  - calculated-insights
  - streaming-insights
  - sql
  - data-cloud-metrics
  - segmentation
inputs:
  - List of metrics and dimensions to compute (names, data types, business definitions)
  - Source Data Model Objects (DMOs) the insight will query
  - Whether the use case needs batch-scheduled or near-real-time signal
  - Planned insight refresh cadence (6h / 12h / 24h)
  - Whether the insight will be used for segmentation, activation, or both
outputs:
  - Calculated Insight SQL definition with GROUP BY dimensions and aggregation measures
  - Insight configuration (schedule, base DMO, dimension/measure API names)
  - Streaming Insight configuration for real-time signal use cases (if applicable)
  - Design review checklist confirming immutable fields are finalized before creation
  - Decision table comparing Calculated vs. Streaming vs. Real-Time Insights for the use case
triggers:
  - "how to create a calculated insight in data cloud"
  - "data cloud insight SQL not producing correct metrics"
  - "can I change the measure API name in an existing calculated insight"
  - "streaming insight vs calculated insight for real-time segmentation"
  - "data cloud insight not refreshing on schedule"
  - "how to define dimensions and measures for data cloud insights"
  - "insight schedule only allows 6 12 or 24 hour intervals"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# Data Cloud Calculated Insights

This skill activates when a practitioner needs to design, author, or troubleshoot Calculated Insights in Data Cloud — batch SQL-based metrics that aggregate DMO data into persistent measures and dimensions attached to Unified Profiles. It also covers Streaming Insights for near-real-time signal use cases and the critical pre-build design decisions that cannot be changed after an insight is created.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Finalize all dimension and measure API names before creation.** Measure API names, measure data types, rollup behavior, and dimension names are immutable after a Calculated Insight is created. Only additive changes (adding new measures or dimensions) are allowed. Renaming or changing a type requires deleting the insight and recreating it, which loses all historical data.
- **Confirm the use case requires Calculated Insights (batch) vs. Streaming Insights (real-time).** Streaming Insights process only Mobile SDK and Marketing Cloud Personalization event sources in near-real time. They cannot join Unified Profiles, cannot produce lifetime aggregates, and cannot be used as segment filter conditions for batch segmentation. Mixing up these two types is the most common design error.
- **Check org limits before adding insights.** The org-wide maximum is 300 total insights (Calculated + Streaming combined). Streaming Insights are additionally capped at 20 per org. An org near its limit cannot create new insights regardless of SQL validity.
- **Confirm available DMOs for the SQL.** The Calculated Insight SQL must reference DMOs (not DLOs). Confirm that all required DMOs have been mapped and populated before authoring the SQL, or the insight will fail silently or return zero rows.

---

## Core Concepts

### SQL Authoring and the 131,021-Character Limit

Calculated Insights are authored using ANSI SQL in the Data Cloud UI's SQL editor. The SQL must use `GROUP BY` to define dimensions — every non-aggregated column in the SELECT must appear in the GROUP BY clause. Aggregation functions (COUNT, SUM, AVG, MIN, MAX) define measures. Subqueries, CTEs (WITH clauses), and joins across multiple DMOs are supported. The SQL has a hard character limit of 131,021 characters. This is rarely hit in practice but matters for complex multi-DMO joins.

The execution timeout is 2 hours. Insights whose SQL takes longer than 2 hours to run are terminated and marked as failed for that run cycle. Optimize complex joins and filter early (use WHERE to limit the data scanned).

### Dimensions and Measures — Immutability After Creation

When a Calculated Insight is saved, every dimension name, every measure API name, every measure data type, and every rollup behavior setting is permanently locked. The platform allows additive changes only: new measures or dimensions can be added to an existing insight, but existing ones cannot be renamed, retyped, or removed. This is the most operationally significant constraint in this domain. It means:

- Dimension API names must use the final production naming convention before the insight is created.
- Measure data types must be chosen correctly the first time (e.g., do not use INTEGER if the result can be a decimal).
- Rollup behavior (how measures are aggregated for nested segments) must be specified upfront.

If a mistake is discovered after creation, the only remediation is to delete the insight (losing all historical metric values) and recreate it with corrected definitions.

### Scheduling — Only 6h, 12h, and 24h Intervals

Calculated Insights run on a scheduler. The only supported cadences are **every 6 hours, every 12 hours, or every 24 hours**. There is no sub-hour scheduling, no on-demand trigger via the UI (though the API allows a manual refresh), and no event-driven execution. Choose the cadence based on the downstream use case: if a segment or activation depends on freshness within 6 hours, select the 6-hour cadence and account for that lag in the downstream SLA.

An insight with a 24-hour cadence that feeds a "purchase in the last 24 hours" segment condition can be stale by up to 48 hours in the worst case (if the insight runs just before the purchase event is ingested). Design insight windows with this lag in mind — use longer lookback windows (e.g., 48 or 72 hours) to absorb scheduling variability.

### Streaming Insights — Scope and Hard Limits

Streaming Insights are a distinct feature. They process event streams from only two sources: **Mobile/Web SDK** and **Marketing Cloud Personalization**. They are evaluated in near-real-time as events arrive and produce a current signal (e.g., "viewed product page in the last 30 minutes") that can trigger Data Actions. Streaming Insights:

- Cannot join Unified Individual profiles or reference standard DMOs from batch data streams.
- Cannot produce lifetime or long-window aggregates (they are windowed, near-real-time signals).
- Cannot be used as segment filter conditions for batch audience segments.
- Are limited to **20 per org** (hard limit).
- Are suited for real-time trigger scenarios (push notifications, personalization calls) — not for audience-building or reporting.

---

## Common Patterns

### Pattern 1: Lifetime and Window Aggregate Metrics for Segmentation

**When to use:** The segmentation team needs filter conditions based on aggregated customer behavior (e.g., "total lifetime spend > $500", "number of purchases in last 90 days >= 3", "average order value in last 12 months").

**How it works:**
1. Design the dimension and measure list on paper first. Write final API names in snake_case following the org's naming convention. Confirm data types (DECIMAL for monetary, INTEGER for counts, DATE for date dimensions).
2. In Data Cloud, navigate to Calculated Insights and click New. Select the base DMO (typically the DMO containing the transactional records, e.g., a custom `PurchaseEvent__dlm` mapped to a `SalesOrder` DMO).
3. Author the SQL. Example for a 90-day purchase count and lifetime spend:
```sql
SELECT
    unified_id__c                          AS customer_id,
    COUNT(order_id__c)                     AS purchase_count_90d,
    SUM(order_total__c)                    AS total_lifetime_spend
FROM SalesOrder__dlm
WHERE order_date__c >= DATEADD(DAY, -90, CURRENT_DATE)
GROUP BY unified_id__c
```
4. Set dimension: `customer_id`. Set measures: `purchase_count_90d` (INTEGER), `total_lifetime_spend` (DECIMAL).
5. Assign a 24-hour refresh schedule.
6. After the first run completes, navigate to Segment Builder and confirm the measures appear as filterable fields on the Unified Individual object.

**Why not the alternative:** Real-time segment filters (evaluated at segment run time against raw DMO data) do not persist as named metrics, cannot be referenced by activation targets, and are re-evaluated from scratch on every segment refresh. Calculated Insights persist as queryable fields that survive across segment runs and can be reused in multiple segments without re-aggregating.

### Pattern 2: Streaming Insight for Real-Time Personalization Trigger

**When to use:** A web personalization system needs to know within seconds whether a customer has abandoned a cart or viewed a product category, so it can trigger a Data Action (push notification, real-time API call).

**How it works:**
1. Confirm the event source is Mobile/Web SDK or Marketing Cloud Personalization. No other source type is compatible with Streaming Insights.
2. In Data Cloud, navigate to Streaming Insights and click New. Select the event stream source.
3. Define the window (e.g., last 30 minutes) and the event condition (e.g., `event_type = 'cart_abandon'`).
4. Connect the Streaming Insight to a Data Action to fire the outbound trigger when the condition is met.
5. Do not attempt to use this insight as a segment filter — it is not available in the Segment Builder for batch audience work.

**Why not the alternative:** Using a Calculated Insight for this use case would introduce a 6–24 hour lag, making it unsuitable for real-time personalization. Streaming Insights are the only mechanism for sub-minute signal delivery within Data Cloud.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Aggregate customer behavior for audience segmentation | Calculated Insight (batch SQL) | Produces persistent, reusable measures; refreshes on a schedule; usable in Segment Builder |
| Real-time trigger on user event (cart abandon, page view) | Streaming Insight | Sub-minute latency; connects directly to Data Actions |
| Metric uses lifetime window or multi-month lookback | Calculated Insight | Streaming Insights are windowed and cannot produce lifetime aggregates |
| Event source is Web/Mobile SDK or MCP Personalization | Either is possible; use Streaming for real-time, Calculated for aggregate | Source compatibility depends on freshness need |
| Need to segment by the metric value | Calculated Insight only | Streaming Insights are not available as Segment Builder filter fields |
| Freshness requirement is under 1 hour | Streaming Insight (if source is compatible) | Calculated Insights minimum cadence is 6 hours |
| Insight involves joins across multiple batch DMOs | Calculated Insight | Streaming Insights cannot join across DMOs |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Design dimension and measure definitions on paper before opening the UI.** List every dimension and measure by its final API name, data type, and business definition. Confirm with stakeholders. This step is mandatory — API names and types cannot be changed after creation. Use snake_case API names and match the org's naming convention. Confirm whether any measure requires a specific rollup behavior for nested segment logic.

2. **Verify all source DMOs are mapped and populated.** In Data Cloud Setup, confirm that the DMOs the SQL will reference have been mapped from their source DLOs and have a non-zero record count. An insight that references an empty or unmapped DMO will produce zero rows with no actionable error message.

3. **Determine whether Calculated Insights or Streaming Insights fit the use case.** Use the Decision Guidance table above. If the use case requires real-time signal delivery (under 1 hour) and the source is Mobile/Web SDK or Marketing Cloud Personalization, use Streaming Insights. For all other cases — especially segmentation, activation, reporting — use Calculated Insights.

4. **Author and validate the SQL.** In the Calculated Insights SQL editor, write the query. Use GROUP BY for all non-aggregated columns. Test against a small date range first. Verify the SQL executes within the 2-hour timeout by checking preview row counts. Stay well under the 131,021-character SQL limit for complex joins.

5. **Configure insight metadata: name, schedule, dimensions, and measures.** Set the API name following the design from Step 1. Select the schedule cadence (6h / 12h / 24h). Assign correct data types to all measures. Set rollup behavior. Save the insight. **After saving, verify the configuration is correct before the first run — dimension and measure definitions are immutable from this point.**

6. **Trigger the first run and monitor execution.** After saving, either wait for the scheduled run or trigger a manual refresh via the API. Monitor the run status in the Calculated Insights detail view. Confirm the run completes successfully (status: Completed, not Failed or Timed Out). Check that the row count in the insight matches expectations.

7. **Verify downstream availability.** Navigate to Segment Builder and confirm the Calculated Insight measures appear as filter fields on the Unified Individual object. For Streaming Insights, confirm the Data Action fires correctly by simulating an event from the SDK or reviewing Data Action execution logs.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All dimension API names and measure API names finalized and reviewed before the insight was created (they are now immutable)
- [ ] Measure data types are correct (no INTEGER used where DECIMAL is needed; no STRING where a numeric type was intended)
- [ ] All referenced DMOs exist, are mapped from their source DLOs, and have a non-zero record count
- [ ] Insight schedule cadence (6h / 12h / 24h) is appropriate for the downstream freshness requirement
- [ ] First run completed successfully with a non-zero row count
- [ ] Calculated Insight measures appear correctly in Segment Builder for the intended segmentation use cases
- [ ] Org-level insight count checked — total insights (Calculated + Streaming) must remain below 300; Streaming Insights must remain below 20
- [ ] If Streaming Insights were used, confirmed source is Mobile/Web SDK or MCP Personalization (no other source types are supported)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Measure API names are permanent** — After a Calculated Insight is created, the API name of every measure is locked. The only recourse for a naming mistake is to delete the insight and recreate it, which discards all historical values. Treat insight creation as a schema migration: require design review sign-off before saving.

2. **Scheduling gaps can double the effective staleness** — A 24-hour Calculated Insight can be up to 48 hours stale in practice (if new events arrive just after the insight finishes running). Design lookback windows conservatively: a "purchases in the last 24 hours" condition should use a 48–72 hour window to avoid edge cases where the insight misses the most recent events.

3. **Streaming Insights cannot be used in Segment Builder** — Teams that build Streaming Insights expecting to use them as audience segment filter conditions discover this limitation only after the insight is live. Streaming Insights are exclusively for real-time trigger/Data Action scenarios. If segmentation is the goal, always use a Calculated Insight.

4. **300 total / 20 streaming org limits are hard caps** — There is no way to increase these limits through support or configuration. Orgs with many campaigns and many data sources can approach the 300-insight ceiling if insights are created ad hoc without governance. Implement an insight naming convention and a lifecycle process (delete stale insights) before the limit becomes a blocker.

5. **Streaming Insights cannot join Unified Profiles** — Streaming Insights operate on raw event streams and cannot resolve or reference a Unified Individual profile. This means a Streaming Insight cannot produce a metric like "this customer's total lifetime spend." It can only assess the current event stream window. If the real-time trigger logic needs to reference persistent profile attributes, the trigger must call an external API to enrich — the Streaming Insight alone cannot provide it.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Calculated Insight SQL definition | The ANSI SQL query with GROUP BY dimensions and aggregation measures, ready for the UI editor |
| Insight configuration record | API name, schedule cadence, dimension names and types, measure names, types, and rollup settings |
| Pre-creation design checklist | Finalized dimension/measure API names and data types, confirmed before insight creation |
| Streaming Insight configuration | Event source, window definition, condition logic, and linked Data Action reference (if applicable) |
| Decision rationale | Documented reasoning for Calculated vs. Streaming Insights choice for the use case |

---

## Related Skills

- `admin/data-cloud-segmentation` — Covers audience segment creation; Calculated Insight measures appear as segment filter fields once the insight has run. Use after this skill when building segments that depend on CI metrics.
- `data/data-cloud-data-streams` — Covers DLO-to-DMO mapping; DMOs must be fully mapped before Calculated Insights can reference them. Use before this skill when DMO configuration is incomplete.
- `admin/data-cloud-identity-resolution` — Identity resolution produces the Unified Individual records that Calculated Insights aggregate. Use before this skill when unified profiles have not been resolved.
- `admin/data-cloud-architecture-patterns` — Covers org-level Data Cloud design decisions including insight governance and the 300-insight limit. Use for multi-BU or high-volume deployments.
