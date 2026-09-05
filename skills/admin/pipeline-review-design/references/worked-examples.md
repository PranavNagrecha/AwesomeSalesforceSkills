# Worked Examples — a weekly pipeline review for a B2B SaaS sales org

One realistic scenario, carried end to end. Every block below is an artefact you can copy,
adapt, and hand to the person or agent named in the last section.

**The org.** B2B SaaS, new-logo motion. 18 AEs across 3 managers, one Sales Director.
Average cycle 45 days, quarterly quota, fiscal year = calendar year. Collaborative Forecasting
is on with one Opportunity-sourced forecast type. Pipeline Inspection **is** licensed, which
matters for one reason only in this pack: it is what makes `Opportunity.AgeInDays` and
`Opportunity.LastStageChangeInDays` exist as queryable, reportable fields
(object_reference.txt:192275–192282, 192715–192724). Everything else here is licence-free.

The review is 45 minutes, every Monday, per manager. It is not a status meeting — it exists to
produce four decisions: what moves to Commit, what gets a rescue plan, what gets pushed, and
what gets closed lost.

---

## 1. The review agenda

| # | Block | Min | Artefact read | Owner | Decision produced |
|---|---|---|---|---|---|
| 1 | Coverage | 5 | `Weekly_Pipeline_Review` dashboard, Coverage tile | Revenue Ops Analyst | Whether the quarter needs new pipeline or better conversion |
| 2 | Week-over-week movement | 5 | Dashboard, Commit-by-week component | Sales Manager | Whether last week's commit call held |
| 3 | Stale deals | 10 | `Stale Deals` list view, sorted by days in stage desc | Sales Manager | Rescue plan, push, or close-lost — one per deal, out loud |
| 4 | Slippage | 5 | `Pipeline by Stage` report, Push Count column | Sales Manager | Which deals get a manager-owned close plan |
| 5 | Stage conversion (monthly) | 10 | Conversion report, first review of the month only | Revenue Ops Analyst | Which stage gate is leaking, and who owns fixing it |
| 6 | Commit call | 10 | Dashboard, forecast-category roll-up component | Sales Manager | The number the manager submits |

Rules that make the agenda work, and that nothing in Setup can enforce for you:

- Deals are updated **before** the meeting, never in it. A review that edits records is a data-entry session with an audience.
- A deal discussed in block 3 or 4 leaves with a named owner and a date, or it leaves as Closed Lost.
- Block 5 runs monthly. Weekly conversion rates on an 18-rep team are noise.

---

## 2. Metric definitions mapped to Opportunity fields

This table is the heart of the pack. Each row is a number someone will say out loud; each row
names the field that produces it and the way it lies to you.

| Metric | Definition | Field / formula | What breaks it |
|---|---|---|---|
| **Coverage ratio** | Open `Amount` with `CloseDate` in the current fiscal quarter ÷ team quota for that quarter | `SUM(Amount)` where `NOT IsClosed` ÷ `Quota_For_Period__c` | `Amount` is unwritable on deals that have products: "Any attempt to update this field, if the record has products, will be ignored" (object_reference.txt:192287–192292). A review that asks a rep to "adjust the amount" changes nothing on those deals |
| **Weighted pipeline** | Coverage, weighted by confidence | `ExpectedRevenue` = `Amount` × `Probability`, read-only (object_reference.txt:192401–192408) | `Probability` is reset by `StageName` on every stage change (object_reference.txt:192893–192904). Last week's manual probability is gone the moment the rep advances the deal |
| **Stage conversion** | Deals entering stage N+1 this quarter ÷ deals entering stage N | Grouped count on `StageName` | `OpportunityHistory` is not a stage-history table — see `admin/opportunity-management` `references/gotchas.md` Gotcha 12 before you build this from history rows |
| **Slippage** | Open deals whose `CloseDate` has left a calendar month at least once | `PushCount` (object_reference.txt:192865–192873) | Counts **calendar-month** pushes only: "moving a close date from April to May counts as one push, but moving from April 1 to April 30 doesn't count", and "the total is not decreased when the close date is moved in" |
| **Stale deals** | Open deals whose `StageName` has not changed in > 15 days | `LastStageChangeInDays` (object_reference.txt:192715–192724) | Falls back to `AgeInDays` when `LastStageChangeDate` is null — a deal that has never been re-staged reports its record age, not zero. See `references/gotchas.md` Gotcha 6 |
| **Forecast-category roll-up** | Open `Amount` summed per `ForecastCategoryName` for the quarter | `ForecastCategoryName`: Best Case, Closed, Commit, Most Likely, Omitted, Pipeline (object_reference.txt:192483–192497) | `Omitted` deals are excluded from the roll-up by design. `ForecastCategory` is a *different* value set (`BestCase`, `Closed`, `Forecast`, `MostLikely`, `Omitted`, `Pipeline` — object_reference.txt:192452–192481) and cannot be written at all |

