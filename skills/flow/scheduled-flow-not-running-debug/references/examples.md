# Examples — Scheduled Flow Not Running Debug

Concrete diagnosis and recovery scenarios. Each example pins one common root cause to one set of evidence and one fix.

---

## Example 1 — SOQL evidence trail: did my scheduled flow run?

**Symptom:** "I scheduled the flow yesterday for 6 AM today. It's now 9 AM and I see nothing."

**Evidence to gather (run all four queries in Workbench / Developer Console):**

```sql
-- 1. Is the schedule registered at all?
SELECT Id, CronJobDetail.Name, State, NextFireTime, PreviousFireTime, OwnerId
FROM CronTrigger
WHERE State = 'WAITING'
ORDER BY NextFireTime ASC
```

```sql
-- 2. What scheduled-apex jobs ran in the last 24 hours?
SELECT Id, ApexClass.Name, Status, JobItemsProcessed, NumberOfErrors,
       ExtendedStatus, CreatedDate, CompletedDate
FROM AsyncApexJob
WHERE JobType = 'ScheduledApex'
  AND CreatedDate = LAST_N_DAYS:1
ORDER BY CreatedDate DESC
```

```sql
-- 3. Did any flow interviews fail in the last 24 hours?
SELECT Id, InterviewLabel, CurrentElement, CreatedDate
FROM FlowInterview
WHERE CreatedDate = LAST_N_DAYS:1
ORDER BY CreatedDate DESC
LIMIT 50
```

```sql
-- 4. Is the scheduling user still active?
-- (Use the OwnerId from query 1)
SELECT Id, Username, IsActive, TimeZoneSidKey
FROM User
WHERE Id = '<OwnerId from query 1>'
```

**Interpretation matrix:**

| Q1 result | Q2 result | Q4 result | Diagnosis |
|---|---|---|---|
| No row for flow | No matching row | — | Schedule was never registered, OR a deploy aborted it. Re-schedule. |
| Row exists, NextFireTime in past | No matching row | `IsActive = false` | Scheduling user deactivated; CronTrigger orphaned. |
| Row exists, NextFireTime future | One row, `Status = 'Completed'`, `JobItemsProcessed = 0` | `IsActive = true` | Schedule fired; start filter matched zero records. Loosen filter. |
| Row exists | One row, `Status = 'Failed'`, `ExtendedStatus` populated | — | Read `ExtendedStatus` for the actual error. |
| Row exists | One row, `Status = 'Holding'` | — | Org daily async-Apex limit pressure. |

---

## Example 2 — Setup navigation: where to click

**Symptom:** Admin says "I can't find where my flow ran."

**Wrong path:**

```
Setup → Quick Find → "Apex Jobs"
   → search for "MyScheduledFlow"
   → no results
   → conclude: "the flow isn't scheduled"
```

**Right path (three clicks):**

```
Setup → Quick Find → "Scheduled Jobs"
   → look for a row whose Apex Class column references the flow runner
   → check Submitted By column = expected scheduling user
   → check Next Run column = expected next-fire UTC, converted to local

Setup → Quick Find → "Paused and Failed Flow Interviews"
   → look for any row in Failed status from the most-recent fire window

Setup → Quick Find → "Flows"
   → only useful for confirming the flow is Active and inspecting design,
     NOT for confirming the schedule is firing
```

**Why the wrong path looks right:** Setup → Apex Jobs DOES show scheduled-apex execution rows when filtering by `JobType = 'ScheduledApex'` in the underlying SOQL — but the UI's "Apex Class" column shows an internal flow-runner class, not the flow's API name. Searching for the flow name returns zero rows even when the flow has been firing every day for months.

---

## Example 3 — Manual run vs scheduled run: isolating the schedule from the logic

**Symptom:** "I want to know if it's the schedule that's broken or the flow that's broken."

**Procedure:**

