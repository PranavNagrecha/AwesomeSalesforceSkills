# Well-Architected Notes — Apex Scheduled Jobs

## Relevant Pillars

### Reliability

Scheduled jobs that perform work inline (SOQL at scale, DML at scale) are fragile. When volume grows, they fail silently at governor limit boundaries and do not automatically retry. The Salesforce Well-Architected reliability framing requires that systems fail gracefully and recover predictably. The Schedulable-as-dispatcher pattern addresses this directly: the Schedulable class itself does nothing that can fail at scale; the Batch Apex or Queueable it dispatches runs in a separate transaction with its own limits and — for Batch Apex — automatic retry behavior per chunk.

Monitoring is equally part of reliability. `CronTrigger.State` and `AsyncApexJob` records are the platform's observability surface for scheduled operations. Orgs without regular audits of `CronTrigger` will miss `ERROR` or `BLOCKED` state jobs silently accumulating.

### Operational Excellence

Scheduled jobs that are not re-created after deployment or sandbox refresh represent an operational gap. The Salesforce Well-Architected operational excellence pillar emphasizes that automation is only reliable when deployment practices treat it as a first-class artifact. Scheduled jobs require post-deployment scripting as a non-optional step, not an afterthought.

The 100-job org limit is an operational governance concern. Without visibility into job inventory, orgs drift toward the limit. A canonical monitoring query and a periodic audit practice keep this under control.

---

## Architectural Tradeoffs

**Inline work vs. dispatcher pattern:** Putting logic directly in `execute()` is faster to write but fragile at scale. The dispatcher pattern adds one level of indirection (an extra class and `Database.executeBatch()` or `System.enqueueJob()` call) but makes the system resilient to volume growth. For any job that touches more than a few hundred records, the dispatcher pattern is always preferable.

**Many small jobs vs. master dispatcher:** Fine-grained scheduling (one job per logical operation) is easier to reason about and monitor individually, but consumes the 100-job limit quickly. A master dispatcher concentrates slot usage at the cost of slightly coarser scheduling granularity. Orgs with complex automation suites should plan for consolidation before they hit the ceiling.

**Fixed cron schedule vs. dynamic rescheduling:** Fixed cron expressions are simple, transparent, and can be read and reasoned about by any team member. Dynamic rescheduling (computing the next fire time from data) is powerful but complex, requires a Queueable delegation pattern, and is harder to audit. Default to fixed schedules unless there is a clear, quantified need for dynamic timing.

---

## Anti-Patterns

1. **Logic-heavy `execute()` methods** — Performing significant SOQL queries, DML operations, or business logic directly inside `execute()` creates a fragile job that breaks silently when data volume grows. The `execute()` method should be a dispatcher that delegates all substantive work to Batch Apex or a Queueable. This anti-pattern is responsible for the majority of production Schedulable failures.

2. **No post-deployment scheduling script** — Assuming that deploying the Apex class automatically activates the scheduled job. This leaves teams confused when the job does not run after a release. Every release involving a scheduled job must include a documented post-deployment step (Anonymous Apex or post-install script) that creates or recreates the `CronTrigger` record.

3. **Unchecked job proliferation toward the 100-job limit** — Adding new scheduled jobs without auditing and retiring obsolete ones. As the org grows and teams add automations, unused jobs accumulate in `WAITING` state for features that have been decommissioned. This silently exhausts the org-wide limit until new scheduling calls start throwing exceptions in production.

4. **Direct callouts from `execute()`** — Attempting HTTP or web service callouts directly inside `execute()` compiles cleanly but throws at runtime. The pattern creates a class that appears correct in development but fails in production on its first invocation, often with no immediate visibility because the failure surfaces only when the cron fires.

---

## Official Sources Used