The 15-day stale threshold is derived, not chosen: it is one third of the org's 45-day average
cycle, so a deal that has burned a third of the cycle without moving surfaces before it is
half-dead. Re-derive it whenever the cycle length changes.

---

## 3. The pipeline-review spec

`review-pack/pipeline-review.yaml` — this is the file `scripts/check_pipeline_review_design.py`
lints, and it is the contract between the metric table above and the XML below.

```yaml
object: Opportunity
cadence: Weekly
meeting_length_minutes: 45
forecast_period: "Current fiscal quarter"
motion: "New logo — B2B SaaS, 45-day average cycle"

roles:
  - role: "Sales Manager"
    responsibility: "Runs the agenda and owns the commit call"
  - role: "Account Executive"
    responsibility: "Updates own deals before the meeting, never during it"
  - role: "Revenue Ops Analyst"
    responsibility: "Owns this spec, the report pack and the field definitions"
  - role: "Sales Ops Admin"
    responsibility: "Owns the validation rules and the list views the review depends on"

fields:
  - api_name: Name
    report_column: OPPORTUNITY_NAME
    list_view_column: NAME
  - api_name: StageName
    report_column: STAGE_NAME
    list_view_column: STAGE_NAME
  - api_name: Amount
    report_column: AMOUNT
    list_view_column: AMOUNT
  - api_name: CloseDate
    report_column: CLOSE_DATE
    list_view_column: CLOSE_DATE
  - api_name: ForecastCategoryName
    report_column: FORECAST_CATEGORY_NAME
    list_view_column: FORECAST_CATEGORY_NAME
  - api_name: LastStageChangeInDays
    report_column: LAST_STAGE_CHANGE_IN_DAYS
    list_view_column: LAST_STAGE_CHANGE_IN_DAYS
  - api_name: PushCount
    report_column: PUSH_COUNT
    list_view_column: PUSH_COUNT
  - api_name: IsClosed
    list_view_column: IsClosed
  - api_name: NextStep
    report_column: NEXT_STEP
    list_view_column: NEXT_STEP
  - api_name: OwnerId
    report_column: USERS.NAME
    list_view_column: OWNER_ID
  - api_name: Quota_For_Period__c
    report_column: Quota_For_Period__c

metrics:
  - id: coverage_ratio
    definition: "Open Amount with CloseDate in the current fiscal quarter, divided by the team quota for that quarter."
    source: "Amount / Quota_For_Period__c"
    owner: "Revenue Ops Analyst"
    target: ">= 3.0x"
    reviewed_when: "Opening five minutes"
  - id: stage_conversion
    definition: "Count of deals that entered stage N+1 this quarter divided by count that entered stage N."
    source: "StageName"
    owner: "Revenue Ops Analyst"
    target: "Proposal to Closed Won >= 35%"
    reviewed_when: "Monthly, first review of the month"
  - id: slippage
    definition: "Open deals whose CloseDate has been pushed out of a calendar month at least once."
    source: "PushCount"
    owner: "Sales Manager"
    target: "< 20% of open count"
    reviewed_when: "Deal-by-deal block"
  - id: stale_deals
    definition: "Open deals whose Stage has not changed in more than 15 days."
    source: "LastStageChangeInDays"
    owner: "Sales Manager"
    target: "< 15% of open count"
    reviewed_when: "Deal-by-deal block"
  - id: forecast_rollup
    definition: "Open Amount summed per ForecastCategoryName for the current fiscal quarter."
    source: "ForecastCategoryName"
    owner: "Sales Manager"
    target: "Commit within 10% of prior-week Commit"
    reviewed_when: "Closing five minutes"

hygiene_rules:
  - id: close_date_in_past
    intent: "An open deal may not carry a CloseDate earlier than today."
    enforcement: "ValidationRule"
    owner: "Sales Ops Admin"
  - id: amount_required_from_proposal
    intent: "Amount must be populated once the deal reaches Proposal."
    enforcement: "ValidationRule"
    owner: "Sales Ops Admin"
  - id: next_step_required_when_open
    intent: "NextStep must be non-blank on any open deal closing in the next 90 days."
    enforcement: "ValidationRule"
    owner: "Sales Ops Admin"

artifacts:
  reports:
    - "Revenue_Ops/Pipeline_By_Stage"
  dashboards:
    - "Revenue_Ops/Weekly_Pipeline_Review"
  list_views:
    - "Opportunity.Stale_Deals"
```

