---
name: pipeline-review-design
description: "Configuring and running Pipeline Inspection in Sales Cloud: enabling the feature, mapping forecast categories into the inspection view, Days in Stage and other deal-change metrics, and pipeline review cadence for sales managers. Use when designing or improving how a team monitors deal health and pipeline movement. NOT for the Revenue Intelligence app, Einstein deal insights, or forecast-accuracy dashboards — use admin/revenue-intelligence-setup. NOT for forecast types, quotas, or forecast hierarchy setup — use admin/collaborative-forecasts. Keywords: pipeline review, coverage ratio, stage conversion, slippage, stale deals, days in stage, LastStageChangeInDays, LastStageChangeDate, AgeInDays, PushCount, ForecastCategoryName, enablePipelineInspection, PipelineInspMetricConfig, OpportunitySettings, review cadence, commit call."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "How do I set up Pipeline Inspection so managers can see deal changes week-over-week?"
  - "I need to configure Days in Stage tracking so the team can spot stalled deals"
  - "My Pipeline Inspection view is not showing the right forecast categories — how do I configure the metrics?"
  - "How do we design a weekly pipeline review cadence in Salesforce using Pipeline Inspection?"
  - "Reps are moving deals backwards in stage and I want a way to surface that in pipeline reviews"
  - "define the metrics for our weekly pipeline review meeting"
  - "build a report showing stalled opportunities by days in stage"
  - "days in stage is wrong for deals that never changed stage"
  - "which Opportunity field gives me days in current stage"
  - "pipeline coverage ratio report disagrees with the forecast page"
  - "list view of opportunities with a close date in the past and no next step"
  - "deploy pipeline inspection settings between orgs"
  - "PushCount is zero even though the rep keeps pushing the close date"
  - "what should a weekly pipeline review agenda cover"
  - "stale opportunities days in stage report for pipeline review"
tags:
  - pipeline-inspection
  - pipeline-review
  - forecast-categories
  - days-in-stage
  - sales-cloud
  - revenue-intelligence
  - pipeline-health
  - deal-velocity
inputs:
  - "Whether the org has Revenue Intelligence, Sales Cloud Einstein, or neither"
  - "List of forecast types and their source objects (Opportunity, Opportunity Splits)"
  - "Which metrics the sales team prioritizes (e.g., Days in Stage, amount changes, stage changes)"
  - "Desired pipeline review cadence (weekly, bi-weekly, etc.) and who participates"
  - "Current Stage picklist values and their ForecastCategoryName mappings"
outputs:
  - "Step-by-step Pipeline Inspection enablement and configuration checklist"
  - "Metrics configuration guidance (Days in Stage, Amount Changed, pipeline change columns)"
  - "Forecast category mapping review for Pipeline Inspection visibility"
  - "Review cadence design with recommended inspection workflow"
  - "Checker output from check_pipeline_review_design.py identifying metadata gaps"
  - "A linted pipeline-review spec (YAML): metrics with definition, source field, owner and target"
  - "Deployable Report, Dashboard and ListView XML for the review pack, plus the package.xml"
  - "Data-hygiene rules expressed as validation-rule intent for admin/validation-rules"
  - "Cadence and RACI table naming the Salesforce role that owns each artefact"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Pipeline Review Design

This skill activates when configuring Pipeline Inspection in Sales Cloud or designing a structured pipeline review process for sales managers and forecast owners. It covers feature enablement, metric configuration (Days in Stage, Amount Changes, Stage Changes), forecast category alignment in the inspection view, and cadence design. Pipeline Inspection is a native Sales Cloud view, not a custom dashboard, and has specific licensing and configuration dependencies that must be verified before setup begins.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the org has **Revenue Intelligence** or **Sales Cloud Einstein** — Pipeline Inspection requires one of these add-ons. It is not available in base Sales Cloud without a qualifying license. Enablement in Setup will be grayed out if the license is absent.
- Verify that Collaborative Forecasting is enabled and at least one forecast type is active — Pipeline Inspection surfaces data within the forecasting framework and cannot function without an active forecast type.
- Identify which Opportunity Stage values map to which ForecastCategoryName values. Stages mapped to `Omitted` will not appear in Pipeline Inspection forecast category groupings; stages mapped to `Closed` appear in the Closed section. Misaligned mappings are the most common reason inspection views look wrong.
- Confirm whether custom forecast categories are in use. Starting Spring '24, orgs can create custom forecast categories beyond the default five (Pipeline, Best Case, Most Likely, Commit, Omitted). If custom categories are active, they must be explicitly included in Pipeline Inspection metric configuration.
- Know which users need access. Pipeline Inspection visibility is governed by the user's position in the forecast hierarchy and their "View All Forecasts" permission. Users outside the forecast hierarchy cannot access the inspection view for deals they do not own.

