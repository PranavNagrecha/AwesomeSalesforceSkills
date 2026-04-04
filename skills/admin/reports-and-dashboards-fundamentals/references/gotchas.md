# Gotchas — Reports and Dashboards Fundamentals

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Tabular Reports Cannot Drive Metric or Chart Dashboard Components Without a Row Limit

**What happens:** An admin adds a Tabular report as the source for a Metric or Bar Chart dashboard component. Salesforce either shows an error ("Source report is not compatible with this component") or displays no data. The admin assumes the report is broken.

**When it occurs:** Tabular reports return raw rows with no aggregation. Dashboard Metric and Chart components require an aggregated value (a sum, count, or grouped subtotal). Without aggregation, there is nothing for the component to display. The only exception is the Table component, which can display rows from a Tabular report — but only if a row limit is set.

**How to avoid:** For Metric, Chart, Gauge, and Funnel dashboard components, always use a Summary or Matrix report as the source. If a flat list must appear in the dashboard, use a Tabular report with a row limit (e.g., Top 10 sorted by Amount descending) and add it as a Table component.

---

## Gotcha 2: Dashboard Filters Do Not Affect All Components — Silently

**What happens:** An admin adds a "Close Date" filter to a dashboard. Some components update when the filter is changed; others do not move. The admin assumes those components are broken or ignores the discrepancy. Stakeholders trust data that is not actually filtered.

**When it occurs:** A dashboard filter only affects components whose source report contains a filter on the same field AND whose filter is mapped to the dashboard filter. If a source report does not have a Close Date filter at all, or if the dashboard filter is not explicitly mapped to that report's filter, the component ignores the dashboard filter entirely. There is no visual indicator on the dashboard that a given component is not affected by a filter.

**How to avoid:** After adding a dashboard filter, test every component individually by applying the filter and verifying each component's row count or values change as expected. Document which components are and are not affected by each filter in the dashboard description. Consider adding a footer note to the dashboard or using a Text component to flag this explicitly.

---

## Gotcha 3: Custom Report Type Joins Are Set at CRT Creation — Changing Them Requires a New CRT

**What happens:** A CRT was created with an inner join ("must have related records") on the Activities leg. Reports built on this CRT silently exclude any parent record with no activities. The admin adds filters and changes sort orders trying to find the "missing" records. The records are not missing — they were excluded by the CRT join type.

**When it occurs:** Whenever a CRT is built with "A records must have related B records" on any leg. Common examples: Accounts must have Contacts, Opportunities must have Opportunity Line Items, Campaigns must have Campaign Members. Any parent record without a matching child is excluded from every report built on that CRT.

**How to avoid:** When creating a CRT, default to "may or may not have related records" (outer join) on every leg unless the business requirement explicitly requires excluding parentless records. If an existing CRT has the wrong join type, you cannot change it — you must create a new CRT with the correct join semantics and migrate reports to the new type.

---

## Gotcha 4: Report Subscriptions Run as the Report Owner, Not the Subscriber

**What happens:** An admin sets up a report subscription and distributes it to 20 users. All 20 recipients receive the same rows — the rows visible to the report owner at the time the subscription runs. A user in the Eastern region receives deals owned by users in the Western region because the report owner is the VP of Sales with View All Data.

**When it occurs:** Report subscriptions always execute as the user who owns the report (or the specified running user, if different). The subscription sends the same result set to every recipient regardless of each recipient's individual record access. This is by design — Salesforce does not re-run the report once per recipient.

**How to avoid:** Do not use report subscriptions to send personalized data to individual contributors. Subscriptions are appropriate for aggregate metrics that all recipients are meant to see (e.g., "total open cases this week" sent to the whole support team). For personalized delivery, users must subscribe themselves to the report using their own running user, or use a dynamic dashboard with on-demand refresh instead.

---

## Gotcha 5: The 2,000-Row Display Limit Is Not the Same as the Export Limit

**What happens:** A report shown in the browser is truncated at 2,000 rows. An analyst concludes the data set is small and builds decisions on that sample. They do not know that the actual result set contains 14,000 rows.

**When it occurs:** The Salesforce report builder and dashboard UI display a maximum of 2,000 rows for performance reasons. There is no visual warning that says "results truncated." The row count shown at the bottom reflects all rows found, but the visible rows in the grid stop at 2,000.

**How to avoid:** For any analysis that might exceed 2,000 rows, always export to CSV or use the Analytics API / Apex `Reports.ReportManager.runReport()` to retrieve the full dataset. Treat the 2,000-row UI view as a preview, not a complete result. For dashboard Table components, the 2,000-row limit applies per component — if more records are needed, consider Apex or a CRM Analytics dataset instead.

---

## Gotcha 6: Bucket Field "Blank" Values Fall into an Implicit Other Category

**What happens:** A bucket field is defined with three ranges: Small (0–10k), Mid (10k–100k), Enterprise (100k+). A report includes opportunities with a blank Amount field. Those records appear in the report under an unlabeled "other" bucket that the admin did not define. Totals do not add up to the expected numbers.

**When it occurs:** Bucket fields have an implicit "Other" category that captures any value not matched by the defined ranges, including null/blank values. If the field being bucketed can be blank (e.g., Amount is not required), blank records will silently fall into "Other" unless the admin explicitly defines a bucket for blanks.

**How to avoid:** When creating a bucket field on a non-required field, always check the "Treat blank values as zeros" option if the field is numeric, or explicitly add a bucket for blank values. Review the "Other" bucket count in the preview to determine whether blank records are being captured there.
