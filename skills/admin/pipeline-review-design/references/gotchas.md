# Gotchas — Pipeline Review Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Pipeline Inspection Toggle Absent from Setup Without Qualifying License

**What happens:** When an admin navigates to Setup and searches for "Pipeline Inspection," the section either does not appear or appears without an enable toggle. Granting Customize Application and all related Sales Cloud permissions does not resolve it.

**When it occurs:** Any org that does not have Revenue Intelligence or Sales Cloud Einstein provisioned. The absence is silent — Setup does not display an explanatory message. It is frequently misdiagnosed as a permission problem or a metadata visibility issue.

**How to avoid:** Before attempting Pipeline Inspection enablement, verify the license in Setup > Company Information > Active Salesforce Licenses. Look for "Revenue Intelligence" or "Sales Cloud Einstein" in the list. If neither is present, Pipeline Inspection cannot be enabled. Escalate to the Account Executive for license provisioning rather than spending time debugging permissions.

---

## Gotcha 2: Lookback Window Selection Is Not Persisted Per User

**What happens:** A sales manager sets the Pipeline Inspection lookback window to 14 days during a Monday review meeting. The next time they open Pipeline Inspection — even the same day — it has reverted to the system default (7 days). Managers who standardize their review on a specific window must re-select it every session.

**When it occurs:** Every time the Pipeline Inspection page is loaded. The window selector is a session-level UI control, not a persisted user preference. There is no admin setting to change the default window for individual users or roles as of Spring '25.

**How to avoid:** Document the standard lookback window in the team's pipeline review playbook and include it as the first step in the meeting agenda ("Set window to 14 days before reviewing"). There is no admin configuration workaround for per-user persistent window selection.

---

## Gotcha 3: Split-Based Forecast Type Changes Visible Deal Amounts in Inspection View

**What happens:** An admin associates an Opportunity Splits-based forecast type with Pipeline Inspection. Managers who previously saw full Opportunity Amounts in the inspection view now see split-attributed amounts. A $500,000 deal where the viewing manager's rep owns a 60% split shows as $300,000. Managers believe deal values have changed and escalate to the admin.

**When it occurs:** When a forecast type with Opportunity Splits as its source object is associated with Pipeline Inspection and selected as the active type in the inspection view. The amount displayed reflects the split percentage for the viewing user's subordinates, not the total Opportunity Amount.

**How to avoid:** When associating forecast types with Pipeline Inspection, explicitly communicate to managers what amount basis each type uses. If managers need to see total deal amounts alongside split attribution, associate both an Opportunity-based and a Split-based forecast type. Train managers to toggle between the types and understand what each shows.

---

## Gotcha 4: Omitted-Stage Deals Are Invisible in Pipeline Totals Without the Filter Toggle

**What happens:** A manager asks why a known large deal is not showing in the Pipeline Inspection totals. The deal exists, is active, and the rep is in the manager's forecast hierarchy. The admin verifies permissions are correct and the deal is visible in regular list views. The deal's Stage is mapped to `Omitted` in ForecastCategoryName.

**When it occurs:** Any time a deal is in a Stage whose ForecastCategoryName is `Omitted`. Pipeline Inspection excludes Omitted deals from all metric totals and column groupings by default. The deal is not displayed unless the "Show Omitted" filter toggle is enabled in the inspection view.

**How to avoid:** Audit Stage-to-ForecastCategoryName mappings before configuring Pipeline Inspection. Document which stages are Omitted and why (e.g., "Dead", "On Hold"). Train managers to use the "Show Omitted" toggle when they need to review parked deals. Do not remap legitimate Omitted stages to revenue categories just to surface them in totals — that corrupts forecast rollups.

---

## Gotcha 5: Users Outside the Forecast Hierarchy Cannot Access Pipeline Inspection Data

**What happens:** A sales director with "Modify All Data" and "View All Forecasts" permissions cannot see data for a specific team in Pipeline Inspection. The team's deals are visible in reports and list views but not in the inspection view.