---

## Questions to Ask Before Configuring

Ask these before building a single report. Each one traces to a failure mode in
`references/gotchas.md`; an assistant that skips them produces a pack that deploys cleanly and
reports the wrong number.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What decision does this meeting produce, and who makes it?" | A review with no decision is a status call with a dashboard. The agenda and the RACI both derive from this answer | The agenda blocks, and one named owner per block |
| "What is the average cycle length, and how was it measured?" | The stale-deal threshold is derived from it, not chosen. Too high hides stalls; too low floods the list | The `stale_deals` target, plus the trigger for re-deriving it when the cycle moves |
| "Does the org sell with products?" | `Amount` cannot be updated on product-bearing opportunities, so "trim that deal" silently does nothing | Whether the coverage conversation is about `Amount` or about line items |
| "Is Pipeline Inspection licensed and enabled in every org this pack must run in, sandboxes included?" | `AgeInDays` and `LastStageChangeInDays` exist only where it is enabled; `LastStageChangeDate` exists everywhere | Which fields the metrics are allowed to use, and whether a fallback is needed |
| "When does the fiscal year start?" | `INTERVAL_CURRENT` is the fiscal quarter and `INTERVAL_CURRENTQ` the calendar one; a calendar-aligned org cannot tell them apart in testing | The `interval` value, recorded in the spec so the next person inherits the reasoning |
| "Who owns each number, and what counts as good for it this quarter?" | An unowned metric drifts and an untargeted one is decoration. The checker refuses both | Every metric's `owner` and `target`, and a quarterly definition review |
| "Which stages map to `Omitted`, and does the business consider those deals dead?" | Omitted deals are excluded from roll-ups and from the report filter by design; parking live deals there removes them from every total | The stage-to-category audit, and whether the review needs a separate parked-deals block |

What a proper configuration adds over just doing it: every number on the agenda traces to a named field, a named owner and a written target, so a disagreement in the meeting is settled by reading the spec instead of by whoever talks loudest.

---

## Core Concepts

### Pipeline Inspection and Licensing Requirements

Pipeline Inspection is a Sales Cloud feature that provides a consolidated view of opportunities with inline metric columns showing how deals have changed over a configurable lookback window (default: 7 days for pipeline changes; configurable up to 90 days for historical comparisons). It is enabled at Setup > Pipeline Inspection and requires either **Revenue Intelligence** or **Sales Cloud Einstein** licensing.

The feature is not a report or dashboard — it is a specialized list view layered on top of the Forecasts page, accessible to forecast managers. It surfaces Opportunity fields alongside calculated change metrics without requiring SOQL reports or custom analytics. This distinction matters for scope: Pipeline Inspection cannot be substituted for a CRM Analytics dashboard, and it cannot replace the Forecasts page for quota attainment tracking.

### Forecast Categories and the Inspection View

Pipeline Inspection groups and filters opportunities by Forecast Category, which maps directly to the `ForecastCategoryName` field on each Stage picklist value. The five default categories available in Pipeline Inspection are:

| Category | Meaning |
|---|---|
| Commit | High-confidence deals the rep is committing to close |
| Best Case | Deals the rep expects to close with additional effort |
| Most Likely | Deals that are probable but not fully committed (available when Most Likely forecast type is active) |
| Open Pipeline | Earlier-stage deals in active consideration |
| Omitted | Excluded from all forecast rollups; these are hidden from Pipeline Inspection totals unless specifically filtered for |

Starting Spring '24, admins can create custom forecast categories in addition to or as replacements for some of the defaults. Custom categories appear in Pipeline Inspection once the underlying forecast type is associated with Pipeline Inspection via Setup > Pipeline Inspection > Forecast Types.

Stages mapped to `Closed` (IsClosed=true) appear in the Closed Won / Closed Lost groupings in the inspection view and are not included in the open pipeline metrics. Deals in Omitted stages are excluded from totals but can be viewed using the "Show Omitted" filter toggle.

### Pipeline Change Metrics and Days in Stage

Pipeline Inspection exposes a set of configurable metric columns that highlight deal movement. The core metrics available are:

