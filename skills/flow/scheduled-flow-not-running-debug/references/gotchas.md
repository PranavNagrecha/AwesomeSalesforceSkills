# Gotchas — Scheduled Flow Not Running Debug

Non-obvious Salesforce platform behaviors that bite admins debugging scheduled flows.

---

## Gotcha 1: Setup → Apex Jobs hides the flow's identity

**What happens:** Admin navigates to Setup → Apex Jobs and searches for their scheduled flow's API name. No results. They conclude "the flow isn't scheduled."

**When it occurs:** Always. Schedule-Triggered Flow execution surfaces in `AsyncApexJob` with `JobType = 'ScheduledApex'` and an `ApexClass.Name` that references an internal Salesforce flow-runner class (the exact class name is platform-internal and changes across releases). The flow's API name is NOT in the visible Apex Jobs UI columns — though it IS in the underlying SOQL fields if you query directly.

**How to avoid:** Use Setup → Scheduled Jobs (which surfaces `CronTrigger` rows including the flow's job detail name) or query `AsyncApexJob` directly filtered by the time window in question, then cross-reference timing against your expected schedule.

---

## Gotcha 2: Deactivating the scheduling user does not abort their CronTrigger

**What happens:** Admin deactivates a user during a license cleanup. That user had originally scheduled three flows. The flows stop firing. Setup → Flows still shows them as Active. The CronTrigger rows still exist in `WAITING` state but produce failed `AsyncApexJob` rows or no rows at all.

**When it occurs:** Any time a Schedule-Triggered Flow's owner is deactivated. Including innocuous-seeming actions like converting a contractor to a frozen state, or running an annual license-cleanup script.

**How to avoid:** Always schedule production flows under a dedicated integration user that's documented in your "do not deactivate" runbook. Never schedule under a real human's identity. Audit existing scheduled flows: `SELECT Id, OwnerId FROM CronTrigger WHERE State = 'WAITING'` and join to `User.IsActive`. Re-schedule any whose owner is at risk of deactivation.

---

## Gotcha 3: Deployment of an invoked Apex class auto-aborts the CronTrigger

**What happens:** A scheduled flow has been running every night for two years. Today's deploy includes an Apex class the flow uses (an invocable action, or a class transitively invoked). Tomorrow morning the flow didn't run. Setup → Flows shows it as Active. Setup → Scheduled Jobs shows no row for it.

**When it occurs:** Any deployment touching a class referenced by a scheduled flow's invocable actions. The `cutover-planning` skill documents this for Batch Apex / `System.schedule()` jobs; the same behavior applies to Schedule-Triggered Flows because they execute through the async-Apex infrastructure.

**How to avoid:** After every production deploy, run `SELECT COUNT_DISTINCT(Id) FROM CronTrigger WHERE State = 'WAITING'` and compare to a pre-deploy baseline. If the count drops, identify and re-schedule the missing flow(s). Alternatively, store a list of expected scheduled flows in version control and add a post-deploy script that checks each is present.

---

## Gotcha 4: DST spring-forward can skip a 2 AM scheduled run

**What happens:** Flow scheduled for "2:30 AM daily" misses one run on the second Sunday of March (US DST spring-forward) — the local 2 AM – 3 AM hour does not exist that day, and the schedule's behavior in that window is non-deterministic across regions.

**When it occurs:** The day a region transitions to daylight savings time. US: second Sunday in March; EU: last Sunday in March; AU: first Sunday in October.

**How to avoid:** Avoid scheduling between 2 AM and 3 AM local time for the scheduling user's TZ. If the schedule is mission-critical (e.g. nightly close-of-business processing), use Batch Apex via `System.schedule()` with an explicit UTC cron expression — the cron infrastructure handles DST transitions more predictably than the Schedule-Triggered Flow UI's "set start time" affordance.

---

## Gotcha 5: Sandbox refreshes copy CronTrigger records — scheduled flows fire in sandbox

**What happens:** Admin refreshes a sandbox from production on Friday. Monday morning the sandbox sends a flurry of "Closed Won" Chatter posts and emails because the production scheduled flow's CronTrigger came over with the refresh and fired against sandbox data.

**When it occurs:** Any sandbox refresh where the source org has active scheduled flows. The CronTrigger rows are copied; their `State` is preserved as `WAITING`; the next fire happens in the sandbox.

**How to avoid:** Implement a SandboxPostCopy Apex class that aborts all CronTriggers immediately after refresh:

```apex
public class FullSandboxPostRefresh implements SandboxPostCopy {
    public void runApexClass(SandboxContext context) {
        for (CronTrigger ct : [SELECT Id FROM CronTrigger WHERE State = 'WAITING']) {
            System.abortJob(ct.Id);
        }
    }
}
```

Decide explicitly which scheduled flows should run in sandbox and re-schedule those. Document the policy in `devops/sandbox-refresh-and-templates`.

---

## Gotcha 6: The flow's last run shows "Completed" but `JobItemsProcessed = 0`

**What happens:** Admin reports "the flow doesn't update anything." Diagnosis shows a clean `Status = 'Completed'` in `AsyncApexJob` for the most recent fire — but `JobItemsProcessed = 0`. The schedule fires fine; the start element's filter is matching zero records.

**When it occurs:** Common in two scenarios: (1) the flow was scheduled before any qualifying records existed and remains correct (just no work to do); (2) the start filter references a custom field that was renamed or whose values shifted (e.g. picklist value changed from "Open" to "InProgress" but the filter still says `Status = 'Open'`).

**How to avoid:** Don't conflate "schedule isn't firing" with "schedule fires but does no work." `JobItemsProcessed = 0` over multiple runs means the filter matches nothing — review the filter against current data with a SOQL preview before assuming the schedule is broken. Add diagnostic logging to the flow (a Get Records that counts qualifying records, then a Send Email if zero) to surface this in real time rather than retroactively.

---

## Gotcha 7: AsyncApexJob `Status = 'Holding'` looks like a hung job but is throttling

**What happens:** Admin sees `AsyncApexJob` rows in `Holding` status for hours. Concludes the platform is broken or the flow is stuck.

**When it occurs:** When the org has consumed a significant fraction of its daily async-Apex execution limit (default minimum 250,000 per 24-hour window, scales with user license count). The platform places new async work in `Holding` until capacity frees up, then promotes them to `Queued` then `Processing`.

**How to avoid:** Treat `Holding` as a queue-pressure signal, not a flow bug. Audit your org's daily async-Apex consumption (Setup → System Overview → API Usage). Consolidate redundant async work — multiple scheduled flows that could be one, redundant Queueable chains, etc. If chronic, this is an architecture conversation, not a flow-debug conversation.
