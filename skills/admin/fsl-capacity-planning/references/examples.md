# Examples — FSL Capacity Planning

## Example 1: Shared Diagnostic Equipment Capped at 8 Hours per Day

**Context:** A utilities company operates a fleet of portable diagnostic analyzers. Each analyzer is registered as a `ServiceResource` with `IsCapacityBased = true` because it can support multiple appointments in a day up to its 8-hour physical capacity, not one dedicated shift. Without capacity records, the scheduler either never books the analyzer (no capacity = unschedulable) or — if `IsCapacityBased` was mistakenly left false — books it without limit, creating physical overbooking.

**Problem:** After initial setup, appointments for the diagnostic work type are never assigned to the analyzer resources. Dispatchers see the analyzers listed in the console but the optimizer never selects them. No error is shown.

**Solution:**

The `IsCapacityBased` field was not set on the `ServiceResource` records. The `ServiceResourceCapacity` records were inserted, but because `IsCapacityBased = false`, the scheduler ignored them and also did not use the resource for standard shift-based scheduling. The fix:

```soql
-- 1. Verify the flag
SELECT Id, Name, IsCapacityBased FROM ServiceResource
WHERE Name LIKE '%Analyzer%'

-- 2. After confirming IsCapacityBased = false, update via Data Loader or Apex:
-- ServiceResource.IsCapacityBased = true (update)

-- 3. Confirm existing ServiceResourceCapacity records are date-contiguous
SELECT Id, ServiceResourceId, StartDate, EndDate, Capacity, CapacityUnit, TimeSlotType
FROM ServiceResourceCapacity
WHERE ServiceResourceId IN (
    SELECT Id FROM ServiceResource WHERE Name LIKE '%Analyzer%'
)
ORDER BY ServiceResourceId, StartDate
```

After setting `IsCapacityBased = true` on each analyzer resource, the existing `ServiceResourceCapacity` records with `Capacity = 8` and `CapacityUnit = Hours` became active. The scheduler began assigning diagnostic appointments up to 8 total hours per day per analyzer.

**Why it works:** `ServiceResourceCapacity` records are only evaluated by the scheduler when the parent `ServiceResource` has `IsCapacityBased = true`. The flag gates the entire capacity mechanism. Without it, capacity records are inert data with no scheduling effect and no error.

---

## Example 2: Silently Rejected Installs Due to WorkCapacityLimit

**Context:** A telecom operator uses FSL to schedule complex fiber-optic installation appointments. The territory manager configured a `WorkCapacityLimit` of 5 complex installs per week for a given territory to match their parts supply. Mid-week, dispatchers noticed that new install appointments were not scheduling, but saw no error in the Dispatcher Console or optimization log.

**Problem:** Three complex install appointments were created on Thursday after the weekly limit of 5 was already reached Monday through Wednesday. The scheduling engine silently rejected them. Dispatchers escalated to admins assuming the scheduling optimizer had a bug.

**Solution:**

```soql
-- Identify the WorkCapacityLimit record for the territory and work type
SELECT Id, ServiceTerritoryId, WorkTypeId, CapacityWindow, CapacityLimit, StartDate, EndDate
FROM WorkCapacityLimit
WHERE ServiceTerritory.Name = 'Northwest Metro'
  AND WorkType.Name = 'Complex Fiber Install'

-- Count this week's scheduled appointments of that type in the territory
SELECT COUNT(Id)
FROM ServiceAppointment
WHERE ServiceTerritoryId = '0HhXXXXXXXXXXXXX'   -- replace with actual Id
  AND WorkTypeId = '08qXXXXXXXXXXXXX'            -- replace with actual Id
  AND SchedStartTime >= THIS_WEEK
  AND Status NOT IN ('Canceled')
```

The query confirmed 5 appointments were already scheduled this week, matching the `CapacityLimit`. The rejected appointments were rescheduled to the following week after the window reset. The operations team added a weekly report showing appointment counts per territory/work type vs. the `WorkCapacityLimit` value so dispatchers could see approaching limits proactively.

**Why it works:** `WorkCapacityLimit` enforcement is intentional and correct — it prevents overbooking a territory. The gap is the silent rejection behavior. Building a monitoring report that tracks appointment count vs. `CapacityLimit` per window turns the silent platform behavior into a visible operational signal for dispatch teams.

---

## Example 3: Seasonal Capacity Reduction for Holiday Period

**Context:** A field service org runs reduced capacity for 10 days over the winter holiday period. Normally, `WorkCapacityLimit` allows 20 standard maintenance visits per week per territory. During the holiday window, only 8 per week should be accepted. The admin needed to configure this in advance without disrupting normal scheduling before or after the holiday window.

**Problem:** The admin could not find a "copy and adjust" UI in FSL for `WorkCapacityLimit`. Attempting to edit the existing record to reduce the limit would have changed it for all future periods, not just the holiday window.

**Solution:**

```soql
-- Step 1: Query existing records to get the current limit IDs and values
SELECT Id, ServiceTerritoryId, WorkTypeId, CapacityWindow, CapacityLimit, StartDate, EndDate
FROM WorkCapacityLimit
WHERE StartDate <= 2025-12-20 AND EndDate >= 2026-01-04

-- Step 2 (via Data Loader or Apex):
-- a) Update existing record: EndDate = 2025-12-19 (pre-holiday cutoff)
-- b) Insert new record: StartDate = 2025-12-20, EndDate = 2026-01-03, CapacityLimit = 8
-- c) Insert continuation record: StartDate = 2026-01-04, EndDate = [original EndDate], CapacityLimit = 20
```

After the adjustment, the scheduler accepted up to 20 maintenance visits per week before and after the holiday window, and only 8 per week during the holiday period. No date gaps were left between the three records, so scheduling was uninterrupted.

**Why it works:** `WorkCapacityLimit` records are date-bounded. The correct approach for seasonal adjustments is to split one long-range record into three: pre-event, event, post-event. This creates the desired time-bound behavior without manual intervention during the event and without leaving the org in a reduced-capacity state afterward.

---

## Anti-Pattern: Deactivating Resources to Reduce Capacity

**What practitioners do:** When a territory is at risk of overbooking during a busy period, some admins set `ServiceResource.IsActive = false` on lower-priority technicians to reduce the scheduling candidate pool.

**What goes wrong:** Deactivating a resource removes it from all scheduling consideration — not just capacity-constrained scheduling. Any existing appointments linked to that resource lose their assigned resource. The resource is also removed from territory member lookups and skill assignment searches. When the admin reactivates the resource after the busy period, they must re-verify all downstream assignments.

**Correct approach:** Use `WorkCapacityLimit` to throttle the territory's appointment intake for the relevant work type during the busy period. For resource-level reduction, create a `ServiceResourceCapacity` record covering the busy window with a lower `Capacity` value. Neither approach removes the resource from the system or disrupts existing appointments.