| Metric | Meaning |
|---|---|
| Amount Changed | Net change in Opportunity Amount over the lookback window |
| Close Date Changed | Flag when the Close Date has been pushed out |
| Stage Changed | Flag when the Stage has moved (forward or backward) |
| Days in Stage | How many days the opportunity has been in its current stage without advancing; this is a native metric calculated by the platform and does not require a formula field |

Days in Stage is configured in Setup > Manage Pipeline Inspection Metrics. It is not derived from a custom field — the platform calculates it from the stage transition event log. Admins can configure the threshold that triggers a visual highlight (e.g., flag deals that have been in the same stage for more than 14 days).

Metric columns can be shown or hidden per inspection view. Not all metrics are available without Revenue Intelligence — some advanced metrics (e.g., AI-powered deal health scores) require the full Revenue Intelligence license rather than just Sales Cloud Einstein.

### Forecast Type Association with Pipeline Inspection

Pipeline Inspection must be associated with one or more active Collaborative Forecasts forecast types to determine which opportunities it surfaces. In Setup > Pipeline Inspection, each active forecast type can be toggled on or off for inclusion in the inspection view. If a forecast type uses Opportunity Splits as its source object, the inspection view will reflect split-credited amounts rather than the full Opportunity Amount.

Associating a forecast type with Pipeline Inspection does not change the forecast type itself. It only controls which source data feeds the inspection view's metric calculations. If multiple forecast types are active (e.g., one for Opportunities and one for Products), each will appear as a selectable filter in the Pipeline Inspection view.

### The Opportunity Fields a Pipeline Review Actually Reads

Every number said out loud in a review comes from one of these. The full metric-to-field mapping,
with the failure mode beside each, is `references/worked-examples.md` §2.

| Field | Type | What it gives the review | Grounding |
|---|---|---|---|
| `StageName` | picklist | The stage ladder. Updating it auto-updates `ForecastCategoryName`, `IsClosed`, `IsWon` and `Probability` | object_reference.txt:192893–192904 |
| `ForecastCategoryName` | picklist | The roll-up axis: Best Case, Closed, Commit, Most Likely, Omitted, Pipeline. Overridable per record | object_reference.txt:192483–192497 |
| `Amount` | currency | Coverage numerator. Update is **ignored** on any record that has products | object_reference.txt:192284–192292 |
| `CloseDate` | date | Period bracketing. Required on every opportunity | object_reference.txt:192320–192326 |
| `LastStageChangeDate` | datetime | Raw stage-movement timestamp, API 52.0+, no feature condition. Filterable and sortable but **not** groupable | object_reference.txt:192707–192713 |
| `LastStageChangeInDays` | int | Days in stage — API 52.0+ **and only where Pipeline Inspection is enabled**. Falls back to `AgeInDays` when the timestamp is null | object_reference.txt:192715–192724 |
| `AgeInDays` | int | Record age since creation, same availability condition | object_reference.txt:192275–192282 |
| `PushCount` | int | Slippage — calendar-month pushes only, never decremented. API 53.0+ | object_reference.txt:192865–192873 |
| `ExpectedRevenue` | currency | Weighted pipeline: read-only `Amount` × `Probability` | object_reference.txt:192401–192408 |
| `NextStep` | string(255) | The only field that makes a stale-deal list actionable | object_reference.txt:192758–192764 |

There is no custom formula field in that list, and there does not need to be. The anti-pattern in
`references/examples.md` shows why the `Stage_Entry_Date__c` + formula pattern is worse than the
platform field it replaces.

### What of Pipeline Inspection Is Deployable

Part of the feature is metadata and part of it is not, which is why a green deploy is never proof
the review surface works.

| Piece | Deployable as | Note |
|---|---|---|
| Feature on/off | `OpportunitySettings.enablePipelineInspection` | Default `false`; also enables Opportunity historical trending (api_meta.txt:123341–123349) |
| Metric labels | `PipelineInspMetricConfig` (`.pipelineInspMetricConfig`, API 57.0+) | Accepts the `*` wildcard in package.xml (api_meta.txt:95626–95632, api_meta.txt:95713–95714) |
| Flow Chart | `OpportunitySettings.enablePipelineInspectionFlow` | Requires Revenue Insights access (api_meta.txt:123360–123366) |
| Single-category roll-up | `OpportunitySettings.enablePipelineInspectionSingleCategoryRollup` | API 55.0+, default `false` (api_meta.txt:123367–123372) |
| Metric thresholds, forecast-type association, hierarchy | not metadata | "To use Pipeline Inspection, additional configuration in Setup is required" (api_meta.txt:123344–123345) |
| The review pack itself | `Report`, `Dashboard`, `ListView` | Fully deployable, licence-free, and the artefact of record |

