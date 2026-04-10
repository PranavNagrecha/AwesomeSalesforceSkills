---
name: fsl-territory-data-setup
description: "Use this skill when bulk loading Service Territory data: boundary polygons, ServiceTerritoryMember assignments, OperatingHours, TimeSlots, and territory hierarchy setup. Trigger keywords: service territory bulk load, KML polygon import FSL, ServiceTerritoryMember migration, OperatingHours data setup, PolygonUtils Apex. NOT for Enterprise Territory Management (ETM/Account Territories), admin-level territory configuration UI, or scheduling policy setup."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "How do I bulk load service territory boundaries and member assignments for FSL"
  - "Importing KML polygon files for FSL service territory boundaries"
  - "ServiceTerritoryMember insert order and EffectiveStartDate requirements"
  - "PolygonUtils Apex class to resolve latitude longitude to service territory"
  - "Operating hours and time slot bulk setup for FSL territories"
tags:
  - fsl
  - field-service
  - data-migration
  - service-territory
  - fsl-territory-data-setup
  - polygon
  - operating-hours
inputs:
  - "Service territory hierarchy (parent/child territories) from source system or design"
  - "Boundary polygon data in KML format (for geographic territory boundaries)"
  - "Resource-to-territory assignments with effective dates"
  - "Operating hours schedules and shift patterns per territory"
outputs:
  - "Ordered data load sequence for service territory objects"
  - "KML polygon import guidance and PolygonUtils usage"
  - "ServiceTerritoryMember setup with correct TerritoryType and date fields"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# FSL Territory Data Setup

This skill activates when a data migration or org setup project requires bulk loading FSL Service Territory data: territory records, operating hours, time slots, boundary polygons, and ServiceTerritoryMember assignments. Territory data has strict insert-order dependencies and polygon boundaries are stored in managed package objects requiring special import handling.

---

## Before Starting

Gather this context before working on anything in this domain:

- Determine the territory hierarchy depth (parent territories, child territories). Parent territories must exist before child territories are inserted.
- Confirm whether geographic polygon boundaries are in scope. Polygon boundaries are stored in FSMP managed package objects — the primary import mechanism is KML file upload in Setup, not Data Loader.
- Verify all resource records (ServiceResource) exist before loading ServiceTerritoryMember records. ServiceTerritoryMember requires both ServiceTerritory and ServiceResource to exist.
- Confirm TerritoryType for each member: Primary, Secondary, or Relocation. Omitting TerritoryType defaults to Primary, which misclassifies contractors and affects scheduling behavior.
- Check territory limits: maximum 50 resources per territory and 1,000 service appointments per day per territory before optimization performance degrades.

---

## Core Concepts

### Insert Order for Territory Objects

The correct sequence:
1. OperatingHours (no parent dependencies)
2. TimeSlot (child of OperatingHours)
3. ServiceTerritory — parent territories first, then child territories
4. ServiceTerritoryMember (references ServiceTerritory + ServiceResource)

Each step must complete before the next. ServiceTerritory has a lookup to OperatingHours — the OperatingHours record must exist before the territory is created.

### Polygon Boundaries

Service territory polygons define geographic boundaries used for appointment booking's "territory lookup by location." Polygon data is stored in FSMP (Field Service managed package) objects, not standard Salesforce objects. The supported bulk import mechanism is KML file upload in Setup > Field Service Settings > Service Territories > Import Polygon.

For Apex-based polygon resolution (finding which territory a lat/lng falls in), use the `FSL.PolygonUtils` class:

```apex
ServiceTerritory territory = FSL.PolygonUtils.getServiceTerritoryForLocation(lat, lng, Date.today());
```

Bulk polygon creation via Apex uses queueable chaining because polygon processing is time-consuming and subject to governor limits per territory.

### ServiceTerritoryMember — Key Fields

| Field | Notes |
|---|---|
| TerritoryType | Primary, Secondary, or Relocation. Omitting defaults to Primary |
| EffectiveStartDate | Required. When the member starts serving this territory |
| EffectiveEndDate | Optional. For relocation members moving between territories |
| ServiceTerritoryId | Parent territory |
| ServiceResourceId | The resource being assigned |

**Relocation pattern:** When a resource permanently moves from Territory A to Territory B, create a ServiceTerritoryMember for Territory B with EffectiveStartDate = transfer date, and set EffectiveEndDate on the Territory A member. Do not delete the old STM record — it is required for historical appointment reporting.

---

## Common Patterns

### Bulk Territory Hierarchy Load

**When to use:** Setting up a new FSL implementation with dozens or hundreds of territories in a regional hierarchy.

