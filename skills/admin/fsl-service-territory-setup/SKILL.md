---
name: fsl-service-territory-setup
description: "Use this skill to configure Field Service Lightning service territories — including territory types, operating hours, time slots, territory hierarchy, member types, and polygon boundaries. NOT for ETM territories (Territory2 / Enterprise Territory Management in Sales Cloud), and NOT for Salesforce Scheduler territories."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "create service territories in Field Service Lightning"
  - "configure territory operating hours FSL"
  - "set up territory hierarchy field service lightning"
  - "assign technicians to service territories as primary or secondary members"
  - "why is the Hard Boundary work rule ignoring my territory members"
  - "configure relocation territory for mobile workforce"
  - "service territory polygon boundaries for scheduling"
tags:
  - field-service
  - fsl
  - service-territory
  - scheduling
  - operating-hours
  - service-resource
inputs:
  - "List of geographic regions or dispatch zones requiring field service coverage"
  - "Technician (ServiceResource) roster and their home or primary base locations"
  - "Business operating hours per region (days of week, shift times, holidays)"
  - "Whether a territory hierarchy (e.g., region > district > local) is required"
  - "Work rules in use, particularly whether Hard Boundary is enabled"
outputs:
  - "Configured ServiceTerritory records with correct ParentTerritoryId hierarchy"
  - "OperatingHours and TimeSlot records tied to each territory"
  - "ServiceTerritoryMember junction records with correct MemberType (Primary / Secondary / Relocation)"
  - "Territory boundary polygons (ServiceTerritoryPolygon) where polygon-based routing is needed"
  - "Checklist confirming limits compliance (50 resources/territory, 1,000 SA/day/territory)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# FSL Service Territory Setup

This skill activates when a practitioner needs to create or reconfigure Field Service Lightning service territories, including territory hierarchy, operating hours, member type assignments, and polygon boundaries. It covers the full ServiceTerritory data model and the scheduling constraints that depend on it.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Field Service is enabled in the org (Setup > Field Service Settings). ServiceTerritory, ServiceTerritoryMember, and OperatingHours objects must be accessible.
- Identify whether Hard Boundary work rules are in use — this changes which member types matter for scheduling eligibility. Hard Boundary only honors Primary and Relocation memberships, not Secondary.
- Know the territory hierarchy depth. The `ParentTerritoryId` lookup on ServiceTerritory is a single-level pointer; deep hierarchies require intentional planning.
- Clarify whether any technicians will use Relocation memberships. Relocation requires explicit `EffectiveStartDate` and `EffectiveEndDate` — omitting them causes the routing engine to silently skip the member.
- Note the two hard limits: 50 active ServiceTerritoryMembers per territory, and 1,000 service appointments per day per territory.

---

## Core Concepts

### ServiceTerritory and the Core Data Model

`ServiceTerritory` is the central scheduling unit for Field Service. Every service appointment is associated with one territory, and the scheduling optimizer and dispatcher use territory boundaries, operating hours, and member rosters to assign work.

Key fields on ServiceTerritory:
- `Name` — human-readable territory label
- `ParentTerritoryId` — lookup to another ServiceTerritory for hierarchy
- `OperatingHoursId` — required for scheduling; defines when the territory is open for work
- `IsActive` — inactive territories are excluded from scheduling

ServiceTerritory is completely separate from the Sales Cloud `Territory2` object used by Enterprise Territory Management. They share no data, no configuration, and no UI. Do not use ETM setup guides when configuring FSL territories.

### ServiceTerritoryMember and Member Types

`ServiceTerritoryMember` is the junction object between `ServiceTerritory` and `ServiceResource`. A resource (technician, crew, or equipment) becomes eligible for work in a territory only via an active membership.

The `MemberType` field controls routing behavior:

| MemberType | Behavior | Constraint |
|---|---|---|
| Primary | Main working territory. Used by the routing engine as the travel origin for the resource. | Only one active Primary membership per resource at any time |
| Secondary | Indicates the resource can occasionally work in this territory. Multiple allowed. Does NOT satisfy Hard Boundary work rules. | Multiple allowed |
| Relocation | Temporary assignment. Routing engine suppresses cross-boundary travel calculation during the date range. | Requires `EffectiveStartDate` and `EffectiveEndDate` |

