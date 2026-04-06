# LLM Anti-Patterns — Pipeline Review Design

Common mistakes AI coding assistants make when generating or advising on Pipeline Review Design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Pipeline Inspection Without Verifying Licensing

**What the LLM generates:** "To set up Pipeline Inspection, go to Setup > Pipeline Inspection and enable the toggle."

**Why it happens:** LLMs trained on Salesforce documentation reproduce setup instructions without including the prerequisite licensing check. Pipeline Inspection instructions in Salesforce Help include the license requirement, but it appears early in the documentation and is easy to omit when synthesizing step-by-step instructions.

**Correct pattern:**

```
Step 1: Verify licensing before any other action.
  Setup > Company Information > Active Salesforce Licenses
  Confirm presence of: "Revenue Intelligence" OR "Sales Cloud Einstein"

  If neither is present:
    - Pipeline Inspection cannot be enabled
    - The enable toggle will be absent from Setup
    - Escalate to Account Executive for license provisioning
    - Do NOT proceed with troubleshooting permissions

Step 2: Only after license confirmed → Setup > Pipeline Inspection > Enable
```

**Detection hint:** If advice to "enable Pipeline Inspection" does not include a licensing check as the first step, the advice is incomplete. Flag any response that jumps directly to Setup navigation without license verification.

---

## Anti-Pattern 2: Conflating Pipeline Inspection with Dashboard Building

**What the LLM generates:** "To build a pipeline review dashboard, use Pipeline Inspection or create CRM Analytics dashboards that show pipeline changes over time."

**Why it happens:** LLMs associate "pipeline review" with dashboards and reporting tooling. They do not clearly distinguish between Pipeline Inspection (a native forecast-layer view) and CRM Analytics dashboards (a separate analytics product). The two are frequently mentioned together in Salesforce marketing content.

**Correct pattern:**

```
Pipeline Inspection:
  - Native feature within the Forecasts page
  - Requires Revenue Intelligence or Sales Cloud Einstein license
  - Shows inline change metrics on live opportunity data
  - NOT a dashboard — cannot be customized with charts or KPIs

CRM Analytics / Tableau CRM dashboards:
  - Separate product requiring CRM Analytics license
  - Fully customizable with charts, datasets, cross-object analysis
  - Used for executive reporting, trend analysis, cohort analysis

Do not recommend CRM Analytics dashboards as an alternative when the user
asks about Pipeline Inspection setup. Recommend CRM Analytics only when
the user's requirements exceed what Pipeline Inspection natively provides.
```

**Detection hint:** Responses that use "pipeline inspection dashboard" or "build a Pipeline Inspection report" conflate the two. Pipeline Inspection is not a dashboard and cannot be built — it is enabled and configured.

---

## Anti-Pattern 3: Claiming ForecastCategoryName Can Be Renamed

**What the LLM generates:** "You can rename forecast categories like 'Commit' and 'Best Case' to match your company's terminology in Setup > Forecast Settings."

**Why it happens:** LLMs infer from general Salesforce picklist customization capabilities that category names can be renamed. The ForecastCategoryName field values are platform-fixed and not configurable. Spring '24 introduced custom forecast categories but those are additive — they do not allow renaming the core five values.

**Correct pattern:**

```
ForecastCategoryName platform-fixed values (cannot be renamed):
  - Pipeline
  - Best Case
  - Most Likely
  - Commit
  - Omitted
  - Closed (used for IsClosed=true stages)

What IS possible as of Spring '24:
  - Create additional custom forecast categories (additive only)
  - These appear alongside the standard categories in Pipeline Inspection
    once associated with a forecast type

What is NOT possible:
  - Rename "Commit" to "Called"
  - Rename "Best Case" to "Upside"

Correct guidance for terminology alignment:
  - Use field help text on StageName to explain internal terminology mapping
  - Use Path guidance text per stage to explain the mapping
  - Document in team playbooks
```

**Detection hint:** Any response claiming forecast category labels can be renamed or relabeled in the UI is incorrect. Flag "you can rename forecast categories" statements immediately.

---

## Anti-Pattern 4: Suggesting Custom Formula Fields for Days in Stage Instead of the Native Metric

**What the LLM generates:**

