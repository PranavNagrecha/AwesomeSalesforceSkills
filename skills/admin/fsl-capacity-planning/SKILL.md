---
name: fsl-capacity-planning
description: "Use this skill to configure and manage Field Service Lightning workforce capacity — covering ServiceResourceCapacity for individual resource caps, WorkCapacityLimit for territory-level demand throttling, and reporting strategies for capacity vs. utilization analysis. NOT for Omni-Channel capacity, NOT for FSL scheduling policy rule configuration, and NOT for FSL resource skill or preference setup (see fsl-resource-management)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Performance
triggers:
  - "field service appointments are being silently rejected and dispatchers see no error explaining why"
  - "territory is over-booked or under-utilized and we cannot see a capacity vs scheduled hours report"
  - "how do I cap the number of appointments or hours a field service resource can take per day or week"
  - "configure work capacity limits by work type and service territory in Field Service Lightning"
  - "resource shows as capacity-based but appointments are not being restricted by any limit"
  - "bulk update seasonal capacity limits for field service territories"
  - "what is the difference between ServiceResourceCapacity and WorkCapacityLimit in FSL"
tags:
  - field-service
  - fsl
  - capacity-planning
  - workforce-management
  - ServiceResourceCapacity
  - WorkCapacityLimit
  - scheduling
  - territory
inputs:
  - "List of service resources that need per-resource capacity caps (hours or appointment counts per period)"
  - "Whether capacity should be modeled at resource level, territory level, or both"
  - "Work types and their typical duration, used to configure WorkCapacityLimit throttles"
  - "Scheduling horizon (weeks or months) for which capacity records must be created in advance"
  - "Whether the org uses CRM Analytics or custom report types for capacity vs. utilization reporting"
outputs:
  - "ServiceResourceCapacity records covering the scheduling horizon for capacity-based resources"
  - "WorkCapacityLimit records per territory and work type for demand-side throttling"
  - "Decision guidance on which capacity mechanism (resource-level vs. territory-level) to apply per scenario"
  - "Reporting strategy for capacity vs. actual service appointment duration"
  - "Validation checklist confirming no silent rejections, no coverage gaps, and no orphaned capacity records"
dependencies:
  - fsl-resource-management
  - fsl-service-territory-setup
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# FSL Capacity Planning

This skill activates when a practitioner needs to configure, audit, or report on Field Service Lightning workforce capacity — including per-resource capacity caps via `ServiceResourceCapacity`, territory-level demand throttling via `WorkCapacityLimit`, and strategies for measuring capacity utilization. It addresses both mechanisms the FSL scheduling engine uses to constrain appointment volume and explains how the two mechanisms interact.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm that Field Service is enabled (Setup > Field Service Settings) and that the running user has access to `ServiceResourceCapacity`, `WorkCapacityLimit`, and `ServiceResource` objects.
- Determine which capacity mechanism applies: resource-level capacity (`ServiceResourceCapacity`) controls how many hours or appointments a single resource can take in a period; territory-level capacity (`WorkCapacityLimit`) controls how many appointments of a given work type a territory accepts in a time window. These are independent and additive — an appointment must satisfy both constraints before it can be scheduled.
- Identify whether resources are marked `IsCapacityBased = true`. `ServiceResourceCapacity` records only take effect on resources where `IsCapacityBased = true` on the `ServiceResource` record. Standard time-slot-based technicians ignore these records entirely.
- Establish the scheduling horizon. `ServiceResourceCapacity` and `WorkCapacityLimit` records cover explicit date ranges. Gaps in coverage silently prevent scheduling without any error shown to dispatchers or optimization logs.
- Note that there are no seasonal capacity templates in FSL. Bulk updates to `WorkCapacityLimit` records (e.g., holiday reductions, peak-season increases) must be performed via Data Loader or Apex — there is no native UI for mass date-range updates.

---

## Core Concepts

### Two Capacity Mechanisms: Resource-Level vs. Territory-Level

FSL provides two distinct capacity objects that serve different purposes and operate independently:

**ServiceResourceCapacity** (API v38.0+) — per-resource cap on hours or appointments within a date range. Applies only when `ServiceResource.IsCapacityBased = true`. The scheduler checks this cap before assigning an appointment to a capacity-based resource. If the resource is at or over the cap for the period, the scheduler excludes it from candidates.

**WorkCapacityLimit** — territory-level demand throttle per work type per time window. Limits how many appointments of a given `WorkType` are accepted in a defined `CapacityWindow` (Daily, Weekly, or Monthly) within a `ServiceTerritory`. When the limit is reached, new appointments of that work type in that territory are rejected silently — no error is displayed to the dispatcher.

Both mechanisms can be active simultaneously. An appointment must pass the `WorkCapacityLimit` check at the territory level before the `ServiceResourceCapacity` check at the resource level is evaluated. Configuring only one without being aware of the other is a common misconfiguration that causes unexpected rejections.