`EffectiveStartDate` and `EffectiveEndDate` on the membership record control when the membership is active for scheduling. Leave `EffectiveEndDate` blank to create an open-ended membership (except for Relocation, which always requires both dates).

### OperatingHours and TimeSlots

Every `ServiceTerritory` requires an `OperatingHours` record. Operating hours define the windows during which service appointments can be scheduled in the territory.

- `OperatingHours` holds the name and time zone for the schedule.
- `TimeSlot` child records define the actual open periods (day of week, start time, end time, type).
- `TimeSlot.Type` can be `Normal` (regular business hours) or `Extended` (after-hours windows).
- The time zone is set at the `OperatingHours` level and applies to all child TimeSlots. A single OperatingHours record cannot span multiple time zones.

Operating hours can be shared across territories or unique per territory. Holiday operating hours can be associated to reflect territory-level closures without modifying the base schedule.

---

## Common Patterns

### Pattern: Basic Territory with Operating Hours and Primary Members

**When to use:** A new dispatch zone needs to be set up from scratch for a group of technicians.

**How it works:**
1. Create an `OperatingHours` record specifying the territory time zone.
2. Add `TimeSlot` records for each working day (e.g., Monday–Friday, 08:00–17:00).
3. Create the `ServiceTerritory` record and link the `OperatingHours` via `OperatingHoursId`.
4. For each technician, create a `ServiceTerritoryMember` with `MemberType = Primary` and no end date.
5. Verify no technician already has an active Primary membership in another territory — only one is allowed per resource at a time.

**Why not the alternative:** Assigning all members as Secondary avoids the "one Primary" constraint, but then Hard Boundary work rules will not enforce territory boundaries during optimization. Technicians without a Primary territory also have no travel origin for scheduling calculations.

### Pattern: Territory Hierarchy for Regional Structure

**When to use:** A field service organization has regional territories containing multiple local dispatch zones, and reporting or routing should reflect that hierarchy.

**How it works:**
1. Create parent territories first (e.g., `West Region`, `East Region`) with `ParentTerritoryId` left blank.
2. Create child territories and set `ParentTerritoryId` to the appropriate parent.
3. Assign operating hours at the local level; regional territories may be structural only.
4. Technicians are typically assigned as members of local territories, not regional ones.
5. Reports and list views can filter by parent territory to aggregate performance across the hierarchy.

**Why not the alternative:** Naming conventions alone (e.g., "West - District 1") do not create a traversable hierarchy and cannot be used in hierarchy-aware queries or UI navigation. Use `ParentTerritoryId` for real parent-child relationships.

### Pattern: Relocation Territory for Temporary Assignments

**When to use:** A technician is temporarily relocated from their home territory to support another region for a defined period.

**How it works:**
1. Identify the destination territory and the assignment window.
2. Create a `ServiceTerritoryMember` with `MemberType = Relocation`, setting `EffectiveStartDate` to the first day and `EffectiveEndDate` to the last day of the assignment.
3. Leave the original Primary membership active and unchanged.
4. During the relocation window, the routing engine suppresses cross-boundary travel estimates between the Primary and Relocation territories.

**Why not the alternative:** Adding the technician as Secondary in the destination territory does not suppress travel calculations, so the optimizer may assign them work in both territories simultaneously without accounting for the distance between them.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Technician permanently works one region | Primary membership in that territory, no end date | Provides travel origin for scheduling; satisfies Hard Boundary rule |
| Technician occasionally covers a second zone | Secondary membership in the second territory | Multiple Secondary memberships are allowed; does not conflict with Primary |
| Technician temporarily assigned to another region | Relocation membership with explicit start/end dates | Routing engine suppresses travel calc across boundary during that window |
| Hard Boundary work rule is active | Ensure Primary or Relocation membership exists in target territory | Hard Boundary only honors Primary and Relocation; Secondary is ignored |
| Need to share operating hours across territories | Single OperatingHours record linked to multiple territories | Reduces maintenance; changes propagate to all linked territories |
| Territory spans multiple time zones | Separate OperatingHours records per time zone | OperatingHours time zone applies to all TimeSlots in that record |
| Territory is being decommissioned | Set `IsActive = false` on ServiceTerritory | Inactive territories are excluded from all scheduling operations |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify prerequisites** — Confirm Field Service is enabled (Setup > Field Service Settings). Check that the ServiceTerritory and OperatingHours objects are visible to the running user's profile. Identify all work rules in use, especially Hard Boundary.

