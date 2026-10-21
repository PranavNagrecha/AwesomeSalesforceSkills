# Well-Architected Notes — Flow Orchestration Admin

## Relevant Pillars

### Reliability

An orchestration's failure mode is a stall, not an error. A stage exits only when its `exitConditions` are met (api_meta 264 L73538); with an all-steps-complete condition one work item nobody picks up holds the whole stage — and holds it quietly. UNVERIFIED (2026-10-20): that all-steps-complete is the default. Reliability here is designed, not inherited: every interactive step needs an owner who exists, an aging alert, and a documented reassignment path (UNVERIFIED (2026-10-20): no corpus line documents a stage or step timeout). Because `FlowOrchestrationWorkItem` is a real record (API 54.0 and later), the aging backlog is reportable with ordinary tooling — but only if someone builds the report before the first stall rather than after.

### Operational Excellence

Orchestrations are the automation most likely to be missing from an org's inventory, because they carry their own `processType` (`Orchestrator`, and `ApprovalWorkflow` from API 63.0) rather than reusing `AutoLaunchedFlow`. Governance dashboards, regression-scope rules, and change-impact analyses that enumerate the older types return confidently wrong answers. Operational excellence starts with the org knowing its orchestrations exist, and extends to versioning them: an in-flight instance is state, so retiring an orchestration is a migration, not a delete (UNVERIFIED (2026-10-20): the effect of deleting an orchestration with running instances).

### User Experience

An interactive step is a request for someone's attention, and the orchestration is only as good as the moment that request arrives. Work assigned to an individual who is on leave, or to a queue nobody monitors, produces a process that appears to be running and is not. The design question for every interactive step is not "who is responsible" but "who will see this today, and what happens if they do not".

## Architectural Tradeoffs

**Orchestration vs. a single flow.** An orchestration buys multi-actor sequencing, durable pause-and-resume and, per Flow Builder practice, parallel work (UNVERIFIED (2026-10-20): no corpus line states steps of one stage run in parallel). It costs a second layer of metadata, a second thing to version, and a second place a process can be stuck. A process with one actor and no genuine wait is cheaper and more reliable as a plain flow — the orchestration adds surface without adding capability.

**Parallel stages vs. sequential ones.** (UNVERIFIED (2026-10-20): no corpus line states that the steps of one stage run in parallel.) Parallel steps compress elapsed time and couple the participants: the slowest reviewer sets the stage duration, and until the stage closes, the reviewers who finished have no visibility that they are waiting on someone. Sequential stages are slower and give a clearer answer to "where is this". Choose parallel when the reviews are genuinely independent and the SLA justifies the monitoring you will have to build.

**Rework loops vs. restart.** Branching backward to an earlier stage preserves the work already done and makes infinite loops possible. Cancelling and restarting is cruder, cannot loop, and discards context. Where a loop is used, it needs a counter or a guard condition. UNVERIFIED (2026-10-20): whether a stage connector may target an earlier stage, and whether the platform stops a cycling orchestration, are not stated in the corpus.

## Anti-Patterns

1. **Inventorying flows without `Orchestrator` and `ApprovalWorkflow`.** A filter that names only `AutoLaunchedFlow` and `Flow` excludes the org's most business-critical automation and reports a clean number while doing it. Enumerate process types explicitly, and check the filter before trusting anyone else's flow audit.

2. **Interactive steps with no aging report.** The Orchestrations UI shows what is running; it does not alert (UNVERIFIED (2026-10-20): Help-only UI behaviour). Without a report over work items by assignee and age, a stalled instance is discovered by the escalation, not by the org.

3. **Treating the invocable Apex behind a Background Step as out of scope.** The class's own `apiVersion` gates its security idiom, and "in API version 67.0 and later, you can't use the WITH SECURITY_ENFORCED clause" (apexdev 264 L11926). An orchestration's deployable surface includes everything it reaches, and a version-pinned helper class three layers down will fail the deploy and be reported as an orchestration problem.

## Official Sources Used

- Metadata API — Flow — `processType` `Orchestrator` (api_meta 264 L70832-70834), `ApprovalWorkflow` (L70752-70754), `EvaluationFlow` and `isOrchestrationConditionMet` (L70783-70787); `FlowOrchestratedStage` exit conditions and unused `faultConnector` (L73498-73543); `FlowStageStep` `actionType` values and entry conditions (L74742-74806); `FlowStageStepAssignee` types (L74889-74894)
- Apex Reference Guide — `ConnectApi.Orchestration` class — exact method signatures and their API versions (54.0 / 63.0 / 66.0) and the "You must specify either relatedRecordId or relatedOrchestrationId" rule — apexref 262 L97764-97855
- Object Reference — `FlowOrchestrationWorkItem` — a work item associated with a run-time instance of an interactive step, API 54.0 and later, and its assignee/sharing access rule — obj 264 L142795-142814
- Platform Events Developer Guide — `FlowOrchestrationEvent` — "notifies subscribers that a paused instance of an orchestration is ready to be resumed", API 53.0 and later, auto-publish cases and fields — platform_events 264 L12611-12694
- Object Reference — `FlowOrchestrationInstance` — run-time instance of an orchestration and its sharing / View All Data access rule — obj 264 L141838-141856
- Apex Developer Guide — API 67.0 versioned behaviour: no `WITH SECURITY_ENFORCED`, user context by default — apexdev 264 L11926-11928
- Repo-canonical: `agents/_shared/AGENT_CONTRACT.md` § "Apex security idiom by API version" — the API 67.0 rule that `WITH SECURITY_ENFORCED` can't be used and the `Security.stripInaccessible` / `SObjectAccessDecision` idiom
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
