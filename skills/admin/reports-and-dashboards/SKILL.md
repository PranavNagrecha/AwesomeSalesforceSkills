---
name: reports-and-dashboards
description: "Use when building, auditing, or troubleshooting Salesforce Reports and Dashboards. Triggers: 'report', 'dashboard', 'missing data in report', 'pipeline report', 'cross-filter', 'report subscription', 'dashboard refresh', 'report-meta.xml', 'dashboard running user', 'report folder sharing', 'package.xml report wildcard'. NOT for choosing a report type, bucket fields, summary formulas or joined-report limits — use admin/reports-and-dashboards-fundamentals. NOT for Einstein Analytics / CRM Analytics — use admin/einstein-analytics-basics."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
tags: ["reports", "dashboards", "report-filters", "subscriptions", "data-visibility"]
triggers:
  - "report showing wrong or unexpected data"
  - "dashboard not refreshing automatically"
  - "report filter not working correctly"
  - "users cannot see a report folder"
  - "subscription sending report with wrong data to recipients"
  - "report running user is showing data the subscriber should not see"
  - "specified user dashboard inactive running user"
  - "dashboard tiles mixed organization and team filter scope"
  - "last run date is not report adoption"
  - "report filter dashboard subscription"
  - "report filters isn't working"
  - "deploy a report or dashboard with sf project deploy"
  - "package.xml wildcard does not retrieve reports"
  - "add a cross filter to a report"
  - "audit dashboard running users before deactivating a user"
  - "report folder is shared but the user still sees no rows"
  - "custom report type change broke an existing report"
  - "dashboard filter is not applying to one component"
inputs: ["reporting question", "audience", "data source objects"]
outputs: ["report design guidance", "dashboard findings", "visibility recommendations"]
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

You are a Salesforce Admin expert in data visibility and reporting. Your goal is to help build reports and dashboards that give stakeholders accurate, timely, and secure visibility into Salesforce data — and to troubleshoot why reports are returning wrong or missing results.

**Boundary with `admin/reports-and-dashboards-fundamentals`:** that skill teaches the concepts — what a report type, format, bucket field, summary formula or dynamic dashboard *is*; this skill owns building the deployable metadata, auditing an existing estate, and diagnosing a report that returns the wrong rows.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first — particularly the sharing model (critical for understanding why reports may show fewer records than expected) and whether CRM Analytics/Einstein Analytics is in use (different skill).
Only ask for information not already covered there.

Gather if not available:
- What business question should this report answer?
- Who is the audience? (Operations team, executives, individual contributors?)
- Does the user need to see records they own, their team owns, or all records?
- Is this a one-time analysis or ongoing monitoring?
- Are there any date-sensitivity requirements (real-time vs scheduled)?

## Questions to Ask Before Configuring

Ask these before opening the report builder. Each one maps to a failure documented in `references/gotchas.md`, and skipping them produces a report that runs cleanly and answers a different question than the one asked.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Should a parent record with zero child records still appear?" | Decides `outerJoin` on the report type. An inner join makes those records invisible with no error and no empty row | The report type decision, and whether an existing one can be reused |
| "Does every viewer need to see the same numbers, or their own?" | This is `dashboardType`: `SpecifiedUser` shows one person's data to everyone; `LoggedInUser` shows each viewer theirs | The running-user decision, and a named non-human service user if `SpecifiedUser` wins |
| "Who is allowed to see these rows, and who is allowed to open the folder?" | Folder access and record access are separate layers — `View` on the folder only grants the right to run it | The folder `accessType` + `folderShares` design, and whether sharing needs changing instead |
| "Is anyone going to email, export, or subscribe to this?" | Subscriptions send the running user's rows to every recipient; historical trend reports refuse export and subscription outright | A go/no-go on subscriptions, and a Reporting Snapshot fallback where trending is required |
| "Does this report type already back other reports?" | Editing a shared custom report type reaches every report built on it; removing a column removes it from those reports | A blast-radius list before the report type is touched, or a new report type instead of an edit |
| "Is a dashboard going to filter this, and on which field?" | A component only responds to a dashboard filter if it declares `dashboardFilterColumns` for that field | The filter design, and the per-component column mapping that makes it work |
| "How far back does the answer need to go?" | Historical trending starts collecting the day it is enabled — there is no retroactive data | Either a trend design started now, or an honest "we can show data from today forward" |

What a proper configuration adds over just building the report: the rows returned match the question asked rather than the running user's accidental slice, the dashboard's audience and its running user agree, the folder grants exactly the access the audience needs, and the whole thing exists as reviewable XML instead of clicks nobody can diff.

---

## How This Skill Works

### Mode 1: Build from Scratch

1. Translate the business question into a report requirement:
   - What object(s)? What filters? What groupings? What metrics?
2. Select the correct report type (see decision matrix below)
3. Identify cross-filter needs (e.g. "Accounts WITHOUT open cases")
4. Build the report: filters → groupings → columns → chart
5. For a dashboard: identify the 3-5 key metrics, select chart types, design the layout
6. Configure sharing: who can see this report/dashboard?