### ServiceResourceCapacity Object

Key fields on `ServiceResourceCapacity` (Object API v38.0+):

| Field | Type | Notes |
|---|---|---|
| `ServiceResourceId` | Lookup | Must reference a resource where `IsCapacityBased = true` |
| `StartDate` | Date | Start of the period this record covers |
| `EndDate` | Date | End of the period (inclusive) |
| `TimeSlotType` | Picklist | `Normal` (standard business hours) or `Extended` (after-hours) |
| `Capacity` | Number | Maximum units available within the period |
| `CapacityUnit` | Picklist | `Hours` or `Appointments` — defines what `Capacity` measures |

The scheduler sums the duration (for `Hours` unit) or count (for `Appointments` unit) of all service appointments already linked to the resource within the period. If that sum equals or exceeds `Capacity`, the resource is excluded from scheduling candidates. Gaps between `EndDate` of one record and `StartDate` of the next create unschedulable windows with no warning.

### WorkCapacityLimit Object

`WorkCapacityLimit` records express territory-level demand throttles per work type. Key fields:

| Field | Type | Notes |
|---|---|---|
| `ServiceTerritoryId` | Lookup | The territory this limit applies to |
| `WorkTypeId` | Lookup | The work type being throttled |
| `CapacityWindow` | Picklist | `Daily`, `Weekly`, or `Monthly` |
| `CapacityLimit` | Number | Maximum appointments within the window |
| `StartDate` / `EndDate` | Date | Date range this limit is active |

When the number of scheduled appointments of the specified work type in the territory reaches `CapacityLimit` within the current window, additional booking attempts are rejected. Importantly, this rejection is **silent**: no error, no notification, no log entry visible to a dispatcher. The appointment simply does not schedule.

### Reporting Gap: No Native Capacity vs. Utilization Aggregation

There is no standard FSL report type that natively aggregates `ServiceResourceCapacity.Capacity` against the actual duration of scheduled `ServiceAppointment` records. To measure capacity utilization (e.g., "Resource X used 6 of 8 available hours this week"), one of two approaches is required:

1. **Custom Report Type** — Create a custom report type joining `ServiceResource` → `ServiceAppointment` and manually compute utilization by comparing appointment durations against the resource's capacity records (queried separately or via a formula field).
2. **CRM Analytics (Tableau CRM)** — Use the FSL Analytics app or a custom dataset recipe to join `ServiceResourceCapacity` and `ServiceAppointment` data and produce utilization dashboards. This is the recommended approach for orgs with more than 50 resources or complex territory structures.

---

## Common Patterns

### Pattern: Resource-Level Capacity Cap for Shared or Pooled Assets

**When to use:** A resource (shared equipment, a pool vehicle, or a contractor billed per appointment) must be capped at a fixed number of hours or appointment slots per day or week.

**How it works:**
1. Verify `ServiceResource.IsCapacityBased = true` for the target resource. If not, update the field before proceeding — `ServiceResourceCapacity` records inserted against a non-capacity-based resource have no scheduling effect.
2. Create `ServiceResourceCapacity` records to cover the full scheduling horizon without gaps. For a resource capped at 8 hours/day, create monthly records or a single long-range record with `Capacity = 8` and `CapacityUnit = Hours`.
3. Use `TimeSlotType = Normal` for standard business hours. If the resource can also be booked in extended hours, create a separate record with `TimeSlotType = Extended`.
4. Monitor approaching capacity by querying: `SELECT ServiceResourceId, Capacity, CapacityUnit, StartDate, EndDate FROM ServiceResourceCapacity WHERE EndDate >= TODAY`.

**Why not the alternative:** Using standard time-slot availability for shared assets means the scheduler treats the asset as if it has one dedicated shift — it will not correctly prevent overbooking across multiple simultaneous appointments consuming the same physical resource.

### Pattern: Territory-Level Demand Throttle by Work Type

**When to use:** A service territory must limit the number of a specific work type (e.g., "Complex Install") it accepts per week because of technician availability, parts supply constraints, or SLA management.

**How it works:**
1. Identify the `ServiceTerritory` and `WorkType` to be throttled.
2. Create a `WorkCapacityLimit` record:
   - `ServiceTerritoryId` = the territory's Id
   - `WorkTypeId` = the relevant work type Id
   - `CapacityWindow` = `Weekly` (or `Daily` / `Monthly` as appropriate)
   - `CapacityLimit` = maximum acceptable appointment count per window
   - `StartDate` / `EndDate` = the date range for this limit
3. Test by attempting to book more appointments than the limit. Confirm that once the limit is reached, additional bookings are rejected (they will not appear as scheduled without error in the dispatcher view).
4. Communicate the limit behavior to dispatchers. Because rejection is silent, dispatchers must actively monitor appointment counts per territory and work type via a custom report or dashboard.