**When it occurs:** Pipeline Inspection uses the Collaborative Forecasts hierarchy to determine visibility. "View All Forecasts" allows seeing all forecast summary data on the Forecasts page, but Pipeline Inspection additionally requires the user to be in the correct position in the hierarchy to see subordinate deal detail. "Modify All Data" does not grant Pipeline Inspection visibility beyond what the forecast hierarchy allows.

**How to avoid:** Confirm that all users who need Pipeline Inspection access are correctly placed in the active forecast hierarchy under Setup > Forecasts > Forecast Settings. Sales directors who need cross-team visibility should be placed at the top of the hierarchy or have an explicit hierarchy position covering the teams they need to review.

---

## Gotcha 6: `LastStageChangeInDays` Reports Record Age on a Deal That Has Never Been Re-Staged

**What happens:** A stale-deal list view filtered on `LastStageChangeInDays > 15` returns deals that were created last quarter and have sat in their opening stage ever since, mixed in with deals that genuinely stalled mid-cycle. The manager reads the list as "18 stalled deals" when eight of them have simply never moved at all. The number is not wrong, but it is not the number anybody thought they were asking for.

**When it occurs:** Whenever `LastStageChangeDate` is null. The Object Reference is explicit about the substitution: `LastStageChangeInDays` is "calculated by the current date minus the `last_stage_change_date` field. If the `last_stage_change_date` is null, then this field contains the value for `AgeInDays`" (object_reference.txt:192715–192724). `AgeInDays` is "the number of days since the opportunity was created" (object_reference.txt:192275–192282). Records loaded by a migration, records created before the field shipped in API 52.0, and records that have genuinely never left their first stage all land in this bucket.

**How to avoid:** Count the population before you set a threshold: `SELECT COUNT(Id) FROM Opportunity WHERE IsClosed = false AND LastStageChangeDate = null`. If it is non-trivial, split the review into two blocks — "stalled" (has moved, then stopped) and "never started" (no stage change at all) — because they need different conversations. Do not compensate by raising the threshold; that hides real stalls to hide the artefact.

---

## Gotcha 7: `AgeInDays` and `LastStageChangeInDays` Do Not Exist Unless Pipeline Inspection Is Enabled

**What happens:** A report or list view built in one org deploys into another and the column comes back blank, or the deploy fails on an unknown field. The field API name is right, the object is right, and the same file works in the source org.

**When it occurs:** Both fields carry a conditional availability clause: `AgeInDays` and `LastStageChangeInDays` are "available in API version 52.0 and later **if you enabled Pipeline Inspection**" (object_reference.txt:192275–192282, 192715–192724). `LastStageChangeDate` itself has no such clause — it is available from API 52.0 unconditionally (object_reference.txt:192707–192713). So the raw timestamp exists everywhere and the two derived day-counts do not. A sandbox refreshed before the feature was turned on, or a partner org on a different licence, produces exactly this split.

**How to avoid:** Treat the two day-count fields as licence-gated, not as standard fields, and check them in every target org before the pack ships. Where the target may not have Pipeline Inspection, build the stale-deal filter on `LastStageChangeDate` with a relative date literal instead — it is available unconditionally and does not silently swap in record age. Note that `LastStageChangeDate` carries `Aggregate, Filter, Nillable, Sort` but **not** `Group` (object_reference.txt:192707–192713), so it can be filtered and sorted but not used as a report grouping.

---

## Gotcha 8: `PushCount` Only Counts Calendar-Month Boundaries, and It Never Goes Down

**What happens:** A slippage metric built on `PushCount` reports zero for a rep who has moved every deal from the 3rd of the month to the 28th of the same month three times running, and reports 4 for a rep who pushed one deal out twice and then pulled it back in twice. Both readings are correct behaviour and both are the opposite of what the review wanted to see.

**When it occurs:** The definition is narrow and the Object Reference states both halves: `PushCount` is "the number of times an opportunity's close date has been pushed out by one calendar month. For example, moving a close date from April to May counts as one push, but moving from April 1 to April 30 doesn't count. The total is not decreased when the close date is moved in" (object_reference.txt:192865–192873). It is available from API version 53.0.