**How it works:**
1. Load OperatingHours records with External IDs (one per schedule type — e.g., Monday-Friday 8am-5pm)
2. Load TimeSlot records referencing OperatingHours External IDs
3. Load parent ServiceTerritory records (IsActive = true, OperatingHoursId mapped)
4. Load child ServiceTerritory records with ParentTerritoryId mapped to parent External IDs
5. Load ServiceTerritoryMember records with TerritoryType, EffectiveStartDate, ServiceResourceId

**Why not flat structure:** ServiceTerritory hierarchy is used for scheduling scope — optimization runs per territory, and child territories inherit scheduling scope boundaries from parents. Loading children before parents creates orphaned records.

### KML Polygon Import for Territory Boundaries

**When to use:** Geographic territory boundaries are needed for the Book Appointment action's location-based territory lookup.

**How it works:**
1. Prepare KML files — one per service territory. Each KML file contains one Polygon element.
2. In Setup > Field Service Settings > Service Territories, select the territory and click "Import Polygon"
3. Upload the KML file. The polygon is stored in the FSMP managed package FSL__Polygon__c object.
4. Verify: use PolygonUtils.getServiceTerritoryForLocation() with a known lat/lng to confirm territory lookup works.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Bulk territory load (no polygons) | Data Loader upsert with External IDs in hierarchy order | Fastest path, re-runnable |
| Geographic polygon boundaries needed | KML import via Setup per territory | Only supported bulk polygon import mechanism |
| Large polygon creation via Apex | Queueable chaining, one territory per job | Governor limits on polygon processing |
| Resource moving permanently to new territory | Create new STM with EffectiveStartDate, end-date old STM | Preserves historical data, correct for scheduling |
| Contractor in multiple territories | Add as Secondary type member in each territory | Primary = home territory; Secondary = overflow territory |

---

## Recommended Workflow

1. **Define the territory hierarchy** — Identify parent/child relationships and territory types. Document operating hours schedules needed (one OperatingHours record per unique schedule pattern).
2. **Load OperatingHours and TimeSlots first** — These have no parent dependencies. Add External IDs for safe upsert.
3. **Load parent ServiceTerritory records** — Map OperatingHoursId via External ID. Verify all parent records before loading children.
4. **Load child ServiceTerritory records** — Map ParentTerritoryId via parent's External ID.
5. **Import polygon boundaries** (if in scope) — Use the KML import in Setup per territory. Verify with PolygonUtils after import.
6. **Load ServiceTerritoryMember records** — Set TerritoryType explicitly, EffectiveStartDate required, map ServiceResourceId. Confirm 50-resource-per-territory limit not exceeded.
7. **Validate with test scheduling** — Create a test ServiceAppointment and use the Book Appointment action to confirm territory lookup and slot retrieval work correctly.

---

## Review Checklist

- [ ] OperatingHours and TimeSlots loaded before ServiceTerritory
- [ ] Parent ServiceTerritory records loaded before child records
- [ ] TerritoryType explicitly set on all ServiceTerritoryMember records
- [ ] EffectiveStartDate set on all ServiceTerritoryMember records
- [ ] Territory member count under 50 per territory
- [ ] Polygon boundaries imported and verified with PolygonUtils (if in scope)
- [ ] Test scheduling run confirms territory lookup and slot availability

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Omitting TerritoryType defaults to Primary and misclassifies contractors** — Primary designation affects which resource is the "home" resource for a territory and scheduling preference. Contractors sharing a territory as Secondary need explicit TerritoryType = Secondary.
2. **Polygon boundaries are in the FSL managed package, not standard objects** — You cannot Data Loader-import polygons directly. KML import via Setup is the only supported bulk mechanism.
3. **Relocation STM records require EffectiveStartDate/EndDate — not deletion** — Deleting the old STM breaks historical appointment reporting. Always set EffectiveEndDate on the departing STM and create a new one for the destination territory.
4. **Exceeding 50 resources per territory degrades optimization performance** — This is a soft limit but exceeding it causes Global Optimization jobs to consistently run over the 2-hour timeout. Design territory structure to respect this limit.
5. **Territory polygons that cross timezone boundaries silently break appointment booking** — If a polygon spans a timezone line, `Book Appointment` derives slots using the territory's OperatingHours timezone but the polygon boundary check uses geography — creating booking windows that don't correspond to local time. Keep polygons within single timezone boundaries.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Territory data load sequence | Ordered loading plan with object dependencies and field mappings |
| ServiceTerritoryMember load CSV | Template CSV with correct columns including TerritoryType and EffectiveStartDate |

---

## Related Skills

- data/fsl-resource-and-skill-data — ServiceResource records that ServiceTerritoryMember references
- architect/fsl-optimization-architecture — Territory sizing constraints and optimization engine considerations
- architect/fsl-multi-region-architecture — Multi-region and multi-timezone territory design
