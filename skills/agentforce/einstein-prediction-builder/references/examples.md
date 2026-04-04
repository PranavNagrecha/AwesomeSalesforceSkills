# Examples — Einstein Prediction Builder

## Example 1: Lead Conversion Likelihood Prediction

**Context:** A B2B company has 15,000 Lead records, of which roughly 2,400 have been converted (IsConverted = true) and 12,600 have not. The sales team wants an AI score on each open lead so SDRs can prioritize outreach. The outcome field to use is IsConverted (a standard Checkbox).

**Problem:** Without a score, SDRs sort by creation date or call volume. Most effort goes to high-volume but low-fit leads. Conversion rate is 8% on worked leads.

**Solution:**

1. Navigate to Setup > Einstein Prediction Builder > New Prediction.
2. Name: `Lead_ConversionLikelihood`
3. Target object: Lead
4. Outcome field: IsConverted (positive outcome = True = Converted)
5. Add an exclusion filter: `IsConverted = False AND CreatedDate = LAST_N_DAYS:730` to scope training to leads created in the last two years, excluding leads older than that which may have been archived or reflect outdated conversion patterns.
6. Review auto-selected predictor fields. Exclude `ConvertedDate` and `ConvertedAccountId` — these are only populated after conversion and constitute leakage.
7. Train. Review metrics: the model should achieve >70% accuracy and recall for the positive (Converted) class above baseline.
8. Activate. Wait 24–48 hours for initial scoring.
9. Add the "Einstein Prediction" component to the Lead record page in Lightning App Builder.

Query to spot-check top score drivers on a specific lead:

```soql
SELECT FieldName, FactorValue, FactorPolarity, Weight
FROM EinsteinModelFactor__c
WHERE PredictionDefinitionId = '0gExx0000000001AAA'
  AND RecordId = '00Qxx0000000001AAA'
ORDER BY Weight DESC
LIMIT 5
```

**Why it works:** The exclusion filter prevents stale historical data from diluting the model. Excluding leakage fields (ConvertedDate, ConvertedAccountId) forces the model to learn from leading indicators — lead source, industry, title, engagement fields — which are the signals available at the time SDRs are working leads.

---

## Example 2: Opportunity Churn / At-Risk Prediction for Renewals

**Context:** A SaaS company manages 4,000 annual renewal Opportunity records. They track whether each renewal closes Won or Closed Lost. They want to flag at-risk renewals 60 days before close date so Customer Success can intervene.

**Problem:** No current mechanism surfaces at-risk renewals proactively. CS managers review manually using subjective criteria. Renewal rate is 74%.

**Solution:**

1. Create a custom Checkbox field on Opportunity: `Is_Churned__c` — populated via a scheduled Flow that sets it to True for Closed Lost renewals and False for Closed Won renewals (only after the close date has passed).
2. Navigate to Setup > Einstein Prediction Builder > New Prediction.
3. Name: `Opportunity_ChurnRisk`
4. Target object: Opportunity
5. Outcome field: `Is_Churned__c` (positive outcome = True = Churned)
6. Add an exclusion filter: `RecordType.Name = 'Renewal' AND CloseDate > TODAY` to score only open renewal opportunities.
7. Exclude leakage fields: `CloseDate` itself (when it is within 7 days it becomes very predictive for the wrong reason — it signals urgency but not churn risk), `StageName` for stages that only exist post-close.
8. Define a segment for Enterprise (AnnualRevenue > 1,000,000) vs. SMB accounts — these populations have different churn drivers.
9. Train, review, activate.
10. Build a List View on Opportunity filtered to `EinsteinScoring_OpportunityChurnRisk__Score__c > 70` to surface the high-risk renewals for CS review.

**Why it works:** The two-segment configuration ensures the model uses different predictor weights for Enterprise and SMB, reflecting that churn drivers (product usage, support ticket volume, executive sponsor engagement) differ meaningfully by segment. Without segments, a single model would average across populations and underperform for both.

---

## Anti-Pattern: Including Outcome-Time Fields as Predictors (Data Leakage)

**What practitioners do:** When setting up a Won/Lost opportunity prediction, they accept Einstein's default auto-selected fields without reviewing them. Einstein may include fields like `CloseDate` (which is often updated at close time), `LastActivityDate`, or custom fields populated by the sales rep at the moment of closing.

**What goes wrong:** The model trains with artificially high accuracy because fields that are updated *at close time* are perfectly correlated with the outcome — but they are only available after the event has already occurred. When the model is used to score *open* opportunities (before close), those fields contain earlier values that carry weak predictive signal. The model underperforms in production despite strong training metrics.

**Correct approach:** Before activating training, review every auto-selected predictor field and ask: "Is this field typically populated or updated before the outcome is known, or at/after close?" Exclude any field that is set simultaneously with or after the outcome event. Keep only fields that represent leading indicators — fields available and meaningful while the opportunity is still open and the sales rep still has the ability to influence the outcome.
