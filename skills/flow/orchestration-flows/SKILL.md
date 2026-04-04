---
name: orchestration-flows
description: "Use when designing or reviewing Flow Orchestration for long-running, multi-user, or asynchronous business processes with stages, steps, work items, and monitoring needs. Triggers: 'flow orchestration', 'work item', 'stages and steps', 'multi-user process', 'long-running flow'. NOT for simple single-transaction record-triggered flows or lightweight approval routing that does not need orchestration."
category: flow
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Reliability
  - Scalability
  - Operational Excellence
triggers:
  - "when should i use flow orchestration"
  - "flow orchestration stages and steps design"
  - "multi user business process in salesforce"
  - "work items in flow orchestration"
  - "orchestration monitoring and recovery"
tags:
  - flow-orchestration
  - work-items
  - asynchronous-process
  - stages
  - multi-user
inputs:
  - "business process timeline and handoff points"
  - "which steps are background vs human-interactive"
  - "monitoring, reassignment, and recovery expectations"
outputs:
  - "orchestration design recommendation"
  - "stage-and-step review findings"
  - "decision on orchestration vs standard flow or apex"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when the business process spans time, people, and system boundaries in a way that normal record-triggered or screen flows do not handle cleanly. Flow Orchestration is valuable when the process needs explicit stage progression, work assignment, and observability instead of pretending the whole journey happens in one synchronous transaction.

## Before Starting

- Is the process actually long-running or multi-user, or could a standard Flow handle it more simply?
- Which parts of the process are background automation, and which parts create work items for humans?
- What must happen when a step is delayed, reassigned, fails, or needs recovery after a long wait?

## Core Concepts

### Orchestration Is For Process Lifecycles, Not Just Automation Steps

Regular Flows are good at single execution paths. Orchestration becomes useful when the process needs explicit lifecycle management across stages, users, and time gaps. Treat it as process architecture, not just a bigger Flow canvas.

### Stages And Steps Need Clear Ownership

Stages should represent meaningful process milestones, while steps should represent work that can be monitored, assigned, and completed. If stage boundaries are vague, monitoring and recovery become unclear.

### Interactive And Background Work Should Be Designed Differently

Human work items need assignment, visibility, and escalation thinking. Background steps need idempotency, fault handling, and service-level expectations. Orchestration only helps if those two concerns are designed deliberately.

### Monitoring Is Part Of The Design

A long-running process is incomplete unless operations teams can see where instances are stuck, who owns the next action, and how to resume or intervene. Orchestration is as much about operational visibility as it is about flow logic.

## Common Patterns

### Stage-Based Onboarding Or Fulfillment

**When to use:** A business journey moves through clear milestones with a mix of automated and human tasks.

**How it works:** Define stages around milestones, keep each step narrow, and route interactive work items to the right users or queues.

**Why not the alternative:** A single standard Flow becomes brittle when it tries to model waits, approvals, and manual follow-up inside one execution path.

### Background Step Plus Human Review

**When to use:** System work should prepare data and then hand it to a reviewer or fulfiller.

**How it works:** Use background steps for deterministic system tasks and interactive steps only where human judgment is genuinely required.

**Why not the alternative:** Making every step human-visible slows the process and reduces automation value.

### Escalation To Apex Or Another Orchestrator

**When to use:** The process needs heavy integration logic, very large data movement, or transaction behavior beyond Flow's fit.

**How it works:** Keep orchestration for human lifecycle management only, or move the process elsewhere if Flow is no longer the right boundary.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single save event with immediate side effects | Standard record-triggered Flow | Orchestration is unnecessary overhead |
| Long-running process with human and system work | Flow Orchestration | Stages, steps, and work items are the right abstraction |
| Process is mostly heavy integration and no human workflow | Apex or external orchestration | Flow Orchestration adds little value |
| Monitoring, reassignment, and stuck-instance handling are important | Flow Orchestration | Operational visibility is built into the model |


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] The use case genuinely requires long-running or multi-user process control.
- [ ] Stages represent real milestones and not arbitrary canvas grouping.
- [ ] Human steps have clear assignment, escalation, and completion ownership.
- [ ] Background steps are idempotent and fault-aware.
- [ ] Monitoring and intervention expectations were designed before launch.
- [ ] The team considered whether standard Flow or Apex would be simpler.

## Salesforce-Specific Gotchas

1. **Orchestration is not a better record-triggered flow by default** — it adds operational structure, which is useful only when the process truly spans time and users.
2. **Poor stage boundaries create monitoring noise** — if stages do not map to real milestones, work-item visibility becomes hard to act on.
3. **Interactive steps are operations work, not just UI** — assignment, backlog management, and reassignment need ownership from the start.
4. **Long-running processes still need failure design** — a stuck orchestration instance is an operational incident, not a cosmetic problem.

## Output Artifacts

| Artifact | Description |
|---|---|
| Orchestration fit assessment | Recommendation on whether Flow Orchestration is justified |
| Stage-and-step model | Proposed process milestones, work items, and background boundaries |
| Monitoring plan | Guidance on stuck-instance visibility, reassignment, and recovery |

## Related Skills

- `flow/fault-handling` — use when error-routing and recovery are the immediate concern inside a step or subflow.
- `admin/approval-processes` — use when the process is really about approval routing rather than broader orchestration.
- `apex/async-apex` — use when the system-work portions need more control than Flow should carry.
