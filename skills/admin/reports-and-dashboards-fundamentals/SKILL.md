---
name: reports-and-dashboards-fundamentals
description: "Use when learning, designing, or explaining Salesforce Reports and Dashboards from first principles — report types, custom report types, groupings, bucket fields, summary formulas, charts, dashboard components, dynamic dashboards, report subscriptions, and folder permissions. Triggers: 'how do I build a report', 'what report type should I use', 'set up a dashboard', 'joined report limits', 'bucket field vs formula', 'dynamic dashboard running user'. NOT for CRM Analytics (use crm-analytics-* skills). NOT for Einstein Discovery predictive analytics. NOT for troubleshooting missing report data caused by sharing model issues (use admin/reports-and-dashboards for that)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - User Experience
tags:
  - reports
  - dashboards
  - report-types
  - custom-report-types
  - bucket-fields
  - summary-formulas
  - dynamic-dashboards
  - joined-reports
  - report-subscriptions
  - dashboard-filters
triggers:
  - "how do I build a report in Salesforce"
  - "what report type should I use for this data"
  - "set up a dashboard for the sales team"
  - "explain joined report limits and blocks"
  - "bucket field versus summary formula"
  - "dynamic dashboard running user configuration"
  - "custom report type for multi-object reporting"
  - "report subscription not sending to all users"
  - "how do I build a report in Salesforce and add it to a dashboard with filters"
  - "stacked date filters undercounting funnel"
  - "bucket field is undeclared business logic"
inputs:
  - "Business question the report must answer"
  - "Primary and related Salesforce objects involved"
  - "Audience (executives, managers, individual contributors)"
  - "Whether data must be grouped, aggregated, or compared across time"
  - "Delivery requirement (on-demand, scheduled subscription, dashboard)"
outputs:
  - "Report type selection with justification"
  - "Report design: filters, groupings, columns, summary formulas, bucket fields"
  - "Dashboard component design with chart type recommendations"
  - "Dynamic dashboard running-user configuration guidance"
  - "Folder sharing and subscription configuration"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-21
---

# Reports and Dashboards Fundamentals

Use this skill when designing or explaining Salesforce Reports and Dashboards from the ground up — choosing the right report type, structuring filters and groupings, configuring dashboard components, setting up dynamic dashboards, and distributing results via subscriptions or folder sharing. Activate when a practitioner needs to understand how the platform works, not just fix a broken report.

---

## Before Starting

Gather this context before working in this domain:

| Context | Why it matters |
|---|---|
| Org edition | Some features (joined reports, dynamic dashboards with more than 5 running users, scheduled dashboard refresh) require Enterprise edition or above. UNVERIFIED (2026-10-21): no report or dashboard edition gate is in the corpus (Help only). |
| Primary objects | Identify the parent object and any related objects needed. The object relationship determines which standard or custom report type to use. |
| Audience and access model | Who will view this report or dashboard? Their sharing access determines what rows they will see. "Run as logged-in user" is secure but shows different data per viewer; "run as specified user" shows the same slice to everyone. |
| Delivery mode | One-time analysis, ongoing dashboard, or scheduled subscription email? |
| Most common wrong assumption | Practitioners assume a report query scans all records in the org. It does not. Role hierarchy and sharing "affect access on components such as records and reports" (secguide 262 L2247-2249). Always confirm sharing access before concluding data is missing. |
| Hard platform limits | 2,000 rows displayed in the report builder UI (no row limit on export); 20 source reports per dashboard; 5 blocks per joined report; maximum 5 dynamic dashboard running users on Enterprise, 10 on Unlimited. UNVERIFIED (2026-10-21): none of these UI limits is in the corpus (Help only). The corpus 2,000-row figure is for the Reports and Dashboards API — "The API returns up to the first 2,000 report rows" (apexdev 264 L33689). |

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Should every viewer see the same rows, or only the rows they can already access?" | `SpecifiedUser` shows everyone one running user's access; `LoggedInUser` shows each viewer their own (api_meta 264 L50170-50186) — the wrong choice is a data leak (Core Concepts §4, Static dashboards row; `references/well-architected.md` Anti-Pattern 1) | A `dashboardType` decision and, for `SpecifiedUser`, a named running user whose access every viewer may see |
| "Will results go out by email subscription, and whose data should recipients receive?" | Every recipient gets the subscription running user's rows (`references/gotchas.md` Gotcha 4). UNVERIFIED (2026-10-21): subscription running-user defaults and caps are Help only | A subscription owner per audience, or one subscription per user |
| "Must parent records with no related child still appear?" | An inner-join CRT leg drops childless parents silently; `outerJoin` is Required on every leg (api_meta 264 L108493-108494; Gotcha 3) | The join type for each CRT leg, written into the design |
| "Which components must respond to each dashboard filter?" | Each report-based component needs a dashboard filter column for the filter to apply (api_meta 264 L50437-50439; Gotcha 2) | A component-by-filter coverage list tested before release |
| "Could the result set exceed 2,000 rows?" | Truncation looks like a complete answer (Gotcha 5); UNVERIFIED (2026-10-21) for the builder UI — the corpus figure is the API's 2,000-row cap (apexdev 264 L33689) | An export or async path for full extracts |
| "Is a bucket field defining business vocabulary, and can the bucketed field be blank?" | Unmatched values land in the `otherBucketLabel` container and numeric blanks follow `nullTreatment` (api_meta 264 L107009-107012); bucket names live only in report XML (Gotchas 6, 10) | A blank-handling choice and a decision to promote shared buckets to a field |
| "Is this tile counting one stage, or every record that has several stage dates?" | Stacked AND-ed date filters report the rarest stamp (Gotcha 9) | One date filter per stage tile |

