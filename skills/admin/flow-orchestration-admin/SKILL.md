---
name: flow-orchestration-admin
description: "Flow Orchestration admin: stage configuration, step assignment, background steps, interactive steps, evaluation flows, work items, pause/resume. NOT for approval routing a standard approval process would handle — use admin/approval-processes."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - User Experience
tags:
  - flow-orchestration
  - work-items
  - stages
  - interactive-steps
  - background-steps
  - workflow
  - admin
triggers:
  - "how do i configure a flow orchestration for admin"
  - "multi user approval with flow orchestration not approval process"
  - "work item assignment in flow orchestration"
  - "interactive step vs background step orchestration"
  - "orchestration pause and resume on user action"
  - "evaluation flow in orchestration stage"
  - "we're having issues with flow orchestration"
inputs:
  - Process being orchestrated (steps, actors, decision points)
  - Step assignees (users, groups, queues)
  - SLA and timeout requirements per stage
  - Integration with external systems (waits for callback, etc.)
outputs:
  - Orchestration metadata (stages, steps, evaluation flows)
  - Work item assignment and notification configuration
  - Pause/resume and timeout handling plan
  - Monitoring view for in-flight orchestrations
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
status: stub
---

# Flow Orchestration Admin

Activate when building multi-step, multi-actor processes with Flow Orchestration in Setup: pause-and-wait workflows that cross users, queues, and background systems. Metadata API stores an orchestration as a `Flow` whose `processType` is `Orchestrator` — "an orchestration that organizes flows into groups of steps contained in a series of stages" (api_meta 264 L70832-70834) — or `ApprovalWorkflow`, "an orchestration that's used for an approval process" (API 63.0+, L70752-70754).

## Before Starting

- **Confirm the process actually needs orchestration.** Single-user approvals → Approval Process is fine. Multi-actor work, waits, and conditional branching → Orchestration (UNVERIFIED (2026-10-20): that steps in one stage run in parallel).
- **Map the actors and handoffs.** Every hand-off (user A → user B, system → user, user → system) is a Step. Diagram them before opening Flow Builder.
- **Decide on interactive vs background steps.** Interactive step = a user opens a work item screen. Background step = a Flow runs headless. Wrong choice produces confused users or stuck work.

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Is this an approval (`ApprovalWorkflow`) or a general orchestration (`Orchestrator`)? | The two process types are separate values (gotchas.md Gotcha 2) | The right `processType` before the first build |
| Which user, group, or queue owns each interactive step, and who covers absence? | A work item waits on its assignee and nothing alerts (Gotcha 4) | An `assignees` entry per step and a reassignment path |
| What is each stage's exit condition — a condition list or an evaluation flow (no corpus line documents a default)? | A stage exits only when its `exitConditions` are met (Core Concepts) | Exit logic stated per stage, not assumed |
| Does an external system finish a step, and can it publish `FlowOrchestrationEvent`? | Resume is event-driven, not polled (Gotcha 8) | The publisher, the instance and step IDs it sends, and its status values |
| Which invocable Apex do background steps reach, and at what `apiVersion`? | Security idioms change at API 67.0 (Gotcha 5) | An inventory of classes and versions in the deploy scope |
| Who operates runs, and through which record access? | Run and work-item access follow sharing rules or View All Data (Gotcha 6, Gotcha 7) | Named operators with tested access |
| Do flow inventories and release gates filter on `processType`? | Orchestrations are invisible to an `AutoLaunchedFlow` filter (Gotcha 1) | Inventory queries that name `Orchestrator` and `ApprovalWorkflow` |

UNVERIFIED (2026-10-20): row 2's "nothing alerts" (Help-only UI behaviour).

A proper configuration adds named owners, explicit exit conditions and an event-driven resume path, where "just building it" leaves a process that stalls silently on the first absent reviewer.

## Core Concepts

### Stage → Step → Work Item

An orchestration consists of Stages that run in series (api_meta 264 L70832-70834). Each Stage holds steps (`stageSteps`, L73543), and a step's `actionType` is `stepInteractive` (a work item a user picks up), `stepBackground` (runs a flow), `stepMuleSoft` (orchestrations only), or `stepApproval` (flow approval processes only, API 62.0+) (L74750-74761). A stage exits when its `exitConditions` are met (L73538), optionally decided by an exit evaluation flow (`exitActionName`, L73509). UNVERIFIED (2026-10-20): the Flow Builder default that a stage exits when all of its steps complete, and that steps in one stage start in parallel, are not stated on any corpus line.

### Evaluation Flow

Stages carry exit conditions only; steps carry entry conditions (`entryConditions`, "requirements that must be met to start the step", api_meta 264 L74805-74806) and exit conditions. A custom condition is an Evaluation Flow — `processType` `EvaluationFlow`, not `AutoLaunchedFlow` — which "uses the isOrchestrationConditionMet output variable and discards values from any other output variables" (L70783-70787). It decides whether a step starts or a stage or step exits.

### Work Items

Interactive steps produce `FlowOrchestrationWorkItem` records (obj 264 L142795-142797) assigned to a user, group, or queue (`AssigneeId`, L142824; `assigneeType` Group / Queue / User, api_meta 264 L74889-74894). An assignee sees all work items assigned to them; anyone else needs a sharing rule or View All Data (obj 264 L142813-142814). Completing the step's screen flow publishes a `FlowOrchestrationEvent` automatically (platform_events 264 L12614-12615).