2. **Create Operating Hours** — Before creating territories, create `OperatingHours` records for each distinct schedule pattern. Add `TimeSlot` records for each working day and any extended-hours windows. If territories share hours, a single OperatingHours record can be reused across them.

3. **Create ServiceTerritory records** — Create territories from the highest level down (parent before child). Set `OperatingHoursId` on each. Set `ParentTerritoryId` on child territories. Keep `IsActive = true` for territories that should appear in scheduling.

4. **Assign ServiceTerritoryMembers** — For each ServiceResource, determine the correct `MemberType`. Assign exactly one Primary per resource. Add Secondary memberships for occasional coverage zones. Add Relocation memberships with mandatory `EffectiveStartDate` and `EffectiveEndDate` for temporary assignments.

5. **Configure polygon boundaries (if needed)** — If the org uses polygon-based territory matching (rather than manual territory assignment on the service appointment), create `ServiceTerritoryPolygon` records attached to each territory with geographic coordinates defining the boundary.

6. **Validate limits** — Check that no territory has more than 50 active ServiceTerritoryMember records. Estimate peak daily appointment volume and confirm it is under 1,000 service appointments per day per territory. Adjust territory granularity if needed.

7. **Test scheduling behavior** — Create a test service appointment within the territory's operating hours and attempt to schedule it using the Dispatcher Console or Einstein for Field Service. Confirm the correct technicians appear as candidates and that Hard Boundary behavior matches expectations.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Each ServiceTerritory has a valid `OperatingHoursId` linked
- [ ] Each ServiceTerritory that is a child has a valid `ParentTerritoryId`
- [ ] Each active ServiceResource has exactly one Primary membership (not zero, not two)
- [ ] All Relocation memberships have explicit `EffectiveStartDate` and `EffectiveEndDate`
- [ ] No territory exceeds 50 active ServiceTerritoryMember records
- [ ] Estimated daily appointment volume per territory is under 1,000
- [ ] Hard Boundary work rule behavior is confirmed if that work rule is active
- [ ] Territory `IsActive` flags are correct — inactive territories are excluded from scheduling
- [ ] OperatingHours time zones match the geographic area of each territory

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Hard Boundary only honors Primary and Relocation — not Secondary** — If the Hard Boundary work rule is active, technicians with only a Secondary membership in a territory are excluded from work in that territory. Teams that add Secondary memberships expecting full scheduling eligibility are surprised when those technicians never appear as candidates.

2. **Relocation without explicit dates causes silent routing failures** — A Relocation `ServiceTerritoryMember` missing `EffectiveStartDate` or `EffectiveEndDate` is silently ignored by the routing engine. No error is raised; the technician simply does not appear as a candidate for the relocation territory.

3. **One active Primary per resource — enforcement is soft in the API** — Salesforce does not hard-block creating a second active Primary membership via the API. The resulting duplicate Primary state breaks scheduling silently. Data loading tools must deduplicate Primary memberships before inserting.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| ServiceTerritory records | Configured territory hierarchy with operating hours and active status |
| OperatingHours + TimeSlot records | Business hours definitions per territory or shared across territories |
| ServiceTerritoryMember records | Resource-to-territory junction records with correct MemberType and date ranges |
| ServiceTerritoryPolygon records | Geographic boundary definitions for polygon-based territory matching |
| Validation checklist | Completed review checklist confirming limits and configuration correctness |

---

## Related Skills

- `fsl-scheduling-policies` — scheduling policies and work rules (including Hard Boundary) that depend on territory setup
- `fsl-service-resource-setup` — ServiceResource configuration, which must precede territory member assignment
- `fsl-integration-patterns` — API patterns for bulk-loading territory and membership records
- `enterprise-territory-management` — Sales Cloud ETM setup; completely separate from FSL ServiceTerritory