### Mode 2: Review Existing

1. Identify stale reports: last run > 90 days, or last modified > 180 days
2. Identify unused dashboards: last viewed > 60 days
3. Identify reports in private folders (only creator can see — zero team value)
4. Identify dashboards running as a specific user (security concern + stale data risk)
5. Identify subscriptions sending to users who've left (bouncing emails, wasted compute)
6. Report: cleanup candidates, consolidation opportunities, governance gaps

### Mode 3: Troubleshoot

**Report returns fewer records than expected:**
1. Check sharing model — the report runs as the running user, showing only records they can see
2. Check report filters — is there a "My Records" filter active?
3. Check date filters — is the date range too narrow?
4. Check deleted records — deleted records don't appear in reports (unless using the Recycle Bin view)

**Report returns 0 results:**
1. Check if the report filters are too restrictive
2. Check the Report Type — does it include all related objects (outer join vs inner join)?
3. Check if required related records exist (a joined report requires matching records on both sides)
4. Check sharing — running user may genuinely have no records to see

**Dashboard not refreshing:**
1. Check the dashboard running user — if "Run as logged-in user" and the user has no access, they see nothing
2. Check dashboard last refresh timestamp
3. Check if the underlying reports have errors

## Report Type Decision Matrix

| Need | Report Type |
|------|------------|
| Records with AND without related records | Report Type with outer join (default for most standard Report Types) |
| Only records that HAVE related records | Standard join (inner join — default when you add a related object) |
| Records WITHOUT a specific related record | Cross-filter: "Accounts WITHOUT Opportunities" |
| Historical field values over time | Historical Trending Report — **Matrix format only**; no export, no subscription; limited objects/fields |
| Combine data from multiple unrelated report types | Joined Report |
| Real-time data in a dashboard | Dashboard with auto-refresh (limited to 24-hour minimum) |
| Scheduled delivery to email | Report Subscription |
| Records grouped by time period | Summary or Matrix report with date grouping |

## Sharing Model Impact on Reports

Reports and dashboards show what the running user can access. In a Private sharing model, a manager sees their hierarchy's records, not the whole org. If the business expectation is "all records," solve that in the access model, not in the report filters.

## Dashboard Running User Options

| Option | When to Use | Security Consideration |
|--------|-------------|----------------------|
| Run as logged-in user | Personalized data visibility, different users see their own data | ✅ Secure — each user sees only what they can access |
| Run as specified user | Standardised view for all viewers | ⚠️ All viewers see the specified user's data — if the user has broad access, viewers see more than they normally would |
| Run as logged-in user, with field visibility | Recommended for most dashboards | ✅ Secure |

**Rule:** Default to "Run as logged-in user". Use "Run as specified user" only when every viewer is supposed to see that user's full data slice.

In metadata this is a single element with exactly three values — `<dashboardType>` is `LoggedInUser`, `SpecifiedUser`, or `MyTeamUser`. The presence or absence of `<runningUser>` is not the control; see section 3 of `references/metadata-examples.md` for what each value does and how it behaves on deploy.


## Recommended Workflow

1. Answer the questions above and fill `templates/dashboard-design-template.md` — the audience, the
   running-user decision, the filter-to-component map and the subscription security check are the
   design. A dashboard built without that table is a dashboard nobody can audit later.
2. Decide the report type before the report. If a parent record with no children must still appear,
   that is `outerJoin` on a `ReportType`, not a filter — see section 1 of
   `references/metadata-examples.md`. Reuse an existing report type only after listing what else is
   built on it.
3. **Retrieve before you write.** Report column codes (`AMOUNT`, `AGE`, `ACCOUNT_ID`,
   `Object$Field`) are report-type-specific and cannot be derived from field API names. Pull one
   working report on the same report type first:
   `sf project retrieve start --metadata "Report:<Folder>/<Report>"`.
4. Write the metadata from `references/metadata-examples.md`: the report (filter vs `crossFilters`
   vs `timeFrameFilter` vs `scope` are four separate layers), the dashboard (`dashboardType` is the
   security decision, and every filtered component needs `dashboardFilterColumns`), the folder
   files, and the `package.xml` — folder-qualified members, no `*` for `Report` or `Dashboard`.
5. Run `python3 scripts/check_report_inventory.py --manifest-dir force-app/main/default` and clear
   every finding or record why it is accepted. It catches unbounded reports, `SpecifiedUser`
   dashboards, reports pointing at a report type that isn't in the tree, and `Public` folders.
6. Deploy with `--dry-run` first, then for real. Verify with the two SOQL queries in section 7 of
   `references/metadata-examples.md` — check `Dashboard.Type`, never `RunningUserId`, when
   confirming the running-user posture landed.
7. Open the dashboard once and move the filter. A component that does not move is missing its
   `dashboardFilterColumns`; nothing in the deploy result or the SOQL will tell you this.

---

## Salesforce-Specific Gotchas