**How to avoid:** Use `PushCount` as a *career* signal on a deal — "this thing has slipped before" — never as a within-quarter slippage rate. For the quarterly number, compare `CloseDate` against a snapshot taken at quarter open, or track pushes with field history on `CloseDate` and turn history tracking on before the quarter starts, since history is never backfilled. State in the spec's `definition` field which of the two you mean; the two numbers will never agree and the review will argue about it otherwise.

---

## Gotcha 9: `Amount` Cannot Be Updated on Any Opportunity That Has Products

**What happens:** A review ends with "trim that deal to $80k", the rep edits `Amount`, saves, and the record still shows the old figure. No error appears. The next week's coverage number is unchanged and everyone assumes the rep ignored the instruction.

**When it occurs:** On any opportunity with line items. The Object Reference describes the failure mode precisely — for opportunities with products "the amount is the sum of the related products. Any attempt to update this field, if the record has products, will be ignored. The update call will not be rejected, and other fields will be updated as specified, but the `Amount` will be unchanged" (object_reference.txt:192284–192292). A Data Loader run or an API integration writing `Amount` alongside other fields succeeds row by row while silently dropping that one value.

**How to avoid:** Establish before the review begins whether the org sells with products. If it does, the coverage conversation is about line items, not about `Amount`, and the review agenda should send the rep to the products related list. `HasOpportunityLineItem` tells you which records are affected and is filterable, so a report column on it stops the ambiguity at the meeting rather than a week later.

---

## Gotcha 10: `INTERVAL_CURRENT` Is the Fiscal Quarter; `INTERVAL_CURRENTQ` Is the Calendar Quarter

**What happens:** The pipeline report and the Forecasts page disagree, by a whole month's worth of deals, in an org whose fiscal year does not start in January. Both are filtered on "current quarter". Nobody can reproduce the discrepancy because both look right in isolation.

**When it occurs:** The `UserDateInterval` enumeration carries both spellings and they mean different things: `INTERVAL_CURRENT` is "Current fiscal quarter" (api_meta.txt:105164) while `INTERVAL_CURRENTQ` is "Current calendar quarter" (api_meta.txt:105226). The same split runs through the whole enum — `INTERVAL_CURFY` is the fiscal year, `INTERVAL_CURY` the calendar year. In a calendar-aligned org the two are identical, which is why this survives every test until the pack is deployed into an org with an April fiscal start.

**How to avoid:** Pick the fiscal variants for anything that will be compared against a forecast or a quota, and write the choice into the spec's `forecast_period` field so it survives the next person. `timeFrameFilter` is a separate element from `filter` with its own required `dateColumn` and `interval` (api_meta.txt:105097–105105), so a report can carry a correct row filter and still bracket the wrong three months.

---

## Gotcha 11: The `ListView` Filter Element the Guide's Field Table Names Is Not the One That Deploys

**What happens:** A hand-authored stale-deals list view fails to deploy, or deploys with its filters missing. The XML looks exactly like the documented field table.

**When it occurs:** The `ListViewFilter` field table names the element `filter` — "Required. Represents the field specified in the filter" (api_meta.txt:44374) — but the guide's own Declarative Metadata Sample Definition, two pages later in the same section, writes `<field>NAME</field>` and `<field>City__c</field>` inside `<filters>` (api_meta.txt:44468–44478). An assistant generating XML from the field table produces `<filter>`; an assistant copying the sample produces `<field>`. Only the second one is the deployable element.

**How to avoid:** Author list views from the sample definition, not from the field table, and run `scripts/check_pipeline_review_design.py` — it flags a `<filters>` entry with no `<field>` child specifically for this. Note the filter value uses the same `FilterOperation` enum as report filters, with no `isBlank` member (api_meta.txt:44385–44400), so a "no next step" view has to be expressed as an `equals` test against an empty value.

---

## Gotcha 12: A Report Folder in package.xml Needs a Trailing Slash or the Deploy Cannot Find It

**What happens:** The deploy of a new review pack fails with `Entity of type 'Report' named 'Revenue_Ops/Weekly' cannot be found`, naming a report that was never authored — the string is actually the folder path.

