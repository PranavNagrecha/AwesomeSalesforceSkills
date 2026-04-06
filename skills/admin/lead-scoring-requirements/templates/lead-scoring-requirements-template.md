# Lead Scoring Requirements — Work Template

Use this template when designing or documenting a lead scoring model for a Salesforce Sales Cloud org.
Fill every section. Do not skip the Handoff SLA — it is required for the model to be operationally complete.

---

## Scope

**Skill:** `lead-scoring-requirements`

**Request summary:** (describe what the stakeholder asked for)

**In scope:**
- [ ] Lead scoring model design (dimensions, weights, thresholds)
- [ ] MQL and SQL threshold definitions
- [ ] Salesforce field map
- [ ] Automation design (Flow trigger type, entry criteria, actions)
- [ ] Handoff SLA documentation

**Out of scope:**
- [ ] Einstein Lead Scoring (requires Sales Cloud Einstein license — separate engagement)
- [ ] Account Engagement automation rule configuration (separate AE-side setup)
- [ ] Lead conversion to Opportunity (see `lead-management-and-conversion` skill)

---

## Context Gathered

Answer these before designing the model:

- **ICP definition (in Salesforce field terms):**
  - Industry values: ___
  - NumberOfEmployees range: ___
  - Target job titles / Title keywords: ___
  - AnnualRevenue range (if applicable): ___
  - Geography / region (if applicable): ___

- **Available behavioral signals (fields that can be populated):**
  - Signal 1: field name ___, source ___
  - Signal 2: field name ___, source ___
  - Signal 3: field name ___, source ___

- **Marketing automation platform:** Sales Cloud only / Account Engagement / Other: ___

- **Estimated lead volume per day:** ___
  - If > 200/day: use Scheduled Flow for recalculation (not record-triggered)

- **Existing qualification framework:** BANT / MEDDIC / Custom: ___

- **Historical data available for threshold calibration:** Yes / No
  - If yes: closed-won opportunity count (last 12 months): ___

---

## Scoring Dimension Matrix

### Dimension 1: Fit (Demographic / Firmographic)

Maximum fit score: ___

| Criterion | Field | Condition | Points |
|---|---|---|---|
| Industry match | `Industry` | IN (...) | ___ |
| Company size | `NumberOfEmployees` | >= ___ AND <= ___ | ___ |
| Title / persona | `Title` | contains '...' | ___ |
| (add rows as needed) | | | |

### Dimension 2: Engagement / Behavioral

Maximum engagement score: ___

| Criterion | Field | Condition | Points |
|---|---|---|---|
| Demo request | `Demo_Requested__c` | = true | ___ |
| Content downloads | `Content_Downloads__c` | >= ___ | ___ |
| (add rows as needed) | | | |

### Composite Score

**Formula:** `Fit_Score__c + Engagement_Score__c`

**Max composite score:** ___ (Fit max + Engagement max)

---

## MQL and SQL Threshold Definitions

### MQL Definition

A lead is Marketing-Qualified when ALL of the following are true:

- [ ] `Composite_Score__c` >= ___ (agreed threshold: ___)
- [ ] `Fit_Score__c` >= ___ (minimum fit gate: ___)
- [ ] Required fields populated: Company, Title, Email (minimum)
- [ ] Additional required fields: ___

**MQL threshold calibration note:** (record how this threshold was derived — e.g., back-scored 150 closed-won opportunities, 87% scored >= 50)

### SQL Definition

A lead is Sales-Qualified when the assigned rep has confirmed:

**BANT criteria:**
- [ ] Budget: ___
- [ ] Authority: decision-maker confirmed
- [ ] Need: clear business problem identified
- [ ] Timeline: purchase window <= ___ months

OR **MEDDIC criteria (if applicable):**
- [ ] Metrics: ___
- [ ] Economic Buyer: identified
- [ ] Decision Criteria: ___
- [ ] Decision Process: ___
- [ ] Identify Pain: ___
- [ ] Champion: ___

---

## Salesforce Field Map