1. **Manual run, same scheduling user.** Log in as the scheduling user. Setup → Flows → click the flow → Run. If it succeeds, the flow logic is sound — the issue is the schedule.
2. **Manual run, system administrator.** If step 1 fails, retry as a System Admin. If the System Admin run succeeds but the scheduling user's run fails, the issue is permissions on the scheduling user's profile.
3. **Compare to the actual scheduled fire.** Get the latest `AsyncApexJob` row for the flow (Example 1, query 2). If `Status = 'Completed'` but the manual run also fails — there's something subtly different between manual-trigger and schedule-trigger context (less common; usually session-context or `$User.UserType` checks).

**Anonymous Apex to fire a flow manually with the same input as a schedule-triggered flow:**

```apex
Map<String, Object> inputs = new Map<String, Object>();
// Schedule-Triggered Flows generally take no inputs — start element queries records itself.
Flow.Interview.MyScheduledFlow myFlow = new Flow.Interview.MyScheduledFlow(inputs);
myFlow.start();
System.debug('Manual run completed');
```

**Why this matters:** if a manual run succeeds but the scheduled run doesn't, do NOT rebuild the flow. The flow is fine. Tune the schedule.

---

## Example 4 — Time-zone diagnosis

**Symptom:** "I scheduled the flow for 6 AM Monday. It runs at 1 AM Monday in our system."

**Diagnosis steps:**

1. Get the CronTrigger and its owner:

```sql
SELECT Id, CronJobDetail.Name, NextFireTime, OwnerId
FROM CronTrigger
WHERE State = 'WAITING'
  AND CronJobDetail.Name LIKE '%MyFlow%'
```

2. Get the owner's time zone:

```sql
SELECT Id, Username, TimeZoneSidKey
FROM User
WHERE Id = '<OwnerId>'
```

3. Get the org's default time zone: Setup → Company Information → "Default Time Zone".

4. **The math.** `NextFireTime` is stored in UTC. The Schedule Trigger UI accepts the start time *in the scheduling user's TZ at the moment they configured it*. Worked example:

```
Scheduling user TZ: Europe/London (UTC+0 in winter, UTC+1 in summer)
Org default TZ:     America/Los_Angeles (UTC-8 in winter, UTC-7 in summer)
Configured time:    "6:00 AM" via the UI
Stored NextFireTime: 06:00 UTC

US team views NextFireTime in their local TZ → "10:00 PM Sunday" (PST) or
"11:00 PM Sunday" (PDT). They expected 6 AM Monday Pacific. Off by 7-8 hours.
```

**Fix:** Either (a) re-schedule using a user whose TZ matches the org default, or (b) accept that the schedule is in the scheduler's TZ and document the actual fire time. Do NOT try to "convert" the stored value — the stored value is correct given the scheduler's TZ context.

---

## Example 5 — Recovering from a deployment-aborted CronTrigger

**Symptom:** "We deployed yesterday, and the scheduled flow that ran every night for two years has stopped running."

**Confirm the cause:**

```sql
-- Compare CronTrigger count before and after deployment
SELECT COUNT_DISTINCT(Id) cnt
FROM CronTrigger
WHERE State = 'WAITING'
```

If this returned a higher number before the deploy than now, you almost certainly lost CronTrigger records to the deployment.

**Recovery — re-activate the scheduled flow:**

The simplest path: Setup → Flows → open the affected flow → click Deactivate (this clears any orphan), then click Activate again. During Activate you'll be prompted for the schedule — re-confirm Once / Daily / Weekly / start time / day-of-week. Verify a new row appears in Setup → Scheduled Jobs.

**Better path — script it for multi-flow deploys:**

Document each scheduled flow's Once / Daily / Weekly cadence in version control. After every deployment, run a checklist that re-activates each flow whose CronTrigger is missing. Do not rely on memory; the gap from "deploy succeeded" to "first missed run" is often a week.

**Prevent recurrence:** add a post-deploy validation step that queries CronTrigger and asserts every expected scheduled flow is registered. The bundled `scripts/check_scheduled_flow_not_running_debug.py` enumerates scheduled flows from metadata; pair it with a SOQL query against CronTrigger to detect the diff.
