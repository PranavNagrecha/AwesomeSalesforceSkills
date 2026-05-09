# Scheduled Flow Not Running — Diagnostic Template

Run this checklist top-to-bottom when a scheduled flow has stopped firing. Each step has an explicit "if-yes go to step N" branch.

## Step 1: Confirm the flow IS scheduled

Setup → Flows → click the flow → check "Schedule" panel.

- ✅ Schedule shows next run time → continue to Step 2
- ❌ Schedule is empty / unscheduled → re-schedule via Setup or `System.schedule()`. Done.

## Step 2: Look in the right place — Scheduled Jobs, not Apex Jobs

Setup → **Scheduled Jobs** (NOT Apex Jobs). Find the row with your flow's name.

- ✅ Row exists with State `WAITING` → continue to Step 3
- ❌ Row missing → `CronTrigger` deletion (deployment-aborted). Re-schedule via Setup. Done.
- ❌ Row exists with State `ABORTED` → reschedule. Done.

## Step 3: Check the scheduling user

```sql
SELECT Id, Name, OwnerId, NextFireTime, State, TimesTriggered
FROM CronTrigger
WHERE CronJobDetail.Name LIKE '%YourFlowName%'
```

Then `SELECT Id, IsActive, TimeZoneSidKey FROM User WHERE Id = '<OwnerId>'`.

- ✅ User active and in expected time zone → Step 4
- ❌ User deactivated → `CronTrigger` keeps running but flow context is broken. Re-schedule under an active service-user account.
- ❌ Time zone mismatch → schedule fires at unexpected wall-clock time. Reschedule with corrected UTC alignment OR change the user's `TimeZoneSidKey`.

## Step 4: Check for deployment-aborted CronTriggers

A deployment that touches the flow OR the scheduling user OR named credentials may auto-abort the schedule. Check `SetupAuditTrail` for `Deployed change set ...` near the time the schedule stopped.

- ✅ No deployment near the stop time → Step 5
- ❌ Deployment occurred → re-schedule. Add a post-deployment hook to re-schedule critical flows.

## Step 5: Check daily async limit

```sql
SELECT MAX(CompletedDate) FROM AsyncApexJob WHERE JobType = 'ScheduledApex' AND Status = 'Completed' AND CompletedDate = LAST_N_DAYS:7
```

If async daily limit is hit before the flow's scheduled time, it queues but is throttled.

- ✅ Daily limit healthy → Step 6
- ❌ Hitting daily limit consistently → reduce other async load or contact Salesforce to raise limit.

## Step 6: Manual run with same input

Setup → Flows → Open in Builder → Debug → set the same scheduled-flow input → Run.

- ✅ Manual run succeeds → schedule infrastructure is broken (re-schedule fixes it)
- ❌ Manual run fails → flow logic is broken (fix the flow itself)

## Recovery: Re-schedule via Apex

```apex
// Cancel + reschedule
List<CronTrigger> ct = [SELECT Id FROM CronTrigger WHERE CronJobDetail.Name LIKE '%YourFlowName%'];
for (CronTrigger c : ct) System.abortJob(c.Id);
System.schedule('YourFlowName', '0 0 6 ? * MON', new YourScheduledFlowInvoker());
```

(Replace `YourScheduledFlowInvoker` with a Schedulable wrapper that invokes the autolaunched flow via `Flow.Interview.YourFlow flow = new Flow.Interview.YourFlow(...)` if needed.)
