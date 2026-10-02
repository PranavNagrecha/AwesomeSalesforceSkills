# Gotchas: Reports and Dashboards

---

## Reports Respect Record-Level Sharing — "Missing" Records Are Usually a Sharing Issue

**What happens:** A VP asks the admin to build a pipeline report. The report shows 50 opportunities. The VP says "that's not right — we have hundreds of opportunities." The admin checks the report, the filters look correct. The issue: the VP's role in the hierarchy only covers their direct reports' records. The hundreds of other opportunities are owned by teams outside their hierarchy. The report is correct — the sharing model is showing them exactly what they're supposed to see.

**When it bites you:** Every time a stakeholder says "my report is missing data." Before investigating the report configuration, always check: "Does the running user have access to the records they expect to see?"

**How to diagnose:**
1. Log in as or simulate the running user
2. Go to the relevant object's list view
3. Select "All [Objects]" (requires View All) — if the count differs from the running user's view, it's a sharing issue
4. Run the same report as a System Administrator — if you see more records, it's a sharing issue, not a report issue

**How to address:**
- Sharing issue confirmed → review sharing model, don't patch the report
- Report was expected to show all records → review whether the user needs elevated access, or if the dashboard should "Run as specified user" with appropriate access

---

## Historical Trending: Only Works on Specific Objects and Fields, and Only Forward

**What happens:** An admin asks: "Can you build a report showing how many open cases we had each day for the last 6 months?" Historical Trending would answer this. But Historical Trending wasn't enabled on Cases 6 months ago. Enabling it now starts capturing data from today. There's no retroactive data. The admin tells the VP there's 6 months of historical trend data — there isn't.

**When it bites you:** Requests for historical trend reports on objects where Historical Trending wasn't set up in advance.

**What Historical Trending supports:**
- Objects: Opportunities, Cases, Forecasting Items, up to 3 custom objects. **Leads are not supported** — there is no Lead entry in the Historical Trending setup list.
- Field types: Number, Currency, Date, Picklist, Lookup. Date/Time, Percent and Checkbox are **not** trackable.
- Lookback: the previous 3 months plus the current month (rolling window). Opportunity history extends to 12 months when Historical Trending is enabled in Pipeline Inspection.
- Up to **5 historical snapshot dates** per historical trend report, and up to 4 historical filters per report. Each report can contain up to 100 fields, and up to 5 million rows of trending data are stored per object.

**How to avoid it:**
- Enable Historical Trending proactively on any object where trend data may be needed
- Set it up before business requests trend reports — not after
- Communicate clearly to stakeholders: "We can show trend data from [date enabled] forward"

---

## Historical Trend Reports Are Matrix-Only, and Can't Be Exported or Subscribed To

**What happens:** An admin builds the trend request as a Summary report grouped by owner, schedules it as a weekly subscription, and promises the VP a spreadsheet. All three steps are unsupported. Pulled through the Analytics REST API the format failure comes back as error 501: `Historical trend data is unavailable in the report format requested. Change the report format to matrix and try again.`

**When it bites you:** Any historical trend requirement phrased like an ordinary report request — "trend it by rep, email it every Monday, export it to Excel."

**What the feature refuses (verbatim from the limits doc):**
- "The summary report format isn't supported." — build it as **Matrix**.
- "Historical trending reports can't be exported."
- "You can't subscribe to historical trend reports."
- "Row limit filters aren't supported." and "Formula fields aren't supported."
- "Dynamic exchange rates aren't supported. When you run a historical trend report, it uses a static exchange rate, which could be outdated."
- "Historical trend reporting with charts is supported in Lightning Experience, but tabular views of historical trend reports aren't available."
- In Lightning Experience "you must set the snapshot date as the primary row grouping" — any other primary grouping is rejected.

**How to avoid it:** If the requirement includes an export, an email subscription, a formula column, or a row limit, historical trending is the wrong feature. Use a Reporting Snapshot into a custom object and report on that custom object normally — it has none of these restrictions.

---

## Report Subscriptions Don't Respect Row-Level Security for Recipients

