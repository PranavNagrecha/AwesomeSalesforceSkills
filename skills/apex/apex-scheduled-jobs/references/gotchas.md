# Gotchas — Apex Scheduled Jobs

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Scheduled Jobs Are Not Deployed by the Metadata API

**What happens:** Deploying the Schedulable Apex class via a change set, the Metadata API, or Salesforce CLI succeeds, but no active scheduled job exists in the target org afterward. The class is deployed; the `CronTrigger` record that represents the active schedule is not.

**When it occurs:** Every time a new scheduled job is introduced in a release, or when an existing job's schedule changes. Teams that treat Salesforce deployments like a traditional "deploy and done" workflow are caught off-guard when the job never runs in production.

**How to avoid:** Include a post-deployment step in every release plan that involves scheduled jobs. The standard approach is an Anonymous Apex script checked into the repository alongside the Apex class:

```apex
// deploy-scheduled-jobs.apex — run after deployment
List<CronTrigger> existing = [
    SELECT Id FROM CronTrigger
    WHERE CronJobDetail.Name = 'Nightly Lead Cleanup' AND State = 'WAITING'
    LIMIT 1
];
if (!existing.isEmpty()) {
    System.abortJob(existing[0].Id);
}
System.schedule('Nightly Lead Cleanup', '0 0 2 * * ?', new NightlyLeadCleanupScheduler());
```

For managed packages, a post-install script implementing `InstallHandler` can call `System.schedule()` automatically.

---

## Gotcha 2: The 100-Job Limit Is Shared and Enforced at Schedule Time, Not Run Time

**What happens:** `System.schedule()` throws `System.AsyncException: Too many jobs in the queue` — not when a job runs, but at the moment a new job is being scheduled. The org has hit the 100-job ceiling. The exception does not roll back cleanly in all contexts, which can leave a deployment partially configured.

**When it occurs:** Orgs that incrementally add scheduled Apex over time without periodic audits. The limit is easily overlooked because Setup > Scheduled Jobs only shows Apex scheduled jobs, while reports and other scheduled items may also consume slots depending on org configuration. The limit is org-wide across all scheduled job types.

**How to avoid:**
- Before adding new scheduled jobs in any release, query `CronTrigger` to confirm headroom:
  ```soql
  SELECT COUNT() FROM CronTrigger WHERE State IN ('WAITING', 'PAUSED', 'BLOCKED')
  ```
- If the org is above 80 jobs, review for consolidation opportunities. Replace multiple single-purpose scheduled classes with a master dispatcher pattern that covers multiple logical operations in one scheduled slot.
- Abort jobs for retired features — stale `WAITING` jobs silently occupy slots after the business process they served has been decommissioned.

---

## Gotcha 3: Direct Callouts From Scheduled Apex Throw a Runtime Exception

**What happens:** A `Schedulable.execute()` method that calls an HTTP endpoint or a web service throws `System.CalloutException: Callout from scheduled Apex not supported` at runtime. The code compiles without error and the class deploys cleanly, so the problem is not visible until the job actually fires.

**When it occurs:** When developers move callout logic from a synchronous context (e.g., a trigger or controller) into a scheduled job without adding an async delegation layer. The compile-time check does not block this pattern.

**How to avoid:** Delegate all callout work to a `@future(callout=true)` method or a Queueable implementing `Database.AllowsCallouts`:

```apex
global class IntegrationSyncScheduler implements Schedulable {
    global void execute(SchedulableContext SC) {
        // Correct: delegate callout to an async context that supports it
        System.enqueueJob(new ExternalApiSyncQueueable());
    }
}
```

Do not attempt to work around this by using `Database.AllowsCallouts` on the Schedulable class itself — the interface does not support it and the callout restriction on the Schedulable execution context is enforced by the platform regardless.

---

## Gotcha 4: Cannot Call System.schedule() From Within execute() to Reschedule Self

**What happens:** A Schedulable attempts to compute its next run time dynamically and calls `System.schedule()` inside its own `execute()` method. This throws a runtime exception: `System.AsyncException: Already running scheduled Apex.`

**When it occurs:** When teams try to implement self-rescheduling patterns to vary the cron schedule based on data conditions (e.g., run more frequently when there are pending records).

**How to avoid:** If dynamic rescheduling is genuinely needed, dispatch a Queueable from `execute()` and perform the abort-and-reschedule logic inside the Queueable's `execute()` method, which runs in a separate transaction where the restriction does not apply. For most cases, a fixed cron schedule is sufficient and simpler.

---

## Gotcha 5: Sandbox Refreshes Delete All Scheduled Jobs

**What happens:** After a sandbox refresh from production, all scheduled Apex jobs that existed in the sandbox are gone. The `CronTrigger` records are not carried over from the production snapshot. Developers who depend on scheduled jobs running in sandboxes for testing integration points or background processing are surprised when nothing runs after a refresh.

**When it occurs:** Every sandbox refresh. This affects full sandbox refreshes as well as partial and developer sandbox refreshes.

**How to avoid:** Maintain a sandbox initialization Anonymous Apex script (or a Custom Setting-driven auto-scheduler pattern) that is run immediately after each sandbox refresh. Document this step in the team's sandbox management runbook. Do not assume sandbox scheduled jobs persist; treat them as ephemeral.

---

## Gotcha 6: Duplicate Job Names Throw at Runtime, Not at Compile Time

**What happens:** Calling `System.schedule('My Job Name', cron, instance)` when a `CronTrigger` record with `CronJobDetail.Name = 'My Job Name'` already exists in `WAITING` state throws `System.AsyncException: A job named My Job Name already exists`. This is enforced at runtime per-org, not at the class level.

**When it occurs:** Post-deployment scripts that call `System.schedule()` without first aborting any existing job with the same name. Commonly happens when a release is run twice (e.g., a failed deployment is retried) or when multiple environments share the same deployment script without environment-specific job naming.

**How to avoid:** Always follow the abort-before-schedule pattern in deployment scripts: query for an existing job by name, abort it if found, then schedule. This is idempotent and safe to run multiple times.
