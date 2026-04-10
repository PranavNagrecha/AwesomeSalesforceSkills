# Gotchas — FSL Capacity Planning

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: WorkCapacityLimit Rejects Appointments Silently — No Error, No Log Entry

**What happens:** When the number of scheduled appointments for a given work type in a territory reaches the `WorkCapacityLimit.CapacityLimit` for the current window, all subsequent booking attempts for that work type in that territory are silently rejected. The scheduling engine returns no error to the dispatcher, writes no entry to the optimization log visible in standard FSL UIs, and shows no warning on the appointment record. The appointment simply does not schedule.

**When it occurs:** Any time a `WorkCapacityLimit` record is active and the per-window appointment count equals or exceeds `CapacityLimit`. This is most likely to surface mid-week or mid-day for orgs using `Daily` or `Weekly` windows during peak demand periods. It also occurs when `CapacityLimit` is inadvertently set too low (e.g., left at 1 from a test record that was never cleaned up).

**How to avoid:** Build a monitoring report or dashboard that shows the count of scheduled appointments per territory and work type against the active `WorkCapacityLimit` values. Query:
```soql
SELECT WorkTypeId, ServiceTerritoryId, CapacityWindow, CapacityLimit, StartDate, EndDate
FROM WorkCapacityLimit
WHERE StartDate <= TODAY AND EndDate >= TODAY
```
Compare against appointment counts per window. Communicate to dispatchers that when appointments stop scheduling for a specific work type, the first thing to check is whether the territory's limit has been reached.

---

## Gotcha 2: ServiceResourceCapacity Records Have No Effect If IsCapacityBased Is False

**What happens:** `ServiceResourceCapacity` records can be inserted against any `ServiceResource` without error, regardless of whether `ServiceResource.IsCapacityBased` is `true` or `false`. However, the scheduler only evaluates `ServiceResourceCapacity` records for resources where `IsCapacityBased = true`. For all other resources, these records are silently ignored — the resource is scheduled using its normal shift-based availability and no capacity cap is enforced.

**When it occurs:** This typically occurs during initial FSL setup when an admin creates the capacity records before enabling the flag on the resource, or when a resource is migrated from shift-based to capacity-based without setting the flag. The records exist in the org, queries return them, but the scheduler does not use them.

**How to avoid:** Always set `ServiceResource.IsCapacityBased = true` on the resource record before creating any `ServiceResourceCapacity` records. After inserting capacity records, verify with:
```soql
SELECT Id, Name, IsCapacityBased FROM ServiceResource
WHERE Id IN (
    SELECT ServiceResourceId FROM ServiceResourceCapacity
)
AND IsCapacityBased = false
```
Any rows returned indicate capacity records that will be silently ignored by the scheduler.

---

## Gotcha 3: Date Gaps Between ServiceResourceCapacity Records Block Scheduling Without Warning

**What happens:** If the `EndDate` of one `ServiceResourceCapacity` record and the `StartDate` of the next record leave even a single day uncovered, the scheduler finds no active capacity record for that resource on the gap day and excludes the resource from all scheduling candidates. No warning or error is surfaced to the dispatcher. This is identical in appearance to the resource having no capacity records at all.

**When it occurs:** Most commonly after a seasonal or holiday adjustment where the admin splits a long-range record into multiple date-bounded records. If the split introduces a 1-day gap (e.g., record A ends March 31, record B starts April 2), April 1 is unschedulable. Also occurs after a bulk Data Loader update where off-by-one date errors are common.

**How to avoid:** After any capacity record creation or update, run an adjacency check:
```soql
SELECT ServiceResourceId, StartDate, EndDate
FROM ServiceResourceCapacity
WHERE ServiceResource.IsCapacityBased = true
ORDER BY ServiceResourceId, StartDate
```
Scan for cases where a record's `StartDate` does not equal the previous record's `EndDate + 1 day`. Automate this with the `check_fsl_capacity_planning.py` script in this skill's `scripts/` folder.

---

## Gotcha 4: No Seasonal Capacity Templates — Bulk Updates Require Data Loader or Apex

**What happens:** There is no native FSL UI to clone, adjust, or bulk-update `WorkCapacityLimit` or `ServiceResourceCapacity` records for a future date range. Admins who expect a "plan ahead" or "copy schedule" UI will not find one. Every seasonal or event-driven capacity change requires exporting existing records, modifying values in a spreadsheet, and re-importing via Data Loader (or writing an Apex batch).

**When it occurs:** Peak-season planning, holiday coverage reductions, new technician onboarding waves, and any situation requiring capacity changes across many resources or territories simultaneously.

**How to avoid:** Establish a documented runbook for capacity updates before the first seasonal cycle. Use Data Loader with a standardized CSV template and maintain version-controlled copies of the CSVs for each planning period. For orgs with frequent changes, build an Apex batch class or Flow triggered by an admin record that updates `WorkCapacityLimit` values. Do not plan to use the standard UI for bulk operations — it does not support them.

---

## Gotcha 5: Resource-Level and Territory-Level Caps Are Fully Independent — Both Must Pass

**What happens:** An appointment must satisfy both a `WorkCapacityLimit` check at the territory level and a `ServiceResourceCapacity` check at the resource level before it can be scheduled. Configuring one mechanism correctly while misunderstanding or neglecting the other leads to confusing rejections or unexpected overcapacity.

**When it occurs:** When an admin configures `WorkCapacityLimit` for demand throttling but does not realize that the target resources also have `IsCapacityBased = true` with tight `ServiceResourceCapacity` values (or vice versa). The appointment passes the territory-level check but is then rejected at the resource level — or the territory-level limit is reached before any resource-level limit is ever evaluated.

**How to avoid:** Always document which capacity mechanism governs each scenario. Use the decision table in SKILL.md to determine whether the constraint belongs at the resource level, the territory level, or both. When appointments stop scheduling unexpectedly, check both mechanisms in sequence: first query `WorkCapacityLimit` to see if the territory limit is reached, then check `ServiceResourceCapacity` records for date gaps or capacity exhaustion on individual resources.
