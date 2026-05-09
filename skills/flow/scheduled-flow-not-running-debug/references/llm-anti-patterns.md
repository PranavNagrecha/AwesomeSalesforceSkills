# LLM Anti-Patterns — Scheduled Flow Not Running Debug

Common mistakes AI assistants make when an admin asks why their scheduled flow isn't firing. Avoid these when generating diagnoses.

---

## Anti-Pattern 1: Suggesting the admin rebuild the flow without diagnosing the schedule

**What the LLM generates:** "Try recreating the Decision element. Check that your Get Records query has the right filter conditions. Also, make sure your Update Records action targets the right object."

**Why it's wrong:**
- The flow itself is rarely the cause. ~80% of "scheduled flow not running" reports resolve to: deactivated scheduling user, deployment-aborted CronTrigger, time-zone confusion, or looking in the wrong Setup screen.
- Rebuilding a flow that was working takes hours and produces a fresh flow with the *same* schedule problem.
- The admin loses confidence in the framework if the LLM throws diagnostic steps at the wrong layer.

**What to do instead:** Always start with the schedule-side evidence trail (CronTrigger row, AsyncApexJob row, scheduling user `IsActive`). Only inspect the flow definition after schedule-side evidence shows the schedule fired and completed normally.

**Detection hint:** Look for "rebuild" / "recreate" / "delete and re-add the element" advice early in the response. That's the wrong layer for this question.

---

## Anti-Pattern 2: Skipping the AsyncApexJob check

**What the LLM generates:** "Check Setup → Flows to see if your flow is active. If it's active, the schedule should be running."

**Why it's wrong:**
- Setup → Flows shows the flow's design-time Active status. It does NOT show whether the underlying CronTrigger actually exists or whether recent runs succeeded.
- A flow can be Active in Setup → Flows with no CronTrigger row (deployment aborted) and no recent AsyncApexJob rows (never fired). Admin sees "Active" and concludes the schedule is working.

**What to do instead:** Always query both `CronTrigger` (is the schedule registered?) and `AsyncApexJob` (did recent runs happen, and what was their status?). Document both queries in the diagnosis.

**Detection hint:** Any diagnosis that doesn't reference `CronTrigger` and `AsyncApexJob` SOQL is incomplete.

---

## Anti-Pattern 3: Ignoring the deactivated scheduling user case

**What the LLM generates:** "Check that the flow is activated and the schedule is set correctly."

**Why it's wrong:**
- The single most common cause of a scheduled flow that "ran for months then stopped" is the scheduling user being deactivated. The schedule remains visible in Setup → Scheduled Jobs but the runs fail.
- The admin reading a generic LLM diagnosis will check the schedule UI, see it looks correct, and conclude "the LLM doesn't know what's wrong."

**What to do instead:** When diagnosing, immediately ask "who originally scheduled this flow, and is that user still Active?" If the LLM can't answer the user-activation question, the diagnosis is incomplete.

**Detection hint:** A diagnosis that doesn't mention `User.IsActive` or `CronTrigger.OwnerId` is missing the most common root cause.

---

## Anti-Pattern 4: Recommending Setup → Apex Jobs as the place to find scheduled flow execution

**What the LLM generates:** "Go to Setup → Apex Jobs and search for your flow name. You should see the execution history there."

**Why it's wrong:**
- Schedule-Triggered Flow execution surfaces in `AsyncApexJob` with `JobType = 'ScheduledApex'` and an internal flow-runner class name — NOT the flow's API name.
- The Setup → Apex Jobs UI's search-by-class-name returns zero rows when searching by flow name.
- Admin follows this advice, finds nothing, and concludes the flow isn't running. False negative.

**What to do instead:** Direct the admin to Setup → **Scheduled Jobs** (which lists CronTrigger rows including job detail names referencing the flow), or to a direct SOQL query against `AsyncApexJob` filtered by time window.

**Detection hint:** The phrase "search for your flow name in Setup → Apex Jobs" is the bad advice. Replace with "Setup → Scheduled Jobs" or a direct SOQL query.

---

## Anti-Pattern 5: Ignoring time-zone differences between scheduling user and viewer

**What the LLM generates:** "Check that the schedule's start time is correct. It should fire at 6 AM as you configured."

**Why it's wrong:**
- "6 AM" in the Schedule Trigger UI is interpreted in the *scheduling user's* time zone, not the org's default time zone or the viewing admin's time zone.
- An EMEA-based admin scheduling for "6 AM" produces a UTC stored fire-time that's 7-9 hours earlier than US-based teams expect.
- "It should fire at 6 AM" is technically true and uselessly misleading.

**What to do instead:** Always compare the scheduling user's `TimeZoneSidKey` to the org's default TZ when investigating timing complaints. Show the math: scheduled time → UTC → viewer's local time. If they differ, that's the issue.

**Detection hint:** Any timing complaint diagnosis that doesn't compare `User.TimeZoneSidKey` to org-default TZ is missing the most common timing root cause.

---

## Anti-Pattern 6: Suggesting deletion of CronTrigger as a fix

**What the LLM generates:** "Delete the existing CronTrigger record and re-create the schedule."

**Why it's wrong:**
- Direct DML on `CronTrigger` is restricted; the Salesforce-supported way to remove a schedule is `System.abortJob(cronTriggerId)`, not `delete`.
- Deleting via Tooling API or other side channels can leave orphan state. The official path is abort-then-reschedule.
- The naive `delete [SELECT Id FROM CronTrigger WHERE ...]` may fail with a System Exception or behave unpredictably depending on org configuration.

**What to do instead:** Use `System.abortJob(jobId)` to clear an unwanted schedule, then deactivate-and-reactivate the flow in Setup → Flows to register a fresh CronTrigger. Document the abort-then-reactivate sequence rather than reaching for raw DML.

**Detection hint:** Any sample code with `delete [SELECT Id FROM CronTrigger]` is wrong. Replace with `System.abortJob(...)`.

---

## Anti-Pattern 7: Assuming `JobType = 'ScheduledFlow'` exists as an AsyncApexJob category

**What the LLM generates:**

```sql
SELECT Id, Status FROM AsyncApexJob WHERE JobType = 'ScheduledFlow'
```

**Why it's wrong:** `AsyncApexJob.JobType` for Schedule-Triggered Flow execution is `'ScheduledApex'`, not `'ScheduledFlow'`. The naming is misleading because the execution does flow through scheduled-Apex infrastructure. A query filtering on `JobType = 'ScheduledFlow'` returns zero rows and the LLM concludes "no scheduled flows exist."

**What to do instead:**

```sql
SELECT Id, ApexClass.Name, Status, JobItemsProcessed
FROM AsyncApexJob
WHERE JobType = 'ScheduledApex'
  AND CreatedDate = LAST_N_DAYS:1
```

Then correlate by time-of-fire to the expected schedule. If you need to filter to flow-only and not user-defined Schedulable classes, an additional `ApexClass.Name LIKE '%Flow%'` heuristic can help, but the primary filter is `JobType = 'ScheduledApex'`.

**Detection hint:** Any SOQL with `JobType = 'ScheduledFlow'` is wrong. The correct filter is `JobType = 'ScheduledApex'`.
