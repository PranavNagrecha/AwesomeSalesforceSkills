# LLM Anti-Patterns — Reports and Dashboards

Common mistakes AI coding assistants make when generating or advising on Salesforce Reports and Dashboards.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Ignoring the Running User setting on dashboards

**What the LLM generates:** "Create the dashboard and share it with the sales team. Everyone will see their own data."

**Why it happens:** LLMs assume dashboards respect the viewer's data access. By default, a dashboard runs as the "Running User" (often the dashboard creator). All viewers see the SAME data -- the Running User's data, not their own. To show viewer-specific data, the dashboard must use "Dynamic Dashboards" (where each viewer sees their own data).

**Correct pattern:**

```
Dashboard Running User options:
1. Specified Running User (default):
   - All viewers see the Running User's data.
   - Use for: executive dashboards where everyone should see the same numbers.
   - Risk: if Running User is a System Admin, viewers see ALL data.

2. Dynamic Dashboard ("Run as logged-in user"):
   - Each viewer sees data based on their own sharing and visibility.
   - Use for: team dashboards where reps should see only their pipeline.
   - Limit: available on Enterprise+ editions, limited number per org.

3. Running User = specific user with broad access:
   - Use for: dashboards that need cross-team visibility.
   - Clearly label who the Running User is.
```

**Detection hint:** If the output creates a dashboard without configuring the Running User or mentioning Dynamic Dashboards, viewers may see the wrong data. Search for `Running User` or `dynamic dashboard` in the dashboard configuration.

---

## Anti-Pattern 2: Choosing the wrong report type (Tabular vs Summary vs Matrix vs Joined)

**What the LLM generates:** "Create a tabular report to show Opportunity pipeline by Stage and Owner."

**Why it happens:** LLMs default to the simplest report type. A pipeline report grouped by Stage and Owner requires a Summary or Matrix report type, not Tabular. Tabular reports are flat lists with no grouping. Summary reports group by rows. Matrix reports group by rows AND columns. The LLM does not match the grouping requirement to the report type.

**Correct pattern:**

```
Report type selection:
- Tabular: flat list, no grouping. Use for data exports or simple lists.
  Cannot be used in dashboards.
- Summary: groups by 1-3 row groupings. Use for most business reports.
  Example: Opportunities grouped by Stage.
- Matrix: groups by rows AND columns. Use for cross-tabulation.
  Example: Opportunities by Stage (rows) AND Owner (columns).
- Joined: combines multiple report blocks (different report types)
  in one view. Use for comparing related datasets.

Key rule: Tabular reports CANNOT be used as dashboard components.
Only Summary, Matrix, and Joined reports can power dashboard charts.
```

**Detection hint:** If the output uses a Tabular report for a dashboard component or for data that needs grouping, the report type is wrong. Search for `Tabular` combined with `dashboard` or `group by`.

---

## Anti-Pattern 3: Not accounting for data visibility differences between report viewers

**What the LLM generates:** "Share the report with the entire sales org. They will all see the same results."

**Why it happens:** LLMs treat reports as static data. Reports respect the running user's sharing and visibility settings. Two users running the same report may see different records based on their OWD, role hierarchy, and sharing rules. An admin sees all records; a sales rep sees only their team's records.

**Correct pattern:**

```
Report data visibility:
1. Reports respect the viewer's record access (OWD, role hierarchy,
   sharing rules, manual sharing).
2. If the report is in a shared folder, users can run it but see
   only THEIR data based on their access level.
3. If the report needs to show cross-team data:
   - Use a dashboard with a specific Running User who has broad access.
   - Or create a reporting-specific sharing rule to grant read access.
4. Report subscriptions: the subscribed user's data access determines
   what data appears in the emailed report.
5. "Report on All" vs "Report on My" — scope filters affect results.
```

**Detection hint:** If the output says all users will "see the same data" in a report without considering sharing, the visibility difference is being ignored. Search for `sharing`, `visibility`, or `record access` in the report sharing instructions.

---

## Anti-Pattern 4: Using cross-filters incorrectly or not at all

**What the LLM generates:** "Create a report showing Accounts without open Cases. Filter by Case Status != 'Open'."

**Why it happens:** LLMs use field-level filters when the requirement is a cross-filter. Filtering `Case Status != 'Open'` shows Accounts that have Cases with a status other than Open -- it does not show Accounts with NO open Cases. Cross-filters ("Accounts WITHOUT Cases where Status = Open") are the correct mechanism.

**Correct pattern:**

