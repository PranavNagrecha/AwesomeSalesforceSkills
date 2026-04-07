---
name: fsl-resource-management
description: "Use this skill to configure Field Service Lightning service resources — including ServiceResource types, skill assignments via ServiceResourceSkill, capacity-based resource setup, and ResourcePreference rules. NOT for service territory setup (see fsl-service-territory-setup), NOT for scheduling policy configuration, and NOT for FSL mobile app setup."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "configure field service resource types technician crew vehicle tool"
  - "technician not appearing as scheduling candidate in field service"
  - "set up skill levels and certifications for field service workers"
  - "capacity-based resource scheduling hours or appointments per period"
  - "expired certification silently blocking field service appointments"
  - "set preferred or required resource for a service account in field service"
  - "field service resource skill record start and end date setup"
tags:
  - field-service
  - fsl
  - service-resource
  - scheduling
  - resource-skills
  - capacity
  - resource-preference
inputs:
  - "List of field workers, crews, and non-human assets (vehicles, tools) to register as resources"
  - "Skill catalog with proficiency levels and any certification expiry dates"
  - "Whether any resources are capacity-based (billed by hours or appointment count rather than time-slot availability)"
  - "Customer accounts that require preferred, required, or excluded resource assignments"
  - "Target service territories (needed to assign resources as territory members)"
outputs:
  - "Configured ServiceResource records with correct ResourceType (Technician or Crew)"
  - "ServiceResourceSkill junction records with SkillLevel, optional StartDate and EndDate"
  - "ServiceResourceCapacity records for capacity-based resources"
  - "ResourcePreference records linking accounts to preferred, required, or excluded resources"
  - "Validation checklist confirming limits compliance and no silently expired skill records"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# FSL Resource Management

This skill activates when a practitioner needs to configure Field Service Lightning service resources — covering ServiceResource object setup, skill and certification assignment, capacity-based resource types, and customer resource preferences. It addresses the full resource data model that the FSL scheduling engine queries when searching for appointment candidates.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Field Service is enabled (Setup > Field Service Settings). ServiceResource, ServiceResourceSkill, Skill, and ResourcePreference objects must be accessible to the running user.
- Identify whether the org uses capacity-based resources. Capacity-based resources (IsCapacityBased = true) are managed differently from time-slot-available technicians and require ServiceResourceCapacity records instead of shift-based availability.
- Collect the skill catalog — the set of Skill records that already exist in the org. ServiceResourceSkill junction records reference existing Skill records by ID. Creating skills that duplicate existing ones causes invisible duplicate-assignment errors.
- Understand certification expiry requirements. ServiceResourceSkill supports optional StartDate and EndDate fields. Any record whose EndDate is in the past is silently treated as inactive by the scheduler — no error, the resource simply drops out of candidate results.
- Note the hard scheduling limit of 20 candidates returned per scheduling search. If a territory has many qualified resources, only 20 are evaluated. Skill-level ordering and resource preferences influence which 20 are surfaced.

---

## Core Concepts

### ServiceResource Object and ResourceType

`ServiceResource` represents any person, crew, vehicle, or tool participating in field service operations. The `ResourceType` field determines how the record behaves in the scheduling engine:

| ResourceType | Description | Linked to User? |
|---|---|---|
| Technician | An individual field worker. Can be linked to a Salesforce User record via the `RelatedRecordId` field. | Optional — can exist without a User |
| Crew | A group of technicians acting as a single schedulable unit. Members are added via ServiceCrewMember. | No User link |

Non-human assets (vehicles, tools, specialized equipment) are typically created as Technician-type resources without a User link. The scheduling engine treats them identically to human technicians when assigning appointments — set skills and capacity accordingly.

Key fields on ServiceResource:
- `Name` — display label used in the Dispatcher Console and scheduling results
- `ResourceType` — `Technician` or `Crew`; cannot be changed after record creation
- `RelatedRecordId` — polymorphic lookup to a User record (for Technician type only)
- `IsActive` — inactive resources are excluded from all scheduling searches
- `IsCapacityBased` — when true, availability is governed by ServiceResourceCapacity records rather than shift blocks

