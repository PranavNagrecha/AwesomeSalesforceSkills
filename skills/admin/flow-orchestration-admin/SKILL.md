---
name: flow-orchestration-admin
description: "Flow Orchestration admin: stage configuration, step assignment, background steps, interactive steps, evaluation flows, work items, pause/resume. NOT for Flow Orchestration development APIs (use flow-orchestration-development). NOT for Approval Processes (use approval-processes)."
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
inputs:
  - Process being orchestrated (steps, actors, decision points)
  - User assignment rules (queues, role hierarchy, explicit users)
  - SLA and timeout requirements per stage
  - Integration with external systems (waits for callback, etc.)
outputs:
  - Orchestration metadata (stages, steps, evaluation flows)
  - Work item assignment and notification configuration
  - Pause/resume and timeout handling plan
  - Monitoring view for in-flight orchestrations
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Flow Orchestration Admin

Activate when building multi-step, multi-actor processes with Flow Orchestration in Setup: pause-and-wait workflows that cross users, queues, and background systems. Flow Orchestration is the successor to Approval Processes for complex branching; it is a no-code first-class orchestrator with stages, steps, and work items.

## Before Starting

- **Confirm the process actually needs orchestration.** Single-user approvals → Approval Process is fine. Multi-actor with parallel work, waits, and conditional branching → Orchestration.
- **Map the actors and handoffs.** Every hand-off (user A → user B, system → user, user → system) is a Step. Diagram them before opening Flow Builder.
- **Decide on interactive vs background steps.** Interactive step = a user opens a work item screen. Background step = a Flow runs headless. Wrong choice produces confused users or stuck work.

## Core Concepts

### Stage → Step → Work Item

An orchestration consists of Stages (run sequentially). Each Stage has Steps (can run in parallel). Each Step is either Interactive (produces a Work Item a user picks up) or Background (runs a flow). Stages advance when all steps complete — including conditional skips.

### Evaluation Flow

A Stage's entry and exit conditions are evaluated by an Evaluation Flow — a small autolaunched flow returning a boolean. Used to decide whether to skip a stage, loop back, or proceed.

### Work Items

Interactive steps produce `WorkItem` records assigned to a user or queue. The assignee opens the Work Items list, picks an item, completes the associated screen flow, and the step advances.

### Pause and resume

Orchestration pauses at Interactive Steps waiting for user action and at wait elements inside Background Steps. Resumption is automatic on work item completion or wait-condition satisfaction.

## Common Patterns

### Pattern: Parallel review with consolidated decision

Stage 1: Background — populate context. Stage 2: Three Interactive Steps in parallel (legal, security, finance review), each producing a Work Item. Stage 3: Evaluation Flow consolidates approvals. Stage 4: Background — enact the decision.

### Pattern: Long-wait with external callback

Background Step kicks off an external process via callout and stores a correlation ID. Orchestration waits on a Platform Event the external system publishes on completion. The event resumes the step.

### Pattern: Conditional rework loop

Stage 4 Evaluation Flow detects a rejection. The orchestration loops back to an earlier Stage to rework. Use conditional navigation (branches between stages) carefully — infinite loops are possible.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single approver, simple | Approval Process | Lower setup cost |
| Multi-actor parallel work | Flow Orchestration | Approval Process cannot branch |
| Wait for external callback | Orchestration + Platform Event | Decouples from source |
| Time-based timeout | Stage with Evaluation Flow + wait | Shipped pattern |
| Round-robin assignment | Work item to queue + assignment rules | Don't hand-code |

## Recommended Workflow

1. Whiteboard the process: actors, decision points, handoffs, SLAs.
2. Decide Approval Process vs Orchestration with `standards/decision-trees/automation-selection.md`.
3. Build required screen flows (for Interactive Steps) and autolaunched flows (for Background / Evaluation).
4. Create the Orchestration in Flow Builder; lay out Stages and Steps; wire Evaluation Flows.
5. Configure work item assignment (user, queue, role-based) and notifications.
6. Test in a sandbox with full actor list; validate parallel-stage timing and evaluation branches.
7. Deploy; monitor the Orchestrations tab; set up alerts for work items aging past SLA.

## Review Checklist

- [ ] Stage and step diagram matches whiteboarded process
- [ ] Evaluation Flows tested for each branch
- [ ] Work item assignment routes to correct queue/user
- [ ] Timeouts in place for long-wait stages
- [ ] Fault paths defined on Background Steps
- [ ] Monitoring view available to ops team
- [ ] Training doc for users completing Interactive Steps

## Salesforce-Specific Gotchas

1. **Parallel steps finish when ALL complete.** A slow reviewer holds up the whole stage; consider timeouts + reassignment.
2. **Evaluation Flows run every entry and exit.** Expensive logic in an Evaluation Flow runs many times across a long orchestration; keep them lean.
3. **Deleting an in-flight Orchestration metadata breaks running instances.** Always retire with a migration plan; do not delete while instances are active.

## Output Artifacts

| Artifact | Description |
|---|---|
| Orchestration diagram | Stages, steps, branches, evaluation flows |
| Work item assignment spec | Queue, user, or role per step |
| Screen + autolaunched flow inventory | All flows the orchestration invokes |
| Monitoring + SLA runbook | Ops procedure for aging work items |

## Related Skills

- `admin/approval-processes` — simpler alternative for linear approvals
- `flow/flow-record-triggered-patterns` — underlying flow building
- `admin/platform-events-for-admins` — external-callback resume pattern
