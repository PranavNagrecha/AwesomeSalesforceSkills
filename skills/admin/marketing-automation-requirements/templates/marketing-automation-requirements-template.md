# Marketing Automation Requirements — Work Template

Use this template to document all requirements for a Salesforce marketing automation program before handing off to the implementation team. Every section must be complete. Sections left blank are blockers.

---

## Scope

**Skill:** `marketing-automation-requirements`

**Request summary:** (describe what the stakeholder asked for)

**Platforms in scope:**
- [ ] MCAE (Account Engagement / Pardot)
- [ ] Marketing Cloud Engagement (MCE)
- [ ] Marketing Cloud Next (MC Next) with Data Cloud
- [ ] Salesforce Sales Cloud (CRM) only

**Platforms explicitly OUT of scope:** (list any platforms in the org that are not covered by this program)

---

## Context Gathered

Record the answers to the Before Starting questions before proceeding.

- **Platform scope confirmed:** (which platform owns prospect scoring?)
- **MQL alignment status:** (joint session scheduled / completed / blocked — explain)
- **Lifecycle stages in scope:** (list which of the 7 MCAE stages apply)
- **Lead volume estimate:** (average leads/day; relevant for automation trigger type)
- **ICP field data quality:** (are Title, Industry, NumberOfEmployees populated reliably?)
- **Known constraints:** (any org limits, existing automation conflicts, or migration in progress)

---

## 1. Lifecycle Stage Map

Define each lifecycle stage in scope, its transition trigger, and the CRM field updates it produces.

| Stage | In Scope? | Transition Trigger | CRM Field Updates | Responsible System |
|---|---|---|---|---|
| Visitor | [ ] Yes / [ ] No | Anonymous — no trigger | None | MCAE |
| Prospect | [ ] Yes / [ ] No | Prospect record created in MCAE | Lead/Contact created in CRM | MCAE + CRM |
| MQL | [ ] Yes / [ ] No | (specify automation rule or manual) | Is_MQL__c, MQL_Date__c, Lifecycle_Stage__c | MCAE |
| SQL | [ ] Yes / [ ] No | (specify rep action or automation) | SQL_Date__c, Lifecycle_Stage__c, Lead Status | CRM |
| Opportunity | [ ] Yes / [ ] No | Lead converted by rep | Opportunity created, Lifecycle_Stage__c on Contact | CRM |
| Customer | [ ] Yes / [ ] No | Opportunity Closed Won | Lifecycle_Stage__c = "Customer" | CRM |
| Won | [ ] Yes / [ ] No | (specify if used) | (specify field updates) | CRM |

---

## 2. Scoring Model Specification

### 2a. Scoring Sources and Point Weights

| Activity | Default MCAE Points | Agreed Points | Notes / Overrides |
|---|---|---|---|
| Form fill (demo request) | +50 | | High-intent override if applicable |
| Form fill (content gate) | +50 | | |
| Form fill (contact us) | +50 | | |
| Email link click | +5 | | |
| Email open | +1 | | |
| Tracked page view (general) | +1 | | |
| Tracked page view (pricing) | +1 | | Consider override |
| Content / file download | +5 | | |
| Webinar registration | +10 | | |
| Custom redirect click | +5 | | |
| (Add additional sources) | | | |

### 2b. Negative Scoring (Required)

| Disqualification Signal | Agreed Point Deduction |
|---|---|
| Unsubscribe / opt-out | |
| Hard bounce | |
| Spam complaint | |
| (Add additional signals) | |

### 2c. Score Ceiling

**Maximum score (ceiling):** _______ points

Rationale: (explain why this ceiling is appropriate for the prospect base)

### 2d. Score Decay Rules

| Rule | Inactivity Period | Point Reduction | Stacks with Rule # |
|---|---|---|---|
| Decay Rule 1 | days | points | — |
| Decay Rule 2 (optional) | days | points | Rule 1 |

Notes: Decay does not reduce score below 0. Decay does not trigger automation rules.

### 2e. Grade Profile Criteria (if score + grade MQL model)

**Profile name:** (e.g., "Enterprise B2B Default")

| Criterion | Field | Value / Condition | Grade Points |
|---|---|---|---|
| (Positive — example) | Title | contains "VP", "Director", "C-level" | + |
| (Positive — example) | Industry | = Technology / SaaS | + |
| (Positive — example) | NumberOfEmployees | >= 200 | + |
| (Negative — example) | Title | contains "Student", "Intern" | - |
| (Negative — example) | Industry | = Education / Non-profit | - |
| (Add all criteria) | | | |

For orgs with multiple ICP segments, create a separate table per segment Profile.

---

## 3. MQL Threshold Definition

**[BLOCKER — implementation cannot begin until this section has two named approvers]**

**Threshold type:** [ ] Score only  /  [ ] Score + Grade

**MQL Threshold:**
- Minimum score: _______
- Minimum grade (if applicable): _______

**Full threshold expression:** (e.g., "Score >= 100 AND Grade >= B")

```
(write the threshold as a plain-English rule that the implementation team will configure)
```

**Marketing approver:** _______________________ Date: ___________

**Sales approver:** _______________________ Date: ___________

---

## 4. SQL Qualification Framework