```
Cross-filters vs field filters:
- Field filter: filters rows within the report results.
  "Show Cases where Status != Open" → shows non-open Cases.
- Cross-filter: filters the parent object based on child existence.
  "Accounts WITHOUT Cases" → shows Accounts with zero Cases.
  "Accounts WITH Cases where Status = Open" → shows Accounts
  that have at least one open Case.

To add a cross-filter:
1. In the report builder, click Filters → Add Cross Filter.
2. Select: [Parent Object] with/without [Child Object].
3. Optionally add sub-filters on the child object.
```

**Detection hint:** If the output uses a field filter (!=) when the requirement is "records WITHOUT related records," a cross-filter is needed. Search for `without` in the requirement and verify a `Cross Filter` is used, not a field filter.

---

## Anti-Pattern 5: Not considering report and dashboard limits

**What the LLM generates:** "Add 25 components to the dashboard to show all the key metrics."

**Why it happens:** LLMs add components without considering limits, and they reach for whichever report number they remember most strongly — usually 2,000, which is the *on-screen row display cap* and gets misapplied to exports, groupings and chart capacity. Exceeding real limits causes silent truncation or errors.

**Correct pattern:**

```
Key limits for reports and dashboards:
- Dashboard widgets: max 25 per dashboard (of which max 20 charts/tables,
  max 3 images, max 25 rich text widgets).
- Dashboard layout: Lightning uses a flexible 12- or 9-column grid
  (the fixed "3 columns" figure is Salesforce Classic only).
- Dashboard filters: max 5 per dashboard, max 50 values per filter.
- Dashboard widget groupings: a widget can calculate up to 1,000 groupings.
- Report chart groups (Lightning): max 2,000 groups.
- Report groupings: max 3 for Summary, 2 row + 2 column for Matrix.
- Report rows displayed on screen: 2,000. This is a DISPLAY cap, not an
  export cap — do not reuse this number anywhere else.
- Joined report blocks: max 5 blocks, max 100 columns per block;
  joined report export / printable view: 20,000 rows.
- Subscriptions: 500 report + 500 dashboard subscriptions per org per hour,
  max 500 recipients per subscription.
- Report export rows:
    * Formatted Report (.xlsx only): 100,000 rows x 100 columns for tabular
      and summary reports; 2,000 rows x 100 columns for MATRIX reports.
    * Details Only as .xlsx: 100,000 rows x 100 columns.
    * Details Only as .xls or .csv: no Salesforce row cap — bounded by the
      receiving spreadsheet tool (1,048,576 rows in modern Excel).
    * Long/rich text fields truncate to 255 characters in every export.

Design for the limits:
- Prioritize the top 10-15 metrics per dashboard.
- Create multiple focused dashboards instead of one overloaded dashboard.
- Use report-level drill-down for detail, not dashboard-level complexity.
```

**Detection hint:** If the output adds more than 20 chart/table widgets to a
dashboard, or more than 3 grouping levels to a summary report, the limit is
exceeded. Separately, grep the output for `2,000` / `2000`: that number is
correct ONLY for (a) the on-screen row display cap, (b) Lightning report chart
groups, and (c) a *matrix* Formatted Report export. If it appears attached to
"export rows" generally, to "groupings", or to "rows in a dashboard chart",
the number has been relabelled onto the wrong dimension — the export figure is
100,000 and the dashboard-widget grouping figure is 1,000.

---

## Anti-Pattern 6: Inventing the Historical Trend Reporting matrix

**What the LLM generates:** "Enable Historical Trending on Leads to trend
lead status week over week. Historical Trending supports Opportunities,
Cases, Leads, Forecasts and up to 3 custom objects; you can track Date,
Date/Time, Number, Currency, Percent, Checkbox and Picklist fields, and keep
up to 8 date snapshots per record."

**Why it happens:** Historical Trend Reporting sits next to two adjacent
features with different rules — Field History Tracking (which *does* work on
Leads, and carries its own per-object trackable-field allowance) and Reporting
Snapshots (which work on any object). The model blends the three, and the
blend is what makes the output dangerous: every element is a real Salesforce
fact, just filed under the wrong feature. The snapshot-date count is the
clearest case — small field-tracking allowances are the numbers most available
in memory near this topic, and one of them gets re-attached to the
snapshot-date dimension, where the documented figure is 5. Leads are added
because lead-funnel trending is such a common request that the feature *feels*
like it must support it.

**Correct pattern:**

