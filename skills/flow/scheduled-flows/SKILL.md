---
name: scheduled-flows
description: "Use when designing or reviewing schedule-triggered flows for recurring automation, replacement of time-based workflow patterns, bounded record selection, idempotent processing, and escalation to Apex when volume is too high. Triggers: 'scheduled flow design', 'nightly flow job', 'time based workflow replacement', 'schedule triggered flow limits'. NOT for record-triggered scheduled paths or large-scale batch processing that should be built directly in Batch Apex."
category: flow
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Scalability
  - Reliability
tags:
  - scheduled-flows
  - schedule-triggered
  - recurring-automation
  - idempotency
  - batch-apex-boundary
triggers:
  - "when should i use a scheduled flow"
  - "nightly automation with schedule triggered flow"
  - "scheduled flow versus batch apex"
  - "time based workflow replacement with flow"
  - "scheduled flow volume and retry design"
inputs:
  - "what recurrence is needed and whether the record set can be bounded tightly"
  - "how much data the flow will inspect or mutate on each run"
  - "what should happen on rerun, partial failure, or duplicate processing"
outputs:
  - "scheduled-flow design for record selection, processing, and escalation boundaries"
  - "review findings for unbounded scope, weak retry behavior, and volume risk"
  - "guidance on when to stay in Flow versus move heavy work to Apex"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-15
---

Use this skill when automation needs to run on a recurring cadence rather than directly from a record event. Schedule-triggered flows work well for bounded recurring tasks such as reminders, renewals, or cleanup logic. They become risky when teams treat them like a general-purpose batch engine and let the record scope or side effects grow without discipline.

---

## Before Starting

Gather this context before working on anything in this domain:

- What recurrence is required, and is the automation tied to a business calendar or to a record event that might fit a scheduled path better?
- How many records could match the criteria on a normal day, and what is the worst-case volume during seasonal or data-load spikes?
- How will the flow avoid duplicate work if it runs again, partially fails, or overlaps with another automation?

---

## Core Concepts

The core design problem in scheduled flows is not the schedule itself. It is bounded scope plus repeat-safe behavior. A recurring automation that cannot explain which records it will touch, why it will touch them only once when appropriate, and when it should escalate out of Flow is not ready for production.

### Choose The Right Time Primitive

If the automation is driven by a record event and only needs delayed follow-up, a scheduled path in a record-triggered flow may be the better fit. A schedule-triggered flow is stronger when the system needs a periodic scan of records that match time-based criteria independently of a recent save event.

### Bounded Selection Comes First

The start criteria should narrow the job to a realistic set of records. Wide-open scans with complex branching downstream create both performance risk and support ambiguity. Good scheduled flows have clear filters, explicit stop conditions, and a manageable result set per run.

### Idempotency Matters In Recurring Automation

A recurring flow should be able to answer whether a record has already been processed for this job window. Fields such as last-reminded date, processed flag, or status transition markers help prevent duplicate tasks, duplicate emails, and repeated updates on every run.

### Flow Is Not Always The Final Execution Engine

When the recurring job becomes large, computationally heavy, or deeply iterative, the right answer may be to use the scheduled flow only as a lightweight orchestration layer or move the workload into Batch Apex entirely. The schedule does not justify using the wrong execution model.

---

## Common Patterns

### Narrow Nightly Follow-Up Flow

**When to use:** The org needs a recurring reminder or status update on a bounded slice of records.

**How it works:** Filter narrowly at start, use idempotent fields to avoid duplicate work, and keep the side effects straightforward.

**Why not the alternative:** A broad nightly sweep without clear selection rules becomes unpredictable and expensive.

### Scheduled Flow As Lightweight Orchestrator

**When to use:** The timing belongs in Flow, but the heavy work should happen elsewhere.

**How it works:** Use the scheduled flow to identify the relevant records or business window, then hand off heavier work to Apex or another supported boundary.

**Why not the alternative:** Forcing Flow to do deep batch-style work creates scale and maintainability problems.

### Replace Time-Based Workflow With Explicit Criteria

**When to use:** A legacy automation relied on time-based behavior and is being moved into Flow.

**How it works:** Rebuild the timing logic with clear filters, processing markers, and failure handling instead of copying the legacy behavior blindly.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Recurring job scans a bounded set of records daily or weekly | Schedule-triggered flow | Good fit for predictable recurring automation |
| Follow-up is tied to a specific record save event | Scheduled path on record-triggered flow | The trigger is event-based, not portfolio-wide |
| Job volume or processing complexity is very high | Batch Apex or another async code boundary | Flow is not the best execution engine for heavy batch work |
| Repeated reminders or status nudges need duplicate prevention | Add idempotent markers or date fields | Recurring runs must know what has already been processed |
| Selection criteria are vague or unbounded | Redesign before scheduling | The schedule will amplify poor scope decisions |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The schedule primitive is correct for the business need.
- [ ] Start criteria narrow the candidate record set intentionally.
- [ ] Idempotent markers prevent duplicate tasks, emails, or updates.
- [ ] Failure handling exists for actions, subflows, or external steps.
- [ ] Volume expectations were reviewed for normal and worst-case runs.
- [ ] Heavy work was escalated out of Flow when appropriate.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **A recurring schedule amplifies weak selection logic** - broad filters turn into repeated large jobs quickly.
2. **Recurring automation needs duplicate prevention explicitly** - without markers, the same records can be processed on every run.
3. **Scheduled flows are not a substitute for true batch architecture** - the timing may fit, while the execution model does not.
4. **A record-event requirement may fit scheduled paths better** - choosing the wrong time primitive creates unnecessary complexity.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Scheduling design | Recommendation for schedule-triggered flow, scheduled path, or Apex |
| Scope and idempotency plan | Rules for bounded selection and duplicate prevention |
| Volume review findings | Risks around record set size, side effects, and execution model choice |

---

## Related Skills

- `flow/flow-bulkification` - use when the recurring job may still break under shared limit pressure.
- `apex/batch-apex-patterns` - use when the workload has clearly crossed into true batch-processing territory.
- `flow/fault-handling` - use when the main challenge is how background failures should be surfaced and handled.
