---
name: fsl-resource-and-skill-data
description: "Use this skill when bulk loading FSL ServiceResource records, ServiceResourceSkill data, skill certifications, capacity-based resource setup, and availability patterns. Trigger keywords: FSL resource migration, ServiceResourceSkill bulk load, skill certification tracking FSL, capacity-based resource, service resource availability. NOT for user provisioning, ServiceResource creation via UI, or ServiceTerritoryMember setup (covered by fsl-territory-data-setup)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "How do I bulk load field service technician skills and certifications"
  - "ServiceResourceSkill EffectiveStartDate and EffectiveEndDate for certification tracking"
  - "Capacity-based resource setup IsCapacityBased field requirement in FSL"
  - "SkillLevel numeric mapping from source system to Salesforce FSL"
  - "ServiceResourceCapacity records require IsCapacityBased true before loading"
tags:
  - fsl
  - field-service
  - data-migration
  - service-resource
  - skills
  - fsl-resource-and-skill-data
inputs:
  - "Technician/resource records from source system with skill types and certification dates"
  - "Skill definitions and SkillLevel values (0–99999 numeric scale)"
  - "Whether resources are capacity-based (crews) or individual technicians"
outputs:
  - "Ordered data load sequence: Skill → ServiceResource → ServiceResourceSkill"
  - "SkillLevel mapping pattern from text/percentage to FSL numeric scale"
  - "Capacity resource configuration and ServiceResourceCapacity load"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# FSL Resource and Skill Data

This skill activates when a data migration or org setup requires bulk loading FSL resource and skill data: Skill definitions, ServiceResource records, ServiceResourceSkill assignments, SkillRequirement mappings, and ServiceResourceCapacity records. Skill data has strict insert-order dependencies, a non-obvious numeric SkillLevel scale, and certification tracking behaviors that differ from typical HR system models.

---

## Before Starting

Gather this context before working on anything in this domain:

- Determine whether resources are individual technicians (standard ServiceResource) or crews/capacity-based resources (IsCapacityBased = true). Capacity-based resources require IsCapacityBased = true on the ServiceResource before any ServiceResourceCapacity records can be created.
- Map source system skill levels (often text like "Expert", "Intermediate", or percentages like "80%") to FSL's numeric SkillLevel field (0–99999). Document the mapping table.
- Confirm whether certification tracking (EffectiveStartDate/EffectiveEndDate on ServiceResourceSkill) is required. FSL has no native certification object — certification is tracked via the date range on the skill assignment record.
- Determine the ServiceResource.ResourceType for each record: Technician, Crew, or Service Vehicle.

---

## Core Concepts

### Insert Order

The correct sequence:
1. Skill (standalone — defines the skill type, e.g., "Electrical", "HVAC Certified")
2. ServiceResource (represents the technician or crew — linked to a User or Asset)
3. ServiceResourceSkill (junction between ServiceResource and Skill, with level and dates)
4. ServiceResourceCapacity (capacity hours per period — only for IsCapacityBased resources)

### SkillLevel — Numeric Scale (0–99999)

`ServiceResourceSkill.SkillLevel` is a numeric field ranging from 0 to 99999. Source systems typically use text labels ("Beginner", "Intermediate", "Expert") or percentage scores. You must establish an explicit numeric mapping:

Example mapping: Beginner = 1, Intermediate = 50, Expert = 99, Certified = 99999.

`SkillRequirement.MinimumSkillLevel` on Work Types sets the minimum skill level a resource must have to be scheduled for that work type. If a resource's SkillLevel < MinimumSkillLevel, the scheduling policy will exclude that resource.

### Certification Tracking via Date Range

FSL does not have a dedicated certification object. Certifications are tracked by the `EffectiveStartDate` and `EffectiveEndDate` fields on `ServiceResourceSkill`:

- A skill with no `EffectiveEndDate` is considered currently active
- A skill with `EffectiveEndDate` in the past is expired but the record is NOT auto-deleted
- Expired skill records remain in the database and must be queried with date filters to exclude them from active skill reporting

**Critical:** If a certification expires (EffectiveEndDate reached), the resource will no longer match SkillRequirements for work types that require that skill — but only if the scheduling policy evaluates certification dates.

### Capacity-Based Resources

Capacity-based resources represent crews or shift-based workers who are scheduled by capacity (hours available) rather than by individual appointment slot. To configure:
1. Set `ServiceResource.IsCapacityBased = true` on the resource record
2. Load `ServiceResourceCapacity` records specifying capacity hours per time period

Attempting to create `ServiceResourceCapacity` records for a resource where `IsCapacityBased = false` fails with a validation error.

---

## Common Patterns