### ServiceResourceSkill and Skill Levels

`ServiceResourceSkill` is the junction object that assigns a `Skill` to a `ServiceResource`. The scheduling engine uses these assignments to match resources to work type requirements on service appointments.

Key fields:
- `ServiceResourceId` — the resource receiving the skill
- `SkillId` — the Skill record being assigned
- `SkillLevel` — decimal value from 0 to 99.99 representing proficiency; work type requirements specify a minimum level
- `StartDate` — (optional) date from which the skill is active; leave blank for immediate activation
- `EndDate` — (optional) certification expiry date; **any record with an EndDate in the past is silently excluded from scheduling without any warning or error**

A resource with a skill whose EndDate is expired appears in the system as if it has no skill at all. This is the leading cause of unexplained candidate drop-outs in production FSL orgs. Routine certification audits should query `ServiceResourceSkill WHERE EndDate < TODAY` and either renew or deactivate those records.

### Capacity-Based Resources

When `IsCapacityBased = true` on a ServiceResource, the scheduling engine does not evaluate that resource against shift blocks or time slot availability. Instead, it checks `ServiceResourceCapacity` records to determine whether the resource has remaining capacity for the period.

`ServiceResourceCapacity` fields:
- `ServiceResourceId` — the capacity-based resource
- `StartDate` / `EndDate` — the period these capacity limits cover
- `TimeSlotType` — `Normal` (regular hours) or `Extended` (after-hours)
- `Capacity` — maximum units available in the period
- `CapacityUnit` — `Hours` or `Appointments`; defines what the Capacity number measures

Capacity resources are used for shared assets (e.g., a pool of specialized diagnostic tools that can be booked up to 8 hours/day) and contractors billed by appointment count rather than shift. A capacity resource with no active ServiceResourceCapacity record cannot be scheduled.

### ResourcePreference

`ResourcePreference` expresses a customer's relationship to a specific resource. The scheduling engine uses preferences to rank or restrict candidates during appointment assignment.

The `PreferenceType` field accepts three values:
- `Preferred` — the resource is favored but not required; other candidates are still valid
- `Required` — only this resource can be assigned to appointments for this account; the scheduler will not assign anyone else
- `Excluded` — this resource must never be assigned to appointments for this account

Key fields:
- `RelatedRecordId` — the Account (or other object) expressing the preference
- `ServiceResourceId` — the resource being preferred/required/excluded
- `PreferenceType` — `Preferred`, `Required`, or `Excluded`

A Required preference combined with an expired skill on that resource creates a scheduling deadlock: the scheduler looks only for the required resource but that resource's skill is expired, so no candidates are returned.

---

## Common Patterns

### Pattern: Registering a Technician with Skills and Certifications

**When to use:** Onboarding a new field technician or adding a certified skill (e.g., electrical certification with expiry) to an existing resource.

**How it works:**
1. Create (or locate) the `ServiceResource` record with `ResourceType = Technician`. Link `RelatedRecordId` to the technician's User record if they need mobile app access.
2. Set `IsActive = true`. Confirm `IsCapacityBased = false` for time-slot-based availability.
3. Identify the relevant `Skill` records in the org. Query `SELECT Id, MasterLabel FROM Skill` to avoid creating duplicates.
4. Create a `ServiceResourceSkill` record for each skill, setting:
   - `SkillLevel` to the technician's proficiency (e.g., 75 for journeyman, 99 for master)
   - `StartDate` to today if the certification begins now
   - `EndDate` to the certification expiry date if one applies
5. Assign the resource to the appropriate territory via `ServiceTerritoryMember` (covered in `fsl-service-territory-setup`).
6. Test by creating a service appointment with a matching work type and verifying the technician appears as a scheduling candidate.

