# Donor Lifecycle Requirements — Work Template

Use this template when working on tasks in this area.

---

## Scope

**Skill:** `donor-lifecycle-requirements`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer each question before designing lifecycle stages or automation.

**Platform confirmation:**
- [ ] NPSP — legacy org (provisioned before December 2025); has npsp__, npe01__, npo02__ packages
  - Moves Management: Opportunity Stage progression + Engagement Plans
  - Lapsed reporting: LYBUNT/SYBUNT reports on Opportunity data
- [ ] Nonprofit Cloud (NPC) — new org (provisioned December 2025 or later)
  - Portfolio management: Actionable Segmentation
  - NPSP Engagement Plans and LYBUNT reports are NOT available
- [ ] Unknown — must confirm before designing any lifecycle features

**Existing donor segments / portfolio tiers:**

| Tier | Name | Criteria (giving history, capacity, relationship) |
|---|---|---|
| Annual Fund | | e.g., cumulative giving < $1,000/year |
| Mid-Level | | e.g., cumulative giving $1,000–$9,999/year |
| Major Gift | | e.g., capacity rated $10,000+; relationship stage: Cultivating |
| Planned Giving / Legacy | | e.g., indicated planned gift; estate |

**Lapsed donor definitions confirmed with fundraising team:**

| Segment | Definition | Priority |
|---|---|---|
| LYBUNT | Gave in the previous fiscal year, no gift in the current fiscal year | High |
| SYBUNT | Gave in a year prior to last year, no gift in the current year | Medium |
| Multi-year lapsed | No gift in 2+ years | Lower (higher re-acquisition cost) |
| Lapsed recurring | ERD Status = Lapsed (missed a scheduled payment) | High — auto-triggered |

**Existing Opportunity Stage picklist values:** (list current values to identify gaps)

| Stage Value | Maps to Lifecycle Stage | Notes |
|---|---|---|
| | | |

---

## Donor Lifecycle Stage Map

Map each lifecycle stage to the Salesforce feature that tracks it.

| Lifecycle Stage | Salesforce Feature | Object / Field | Notes |
|---|---|---|---|
| Prospect identified | Opportunity (or Lead) | Stage = Prospect Identified | |
| In cultivation | Opportunity Stage | Stage = In Cultivation | |
| Proposal / ask pending | Opportunity Stage | Stage = Proposal Pending | |
| Solicitation made | Opportunity Stage | Stage = Solicitation Made | |
| Gift closed | Opportunity | Stage = Closed Won | NPSP BDI processes payment |
| Gift lapsed (one-time) | LYBUNT/SYBUNT report | npsp__LastOppDate__c on Contact | |
| Recurring active | npe03__Recurring_Donation__c | Status = Active | |
| Recurring lapsed | npe03__Recurring_Donation__c | Status = Lapsed (auto-transitions on missed payment) | |
| Re-engaged | New Opportunity in re-engagement Campaign | Linked to Campaign | |
| Upgraded (mid-level) | Opportunity Amount + giving history | Threshold analysis on npo02__ rollup fields | |
| Major gift prospect | Opportunity Record Type = Major Gift | Restricted stage progression | |

---

## Moves Management Configuration Requirements (NPSP)

**Opportunity Stage values to create/update:**

| Stage Value | Sort Order | Probability | Is Won | Is Closed |
|---|---|---|---|---|
| Prospect Identified | 1 | 10 | No | No |
| In Cultivation | 2 | 25 | No | No |
| Proposal Pending | 3 | 50 | No | No |
| Solicitation Made | 4 | 75 | No | No |
| Closed Won | 5 | 100 | Yes | Yes |
| Closed Lost | 6 | 0 | No | Yes |

**Opportunity Record Type for Major Gift Solicitations:**
- [ ] Create new Record Type: Major Gift Solicitation
- [ ] Restrict stage progression to cultivation-aligned stages
- [ ] Add Path component on Opportunity layout

**Engagement Plan Templates to build:**

| Plan Name | Triggered by | Steps (tasks) |
|---|---|---|
| Major Gift Cultivation | Opportunity Stage = In Cultivation | 1. Thank-you call (Day 0), 2. Site visit invite (Day 14), 3. Proposal draft review (Day 30) |
| LYBUNT Re-engagement | Campaign member added to re-engagement Campaign | 1. Personal call (Day 0), 2. Handwritten note (Day 7), 3. Event invitation (Day 21) |
| New Recurring Donor Welcome | ERD created | 1. Welcome call (Day 3), 2. Impact update (Day 30) |
| (add rows as needed) | | |

---

## Lapsed Donor Re-engagement Design

**LYBUNT re-engagement workflow:**

1. Run LYBUNT report filtered to: gave $[threshold]+ last fiscal year, no gift current year
2. Mass-action to add results as Campaign Members on Campaign: [re-engagement campaign name]
3. Assign Engagement Plan Template: LYBUNT Re-engagement (auto-generates task sequence)
4. Track re-engagement gifts via Opportunity linked to Campaign
5. Measure re-engagement rate at Campaign close: Campaign ROI report

**ERD lapsed recurring donor workflow:**

- Trigger: npe03__Status__c transitions to Lapsed (NPSP auto-transitions on missed payment)
- Action: Create Task or send alert to assigned fundraiser
- Outreach: Personal call to discuss payment update or gift modification

**Segmentation design:**

| Segment | Identification Method | Re-engagement Approach |
|---|---|---|
| LYBUNT — $500+ | LYBUNT report filtered by gift amount | Personal call + Engagement Plan |
| LYBUNT — under $500 | LYBUNT report filtered by gift amount | Email series + event invite |
| SYBUNT | SYBUNT report | Targeted appeal + impact story |
| Lapsed recurring | ERD Status = Lapsed | Fundraiser call to update payment |

---

## Report Design

Design reports before configuring automation.

| Report Name | Primary Object | Grouped By | Filters | Purpose |
|---|---|---|---|---|
| Portfolio Pipeline | Opportunity | Fundraiser, Stage | Open opportunities; Major Gift RT | Weekly portfolio review |
| LYBUNT Donors | Contact + Opportunity | (flat list) | npsp__LastOppDate__c in prior FY; no gift current FY | Annual re-engagement |
| SYBUNT Donors | Contact + Opportunity | (flat list) | Last gift > 1 year ago | Lapsed re-engagement |
| Donor Upgrade Candidates | Contact | Giving tier | Consecutive years giving; amount trending up | Upgrade identification |
| Recurring Lapsed | npe03__Recurring_Donation__c | Fundraiser | Status = Lapsed | Immediate follow-up queue |

---

## Review Checklist

- [ ] NPSP vs NPC platform confirmed
- [ ] Donor lifecycle stages mapped to Salesforce features (Opportunity Stage, ERD Status, etc.)
- [ ] Portfolio tier definitions and criteria documented
- [ ] Lapsed donor definitions (LYBUNT, SYBUNT) confirmed with fundraising team
- [ ] NPSP rollup fields (npsp__LastOppDate__c, npo02__TotalOppAmount__c) confirmed accurate
- [ ] Engagement Plans designed for cultivation stage task sequences
- [ ] NPC Actionable Segmentation NOT conflated with marketing automation
- [ ] Report designs completed before automation configuration begins

---

## Notes

(Record deviations from the standard pattern and justification)
