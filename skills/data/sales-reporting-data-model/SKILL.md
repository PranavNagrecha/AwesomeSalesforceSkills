---
name: sales-reporting-data-model
description: "Use when designing or troubleshooting Salesforce sales reporting — covers Historical Trend Reporting, Reporting Snapshots, and Custom Report Types for pipeline and opportunity analysis. Trigger keywords: historical trending, opportunity snapshot, reporting snapshot, pipeline history, custom report type join, point-in-time reporting. NOT for CRM Analytics (Tableau CRM / Einstein Analytics) or Marketing Cloud reports. NOT for general SOQL optimization."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Scalability
triggers:
  - "how do I see how opportunity stage changed over the last 90 days in Salesforce"
  - "I need to compare pipeline this quarter to the same period last year"
  - "reporting snapshot source report limit 2000 rows not working"
  - "how do I create a report of accounts with no opportunities"
  - "historical trend reporting not showing data before activation date"
  - "custom report type without join for exception analysis"
tags:
  - sales-reporting
  - historical-trending
  - reporting-snapshots
  - custom-report-types
  - opportunity
  - pipeline
  - point-in-time
  - data-model
inputs:
  - "Whether Historical Trend Reporting is already enabled in the org (Setup > Historical Trend Reporting)"
  - "Number of fields to track historically on Opportunity (max 8 total, 5 standard + 3 custom)"
  - "How far back historical pipeline data is needed (HTR covers ~3 months; Snapshots offer unlimited history)"
  - "Expected row count of the source report driving a Reporting Snapshot (cap is 2,000 rows)"
  - "Which objects need to be joined in a Custom Report Type (max 4-object chain)"
  - "Whether the reporting requirement needs exception / gap analysis ('records without related records')"
outputs:
  - "Recommendation on Historical Trend Reporting vs Reporting Snapshots vs Custom Report Types for each use case"
  - "HTR field selection and activation checklist"
  - "Reporting Snapshot design (source report, target object, field mapping, schedule)"
  - "Custom Report Type configuration guidance (relationship chain, 'with/without' joins)"
  - "Pipeline trend or opportunity history report configuration steps"
  - "Review checklist for each mechanism"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Sales Reporting Data Model

This skill activates when a practitioner needs to design, configure, or troubleshoot sales reporting mechanisms in Salesforce — specifically Historical Trend Reporting (HTR), Reporting Snapshots, and Custom Report Types (CRTs) for pipeline analysis and opportunity reporting. It covers the data model constraints, activation requirements, scheduling, and architectural tradeoffs for each mechanism. It does NOT cover CRM Analytics / Tableau CRM, Marketing Cloud Datorama, or SOQL query optimization.

---

## Before Starting

Gather this context before working on anything in this domain:

- **HTR activation state**: Is Historical Trend Reporting enabled? Check Setup > Historical Trend Reporting. HTR must be explicitly enabled per object (Opportunity is the main candidate). Activation must happen before data collection begins — no retroactive history is captured for the period before activation.
- **Row-count reality for Reporting Snapshots**: The source report driving a Reporting Snapshot cannot exceed 2,000 rows at run time. If the org has more than 2,000 Opportunities in the scoped report, the snapshot run will truncate or fail. Confirm pipeline scope before recommending Snapshots as the mechanism.
- **Common wrong assumption — HTR retention**: Practitioners assume HTR data is kept indefinitely. It is not. Salesforce retains approximately 3 months of historical trending data on Opportunity (and up to 4 months on Forecasts/Cases). This is a hard platform limit, not configurable.
- **Key limits in play**:
  - HTR tracks up to 8 fields total per object (5 standard + 3 custom on Opportunity). Additional fields beyond 8 cannot be tracked.
  - CRTs support up to a 4-object relationship chain.
  - Reporting Snapshots run on a scheduled basis (hourly, daily, weekly) and write to a custom object — storage limits apply.
  - CRT "without" joins (exception reporting) require explicit configuration in the CRT wizard.

---

## Core Concepts

### Historical Trend Reporting (HTR)