| Field Label | API Name | Type | Updated By | Notes |
|---|---|---|---|---|
| Fit Score | `Fit_Score__c` | Number(3,0) | Record-triggered Flow | Recalculated on ICP field change |
| Engagement Score | `Engagement_Score__c` | Number(3,0) | Flow (on signal field change) | Updated when behavioral signals write back |
| Composite Score | `Composite_Score__c` | Number(3,0) | Flow | Fit + Engagement; stored Number for Flow/Assignment Rule use |
| Is MQL | `Is_MQL__c` | Checkbox | Flow | Set true when MQL conditions met |
| MQL Date | `MQL_Date__c` | DateTime | Flow | Stamped when Is_MQL__c flips to true |
| SQL Date | `SQL_Date__c` | DateTime | Rep / Flow | Stamped when rep accepts and qualifies |
| Lead Stage | `Lead_Stage__c` | Picklist | Flow | Raw / Nurture / MQL / Accepted / SQL / Converted / Recycled |
| Recycle Count | `Recycle_Count__c` | Number(2,0) | Flow | Incremented on each recycle event |
| Recycle Reason | `Recycle_Reason__c` | Picklist | Rep / Flow | No Response / Wrong Timing / Not DM / Competitor / Other |
| Recycle Date | `Recycle_Date__c` | DateTime | Flow | Last recycle event timestamp |

---

## Automation Design

### Flow 1: Fit Score Calculation

- **Type:** Record-Triggered Flow (Before Save recommended for performance)
- **Object:** Lead
- **Trigger:** Create or Edit when ICP fields change (Industry, NumberOfEmployees, Title)
- **Entry criteria:** None (run on all qualifying edits)
- **Actions:** Decision elements evaluate each fit criterion; Assignment elements accumulate fit points; Update `Fit_Score__c`
- **Downstream:** After `Fit_Score__c` is updated, Flow 3 (Composite + MQL) re-evaluates

### Flow 2: Engagement Score Update

- **Type:** Record-Triggered Flow (After Save)
- **Object:** Lead
- **Trigger:** Edit when behavioral signal fields change
- **Entry criteria:** Any signal field changed from previous value
- **Actions:** Recalculate `Engagement_Score__c` from signal fields
- **Note:** If signals are written by external systems in bulk, consider Scheduled Flow

### Flow 3: Composite Score and MQL Flag

- **Type:** Record-Triggered Flow (After Save)
- **Object:** Lead
- **Trigger:** Edit when `Fit_Score__c` or `Engagement_Score__c` changes
- **Actions:**
  1. Update `Composite_Score__c` = `Fit_Score__c` + `Engagement_Score__c`
  2. If MQL conditions met AND `Is_MQL__c` was false: set `Is_MQL__c` = true, stamp `MQL_Date__c`, update `Lead_Stage__c` = MQL
  3. Assign lead to sales queue / send notification per handoff SLA

---

## Handoff SLA

**Score threshold for MQL routing:** Composite_Score__c >= ___

**Required fields before handoff (must be populated):**
- Company
- Title
- Email or Phone
- ___

**Rep response time SLA:**
- Hot MQL (score >= ___): ___ business hours
- Warm MQL (score ___ to ___): ___ business days

**SQL acceptance criteria:** (list the BANT/MEDDIC items above the rep must confirm)

**Recycle definition:** A rep may recycle an MQL to Nurture when:
- No response after ___ business days
- Lead is not a decision-maker
- Lead is a competitor
- Timing is > ___ months out
- Other (documented in `Recycle_Reason__c`)

**On recycle:**
- `Is_MQL__c` = false
- `Lead_Stage__c` = Recycled then Nurture (after ___ days)
- `Recycle_Count__c` incremented
- `Recycle_Reason__c` populated by rep

**SLA sign-off:**
- Marketing lead: ___ Date: ___
- Sales ops lead: ___ Date: ___

---

## Checklist

Copy from SKILL.md review checklist and tick items as complete.

- [ ] Scoring dimension matrix complete with point values and max scores documented
- [ ] MQL threshold calibrated against historical closed-won data (or explicitly noted as estimated pending data)
- [ ] SQL acceptance criteria documented and signed off by sales
- [ ] All required Lead fields identified with API names, types, and owning automation
- [ ] Composite score field is Number (not Formula) for Flow and Assignment Rule compatibility
- [ ] Automation design specifies trigger type, entry criteria, and actions for each Flow
- [ ] Handoff SLA covers threshold, required fields, response time, and recycle process
- [ ] SLA signed off by marketing and sales leadership
- [ ] Einstein Lead Scoring confirmed out of scope (or documented as a future phase)

---

## Notes

(Record any deviations from the standard pattern and the reason for each deviation.)
