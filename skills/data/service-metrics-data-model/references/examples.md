# Examples — Service Metrics Data Model

## Example 1: SOQL Query for SLA Compliance Rate by Milestone Type

**Context:** A service operations analyst needs to report monthly SLA compliance for "First Response" and "Resolution" milestones across all cases closed in the last quarter. The org uses Entitlement Processes with Business Hours.

**Problem:** Querying `CaseMilestone WHERE IsViolated = false` incorrectly includes open in-progress milestones (which have not been violated yet but are not complete) in the compliance numerator, inflating the reported compliance rate.

**Solution:**

Step 1 — Query completed and violated milestones only (exclude open future milestones from the denominator):

```sql
SELECT
    MilestoneType.Name,
    COUNT(Id)                          total_milestones,
    SUM(CASE WHEN IsViolated = false AND IsCompleted = true THEN 1 ELSE 0 END) compliant,
    SUM(CASE WHEN IsViolated = true THEN 1 ELSE 0 END)                        violated,
    AVG(ElapsedTimeInMins)             avg_elapsed_mins
FROM CaseMilestone
WHERE (IsCompleted = true OR IsViolated = true)
  AND Case.ClosedDate >= LAST_N_DAYS:90
GROUP BY MilestoneType.Name
```

Step 2 — Build the equivalent Salesforce Summary report:

```
Report type: CaseMilestone with Case and MilestoneType (Custom Report Type)

Filters:
  - (IsCompleted = true) OR (IsViolated = true)
  - Case: Closed Date = Last 90 Days

Groupings:
  - MilestoneType: Name (row grouping)
  - Case: Closed Date (column grouping by month)

Summary columns:
  - Count of CaseMilestone ID
  - AVG ElapsedTimeInMins
  - Custom Summary Formula: Compliance % = (Count of ID where IsViolated = false) / (Count of ID) * 100
```

**Why it works:** Filtering to `IsCompleted = true OR IsViolated = true` scopes the dataset to milestones that have reached a terminal state — either completed on time, completed late, or timed out without completion. Open in-progress milestones are excluded from both numerator and denominator, giving a true compliance rate.

---

## Example 2: MTTR Derivation Using BusinessHours.diff() in Apex

**Context:** A financial services client requires MTTR measured in business hours, not calendar hours. Their support SLA covers Monday–Friday 8am–6pm. Cases closed outside business hours should still count only the business-time duration.

**Problem:** A formula field using `(ClosedDate - CreatedDate) * 24 * 60` counts weekend and overnight hours, overstating MTTR for cases that span non-business periods — giving inaccurate performance data.

**Solution:**

Step 1 — Create a custom Number field on Case: `MTTR_BH_Mins__c` (Number 10, 2).

Step 2 — Write an Apex trigger that fires on Case after-update when `IsClosed` becomes true:

```apex
trigger CaseMTTRTrigger on Case (after update) {
    // Retrieve the default Business Hours ID (or query from Entitlement)
    Id defaultBhId = [SELECT Id FROM BusinessHours WHERE IsDefault = true LIMIT 1].Id;

    List<Case> toUpdate = new List<Case>();

    for (Case newCase : Trigger.new) {
        Case oldCase = Trigger.oldMap.get(newCase.Id);
        // Only compute MTTR when case transitions to closed
        if (newCase.IsClosed && !oldCase.IsClosed
                && newCase.ClosedDate != null && newCase.CreatedDate != null) {
            // BusinessHours.diff returns milliseconds of business time
            Long bhMillis = BusinessHours.diff(defaultBhId, newCase.CreatedDate, newCase.ClosedDate);
            Decimal mttrMins = bhMillis / 60000.0;
            toUpdate.add(new Case(Id = newCase.Id, MTTR_BH_Mins__c = mttrMins));
        }
    }

    if (!toUpdate.isEmpty()) {
        update toUpdate;
    }
}
```

Step 3 — Validate against a known case:

```
Case 00001234:
  CreatedDate: 2026-03-27 09:00 (Friday 9am)
  ClosedDate:  2026-03-30 10:00 (Monday 10am)
  Business Hours: Mon-Fri 08:00-18:00

  Calendar time: ~73 hours (4,380 mins)
  Business time: 9am-6pm Friday (9h = 540 mins) + 8am-10am Monday (2h = 120 mins) = 660 mins

  MTTR_BH_Mins__c should be approximately 660.
```

**Why it works:** `BusinessHours.diff()` is the only Salesforce-native method that correctly accounts for non-business hours, holidays, and time zone offsets defined in the Business Hours record. The result matches what Salesforce itself uses when computing `CaseMilestone.ElapsedTimeInMins`.

---

## Example 3: Identifying Late-Completed Milestones vs. Open Violations

**Context:** A support manager reviews a dashboard and sees 15% of milestones flagged as `IsViolated = true`. They want to know how many of those were eventually completed (late) vs. still unresolved.

**Problem:** Treating `IsViolated = true` as "still open and unresolved" misclassifies late-but-completed milestones as active problems, skewing escalation and workload reports.

**Solution:**

```sql
SELECT
    IsCompleted,
    IsViolated,
    COUNT(Id) record_count
FROM CaseMilestone
WHERE MilestoneType.Name = 'Resolution'
  AND Case.ClosedDate >= THIS_QUARTER
GROUP BY IsCompleted, IsViolated
ORDER BY IsCompleted, IsViolated
```

Expected result shape:

```
IsCompleted | IsViolated | record_count | Interpretation
------------|------------|--------------|------------------------------
true        | false      | 820          | Completed on time (compliant)
true        | true       | 95           | Completed late (SLA miss)
false       | false      | 12           | Open, on-track (TargetDate future)
false       | true       | 8            | Open, overdue (TargetDate past, no completion)
```

**Why it works:** The four-quadrant breakdown fully characterizes milestone state. The critical insight is that `(IsCompleted=true, IsViolated=true)` is a distinct, valid terminal state representing late completion — not an error or open case.

---

## Anti-Pattern: Using IsViolated = false as the SLA Compliance Filter

**What practitioners do:** They add a filter `IsViolated = false` to a `CaseMilestone` report to get "compliant" milestones and divide by total to get a compliance rate.

**What goes wrong:** Open in-progress milestones also have `IsViolated = false` (the target date has not passed yet). They appear in the "compliant" bucket, inflating the compliance percentage — especially for recently opened cases. A report run mid-month will show artificially high compliance because new cases have not yet had time to be violated.

**Correct approach:** Filter to terminal-state milestones only: `(IsCompleted = true OR IsViolated = true)`. Compute compliance within that filtered set: `(IsCompleted = true AND IsViolated = false)` is compliant; `IsViolated = true` is non-compliant regardless of `IsCompleted`.
