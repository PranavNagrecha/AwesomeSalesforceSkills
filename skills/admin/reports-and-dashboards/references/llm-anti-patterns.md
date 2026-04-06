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

**Why it happens:** LLMs add components without considering limits. Dashboards support a maximum of 20 components. Reports support up to 250 groupings and 2,000 rows in dashboard charts. Report subscriptions have per-user limits. Exceeding limits causes silent truncation or errors.

**Correct pattern:**

```
Key limits for reports and dashboards:
- Dashboard components: max 20 per dashboard.
- Dashboard columns: 3 (9 components per column for a 3-column layout).
- Report rows in dashboard chart: max 2,000.
- Report groupings: max 3 for Summary, 2 row + 2 column for Matrix.
- Report subscriptions: max 5 per user (Enterprise edition).
- Joined report blocks: max 5 blocks.
- Dashboard refresh: auto-refresh every 24 hours minimum.
- Report export rows: 2,000 for formatted, no limit for Excel export.

Design for the limits:
- Prioritize the top 10-15 metrics per dashboard.
- Create multiple focused dashboards instead of one overloaded dashboard.
- Use report-level drill-down for detail, not dashboard-level complexity.
```

**Detection hint:** If the output adds more than 20 dashboard components or creates reports with more than 3 grouping levels, limits will be exceeded. Count components and grouping levels.
