---
name: pipeline-review-design
description: "Configuring and running Pipeline Inspection in Sales Cloud: enabling the feature, mapping forecast categories to the inspection view, configuring Days in Stage and other metrics, setting review cadence, and interpreting pipeline change signals for sales managers. Use when designing or improving how a team monitors deal health and pipeline movement. NOT for building custom dashboards or reports (use reports-and-dashboards skill). NOT for enabling Einstein Opportunity Scoring or AI insights (use einstein-copilot-for-sales skill). NOT for setting up Collaborative Forecasts or forecast types (use collaborative-forecasts skill)."
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
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
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

## Core Concepts

### Pipeline Inspection and Licensing Requirements

Pipeline Inspection is a Sales Cloud feature that provides a consolidated view of opportunities with inline metric columns showing how deals have changed over a configurable lookback window (default: 7 days for pipeline changes; configurable up to 90 days for historical comparisons). It is enabled at Setup > Pipeline Inspection and requires either **Revenue Intelligence** or **Sales Cloud Einstein** licensing.

The feature is not a report or dashboard — it is a specialized list view layered on top of the Forecasts page, accessible to forecast managers. It surfaces Opportunity fields alongside calculated change metrics without requiring SOQL reports or custom analytics. This distinction matters for scope: Pipeline Inspection cannot be substituted for a CRM Analytics dashboard, and it cannot replace the Forecasts page for quota attainment tracking.

### Forecast Categories and the Inspection View

Pipeline Inspection groups and filters opportunities by Forecast Category, which maps directly to the `ForecastCategoryName` field on each Stage picklist value. The five default categories available in Pipeline Inspection are:

- **Commit** — high-confidence deals the rep is committing to close
- **Best Case** — deals the rep expects to close with additional effort
- **Most Likely** — deals that are probable but not fully committed (available when Most Likely forecast type is active)
- **Open Pipeline** — earlier-stage deals in active consideration
- **Omitted** — excluded from all forecast rollups; these are hidden from Pipeline Inspection totals unless specifically filtered for

Starting Spring '24, admins can create custom forecast categories in addition to or as replacements for some of the defaults. Custom categories appear in Pipeline Inspection once the underlying forecast type is associated with Pipeline Inspection via Setup > Pipeline Inspection > Forecast Types.

Stages mapped to `Closed` (IsClosed=true) appear in the Closed Won / Closed Lost groupings in the inspection view and are not included in the open pipeline metrics. Deals in Omitted stages are excluded from totals but can be viewed using the "Show Omitted" filter toggle.

### Pipeline Change Metrics and Days in Stage

Pipeline Inspection exposes a set of configurable metric columns that highlight deal movement. The core metrics available are:

- **Amount Changed** — net change in Opportunity Amount over the lookback window
- **Close Date Changed** — flag when the Close Date has been pushed out
- **Stage Changed** — flag when the Stage has moved (forward or backward)
- **Days in Stage** — how many days the opportunity has been in its current stage without advancing; this is a native metric calculated by the platform and does not require a formula field

Days in Stage is configured in Setup > Manage Pipeline Inspection Metrics. It is not derived from a custom field — the platform calculates it from the stage transition event log. Admins can configure the threshold that triggers a visual highlight (e.g., flag deals that have been in the same stage for more than 14 days).

Metric columns can be shown or hidden per inspection view. Not all metrics are available without Revenue Intelligence — some advanced metrics (e.g., AI-powered deal health scores) require the full Revenue Intelligence license rather than just Sales Cloud Einstein.

### Forecast Type Association with Pipeline Inspection

Pipeline Inspection must be associated with one or more active Collaborative Forecasts forecast types to determine which opportunities it surfaces. In Setup > Pipeline Inspection, each active forecast type can be toggled on or off for inclusion in the inspection view. If a forecast type uses Opportunity Splits as its source object, the inspection view will reflect split-credited amounts rather than the full Opportunity Amount.

Associating a forecast type with Pipeline Inspection does not change the forecast type itself. It only controls which source data feeds the inspection view's metric calculations. If multiple forecast types are active (e.g., one for Opportunities and one for Products), each will appear as a selectable filter in the Pipeline Inspection view.

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

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Verify licensing and prerequisites: Confirm Revenue Intelligence or Sales Cloud Einstein is provisioned (Setup > Company Information). Confirm Collaborative Forecasting is enabled and at least one active forecast type exists. Confirm the admin user has the Customize Application and Manage Pipeline Inspection permissions.
2. Enable Pipeline Inspection in Setup > Pipeline Inspection. Toggle the feature on. Associate each active forecast type the sales team uses for pipeline reviews. Do not associate forecast types that are experimental or not aligned to current quota plans.
3. Configure metrics in Setup > Manage Pipeline Inspection Metrics. At minimum enable: Days in Stage, Amount Changed, Close Date Changed, and Stage Changed. Set the Days in Stage highlight threshold to reflect the typical sales cycle (e.g., 14 days for a 30-day average deal cycle). Document this threshold so managers understand when a deal is flagged.
4. Review Stage picklist ForecastCategoryName mappings in Setup > Opportunity Stages. Verify that every revenue-bearing stage is mapped to Pipeline, Best Case, Most Likely, or Commit. Verify that truly inactive or discarded stages are mapped to Omitted. Fix any misalignments before reviewing inspection data.
5. Validate user access: confirm that sales managers who will use Pipeline Inspection are in the active forecast hierarchy under Setup > Forecasts > Forecast Settings. Confirm they have "View All Forecasts" or direct subordinate relationship to the opportunities they need to review.
6. Run the skill-local checker: `python3 skills/admin/pipeline-review-design/scripts/check_pipeline_review_design.py --manifest-dir path/to/metadata`. Review all flagged issues before concluding configuration.
7. Design the review cadence with stakeholders: define meeting frequency, who reviews which segment, how stalled deals are handled, and when re-forecast updates are triggered by Pipeline Inspection signals.

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
| Checker output | Output of `check_pipeline_review_design.py` listing metadata issues found in the deployed manifest |

---

## Related Skills

- opportunity-management — use when Stage picklist values and ForecastCategoryName mappings need to be created or corrected before Pipeline Inspection configuration
- collaborative-forecasts — use when designing the underlying forecast types and hierarchy that Pipeline Inspection depends on
- einstein-copilot-for-sales — use when AI-powered deal health scores or Opportunity Scoring insights inside Pipeline Inspection are required
- reports-and-dashboards — use when the team needs custom pipeline analytics beyond what Pipeline Inspection natively surfaces
