# Agentforce Sales AI Setup — Work Template

Use this template when configuring Einstein for Sales features in a Salesforce org.

## Scope

**Skill:** `agentforce-sales-ai-setup`

**Request summary:** (fill in what the practitioner asked for — e.g., "Enable Einstein for Sales from scratch," "Investigate why Opportunity Scores are missing," "Confirm Pipeline Inspection AI is working")

## License Verification

Complete this section before any configuration work begins.

| License | Required For | Status |
|---|---|---|
| Einstein for Sales add-on OR Einstein 1 Sales edition | Opportunity Scoring, Pipeline Inspection, EAC | ☐ Confirmed / ☐ Not Present |
| Einstein Generative AI (Einstein GPT) | AI email composition (generative drafts) | ☐ Confirmed / ☐ Not Present / ☐ Not in scope |

**How to check:** Setup > Company Information > Feature Licenses

**Notes:** (record any license gaps or procurement actions needed)

---

## Data Readiness Check

Run before enabling Opportunity Scoring. Do not skip.

```sql
SELECT COUNT(Id) closedOppsInRange
FROM Opportunity
WHERE IsClosed = true
AND CloseDate = LAST_N_DAYS:730
```

**Result:** _______ closed opportunities in last 24 months

**Gate:** Must be >= 200 to proceed with Opportunity Scoring enablement.

- [ ] Result >= 200 — proceed
- [ ] Result < 200 — defer Opportunity Scoring; document gap and timeline for stakeholders

---

## Pre-Enablement State Check

| Prerequisite | Status | Notes |
|---|---|---|
| Collaborative Forecasting enabled? | ☐ Yes / ☐ No | Required for Pipeline Inspection AI insights |
| Opportunity Scoring previously enabled? | ☐ Yes / ☐ No | Note model status if previously enabled |
| Pipeline Inspection previously enabled? | ☐ Yes / ☐ No | Note current AI insights visibility |
| Sandbox vs. production? | ☐ Sandbox / ☐ Production | Score generation only works in production |

---

## Enablement Sequence Log

Record each feature enablement step as it is completed.

| Step | Feature | Action | Timestamp | Status |
|---|---|---|---|---|
| 1 | Opportunity Scoring | Enable toggle in Setup > Einstein > Sales > Opportunity Scoring | | ☐ Done |
| 2 | Opportunity Scoring | Model status check | | ☐ Active / ☐ Training / ☐ Insufficient Data |
| 3 | Collaborative Forecasting | Enable in Setup > Forecasts Settings (if not already active) | | ☐ Done / ☐ Already Active |
| 4 | Pipeline Inspection | Enable toggle | | ☐ Done |
| 5 | Pipeline Inspection | Confirm AI insights column visible to forecast manager | | ☐ Visible / ☐ Missing |
| 6 | Einstein Email (if licensed) | Enable in Setup > Einstein for Sales > Email | | ☐ Done / ☐ Not in scope |

**Model training wait note:** Initial Opportunity Scoring model training takes 24–72 hours. Do not enable Pipeline Inspection until model status is "Active."

---

## Permission Set Assignments

| Permission Set | Assigned To (Users / Profiles) | Status |
|---|---|---|
| Einstein for Sales | | ☐ Done |
| Einstein for Sales Email (if email composition in scope) | | ☐ Done / ☐ Not in scope |

---

## Page Layout Verification

| Field / Component | Object / Page | Status |
|---|---|---|
| Opportunity Score field | Opportunity page layout | ☐ Added / ☐ Already present |
| Opportunity Score Change field | Opportunity page layout | ☐ Added / ☐ Already present / ☐ Not needed |
| Pipeline Inspection tab | Sales App navigation | ☐ Visible to forecast manager |

---

## Validation Results

| Validation | Expected Result | Actual Result | Pass/Fail |
|---|---|---|---|
| Opportunity Score field visible on Opportunity record | Score value (0–99) shown once model is Active | | |
| Pipeline Inspection AI insights column | Visible to forecast manager when Collaborative Forecasting is enabled | | |
| AI email compose button | Visible in email composer on Opportunity/Contact (only if Einstein Generative AI licensed) | | |
| Sandbox score absence | Expected — not a defect | N/A — document explicitly if sandbox | ☐ Documented |

---

## Issues Log

| Issue | Root Cause | Resolution | Status |
|---|---|---|---|
| | | | |

---

## Notes and Deviations

(Record any deviations from the standard enablement sequence, stakeholder decisions, or platform behaviors observed that are not covered in the standard workflow.)
