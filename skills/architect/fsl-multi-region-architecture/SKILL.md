---
name: fsl-multi-region-architecture
description: "Use this skill when designing FSL for multiple geographic regions or timezones: territory timezone configuration, cross-territory resource assignment, concurrent optimization serialization, and regional scheduling boundaries. Trigger keywords: multi-region FSL, FSL timezone territories, cross-territory resource scheduling, concurrent optimization territories, international FSL deployment. NOT for multi-org strategy, single-timezone single-region FSL deployments, or Experience Cloud multi-region (covered by architect/multi-org-strategy)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Scalability
triggers:
  - "FSL deployment spanning multiple timezones — how to configure territories correctly"
  - "Resources assigned to multiple service territories for cross-territory scheduling"
  - "Concurrent optimization jobs for multiple territories in different regions conflict"
  - "Appointment booking showing wrong time slots for customers near timezone boundary"
  - "Hard boundary vs soft boundary for cross-territory resource assignment in FSL"
tags:
  - fsl
  - field-service
  - multi-region
  - timezone
  - territories
  - cross-territory
  - fsl-multi-region-architecture
inputs:
  - "Geographic regions and timezone coverage of the FSL deployment"
  - "Whether resources serve multiple territories (cross-territory assignment)"
  - "Service territories that share resources across geographic boundaries"
outputs:
  - "Timezone-aligned territory design recommendations"
  - "Cross-territory resource assignment pattern (Hard vs. Soft boundary)"
  - "Optimization serialization strategy for multi-territory concurrent jobs"
  - "Appointment booking timezone configuration guidance"
dependencies:
  - architect/fsl-optimization-architecture
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# FSL Multi-Region Architecture

This skill activates when an architect designs a FSL deployment spanning multiple geographic regions or timezones. Multi-region FSL introduces territory timezone configuration requirements, cross-territory resource assignment patterns, and optimization serialization constraints that single-region deployments don't encounter.

---

## Before Starting

Gather this context before working on anything in this domain:

- Map all geographic regions and their timezones. Identify any service territories that would need to span timezone boundaries — these must be split.
- Determine whether any resources need to serve multiple territories (e.g., specialists who travel across regional boundaries). This requires Secondary ServiceTerritoryMember records.
- Confirm whether optimization jobs for different regions run concurrently. Concurrent optimization jobs over territories that share resources conflict and must be serialized.
- Understand the customer appointment booking experience — specifically, whether customers in border areas between territories need to see slots in their local timezone.

---

## Core Concepts

### Territory Timezone Configuration

Each ServiceTerritory derives its timezone from its associated OperatingHours record. The `Book Appointment` Global Action derives available time slots using the territory's OperatingHours timezone. 

**Critical architectural constraint:** If a territory's polygon boundary crosses a timezone line, the appointment booking UI will show time slots that don't correspond to the customer's local time. A territory polygon in the Eastern US that extends into the Central timezone will show Eastern time slots for customers who expect Central time.

**Design rule:** Service territory polygon boundaries must not cross timezone lines. If coverage spans two timezones, create two separate territories — one per timezone — each with its own OperatingHours record specifying the correct timezone.

### Cross-Territory Resource Assignment

Resources are assigned to territories via ServiceTerritoryMember. For cross-territory resources:

| TerritoryType | Behavior | Use Case |
|---|---|---|
| **Primary** | Home territory. Resource appears first in scheduling for this territory | Standard technician home assignment |
| **Secondary** | Resource can be scheduled in this territory as overflow | Specialist covering multiple regions |
| **Hard Boundary** | Resource is restricted to their primary territory — cannot be scheduled in others | Union rules, certification zone restrictions |
| **Soft Boundary** | Resource can be scheduled in secondary territories | Standard overflow coverage |

Hard Boundaries restrict a resource to their Primary territory. Soft Boundaries allow scheduling across Primary and Secondary territories. The scheduling policy's Travel Radius and boundary settings determine which assignments the engine considers.

**Creating cross-territory assignment:**
1. Create a Primary ServiceTerritoryMember for the resource's home territory
2. Create one or more Secondary ServiceTerritoryMember records for overflow territories
3. Set boundary mode to Soft in the scheduling policy

### Optimization Serialization for Shared Resources

**Critical constraint:** Concurrent Global optimization jobs for territories that share resources via Secondary assignments will conflict. When Territory A's optimization is assigning a shared resource to an appointment while Territory B's optimization is simultaneously trying to reassign the same resource, one job will fail or produce incorrect results.

**Design rule:** Territories that share resources must run Global optimization sequentially, not concurrently. Schedule optimization jobs with time gaps between regions:
- Region A (10pm–11pm)
- Region B (11pm–midnight)
- Region C (midnight–1am)