Historical Trend Reporting is a declarative Salesforce feature that captures daily snapshots of selected field values on Opportunity (and a few other objects: Cases, Forecasting Items, Leads). It enables trend-style reports such as "show me how this Opportunity's Amount and Stage changed over the past 90 days" without a custom snapshot architecture.

**How it works under the hood:** Salesforce stores trending data in a separate, internal system data store — not in a custom object. The data appears in the report builder as a special "historical" row for each date in a date range. You select which fields to trend in Setup > Historical Trend Reporting.

**Key constraints:**
- Tracking is forward-only. Enabling HTR today means trend data starts accumulating today.
- Up to 8 fields tracked per object (Opportunity defaults: Amount, CloseDate, Forecast Category, Opportunity Name, Stage, Owner — that leaves 3 custom field slots).
- Retention window: approximately 3 months for Opportunity (up to 4 months for other objects). Older snapshots are automatically purged.
- Only specific report types support HTR: "Opportunities with Historical Trending" is the dedicated type.
- No API access to the raw trend data — it is report-only.

### Reporting Snapshots

Reporting Snapshots are a platform mechanism that runs a source report on a schedule and writes the results as records into a custom object (the "target object"). This allows you to store unlimited historical pipeline data and report on it with any standard report type — including historical comparisons going back years.

**How it works:**
1. Define a source report (must be a Tabular or Summary report with 2,000 rows or fewer at run time).
2. Create a target custom object with fields matching the source report columns.
3. Map source report columns to target object fields in the Reporting Snapshot configuration.
4. Set a schedule (hourly, daily, weekly).
5. Salesforce runs the source report at the scheduled time and inserts records into the target object.

**Key constraints:**
- Source report row cap: **2,000 rows maximum** at run time. Exceeding this causes the snapshot to truncate or fail silently.
- Target object accumulates records over time — storage costs grow. Plan a data retention/archival strategy.
- Source report must be owned by an active user with run access to all data in scope.
- Snapshot runs do not backfill — missed runs are simply skipped.

### Custom Report Types (CRTs)

Custom Report Types allow report builders to create report types that join up to 4 related objects (versus the limited set of standard report types), and to control which fields are available in the report. They also support "records without related records" joins — essential for exception and gap analysis (e.g., "Accounts with no Open Opportunities").

**Key features:**
- Join up to 4 objects in a parent-child chain.
- For each join step, choose: "Each A record must have at least one related B record" (inner-join behavior) OR "A records may or may not have related B records" (outer-join / 'without' behavior).
- Control exactly which fields appear in the report type, including renaming fields for clarity.
- CRTs must be set to "Deployed" status before users can access them.

**CRTs are the right tool for:**
- Pipeline gap analysis (Accounts without Opportunities in the last 90 days).
- Multi-object drill-through (Opportunity > Opportunity Line Item > Product > Pricebook).
- Exception reports (Contacts with no Activity in 60 days).

---

## Common Patterns

### Pattern: Forward-Looking Pipeline Trend With HTR

**When to use:** A sales operations team wants a weekly view showing how Opportunity Stage and Amount have changed over the past 60–90 days for open deals. The pipeline scope fits within 2–3 months.

**How it works:**
1. Enable Historical Trend Reporting in Setup > Historical Trend Reporting. Select "Opportunity" and check the fields to track (e.g., Amount, CloseDate, StageName, plus any custom forecast fields). Save.
2. Wait for data to accumulate — at minimum 2 data points are needed before trends are visible.
3. In the Report Builder, create a new report with type "Opportunities with Historical Trending."
4. Add a "Historical Date" filter scoping the trend window (e.g., "Last 90 Days").
5. Add historical field columns (e.g., "Amount (Historical)," "Stage (Historical)") alongside current columns.
6. Group by Opportunity Name and Historical Date to see field changes per deal over time.

**Why not just use Reporting Snapshots:** HTR is fully declarative with no custom object, no scheduler configuration, and no storage overhead. For a rolling 3-month window on Opportunity fields, HTR is lower-maintenance.

**Why not use HTR for multi-year history:** The 3-month retention cap means data older than ~90 days is purged. Use Reporting Snapshots for multi-year pipeline history.

