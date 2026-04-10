# FSL Resource and Skill Data — Work Template

Use this template when loading FSL resource and skill data.

## Scope

**Skill:** `fsl-resource-and-skill-data`

**Request summary:** (fill in — e.g. "Migrate 850 technician skill records from SAP HR to FSL")

## Context Gathered

- **Resource types:** Technician / Crew / Service Vehicle (circle)
- **Capacity-based resources:** yes / no
- **Source skill level format:** (text labels / percentage / numeric)
- **Certification expiry tracking required:** yes / no
- **SkillRequirement MinimumSkillLevel on Work Types:** (query and document before defining scale)

## SkillLevel Mapping Table

| Source Label | FSL SkillLevel (0-99999) |
|---|---|
| (define before migration) | |

## Load Sequence

| Step | Object | Operation | Notes |
|------|--------|-----------|-------|
| 1 | Skill | Upsert on Legacy_Skill_Id__c | One per skill type |
| 2 | ServiceResource | Upsert on Legacy_SR_Id__c | Set IsCapacityBased for crews |
| 3 | ServiceResourceSkill | Upsert on Legacy_SRS_Id__c | Numeric SkillLevel, EffectiveStartDate |
| 4 | ServiceResourceCapacity | Upsert (if capacity-based only) | After ServiceResource with IsCapacityBased=true |

## ServiceResourceSkill CSV Required Columns

```
Legacy_SRS_Id__c, ServiceResourceId (via Legacy_SR_Id__c), SkillId (via Legacy_Skill_Id__c),
SkillLevel (numeric), EffectiveStartDate, EffectiveEndDate (for expiring certs)
```

## Validation Checklist

- [ ] SkillLevel values are all integers (no text)
- [ ] EffectiveStartDate populated for all ServiceResourceSkill records
- [ ] EffectiveEndDate populated for expired/expiring certifications
- [ ] IsCapacityBased = true set for crew resources before ServiceResourceCapacity load
- [ ] SkillLevel scale consistent with SkillRequirement MinimumSkillLevel on Work Types
- [ ] Test scheduling confirms certified resources appear as candidates for work types requiring skills

## Notes

(Record deviations and transformation rules applied.)
