# Volunteer Management Requirements — Work Template

Use this template when designing or implementing volunteer management in a Salesforce nonprofit org.

## Scope

- Org platform: [ ] NPSP + V4S  [ ] Nonprofit Cloud (NPC) native
- Processes in scope: [ ] Recruitment  [ ] Scheduling  [ ] Hours Tracking  [ ] Recognition  [ ] Skills Matching

---

## Platform Confirmation

| Check | Result |
|---|---|
| Installed Packages: V4S present? (GW_Volunteers namespace) | |
| NPC license provisioned? (Setup > Company Information) | |
| Platform decision | V4S (NPSP) / NPC-native |

---

## Object Model Selection

### V4S (NPSP Orgs)

| Business Entity | Salesforce Object (Full API Name) |
|---|---|
| Volunteer Campaign | `GW_Volunteers__Volunteer_Campaign__c` |
| Volunteer Job | `GW_Volunteers__Volunteer_Job__c` |
| Volunteer Shift | `GW_Volunteers__Volunteer_Shift__c` |
| Volunteer Hours | `GW_Volunteers__Volunteer_Hours__c` |
| Hours Rollup Field | `GW_Volunteers__Total_Volunteer_Hours__c` on Contact |

### NPC-Native

| Business Entity | Salesforce Object |
|---|---|
| Volunteer Initiative | `VolunteerInitiative__c` |
| Job Position Assignment | `JobPositionAssignment__c` |
| Total Hours | `TotalVolunteerHours__c` on Contact (DPE-computed) |

---

## DPE Schedule (NPC Only)

| Item | Value |
|---|---|
| DPE Definition Name | |
| Scheduled Frequency | |
| Estimated Lag (hours insert → field updated) | |
| Recognition automation trigger strategy | After DPE run / Scheduled Flow |

---

## Skills Matching Scope

- Is skills matching required? [ ] Yes  [ ] No
- If yes: [ ] Custom junction object  [ ] Third-party app (specify: _________)
- Junction object design: Contact → `Volunteer_Skill__c` ← Skill taxonomy
- Matching logic: [ ] Flow  [ ] Apex

---

## Recognition Workflow Design

| Milestone | Threshold (hours) | Trigger Event | Award / Action |
|---|---|---|---|
| Example: Bronze | 25 | After DPE run | Badge email |
| | | | |
| | | | |

---

## Validation Checklist

- [ ] All V4S API names include `GW_Volunteers__` prefix
- [ ] DPE schedule documented and lag accounted for in NPC automations
- [ ] Skills matching scoped as custom build if required
- [ ] Recognition flows trigger after DPE window (NPC) or hours rollup trigger (V4S)
- [ ] Volunteer self-service portal approach confirmed (Force.com Site for V4S, Experience Cloud for NPC)
- [ ] Pilot dataset tested with confirmed rollup totals

---

## Notes

_Capture any org-specific decisions, deviations, or open questions here._