If optimization windows overlap, use territory groups with serialized execution.

---

## Common Patterns

### Timezone-Split Territory Design

**When to use:** FSL deployment spanning two or more timezones.

**How it works:**
1. Map territory coverage areas to timezone boundaries
2. For any territory that spans a timezone line: split into two territories aligned to each timezone
3. Create separate OperatingHours records per timezone (e.g., "Eastern 8am-5pm" and "Central 8am-5pm")
4. Assign each split territory the correct OperatingHours record
5. Import KML polygons that stay within the timezone boundary for each territory
6. For resources that operate in both split territories: add Secondary ServiceTerritoryMember in the adjacent territory

### Cross-Regional Specialist Pool

**When to use:** A small pool of certified specialists serves all regional territories on demand.

**How it works:**
1. Assign each specialist a Primary territory (typically home region or HQ territory)
2. Add Secondary ServiceTerritoryMember records for all other territories they may serve
3. Set the scheduling policy to Soft Boundaries for these resources
4. When a specialist is dispatched across regions, the optimization engine assigns them based on travel feasibility and skill match
5. The specialist appears in the `Book Appointment` slot list for secondary territories when availability allows

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Territory spans timezone line | Split into separate territories per timezone | Prevents incorrect slot times for customers |
| Resource serves multiple territories | Secondary ServiceTerritoryMember + Soft Boundary | Enables cross-territory scheduling |
| Resource must stay in home territory | Hard Boundary | Enforces geographic restriction |
| Territories share resources | Serialize optimization jobs per region | Concurrent jobs conflict over shared resources |
| Customer sees wrong time slots at border | Check territory polygon vs. timezone line | Polygon must not cross timezone boundary |
| International deployment | One territory set per country/timezone, separate OperatingHours | Same timezone rule applies internationally |

---

## Recommended Workflow

1. **Map all timezones in the deployment** — Create a territory-to-timezone mapping table. Flag any proposed territory that spans a timezone boundary.
2. **Split timezone-boundary territories** — Redesign any territory that crosses a timezone line into two territories, one per timezone.
3. **Configure OperatingHours per timezone** — Create distinct OperatingHours records for each timezone in the deployment. Name them clearly (e.g., "Standard Hours — US Eastern").
4. **Design cross-territory resource model** — Identify all resources who serve multiple territories. Create Secondary ServiceTerritoryMember records and confirm Soft Boundary policy settings.
5. **Plan optimization serialization** — List all territory pairs that share resources. Design an optimization schedule that runs these territories sequentially, not concurrently.
6. **Validate appointment booking** — Create test ServiceAppointments in territories near timezone boundaries and verify the `Book Appointment` action returns slots in the correct local time.
7. **Document regional deployment map** — Produce a territory-region-timezone map for ongoing operations reference. Include optimization schedule, shared resource list, and boundary rules.

---

## Review Checklist

- [ ] No territory polygon crosses a timezone line
- [ ] Each territory has an OperatingHours record with the correct timezone
- [ ] Cross-territory resources have both Primary and Secondary ServiceTerritoryMember records
- [ ] Scheduling policy boundary mode set correctly (Soft or Hard)
- [ ] Optimization jobs for territories sharing resources are serialized
- [ ] Appointment booking tested near timezone boundaries with correct local time validation
- [ ] Multi-region deployment map documented

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Territory polygons crossing timezone boundaries produce incorrect appointment slot times** — There is no error. The Book Appointment action silently returns slots in the wrong timezone for customers at the boundary. The only remedy is redesigning the territory.
2. **Concurrent optimization for territories sharing resources causes conflicts** — Two optimization jobs running simultaneously for territories with shared Secondary-type resources will interfere with each other's assignments. Always serialize optimization by time-gapping regional jobs.
3. **Hard Boundary restricts the resource to their primary territory regardless of secondary assignments** — A resource with Secondary assignments in other territories but Hard Boundary set in the scheduling policy will never be scheduled outside their primary territory. Verify boundary mode matches the intent.
4. **Book Appointment derives slot timezone from territory OperatingHours — not customer address** — If OperatingHours timezone is wrong (e.g., Pacific hours applied to an Eastern territory), all slot times will be offset by 3 hours with no UI indication to the booking agent.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Territory-timezone mapping table | List of all territories with their timezone, OperatingHours record, and any timezone-split decisions |
| Optimization serialization schedule | Timed optimization job schedule showing regional sequencing to avoid shared-resource conflicts |
| Cross-territory resource matrix | Resources with multiple territory assignments, boundary type, and scheduling policy settings |

---

## Related Skills

- architect/fsl-optimization-architecture — Optimization mode selection and territory sizing that affects multi-region design
- data/fsl-territory-data-setup — Territory data loading including OperatingHours and ServiceTerritoryMember