A proper configuration adds what clicking through the builder skips: an explicit access decision for every dashboard and subscription, join types chosen on purpose, and limits checked before the data set outgrows them.

---

## Core Concepts

### 1. Report Types

A report type is the schema that defines which objects and fields are available in a report. Every report is built on exactly one report type.

**Standard report types** ship with Salesforce and cover common object pairs (Accounts with Contacts, Opportunities with Products, Cases with Solutions, etc.). Their join behaviour varies by type and is not documented in the corpus — UNVERIFIED (2026-10-21): the earlier "left-outer join by default" claim has no corpus source; preview the report type before relying on childless parents appearing.

**Custom report types (CRTs)** are created by admins when no standard type covers the required object combination, or when a standard type exposes the wrong join semantics. A CRT defines:
- A primary object (always required)
- Up to 3 related objects in a chain, each configured as "must have" (inner join) or "may or may not have" (outer join)
- A field layout — which fields appear and in what order in the report builder

Critical CRT limits: "A maximum of four objects can be joined in a custom report type", and "an inner join isn't allowed if there has been an outer join earlier in the join sequence" (api_meta 264 L108486-108489); the primary object "can't" be edited "after initial creation" (L108421-108423). Maximum 1,000 fields in the field layout — UNVERIFIED (2026-10-21): not in the corpus.

**Join semantics matter**: if a CRT leg is set to "must have related records," any parent that has no child of that type is excluded from report results. This is the single most common cause of unexpectedly missing rows.

### 2. Report Formats

Salesforce offers four report formats:

| Format | Use Case | Grouping |
|--------|----------|---------|
| **Tabular** | Flat list, data export, row-level detail | None |
| **Summary** | Subtotals by a single dimension (Stage, Owner, Region) | 1–3 row groupings |
| **Matrix** | Crosstab — rows and columns both grouped | 1–2 row groupings + 1–2 column groupings |
| **Joined** | Multiple report types side by side in one report | Up to 5 blocks, each with its own report type and filters |

The four `ReportFormat` values are Matrix, Summary, Tabular and Joined (api_meta 264 L107385-107391); grouping maxima are 2 across, and 2 down for matrix / 3 for summary (L106746, L106765-106766). The 5-block figure is UNVERIFIED (2026-10-21): `Report.block` is "each block in a joined report" with no maximum stated (L106662-106663).

Tabular reports cannot be used as dashboard source reports directly unless they have a row limit applied. Summary and Matrix reports are the standard dashboard source formats. UNVERIFIED (2026-10-21): not in the corpus.

Joined reports have strict limits: maximum 5 blocks, 100 columns per block, 10 custom summary formulas per block (50 per report), and 10 cross-block formulas. Bucketed fields, cross filters, and conditional highlighting are unavailable inside a joined report entirely. On a dashboard you can add a joined report's **chart** as a widget but not the full report, and you cannot add a filter to a dashboard whose widgets are all joined reports. UNVERIFIED (2026-10-21): these joined-report limits are Help only; the corpus says only that charts and custom summary formulas exist on joined reports (`ReportChart`, api_meta 264 L107511; `aggregates`, L106659-106660 — though the `chart` field row at L106671 names only summary and matrix).

### 3. Filters, Bucket Fields, and Summary Formulas