**When it occurs:** When a nested report folder is listed in package.xml without its contents. The guide states that "when you reference a nested folder by itself (without its contents), the API can misinterpret the path as a report component", and that omitting the trailing slash "causes the operation to fail with an error" of exactly that shape (api_meta.txt:103929–103939). Neither `Report` nor `Dashboard` accepts the `*` wildcard in package.xml (api_meta.txt:103882, api_meta.txt:47641), and `ListView` rejects it too (api_meta.txt:44501–44503), so every member has to be listed by name and the folder-vs-report ambiguity is unavoidable.

**How to avoid:** Write nested folder members with a trailing slash (`<members>Revenue_Ops/Sub/</members>`) and list the reports separately. Because no wildcard is available, generate the member list from a `listMetadata` call on `ReportFolder` rather than by hand — the guide documents that two-step call as the supported way to populate package.xml for reports (api_meta.txt:103882–103896).

---

## Gotcha 13: `enablePipelineInspection` Also Switches On Historical Trending, and Still Is Not Enough on Its Own

**What happens:** A one-line settings deploy flips Pipeline Inspection on. Two things then go wrong in opposite directions. Historical trending for Opportunity starts running in an org that never asked for it and never budgeted the storage or the report-type consequences. Meanwhile the managers who were told the feature is live open the Opportunity tab and find nothing usable, because the flag alone does not configure anything.

**When it occurs:** On any deploy of `OpportunitySettings` that sets `enablePipelineInspection` to `true`. The guide states both halves in the same field entry: the setting "also enables historical trending for opportunities, if the org has the historical trending org perm", "also enables historical trending for opportunities, if historical trending isn't already enabled", and "to use Pipeline Inspection, additional configuration in Setup is required" (api_meta.txt:123341–123349). The default is `false`, so this is always an explicit act. Available from API version 52.0.

**How to avoid:** Treat the flag as step one of a runbook, never as the change itself. Sequence it: confirm the historical-trending position first (a separate conversation with its own limits and report-type effects), deploy the setting, then complete the Setup configuration, then verify with a real manager account before announcing the feature. Keep `enablePipelineInspectionFlow` out of the package unless Revenue Insights is confirmed — "to use this feature, access to Revenue Insights is required" (api_meta.txt:123360–123366), and Revenue Insights "is part of Revenue Intelligence, which is available for an additional cost" (api_meta.txt:123374–123380).

---

## Gotcha 14: `PipelineInspMetricConfig.metric` Is a Fourth Forecast Vocabulary

**What happens:** Someone maps the org's forecast categories onto Pipeline Inspection metric configs by copying the category names across, and the deploy fails on an invalid enumeration value — or worse, succeeds against a member that means something adjacent but not identical, and the relabelled metric quietly stops matching the forecast roll-up it was supposed to mirror.

**When it occurs:** Whenever a stage-to-category design is carried into `PipelineInspMetricConfig`. The `PipelineInspectionMetric` enumeration is `BestCase`, `ClosedLost`, `ClosedWon`, `Commit`, `MostLikely`, `OpenPipeline`, `TotalPipeline` — all available in API version 58.0 and later (api_meta.txt:95667–95676). Set that beside `ForecastCategoryName`, whose values are `Best Case`, `Closed`, `Commit`, `Most Likely`, `Omitted`, `Pipeline` (object_reference.txt:192483–192497). The overlap is partial and the gaps run both ways: there is no `Omitted` and no `Pipeline` metric, `Closed` splits into `ClosedWon` and `ClosedLost`, and `OpenPipeline` / `TotalPipeline` are aggregates that correspond to no single category at all. This is a *fourth* spelling of the same family of ideas, on top of the three already documented in `admin/opportunity-management` `references/gotchas.md` Gotcha 13.

**How to avoid:** Keep a single mapping table in the design doc with one column per vocabulary — metadata `forecastCategory`, SOQL `ForecastCategoryName`, `Opportunity.ForecastCategory`, and `PipelineInspMetricConfig.metric` — and never let a value cross columns unlabelled. Only `masterLabel` is yours to choose, and it is capped at 50 characters (api_meta.txt:95664); the `metric` value underneath it is fixed. When a manager asks to "rename Commit", the answer is a `masterLabel` on a `Commit` metric config, not a change to any category anywhere.