### Pause and resume

`FlowOrchestrationEvent` "notifies subscribers that a paused instance of an orchestration is ready to be resumed"; the platform publishes it when an interactive step's screen flow completes, an asynchronous background step completes, or a MuleSoft step completes (platform_events 264 L12611-12615).

## Common Patterns

### Pattern: Parallel review with consolidated decision

Stage 1: Background — populate context. Stage 2: Three Interactive Steps in parallel (legal, security, finance review), each producing a Work Item. Stage 3: Evaluation Flow consolidates approvals. Stage 4: Background — enact the decision. UNVERIFIED (2026-10-20): that the three steps of one stage run in parallel (see Core Concepts).

### Pattern: Long-wait with external callback

Background Step kicks off an external process via callout and stores the orchestration instance and step instance IDs. On completion the external system publishes `FlowOrchestrationEvent` (`create()`, platform_events 264 L12625) with `OrchestrationInstanceId`, `StepInstanceId` and `StepStatus` `Completed` or `Error` (L12662-12698); "setting the payload for manually published flow orchestration events isn't supported" (L12652-12653).

### Pattern: Conditional rework loop

Stage 4 Evaluation Flow detects a rejection. The orchestration loops back to an earlier Stage to rework. UNVERIFIED (2026-10-20): no corpus line states that a stage `connector` may target an earlier stage or that loops are possible — test it in a sandbox before designing around it.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single approver, simple | Approval Process | Lower setup cost |
| Multi-actor parallel work | Flow Orchestration | An Approval Process step routes one approve-or-reject request to up to 25 approvers with `Unanimous` or `FirstResponse` handling (api_meta 264 L25404-25414); an orchestration step runs a flow (`actionName`, L74746-74747) |
| Wait for external callback | Orchestration + `FlowOrchestrationEvent` | Decouples from source |
| Time-based timeout | Stage with Evaluation Flow + wait | See note below |
| Round-robin assignment | Assign the step to a Queue | `AssignmentRules` route cases (api_meta 264 L25704), not work items |

UNVERIFIED (2026-10-20): the time-based-timeout row (no corpus line documents a stage timeout or wait inside an evaluation flow), any round-robin distribution of work items across queue members, and that the steps of one stage run in parallel (multi-actor row).

## Recommended Workflow

1. Whiteboard the process: actors, decision points, handoffs, SLAs.
2. Decide Approval Process vs Orchestration with `standards/decision-trees/automation-selection.md`.
3. Build required screen flows (for Interactive Steps), autolaunched flows (for Background Steps) and `EvaluationFlow` flows (for custom entry and exit conditions, api_meta 264 L70783-70787).
4. Create the Orchestration in Flow Builder; lay out Stages and Steps; wire Evaluation Flows.
5. Configure work item assignment — user, group, or queue, the only `assigneeType` values besides `invalid` (api_meta 264 L74889-74894) — and notifications.
6. Test in a sandbox with full actor list; validate stage timing and evaluation branches (UNVERIFIED (2026-10-20): whether steps in one stage run in parallel — observe it in the sandbox run).
7. Deploy; monitor `FlowOrchestrationInstance` and `FlowOrchestrationWorkItem` records; set up alerts for work items aging past SLA; run `scripts/check_flow_orchestration_admin.py --manifest-dir <src>` before each deploy.

## Review Checklist

- [ ] Stage and step diagram matches whiteboarded process
- [ ] Evaluation Flows tested for each branch
- [ ] Work item assignment routes to correct queue/user
- [ ] Aging report and reassignment path in place for long-wait stages (UNVERIFIED (2026-10-20): no corpus line documents a stage timeout)
- [ ] Fault paths defined inside each background step's flow (a stage's own `faultConnector` is "Not used", api_meta 264 L73541)
- [ ] Monitoring view available to ops team
- [ ] Training doc for users completing Interactive Steps

## Salesforce-Specific Gotchas

1. **A stage exits only when its exit condition is met.** With an all-steps-complete condition a slow reviewer holds up the whole stage; consider an aging report + reassignment. UNVERIFIED (2026-10-20): that all-steps-complete is the default exit condition, and any stage timeout (no corpus line documents one).
2. **Evaluation Flows run at every entry and exit check.** Expensive logic in an Evaluation Flow runs many times across a long orchestration; keep them lean. UNVERIFIED (2026-10-20): how often an evaluation flow is re-run is not stated on any corpus line.
3. **Deleting an in-flight Orchestration metadata breaks running instances.** Always retire with a migration plan; do not delete while instances are active. UNVERIFIED (2026-10-20): the effect of deleting an orchestration version with running instances is not in the corpus.

## Output Artifacts

| Artifact | Description |
|---|---|
| Orchestration diagram | Stages, steps, branches, evaluation flows |
| Work item assignment spec | User, group, or queue per step |
| Screen + autolaunched flow inventory | All flows the orchestration invokes |
| Monitoring + SLA runbook | Ops procedure for aging work items |

## Related Skills

- `admin/approval-processes` — simpler alternative for linear approvals
- `flow/record-triggered-flow-patterns` — underlying flow building
- `flow/flow-and-platform-events` — external-callback resume pattern
- `flow/flow-orchestration-patterns` — orchestration design patterns