- **Apex Developer Guide — Apex Scheduler** (apexdev.txt L16590–L17000; PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf) — supports: the `Schedulable` contract and that "The implemented method must be declared as global or public" (L16620); the 100-concurrent-jobs ceiling (L16597); the CRON field table and special characters `? / L W #` (L16826–L16913); "Apex doesn't allow for a job to be scheduled more than once an hour" (L16923); "Synchronous Web service callouts aren't supported from scheduled Apex" and the Batch-with-`AllowsCallouts` exemption (L16975–L16977); member-variable persistence and the `transient` remedy (L16984–L16989); the schedulable-class deploy lock and its exact error string (L16604–L16608, L16990–L16995); paused-job resume with no catch-up (L16996–L16998); sandbox refresh clearing schedules (L16982); maintenance-downtime rollback and reschedule (L16978–L16981); "The scheduler runs as system" (L16613); "The `System.schedule` method uses the user's time zone as the basis of all schedules" (L16820); the duplicate-name `AsyncException` text (L16810–L16813); `CronJobDetail.JobType = '7'` as the scheduled-Apex count filter (L16700–L16704).
- **Apex Developer Guide — Per-Transaction Apex Limits** (apexdev.txt L19529–L19600) — supports the load-bearing correction in this skill: "Although scheduled Apex is an asynchronous feature, synchronous limits apply to scheduled Apex jobs" (L19536), and the specific figures the dispatcher pattern is sized against — 100 SOQL (L19544), 6 MB heap (L19577), 10,000 ms CPU (L19579), and 50 `System.enqueueJob` calls in the synchronous column (L19571).
- **Apex Developer Guide — Using the System.scheduleBatch Method** (apexdev.txt L17293–L17344) — supports Gotcha 13: one execution only, minutes-from-now rather than CRON, returns a CronTrigger Id, and the limit hand-off — "All scheduled Apex limits apply… After the batch job is queued… the job no longer counts toward scheduled Apex limits" (L17339–L17342).
- **Apex Reference Guide — `System.schedule` / `System.abortJob` / `Schedulable` interface** (apexrefguide.txt L229017–L229060, L238661–L238695, L239710–L239790; https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_system.htm) — supports the `schedule` signature returning a `String` CronTrigger Id (L239722–L239735); that `SchedulableContext.getTriggerId` yields an Id `abortJob` accepts while an `AsyncApexJob` Id does not (L238679–L238695); and that an aborted job's in-progress code "will continue to execute until it completes" (L238663).
- **Object Reference for Salesforce — `CronTrigger` and `CronJobDetail`** (object_reference.txt L86664–L86840; PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf) — supports the full nine-value `State` enum including the platform-set `PAUSED` / `PAUSED_BLOCKED` and the `BLOCKED` definition ("Execution of a second instance of the job is attempted while one instance is running"); `NextFireTime`, `PreviousFireTime`, `TimesTriggered`, `TimeZoneSidKey`, `StartTime`, `EndTime`, `OwnerId`; and the `CronJobDetail.JobType` code table (`'7'` scheduled Apex, `'6'` scheduled Flow, `'8'` report run, `'3'` dashboard refresh).
- **Object Reference for Salesforce — `AsyncApexJob`** (object_reference.txt L42262–L42440) — supports the in-flight guard's `Status` values (`Holding`, `Preparing`, `Processing`, `Queued`, plus `Aborted`, `Completed`, `Failed`), the `JobType` values (`BatchApex`, `BatchApexWorker`, `Queueable`, `ScheduledApex`, `Future`), and `CronTriggerId` — the join from a run back to its schedule, "available in API version 53.0 and later".
- **Salesforce App Limits Cheat Sheet** (salesforce_app_limits_cheatsheet.txt L36, L313, L262, L345) — supports the precise name and edition exception for the ceiling: "Maximum number of Apex classes scheduled concurrently — 100. In Developer Edition orgs, the limit is 5" (L313); the 250,000-or-licenses×200 daily async execution limit shared across Batch, Queueable, scheduled Apex and future methods (L262, L345); and an independent restatement of the synchronous-limits note (L36).
- **`standards/decision-trees/async-selection.md`** (repo, Q9 and the "Clock (cron)" branch) — supports step 1 of the Recommended Workflow and the Decision Guidance table: when a schedule is the right trigger versus a record-triggered path, Platform Events, or a scheduled Flow.
- **Salesforce Well-Architected — Reliability and Operational Excellence**: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — supports the pillar framing above: fail-gracefully / recover-predictably for the dispatcher pattern, and treating the schedule as a first-class deployment artifact for the runbook.