Lint it before anything else:

```bash
python3 skills/admin/pipeline-review-design/scripts/check_pipeline_review_design.py \
    --manifest-dir force-app/main/default
```

The checker refuses a metric with no owner or no target, a duplicate metric id, a metric whose
`source` names a field the spec never declared, a Report column or ListView filter that the spec
never declared, and a Report XML that is not well-formed. It exits 1 on any of those.

---

## 4. Report — open pipeline by stage, with a deal-size bucket and a fiscal-quarter filter

`force-app/main/default/reports/Revenue_Ops/Pipeline_By_Stage.report-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Report xmlns="http://soap.sforce.com/2006/04/metadata">
    <buckets>
        <bucketType>number</bucketType>
        <developerName>BucketField_DealSize</developerName>
        <masterLabel>Deal Size</masterLabel>
        <nullTreatment>z</nullTreatment>
        <sourceColumnName>AMOUNT</sourceColumnName>
        <values>
            <sourceValues>
                <to>25000</to>
            </sourceValues>
            <value>Velocity</value>
        </values>
        <values>
            <sourceValues>
                <from>25000</from>
                <to>150000</to>
            </sourceValues>
            <value>Mid-Market</value>
        </values>
        <values>
            <sourceValues>
                <from>150000</from>
            </sourceValues>
            <value>Enterprise</value>
        </values>
    </buckets>
    <chart>
        <chartSummaries>
            <aggregate>Sum</aggregate>
            <axisBinding>y</axisBinding>
            <column>AMOUNT</column>
        </chartSummaries>
        <chartType>HorizontalBar</chartType>
        <groupingColumn>STAGE_NAME</groupingColumn>
        <legendPosition>Bottom</legendPosition>
        <location>CHART_TOP</location>
        <size>Medium</size>
    </chart>
    <columns>
        <field>OPPORTUNITY_NAME</field>
    </columns>
    <columns>
        <field>USERS.NAME</field>
    </columns>
    <columns>
        <aggregateTypes>Sum</aggregateTypes>
        <field>AMOUNT</field>
    </columns>
    <columns>
        <field>BucketField_DealSize</field>
    </columns>
    <columns>
        <field>CLOSE_DATE</field>
    </columns>
    <columns>
        <field>LAST_STAGE_CHANGE_IN_DAYS</field>
    </columns>
    <columns>
        <field>PUSH_COUNT</field>
    </columns>
    <columns>
        <field>NEXT_STEP</field>
    </columns>
    <description>Open pipeline for the current fiscal quarter, grouped by stage and bucketed by deal size. Owned by Revenue Ops.</description>
    <filter>
        <booleanFilter>1 AND 2</booleanFilter>
        <criteriaItems>
            <column>FORECAST_CATEGORY_NAME</column>
            <operator>notEqual</operator>
            <value>Omitted</value>
        </criteriaItems>
        <criteriaItems>
            <column>AMOUNT</column>
            <operator>greaterThan</operator>
            <value>0</value>
        </criteriaItems>
    </filter>
    <format>Summary</format>
    <groupingsDown>
        <field>STAGE_NAME</field>
        <sortOrder>Asc</sortOrder>
    </groupingsDown>
    <name>Pipeline by Stage</name>
    <reportType>Opportunity</reportType>
    <scope>organization</scope>
    <showDetails>true</showDetails>
    <showGrandTotal>true</showGrandTotal>
    <showSubTotals>true</showSubTotals>
    <timeFrameFilter>
        <dateColumn>CLOSE_DATE</dateColumn>
        <interval>INTERVAL_CURRENT</interval>
    </timeFrameFilter>
</Report>
```

> **UNVERIFIED (2026-09-05) — retrieve the column codes before you deploy this.** The codes
> `AMOUNT`, `CLOSE_DATE`, `OPPORTUNITY_NAME` and `USERS.NAME` are taken from the Metadata API
> guide's own examples (api_meta.txt:104019–104031 and api_meta.txt:104626 for
> `AMOUNT`, api_meta.txt:104568 for `OPPORTUNITY_NAME`, api_meta.txt:105098–105099 and
> api_meta.txt:105573 for `CLOSE_DATE`, api_meta.txt:105589 for `USERS.NAME`), and `Opportunity`
> as a `reportType` value is from the guide's joined-report sample (api_meta.txt:105570). The
> codes `STAGE_NAME`, `FORECAST_CATEGORY_NAME`, `LAST_STAGE_CHANGE_IN_DAYS`, `PUSH_COUNT` and
> `NEXT_STEP` are **not published anywhere in the guide** — they are the shape the other codes
> follow, not a documented list. Retrieve one working report on the `Opportunity` report type
> from the target org, read the real codes off it, and correct both this file and the spec's
> `report_column` values. The spec exists so that correction is one edit in one place.

