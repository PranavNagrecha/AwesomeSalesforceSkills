# LLM Anti-Patterns — Collaborative Forecasts

Common mistakes AI coding assistants make when generating or advising on Collaborative Forecasts.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming You Can Recover Adjustments After a Rollup Method Change

**What the LLM generates:** "If you switch from single-category to cumulative rollup, you can restore your adjustments from the ForecastingAdjustment object or by using the Recycle Bin."

**Why it happens:** LLMs generalize from the pattern that most Salesforce data deletions are soft-deletes recoverable via Recycle Bin. ForecastingAdjustment deletions triggered by rollup method changes are hard-deletes with no recovery mechanism — this is a documented exception that training data may underrepresent.

**Correct pattern:**
```
Switching rollup method permanently and irrecoverably deletes all ForecastingAdjustment
records for that Forecast Type. There is no Recycle Bin recovery, no API restore,
and no support case path to recover the records. The only mitigation is to export
ForecastingAdjustment records via Data Loader BEFORE making the change.
```

**Detection hint:** Any response that suggests "recovery," "undo," "Recycle Bin," or "restore" in the context of rollup method changes is incorrect.

---

## Anti-Pattern 2: Asserting That Role Assignment Automatically Enables a User in the Forecast Hierarchy

**What the LLM generates:** "Once you assign a user to a role in the role hierarchy, they will automatically appear in the Collaborative Forecast for that role's position."

**Why it happens:** Role hierarchy is the structural basis for the forecast hierarchy, and LLMs often conflate "belongs to the hierarchy" with "appears in the forecast." The `ForecastEnabled` field is a separate, explicit enablement step that is easily overlooked.

**Correct pattern:**
```
A user appears in the Collaborative Forecast hierarchy only when TWO conditions are met:
1. The user has a role assigned that is part of the forecast role hierarchy.
2. The user's ForecastEnabled field is set to true.

Role assignment alone is not sufficient. ForecastEnabled must be explicitly set
on each user record — via Setup UI, Data Loader, or API update.
```

**Detection hint:** Any response that only mentions "assign the correct role" without also mentioning `ForecastEnabled = true` is incomplete.

---

## Anti-Pattern 3: Suggesting More Than 4 Active Forecast Types Without Noting the Limit

**What the LLM generates:** "You can create as many Forecast Types as you need — one for each product family, one for each region, and one for each sales motion."

**Why it happens:** Salesforce documentation for Forecast Types describes creation and configuration but the active-type limit is a capacity constraint documented separately. LLMs trained on configuration guides may not surface the limit unless specifically asked.

**Correct pattern:**
```
Salesforce supports up to 4 ACTIVE Forecast Types by default per org.
Additional types can exist in inactive state. If more than 4 active types
are required, a Salesforce Support case is required to request a limit increase.
Design Forecast Types to cover the highest-value reporting dimensions and
combine motions where possible before requesting an increase.
```

**Detection hint:** Any response that proposes more than 4 Forecast Types without acknowledging the default limit is incomplete.

---

## Anti-Pattern 4: Advising That Manager Judgment Works on All Forecast Types Including Split-Based

**What the LLM generates:** "Your forecast managers can use Manager Judgment to adjust any subordinate's forecast total, regardless of which Forecast Type is in use."

**Why it happens:** Manager Judgment is a prominent feature of Collaborative Forecasts described prominently in documentation. The exception for split-based types (Opportunity Splits, Product Splits) is a less-prominent constraint that LLMs frequently miss.

**Correct pattern:**
```
Manager Judgment (manager-level owner adjustments) is NOT available for
Forecast Types sourced from Opportunity Splits or Product Splits.
It is only available for Forecast Types sourced from Opportunity,
Opportunity Product (Product Family), or Line Item Schedule.

For split-based types, managers cannot adjust subordinate forecast totals.
Communicate this limitation to sales managers before rolling out split-based types.
```

**Detection hint:** Any response that promises manager adjustment capability for split-based forecast types without noting this exception is incorrect.

---

## Anti-Pattern 5: Treating Forecast Category Mapping as a Per-Forecast-Type Setting

**What the LLM generates:** "You can configure different stage-to-category mappings for each Forecast Type — for example, map 'Negotiation' to Commit in your AE forecast but to Best Case in your SE overlay forecast."

**Why it happens:** Since each Forecast Type has independent settings for source object, hierarchy, and rollup method, LLMs may assume stage-to-category mapping is also per-type. In reality, stage mapping is a global org setting.

**Correct pattern:**
```
Stage-to-forecast-category mapping is a GLOBAL org setting.
It applies to ALL Forecast Types identically — there is no per-type stage mapping.
Every opportunity stage maps to exactly one forecast category,
and that mapping applies across all active Forecast Types simultaneously.

If different sales motions need different stage-category semantics,
this must be handled through separate opportunity stage values or
alternative pipeline reporting outside of Collaborative Forecasts.
```

**Detection hint:** Any response that describes per-type stage mapping configuration is incorrect.

---

## Anti-Pattern 6: Recommending Quota Loads Without Specifying ForecastingTypeId

**What the LLM generates:** "Load quotas by creating ForecastingQuota records with the user ID, the period start date, and the quota amount."

**Why it happens:** LLMs may describe the most prominent fields on the ForecastingQuota object without noting that quotas are specific to a particular Forecast Type. In orgs with multiple active Forecast Types, a quota without a ForecastingTypeId reference will be ambiguous or fail to associate with the intended type.

**Correct pattern:**
```
ForecastingQuota records require ALL of these fields:
  - QuotaOwnerId      (user ID)
  - StartDate         (must exactly match forecast period boundary date)
  - QuotaAmount       (currency value)
  - ForecastingTypeId (ID of the specific ForecastingType — required)
  - CurrencyIsoCode   (required in multi-currency orgs)

Without ForecastingTypeId, quota records may load successfully
but will not display attainment for any specific Forecast Type.
Query: SELECT Id, Name FROM ForecastingType
to obtain the correct ID before bulk-loading quota records.
```

**Detection hint:** Any quota load guidance that omits `ForecastingTypeId` as a required field is incomplete.
