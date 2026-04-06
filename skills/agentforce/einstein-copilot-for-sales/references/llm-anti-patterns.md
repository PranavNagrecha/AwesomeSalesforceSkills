# LLM Anti-Patterns — Einstein Copilot For Sales

Common mistakes AI coding assistants make when generating or advising on Einstein AI features for Sales Cloud.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Enabling Opportunity Scoring Without Sufficient Historical Data

**What the LLM generates:** "Enable Einstein Opportunity Scoring in Setup and scores will appear on opportunities" without noting the minimum data requirements — at least 200 closed-won and 200 closed-lost opportunities with populated Amount, Close Date, and Stage fields over the past 2 years.

**Why it happens:** LLMs describe the enablement steps but not the data prerequisites. Einstein Opportunity Scoring trains a model on historical win/loss patterns. Without enough data, the model either fails to build or produces low-confidence scores that mislead reps.

**Correct pattern:**

```text
Einstein Opportunity Scoring prerequisites:

Data requirements:
- Minimum 200 closed-won AND 200 closed-lost opportunities
- Close dates within the past 24 months
- Amount field populated on most records
- Stage field consistently used (not skipped from Open to Closed)
- StageName values are standardized (not free-text variants)

Enablement steps:
1. Verify data quality BEFORE enabling
2. Setup > Einstein Opportunity Scoring > Enable
3. Wait for initial model training (24-72 hours)
4. Review model scorecard for accuracy metrics
5. If accuracy is below threshold, improve data quality first

Common failure modes:
- "No model available" — insufficient data volume
- Scores cluster around 50 — features are not predictive
  (Stage values are inconsistent, Amount is rarely filled)
- Scores change dramatically after data cleanup — expected,
  retrain will use the improved data
```

**Detection hint:** Flag Opportunity Scoring enablement guides that do not mention minimum record counts. Check for orgs enabling scoring with fewer than 400 total closed opportunities.

---

## Anti-Pattern 2: Assuming Einstein Activity Capture Syncs All Email and Calendar Data

**What the LLM generates:** "Enable Einstein Activity Capture and all rep emails and calendar events will be captured in Salesforce" without noting the selective sync configuration, privacy exclusion lists, and the fact that captured activities are NOT standard Activity records.

**Why it happens:** The name "Activity Capture" implies complete capture. LLMs do not distinguish between standard Salesforce activities (Tasks/Events) and Einstein Activity records, which live in a separate data store, are not reportable via standard reports, and are not included in SOQL queries on Task/Event objects.

**Correct pattern:**

```text
Einstein Activity Capture behavior:

What is captured:
- Emails and calendar events from connected accounts
  (Google Workspace or Microsoft 365)
- Matched to Salesforce contacts/leads by email address

What is NOT captured:
- Emails from domains on the exclusion list
- Calendar events marked as private
- Emails from unmatched email addresses (no contact/lead match)

Critical distinction:
- Captured activities are NOT standard Task/Event records
- They appear in the Activity Timeline on the record page
- They are NOT queryable via SOQL on Task or Event
- They are NOT included in standard Salesforce reports
- They ARE included in Einstein Activity reports (Analytics)

Configuration checklist:
1. Connect email provider (OAuth consent required per user)
2. Configure exclusion lists (internal domains, competitors)
3. Set sync direction (emails, calendar, or both)
4. Assign the Einstein Activity Capture permission set
5. Educate reps: these are NOT logged activities — manual
   logging is still needed for reportable activity metrics
```

**Detection hint:** Flag Activity Capture guides that claim all emails are captured without mentioning exclusion lists. Check for instructions that treat captured activities as standard Task/Event records. Flag reports built on Task/Event objects expecting Activity Capture data.

---

## Anti-Pattern 3: Confusing Einstein for Sales Features with Agentforce Agent Capabilities

**What the LLM generates:** "Use Einstein Copilot to automatically send follow-up emails to leads" when the user is asking about Einstein AI Email Generation (a Sales Cloud AI feature) and not about Agentforce Copilot (an autonomous agent). The two are different products with different setup paths.

**Why it happens:** Salesforce has rebranded and consolidated AI features multiple times. "Einstein Copilot," "Einstein for Sales," "Agentforce," and "Sales AI" overlap in marketing but refer to different capabilities. LLMs conflate them.

**Correct pattern:**