| Element | Behavior |
|---|---|
| Standard filters | Date range (relative dates like "This Quarter" are preferred over absolute dates for ongoing reports), record type, owner, and custom field filters. Up to 20 filter conditions per report (UNVERIFIED (2026-10-21) for the builder; the API allows "up to 20 custom field filters when you run a report", apexdev 264 L33690). |
| Cross-filters | Show parent records WITH or WITHOUT matching child records without adding columns from the child (`crossFilters`, "condition (WITH or WITHOUT)", API 68.0+ in metadata — api_meta 264 L106680-106682; up to five subfilters, L107813-107814). Example: "Accounts WITHOUT open Opportunities in the last 90 days." Cross-filters are powerful but add query time; use them deliberately. |
| Row limits with sort | Available only on Tabular and Summary reports. Limits the rows returned (e.g., Top 10 Opportunities by Amount). Required for dashboard components that show a list from a tabular report. UNVERIFIED (2026-10-21): the format restriction and the dashboard requirement are not in the corpus; `rowLimit` "Defines the maximum number of rows that can be returned" (api_meta 264 L106809-106810). |
| Bucket fields | Group field values into named categories inline without creating a formula field on the object. Example: bucket Amount into "Small" (under 10,000), "Mid" (10,000–100,000), "Enterprise" (above 100,000). Bucket fields are report-local (`Report.buckets`, api_meta 264 L106668); they do not persist as fields on the object. Maximum 5 bucket columns per report, 20 bucket values per bucket column — UNVERIFIED (2026-10-21): not in the corpus. |
| Summary formulas | Custom calculations across grouped rows. Example: Win Rate = CLOSED_WON_COUNT / TOTAL_COUNT. Summary formulas can reference other summary fields but not individual row fields. They exist on summary, matrix, and joined reports (`aggregates`, api_meta 264 L106659-106660) — not on tabular reports. |
| Report formula columns | Row-level formulas added via "Add Formula Column" — these calculate per row, like field formulas, and appear as a column in Tabular or Summary reports. |

### 4. Dashboards and Dynamic Dashboards

A dashboard is a visual display of up to 20 source reports (UNVERIFIED (2026-10-21): not in the corpus) shown as components (charts, metrics, tables, gauges, funnels — `DashboardComponentType` values, api_meta 264 L50388-50429).

| Element | Behavior |
|---|---|
| Static dashboards | `SpecifiedUser`: "All users see data at the access level of one specific running user … regardless of their own security settings" (api_meta 264 L50172-50175). On deploy, a missing or invalid `runningUser` is replaced with the deploying user (L50229-50232). If a viewer has less access than the running user, they still see the running user's data. This is a security concern. |
| Dynamic dashboards | `LoggedInUser`: "Each logged-in user sees data according to his or her own access level" (api_meta 264 L50185-50186). Enterprise edition supports up to 5 dynamic dashboard running users per org; Unlimited edition supports up to 10. Dynamic dashboards cannot be subscribed to or scheduled for delivery. UNVERIFIED (2026-10-21): the 5 / 10 caps and the no-subscription rule are Help only. |
| Dashboard components | Chart (bar, line, donut, funnel, scatter), Metric (single number), Gauge, Table (list from a source report), and Visualforce/Lightning Component (custom) — `componentType` values include Bar, Donut, Funnel, Gauge, LightningWebComponent, Line, Metric, Scatter, Table and VisualforcePage (api_meta 264 L50388-50429). Each component maps to one source report. |
| Dashboard filters | Up to 3 filters per dashboard (UNVERIFIED (2026-10-21): not in the corpus). "Each report-based component must have a dashboard filter column that defines the column that the filter applies to" (api_meta 264 L50437-50439); a component without one is not filtered. Test each component after adding a filter — some may be unaffected. |
| Refresh scheduling | Dashboards can be set to auto-refresh every 24 hours (minimum interval). Dynamic dashboards refresh on demand only; they cannot be scheduled. UNVERIFIED (2026-10-21): Help only. |

---

## Common Patterns

### Pattern 1: Summary Report as a Dashboard Metric Source

**When to use:** An executive dashboard needs KPIs — total pipeline value, number of open cases, win rate this quarter.

**How it works:**
1. Create a Summary report on the target object (e.g., Opportunities).
2. Group by Close Date (monthly) or Stage.
3. Add summary fields: SUM(Amount), COUNT(Id).
4. Add a Summary Formula for Win Rate if needed.
5. Apply a relative date filter ("Current FQ" or "This Quarter") so the report stays current without manual updates.
6. In the dashboard, add a Metric component pointing to this report, selecting the summary field as the value.

**Why not tabular:** Tabular reports cannot drive Metric or Chart dashboard components without a row limit (UNVERIFIED (2026-10-21): not in the corpus). They lose aggregation — each row is a raw record, not a grouped total.

