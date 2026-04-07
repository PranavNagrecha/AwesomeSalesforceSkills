# MCAE Lead Scoring and Grading — Work Template

Use this template when designing or documenting a lead scoring and grading model in Account Engagement (MCAE / Pardot). Fill every section before activating any automation rule or going live with the MQL routing.

---

## Scope

**Skill:** `mcae-lead-scoring-and-grading`

**Request summary:** (describe what is being configured or changed)

**MCAE Business Unit name:** _______________

**Salesforce org:** _______________

**Date:** _______________

---

## Prerequisites Confirmed

- [ ] MCAE Business Unit is provisioned and connected to Salesforce CRM
- [ ] CRM connector is active and syncing
- [ ] Score field is mapped in connector field mapping: Lead field name: _______________, Contact field name: _______________
- [ ] Grade field is mapped in connector field mapping: Lead field name: _______________, Contact field name: _______________
- [ ] Marketing has MCAE admin or marketing-user role required to configure scoring

---

## MQL Definition (Get Sign-Off Before Building)

The agreed MQL threshold for this org:

| Dimension | Threshold | Rationale |
|---|---|---|
| Score (behavioral) | >= ___ | (why this number — e.g., "form fill (50) + 5 email clicks (25) + 25 page views = 100") |
| Grade (fit) | >= ___ | (why this grade — e.g., "B means decent fit; A reserved for exact ICP") |
| Combined logic | Score AND Grade | Always use AND — see SKILL.md for rationale |

**MQL definition approved by (Sales):** _______________  **Date:** _______________

**MQL recycle definition (when to un-MQL a prospect):**

| Condition | Action |
|---|---|
| Score drops below ___ | Remove from MQL campaign, move to nurture |
| Prospect unsubscribes | Remove from all active lists, mark disqualified |

---

## Scoring Point Table

Document the agreed point values per activity type. These are configured in MCAE Admin > Scoring.

| Activity | Default Points | Configured Points | Notes |
|---|---|---|---|
| Form fill (submission) | +50 | | |
| Form fill (error) | +5 | | |
| Email link click | +5 | | |
| Email open | +1 | | |
| Page view (tracked) | +1 | | |
| Custom redirect click | +5 | | |
| File download | +5 | | |
| Webinar registration | +10 | | |
| Unsubscribe | -50 | | |
| Hard bounce | -75 | | |

**Per-asset score overrides** (high-intent assets that should score higher than the default):

| Asset Name | Asset Type | Override Points | Rationale |
|---|---|---|---|
| | | | |
| | | | |

---

## Score Decay Rules

Document all decay rules. Configured in MCAE Admin > Scoring > Decay Scoring.

| Rule # | Inactivity Period (Days) | Points Reduced | Notes |
|---|---|---|---|
| 1 | | | |
| 2 | | | |

**Decay calibration check:** At the agreed decay rate, how long does it take a prospect who scored 100 from a single form fill to drop below MQL threshold?

- Day 30: Score = ___ (after first decay)
- Day 60: Score = ___ (after second decay)
- Day 90: Score = ___ (after continued decay)

Is this decay rate appropriate for your sales cycle length? [ ] Yes  [ ] No — adjust decay period.

---

## Profile Definitions

Document each ICP profile and its criteria. Configured in MCAE Admin > Profiles.

### Profile 1: [Profile Name]

**Target segment description:** _______________

**Is this the default profile?** [ ] Yes  [ ] No

| Criterion | Field | Match Type | Value | Grade Points |
|---|---|---|---|---|
| | Job Title | contains | "VP" | +___ |
| | Job Title | contains | "Intern" | -___ |
| | Industry | equals | "Technology" | +___ |
| | Employees | greater than | 500 | +___ |
| | Country | not in | [list] | -___ |
| | | | | |

---

### Profile 2: [Profile Name]

**Target segment description:** _______________

**Is this the default profile?** [ ] Yes  [ ] No

| Criterion | Field | Match Type | Value | Grade Points |
|---|---|---|---|---|
| | | | | |
| | | | | |

---

## Automation Rules

Document each automation rule. Configured in MCAE Automation > Automation Rules.

### Rule 1: MQL Promotion Rule

| Field | Value |
|---|---|
| Rule name | |
| Criteria match type | ALL |
| Criterion 1 | Prospect Score >= [threshold] |
| Criterion 2 | Prospect Grade >= [letter] |
| Additional criteria | (e.g., Prospect opted-in = true) |
| Action 1 | Assign to: [queue/user name] |
| Action 2 | Notify: [SDR manager email] |
| Action 3 | Add to Salesforce Campaign: [campaign name] with status [Responded] |
| Repeat setting | Yes — repeat when prospect re-qualifies after score reset |
| Activation date | |
| Activation notes | (retroactive impact check — see gotchas.md) |

---

### Rule 2: MQL Recycle Rule (Score Drop)

| Field | Value |
|---|---|
| Rule name | |
| Criteria match type | ALL |
| Criterion 1 | Prospect Score < [threshold] |
| Criterion 2 | Prospect is member of Salesforce Campaign: [MQL campaign] |
| Action 1 | Remove from Salesforce Campaign: [MQL campaign] |
| Action 2 | Add to List: [Nurture re-engagement list] |
| Action 3 | Notify: [SDR manager] |
| Repeat setting | Yes |
| Activation date | |

---

## Test Validation Log

Before going live, validate with a test prospect:

| Test Step | Expected Result | Actual Result | Pass/Fail |
|---|---|---|---|
| Create test prospect in MCAE | Prospect created, score = 0, no grade | | |
| Submit test form (50 pts) | Score = 50 | | |
| Click test email link (5 pts) | Score = 55 | | |
| View 5 tracked pages (1 pt each) | Score = 60 | | |
| Fill form again (50 pts) | Score = 110 (above MQL threshold) | | |
| Check Automation Rule fired | Prospect assigned to Sales queue | | |
| Check CRM Lead/Contact | Score field = 110, Grade field = [letter] | | |
| Manually reduce score below threshold | MQL Recycle rule fires | | |
| Check decay fires (simulate or wait) | Score reduces per decay rule | | |

---

## Sign-Off and Handoff

| Role | Name | Sign-Off Date |
|---|---|---|
| Marketing Admin (MCAE) | | |
| Sales Operations | | |
| SDR Manager / Sales Lead | | |

**Go-live date:** _______________

**Post-launch review date (30 days after go-live):** _______________

**Review items at 30-day check:**
- [ ] MQL volume is within expected range (neither flooding nor too sparse)
- [ ] Sales team is accepting and working MQLs (not ignoring the queue)
- [ ] No unexpected retroactive rule triggers reported
- [ ] Score decay is running as expected (no prospect with 6+ months inactivity is still MQL-eligible)
- [ ] Manual override count reviewed and policy confirmed