**Why not the alternative:** Relying on dispatcher judgment to throttle territory demand is not scalable and breaks under dispatch team turnover. Encoding the limit in `WorkCapacityLimit` enforces it automatically at the scheduling engine level.

### Pattern: Seasonal or Event-Driven Capacity Adjustment

**When to use:** Capacity needs to change for a known future period (holiday reductions, peak-season expansions, a planned technician leave block).

**How it works:**
1. Identify which records need updating: `ServiceResourceCapacity` for resource-level adjustments, `WorkCapacityLimit` for territory-level adjustments.
2. Because no bulk-update UI exists, use one of:
   - **Data Loader** — export the current records, modify `Capacity`, `StartDate`, and `EndDate` in the CSV, then use upsert to apply changes.
   - **Apex batch job** — query the affected records and update the `Capacity` field programmatically.
3. Ensure the new records cover the adjusted period end-to-end. Insert a reduced-capacity record for the holiday window, then resume with the standard record after the window ends. Do not leave a date gap between records.
4. After the seasonal period ends, revert or create continuation records to restore standard capacity. Stale low-capacity records left in place silently prevent normal scheduling after the season ends.

**Why not the alternative:** Deactivating resources during low-capacity periods is not equivalent — it removes the resource from all scheduling, not just capacity-constrained scheduling. The correct approach is a reduced-capacity record, not resource deactivation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Cap a single resource's daily appointment count | `ServiceResourceCapacity` with `CapacityUnit = Appointments` | Resource-level cap; requires `IsCapacityBased = true` |
| Cap a single resource's available hours per week | `ServiceResourceCapacity` with `CapacityUnit = Hours` | Hour-based cap enforced by scheduler against actual SA durations |
| Limit how many Complex Installs a territory accepts per week | `WorkCapacityLimit` with `CapacityWindow = Weekly` | Territory-level demand throttle; works independently of resource-level caps |
| Reduce capacity for a 2-week holiday period | New `ServiceResourceCapacity` or `WorkCapacityLimit` record with lower `Capacity` for that date range | No seasonal template UI; must create date-bounded records manually |
| Measure resource utilization vs. capacity | Custom report type or CRM Analytics dataset joining `ServiceResourceCapacity` and `ServiceAppointment` | No native aggregated report type exists |
| Resource appears capacity-based but is not restricted | Verify `ServiceResource.IsCapacityBased = true`; confirm no date gaps in `ServiceResourceCapacity` records | `IsCapacityBased` must be set before capacity records have effect |
| Dispatchers see no error but appointments stop scheduling | Check `WorkCapacityLimit` — limit reached causes silent rejection | Silent rejection is `WorkCapacityLimit`'s default behavior; no UI notification |
| Standard technician should have shift-based availability | Do NOT use `ServiceResourceCapacity`; use operating hours and shifts | Capacity records only apply to `IsCapacityBased = true` resources |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Audit prerequisites** — Confirm Field Service is enabled and the running user can read and write `ServiceResource`, `ServiceResourceCapacity`, and `WorkCapacityLimit`. Query `SELECT Id, Name, IsCapacityBased FROM ServiceResource WHERE IsActive = true` to identify which resources are capacity-based and which are shift-based. This determines which capacity mechanism applies.

2. **Configure resource-level capacity** — For each resource where `IsCapacityBased = true`, create `ServiceResourceCapacity` records to cover the full scheduling horizon without gaps. Set `Capacity` and `CapacityUnit` to match the business rule (hours or appointment count). Create separate records for `Normal` and `Extended` `TimeSlotType` if both apply. Verify no date gaps exist between records by sorting on `StartDate`.

3. **Configure territory-level demand throttles** — For each territory and work type combination that requires demand management, create `WorkCapacityLimit` records with the appropriate `CapacityWindow` and `CapacityLimit`. Confirm `StartDate` and `EndDate` cover the intended scheduling window. Document the limit and communicate it to dispatchers — rejection is silent.

4. **Handle seasonal adjustments** — If near-future capacity changes are required (holiday reductions, peak expansions), create bounded `ServiceResourceCapacity` or `WorkCapacityLimit` records with the adjusted values. Do not leave date gaps. After the seasonal period, create continuation records to restore standard capacity.

5. **Build a utilization reporting strategy** — If the org does not already have a capacity utilization report, create a custom report type joining `ServiceResource` and `ServiceAppointment`, or configure a CRM Analytics recipe. Document the reporting approach for operations teams who will monitor capacity health.