**Why not the alternative:** Creating skills at the Skill object level without ServiceResourceSkill junction records has no effect on scheduling. The skill must be explicitly linked to the resource.

### Pattern: Capacity-Based Resource for Shared Equipment

**When to use:** A piece of equipment (e.g., a calibration rig, a specialized truck) can be booked for a fixed number of hours or appointments per day and is shared across multiple service appointments.

**How it works:**
1. Create the `ServiceResource` with `ResourceType = Technician` (equipment uses this type), a descriptive Name, no `RelatedRecordId`, and `IsCapacityBased = true`.
2. Set `IsActive = true`.
3. Create `ServiceResourceCapacity` records for each period the equipment is available:
   - `StartDate` and `EndDate` defining the period (e.g., current month)
   - `Capacity` set to the maximum units (e.g., 8 for 8 hours/day)
   - `CapacityUnit` set to `Hours` or `Appointments`
4. Assign the equipment resource to the relevant service territory via `ServiceTerritoryMember`.
5. Add the necessary skill (e.g., `Equipment-CalibrationRig`) via `ServiceResourceSkill` so work types requiring that equipment find this resource during scheduling.

**Why not the alternative:** Using a standard time-slot-available resource for shared equipment means the scheduler treats it as if it has one dedicated shift, which does not correctly model shared or partial-day bookings across multiple appointments.

### Pattern: Enforcing a Customer Resource Requirement

**When to use:** A customer account has a contractual or relationship requirement that a specific technician always handles their work orders.

**How it works:**
1. Identify the Account record and the ServiceResource representing the required technician.
2. Create a `ResourcePreference` record:
   - `RelatedRecordId` = the Account Id
   - `ServiceResourceId` = the technician's ServiceResource Id
   - `PreferenceType` = `Required`
3. Verify the required technician has all skills specified on the account's work types. A Required preference against an under-skilled or skill-expired resource results in zero candidates returned.
4. Consider pairing this with a backup plan: if the required technician is unavailable, a human dispatcher must manually override the preference or temporarily change it to `Preferred`.

**Why not the alternative:** Relying on dispatcher memory or case notes to enforce customer-resource assignments is not scalable and breaks when dispatchers change. The ResourcePreference object encodes this rule in the data model so the scheduler enforces it automatically.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Individual field worker needing mobile access | Technician-type ServiceResource linked to their User via RelatedRecordId | User link enables FSL mobile app authentication and push notifications |
| Non-human asset (vehicle, tool) | Technician-type ServiceResource with no RelatedRecordId, IsCapacityBased as needed | Vehicles and tools model identically to technicians; ResourceType Crew is for groups |
| Group of workers dispatched as one unit | Crew-type ServiceResource with members added via ServiceCrewMember | Crew dispatches the entire group as one scheduling candidate |
| Resource available fixed hours/appointments per period | IsCapacityBased = true with ServiceResourceCapacity records | Capacity model prevents overbooking shared assets |
| Certification that expires on a known date | ServiceResourceSkill with EndDate set to expiry | Scheduler silently drops the resource when EndDate passes; EndDate is the correct enforcement mechanism |
| Customer always served by specific technician | ResourcePreference with PreferenceType = Required | Encodes the constraint in the data model; scheduler enforces automatically |
| Customer should avoid a specific technician | ResourcePreference with PreferenceType = Excluded | Scheduler will not surface excluded resources as candidates for that account |
| Technicians not appearing as candidates | Query ServiceResourceSkill WHERE EndDate < TODAY for this resource | Expired skill records are the most common silent cause of missing candidates |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify prerequisites** — Confirm Field Service is enabled (Setup > Field Service Settings). Verify that ServiceResource, Skill, ServiceResourceSkill, and ResourcePreference are accessible. Run `SELECT Id, MasterLabel FROM Skill` to obtain the existing skill catalog before creating any new skills.