```
Historical Trend Reporting (Setup -> Historical Trending):
- Objects: Opportunities, Cases, Forecasting Items, and up to 3 custom
  objects. Leads are NOT supported.
- Trackable field types: Number, Currency, Date, Picklist, Lookup.
  Date/Time, Percent and Checkbox are NOT trackable. Formula fields are
  not supported at all.
- Snapshot dates per historical trend report: up to 5.
- Historical filters per report: up to 4.
- Fields per historical trend report: up to 100.
- Retention: previous 3 months plus the current month (12 months for
  Opportunity history with Pipeline Inspection historical trending on).
- Storage: up to 5 million rows of trending data per object; collection
  stops above that, with an admin alert at 70%.
- Format: MATRIX only. The summary format is not supported, and Lightning
  gives you charts but no tabular view of a trend report. In Lightning the
  snapshot date must be the primary row grouping.
- Not available at all: export, subscriptions, row-limit filters, and
  dynamic exchange rates (a static rate is used instead).
- No retroactive data: tracking starts the day you enable it.

For lead-funnel trending, use a Reporting Snapshot into a custom object,
or Field History Tracking plus a history report — not Historical Trending.
```

**Detection hint:** Grep the output for `Historical Trend`. If the same
sentence also contains `Lead`, `Date/Time`, `Percent`, `Checkbox`, or a
snapshot-date count other than `5`, it is wrong. A second mechanical check:
`Forecasting Items` must be present in any supported-object list — an answer
that says "Forecasts" but omits Cases or includes Leads was generated from
memory of Field History Tracking, not from the Historical Trending doc. Third
check: if the answer summary-formats, subscribes to, or exports a historical
trend report, it has designed something the platform rejects — the Analytics
REST API returns error 501 telling you to change the format to matrix.

---

## Anti-Pattern 7: Writing report/dashboard package.xml with folder labels and wildcards

**What the LLM generates:** a `Report` section containing `<members>*</members>`,
or an explicit member written with the folder's display label:
`<members>Sales Team Reports/Pipeline by Stage</members>`.

**Why it happens:** almost every other metadata type accepts the wildcard, and
the label is the only folder name the model has ever seen (it is what the UI
shows). Reports and dashboards are the exception on both counts, so a manifest
that looks completely ordinary retrieves nothing and deploys nothing.

**Correct pattern:**

```
package.xml members for Report and Dashboard:
- A member is <folder developer name>/<item developer name>. The names in
  package.xml must be developer names, never report or dashboard titles.
- No wildcard: neither Report nor Dashboard accepts <members>*</members>.
  The Metadata API guide states the restriction separately for each type.
  Enumerate every member explicitly.
- To enumerate, call listMetadata() with type = ReportFolder (or
  DashboardFolder) and folder = *, take the folder fullNames it returns,
  then call listMetadata() again with type = Report (or Dashboard) and
  folder = each of those names.
- A nested folder referenced on its own needs a trailing slash:
  <members>TopLevel/SubLevel/</members>. Omitting it fails with
  "Entity of type 'Report' named 'TopLevel/SubLevel' cannot be found".
```

**Detection hint:** grep the manifest for `<members>*</members>` beneath a
`Report` or `Dashboard` type, and for any report/dashboard member containing a
space — a space almost always means a label was pasted where a developer name
belongs. Both are wrong by construction, before the org is ever contacted.

---

## Anti-Pattern: Treating LastRunDate as Adoption

**What the LLM generates:** "Delete every report with LastRunDate older than 12 months" or "this dashboard is used weekly because LastRunDate is recent."

**Why it happens:** LastRunDate updates on dashboard refresh, subscriptions, and API runs — not only a human opening the report.

**Correct pattern:** Use `LastViewedDate` (per user) for adoption. Inventory dashboard `runningUser` / `SpecifiedUser` before offboarding. Do not equate a scheduled refresh with a reader.

**Detection hint:** Cleanup plans keyed only on `LastRunDate`; no mention of dashboard references or running-user hygiene.

---

## Anti-Pattern: Mixing `organization` and `team` Tiles Without Saying So

**What the LLM generates:** A six-component "pipeline health" dashboard cloned from mixed personal and org reports.

**Correct pattern:** Every component's `filterScope` matches the dashboard's audience. Titles that compare counts must share a scope. Sharing, report scope, and dashboard running user are three layers.

**Detection hint:** Dashboard XML with both `<filterScope>organization</filterScope>` and `<filterScope>team</filterScope>` (or `mine`) in neighbouring components.