### How to read it

- **The bucket, not a formula field.** `BucketField_DealSize` segments `AMOUNT` inside the
  report, so no custom field is created and the bands can change per quarter without a deploy.
  `developerName` "must be of the format `BucketField_name`" (api_meta.txt:104302–104305) and is
  what `<columns><field>` and `<chart><groupingColumn>` reference. Numeric buckets take `to` only
  on the first band and `from` only on the last; `nullTreatment` `z` treats an empty `Amount` as
  zero, which is why hygiene rule `amount_required_from_proposal` exists — otherwise blank-Amount
  deals land silently in the Velocity band.
- **`timeFrameFilter` is a separate element from `filter`,** with its own required `dateColumn`
  and `interval` (api_meta.txt:105097–105105). `INTERVAL_CURRENT` is the **current fiscal
  quarter**; `INTERVAL_CURRENTQ` is the **current calendar quarter** (api_meta.txt:105164,
  api_meta.txt:105226). This org's fiscal year is calendar-aligned so both happen to agree —
  the moment it is not, the wrong one disagrees with the Forecasts page every quarter.
- **`booleanFilter` numbers the `criteriaItems` in document order from 1.** Reordering the two
  `criteriaItems` blocks silently rewires `1 AND 2`.
- **`Omitted` is excluded here on purpose.** Filtering it out at the report keeps the report's
  total equal to the forecast roll-up. Never remap a stage out of `Omitted` to make deals visible
  — that changes the forecast, not the report.
- `scope` is a third visibility layer on top of record sharing and the dashboard running user.
  For report-folder sharing, the running-user question and the `scope` value set, read
  `admin/reports-and-dashboards` `references/metadata-examples.md` rather than duplicating it here.
- If this report has to become a custom report type (adding Quota or a related object), the
  `baseObject` and join rules are in `admin/report-type-strategy`.

---

## 5. Dashboard — the four things the manager looks at

`force-app/main/default/dashboards/Revenue_Ops/Weekly_Pipeline_Review.dashboard-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Dashboard xmlns="http://soap.sforce.com/2006/04/metadata">
    <backgroundEndColor>#FFFFFF</backgroundEndColor>
    <backgroundFadeDirection>Diagonal</backgroundFadeDirection>
    <backgroundStartColor>#FFFFFF</backgroundStartColor>
    <chartTheme>light</chartTheme>
    <colorPalette>colorSafe</colorPalette>
    <dashboardFilters>
        <dashboardFilterOptions>
            <operator>equals</operator>
            <values>Enterprise</values>
        </dashboardFilterOptions>
        <dashboardFilterOptions>
            <operator>equals</operator>
            <values>Mid-Market</values>
        </dashboardFilterOptions>
        <dashboardFilterOptions>
            <operator>equals</operator>
            <values>Velocity</values>
        </dashboardFilterOptions>
        <name>Deal Size</name>
    </dashboardFilters>
    <dashboardType>MyTeamUser</dashboardType>
    <description>Weekly pipeline review pack. Managers view their own team; the Director views from a subordinate's point of view.</description>
    <leftSection>
        <columnSize>Medium</columnSize>
        <components>
            <componentType>Metric</componentType>
            <dashboardFilterColumns>
                <column>BucketField_DealSize</column>
            </dashboardFilterColumns>
            <displayUnits>Auto</displayUnits>
            <drillEnabled>false</drillEnabled>
            <header>Coverage</header>
            <metricLabel>Open pipeline, current fiscal quarter</metricLabel>
            <report>Revenue_Ops/Pipeline_By_Stage</report>
            <title>Coverage</title>
            <useReportChart>false</useReportChart>
        </components>
        <components>
            <chartAxisRange>Auto</chartAxisRange>
            <componentType>Bar</componentType>
            <dashboardFilterColumns>
                <column>BucketField_DealSize</column>
            </dashboardFilterColumns>
            <displayUnits>Auto</displayUnits>
            <drillEnabled>true</drillEnabled>
            <enableHover>true</enableHover>
            <header>Amount by stage</header>
            <legendPosition>Bottom</legendPosition>
            <report>Revenue_Ops/Pipeline_By_Stage</report>
            <showValues>true</showValues>
            <sortBy>RowValueDescending</sortBy>
            <title>Pipeline by stage</title>
            <useReportChart>false</useReportChart>
        </components>
    </leftSection>
    <rightSection>
        <columnSize>Medium</columnSize>
        <components>
            <componentType>Donut</componentType>
            <dashboardFilterColumns>
                <column>BucketField_DealSize</column>
            </dashboardFilterColumns>
            <displayUnits>Auto</displayUnits>
            <drillEnabled>true</drillEnabled>
            <header>Forecast category roll-up</header>
            <legendPosition>Right</legendPosition>
            <report>Revenue_Ops/Pipeline_By_Stage</report>
            <showPercentage>true</showPercentage>
            <title>Commit / Best Case / Pipeline</title>
            <useReportChart>false</useReportChart>
        </components>
        <components>
            <componentType>Table</componentType>
            <dashboardFilterColumns>
                <column>BucketField_DealSize</column>
            </dashboardFilterColumns>
            <drillEnabled>true</drillEnabled>
            <header>Stalled deals</header>
            <report>Revenue_Ops/Pipeline_By_Stage</report>
            <sortBy>RowValueDescending</sortBy>
            <title>Longest in stage</title>
            <useReportChart>false</useReportChart>
        </components>
    </rightSection>
    <textColor>#000000</textColor>
    <title>Weekly Pipeline Review</title>
    <titleColor>#000000</titleColor>
    <titleSize>12</titleSize>
</Dashboard>
```

