# Fundraising Process Mapping — Work Template

Use this template when documenting or designing the fundraising lifecycle for a Salesforce nonprofit org. Complete all sections before any Salesforce configuration begins.

---

## Scope

**Skill:** `fundraising-process-mapping`

**Org name / client:** (fill in)

**Request summary:** (describe what the user or stakeholder asked for — e.g., "Map the major gift cultivation lifecycle for Opportunity stage configuration")

**Platform confirmed:** [ ] NPSP (npsp namespace present in Installed Packages)  [ ] Nonprofit Cloud (NPC)  [ ] Standard Salesforce (no NPSP, no NPC)

---

## Context Gathered

Answer these questions before producing the stage map:

- **Platform verification result:** (NPSP namespace present? NPC confirmed? Post-December 2025 org?)
- **Active program types:** (Which of the following are in use: Annual Fund / Donation, Major Gift, Grant, In-Kind, Planned Giving, Other)
- **Current Opportunity Record Types:** (list all Record Types visible in Setup)
- **Current Sales Processes:** (list all Sales Processes and their assigned Record Types)
- **Gift officer / development team roles:** (who owns Identification? Cultivation? Stewardship?)
- **Existing stage names (if any):** (list current stage values for each Record Type)
- **Known constraints:** (any hard requirements on stage names, probabilities, or pipeline report format)

---

## Stage Map — [Program Type 1: e.g., Major Gift]

| Stage Name | Probability % | Entry Criteria | Exit Criteria | Responsible Role |
|---|---|---|---|---|
| (stage 1) | % | (what moves a record INTO this stage) | (what triggers movement to the next stage) | (role or team) |
| (stage 2) | % | | | |
| (stage 3) | % | | | |
| (stage 4) | % | | | |
| (stage 5) | % | | | |
| Closed Won | 100% | (signed pledge or payment received) | — | (role) |
| Closed Lost | 0% | (donor declines or prospect disqualified) | — | (role) |

---

## Stage Map — [Program Type 2: e.g., Grant]

| Stage Name | Probability % | Entry Criteria | Exit Criteria | Responsible Role |
|---|---|---|---|---|
| (stage 1) | % | | | |
| (stage 2) | % | | | |
| (stage 3) | % | | | |
| Awarded / Closed Won | 100% | (award letter received) | — | (role) |
| Declined / Closed Lost | 0% | (grant declined or not submitted) | — | (role) |

---

## Stage Map — [Program Type 3: e.g., Donation / Annual Fund]

| Stage Name | Probability % | Entry Criteria | Exit Criteria | Responsible Role |
|---|---|---|---|---|
| (stage 1) | % | | | |
| (stage 2) | % | | | |
| Closed Won | 100% | (gift received) | — | (role) |
| Closed Lost | 0% | (donor declines or lapses) | — | (role) |

---

## Moves Management Alignment (Major Gift Program Only)

Map each Major Gift stage to the corresponding Moves Management phase:

| Major Gift Stage | Moves Management Phase | Key Activities at This Phase |
|---|---|---|
| (stage name) | Identification | Wealth screening, referral intake, prospect research |
| (stage name) | Qualification | Discovery call, first meeting, capacity confirmation |
| (stage name) | Cultivation | Strategy meetings, impact events, site visits, impact reports |
| (stage name) | Solicitation | Formal proposal delivery, ask conversation |
| (stage name) | Stewardship | Recognition, impact reporting, multi-year pledge management |

---

## Automation Dependency List

List all Flows, Process Builder processes, validation rules, Apex triggers, or rollup configurations that reference specific stage values by name. These must be reviewed and updated if stage names change.

| Automation Name | Type | Stage Value Referenced | Impact if Stage Renamed |
|---|---|---|---|
| (automation name) | (Flow / Process Builder / Apex / Rollup) | (stage value) | (what breaks) |

---

## NPSP vs NPC Platform Notes

- **If NPSP:** NPSP ships four pre-configured sales processes (Donation, Grant, In-Kind, Major Gift). Confirm each is present and assigned to the correct Record Type. Engagement Plans are available for post-close stewardship task automation.
- **If NPC:** Do not reference NPSP Engagement Plans — they do not exist in NPC. Stewardship automation must use Flow, Cadences, or other native automation. Confirm NPC fundraising object model before designing stages.
- **If migrating NPSP → NPC:** Run a stage audit before any migration work. Export all current stage values, query active Opportunity records per stage, and build an NPSP-to-NPC stage mapping table before touching any configuration.

---

## Development Leadership Sign-Off

- [ ] Stage map reviewed with chief development officer or development director
- [ ] Stage vocabulary confirmed to reflect how gift officers actually describe their pipeline
- [ ] Probability values reviewed and agreed
- [ ] Automation dependency list reviewed by technical team
- [ ] Stage design document approved before Salesforce configuration begins

**Approved by:** (name, title, date)

---

## Deviations from Standard Pattern

(Document any deliberate decisions that differ from the skill's recommended patterns and why.)

---

## Handoff Notes for Implementation

(List what the implementation team needs to action next, e.g., "Configure Major Gift Sales Process with approved stage values," "Build stage-change Flow for Cultivation → Solicitation transition," "Review existing rollups for stage dependency.")