---

## Common Patterns

### Enabling Pipeline Inspection for a Sales Manager Team

**When to use:** A sales manager team wants to run structured weekly pipeline reviews using Pipeline Inspection instead of manual list views or reports.

**How it works:**
1. Confirm Revenue Intelligence or Sales Cloud Einstein license is provisioned — check Company Information in Setup for the license presence.
2. Navigate to Setup > Pipeline Inspection > Enable Pipeline Inspection. Toggle the feature on.
3. Select which active forecast types to associate with Pipeline Inspection. Enable at least the primary Opportunity-based forecast type.
4. Configure metrics in Setup > Manage Pipeline Inspection Metrics. Enable Days in Stage, Amount Changed, Close Date Changed, and Stage Changed as a baseline set.
5. Set the Days in Stage threshold to a value that reflects the expected sales cycle (e.g., 14 days for a 30-day cycle, 21 days for a 90-day cycle).
6. Verify that sales managers and forecast owners have "View All Forecasts" permission or are in the forecast hierarchy. Users who are not in the hierarchy cannot view the inspection panel.
7. Train managers on the lookback window selector — the default is 7 days but can be extended to compare this week to last quarter.

**Why not a custom report:** Reports are static snapshots. Pipeline Inspection shows inline change signals on live data, enabling managers to spot regression (stage moved backwards, close date pushed, amount trimmed) in a single scrollable view without pivoting to a separate analytics tool.

### Designing a Stage Stall Detection Configuration

**When to use:** The team wants to proactively surface deals that are stuck in a stage for too long before they become forecast risks.

**How it works:**
1. Audit the existing Stage picklist values and their ForecastCategoryName mappings. Identify the stages where deal stall is most impactful (typically stages mapped to Best Case and Commit).
2. In Setup > Manage Pipeline Inspection Metrics, configure the Days in Stage metric. Set a threshold that triggers visual highlighting — a common starting point is 1.5x the average time reps spend in that stage based on historical data.
3. During pipeline review meetings, managers sort the inspection view by Days in Stage descending to prioritize stalled deals first.
4. Document the review cadence: which deals require a manager comment, which trigger a re-forecast update, and which are escalated.