### How to read it

- `backgroundEndColor`, `backgroundFadeDirection`, `backgroundStartColor`, `leftSection`,
  `rightSection`, `textColor`, `title`, `titleColor` and `titleSize` are all **required**
  (api_meta.txt:47684, 47692, 47699, 47823, 47840, 47856, 47859, 47861, 47864). `middleSection`
  is optional. `componentType` is required on every component (api_meta.txt:47989).
- `dashboardType` is `MyTeamUser`: "Managers can choose to view the dashboard from the point of
  view of their subordinates in the role hierarchy" (api_meta.txt:47794–47797). That is the right
  choice for a per-manager review — one dashboard, each manager sees their own team, and the
  Director can step into any manager's view. `SpecifiedUser` would show all three managers the
  same team's numbers.
- **Every component declares `dashboardFilterColumns`.** The `column` there is "the report column
  code for the filter" (api_meta.txt:48317) — here the bucket's `developerName`, which is exactly
  why the bucket lives on the report rather than in a formula field. A component that omits this
  element renders fine and silently ignores the Deal Size filter.
- **No `runningUser` element is emitted, and one will be stamped in anyway.** The guide: "when you
  deploy a dashboard and the value in this field is not defined or does not correspond to a valid
  user, the field is populated with the username of the user performing the deployment"
  (api_meta.txt:47842–47850). For a `MyTeamUser` dashboard that stored value is not what drives
  visibility, but it is not blank either — see `admin/reports-and-dashboards`
  `references/gotchas.md` for what that stamped value does and does not mean.
- `<report>` is `folderDeveloperName/reportDeveloperName` — a developer name, not the title
  (guide sample: `<report>TestReportFolder/TestReport</report>`, api_meta.txt:49057).
- Four components on one report is deliberate. Each one re-reads the same filtered row set, so
  the coverage tile and the stage bar can never disagree — a failure mode that appears the moment
  tiles are built on reports with different `scope` values.

---

## 6. List view — stale deals

`force-app/main/default/objects/Opportunity/listViews/Stale_Deals.listView-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ListView xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Stale_Deals</fullName>
    <booleanFilter>1 AND 2 AND 3</booleanFilter>
    <columns>NAME</columns>
    <columns>STAGE_NAME</columns>
    <columns>AMOUNT</columns>
    <columns>CLOSE_DATE</columns>
    <columns>LAST_STAGE_CHANGE_IN_DAYS</columns>
    <columns>NEXT_STEP</columns>
    <columns>OWNER_ID</columns>
    <filterScope>Everything</filterScope>
    <filters>
        <field>IsClosed</field>
        <operation>equals</operation>
        <value>false</value>
    </filters>
    <filters>
        <field>LAST_STAGE_CHANGE_IN_DAYS</field>
        <operation>greaterThan</operation>
        <value>15</value>
    </filters>
    <filters>
        <field>FORECAST_CATEGORY_NAME</field>
        <operation>notEqual</operation>
        <value>Omitted</value>
    </filters>
    <label>Stale Deals (15+ days in stage)</label>
    <sharedTo>
        <role>Sales_Manager</role>
    </sharedTo>
</ListView>
```