### Bulk Skill and ServiceResourceSkill Load

**When to use:** Migrating technician skill data from a legacy field service system or HR system.

**How it works:**
1. Extract distinct skill types from source. Load as Skill records with External IDs.
2. Load ServiceResource records, linking to existing User records via User.FederationIdentifier or External ID.
3. Load ServiceResourceSkill records mapping ServiceResource External ID + Skill External ID + SkillLevel + dates.

**SkillLevel mapping example:**
```
Source: "Certified HVAC Technician"
FSL SkillLevel: 99
FSL SkillRequirement.MinimumSkillLevel on HVAC Work Type: 90
Result: Resource qualifies for HVAC appointments
```

### Certification Expiry Tracking

**When to use:** Source system tracks certification expiry dates that affect scheduling eligibility.

**How it works:** Load `ServiceResourceSkill.EffectiveEndDate` from the source certification expiry date. Build a scheduled report or Flow that queries skills with `EffectiveEndDate < TODAY()` and notifies the operations team to arrange recertification.

```soql
SELECT ServiceResource.Name, Skill.MasterLabel, EffectiveEndDate
FROM ServiceResourceSkill
WHERE EffectiveEndDate < TODAY()
ORDER BY EffectiveEndDate ASC
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Individual technician | ServiceResource with ResourceType = Technician | Standard scheduling model |
| Crew (multiple people one schedule) | ServiceResource with IsCapacityBased = true | Capacity scheduling model |
| Certification expiry tracking | EffectiveEndDate on ServiceResourceSkill | No native cert object — date range is the mechanism |
| Text skill levels from source | Define numeric mapping table, transform on load | SkillLevel is numeric 0-99999, cannot accept text |
| Skill no longer valid | Set EffectiveEndDate to expiry date, do NOT delete | Delete breaks history; expiry date preserves record |

---

## Recommended Workflow

1. **Extract distinct skill types** — Build a deduplicated list of all skill types in the source data. Create a numeric SkillLevel mapping table.
2. **Load Skill records** — One record per skill type. Add External IDs.
3. **Load ServiceResource records** — Map to existing User records. Set ResourceType and IsCapacityBased correctly. Add External IDs.
4. **Load ServiceResourceSkill records** — Map ServiceResourceId, SkillId, SkillLevel (numeric), EffectiveStartDate, EffectiveEndDate (if applicable).
5. **Load ServiceResourceCapacity (if capacity-based)** — Only after ServiceResource records have `IsCapacityBased = true`.
6. **Validate SkillRequirement alignment** — Query Work Types to confirm `SkillRequirement.MinimumSkillLevel` values align with the loaded SkillLevel scale.
7. **Test scheduling eligibility** — Create test ServiceAppointments and verify that resources with the correct skills appear as candidates in the Book Appointment action.

---

## Review Checklist

- [ ] Skill records loaded before ServiceResourceSkill
- [ ] ServiceResource records loaded before ServiceResourceSkill
- [ ] SkillLevel numeric mapping table documented and applied
- [ ] IsCapacityBased = true set before ServiceResourceCapacity load
- [ ] EffectiveStartDate populated for all ServiceResourceSkill records
- [ ] EffectiveEndDate populated for expired/expiring certifications
- [ ] SkillRequirement MinimumSkillLevel values on Work Types reviewed against loaded SkillLevel scale
- [ ] Test scheduling confirms resource skill eligibility

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Expired ServiceResourceSkill records are NOT auto-deleted** — They remain in the database indefinitely. Reporting on "current" skills must filter by `EffectiveEndDate > TODAY() OR EffectiveEndDate = NULL`.
2. **SkillLevel is numeric 0–99999 — text values throw a type error** — Source systems that store skill levels as "Expert" or "Level 3" must be transformed to numbers before loading.
3. **IsCapacityBased must be true BEFORE ServiceResourceCapacity is created** — Setting IsCapacityBased after attempting to load capacity records fails. The field must be set on the ServiceResource at creation time.
4. **ServiceResource links to User or Asset, not Contact** — A common migration error is trying to link ServiceResource to a Contact record. Only User and Asset are valid related-record types.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Skill load CSV template | Template with Skill MasterLabel, Description, and External ID columns |
| ServiceResourceSkill load CSV | Template with ServiceResource, Skill, SkillLevel, EffectiveStartDate, EffectiveEndDate columns |
| SkillLevel mapping table | Source-to-FSL numeric mapping for skill levels |

---

## Related Skills

- data/fsl-territory-data-setup — ServiceTerritoryMember setup that follows ServiceResource load
- architect/fsl-optimization-architecture — How skill requirements factor into scheduling policy and optimization engine