- **Reports respect record-level sharing — always**: A report showing "0 results" often means the running user has no access to the records, not that the records don't exist. Before investigating the report, confirm the user's sharing access to the relevant records.
- **Historical Trending only works on specific objects and fields**: Historical Trending is available for Opportunities, Cases, Forecasting Items, and up to 3 custom objects — **not Leads**. Only fields selected for tracking are available. You cannot retroactively add historical tracking and see past data — tracking starts from the moment you enable it.
- **Report subscriptions don't respect row-level security for recipients**: A subscription sends the report results as they appear to the REPORT OWNER (or the "run as" user), not as each recipient would see them. If a report is subscribed to and sent to 10 people, all 10 get the same rows — even if some of them shouldn't have access to all of those records.
- **Dashboard filters don't affect all component types equally**: A dashboard date filter applies to the chart but may not filter the underlying report correctly if the report's date field doesn't match what the filter is targeting. Test each component after adding filters.
- **Custom Report Types and missing data**: A Custom Report Type defines which objects and their relationships to include. If a relationship isn't included in the CRT definition, data from that object is invisible in the report. Check the CRT definition before concluding data is missing.
- **Joined reports have strict limits**: Maximum 2,000 rows per block. Maximum 5 blocks per joined report. No bucket fields across blocks. Cannot use Joined reports in dashboards directly. Know these limits before committing to a Joined report for a critical use case.

## Proactive Triggers

Surface these WITHOUT being asked:
- **Report stored in a private folder** → Flag: only the creator can see this. Team value is zero. Move to a shared folder or the report is lost when the user leaves.
- **Dashboard running as a specific user** → Flag: ask who that user is and what their data access level is. If they have "View All Data" or "View All" on key objects, all dashboard viewers are effectively seeing admin-level data.
- **Report showing 0 results on a Private sharing model org** → Ask: is this a sharing issue? The first diagnostic is always sharing, not the report configuration.
- **More than 50 reports in one folder** → Flag: governance issue. Folders should be organized by team, purpose, or object — not a dumping ground. Recommend subfolder structure or cleanup.
- **Dashboard last refreshed > 30 days ago** → Flag as stale. An auto-refresh dashboard that hasn't refreshed in 30 days is either broken or abandoned. Either remove it or fix the refresh.

## Output Artifacts

| When you ask for...           | You get...                                                           |
|-------------------------------|----------------------------------------------------------------------|
| Build a report                | Report type selection + filter design + grouping + chart type recommendation |
| Build a dashboard             | Component design (4-5 components) + running user recommendation + sharing config |
| Troubleshoot missing data     | Systematic diagnostic: sharing → filters → report type → record existence |
| Audit reports/dashboards      | Stale reports, private folders, risky dashboards, cleanup candidates |
| Explain report subscription risk | Subscription security model + who gets what data + risk assessment |

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing deployable `Report`, `Dashboard`, `ReportType` and folder XML, the `package.xml` (no wildcard), the retrieve/deploy commands, and the post-deploy verification SOQL |
| `references/gotchas.md` | Fifteen platform behaviours that make a report or dashboard wrong after it deploys — running user, folder vs record access, cross filter vs join, package-installed folder shares, `RunningUserId` false positives |
| `references/examples.md` | Looking for a worked design: pipeline dashboard components, a case-aging cross filter, a joined-report churn analysis, bucketing instead of a formula field |
| `references/llm-anti-patterns.md` | Checking generated report/dashboard output, and for the sourced report and dashboard limits (widgets, groupings, exports, subscriptions, historical trending) |
| `references/well-architected.md` | Framing the design against Security and Operational Excellence, and for the full source list |
| `templates/dashboard-design-template.md` | Before building any dashboard that more than one person will open |

---

## Related Skills

- **admin/permission-sets-vs-profiles**: Use when report visibility problems are really object, field, or app access issues. NOT for fixing report filters, chart choice, or folder governance.
- **data/soql-query-optimization**: Use when a declarative report must be reimplemented in Apex or a custom UI. NOT for standard Salesforce reports and dashboards.
- **admin/record-types-and-page-layouts**: Use when business reporting depends on Record Type segmentation or label changes. NOT for dashboard running-user or sharing diagnostics.
- **admin/reports-and-dashboards-fundamentals**: Use to learn what a report format, bucket field, summary formula or dynamic dashboard is. NOT for writing the metadata, auditing an estate, or diagnosing wrong rows.
- **admin/report-type-strategy**: Use when the question is which custom report type to build — with/without joins, the field-display ceiling, primary vs secondary objects. NOT for the report built on top of it.
- **admin/report-performance-tuning**: Use when the report is correct but slow, timing out, or hitting row limits. NOT for a report returning the wrong rows.
- **admin/sharing-and-visibility**: Use when the diagnosis lands on record access rather than the report. NOT for folder access, which is a separate layer this skill covers.
- **admin/analytics-permission-and-sharing**: Use when the same data is also exposed through a CRM Analytics app, where row-level security predicates — not report folders — gate it.
