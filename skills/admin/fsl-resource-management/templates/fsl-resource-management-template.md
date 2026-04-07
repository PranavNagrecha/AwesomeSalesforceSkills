# FSL Resource Management — Work Template

Use this template when working on tasks in this area. Fill in each section as you progress through the workflow in SKILL.md.

## Scope

**Skill:** `fsl-resource-management`

**Request summary:** (describe what the user asked for — e.g., "onboard 12 new technicians with HVAC certifications", "set up the calibration rig as a capacity-based resource", "configure Required preference for Acme account")

---

## Context Gathered

Record answers to the Before Starting questions from SKILL.md before taking any action.

- **Field Service enabled?** (Setup > Field Service Settings — confirm ServiceResource and related objects are accessible)
- **Capacity-based resources involved?** (yes / no — if yes, list which resources and their Capacity/CapacityUnit requirements)
- **Existing Skill catalog:** (paste SOQL result or list of Skill.MasterLabel values already in the org — avoids duplicate Skill creation)
- **Certification expiry dates in scope?** (yes / no — if yes, list skill names and their EndDate values)
- **ResourcePreference changes in scope?** (yes / no — if yes, list Account names and required/preferred/excluded resource assignments)
- **Target service territories:** (list territory names — resources must be assigned as ServiceTerritoryMember before they appear in scheduling)
- **Known constraints or failure modes to watch for:**

---

## Approach

Which pattern from SKILL.md applies? (select one or more)

- [ ] Pattern: Registering a Technician with Skills and Certifications
- [ ] Pattern: Capacity-Based Resource for Shared Equipment
- [ ] Pattern: Enforcing a Customer Resource Requirement
- [ ] Other (describe):

**Why this pattern fits:**

---

## Resource Configuration Plan

| Resource Name | ResourceType | IsCapacityBased | RelatedRecordId (User) | Territory Assignment |
|---|---|---|---|---|
| (fill in) | Technician / Crew | true / false | (User Id or blank) | (Territory name) |

---

## Skill Assignment Plan

| Resource Name | Skill Name | SkillLevel (0–99.99) | StartDate | EndDate (if certification expires) |
|---|---|---|---|---|
| (fill in) | (from existing Skill catalog) | (numeric) | (YYYY-MM-DD or blank) | (YYYY-MM-DD or blank) |

---

## Capacity Configuration Plan (capacity-based resources only)

| Resource Name | Period StartDate | Period EndDate | Capacity | CapacityUnit |
|---|---|---|---|---|
| (fill in) | YYYY-MM-DD | YYYY-MM-DD | (number) | Hours / Appointments |

---

## ResourcePreference Plan

| Account Name | Resource Name | PreferenceType | Skill coverage verified? |
|---|---|---|---|
| (fill in) | (fill in) | Required / Preferred / Excluded | yes / no |

---

## Review Checklist

Tick each item as complete before marking work done.

- [ ] Each ServiceResource has `IsActive = true` unless intentionally deactivated
- [ ] ResourceType is `Technician` for individual workers and assets; `Crew` only for group units
- [ ] No `ServiceResourceSkill` records have `EndDate` in the past (`SELECT ... WHERE EndDate < TODAY`)
- [ ] No duplicate `ServiceResourceSkill` records exist for the same resource and skill combination
- [ ] Capacity-based resources have at least one active `ServiceResourceCapacity` record covering the current period
- [ ] `Required` ResourcePreference records are paired with resources that hold all required active skills
- [ ] Each ServiceResource has at least one `ServiceTerritoryMember` record in an active territory
- [ ] SkillLevel values align with work type minimum skill level requirements
- [ ] No territory involved in this work exceeds 50 active ServiceTerritoryMember records
- [ ] Test appointment created and expected candidates verified in Dispatcher Console

---

## Expiry Monitoring Query

Run this after setup to confirm no skills are already expired or expiring within 30 days:

```soql
SELECT Id, ServiceResource.Name, Skill.MasterLabel, SkillLevel, StartDate, EndDate
FROM ServiceResourceSkill
WHERE EndDate <= NEXT_N_DAYS:30
ORDER BY EndDate ASC
```

---

## Notes

Record any deviations from the standard pattern, edge cases encountered, and reasons for any decisions that differ from SKILL.md guidance.

- (deviation 1)
- (deviation 2)
