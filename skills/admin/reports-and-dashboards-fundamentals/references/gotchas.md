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

## Gotcha 4: Each Subscription Has Its Own Running User — Defaulting to Whoever Created It, Not the Report Owner

**What happens:** An admin sets up a report subscription and adds 20 recipients. All 20 receive the same rows — the rows visible to *that subscription's* running user, which defaults to the admin who created it. A rep in the Eastern region receives Western-region deals because the admin has View All Data. The team expected Salesforce to re-run the report once per recipient. It does not.

**When it occurs:** Every Lightning subscription carries its own running user, defaulting to **Me** — the person creating the subscription — not the report's owner and not each recipient. Two users subscribing to the same report produce two subscriptions with two different running users. Salesforce Help: "Recipients see the same report data as the person running the report. It's possible that they see more or less data than they normally see in Salesforce." Pointing a subscription elsewhere is permission-gated: **Subscribe to Reports: Set Running User** to choose another person, **Subscribe to Reports: Add Recipients** to send to anyone but yourself, and **Subscribe to Reports: Send to Groups and Roles** to target roles, roles-and-subordinates, or public groups. Plain **Subscribe to Reports** only lets a user subscribe themselves.

**How to avoid:** For personalized delivery, have each user create their own subscription so their own running user applies. Reserve **Set Running User** for aggregate metrics every recipient is cleared to see, and audit who holds that permission — it is the one that actually leaks rows. Then size the delivery against the real ceilings: an attachment is capped at 15,000 rows, 30 columns, and 3 MB; up to 5 conditions can gate whether the email sends at all; each user gets 15 report and 15 dashboard subscriptions on Unlimited Edition and 7 on other editions; and the org can schedule 500 report and 500 dashboard subscriptions in any given hour.

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

---

## Gotcha 7: A Report Referenced by Any Dashboard Cannot Be Deleted

**What happens:** A cleanup plan says "delete every report not run in 12 months." The deletes fail partway through. In the UI the action is blocked; through the Analytics REST API it returns HTTP 403 with `The report can't be deleted because there are one or more dashboards referencing it.` The team treats a designed guard rail as an unexpected outage and stops the cleanup.

**When it occurs:** Any time a dashboard component still points at the report — including dashboards sitting in folders the person running the cleanup cannot see. Report deletion is not a leaf operation; every dashboard in the org is a potential reference holder, so a usage report on "last run date" alone will never predict which deletes succeed.

**How to avoid:** Make the platform's refusal the enforcement point rather than the surprise. Run a deprecate-then-delete cycle: rename the report with a `DEPRECATED_` prefix, leave it in place for one full reporting cycle, and delete only after nobody complains — at which point a successful delete is itself proof no dashboard depends on it. Deleted reports land in the Recycle Bin, so an over-eager delete is recoverable within the retention window.

---

## Gotcha 8: Folder Names Are Unique Across Reports AND Dashboards, and Subfolders Need Their Own Permission

**What happens:** An admin building out a folder tree tries to create a dashboard folder named "Sales Ops" alongside an existing *report* folder of the same name, and the save fails. Later, a delegated admin with full access to every report in the tree still cannot create the subfolders the design calls for.

**When it occurs:** The folder namespace is shared across both asset types — per Salesforce Help, "You can't have more than one report or dashboard folder with the same name as another report or dashboard folder." Separately, creating a subfolder requires the **Create Report Folders** user permission (or **Create Dashboard Folders** for dashboards) *plus* manage access on the root folder of that tree. Access to the reports inside the folder grants nothing here. Up to 3 subfolder levels are allowed.

**How to avoid:** Prefix folder names by asset type ("RPT — Sales Ops", "DSH — Sales Ops") so the shared namespace never collides, and settle tree depth up front against the 3-level ceiling rather than discovering it mid-migration. When delegating folder maintenance, grant **Create Report Folders** / **Create Dashboard Folders** plus Manage access on the one specific root folder — not blanket "Manage Reports in Public Folders", which grants manage access to every public report folder in the org.
