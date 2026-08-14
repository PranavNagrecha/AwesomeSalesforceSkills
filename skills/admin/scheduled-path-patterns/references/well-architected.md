# Well-Architected Notes — Scheduled Path Patterns

## Relevant Pillars

- **Reliability** — Primary. A scheduled path introduces a gap between decision and action, and everything that makes it fail lives in that gap: the record changed, the record was deleted, the anchor field moved, the Flow version was swapped. A path is reliable exactly to the extent that its branch re-establishes truth before acting rather than trusting the snapshot it was queued with.
- **Scalability** — Primary alongside Reliability. Entry criteria are the throttle. Filtering at the Start element prevents interviews from being created; filtering inside the branch only decides what to do with interviews that already exist. On a high-volume object that difference is the whole scalability story.
- **Operational Excellence** — Secondary. Paused interviews are durable state with no version migration. Deactivating a Flow does not drain what is already queued, so a version swap is a change with a drain window, and Setup → Paused And Waiting Interviews is a queue that needs an owner and a monitoring habit.
- **Performance** — Secondary. The resumed branch runs in an asynchronous transaction whose limit budget is shared across the batch of interviews resumed together. A DML element inside a loop is the reliable way to exhaust it.

## Architectural Tradeoffs

| Tradeoff | Decision criteria |
|---|---|
| Event-anchored vs field-anchored offset | Event-anchored (`RecordTriggerEvent`) when "N after this happened" is the requirement — the schedule is immutable and cannot drift. Field-anchored when the business date is the point, accepting that the schedule is fixed at queue time and will not follow later edits to that field. |
| Scheduled path vs scheduled (batch) Flow | Scheduled path when the trigger is a record event and the wait is short and bounded. Scheduled Flow when the condition must be re-evaluated against *current* data — a nightly sweep is correct under field edits in a way a queued interview is not. |
| Scheduled path vs Schedulable Apex | Scheduled path for admin-owned, low-to-moderate volume, simple branches. Schedulable + Queueable Apex when the work fans out, needs retry semantics, needs callouts, or when the volume would make the paused-interview queue the operational bottleneck. |
| Filter at Start vs decide in the branch | Filter at Start, always, for anything volume-sensitive. A Decision element inside the branch is a correctness tool, not a throughput tool — the interview already exists by the time it runs. |
| One path with a re-read vs two paths (schedule + supersede) | One path suffices when the anchor cannot move. Add a second `ISCHANGED` path when the anchor field is business-editable, and make the branch idempotent with a "sent" flag so two queued interviews cannot both act. |

## Architectural Anti-Patterns

1. **Trusting `$Record` inside the scheduled branch** — This is the defining mistake of the pattern. The record variable is the queue-time snapshot; the branch runs later by design. Any decision made off it is a decision made on stale data, and the failure is silent — a notification about a closed Case, an escalation on a resolved issue.
2. **Unfiltered entry criteria on a high-volume object** — Queueing one interview per row and filtering afterward. The cost lands on the paused-interview queue and on the asynchronous limit budget of every resumed batch, and it is invisible until a data load makes it visible all at once.
3. **Treating a scheduled path as guaranteed delivery** — Delete the record and the branch never runs, with no error and no notification. Anything that must happen regardless of the record's survival does not belong in a scheduled path; it belongs in a scheduled sweep over durable state.
4. **Version-swapping without draining** — Queued interviews execute under the version that queued them. "We changed that Flow" is not true for anything already in flight, which makes post-change incident analysis confusing until someone remembers to check the queue.

## Official Sources Used

- Metadata API Developer Guide — Flow. Confirms the `FlowScheduledPathOffsetUnit` enumeration and its verbatim "possible values are: Months, Days, Hours, Minutes" — the fixed offset vocabulary a scheduled path can use. — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm (verified 2026-08-14)
- Apex Developer Guide — Execution Governors and Limits. Confirms the asynchronous limit budget the resumed branch runs under: 100 synchronous vs 200 asynchronous total SOQL queries, 150 total DML statements, 50,000 records retrieved by SOQL, 6 MB synchronous vs 12 MB asynchronous heap, "Maximum CPU time on the Salesforce servers" of 10,000 ms synchronous vs 60,000 ms asynchronous, and 10,000 as the "Total number of records processed as a result of DML statements, Approval.process, or database.emptyRecycleBin". — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm (verified 2026-08-14)
- Apex Developer Guide — Enforce Object and Field Permissions. Confirms the API-version gate on invocable Apex called from a scheduled branch: in API version 67.0 and later "Apex runs in user context by default, meaning that the current user's permissions and field-level security (FLS) are enforced during code execution", while "In API version 66.0 and earlier, system mode is the default." — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_perms_enforcing.htm (verified 2026-08-14)
- Salesforce Well-Architected Overview — pillar definitions used to map the tradeoffs above. — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