**Why not a formula field for days in stage:** A custom formula field calculating days in current stage requires a workflow or flow to capture the stage-entry date. Platform-native Days in Stage in Pipeline Inspection uses the stage transition history without additional configuration and is recalculated automatically.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org has no Revenue Intelligence or Sales Cloud Einstein | Cannot enable Pipeline Inspection — use reports and list views instead | Pipeline Inspection requires a qualifying license; attempting to enable without it produces no toggle in Setup |
| Custom forecast categories are active (Spring '24+) | Associate each custom forecast type with Pipeline Inspection explicitly in Setup | Custom categories do not auto-associate; they must be opted into the inspection view |
| Deals in Omitted stages need visibility during review | Use the "Show Omitted" filter toggle in Pipeline Inspection | Do not remap stages from Omitted to a revenue category just to make them visible — that would corrupt forecast rollups |
| Multiple forecast types are active | Enable the primary forecast type for inspection; optionally enable others | Each enabled type adds a selector in the view; too many creates confusion for managers unfamiliar with which type drives quota |
| Team wants AI deal health scores in inspection view | Verify full Revenue Intelligence license is active (not just Sales Cloud Einstein) | AI-powered deal health scores require Revenue Intelligence; Sales Cloud Einstein enables basic Pipeline Inspection but not AI insights |
| Stage moved backward needs to be surfaced | Stage Changed metric is sufficient; no additional config needed | Pipeline Inspection flags stage changes in both directions; backward movement shows in the Stage Changed column |
| Days in Stage thresholds differ by sales segment | Use segment-specific review filters during cadence meetings | A single global threshold applies in Pipeline Inspection; segment differentiation is achieved through manager-level filtering at review time |

---

## Recommended Workflow

1. **Draft the spec first.** Copy `templates/pipeline-review-spec-template.yaml` into the project and fill in cadence, roles, `fields`, `metrics` (each with `id`, `definition`, `source`, `owner`, `target`) and `hygiene_rules`. Start from the metric set in `references/worked-examples.md` §2 rather than inventing one. No XML until the spec exists — the spec is what the report columns are checked against.
2. **Ground every metric in a field that exists in the target org.** Confirm `LastStageChangeInDays`, `AgeInDays` and `PushCount` are present (they are version- and feature-gated), record whether the org sells with products, and record the fiscal-year start so the report `interval` is a decision rather than a default. Read `references/gotchas.md` 7, 9 and 10 before this step, not after.
3. **Harvest the real column codes.** Retrieve one working Opportunity report and one Opportunity list view from the target org, read the report column codes and list-view tokens off them, and write those into the spec's `report_column` / `list_view_column` values. Never hand-author them — see `references/gotchas.md` 11 and `admin/list-views-and-compact-layouts`.
4. **Build the pack** — Report, Dashboard, ListView — shaped from `references/worked-examples.md` §4–§6, and the package.xml from §9. If Pipeline Inspection itself is being deployed, add the `OpportunitySettings` and `PipelineInspMetricConfig` files from §8b and read `references/gotchas.md` 13 before setting `enablePipelineInspection`.
5. **Lint before deploying:** `python3 skills/admin/pipeline-review-design/scripts/check_pipeline_review_design.py --manifest-dir <source-dir>`. Exit 1 means a metric has no owner, target or resolvable source; a metric id repeats; a report or list-view column references something the spec never declared; or a Report XML is malformed. Fix the spec or the XML — never silence the checker.
6. **Deploy validate-only, deploy, then verify with data.** Run the two SOQL checks in `references/worked-examples.md` §9. If average days-in-stage tracks record age, or the null-`LastStageChangeDate` count is non-trivial, the stale-deal number is measuring the wrong thing and the threshold conversation has to happen again.
7. **Publish the cadence and roles table** (§8) and schedule the quarterly review of the metric definitions. Hand the `hygiene_rules` intent to `admin/validation-rules` for the deployable `ValidationRule` metadata, and the stage-ladder consequences to `admin/opportunity-management`.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Revenue Intelligence or Sales Cloud Einstein license is confirmed present in the org
- [ ] Collaborative Forecasting is enabled and at least one active forecast type is associated with Pipeline Inspection
- [ ] Pipeline Inspection toggle is on in Setup > Pipeline Inspection
- [ ] Days in Stage, Amount Changed, Close Date Changed, and Stage Changed metrics are enabled
- [ ] Days in Stage threshold is set to a value aligned with the team's average sales cycle length
- [ ] Every active opportunity stage has the correct ForecastCategoryName mapping (no revenue-bearing stages mapped to Omitted)
- [ ] Custom forecast categories (if any) are explicitly associated with Pipeline Inspection
- [ ] Sales managers who need access are in the forecast hierarchy or have "View All Forecasts" permission
- [ ] Review cadence (frequency, scope, escalation triggers, re-forecast rules) is documented and communicated
- [ ] Checker script output has been reviewed and all flagged issues resolved
- [ ] The pipeline-review spec exists and `check_pipeline_review_design.py --manifest-dir` exits 0
- [ ] Every metric in the spec has a definition, a source field, a named owner and a target
- [ ] Report column codes and list-view tokens were harvested from the target org, not hand-authored
- [ ] The report `interval` is the fiscal variant if the number will be compared to a forecast
- [ ] The null-`LastStageChangeDate` population was counted before the stale threshold was set
- [ ] Data-hygiene rules have been handed to `admin/validation-rules` with an owner, not left verbal

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Pipeline Inspection toggle is missing from Setup when the license is absent** — If the org does not have Revenue Intelligence or Sales Cloud Einstein, the Pipeline Inspection section either does not appear in Setup or appears with no enable toggle. This is frequently misdiagnosed as a permission issue. The root cause is always licensing. Check Setup > Company Information > Active Licenses before investigating permissions.

2. **Stages mapped to Omitted are silently excluded from all inspection totals** — Deals in Omitted stages do not appear in Pipeline Inspection open pipeline calculations. This is correct behavior, but it surprises teams that use Omitted for "on hold" deals they still intend to close. If managers need to review those deals, they must use the "Show Omitted" filter — there is no metric column that surfaces Omitted deal count by default.

3. **Days in Stage threshold is global — it does not vary by stage or segment** — Pipeline Inspection applies a single Days in Stage threshold across all open stages. Teams with multi-stage cycles of significantly different expected durations must rely on meeting-level filtering rather than expecting the platform to differentiate thresholds by stage.

4. **Pipeline change lookback window resets on page load — it is not persisted per user** — The lookback window selector in Pipeline Inspection is a session-level UI control. It does not save per user. Every time a manager opens the inspection view, it defaults to the system-configured window. There is no admin workaround for per-user persistent window selection as of Spring '25.

5. **Associating a split-based forecast type with Pipeline Inspection changes visible amounts** — When a forecast type that uses Opportunity Splits as its source object is selected in Pipeline Inspection, the Amount column reflects the split-attributed amount for the viewing user, not the full Opportunity Amount. This confuses managers who expect to see the total deal size.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Pipeline Inspection configuration checklist | Completed checklist confirming licensing, feature toggle, metric settings, forecast type associations, and user access |
| Stage-to-forecast-category mapping audit | Table of all Stage values, their ForecastCategoryName, IsClosed, and IsWon values — used to verify correct grouping in Pipeline Inspection |
| Review cadence design document | Meeting frequency, scope definition, Days in Stage escalation thresholds, and re-forecast trigger rules |
| Pipeline-review spec (YAML) | `templates/pipeline-review-spec-template.yaml` filled in: cadence, roles, field inventory, metrics with owner and target, hygiene rules, artefact list |
| Review pack metadata | Deployable `Report`, `Dashboard` and `ListView` XML plus the package.xml, shaped from `references/worked-examples.md` §4–§6 and §9 |
| Pipeline Inspection settings (optional) | `OpportunitySettings` flags and `PipelineInspMetricConfig` files, where the feature itself is being deployed rather than clicked |
| Data-hygiene rule intent | Close Date, Amount and Next Step rules stated as intent plus formula, for `admin/validation-rules` to turn into `ValidationRule` metadata |
| Cadence and RACI table | Who updates deals, who runs the meeting, who owns each metric definition, and when the definitions are re-reviewed |
| Checker output | Output of `check_pipeline_review_design.py --manifest-dir` listing spec and metadata issues found in the pack |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | Building the pack: a full B2B SaaS weekly review carried end to end — agenda, metric-to-field map, the linted spec, deployable Report / Dashboard / ListView XML, the deployable half of Pipeline Inspection, hygiene rules, RACI, package.xml and verification SOQL |
| `references/gotchas.md` | Fourteen platform behaviours behind most wrong pipeline numbers — the `LastStageChangeInDays` age fallback, feature-gated fields, `PushCount` semantics, unwritable `Amount`, fiscal vs calendar intervals, and the fourth forecast vocabulary |
| `references/examples.md` | Worked enablement, forecast-category diagnosis and stall-threshold scenarios, plus the SOQL that shows why a custom days-in-stage formula field is worse than the platform field |
| `references/well-architected.md` | Pillar mapping, the inspection-view-vs-report-pack and native-field-vs-snapshot tradeoffs, and the official-source list behind every claim in this package |
| `references/llm-anti-patterns.md` | Self-checking generated output — the six ways an assistant gets Pipeline Inspection and pipeline metrics wrong |
| `templates/pipeline-review-spec-template.yaml` | Starting a new review: the YAML shape `scripts/check_pipeline_review_design.py` lints |
| `scripts/check_pipeline_review_design.py` | Gating the pack before deploy: metric completeness, unique ids, resolvable sources, and every Report / ListView column checked against the spec |

---

## Related Skills

- admin/opportunity-management — where the stage ladder, its `ForecastCategoryName` mapping and the sales process are actually configured
- admin/sales-process-mapping — agree the stages and their exit criteria before any metric is defined against them
- admin/collaborative-forecasts — forecast types, rollups, quotas and the hierarchy that Pipeline Inspection reads
- admin/reports-and-dashboards — folder sharing, running-user semantics, subscriptions, and the canonical Report / Dashboard metadata reference
- admin/report-type-strategy — when the review pack outgrows the standard `Opportunity` report type and needs a custom one
- admin/list-views-and-compact-layouts — list-view column tokens, `sharedTo`, and sprawl control for the stale-deals view
- admin/validation-rules — turning the data-hygiene rules into deployable `ValidationRule` metadata
- admin/revenue-intelligence-setup — the Revenue Intelligence app, Revenue Insights and AI deal insights that sit above this
- admin/report-performance-tuning — when the pipeline report is slow rather than wrong
