# Well-Architected Notes — Scheduled Flow Not Running Debug

## Relevant Pillars

- **Reliability** — Scheduled flows are unattended automation. When they silently stop, business processes (renewals, escalations, nightly cleanup) silently degrade. Reliability here means knowing within hours, not weeks, that a schedule has failed. The single highest-leverage move is monitoring `CronTrigger` row count and sending an alert when an expected scheduled job goes missing.
- **Operational Excellence** — The debug-side of this skill is operational excellence: standard SOQL evidence trail, standard Setup navigation, standard recovery procedure. Without a runbook, every "scheduled flow not running" report becomes an ad-hoc investigation. With a runbook, it becomes a 10-minute triage.

## Architectural Tradeoffs

| Tradeoff | Why it matters |
|---|---|
| Schedule-Triggered Flow vs Scheduled Apex (`System.schedule()`) | Scheduled Flows are admin-configurable and survive admin handoffs. Scheduled Apex is more reliable across DST transitions and gives explicit cron control. Use Flow for admin-tunable cadences; use Apex for mission-critical UTC-anchored windows. |
| Schedule under real human user vs dedicated integration user | Real-human is convenient initially but creates a bus-factor risk: deactivation, role change, or vacation can break the schedule. Integration user is more setup work but durable. Always integration user for production. |
| Fault-handling at flow level vs catching errors in monitoring | Adding a Fault Path inside the flow handles most error cases gracefully but doesn't help if the schedule never fires (CronTrigger missing). External monitoring (a separate scheduled job that checks for expected CronTriggers) catches the cases the flow can't see. Both layers, not either-or. |
| Aggressive sandbox CronTrigger cleanup vs preserving for testing | A SandboxPostCopy that aborts all CronTriggers prevents runaway sandbox automation but may delete schedules a developer needs to test. Decide by sandbox tier: production-clone-sized sandboxes should always abort; developer sandboxes can preserve. Document the policy. |

## Anti-Patterns

1. **Rebuilding the flow without diagnosing the schedule** — The most common LLM and admin response to "scheduled flow not running" is to inspect the flow's Decision elements, Get Records filters, and Update Records actions. Almost every real cause is environmental (deactivated user, aborted CronTrigger, wrong place to look) — the flow definition is rarely the issue. Diagnose the schedule first; the flow second.
2. **Scheduling under the implementation lead's identity** — A senior admin builds and schedules the flow during go-live. Six months later they leave the company. The schedule keeps running until their account is deactivated, then quietly stops. This is the textbook bus-factor failure.
3. **Treating `Status = 'Completed', JobItemsProcessed = 0` as a schedule failure** — It's the opposite. The schedule worked. The filter matched zero records. Tune the filter or accept zero-work runs; don't tear down the schedule.
4. **Assuming Setup → Apex Jobs is the home of scheduled flow execution** — The UI search lies. Searching for the flow's API name in Setup → Apex Jobs returns zero rows even when execution rows exist underneath.
5. **Ignoring DST in scheduled-flow design** — A "2 AM daily" schedule is fine 363 days a year and broken twice. If you must schedule near 2 AM, use Scheduled Apex with explicit UTC cron, not Schedule-Triggered Flow.
6. **Deploying without a post-deploy CronTrigger check** — Deployments can silently abort scheduled flows. Without a post-deploy validation, the gap from deploy-success to first-missed-fire is often a week, and the link between cause and effect is forgotten by then.

## Official Sources Used

- Salesforce Help — Schedule a Flow — https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_schedule.htm
- Salesforce Help — Configure the Schedule Trigger — https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_schedule_when.htm
- Object Reference — `AsyncApexJob` — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_asyncapexjob.htm
- Object Reference — `CronTrigger` — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_crontrigger.htm
- Object Reference — `FlowInterview` — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_flowinterview.htm
- Apex Reference — `System.abortJob` — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_system.htm
- Salesforce Help — Salesforce Time Zone Settings — https://help.salesforce.com/s/articleView?id=sf.admin_supported_timezone.htm
- Salesforce Well-Architected — Reliability — https://architect.salesforce.com/docs/architect/well-architected/guide/reliability.html
- Salesforce Well-Architected — Operational Excellence — https://architect.salesforce.com/docs/architect/well-architected/guide/operational-excellence.html
