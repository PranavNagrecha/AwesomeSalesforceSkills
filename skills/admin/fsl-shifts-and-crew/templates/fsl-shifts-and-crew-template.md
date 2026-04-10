# FSL Shifts and Crew — Work Template

Use this template when configuring FSL Shift-based availability or Crew ServiceResources.

## Scope

**Skill:** `fsl-shifts-and-crew`

**Request summary:** (fill in what the user or project requires — e.g., "bulk shift generation for 30 technicians" or "static crew configuration for installation team")

---

## Context Gathered

Answer these before proceeding (see SKILL.md > Before Starting):

- **Operating Hours records in place?** Yes / No — list relevant Operating Hours names and time zones:
- **Existing ShiftTemplates or ShiftPatterns?** Yes / No — if yes, list names to avoid duplication:
- **Shift generation approach:** ShiftTemplate (ad hoc) / ShiftPattern (bulk, recommended for 10+ resources)
- **Crew model required:** Static (fixed members, skill aggregation) / Shell/Dynamic (variable membership, CrewSize governs capacity) / Not applicable
- **Known constraints (timezone mismatches, Operating Hours gaps, resource record type issues):**

---

## Shift Configuration Plan

### ShiftPattern Definition (if bulk generation)

| Field | Value |
|---|---|
| Pattern Name | (fill in) |
| PatternLength (days) | (e.g., 7 for weekly, 14 for two-week rotation) |
| TimeZone | (must match territory Operating Hours timezone) |

### ShiftPatternEntry Records

| DayOfPattern | StartTime | EndTime | ShiftType (optional) |
|---|---|---|---|
| 1 (Monday) | HH:MM | HH:MM | (fill in or leave blank) |
| 2 (Tuesday) | HH:MM | HH:MM | |
| 3 (Wednesday) | HH:MM | HH:MM | |
| 4 (Thursday) | HH:MM | HH:MM | |
| 5 (Friday) | HH:MM | HH:MM | |
| 6 (Saturday) | (leave blank if no weekend shifts) | | |
| 7 (Sunday) | | | |

### Resources Receiving Generated Shifts

| ServiceResource Name | ResourceType | Territory | Generation Date Range |
|---|---|---|---|
| (fill in) | Technician / Crew | (territory name) | (start – end dates) |

---

## Crew Configuration Plan (if applicable)

| Field | Value |
|---|---|
| Crew Name | (fill in) |
| Crew Model | Static / Shell (Dynamic) |
| CrewSize | (Shell only — expected headcount, e.g., 3) |
| Member Resources (Static only) | (list member Technician ServiceResource names) |

### Member Skill Assignments (Static Crew)

Skills must be assigned to each member's Technician ServiceResource, NOT to the Crew record.

| Member Resource | Skill Name | SkillLevel | StartDate | EndDate (if expiry) |
|---|---|---|---|---|
| (fill in) | (skill name) | (1–10) | (date) | (date or blank) |

---

## Validation Checklist

Before marking work complete, confirm each item:

- [ ] All generated Shift records have `Status = Confirmed` (verify via SOQL: `SELECT Status, COUNT(Id) FROM Shift WHERE StartTime >= TODAY GROUP BY Status`)
- [ ] Shift start/end times fall within the associated Operating Hours window (no overflow beyond OperatingHours.TimeSlots)
- [ ] ShiftPattern TimeZone matches the service territory's Operating Hours timezone
- [ ] Static Crew: ServiceCrewMember records created for all members with correct StartDate
- [ ] Static Crew: Required skills are on member Technician records (not on the Crew ServiceResource)
- [ ] Shell Crew: CrewSize is populated and reflects expected headcount
- [ ] Service appointments are dispatched to the Crew ServiceResource, not to individual member records
- [ ] Shift Get Candidates validated in Dispatcher Console — target resources appear as candidates for a test appointment in the shift window
- [ ] Ran `python3 check_fsl_shifts_and_crew.py --manifest-dir <path>` and resolved all WARNs

---

## Approach Notes

- Which pattern from SKILL.md applies? (ShiftPattern bulk generation / Static Crew / Shell Crew)
- Deviations from standard pattern:
- Any resource-type errors encountered and how resolved:

---

## Post-Work Notes

(Record any decisions, edge cases, or follow-up items discovered during implementation.)