> **UNVERIFIED (2026-09-05) — the list-view column tokens need the same retrieve.** `NAME` is
> grounded: it is the token the guide's own `ListView` sample uses (api_meta.txt:44468–44478),
> and the guide states plainly that "Field names in the ListView columns don't always match their
> API name counterparts" (api_meta.txt:44317–44319). `STAGE_NAME`, `AMOUNT`, `CLOSE_DATE`,
> `LAST_STAGE_CHANGE_IN_DAYS`, `NEXT_STEP`, `OWNER_ID` and `FORECAST_CATEGORY_NAME` are not
> documented tokens. Retrieve one existing Opportunity list view and harvest the real ones. Custom
> fields are the safe case — they use the API name directly. See `admin/list-views-and-compact-layouts`
> `references/gotchas.md` for the full token trap.

### How to read it

- **The filter element is `<field>`, not `<filter>`.** The guide's `ListViewFilter` field table
  names the element `filter` — "Required. Represents the field specified in the filter"
  (api_meta.txt:44374) — while the guide's own sample XML two pages later writes `<field>NAME</field>`
  and `<field>City__c</field>` (api_meta.txt:44468–44478). An LLM authoring from the table produces
  a list view that will not deploy. `check_pipeline_review_design.py` flags a `<filters>` entry with
  no `<field>` for exactly this reason.
- `filterScope` is required and is an enum. `Everything` is "All records, for example All
  Opportunities"; `Mine`, `Team` ("My team's opportunities" in the Lightning UI) and `SalesTeam`
  ("My opportunity teams", API 49.0+) are the ones a sales org reaches for (api_meta.txt:44409–44448).
  `MyTerritory` does not apply here: "Opportunities can't be filtered by `MyTerritory`"
  (api_meta.txt:44425–44426).
- `operation` is the same fixed enum as report filters: `equals`, `notEqual`, `lessThan`,
  `greaterThan`, `lessOrEqual`, `greaterOrEqual`, `contains`, `notContain`, `startsWith`,
  `includes`, `excludes`, `within` (api_meta.txt:44385–44400). There is no `isBlank` — a
  "no next step" list view has to be `NEXT_STEP equals ""`.
- **`sharedTo` is what stops this being a public view.** Its absence is what makes a view public;
  see `admin/list-views-and-compact-layouts` `references/gotchas.md`.
- A list view is the right surface for block 3 because managers act on rows one at a time.
  A report is the right surface for blocks 1, 4 and 6 because those are totals.

---

## 7. Data-hygiene rules, expressed as validation-rule intent

The review is only as good as the three fields it reads. These are stated as intent plus formula;
the deployable `ValidationRule` metadata, the `errorDisplayField` choice and the bypass pattern
belong to `admin/validation-rules`.

| Rule id | Intent | Trigger condition | What the review loses without it |
|---|---|---|---|
| `close_date_in_past` | An open deal may not carry a `CloseDate` earlier than today | Open **and** `CloseDate < TODAY()` | Coverage counts revenue in a quarter that has already ended; the commit call is arithmetically wrong |
| `amount_required_from_proposal` | `Amount` must be populated from the Proposal stage onward | Open, stage at/after Proposal, `Amount` blank or ≤ 0 | Blank-Amount deals fall into the Velocity bucket because `nullTreatment` is `z`, so the deal-size mix reads as healthier than it is |
| `next_step_required_when_open` | `NextStep` must be non-blank on any open deal closing within 90 days | Open, `CloseDate` within 90 days, `NextStep` blank | Block 3 has nothing to review — every stale deal looks identical |

```text
# close_date_in_past
AND(
  NOT(IsClosed),
  CloseDate < TODAY()
)

# amount_required_from_proposal
AND(
  NOT(IsClosed),
  CASE(StageName,
       "Proposal", 1,
       "Negotiation", 1,
       0) = 1,
  OR(ISBLANK(Amount), Amount <= 0)
)

# next_step_required_when_open
AND(
  NOT(IsClosed),
  CloseDate <= TODAY() + 90,
  ISBLANK(NextStep)
)
```

Three things to know before these ship:

