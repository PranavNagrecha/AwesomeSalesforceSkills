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

- Apex Developer Guide — Scheduled Apex: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_scheduler.htm
- Apex Developer Guide — Schedulable Interface: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_interface_schedulable.htm
- Apex Reference Guide — System.schedule(): https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_system.htm#apex_System_System_schedule
- Apex Reference Guide — System.abortJob(): https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_system.htm#apex_System_System_abortJob
- Apex Developer Guide — Testing Scheduled Apex: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_scheduler_test.htm
- Salesforce Well-Architected Overview — Reliability: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Well-Architected Overview — Operational Excellence: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