**What happens:** An admin creates a report of all Opportunities over $1M. They set up a subscription to send this report every Monday to 15 sales reps. Each rep only has access to their own opportunities via the sharing model. But the subscription sends the full report — all 1M+ opportunities — because it runs as the report owner (a Manager with "View All"). Each rep receives everyone else's pipeline data in their inbox.

**When it bites you:** Any time a report subscription is configured to send to users who have narrower access than the report owner.

**How to avoid it:**
- Before scheduling a subscription, explicitly check: does the report contain records the recipients shouldn't see?
- If recipients should see different data: DON'T use subscriptions — have each user run the report themselves ("Run as logged-in user" applies when users run manually)
- Secure alternative: build a dashboard with "Run as logged-in user" that each rep visits individually
- If a subscription is necessary: ensure the report's report type and filters produce only data appropriate for ALL recipients

---

## Dashboard Filters Don't Always Filter All Component Types

**What happens:** An admin adds a date range filter to a dashboard. The filter appears at the top and looks like it applies to all components. But one component (a matrix report) doesn't update when the filter changes. The underlying report uses a different date field than what the dashboard filter is targeting.

**When it bites you:** Complex dashboards with multiple report types where different components use different date fields.

**How to avoid it:**
- After adding any dashboard filter, test EVERY component by changing the filter value and verifying the component updates
- Dashboard filters only work when the underlying report field matches what the filter targets
- Document which components a filter applies to in the dashboard description

---

## Custom Report Types: Missing Data Due to Join Type

**What happens:** An admin creates a Custom Report Type: Account → Contacts → Opportunities. The report returns only Accounts that have at least one Contact AND at least one Opportunity. An Account with no Contacts but with Opportunities is invisible. The admin built an "inner join" report thinking they had "all accounts with opportunities."

**When it bites you:** Any Custom Report Type that chains multiple relationships. The default join type may exclude records the user expects to see.

**The join types:**
- "A record must have related B records" → inner join (default) — only records WITH the relationship appear
- "A records may or may not have related B records" → outer join — records appear even without the relationship

**How to avoid it:**
- When creating a Custom Report Type, explicitly choose the join type for each related object
- Ask: "Should records without [related object] still appear in the report?" If yes → outer join
- Test with a record you know has no related records — does it appear?

---

## SpecifiedUser Dashboards Die With the Running User

**What happens:** Dashboard `dashboardType` is `SpecifiedUser`. Every component runs in that user's security context. Deactivate the user and refresh/subscriptions fail silently or with "the running user is inactive." Viewers see stale stored results. This is the highest-ratio operational failure on reporting-heavy orgs.

**When it bites you:** Small firms where one admin is the SpecifiedUser on every dashboard; PE/search-fund shops after a departure.

**How to avoid it:**
- Prefer `LoggedInUser` (dynamic) when the audience should see *their* data.
- If SpecifiedUser is required (one shared "ops" view), the running user must be a **named integration/service user that never leaves**, not a human.
- Inventory `runningUser` on every dashboard before offboarding. Re-point or convert to LoggedInUser in the same change as deactivation.
- Do not treat LastRunDate as adoption — dashboard refresh and auditors inflate it. `LastViewedDate` is per-user and is the honest signal.

---

## Mixed Report `scope` on One Dashboard Silently Undercounts