- `IsClosed` and `IsWon` are "directly controlled by `StageName`. You can query and filter on this
  field, but you can't directly set it" (object_reference.txt:192553–192560, 192617–192630). That
  is what makes `NOT(IsClosed)` a safe guard: it cannot drift from the stage ladder.
- `NextStep` is a 255-character string (object_reference.txt:192758–192764). It is not a picklist,
  so `ISBLANK` is the only test available and "TBD" satisfies the rule. The rule buys you a
  non-empty field, not a real next step — that is a coaching problem, not a platform one.
- Enforcement is bypassed by bulk and mass-close paths. Read `admin/sales-process-mapping`
  `references/gotchas.md` Gotcha 3 before you assume a validation rule closes the hole.

---

## 8. Cadence and roles

| Activity | When | R | A | C | I |
|---|---|---|---|---|---|
| Rep updates own deals | By 17:00 Friday | Account Executive | Sales Manager | — | Revenue Ops Analyst |
| Report pack refreshed / checked | Monday 08:00 | Revenue Ops Analyst | Revenue Ops Analyst | Sales Ops Admin | Sales Manager |
| Weekly review meeting | Monday, 45 min per manager | Sales Manager | Sales Manager | Account Executive | Sales Director |
| Commit call submitted | Monday, end of meeting | Sales Manager | Sales Director | Revenue Ops Analyst | — |
| Stage-conversion read-out | First review of the month | Revenue Ops Analyst | Sales Director | Sales Manager | Account Executive |
| Metric definitions reviewed | Start of each quarter | Revenue Ops Analyst | Sales Director | Sales Manager | Sales Ops Admin |
| Stale threshold re-derived | Whenever the average cycle moves ±20% | Revenue Ops Analyst | Sales Director | Sales Manager | — |
| Validation rules and list views maintained | On change | Sales Ops Admin | Sales Ops Admin | Revenue Ops Analyst | Sales Manager |

Salesforce roles are named deliberately: the Sales Ops Admin owns anything that deploys, the
Revenue Ops Analyst owns anything that defines a number, and neither owns the other's artefact.
A review pack where the same person owns both is a pack where a metric changes without anyone
noticing the report changed with it.

---

## 8b. The Pipeline Inspection half that *is* deployable

Most of Pipeline Inspection is Setup clicks, but two pieces are metadata and belong in the same
package as the report pack so the review surface arrives with the review pack.

`force-app/main/default/settings/Opportunity.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<OpportunitySettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enablePipelineInspection>true</enablePipelineInspection>
    <enableExpandedPipelineInspectionSetup>true</enableExpandedPipelineInspectionSetup>
    <enablePipelineInspectionSingleCategoryRollup>false</enablePipelineInspectionSingleCategoryRollup>
    <oppAmountDealMotionEnabled>true</oppAmountDealMotionEnabled>
</OpportunitySettings>
```

`force-app/main/default/pipelineInspMetricConfigs/Commit.pipelineInspMetricConfig-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PipelineInspMetricConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <isCumulative>true</isCumulative>
    <isProtected>false</isProtected>
    <masterLabel>Commit — manager-called</masterLabel>
    <metric>Commit</metric>
</PipelineInspMetricConfig>
```

### How to read it

- `enablePipelineInspection` defaults to `false` and, when set, "also enables historical trending
  for opportunities, if historical trending isn't already enabled" (api_meta.txt:123341–123349).
  One boolean, two features — budget for the historical-trending side effect before you flip it.
- **The flag is not the feature.** The same entry states that "to use Pipeline Inspection,
  additional configuration in Setup is required" (api_meta.txt:123344–123345). A green deploy
  proves the setting landed, not that a manager can use the view.
- `enablePipelineInspectionFlow` (the Flow Chart, API 54.0+) is a separate flag and "to use this
  feature, access to Revenue Insights is required" (api_meta.txt:123360–123366). Revenue Insights
  itself "is part of Revenue Intelligence, which is available for an additional cost"
  (api_meta.txt:123374–123380). Do not put it in the package unless the licence is confirmed.
- `enablePipelineInspectionSingleCategoryRollup` decides whether metrics display as single
  forecast categories (`true`) or rolled up (`false`, the default), and it too requires the Setup
  configuration to exist (api_meta.txt:123367–123372).
- `PipelineInspMetricConfig` files carry the suffix `.pipelineInspMetricConfig` in a
  `pipelineInspMetricConfigs` folder, are available from API version 57.0, and unlike `Report`
  and `Dashboard` this type **does** accept the `*` wildcard in package.xml
  (api_meta.txt:95626–95632, api_meta.txt:95713–95714). Only users with Customize Application or
  Modify All Data can access the type (api_meta.txt:95635).
