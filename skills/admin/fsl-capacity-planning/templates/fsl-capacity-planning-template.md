# FSL Capacity Planning — Work Template

Use this template when configuring or auditing FSL capacity constraints.

## Scope

**Skill:** `fsl-capacity-planning`

**Request summary:** (describe the capacity planning task — e.g., "cap shared equipment to 8 hours/day," "limit Complex Install appointments to 5/week per territory," "build utilization report")

---

## Context Gathered

Answer these before writing any records:

- **Capacity mechanism needed:** [ ] Resource-level (ServiceResourceCapacity) [ ] Territory-level (WorkCapacityLimit) [ ] Both
- **IsCapacityBased flag status:** Are the target ServiceResource records marked `IsCapacityBased = true`? (Required for ServiceResourceCapacity to take effect)
- **Scheduling horizon:** From ________ to ________ (dates that capacity records must cover without gaps)
- **CapacityUnit:** [ ] Hours [ ] Appointments (for ServiceResourceCapacity)
- **CapacityWindow:** [ ] Daily [ ] Weekly [ ] Monthly (for WorkCapacityLimit)
- **Seasonal adjustments needed:** [ ] Yes — date range: ________ [ ] No
- **Reporting strategy in place:** [ ] Custom report type [ ] CRM Analytics [ ] None (needs to be built)

---

## Resource Capacity Configuration Plan

(Complete for each resource requiring ServiceResourceCapacity records)

| Resource Name | ServiceResource Id | IsCapacityBased | Period Start | Period End | Capacity | CapacityUnit | TimeSlotType |
|---|---|---|---|---|---|---|---|
| (fill in) | (fill in) | true | YYYY-MM-DD | YYYY-MM-DD | (number) | Hours / Appointments | Normal / Extended |
| (fill in) | | true | | | | | |

**Gap check:** After inserting records, run the adjacency SOQL and confirm no date gaps exist.

---

## Territory Capacity Limit Configuration Plan

(Complete for each territory/work type requiring WorkCapacityLimit records)

| Territory Name | Territory Id | Work Type | Work Type Id | CapacityWindow | CapacityLimit | Start Date | End Date |
|---|---|---|---|---|---|---|---|
| (fill in) | (fill in) | (fill in) | (fill in) | Weekly | (number) | YYYY-MM-DD | YYYY-MM-DD |
| | | | | | | | |

**Dispatcher communication:** Confirm dispatchers are aware that limit-reached rejections are silent. Link to monitoring report: ________

---

## Seasonal / Event-Driven Adjustments

| Period | Adjustment Type | Records to Update | New Capacity / Limit | Start | End | Method |
|---|---|---|---|---|---|---|
| (e.g., Holiday 2025) | ServiceResourceCapacity | (resource name / Id) | (reduced value) | YYYY-MM-DD | YYYY-MM-DD | Data Loader / Apex |
| (continuation) | ServiceResourceCapacity | (same resource) | (restored value) | YYYY-MM-DD | YYYY-MM-DD | Data Loader / Apex |

---

## Validation Steps

```soql
-- 1. Confirm IsCapacityBased is set on all capacity-based resources
SELECT Id, Name, IsCapacityBased FROM ServiceResource
WHERE Id IN (SELECT ServiceResourceId FROM ServiceResourceCapacity)
AND IsCapacityBased = false
-- Expect: 0 rows

-- 2. Check for date gaps in ServiceResourceCapacity records
SELECT ServiceResourceId, StartDate, EndDate
FROM ServiceResourceCapacity
WHERE ServiceResource.IsCapacityBased = true
ORDER BY ServiceResourceId, StartDate
-- Review manually for consecutive coverage

-- 3. Check for zero-capacity ServiceResourceCapacity records
SELECT Id, ServiceResourceId, Capacity, CapacityUnit, StartDate, EndDate
FROM ServiceResourceCapacity
WHERE Capacity <= 0
-- Expect: 0 rows

-- 4. Check for zero-limit WorkCapacityLimit records
SELECT Id, ServiceTerritoryId, WorkTypeId, CapacityLimit, CapacityWindow, StartDate, EndDate
FROM WorkCapacityLimit
WHERE CapacityLimit <= 0
-- Expect: 0 rows

-- 5. Check for expired WorkCapacityLimit records (cleanup)
SELECT Id, ServiceTerritoryId, WorkTypeId, EndDate
FROM WorkCapacityLimit
WHERE EndDate < TODAY
-- Review: remove or archive if no longer needed
```

---

## Review Checklist

Copy from SKILL.md and tick as completed:

- [ ] All capacity-based resources have `ServiceResource.IsCapacityBased = true`
- [ ] `ServiceResourceCapacity` records cover the full scheduling horizon with no date gaps
- [ ] Each `ServiceResourceCapacity` record has a valid `CapacityUnit` and a non-zero `Capacity`
- [ ] `WorkCapacityLimit` records exist for each territory/work type pair that requires demand throttling
- [ ] `WorkCapacityLimit` records have non-zero `CapacityLimit` values and cover the active scheduling window
- [ ] Dispatchers are informed that `WorkCapacityLimit` rejections are silent — a monitoring report or dashboard is in place
- [ ] Seasonal or event-driven capacity changes have bounded date records and continuation records after the event ends
- [ ] A utilization reporting strategy is documented and accessible to operations
- [ ] No standard time-slot-based resources (non-capacity-based) have `ServiceResourceCapacity` records that could create false expectations

---

## Notes

(Record any deviations from the standard pattern, org-specific constraints, or decisions made during this engagement.)