6. **Validate end-to-end** — Query `SELECT Id, StartDate, EndDate, Capacity, CapacityUnit FROM ServiceResourceCapacity WHERE ServiceResource.IsCapacityBased = true ORDER BY ServiceResourceId, StartDate` and scan for gaps. Query `WorkCapacityLimit` records and confirm `CapacityLimit` values are non-zero and dates cover the active scheduling window. Create a test service appointment for each throttled work type and territory to confirm limits are enforced as expected.

7. **Review checklist and handoff** — Complete the review checklist below. If dispatchers report silent appointment rejections, re-examine `WorkCapacityLimit` records first, then check for date gaps in `ServiceResourceCapacity`. Document the capacity model for operations teams.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All capacity-based resources have `ServiceResource.IsCapacityBased = true`
- [ ] `ServiceResourceCapacity` records cover the full scheduling horizon with no date gaps
- [ ] Each `ServiceResourceCapacity` record has a valid `CapacityUnit` (`Hours` or `Appointments`) and a non-zero `Capacity`
- [ ] `WorkCapacityLimit` records exist for each territory/work type pair that requires demand throttling
- [ ] `WorkCapacityLimit` records have non-zero `CapacityLimit` values and cover the active scheduling window
- [ ] Dispatchers are informed that `WorkCapacityLimit` rejections are silent — a monitoring report or dashboard is in place
- [ ] Seasonal or event-driven capacity changes have bounded date records and continuation records after the event ends
- [ ] A utilization reporting strategy (custom report type or CRM Analytics) is documented and accessible to operations
- [ ] No standard time-slot-based resources (non-capacity-based) have `ServiceResourceCapacity` records that could create false expectations

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **WorkCapacityLimit rejections are completely silent** — When a territory-level capacity limit is reached, the scheduling engine stops accepting appointments for that work type in that territory without displaying any error to the dispatcher or writing to any log visible in standard FSL UIs. Dispatchers see the appointment as unscheduled but receive no explanation. The only detection method is a SOQL query against `WorkCapacityLimit` to compare the limit against the actual appointment count for the period.

2. **ServiceResourceCapacity has no effect unless IsCapacityBased = true** — Inserting `ServiceResourceCapacity` records against a `ServiceResource` where `IsCapacityBased = false` produces no scheduling restriction and no error. The scheduler silently ignores those records. This is the most common misconfiguration when setting up capacity-based scheduling for the first time: the capacity records exist, but the resource flag was never set.

3. **No native report type aggregates capacity vs. actual utilization** — There is no standard FSL report type that joins `ServiceResourceCapacity.Capacity` to `ServiceAppointment` durations. Orgs that need capacity utilization metrics must build a custom report type or a CRM Analytics dataset recipe. Teams that assume a standard report exists often discover this only when asked to produce an operations dashboard.

4. **Date gaps in capacity records silently block scheduling** — If `ServiceResourceCapacity` record A ends on March 31 and the next record B starts on April 2, no appointments can be scheduled on April 1 for that resource, and no warning is issued. The scheduler finds no active capacity record and excludes the resource from candidates without any indication to the dispatcher. Gap auditing via SOQL `ORDER BY StartDate` is required at setup and after any seasonal update.

5. **No seasonal capacity template or bulk UI exists** — There is no native FSL UI to bulk-adjust `WorkCapacityLimit` or `ServiceResourceCapacity` values for a future time range. Peak-season or holiday adjustments must be performed via Data Loader, Apex batch, or the API. Teams that expect a "copy and reduce" UI workflow discover this constraint only when the need arises under time pressure.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `ServiceResourceCapacity` records | Per-resource capacity caps (hours or appointment counts) covering the scheduling horizon without date gaps |
| `WorkCapacityLimit` records | Territory + work type demand throttles with defined capacity windows |
| Utilization reporting strategy | Custom report type definition or CRM Analytics recipe spec for capacity vs. actual appointment hours |
| Seasonal adjustment runbook | Data Loader or Apex batch procedure for updating capacity records at period boundaries |
| Capacity audit query | SOQL to detect date gaps and zero-capacity records for ongoing operational monitoring |

---

## Related Skills

- `fsl-resource-management` — ServiceResource setup including `IsCapacityBased` flag and `ServiceResourceCapacity` fundamentals; must be completed before capacity planning records can be inserted
- `fsl-service-territory-setup` — ServiceTerritory and operating hours configuration; `WorkCapacityLimit` requires valid territory records
- `fsl-scheduling-policies` — Work rules and optimization settings; scheduling policies interact with capacity limits during automated optimization runs

## Official Sources Used

- Capacity Planning Overview — https://help.salesforce.com/s/articleView?id=sf.fs_capacity_planning.htm
- Define Capacity-Based Resources — https://help.salesforce.com/s/articleView?id=sf.fs_capacity_based_resources.htm
- Manage Work Capacity — https://help.salesforce.com/s/articleView?id=sf.fs_work_capacity.htm
- ServiceResourceCapacity Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_serviceresourcecapacity.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