- `masterLabel` is required and capped at 50 characters; `metric` is required and its enumeration
  is `BestCase`, `ClosedLost`, `ClosedWon`, `Commit`, `MostLikely`, `OpenPipeline`,
  `TotalPipeline` — all API 58.0 and later (api_meta.txt:95664, api_meta.txt:95667–95676). That is a *different*
  vocabulary from `ForecastCategoryName`; see `references/gotchas.md` Gotcha 14.
- `isCumulative` is documented as "Required. Read only" with a default of `true`
  (api_meta.txt:95643–95647). Emit it, but do not plan a design around changing it.

---

## 9. Deploying the pack

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Revenue_Ops/</members>
        <members>Revenue_Ops/Pipeline_By_Stage</members>
        <name>Report</name>
    </types>
    <types>
        <members>Revenue_Ops</members>
        <members>Revenue_Ops/Weekly_Pipeline_Review</members>
        <name>Dashboard</name>
    </types>
    <types>
        <members>Opportunity.Stale_Deals</members>
        <name>ListView</name>
    </types>
    <types>
        <members>*</members>
        <name>PipelineInspMetricConfig</name>
    </types>
    <types>
        <members>Opportunity</members>
        <name>Settings</name>
    </types>
    <version>62.0</version>
</Package>
```

`Report`, `Dashboard` and `ListView` all reject the `*` wildcard in package.xml
(api_meta.txt:103882, api_meta.txt:47641, api_meta.txt:44501–44503). The trailing slash on `Revenue_Ops/` is not a
typo: when a folder is referenced without its contents "the API can misinterpret the path as a
report component", and omitting the slash fails with `Entity of type 'Report' named
'TopLevel/SubLevel' cannot be found` (api_meta.txt:103929–103939).

```bash
# Retrieve the real column codes from a working report first
sf project retrieve start -m "Report:Revenue_Ops/Some_Existing_Opportunity_Report" -o prod

# Lint the pack before you deploy it
python3 skills/admin/pipeline-review-design/scripts/check_pipeline_review_design.py \
    --manifest-dir force-app/main/default

# Validate-only against production
sf project deploy start -x manifest/package.xml -o prod --dry-run

# Deploy
sf project deploy start -x manifest/package.xml -o prod
```

**Verification.** Deploying the pack proves the XML parsed, not that the numbers are right. Run
this in the target org and check that the stale count on the list view matches:

```sql
SELECT StageName,
       COUNT(Id) deals,
       SUM(Amount) pipeline,
       AVG(LastStageChangeInDays) avgDaysInStage
FROM Opportunity
WHERE IsClosed = false
  AND ForecastCategoryName != 'Omitted'
  AND CloseDate = THIS_FISCAL_QUARTER
GROUP BY StageName
ORDER BY StageName
```

If `avgDaysInStage` is suspiciously close to the age of the deals themselves, `LastStageChangeDate`
is null on those records and the field is reporting `AgeInDays` instead
(object_reference.txt:192715–192724). Confirm with:

```sql
SELECT COUNT(Id)
FROM Opportunity
WHERE IsClosed = false AND LastStageChangeDate = null
```

Anything above zero is a deal that has never been re-staged since creation, and it is inflating
the stale count.

---

## 10. Who consumes each artefact

| Artefact | Consumed by | What it is used for |
|---|---|---|
| `pipeline-review.yaml` | `scripts/check_pipeline_review_design.py` | Gate: no metric ships without a definition, source, owner and target |
| Metric-to-field table (§2) | `agents/sales-stage-designer/AGENT.md` | The stage ladder has to make the movement measurable; that agent already reads this skill for exactly this reason |
| Report + Dashboard XML (§4, §5) | `skills/admin/reports-and-dashboards` | Folder sharing, running-user semantics, subscription behaviour |
| Report type questions | `skills/admin/report-type-strategy` | If the pack outgrows the standard `Opportunity` report type |
| List view XML (§6) | `skills/admin/list-views-and-compact-layouts` | Column tokens, `sharedTo`, sprawl control |
| Hygiene rules (§7) | `skills/admin/validation-rules` | Deployable `ValidationRule` metadata and the bypass pattern |
| Stage / forecast-category mapping | `skills/admin/opportunity-management` | Where the stage ladder and its category mapping are actually configured |
| Cadence and roles (§8) | The review itself | Nothing deploys it; it is the artefact that fails silently if nobody owns it |
