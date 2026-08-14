# Well-Architected Notes — Flow Orchestration Admin

## Relevant Pillars

### Reliability

An orchestration's failure mode is a stall, not an error. A parallel stage advances only when every step in it completes, so one work item nobody picks up holds the whole stage — and holds it quietly. Reliability here is designed, not inherited: every interactive step needs an owner who exists, a timeout, and a documented reassignment path. Because `FlowOrchestrationWorkItem` is a real record (API 54.0 and later), the aging backlog is reportable with ordinary tooling — but only if someone builds the report before the first stall rather than after.

### Operational Excellence

Orchestrations are the automation most likely to be missing from an org's inventory, because they carry their own `processType` (`Orchestrator`, and `ApprovalWorkflow` from API 63.0) rather than reusing `AutoLaunchedFlow`. Governance dashboards, regression-scope rules, and change-impact analyses that enumerate the older types return confidently wrong answers. Operational excellence starts with the org knowing its orchestrations exist, and extends to versioning them: an in-flight instance is state, so retiring an orchestration is a migration, not a delete.

### User Experience

An interactive step is a request for someone's attention, and the orchestration is only as good as the moment that request arrives. Work assigned to an individual who is on leave, or to a queue nobody monitors, produces a process that appears to be running and is not. The design question for every interactive step is not "who is responsible" but "who will see this today, and what happens if they do not".

## Architectural Tradeoffs

**Orchestration vs. a single flow.** An orchestration buys multi-actor sequencing, parallel work, and durable pause-and-resume. It costs a second layer of metadata, a second thing to version, and a second place a process can be stuck. A process with one actor and no genuine wait is cheaper and more reliable as a plain flow — the orchestration adds surface without adding capability.

**Parallel stages vs. sequential ones.** Parallel steps compress elapsed time and couple the participants: the slowest reviewer sets the stage duration, and until the stage closes, the reviewers who finished have no visibility that they are waiting on someone. Sequential stages are slower and give a clearer answer to "where is this". Choose parallel when the reviews are genuinely independent and the SLA justifies the monitoring you will have to build.

**Rework loops vs. restart.** Branching backward to an earlier stage preserves the work already done and makes infinite loops possible. Cancelling and restarting is cruder, cannot loop, and discards context. Where a loop is used, it needs a counter or a guard condition — the platform will not stop the orchestration from cycling on its own.

## Anti-Patterns

1. **Inventorying flows without `Orchestrator` and `ApprovalWorkflow`.** A filter that names only `AutoLaunchedFlow` and `Flow` excludes the org's most business-critical automation and reports a clean number while doing it. Enumerate process types explicitly, and check the filter before trusting anyone else's flow audit.

2. **Interactive steps with no aging report.** The Orchestrations UI shows what is running; it does not alert. Without a report over work items by assignee and age, a stalled instance is discovered by the escalation, not by the org.

3. **Treating the invocable Apex behind a Background Step as out of scope.** The class's own `apiVersion` gates its security idiom, and from 67.0 `WITH SECURITY_ENFORCED` does not compile at all. An orchestration's deployable surface includes everything it reaches, and a version-pinned helper class three layers down will fail the deploy and be reported as an orchestration problem.

## Official Sources Used

- Metadata API — Flow (Visual Workflow) — `processType` values `Orchestrator` ("An orchestration that organizes flows into groups of steps contained in a series of stages", API 53.0+) and `ApprovalWorkflow` ("An orchestration that's used for an approval process", API 63.0+); `FlowOrchestratedStage` as an array of stage nodes (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
- Apex Reference Guide — `ConnectApi.Orchestration` class — exact method signatures and their API versions (54.0 / 63.0 / 66.0) and the "You must specify either relatedRecordId or relatedOrchestrationId" rule (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ConnectAPI_Orchestration_static_methods.htm
- Object Reference — `FlowOrchestrationWorkItem` — a work item associated with a run-time instance of an interactive step, API 54.0 and later (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_floworchestrationworkitem.htm
- Platform Events Developer Guide — `FlowOrchestrationEvent` — "notifies subscribers that a paused instance of an orchestration is ready to be resumed", API 53.0 and later (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/sforce_api_objects_floworchestrationevent.htm
- Object Reference — `FlowOrchestrationInstance` — the run-time instance object behind the Orchestration Runs list view — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_floworchestrationinstance.htm
- Repo-canonical: `agents/_shared/AGENT_CONTRACT.md` § "Apex security idiom by API version" — the 67.0 removal of `WITH SECURITY_ENFORCED` and the `Security.stripInaccessible` / `SObjectAccessDecision` idiom
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