### Pattern 2: Cross-Filter for Negative Conditions

**When to use:** Finding records that lack a related child — "Accounts with no activity in 60 days," "Contacts without open cases," "Opportunities with no products."

**How it works:**
1. Start a Summary report on the parent object (e.g., Accounts).
2. Add a Cross-Filter: "Accounts WITHOUT Activities."
3. Optionally add a sub-filter on the cross-filter: Activity Date > LAST 60 DAYS.
4. Group by Account Owner to surface ownership for follow-up.

**Why not a formula field:** Formula fields cannot reference child record existence without a roll-up summary field on the parent, which requires a master-detail relationship (`summaryForeignKey` is the "Master-detail field on the child", api_meta 264 L45869). Cross-filters work on any lookup relationship (UNVERIFIED (2026-10-21): the corpus says only that `relatedTableJoinColumn` is "The field from the child object that is used to join the parent", L107826).

### Pattern 3: Custom Report Type for Multi-Object Reporting

**When to use:** You need columns from three or more related objects, or the standard report type uses the wrong join direction.

**How it works:**
1. Go to Setup > Report Types > New Custom Report Type.
2. Set Primary Object (e.g., Accounts).
3. Add related objects in sequence: Opportunities (may or may not have), then Opportunity Products (may or may not have).
4. In the Field Layout, add the specific fields needed from each object. Remove noise fields.
5. Set the CRT to Deployed — `deployed` "Indicates whether the report type is available to users (true) or whether it's still in development (false)" (api_meta 264 L108453-108454). The earlier "~24 hours to appear" figure has no corpus source and was removed.
6. Build the report on this CRT.

**Why not standard types:** Standard types expose a fixed field set and fixed join semantics. A CRT gives control over both.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|-----------|---------------------|--------|
| Flat list for export or audit | Tabular report | No aggregation needed; exports are unlimited rows (UNVERIFIED (2026-10-21): no export row figure in the corpus) |
| Grouped totals by one dimension | Summary report | Single-axis grouping with subtotals |
| Crosstab (rows and columns both grouped) | Matrix report | Two-axis grouping, ideal for quota attainment grids |
| Combining data from two unrelated objects | Joined report (max 5 blocks — UNVERIFIED (2026-10-21)) | "Joins data from different report types storing each report's data in its own block" (api_meta 264 L107391) |
| Records that LACK a related child | Cross-filter with "WITHOUT" | Avoids formula complexity; works on lookup relationships |
| Grouping values into named ranges inline | Bucket field | Report-local; no object-level field change needed |
| KPI across grouped rows (win rate, avg deal size) | Summary formula | Calculates from aggregate values across the group |
| All dashboard viewers see the same data slice | Static dashboard with a named running user | Simple governance; watch for over-sharing risk |
| Each viewer sees their own data | Dynamic dashboard | Secure; limited to 5–10 running users per org edition (UNVERIFIED (2026-10-21): Help only) |
| Scheduled report delivery by email | Report subscription (not dashboard) | Dynamic dashboards cannot be subscribed to (UNVERIFIED (2026-10-21): Help only) |
| Parent records with no matching children | Outer join on CRT leg | An outer join "returns a row even if the joined table doesn't contain a matching value" (api_meta 264 L108493-108494) |
| Parent records ONLY when children exist | Inner join on CRT leg ("must have") | Filters out parents with no matching child record |

---

## Recommended Workflow

1. **Define the business question** — translate the stakeholder ask into: primary object, required fields, grouping dimension, metric (count/sum/formula), and date range. Write it out before touching the UI.
2. **Select the report type** — use a standard report type if it covers the required objects and join semantics. Create a Custom Report Type only when a standard type cannot provide the needed field set or join behavior.
3. **Build the report** — apply filters (use relative date ranges, not hard-coded dates), add groupings, add columns, add bucket fields or summary formulas as needed. Preview with real data before saving.
4. **Validate results** — verify row counts against a known control (SOQL query or list view). Check that filters are not inadvertently excluding records. If counts are off, check CRT join semantics and sharing access before changing filters.
5. **Design the dashboard** — identify 3–5 key components. Match each component type to its purpose (Metric for KPIs, Bar/Column for comparisons, Line for trends, Gauge for quota progress). Set the running user configuration (static vs dynamic).
6. **Configure access and delivery** — assign the report and dashboard to a shared folder with appropriate view/edit permissions. If scheduled delivery is needed, set up a Report Subscription (not a dashboard subscription). Confirm subscription recipients are current employees.
7. **Document and govern** — add a description to the report and dashboard. Record the intended audience, data owner, and refresh cadence. Move reports from private folders to shared folders immediately.