```text
Einstein for Sales feature disambiguation:

Einstein Opportunity Scoring — predictive score on Opportunity records
  Setup: Setup > Einstein Opportunity Scoring
  NOT an Agentforce feature. Standalone ML model.

Einstein Activity Capture — email and calendar sync
  Setup: Setup > Einstein Activity Capture
  NOT an Agentforce feature. Data integration.

Einstein AI Email Generation — draft emails for sales reps
  Setup: Setup > Einstein for Sales > Email
  Uses generative AI but is a Sales Cloud feature, not Agentforce.
  Rep triggers it from the email composer on a record page.

Pipeline Inspection AI — forecast and pipeline insights
  Setup: Sales Cloud > Pipeline Inspection
  Analytics feature. Not an agent.

Agentforce for Sales — autonomous agent handling sales tasks
  Setup: Agent Builder > create agent
  Requires Agentforce license. Different product.

When advising: confirm which feature the user is asking about
before providing setup instructions.
```

**Detection hint:** Flag advice that directs users to Agent Builder for Einstein Opportunity Scoring or Activity Capture. Check for Agentforce license requirements applied to standard Sales Cloud AI features.

---

## Anti-Pattern 4: Not Configuring Pipeline Inspection Prerequisites Before Expecting AI Insights

**What the LLM generates:** "Enable Pipeline Inspection and Einstein will show AI-powered pipeline insights" without noting that Pipeline Inspection requires Forecasting to be enabled with specific forecast types, and AI insights require historical forecast snapshot data.

**Why it happens:** Pipeline Inspection is presented as a single feature. In reality, it sits on top of Collaborative Forecasting and requires forecast hierarchies, forecast types, and historical snapshot data to power its AI insights.

**Correct pattern:**

```text
Pipeline Inspection prerequisite chain:

1. Collaborative Forecasting must be enabled
   - Setup > Forecasts Settings > Enable Forecasts
   - At least one forecast type configured (e.g., Opportunity Revenue)
   - Forecast hierarchy matches the role hierarchy or territory model

2. Forecast history tracking must accumulate data
   - AI insights use historical forecast snapshots
   - Minimum: 4-8 weeks of forecast data for meaningful trends
   - Insights improve over 3-6 months of data accumulation

3. Pipeline Inspection enablement:
   - Setup > Pipeline Inspection > Enable
   - Assign to the relevant forecast types
   - Users need "View All Forecasts" or be in the forecast hierarchy

4. AI insights appear ONLY when:
   - Sufficient historical forecast data exists
   - Opportunity data has consistent stage progression
   - Einstein for Sales license is assigned to users

Common issue: "Pipeline Inspection is enabled but I see no AI insights"
→ The forecast history has not accumulated enough data yet.
```

**Detection hint:** Flag Pipeline Inspection guides that skip the Collaborative Forecasting prerequisite. Check for AI insight expectations without historical forecast data accumulation.

---

## Anti-Pattern 5: Overlooking Data Quality Impact on Einstein Sales Predictions

**What the LLM generates:** "Einstein will analyze your opportunities and provide accurate predictions" without emphasizing that prediction quality is entirely dependent on data quality — inconsistent Stage values, missing Close Dates, stale pipeline, and duplicate records directly reduce prediction accuracy.

**Why it happens:** LLMs describe AI features optimistically. Einstein models are only as good as the data they train on. Poor data quality is the most common reason Einstein Sales features underperform, but it is not an Einstein configuration issue — it is a data governance issue.

**Correct pattern:**

```text
Data quality impact on Einstein Sales features:

Fields that directly affect model quality:
- StageName: must be used consistently (reps skip stages → bad signal)
- Amount: must be populated and realistic (not $0 or $1)
- CloseDate: must reflect actual expected close (not bulk-updated)
- Probability: should match StageName (custom mappings break this)
- OwnerId: should reflect the actual working rep

Data hygiene for Einstein:
1. Close stale opportunities (>6 months past CloseDate still Open)
2. Standardize Stage values (merge duplicate or similar stages)
3. Remove test and training opportunities from the dataset
4. Ensure at least 70% of closed opps have Amount populated
5. Deduplicate accounts and contacts used in opportunity matching

Monitoring:
- Review Einstein model scorecard after each retraining cycle
- Track prediction accuracy over time (predicted vs actual outcomes)
- If accuracy drops: investigate recent data quality changes

"Enable Einstein" is not a substitute for "fix your data."
```

**Detection hint:** Flag Einstein Sales enablement guides that do not mention data quality prerequisites. Check for orgs with more than 30% of opportunities missing Amount or CloseDate. Flag stale pipelines with open opportunities past CloseDate by more than 90 days.

---