2. **Create or update ServiceResource records** — For each technician, crew, or asset, create a `ServiceResource` with the correct `ResourceType`. Set `RelatedRecordId` for any technician who needs mobile app access. Set `IsCapacityBased = true` only for resources governed by capacity rather than shift blocks. Set `IsActive = true`.

3. **Assign skills** — Create `ServiceResourceSkill` records for each resource-skill pairing. Set `SkillLevel` to the resource's proficiency. Set `EndDate` for any certification with an expiry. Avoid duplicate skill assignments on the same resource — query first.

4. **Configure capacity records if needed** — For capacity-based resources, create `ServiceResourceCapacity` records covering the scheduling horizon. Set `Capacity` and `CapacityUnit` to match business rules. Gaps in the date coverage silently prevent scheduling.

5. **Configure ResourcePreference records** — For accounts with preferred, required, or excluded resource assignments, create `ResourcePreference` records with the appropriate `PreferenceType`. Cross-check that Required resources have all necessary active skills.

6. **Assign resources to territories** — Each resource must have at least one `ServiceTerritoryMember` record before it will appear in scheduling searches. See `fsl-service-territory-setup` for member type rules.

7. **Validate and test** — Query `SELECT Id, ServiceResourceId, EndDate FROM ServiceResourceSkill WHERE EndDate < TODAY` to surface any expired records. Create a test service appointment and confirm expected candidates appear in the Dispatcher Console. Verify the 20-candidate limit is not masking under-qualified resources in large territories.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Each ServiceResource has `IsActive = true` unless intentionally deactivated
- [ ] ResourceType is `Technician` for individual workers and assets; `Crew` only for group units
- [ ] Capacity-based resources have at least one active `ServiceResourceCapacity` record covering the current period
- [ ] No `ServiceResourceSkill` records have `EndDate` in the past (query: `WHERE EndDate < TODAY`)
- [ ] No duplicate `ServiceResourceSkill` records exist for the same resource and skill combination
- [ ] Required `ResourcePreference` records are paired with resources that hold all required active skills
- [ ] Each ServiceResource has at least one `ServiceTerritoryMember` record in an active territory
- [ ] SkillLevel values align with work type minimum skill level requirements
- [ ] The 50-resources-per-territory limit is not exceeded for any territory this resource joins

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Expired ServiceResourceSkill records silently block scheduling** — When a `ServiceResourceSkill` record has an `EndDate` in the past, the scheduler treats the resource as if it has no skill at all. No error message is shown in the Dispatcher Console or optimization log. The resource simply does not appear as a candidate. This is the most common unexplained candidate drop-out in production FSL orgs.

2. **Capacity resources with date gaps are unschedulable without warning** — A capacity-based resource with no active `ServiceResourceCapacity` record for the current period cannot be scheduled. The scheduler does not flag this as a configuration error; it simply returns no capacity and excludes the resource. Capacity records must be created proactively to cover future scheduling windows.

3. **Required ResourcePreference + missing skill = zero candidates, no error** — When a `ResourcePreference` with `PreferenceType = Required` points to a resource that lacks the required skill (or whose skill is expired), the scheduler returns zero candidates for that appointment. The error surfaces as "no available resources" rather than as a preference or skill configuration problem.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| ServiceResource records | Configured technicians, crews, and assets with correct ResourceType and IsCapacityBased flag |
| ServiceResourceSkill records | Skill-to-resource junction records with SkillLevel and optional certification dates |
| ServiceResourceCapacity records | Period-based capacity definitions for capacity-based resources |
| ResourcePreference records | Customer-resource preference, required, or exclusion rules |
| Validation checklist | Completed review checklist confirming no expired skills, no capacity gaps, and limits compliance |

---

## Related Skills

- `fsl-service-territory-setup` — ServiceTerritory and ServiceTerritoryMember configuration; resources must be assigned to territories before they appear in scheduling
- `fsl-scheduling-policies` — Work rules and scheduling policies that consume resource skill and preference data during optimization
- `fsl-work-type-setup` — Work type and required skill configuration; skill level minimums on work types must match resource SkillLevel values