---

## Review Checklist

Run through these before marking work complete:

- [ ] Report type (standard vs custom) is the minimum required to answer the business question — no over-engineering
- [ ] All date filters use relative ranges ("This Quarter," "Last 30 Days") rather than hard-coded dates
- [ ] Groupings produce meaningful subtotals — not a grouping on a high-cardinality field like Email
- [ ] Dashboard running user is set to "Run as logged-in user" unless a static view has been explicitly approved
- [ ] Dashboard filters tested against all components — confirm which components are and are not affected
- [ ] Report and dashboard are in a shared folder, not a private folder
- [ ] Report subscriptions are addressed to named, currently active recipients, and each subscription's running user is confirmed (it defaults to whoever created the subscription, not the report owner — UNVERIFIED (2026-10-21): Help only)
- [ ] CRT join semantics verified — "may or may not have" vs "must have" matches the business intent
- [ ] Row and block limits confirmed — not approaching 2,000 rows in dashboard tables, not exceeding 5 blocks in joined reports (UNVERIFIED (2026-10-21): Help-only limits)
- [ ] No dashboard has more than 20 source report components (UNVERIFIED (2026-10-21): Help-only limit)

---

## Salesforce-Specific Gotchas

1. **Tabular reports cannot drive most dashboard components without a row limit** — Tabular reports return raw rows ("Lists data with no sorting or subtotals", api_meta 264 L107389). A Metric or Chart component requires an aggregated value. If you drop a tabular report as a dashboard source, it will either error or only display as a table. Set a row limit and sort to enable tabular use in dashboards, or convert to a Summary report. UNVERIFIED (2026-10-21): the row-limit rule for dashboard use is not in the corpus.

2. **CRT field layout is not the same as field visibility** — Adding a field to a CRT's field layout makes it available in the report builder, but field-level security still controls whether individual users can see the field's values. A user who cannot read the field in the UI cannot see it in a report either — "Field permissions control the visibility of fields in any part of the app, including related lists, list views, reports, and search results" (secguide 262 L621).

3. **Joined report blocks are independent — they do not join on a common key** — Blocks in a joined report sit side by side but do not perform a SQL-style JOIN on a shared ID. Each block is its own report with its own filters. If you need a true comparison of matched records, use a Summary or Matrix report on a CRT that includes both objects.

4. **Summary formulas can reference PARENTGROUPVAL and PREVGROUPVAL — but only in the correct context** — PREVGROUPVAL returns the value from the previous grouping level (e.g., prior month). PARENTGROUPVAL returns the value from the next-higher grouping level (e.g., the region total when you are viewing a territory row). These functions are only available in Matrix and Summary reports, and they require the referenced grouping level to exist in the report. UNVERIFIED (2026-10-21): the function semantics and the format restriction are Help only; the corpus shows both functions only inside a sample `calculatedFormula` (api_meta 264 L108016-108018).

5. **Dynamic dashboards cannot be subscribed to or scheduled** — A dynamic dashboard (run as logged-in user) refreshes on demand only. You cannot set a nightly refresh schedule or send a subscription email from a dynamic dashboard. If stakeholders need scheduled delivery, build a separate static report subscription alongside the dynamic dashboard. UNVERIFIED (2026-10-21): the claim in this heading is Help only, not in the corpus.

---

## Output Artifacts

| Artifact | Description |
|----------|-------------|
| Report design document | Report type selection, filter logic, grouping structure, summary fields, and bucket field definitions |
| Dashboard component map | Component-to-report mapping, chart type rationale, running user configuration, and filter coverage |
| Folder permission matrix | Which roles or public groups have view/edit access to the report and dashboard folders |
| Subscription configuration | Recipient list, frequency, conditions for conditional subscriptions, and running user confirmation |

---

## Related Skills

- **admin/reports-and-dashboards** — Use for troubleshooting missing or incorrect data in existing reports, diagnosing sharing model impact, and auditing report governance. Use this fundamentals skill for design and first-time build questions.
- **admin/sharing-and-visibility** — Use when report results diverge from expectations because of record-level sharing rules, role hierarchy, or manual shares. The report is functioning correctly — the access model is the issue.
- **admin/permission-sets-vs-profiles** — Use when users cannot open a report folder or see specific fields in a report due to object or field permissions. Not for report filter or chart configuration questions.
- **admin/einstein-analytics-basics** — Use when operational Salesforce Reports and Dashboards are insufficient and CRM Analytics (Einstein Analytics) is being evaluated. NOT for standard reports and dashboards.