**Framework in use:** [ ] BANT  /  [ ] MEDDIC  /  [ ] Custom (describe below)

**SQL acceptance criteria (rep must confirm all of the following before converting to SQL):**

For BANT:
- [ ] Budget: (describe minimum budget confirmation requirement)
- [ ] Authority: (describe decision-maker confirmation requirement)
- [ ] Need: (describe need confirmation requirement)
- [ ] Timeline: (describe timeline requirement, e.g., purchase within 6 months)

For MEDDIC (replace BANT section):
- [ ] Metrics: (quantified business impact identified)
- [ ] Economic Buyer: (named and accessible)
- [ ] Decision Criteria: (documented)
- [ ] Decision Process: (mapped)
- [ ] Identify Pain: (confirmed)
- [ ] Champion: (identified inside the account)

---

## 5. Handoff Mechanism Specification

**Automation trigger:** (MCAE Automation Rule — specify rule name and criteria / Engagement Studio step — specify program name and step)

**CRM field updates on MQL transition:**

| Field | API Name | New Value | Type |
|---|---|---|---|
| MQL flag | Is_MQL__c | true | Checkbox |
| MQL timestamp | MQL_Date__c | Today | DateTime |
| Lifecycle stage | Lifecycle_Stage__c | "MQL" | Picklist |
| (Add additional fields) | | | |

**Assignment target:** (queue name or user — specify)

**Notification method(s):**
- [ ] MCAE alert email to assigned rep
- [ ] CRM Task created on Lead record (Subject: _______________________)
- [ ] Salesforce notification (Chatter / Bell notification)
- [ ] External notification (Slack via Flow — specify channel)

---

## 6. Sales SLA

| MQL Tier | Definition | Max Response Time | SLA Start |
|---|---|---|---|
| Tier 1 (Hot) | e.g., demo request form fill | 1 business day | Task created date |
| Tier 2 (Warm) | e.g., score >= threshold via content | 3 business days | Task created date |
| (Add tiers) | | | |

**Recycle trigger:** (conditions under which a rep marks an MQL as recycled — e.g., no response within SLA, wrong persona confirmed, not a decision-maker)

**Recycle field requirements:**

| Field | API Name | Type | Values / Notes |
|---|---|---|---|
| Recycle reason | Recycle_Reason__c | Picklist | Timing / Wrong Persona / Competitor / No Budget / Other |
| Recycle date | Recycle_Date__c | DateTime | Stamped when rep recycles |
| Recycle count | Recycle_Count__c | Number | Incremented on each recycle event |

**Post-recycle action:** (specify what MCAE program the prospect re-enters after recycle — e.g., "Re-Engagement Nurture Program")

**Escalation process:** (what happens if rep does not act within SLA window — notify manager? reassign?)

---

## 7. CRM Field Requirements

All fields that must be created or modified on Lead and/or Contact objects:

| Object | Field Label | API Name | Type | Owner System | Notes |
|---|---|---|---|---|---|
| Lead | MQL Flag | Is_MQL__c | Checkbox | MCAE | Protected from manual CRM edits |
| Lead | MQL Date | MQL_Date__c | DateTime | MCAE | |
| Lead | SQL Date | SQL_Date__c | DateTime | CRM (rep action) | |
| Lead | Lifecycle Stage | Lifecycle_Stage__c | Picklist | MCAE + CRM | See stage map above |
| Lead | Recycle Reason | Recycle_Reason__c | Picklist | CRM (rep) | |
| Lead | Recycle Date | Recycle_Date__c | DateTime | CRM | |
| Lead | Recycle Count | Recycle_Count__c | Number | CRM | |
| Contact | (mirror fields as needed) | | | | |

---

## 8. Calibration Review

**Scheduled calibration review date:** _______________________ (recommend 60–90 days post-launch)

**Review participants:** (VP Marketing, VP Sales, Marketing Ops, Sales Ops)

**Metrics to evaluate at review:**
- MQL volume (per week/month)
- MQL-to-SQL conversion rate (target: ______%)
- SQL-to-Opportunity conversion rate (target: ______%)
- Median rep response time vs. SLA
- Top recycle reasons (frequency by Recycle_Reason__c value)

**Threshold adjustment process:** (how will threshold changes be proposed, approved, and implemented after go-live)

---

## Approach Notes

**Pattern applied:** (Pattern 1: Score + Grade / Pattern 2: Score-Only / Pattern 3: MC Next Scoring Model)

**Rationale:** (why this pattern was chosen over the alternatives)

**Deviations from standard pattern:** (document any decisions that differ from the SKILL.md recommended approach and why)

---

## Sign-Off Checklist

- [ ] Platform scope confirmed and documented
- [ ] Lifecycle stage map complete for all in-scope stages
- [ ] Scoring model specification covers all 6 elements: sources, weights, decay, ceiling, grade criteria, negative scoring
- [ ] MQL threshold has two named approvers (marketing AND sales)
- [ ] SQL qualification framework named and criteria listed
- [ ] Handoff mechanism fully specified: trigger, field updates, notification, assignment
- [ ] Sales SLA documented: response time by tier, recycle criteria, escalation
- [ ] CRM field requirements list complete
- [ ] Calibration review scheduled
- [ ] MCE Automation Studio and MCAE Engagement Studio are not conflated anywhere in this document