### Pattern: Long-Term Pipeline History Archive With Reporting Snapshots

**When to use:** Leadership wants a quarterly review comparing current pipeline to the same date last year. The window exceeds HTR's retention cap. The scoped pipeline report has fewer than 2,000 rows.

**How it works:**
1. Create a source Summary report scoped to the relevant pipeline view (e.g., "Open Opportunities by Stage and Owner," row count below 2,000).
2. Create a custom object (e.g., `Pipeline_Snapshot__c`) with fields matching the source report columns. Use Currency for amount, Date for dates, Percent for probability — never Text for these types.
3. In Setup > Reporting Snapshots, create a new snapshot. Map source report columns to target object fields.
4. Set a schedule (e.g., daily at midnight). Use a service account as the Running User.
5. Build reports and dashboards on `Pipeline_Snapshot__c`, filtering by `Snapshot_Date__c` to compare pipeline at different points in time.

**Why not just use HTR:** HTR retention is limited to ~3 months. Reporting Snapshots accumulate indefinitely.

### Pattern: Gap / Exception Report With Custom Report Type

**When to use:** A sales manager wants a report of Accounts that have no Opportunities created in the last 90 days — cold accounts at risk of churn.

**How it works:**
1. In Setup > Report Types, create a new Custom Report Type. Primary object: Account.
2. Add related object: Opportunities. For the join type, select "A records may or may not have related B records" (outer join).
3. Set CRT status to "Deployed."
4. Build a report using the new CRT. Add a cross-filter: "Accounts without Opportunities where Created Date > 90 days ago."
5. The report returns Accounts that have no Opportunities meeting the criteria.

**Why not use a standard report type:** Standard "Accounts with Opportunities" report types use inner join semantics — they only return Accounts that have at least one Opportunity. The "without" join in a CRT is required for exception/gap queries.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to see how deal stage and amount changed over last 3 months | Historical Trend Reporting | Declarative, zero storage cost, built for rolling trend windows on Opportunity |
| Need pipeline snapshot history going back more than 3 months | Reporting Snapshots to a custom object | HTR data is purged after ~3 months; Snapshots store indefinitely |
| Source report for Snapshot has more than 2,000 rows at run time | Segment into multiple smaller source reports or use Apex-based snapshot logic | Reporting Snapshot hard cap is 2,000 rows; excess rows are silently dropped |
| Need to join 3 or more related objects in a single report | Custom Report Type with multi-object chain | Standard report types cap at 2 objects; CRTs support up to 4 |
| Need to report on Accounts with NO related Opportunities | Custom Report Type with "without" join | Only CRTs offer outer-join / gap-analysis semantics |
| Need to track a 4th custom field on Opportunity in HTR | Evaluate field priority carefully; 8-field cap is hard | HTR allows 5 standard + 3 custom Opportunity fields; remove a lower-priority field to add a new one |
| Need real-time intra-day pipeline snapshots | Apex-based custom snapshot logic or Data Cloud | Reporting Snapshots run at most hourly and have a 2,000-row cap |
| Need to report on historical pipeline across multiple currencies | Use Currency field type on Snapshot target object | Multi-currency orgs require Currency field type, not Text; HTR handles currency natively |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on sales reporting data model tasks:

1. **Clarify the time horizon and scope**: Determine how far back history is needed (3 months or less vs. multi-year). Confirm whether the pipeline scope (filtered Opportunity count) is below 2,000 rows if Reporting Snapshots are under consideration. This drives mechanism selection.
2. **Select the reporting mechanism**: Use the Decision Guidance table to choose between Historical Trend Reporting, Reporting Snapshots, or Custom Report Types. In some designs, all three are combined (HTR for near-term trends, Snapshots for long-term archive, CRTs for exception analysis).
3. **Configure HTR if selected**: In Setup > Historical Trend Reporting, enable Opportunity trending. Select up to 8 fields (5 standard + 3 custom). Save. Confirm data starts populating the next day. Build the "Opportunities with Historical Trending" report type in the Report Builder.
4. **Design and activate the Reporting Snapshot if selected**: Create the target custom object with matching field types (Currency, Date, Percent — not Text). Create the source Tabular/Summary report and confirm row count is below 2,000. Configure the Reporting Snapshot field mappings in Setup > Reporting Snapshots. Set the schedule and activate. Monitor the first run for errors in the Reporting Snapshot run history.
5. **Create and deploy the Custom Report Type if selected**: In Setup > Report Types, define the object chain (up to 4 objects). Set each join relationship to "with" (inner) or "without" (outer) semantics as required. Set status to "Deployed." Build and validate reports using the new CRT.
6. **Build and test reports and dashboards**: Validate that filters, groupings, and date ranges return expected data. For Reporting Snapshots, test by comparing a current snapshot run to a known pipeline state. For HTR, confirm historical columns show expected values on deals with known history.
7. **Document retention limits and operational procedures**: Record the HTR 3-month retention cap for stakeholders. For Reporting Snapshots, document storage growth rate and any archival/purge plan for old snapshot records. Confirm the Snapshot source report owner is an active service account user with ongoing data access.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] HTR is enabled for Opportunity (if using historical trending reports) and fields are selected within the 8-field cap
- [ ] HTR was not enabled after the period of interest — if enabled today, data before today is not available
- [ ] Reporting Snapshot source report row count verified to be below 2,000 at run time
- [ ] Reporting Snapshot target custom object fields use correct field types (Currency for amounts, Date for dates — not Text)
- [ ] Reporting Snapshot schedule is active and source report owner is an active, licensed service account user
- [ ] Reporting Snapshot run history checked for errors after first execution
- [ ] Custom Report Type status is "Deployed" (not Draft)
- [ ] CRT join type ("with" vs "without") is correctly set for each relationship step and validated with test data
- [ ] Reports built on Snapshot target objects include a Snapshot_Date__c filter to scope to the correct time period
- [ ] Multi-currency orgs: Currency field type used (not Text) on Snapshot target object for monetary values

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **HTR data is not retroactive** — Enabling Historical Trend Reporting today means trend data begins accumulating from today forward. Data from before activation is permanently unavailable. There is no way to backfill historical trending data.

2. **Reporting Snapshot source report row cap is silently enforced** — If the source report exceeds 2,000 rows at run time, Salesforce truncates the result set and writes only the first 2,000 rows into the target object without raising an obvious error. The snapshot run is marked "Successful" in the run history log.

3. **HTR field cap of 8 cannot be worked around with formula fields** — Formula fields are not eligible for HTR tracking. Only standard and custom non-formula fields can be tracked. To track computed values, track the underlying component fields and compute at report time.

4. **Reporting Snapshot records accumulate indefinitely** — A daily snapshot of 1,500 Opportunity rows creates ~547,500 records per year in the target object. Without an archival or deletion strategy, the org will hit storage limits.

5. **CRT "without" join applies only at the immediately adjacent relationship step** — In an Account > Opportunity > OLI chain, "without" at the Account-Opportunity step shows Accounts without Opportunities; "without" at the Opportunity-OLI step shows Opportunities without Line Items. Configuring the wrong step produces unexpected results.

6. **HTR trending columns only appear in the dedicated report type** — The "Opportunities with Historical Trending" report type is required. Adding date filters to a standard Opportunities report type does not expose trending columns.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `sales-reporting-data-model-template.md` | Work template for designing and documenting sales reporting architecture decisions — captures mechanism choice rationale, field selections, Snapshot object design, and CRT configuration |
| `check_sales_reporting_data_model.py` | stdlib Python checker that scans Salesforce metadata XML for common issues: Snapshot target object fields using wrong types, missing HTR field configuration, undeployed CRTs |

---

## Related Skills

- `sales-cloud-architecture` — use for broader Sales Cloud data model design (Lead-to-Cash object chain, territory, forecasting) that underpins the reporting layer
- `soql-query-optimization` — use when building SOQL queries against Reporting Snapshot target objects or when diagnosing slow report run times
- `data-migration-planning` — use when migrating historical Reporting Snapshot records or archiving old snapshot data to external storage
- `person-accounts` — use when pipeline reports include Person Account Opportunities and filters need to separate individual vs. business account deals
