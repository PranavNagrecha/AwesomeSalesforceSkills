# Sales Process Mapping — Work Template

Use this template when working on a sales process mapping engagement. Fill each section before handing off to the opportunity-management skill for configuration.

---

## Scope

**Organisation / Business Unit:** (fill in)

**Request summary:** (fill in what the user or stakeholder asked for)

**Date of discovery sessions:** (fill in)

**Key stakeholders interviewed:**
- Sales Leader (VP/Director): (name, title)
- Front-line AEs (2–3): (names)
- RevOps or Sales Ops lead: (name, title)
- Other: (name, role)

---

## Selling Motions Identified

List each distinct selling motion. Each motion with a divergent stage sequence becomes a separate Salesforce Sales Process.

| Motion Name | Deal Type | Typical Deal Size | Avg Sales Cycle | Separate Stage Sequence Needed? |
|---|---|---|---|---|
| (e.g., New Logo — Enterprise) | Direct | $50K–$500K | 90–180 days | Yes |
| (e.g., Renewal) | Renewal | $20K–$200K | 30–60 days | Yes |
| (add rows as needed) | | | | |

---

## Stage Map — [Motion Name]

Repeat this table for each distinct selling motion.

| # | Stage Name (exact picklist string) | Definition | Entry Criteria | Exit Criteria | ForecastCategoryName | Default Probability | Primary Owner Role |
|---|---|---|---|---|---|---|---|
| 1 | | | | | Pipeline / Best Case / Commit / Closed / Omitted | % | |
| 2 | | | | | | % | |
| 3 | | | | | | % | |
| 4 | | | | | | % | |
| 5 | | | | | | % | |
| n | Closed Won | Contract fully executed by both parties | Signed contract received | — | Closed | 100% | AE |
| n+1 | Closed Lost | Deal ended without purchase | Decision made against purchase or no decision | — | Closed | 0% | AE |

Note: Stage names in this column are the exact strings that will be entered as global picklist values in Salesforce. Confirm spelling and capitalisation before handoff.

---

## Stage Transition Rules — [Motion Name]

Document every transition restriction. Each row that requires enforcement becomes a validation rule requirement in the handoff brief.

| From Stage | To Stage | Direction | Rule | Enforcement Method | Fields Required Before Transition |
|---|---|---|---|---|---|
| (e.g., Discovery) | (e.g., Evaluation) | Forward | Allowed if champion identified | Validation Rule | Champion_Name__c (text), Champion_Title__c (text) |
| (e.g., Negotiation) | (e.g., Proposal) | Backward | Blocked — manager approval required | Validation Rule + Approval Process | Manager_Approval_Status__c |
| Any | Closed Won | Forward | Win/loss reason required | Validation Rule | Win_Loss_Reason__c |
| (add rows as needed) | | | | | |

---

## Win/Loss Reason Taxonomy

### Win Reasons (5–8 values)

| # | Reason Label | Description / When to Select |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

### Loss Reasons (5–8 values, always include "No Decision / Status Quo")

| # | Reason Label | Description / When to Select |
|---|---|---|
| 1 | No Decision / Status Quo | Prospect did not choose any vendor; maintained current state |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

**Capture point:** (e.g., On transition to Closed Won or Closed Lost)

**Enforcement method:** (e.g., Required picklist on Opportunity enforced by validation rule when StageName = 'Closed Won' or 'Closed Lost')

**Data owner:** (e.g., AE self-reported; manager reviews within 5 business days)

---

## Open Questions Log

All unresolved items from discovery. Do not hand off to configuration until all questions are resolved.

| # | Question | Stakeholder Owner | Target Resolution Date | Status |
|---|---|---|---|---|
| 1 | | | | Open / Resolved |
| 2 | | | | |
| (add rows as needed) | | | | |

---

## Handoff Brief for opportunity-management Skill

Complete this section after all open questions are resolved. This is the input specification for the opportunity-management skill.

**Number of distinct Sales Processes required:** (e.g., 2)

**Sales Process 1 — [Name]:**
- Record Type: (name)
- Stage names in order: (exact picklist strings, comma-separated)
- Forecast category per stage: (stage to category mapping)

**Sales Process 2 — [Name]:** (repeat as needed)
- Record Type: (name)
- Stage names in order:
- Forecast category per stage:

**Validation Rules Required:**

| Rule # | Condition | Error Message | Stage(s) |
|---|---|---|---|
| 1 | (e.g., ISPICKVAL(StageName, 'Proposal') && ISBLANK(CloseDate)) | Close Date is required before moving to Proposal. | Proposal |
| 2 | (e.g., ISPICKVAL(StageName, 'Closed Won') && ISBLANK(Win_Loss_Reason__c)) | Win reason is required when closing as Won. | Closed Won |
| (add rows) | | | |

**Custom Fields Required:**

| Field Label | API Name | Type | Required? | Object |
|---|---|---|---|---|
| Win/Loss Reason | Win_Loss_Reason__c | Picklist | Yes (on close) | Opportunity |
| (add rows) | | | | |

**Additional configuration dependencies flagged:**
- (e.g., Opportunity Splits required: Yes / No)
- (e.g., Collaborative Forecasts in use: Yes / No — forecast type alignment needed)
- (e.g., Path configuration needed: Yes / No — per record type)

---

## Notes and Deviations

Record any decisions that deviate from the standard patterns in the SKILL.md, and explain why.

(fill in)
