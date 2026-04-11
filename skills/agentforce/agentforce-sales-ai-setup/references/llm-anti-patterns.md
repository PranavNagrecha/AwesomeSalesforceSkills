# LLM Anti-Patterns — Agentforce Sales AI Setup

Common mistakes AI coding assistants make when generating or advising on Einstein for Sales setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming Opportunity Scoring Works in Sandboxes

**What the LLM generates:** "Enable Einstein Opportunity Scoring in your sandbox, assign the permission set, and verify that scores appear on opportunity records within 24 hours."

**Why it happens:** LLMs default to sandbox-first guidance because sandbox testing is the standard Salesforce deployment practice. The sandbox limitation for Opportunity Scoring model training is a platform-specific constraint that runs counter to the general rule, so it is under-represented in training data.

**Correct pattern:**

```
Opportunity Scoring model training only runs in production orgs.
Sandbox validation is limited to:
- Confirming the Setup toggle works
- Confirming permission set assignment
- Confirming the Opportunity Score field is on the page layout

Score generation validation must be performed in production
or a developer org loaded with production-representative data.
```

**Detection hint:** Any guidance that says "verify scores appear in sandbox" or "test Opportunity Scoring in your [sandbox type] sandbox" is incorrect.

---

## Anti-Pattern 2: Treating Einstein for Sales as a Single License That Enables All Features

**What the LLM generates:** "Purchase the Einstein for Sales add-on and you'll have access to Opportunity Scoring, Pipeline Inspection, and AI email composition for your reps."

**Why it happens:** LLMs often collapse Salesforce product marketing language (which uses "Einstein for Sales" as an umbrella term) with actual license SKU behavior. The Einstein Generative AI add-on is a distinct license tier that is sometimes bundled (in Einstein 1 Sales edition) but is NOT included in the base Einstein for Sales add-on.

**Correct pattern:**

```
Einstein for Sales add-on includes:
- Opportunity Scoring
- Einstein Activity Capture
- Pipeline Inspection (with AI insights when Collaborative Forecasting is enabled)
- Einstein Relationship Insights

Einstein Generative AI (separate license) additionally unlocks:
- AI email composition (generative draft emails for reps)

To confirm: Setup > Company Information > Feature Licenses
Look for BOTH "Einstein for Sales" AND "Einstein Generative AI"
before planning email composition rollout.
```

**Detection hint:** Any guidance that lists "AI email composition" or "Generate Email" as a feature unlocked by Einstein for Sales without mentioning the Einstein Generative AI license is incorrect.

---

## Anti-Pattern 3: Enabling Pipeline Inspection Without Checking Collaborative Forecasting

**What the LLM generates:** "Enable Opportunity Scoring, wait for the model to train, then enable Pipeline Inspection. AI insights will appear for your forecast managers."

**Why it happens:** The Collaborative Forecasting dependency for Pipeline Inspection AI insights is a non-obvious cross-feature dependency. LLMs trained on Salesforce help documentation may associate Pipeline Inspection primarily with Einstein for Sales and Opportunity Scoring, missing the Collaborative Forecasting prerequisite.

**Correct pattern:**

```
Pipeline Inspection AI insights require ALL THREE of the following:
1. Einstein for Sales license active
2. Opportunity Scoring model status = "Active"
3. Collaborative Forecasting enabled (Setup > Forecasts Settings)

If Collaborative Forecasting is not enabled, Pipeline Inspection
renders deal movement data but AI insights column is absent with no error.
```

**Detection hint:** Any Pipeline Inspection enablement checklist that does not include "Confirm Collaborative Forecasting is enabled" is missing a critical step.

---

## Anti-Pattern 4: Skipping the Pre-Enablement Opportunity Data Check

**What the LLM generates:** "Go to Setup > Einstein > Sales > Opportunity Scoring and toggle the feature on. The model will train automatically and scores will appear within 24–72 hours."

**Why it happens:** LLMs replicate the Salesforce Help documentation's enablement steps accurately but omit the pre-enablement data readiness validation. The Setup UI does not block enablement for orgs with insufficient data, so the validation step is easy to miss from documentation alone.

**Correct pattern:**

```sql
-- Run BEFORE enabling Opportunity Scoring
SELECT COUNT(Id) closedOppsInRange
FROM Opportunity
WHERE IsClosed = true
AND CloseDate = LAST_N_DAYS:730

-- Result must be >= 200 to proceed
-- If < 200: defer enablement, do not enable the toggle
```

If the result is below 200, the model enters "Insufficient Data" status after training fails, and scores never appear — even though the feature appears active.

**Detection hint:** Any Opportunity Scoring enablement guidance that does not include a pre-check for closed opportunity count is incomplete.

---

## Anti-Pattern 5: Conflating Einstein Opportunity Scoring Model Training Cadence with Real-Time Scoring

**What the LLM generates:** "Opportunity Scoring updates in real time as reps update opportunity fields — the score reflects the current state of the deal."

**Why it happens:** LLMs associate AI scoring with real-time inference, which is the architecture for many AI scoring products. Salesforce Opportunity Scoring uses a batch-trained weekly model, not real-time inference. Scores are updated on a weekly retraining cycle, not immediately when field values change.

**Correct pattern:**

```
Einstein Opportunity Scoring behavior:
- Initial model training: 24–72 hours after enablement (for qualifying orgs)
- Model retrains: weekly (not real-time)
- Score updates: scores on individual opportunities update on the weekly retraining cycle
- Field changes by reps do NOT trigger immediate score recalculation
- Score factors reflect the state captured during the last training run

Implication: if a rep closes a major deal that would shift scoring factors,
scores on other opportunities reflect that shift only after the next weekly retrain.
```

**Detection hint:** Any guidance that describes Opportunity Scoring as "real-time," "instant," or "updating when fields change" is incorrect.

---

## Anti-Pattern 6: Recommending Sandbox for Full Einstein for Sales Acceptance Testing

**What the LLM generates:** "Complete your Einstein for Sales acceptance testing in a Full Sandbox before deploying to production to ensure all features work correctly."

**Why it happens:** Full Sandbox testing is the standard best practice for Salesforce deployments. LLMs apply this general rule uniformly without accounting for Einstein for Sales-specific platform constraints.

**Correct pattern:**

```
Einstein for Sales sandbox validation scope:
✓ Enablement flow (Setup toggles)
✓ Permission set assignment
✓ Page layout configuration (Opportunity Score field, Pipeline Inspection tab)
✓ User access verification

Cannot be validated in sandbox:
✗ Opportunity Scoring model training
✗ Score generation on opportunity records
✗ Pipeline Inspection AI insights (requires Active model)

Separate the enablement acceptance test (sandbox) from
the scoring/AI insights acceptance test (production, post go-live).
Document this split in UAT planning so testers do not
incorrectly flag missing scores as a deployment defect.
```

**Detection hint:** Any UAT guidance that includes "verify Opportunity Score values on records in sandbox" is setting incorrect expectations.
