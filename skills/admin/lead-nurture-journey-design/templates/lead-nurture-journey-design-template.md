# Lead Nurture Journey Design — Work Template

Use this template when designing or reviewing an MCAE Engagement Studio lead nurture program.
Complete every section before beginning Engagement Studio configuration.

---

## Scope

**Skill:** `lead-nurture-journey-design`

**Request summary:** (fill in what the user or project asked for)

**Target prospect segment:** (who enters this program — ICP segment, score range, stage)

---

## Prerequisites Confirmed

- [ ] MCAE Business Unit is provisioned and CRM connector is active
- [ ] Score and Grade fields are mapped in the CRM connector field mapping
- [ ] MQL definition is agreed and signed off by Sales: Score >= ___ AND Grade >= ___
- [ ] Content inventory audit is complete (see section below)

---

## Content Inventory — Funnel Stage Map

Complete this table before any Engagement Studio configuration. Every "Send Email" step in the program must correspond to a row in this table.

| Funnel Stage | Asset Name | Asset Type | Gated (Form)? | Notes |
|---|---|---|---|---|
| Awareness | | | Yes / No | |
| Awareness | | | Yes / No | |
| Consideration | | | Yes / No | |
| Consideration | | | Yes / No | |
| Decision | | | Yes / No | |
| Decision | | | Yes / No | |

**Stage gaps identified:** (list any stages with zero assets — must be resolved before launch)

- Awareness gap: Yes / No — Notes:
- Consideration gap: Yes / No — Notes:
- Decision gap: Yes / No — Notes:

---

## Program Entry and Suppression Configuration

**Entry list name:** _______________

**Entry list criteria:**
- Prospect score: >= ___
- Prospect grade: >= ___
- Other criteria: (e.g., "opted in," "not already MQL," "not existing customer")

**Suppression lists:**

| List Name | Reason |
|---|---|
| | Existing customers |
| | Opted-out prospects |
| | Competitor domains |
| | (add additional) |

---

## MQL Definition

**Score threshold:** _______________

**Grade threshold:** _______________

**MQL handoff action (inside program):** Notify User / Create Task / both

**Sales owner / queue for assignment:** _______________

**Companion Automation Rule name:** _______________ (must exist outside program — see gotchas)

---

## Program Flow Design

Complete this flow design on paper before opening Engagement Studio.

| Step # | Step Type | Detail | Wait (days) | Branching? |
|---|---|---|---|---|
| 1 | Send Email | [Asset name — Awareness] | — | No |
| 2 | Wait | — | 5 | No |
| 3 | Rule | Did prospect click Step 1 email? | — | Yes / No |
| 4 (Yes) | Send Email | [Asset name — Consideration] | — | No |
| 4 (No) | Send Email | [Asset name — Awareness alt] | — | No |
| 5 | Wait | — | 5 | No |
| 6 | Rule | [condition] | — | Yes / No |
| ... | ... | ... | ... | ... |
| N | Change Prospect Field | Nurture Stage = [value] | — | No |
| N+1 | Notify User / Create Task | MQL handoff | — | No |

**Program exit points and exit actions:**

| Exit condition | Exit action before exit |
|---|---|
| MQL threshold reached | Notify User + Create Task |
| End of program — no MQL | Add to "Long-term Nurture" list + Change Field "Nurture Status" = "Program Complete" |
| Re-engagement failed | Add to "Dormant" list + Change Field "Marketing Status" = "Dormant" |

---

## Behavioral Trigger Definitions

Document each Rule step's trigger condition:

| Rule Step # | Trigger type | Field / Asset evaluated | Condition | Time window |
|---|---|---|---|---|
| Step 3 | Email click | [Email name] | Clicked | Last 7 days |
| Step 6 | Form submit | [Form name] | Submitted | Last 14 days |
| Step 9 | Score threshold | Prospect Score | >= [value] | Current |
| Step 9 | Grade threshold | Prospect Grade | >= [letter] | Current |

---

## Execution Cadence Documentation

**Program evaluation frequency:** Weekly (platform constraint — not configurable)

**Minimum expected time from entry to Decision content:** ___ days (estimate based on Wait steps)

**Minimum expected time from entry to MQL handoff (if all gates pass):** ___ days (estimate)

**Real-time actions handled outside this program (Completion Actions or Automation Rules):**

| Trigger event | Real-time action | Tool used |
|---|---|---|
| Form submit — entry gated asset | Autoresponder email | Completion Action on form |
| Score >= [MQL] threshold (any channel) | Sales assignment + notification | Automation Rule |

---

## Stakeholder Sign-Off

| Role | Name | Sign-off date |
|---|---|---|
| Marketing lead | | |
| Sales lead (MQL definition) | | |
| MCAE admin / builder | | |

---

## Review Checklist

Complete before activating the program:

- [ ] Content inventory table is complete — no stage gaps
- [ ] Entry list and suppression lists are confirmed
- [ ] MQL definition is documented and signed off
- [ ] Every "Send Email" step has a corresponding content inventory row
- [ ] Every "Send Email" step is followed by a Wait step of >= 3 days before the next Rule
- [ ] All Rule steps have explicit time windows where recency matters
- [ ] A "Change Prospect Field" or "Add Tag" step tracks nurture stage at each progression point
- [ ] MQL handoff has a companion Automation Rule outside the program
- [ ] Every exit point has at least one status-setting step before the prospect exits
- [ ] Test prospect confirmed routing through at least one Yes branch and one No branch
- [ ] Program cadence and stakeholder expectations are documented and shared

---

## Notes and Deviations

(Record any decisions that deviate from the standard pattern in SKILL.md and explain why.)
