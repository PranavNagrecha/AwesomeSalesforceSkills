# Examples — Pipeline Review Design

## Example 1: Enabling Pipeline Inspection for a Mid-Market Sales Team

**Context:** A Sales Ops admin is asked to enable Pipeline Inspection for a mid-market sales team of 12 reps and 3 managers. The org has Sales Cloud Einstein. Collaborative Forecasting is active with one forecast type using Opportunity as the source object.

**Problem:** Without Pipeline Inspection, managers run weekly pipeline reviews using a manually refreshed report. They cannot see inline change metrics (amount trimmed, date pushed, stage moved backwards) without cross-referencing multiple reports. The review takes 90 minutes because managers must switch between the forecast page and separate pipeline reports.

**Solution:**

```
Setup > Pipeline Inspection
  1. Enable Pipeline Inspection: ON
  2. Associate forecast types:
     - Opportunity Forecast (primary) → ENABLED
  3. Navigate to Setup > Manage Pipeline Inspection Metrics:
     - Days in Stage: ENABLED, threshold = 14 days
     - Amount Changed: ENABLED
     - Close Date Changed: ENABLED
     - Stage Changed: ENABLED
  4. Verify forecast hierarchy includes all 3 managers as forecast managers
     and 12 reps as subordinates under each manager.
  5. Verify managers have "View All Forecasts" OR direct subordinate visibility
     in the active forecast hierarchy.
```

**Why it works:** Pipeline Inspection layers change-detection columns directly onto the live Opportunity list within the Forecasts page. Managers see deal movement without leaving the forecast context. The 14-day Days in Stage threshold aligns to the team's average 28-day deal cycle — deals in the same stage for half the expected cycle are surfaced for review.

---

## Example 2: Diagnosing Why Commit Deals Are Missing from Pipeline Inspection

**Context:** A sales manager reports that several high-confidence deals are not appearing in the Commit category of Pipeline Inspection, even though reps have moved them to the "Proposal/Price Quote" stage which the team considers Commit-level confidence.

**Problem:** The admin discovers that the "Proposal/Price Quote" stage has its `ForecastCategoryName` set to `Best Case` rather than `Commit` in the Stage picklist configuration. Pipeline Inspection groups deals strictly by their stage's `ForecastCategoryName` — it does not use the Opportunity's editable Forecast Category field override unless that override is explicitly set on the record.

**Solution:**

```
Step 1: Audit Stage picklist values
  Setup > Opportunity Stages → review ForecastCategoryName for each stage:

  Stage: Proposal/Price Quote
    ForecastCategoryName: Best Case  ← incorrect for this team's intent

Step 2: Decision point
  Option A — Change the stage's ForecastCategoryName to Commit:
    - Correct if this stage genuinely represents Commit-level confidence
    - Changes how this stage appears in ALL existing forecast rollups

  Option B — Use the editable Forecast Category override per opportunity:
    - Reps manually set Forecast Category to "Commit" on individual records
    - Stage-level mapping stays at Best Case
    - Appropriate if the same stage can be either Best Case or Commit
      depending on deal specifics
    - Requires: Setup > Forecasts > Enable "Allow Forecast Category Override"

Step 3: If Option A chosen:
  Setup > Opportunity Stages > Edit "Proposal/Price Quote"
    ForecastCategoryName: Commit → Save
  Verify existing opportunities reflect the updated category in Pipeline Inspection.
```

**Why it works:** Pipeline Inspection reads `ForecastCategoryName` from the Opportunity record, which is either derived from the Stage's default mapping or overridden per record when "Allow Forecast Category Override" is enabled. Fixing the stage-level mapping is the cleanest solution when the stage consistently represents one confidence level.

---

## Example 3: Configuring a Stage Stall Alert for a 60-Day Sales Cycle

**Context:** An enterprise sales team has a 60-day average deal cycle. Deals in "Technical Evaluation" and "Business Justification" stages are the highest-risk stall points. The team wants Pipeline Inspection to highlight deals stuck in those stages for more than 21 days.

**Problem:** By default, Pipeline Inspection applies a single Days in Stage threshold to all stages. The admin needs to set a threshold meaningful for the highest-risk stages without flooding every stage with false-positive highlights.

**Solution:**

```
Setup > Manage Pipeline Inspection Metrics
  Days in Stage: ENABLED
  Threshold for highlight: 21 days

Review cadence configuration (documented in team playbook, not in Setup):
  - During Monday pipeline review, manager sorts Pipeline Inspection by
    "Days in Stage" descending
  - Deals in Technical Evaluation or Business Justification with Days in Stage
    > 21 are reviewed first
  - Manager applies stage filter in the inspection view for focused review
  - Other stages: 21-day threshold may flag deals, but manager de-prioritizes
    those visually based on stage context

Note: Stage-specific thresholds are not natively supported as of Spring '25.
  The 21-day global threshold is chosen as the minimum meaningful signal
  for the highest-risk stages in this 60-day cycle.
```

**Why it works:** The global threshold is set to the minimum value meaningful for the riskiest stages. Combined with manager-level stage filtering during review meetings, the team achieves targeted deal health monitoring without needing stage-specific thresholds.

---

## Anti-Pattern: Building a Custom Formula Field for Days in Current Stage

**What practitioners do:** Admins create a custom Date field `Stage_Entry_Date__c` on Opportunity, set it via Flow each time the Stage changes, then add a formula field `Days_In_Stage__c = TODAY() - Stage_Entry_Date__c`. They display this formula field in reports and list views.

**What goes wrong:** This duplicates functionality already provided natively by Pipeline Inspection's Days in Stage metric. The custom formula approach requires flow maintenance, breaks when flows are deactivated or missing trigger conditions, and produces stale values if the flow misfires. The formula value in a report does not benefit from Pipeline Inspection's visual highlight and change-window context. The native Days in Stage metric is recalculated from the platform's stage transition history and requires no additional field configuration.

**Correct approach:** Use Pipeline Inspection's native Days in Stage metric configured in Setup > Manage Pipeline Inspection Metrics. Reserve custom formula fields only for reporting use cases that need the value outside the Pipeline Inspection context (e.g., a report used by executives who do not have forecast hierarchy access). Even in those cases, document that the formula field is a reporting supplement — not a replacement for the native metric.