```
// Create this formula field on Opportunity:
// Days_In_Current_Stage__c (Number)
// Formula: TODAY() - Stage_Entry_Date__c

// Then create a Flow to capture Stage_Entry_Date__c each time Stage changes
```

**Why it happens:** LLMs default to "build it yourself" solutions for metrics they do not recognize as being natively available. Days in Stage is a native Pipeline Inspection metric that requires no custom fields, formulas, or triggers. LLMs trained before Pipeline Inspection was widely documented will suggest a custom implementation.

**Correct pattern:**

```
Native Days in Stage is available in Pipeline Inspection:
  Setup > Manage Pipeline Inspection Metrics
    Days in Stage: Enable → ON
    Threshold: set to desired number of days

This requires:
  - Revenue Intelligence or Sales Cloud Einstein license
  - Pipeline Inspection enabled

The platform calculates Days in Stage from the Stage transition history
automatically. No formula field, Flow, or Apex trigger is needed.

When to still build a custom field:
  - You need the Days in Stage value in a standard report (not inspection view)
  - You need the value in a process or Flow condition
  - Users who lack forecast hierarchy access need to see it
  In those cases: custom field supplements the native metric; does not replace it.
```

**Detection hint:** If the response includes a formula field or trigger to calculate "days in current stage" without first noting the native Pipeline Inspection metric, the response is incomplete and likely unnecessary.

---

## Anti-Pattern 5: Treating Pipeline Inspection as an Enforcement Mechanism

**What the LLM generates:** "Configure Pipeline Inspection to prevent reps from pushing close dates without manager approval. The Stage Changed metric will block unauthorized stage movements."

**Why it happens:** LLMs conflate visibility with control. Pipeline Inspection detects and surfaces changes — it does not block or gate them. The "Stage Changed" column is a read-only metric. LLMs may infer enforcement capability from the feature's name or from descriptions of its change-detection functionality.

**Correct pattern:**

```
Pipeline Inspection capabilities:
  - Detect: Yes — surfaces amount changes, close date changes, stage changes
  - Alert: Yes — visual highlights when thresholds are met
  - Block: No — Pipeline Inspection cannot prevent saves, require approvals,
              or enforce any data quality rule

Enforcement mechanisms (separate from Pipeline Inspection):
  - Validation Rules: prevent saving records that do not meet field conditions
  - Approval Processes: require manager approval before field values can change
  - Flow with Decision element: implement stage-progression enforcement rules

Correct design:
  - Pipeline Inspection = visibility layer (shows what changed)
  - Validation Rules + Approval Processes = enforcement layer (controls what can change)
  - These are complementary, not interchangeable
```

**Detection hint:** Any response claiming Pipeline Inspection "prevents," "blocks," "requires approval for," or "enforces" deal changes is incorrect. Pipeline Inspection is a read-only inspection tool.

---

## Anti-Pattern 6: Assuming Pipeline Inspection Works Without Collaborative Forecasting

**What the LLM generates:** "Pipeline Inspection works independently — you do not need to set up Collaborative Forecasting first. Just enable it in Setup."

**Why it happens:** Pipeline Inspection is described in some Salesforce documentation as a standalone feature. LLMs miss the dependency on Collaborative Forecasting being active, because the dependency is listed as a prerequisite rather than being repeated in the setup steps.

**Correct pattern:**

```
Prerequisites for Pipeline Inspection (ALL must be true):
  1. Revenue Intelligence or Sales Cloud Einstein license is active
  2. Collaborative Forecasting is enabled:
     Setup > Forecasts Settings > Enable Forecasts = ON
  3. At least one active Forecast Type exists:
     Setup > Forecast Settings > Forecast Types > at least 1 active type
  4. The forecast type must be associated with Pipeline Inspection:
     Setup > Pipeline Inspection > associate forecast type

If Collaborative Forecasting is not enabled:
  - Pipeline Inspection has no data source to draw from
  - The feature may appear to enable successfully but will show no data
  - The error manifests as an empty inspection view, not a setup error

Verify ALL four prerequisites before attempting enablement.
```

**Detection hint:** Any Pipeline Inspection setup guidance that does not mention Collaborative Forecasting as a prerequisite is incomplete. Flag responses that treat Pipeline Inspection as dependency-free.