**What happens:** `scope` lives on the *report*, not on the dashboard component, so neighbouring tiles can sit on reports with different scopes with no UI cue. The Metadata API guide defines `scope` as "the scope of data on which you run the report" — whether it runs against all opportunities, ones you own, or ones your team owns — and notes that the valid values depend on the report type (for Accounts reports: `MyAccounts`, `MyTeamsAccounts`, `AllAccounts`; the guide's own sample report uses `organization`). Readers compare 2,400 against 13,000 as if they were the same population.

**When it bites you:** Pipeline health / KPI dashboards cloned from a personal report.

**How to avoid it:** Open each `*.report-meta.xml` behind the dashboard and compare their `<scope>` values before shipping. Org-wide tiles cannot sit next to owner- or team-scoped tiles unless the title says so. Record sharing, report `scope`, and dashboard `dashboardType` are **three independent layers**, and none of them is visible from the dashboard XML alone.

---

## Licence-Gated Columns Look Like a Broken Report

**What happens:** Same report type, same API version, same FLS. Analytics REST returns ~40 columns with a Marketing Cloud / ListEmail PSL and ~20 without. Unlicensed runs look empty. Teams write "the org cannot report on unique opens."

**When it bites you:** Marketing / email engagement reports; B2BMA / CRMA seats; Data Cloud reports on an unconfigured tenant.

**How to avoid it:** Check **entitlement** before "field missing." Never conclude capability from one login. Production vs sandbox can differ on which PSLs are assigned.

---

## Zero Dashboard Filters Produce Clone Farms

**What happens:** Twelve identical 6-component dashboards instead of one dashboard with `dashboardFilters`. Year-stamped and person-named copies follow. Each clone is 6 more source reports to keep alive, and the twelfth copy silently drifts from the first.

**When it bites you:** Any request phrased as "the same dashboard but for <region / year / rep>", and any org where the requester has Manage on the folder and can clone without asking. The clone is faster to produce than the filter, so it wins by default unless someone stops it.

**How to avoid it:** Filter-first. A clone per company / year / person is a smell. Salesforce-shipped dashboards often already demonstrate filters — copy that, not the 12 folders.


---

## A Deployed Dashboard With a Bad `runningUser` Silently Becomes Yours

**What happens:** `runningUser` takes a *username*. The Metadata API guide states that when you deploy a dashboard and the value in that field "is not defined or does not correspond to a valid user, the field is populated with the username of the user performing the deployment." There is no error, no warning, and no line in the deploy result. A `SpecifiedUser` dashboard promoted from sandbox — where the running user was `ops@acme.com.uat` — lands in production running as the release engineer, who typically has the broadest access in the org.

**When it bites you:** Every sandbox-to-production promotion where usernames carry a sandbox suffix. Also any deploy from a repo where the running user left the company between the commit and the release.

**How to avoid it:**
- Treat `runningUser` as an environment-specific value, like a Named Credential endpoint. Substitute it per target org rather than committing one username to a shared branch.
- After every deploy of a `SpecifiedUser` dashboard, verify in the org: `SELECT DeveloperName, Type, RunningUserId FROM Dashboard WHERE FolderName = '<folder>'`. Compare `RunningUserId` to the user you intended, not to the XML you deployed.
- Prefer `LoggedInUser`, which needs no `runningUser` element at all and therefore cannot drift.

---

## `RunningUserId` Is Populated on Dashboards That Don't Have a Running User

**What happens:** An admin writes an audit query to find every dashboard that bypasses viewer access: `WHERE RunningUserId != null`. It returns essentially every dashboard in the org. The Object Reference explains why — for a dashboard created in Lightning Experience and configured to run as the viewing user, `RunningUserId` returns the user ID of the *dashboard creator*; for one created in Salesforce Classic and set to run as the logged-in user, it returns the *last specified running user*. The field is never null in practice, so the query has no discriminating power.

**When it bites you:** Any governance sweep, offboarding checklist, or security review that inventories dashboards through SOQL rather than through metadata.

**How to avoid it:**
- Filter on `Dashboard.Type` instead. It is a restricted picklist with exactly three values — `SpecifiedUser`, `LoggedInUser`, `MyTeamUser` — and only `SpecifiedUser` bypasses the viewer's own access.
- In metadata, the equivalent check is `<dashboardType>`, not the presence of `<runningUser>`.
- A dashboard audit that reports "N dashboards have a running user" without splitting by `Type` has produced a number, not a finding.

---

## A Dashboard Filter Silently Skips Any Component That Doesn't Declare Its Column

**What happens:** The filter renders at the top of the dashboard, its picklist works, and most tiles respond. One tile never moves. The cause is structural rather than a field mismatch: the Metadata API guide states that "each report-based component must have a dashboard filter column that defines the column that the filter applies to." A component whose XML lacks the matching `<dashboardFilterColumns><column>` entry is not filtered — it renders its full, unfiltered result next to filtered neighbours.

**When it bites you:** Components added to an existing dashboard after the filter was created, and components cloned from a dashboard that had no filters. The result reads as a data discrepancy, not a configuration gap.

**How to avoid it:**
- Every filtered component needs one `dashboardFilterColumns` entry per dashboard filter it must respond to. Three filters on a dashboard means three entries on each participating component.
- After adding a filter or a component, change the filter value and confirm each tile's number actually changes. A tile that holds still is the failure signal.
- In review, diff the count of `<dashboardFilters>` blocks against the count of `<dashboardFilterColumns>` entries inside each `<components>` block.

---

## `accessType: Public` on a Report Folder Includes Portal Users

**What happens:** An admin sets a report folder to `Public`, meaning "everyone at the company." The Metadata API guide defines the four `accessType` values precisely: `Shared` is "accessible only by the specified set of users"; `Public` is "accessible by all users, **including portal users**"; `PublicInternal` is "accessible by all users, excluding portal users"; `Hidden` is hidden from all. `Public` is the widest setting in the platform, and in an org with an Experience Cloud site or a Customer Portal it exposes the folder to external users.

**When it bites you:** Orgs that enable a partner or customer portal *after* the reporting estate was built. The folder setting doesn't change; its blast radius does.

**How to avoid it:**
- `PublicInternal` is the setting that matches what most orgs mean by "public." Reserve `Public` for content that is genuinely acceptable to a partner or customer.
- `publicFolderAccess` (`ReadOnly` / `ReadWrite`) only takes effect when `accessType` is `Public` — setting it on a `Shared` folder does nothing and can create a false sense that access was constrained.
- Sweep `*.reportFolder-meta.xml` and `*.dashboardFolder-meta.xml` for `<accessType>Public</accessType>` before enabling any portal.

---

## Folder Sharing Is Dropped During Package Installation

**What happens:** A team ships a reporting bundle as a managed or unlocked package with the folder shares carefully modelled in `folderShares`. In the subscriber org the folders arrive and the reports arrive; the sharing does not. The Metadata API guide carries this as an explicit Important note: "During package installation, FolderShare for DashboardFolder and ReportFolder is ignored."

**When it bites you:** ISV packages, unlocked-package delivery of reporting content, and any "reporting starter pack" installed rather than deployed.

**How to avoid it:**
- Split the delivery: package the reports, dashboards and report types; apply folder sharing as a separate post-install metadata deploy or a documented Setup step.
- A direct `sf project deploy` of the same folder XML *does* carry `folderShares` — the exclusion is specific to package **installation**. Know which mechanism the customer will use.
- Add a post-install verification step that reads folder access back, rather than assuming it landed.

---

## An Outer Join and a `with` Cross Filter Cancel Each Other Out

**What happens:** An admin builds a report type with `<outerJoin>true</outerJoin>` so that Accounts with no Cases still appear, then adds a cross filter — `operation` `with`, `relatedTable` `Case` — to see accounts that have open cases. The childless Accounts the outer join was built to include are removed again by the cross filter. The report type change looks like it did nothing.

**When it bites you:** Reports assembled by two people, or over two sessions — someone fixes the join, someone else adds the cross filter, and neither sees the other's layer.

**How to avoid it:**
- `outerJoin` and `crossFilters` are independent mechanisms: the join decides which rows the report type can *produce*; the cross filter decides which parents survive based on child existence. They stack, they don't merge.
- "Records WITHOUT related records" is `operation` `without` on the cross filter — not an outer join, and not a `!=` field filter. An outer join alone returns both populations mixed together.
- When the requirement is "with or without," add the outer join and add **no** cross filter on that relationship.

---

## `baseObject` on a Report Type Is Permanent, and the Join Rules Are Directional

**What happens:** A report type is created on the wrong primary object — Contacts when the requirement was Accounts. The guide is explicit: `baseObject` is required and "You can't edit this field after initial creation." The only remedy is a new report type and the migration of every report built on the old one. Two further constraints bite when a team tries to widen an existing report type instead: a maximum of **four objects** can be joined in one custom report type, and once an outer join appears in a join sequence, "an inner join isn't allowed if there has been an outer join earlier in the join sequence."

**When it bites you:** Report types that grow over years, and any attempt to "just add one more object" to a four-object type.

**How to avoid it:**
- Settle the primary object against the question the report answers — the object whose records must appear even when nothing else exists — before creating the report type.
- Order the joins so that any required inner joins come before any outer join. If the required order can't satisfy that, the design needs two report types, not one.
- Before editing a shared report type, list what depends on it: `SELECT Id, Name, FolderName FROM Report` and match on the report type in the retrieved XML. Removing a column from a report type removes it from every report that displays it.

---

## `Report` and `Dashboard` Reject the Wildcard; `ReportType` Accepts It

**What happens:** One `package.xml` contains all three types. The `ReportType` section uses `<members>*</members>` and works. The engineer copies the pattern to the `Report` and `Dashboard` sections, the deploy succeeds, and zero reports move. The Metadata API guide states the restriction separately for each type: `Report`, `Dashboard`, `Folder` and `FolderShare` do not support the wildcard; `ReportType` does. A wildcard on an unsupported type is not an error — it just matches nothing.

**When it bites you:** Hand-written manifests, and CI pipelines that generate a manifest by templating one pattern across every type in a change.

**How to avoid it:**
- Enumerate `Report` and `Dashboard` members explicitly, folder-qualified and using developer names: `<members>Revenue_Ops/Open_Cases_By_Owner</members>`.
- Build the list with two passes of `listMetadata()` — first `ReportFolder` (or `DashboardFolder`) with `folder` = `*` to get folder names, then `Report` (or `Dashboard`) once per folder.
- Treat a report or dashboard member containing a space as a bug: the manifest wants developer names, and a space almost always means a label was pasted in.

---

## F-49: A Report `description` Over 255 Characters Fails Deploy

**What happens:** A report's `<description>` carries a build note or a UNVERIFIED marker in
addition to its stated purpose, and the deploy is rejected outright: `Value too long for field:
Description maximum length is:255`. Nothing in the Metadata API Developer Guide's `Report` field
table states this limit — it was proven only by a live `sf project deploy start --dry-run`
against the case-onboarding M5-S01 build (`reports/MOCK-DEPLOY-M5.md`, API 67.0).

**When it occurs:** Any report description used as a scratch pad for build notes, TODOs, or a
runbook pointer — exactly the kind of thing a UNVERIFIED-marker workflow is tempted to write
there instead of into `deploy-order.md` or a config workbook.

**How to avoid it:**
- Keep `<description>` a one- or two-sentence statement of what the report is for. Notes about
  what's incomplete or deferred belong in the build's own deploy-order/runbook file, not the
  metadata.
- Run `python3 scripts/check_report_inventory.py --manifest-dir <dir>` before deploying — RPT-DESC-01
  fails the run (ERROR) at 256+ characters; RPT-DESC-02 is an advisory INFO at 235+ characters
  that never fails the run, even under `--strict`.

---

## F-50: A Guessed `reportType` Or Grouping Column Fails Only At Deploy, With No Offline Signal

**What happens:** Three separate guesses on the same report all pass local review and all fail
live, each pointing to the next: `<reportType>Cases</reportType>` (looks like the obvious API
name for the standard Case report type) → `invalid report type`. Switching to the correct
`CaseList` moves the failure to the grouping: `<groupingsDown><field>USERS.NAME</field>` (copied
from the Metadata API guide's own — unrelated — Report sample) → `Grouping: Invalid value
specified: USERS.NAME`. Switching the grouping to `OWNER` moves the failure again: `PRIORITY` was
also listed as a `<columns>` entry → `You can't include groupings in the selected columns list:
PRIORITY`. All three values were marked UNVERIFIED in this skill's own examples before being
proven wrong live (`reports/MOCK-DEPLOY-M5.md`, F-50).

**When it occurs:** Any report on a standard object where the report type API name or a
grouping/column code is typed from familiarity with the object's field API names, rather than
retrieved. Standard report type API names are not the object name — `CaseList`, not `Cases` (and
by the same pattern, expect `AccountList`, `OpportunityList` rather than the bare object name;
confirm each one, don't extrapolate the suffix). A field cannot be both a `groupingsDown`/
`groupingsAcross` entry and a `columns` entry on the same report — pick one.

**How to avoid it:**
- Retrieve one working report on the target report type before writing any XML (this skill's own
  Recommended Workflow step 3). Read the `reportType`, `groupingsDown`/`groupingsAcross`, and
  `columns` values off that retrieve — don't infer them from field API names or from an unrelated
  sample.
- Run `python3 scripts/check_report_inventory.py --manifest-dir <dir>` before deploying:
  RPT-TYPE-01 (WARN) flags a `reportType` this project has already proven invalid (`Cases`) and
  suggests the proven replacement; RPT-GRP-01 (ERROR) flags any field present in both a
  grouping and `<columns>`.
- A `--dry-run` deploy is not optional verification here — the checker's known-invalid list only
  grows by what has actually been proven live; a guess that hasn't been tried yet will pass the
  checker and still fail the org.

---

## F-51: A Report Column Code Can Be Un-Guessable, Not Just Wrong

**What happens:** A Case report needs an `IsEscalated = true` filter. Five plausible column-code
candidates — `ESCALATED`, `IS_ESCALATED`, `CASES.ESCALATED`, `ISESCALATED`, `CASE_ESCALATED` —
are each rejected live with `filters-criteriaItems-column: Invalid value specified`
(`reports/MOCK-DEPLOY-M5.md`, F-51). No cited skill or guide states the correct code, and probing
by pattern has run out of plausible guesses.

**When it occurs:** Any filter, grouping, or column on a checkbox or non-obvious field where the
report column code doesn't follow the `FIELD_NAME` pattern seen elsewhere in the same report type
— checkbox fields in particular are a common miss, since their column code is not reliably the
upper-cased field name.

**How to avoid it:**
- Don't keep guessing. This skill's own rule is to retrieve a working report on the same report
  type and read the code off it (Recommended Workflow step 3) — that is the only reliable source
  for a code that resists pattern-guessing.
- When no existing report already uses the field and a retrieve isn't available in the moment,
  ship the report **without** that criterion and record it as a runbook step: deploy first, then
  either (a) add the filter in the report builder UI and let it write the code, or (b) build the
  filter once by hand, retrieve that report, and copy the code into source for next time.
  Deploying an honestly incomplete filter beats deploying a guessed column code that silently
  narrows or breaks the report.
- `python3 scripts/check_report_inventory.py` flags this pattern generically: RPT-COL-01 (INFO)
  fires on any `criteriaItems`/`columns` code that isn't one of the report's own grouping fields
  or in its small set of already-confirmed codes — a nudge to retrieve, not a verdict on
  right-or-wrong, since column codes are report-type-specific and this cannot be settled offline.

---

## N4-F-03: A Chart Dashboard Component Without `<sortBy>` Fails Deploy, Though the Guide Never Requires It

**What happens:** A validate-only deploy to org `sfskills-dev` (2026-10-02T17:53Z, northwind-sales
M4-S02, `reports/MOCK-DEPLOY-M4.md` run 1) refused `Dashboard Enterprise_Sales/Enterprise_Pipeline`
with this message, verbatim:

> Chart dashboard components require the sortBy attribute

The refused component was a `Column` chart with a `groupingColumn`, `useReportChart` `false`,
and no `<sortBy>`. The Metadata API Developer Guide (v67.0, Summer '26, `DashboardComponent`)
describes `sortBy` only as "The sort option for the dashboard component" and never marks it
required. Every chart in the guide's own Dashboard samples does carry one
(`<sortBy>RowLabelAscending</sortBy>`). Run 2 (18:00:02Z) accepted the added `sortBy`. It then
refused the same component again with "Chart dashboard components require the chartAxisRange
attribute" (N4-F-04). The guide does not mark `chartAxisRange` required either. It describes the
field as "A manual or automatic axis range for bar or line charts", yet the org demanded it on a
`Column` chart.

**When it occurs:** Any hand-written chart component. A chart here is a `componentType` that
contains Bar, Column, Line, Pie, Donut, Funnel or Scatter. From the guide's enumeration that is:
`Bar`, `BarGrouped`, `BarStacked`, `BarStacked100`, `Column`, `ColumnGrouped`, `ColumnLine`,
`ColumnLineGrouped`, `ColumnLineStacked`, `ColumnLineStacked100`, `ColumnStacked`,
`ColumnStacked100`, `Donut`, `Funnel`, `Line`, `LineCumulative`, `LineGrouped`,
`LineGroupedCumulative`, `Pie`, `Scatter` and `ScatterGrouped`. `Metric`, `Table`, `Gauge` and
`FlexTable` are not charts. The defect reads as optional because the field table has no
"Required." and because alphabetical element order puts `sortBy` far below `componentType`.

**How to avoid it:**
- Give every chart component both `<sortBy>` (`RowLabelAscending`, `RowLabelDescending`,
  `RowValueAscending` or `RowValueDescending`, from the `DashboardComponentFilter` enumeration)
  and `<chartAxisRange>`. Better still, copy the component from a retrieve of a working dashboard.
- Run `python3 scripts/check_report_inventory.py --manifest-dir <dir>`. RPT-DASH-SORT-01 (HIGH)
  flags a chart component with no `<sortBy>`, in classic `<components>` and in grid
  `<dashboardComponent>` alike. The checker does **not** flag a missing `chartAxisRange` yet.
- Still UNVERIFIED (2026-10-02), so do not rely on them:
  - The guide says a component with groupings stores its sort in `groupingSortProperties` from
    API 46.0, "otherwise, it is stored in the sortBy field". It is unproven whether
    `groupingSortProperties` alone satisfies the org; the refused component had a grouping and
    the org still asked for `sortBy`.
  - It is unproven whether `useReportChart` `true` exempts a component. The checker fires either
    way.
  - `chartAxisRange` casing. The `DashboardComponent` field table lists `auto` / `manual`. The
    `ChartRangeType` enumeration and every guide sample write `Auto` / `Manual`, which is what
    `references/metadata-examples.md` uses. The org has not yet judged either form.
  - `isAutoSelectFromReport` vs `autoselectColumnsFromReport`. The guide's `chartSummary` row
    says it is "Required if isAutoSelectFromReport is set to false". Neither name has its own row
    in the field table. The guide's grid-layout sample writes `<autoselectColumnsFromReport>`.
  - `summaryAxisRange` is not a dashboard field. It belongs to the `Report` `chart` element,
    where the guide marks it "Required" for bar, line and column charts. The report example now
    carries it. No org has confirmed that requirement yet.

---

## N4-F-04 / RPT-DASH-AXIS-01: The Org Names One Missing Chart Attribute Per Run

**What happens:** northwind-sales M4 run 1 refused a `Column` dashboard component for a missing `<sortBy>`; run 2, with `sortBy` present, refused the same component: "Chart dashboard components require the chartAxisRange attribute" (org-verified 2026-10-02). The guide marks neither as required; every sample carries both. The skill's own § 3 example carries both too — the builder misread it as a different component.

**How to avoid:** a chart component carries `<sortBy>` and `<chartAxisRange>` (`Auto` is the casing the samples and the org accept). The checker now flags both (RPT-DASH-SORT-01, RPT-DASH-AXIS-01). Copy the whole component block from § 3, not one element.

## N4-F-05: A Custom Report Type's Record-Type Column Is The Lookup's Relationship Name Alone

**What happens:** three forms were tried for an Opportunity record-type column on a custom report type. `<field>RecordTypeId</field>` — "Could not find field RecordTypeId in table Opportunity". `<field>RecordType.Name</field>` — "Could not find field Name in table Record Type". `<field>RecordType</field>` with `<table>Opportunity</table>` — accepted (org-verified 2026-10-02). The guide's only lookup-column sample (`obj_lookup__c.Id` / `.Name`) misleads here; a read-only retrieve of twelve custom report types in the validating org found no example to copy. The matching report column code is `Opportunity$RecordType`.

**How to avoid:** name a record-type column by the lookup's relationship name, nothing appended. Filter values on it: UNVERIFIED (2026-10-02) whether the label or the developer name is matched — an empty report, not a failed deploy, is the symptom.

## N4-F-06: A Report On A New Custom Report Type Cannot Be Validated In The Same Deployment

**What happens:** with the report type accepted in the same package, the report still fails checkOnly with "invalid report type", and a dashboard on that report fails with "no Report named … found" (org-verified 2026-10-02). The type does not exist when the report is validated.

**How to avoid:** deploy the ReportType first, then the Report and Dashboard. A validate-only loop can never show the second half green; the gate accepts it on the checker, the manual tests and the type's own validation, and the runbook orders the deploy. This is the same split M4-S01's column-code probe needs, so plan it once.
