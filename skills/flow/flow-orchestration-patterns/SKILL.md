---
name: flow-orchestration-patterns
description: "Flow Orchestration design patterns — multi-stage, multi-step flows where each step is itself an autolaunched flow or a screen flow assigned to a user / queue, with Work Items appearing in users' inboxes for interactive steps. Covers the stage / step model, interactive vs background steps, evaluation flows that gate stage transitions, work-item assignment (running user / queue / formula-derived user), and the persistence model (orchestrations survive across days / weeks). NOT for the basic record-triggered or screen flow runtime (use flow/flow-best-practices), NOT for Approval Processes (different runtime, see admin/approval-process-design)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "flow orchestration multi-stage approval workflow"
  - "orchestration work item assigned user queue"
  - "evaluation flow stage transition gating"
  - "interactive step screen flow vs background autolaunched"
  - "orchestration long running multi-day persistence"
  - "orchestration stage exit criteria record condition"
tags:
  - flow
  - orchestration
  - work-item
  - stage
  - step
  - evaluation-flow
inputs:
  - "Process shape: linear (A → B → C), branching (A → either B or C), or parallel (A → B and C concurrently)"
  - "Whether each step is interactive (user takes action via Work Item) or background (autolaunched)"
  - "Stage exit criteria — what condition signals 'this stage done, move to next'"
  - "Assignee model — running user / specific user / queue / formula-derived"
  - "Time scale — minutes, hours, or multi-day"
outputs:
  - "Orchestration definition (stages + steps + connectors + evaluation flows)"
  - "Per-step assignee strategy"
  - "Stage exit criteria expressions"
  - "Work-item visibility model (where users see their assigned items)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-04
---

# Flow Orchestration Patterns

Flow Orchestration is the multi-stage version of Flow — a top-level
orchestration contains stages, each stage contains steps, and each
step is itself a flow (autolaunched for background work, screen flow
for interactive). Orchestrations are persistent: they survive across
days and weeks, with users picking up assigned Work Items from their
inbox, and the orchestration moves through stages as exit criteria
are met.

This is the answer for processes that span multiple humans /
multiple business days / multiple decision points — the kind of
process that used to be a Workflow Rule chain, an Approval Process,
or a confused mix of triggers and Process Builder. Orchestrations
make the multi-stage shape explicit.

What this skill is NOT. The basic Flow runtime (single-flow
execution semantics, governor limits per interview, fault paths)
lives in `flow/flow-best-practices`. Approval Processes are a
different runtime with their own UI and metadata — see
`admin/approval-process-design`. This skill is specifically about
the Orchestration metadata type and the patterns for assembling
multi-stage processes from it.

---

## Before Starting

- **Identify the process shape.** Linear (A → B → C, no branching)?
  Branching (A → either B or C based on a decision)? Parallel (A
  triggers both B and C, both must finish before D)? Each shape
  maps to different orchestration metadata.
- **Identify each step's nature.** Interactive (a user opens a Work
  Item and takes action via screen flow) vs Background (autolaunched
  flow that runs without user input). Mixing them is the rule, not
  the exception.
- **Decide stage exit criteria.** When does stage 1 end so stage 2
  begins? Default is "all steps in the stage completed". You can
  override with an evaluation flow that runs a record-condition
  check.
- **Decide the time scale.** Orchestrations can run for minutes
  (short-form approval) or weeks (employee onboarding). Long-running
  orchestrations have specific gotchas around flow definition
  changes, user deactivation, and Work Item retention.

---

## Core Concepts

### The orchestration / stage / step hierarchy

```
Orchestration (top-level metadata)
  │
  ├── Stage 1
  │     ├── Step 1A — Interactive (screen flow, assigned to <user/queue>)
  │     └── Step 1B — Background (autolaunched flow)
  │
  ├── Stage 2 (gated by Stage 1 completion + optional evaluation flow)
  │     ├── Step 2A — Interactive
  │     └── Step 2B — Interactive
  │
  └── Stage 3
        └── Step 3 — Background
```

A stage's steps run in parallel by default. A stage completes when
all its steps are done. Stages run sequentially.

### Interactive vs background steps

| Step type | Runs as | Visible to user? | Use case |
|---|---|---|---|
| **Interactive** | Screen flow assigned to a user / queue | Work Item in the assignee's inbox | Approval click, form fill, document review |
| **Background** | Autolaunched flow, runs to completion | Invisible | Field updates, notifications, system integration |

Mixing within a stage is normal. A "Wait for VP approval" stage
might have an Interactive step (the VP's Work Item) AND a Background
step (a notification Apex callout to a downstream system). Both run
in parallel; stage completes when both finish.

### Evaluation flows for stage transitions

The default rule "stage completes when all its steps are done" works
for most orchestrations. When you need additional gating (e.g.
"stage completes only if the record's status is now 'Approved'"),
attach an **evaluation flow** to the stage's exit. The evaluation
flow runs at exit-attempt time; it returns true/false, and the stage
transitions only on true.

Evaluation flows are autolaunched flows that take the orchestration's
context (record Id, custom variables) and return a Boolean output.
They run quickly (no user interaction) and can re-check the source
record's state — important for orchestrations spanning days where
the record may have been updated outside the orchestration.

### Work Item assignment

Each interactive step has an assignee. Salesforce supports four
assignment models:

| Model | Configuration | Use case |
|---|---|---|
| **Running user** | Default — whoever started the orchestration | Self-service flows |
| **Specific user** | Hardcoded user reference | Small-team / single-approver flows |
| **Queue** | Queue reference; any queue member can claim | Workload-balanced approvals |
| **Formula-derived** | Expression evaluating to a user Id | Manager-of-running-user, region-VP-from-record-field |

Formula-derived is the most powerful and most error-prone — if the
formula returns null or an inactive user, the step is stuck.

### Persistence and the long-running gotcha

Orchestrations are **persistent** across days. The orchestration
state is stored on the platform; users pick up Work Items from their
inbox at their pace. This is the feature.

The cost: long-running orchestrations are sensitive to changes in
the underlying flow definitions. A screen flow that's modified
between when a Work Item was created and when the user opens it may
present a different UI than the orchestration originally
specified — at best confusing, at worst broken (if the flow's input
variables changed shape). Salesforce versions flow definitions, but
the version-binding behavior for in-flight orchestrations isn't
always intuitive.

---

## Common Patterns

### Pattern A — Linear approval chain

**When to use.** Document review process: Author submits → Manager
reviews → VP approves → Document marked Final.

```
Orchestration: Document_Approval
  Stage 1: Submission
    Step: Mark Submitted (Background — sets status, fires notification)
  Stage 2: Manager Review
    Step: Manager Review Work Item (Interactive — assigned to author's manager via formula)
  Stage 3: VP Approval
    Step: VP Approval Work Item (Interactive — assigned to manager's manager)
  Stage 4: Finalize
    Step: Mark Final (Background — sets status to Final, archives)
```

Each stage's exit criteria: default (all steps complete). No
evaluation flow needed.

### Pattern B — Branching approval based on amount threshold

**When to use.** Expense approval where small expenses skip
VP-level approval.

```
Orchestration: Expense_Approval
  Stage 1: Manager Review
    Step: Manager Review Work Item
    Exit evaluation flow: returns true (always — manager always reviews)

  Stage 2: VP Review (conditional)
    Step: VP Review Work Item
    Entry condition: orchestration variable Amount > 10000

  Stage 3: Finalize (always)
    Step: Mark Approved (Background)
```

Stage 2 is gated by an entry condition; small expenses skip directly
to Stage 3. The orchestration metadata supports this via stage-level
conditions.

### Pattern C — Parallel steps with mixed interactive + background

**When to use.** Onboarding: when employee starts, simultaneously
provision their accounts (background) AND have HR collect their
documents (interactive).

```
Orchestration: Employee_Onboarding
  Stage 1: Day 1
    Step 1A: Provision Accounts (Background — Apex action calls IDP)
    Step 1B: HR Document Collection (Interactive — assigned to HR queue)
    Step 1C: Slack Welcome (Background — Slack webhook action)

  Stage 2: Week 1 Training
    Step 2: Mandatory Training Work Item (Interactive — assigned to running user)
```

Stage 1 has three parallel steps; stage completes when all three
finish. The HR document step is the long pole; provisioning and
Slack happen in seconds.

### Pattern D — Long-running orchestration with re-evaluation gate

**When to use.** Multi-week process where the underlying record's
state may change outside the orchestration (case escalation, opp
loss, employee termination).

**Approach.** Add an evaluation flow at every stage's exit that
re-checks the source record's state. If the record is in a
terminal state (case closed, opp lost), the evaluation flow
returns false, the orchestration is held — admins decide whether to
cancel or resume.

The evaluation flow's output drives a side-decision: log the
state-mismatch to a custom object, optionally email an admin, hold
the orchestration.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| Single-decision approval (one user clicks Approve) | **Approval Process** OR single-stage orchestration with one interactive step | Approval Process is older but simpler; orchestration is overkill for single-step |
| Multi-stage process with > 2 humans involved | **Orchestration** Pattern A or B | Orchestration's stage / step model is built for this |
| Branching based on record condition | **Pattern B** with stage entry conditions | Skip stages that don't apply |
| Parallel work in a single stage | **Pattern C** with mixed interactive + background | Default parallel-within-stage is the right shape |
| Long-running with possible record-state change | **Pattern D** with evaluation flows on every stage exit | Re-check at each stage boundary |
| Single user does everything sequentially | **Screen flow with multiple screens** | Don't reach for orchestration when one flow with one user fits |
| Background-only (no human interaction) | **Autolaunched flow chain** | Orchestration's stage model is overhead with no benefit |
| Stage step assigned to "the manager of the manager" | **Formula-derived** assignee | Documented as a recognized pattern; test for null managers |
| Need to cancel an in-flight orchestration | **Run an autolaunched flow that completes the current step + skips the rest** | No direct cancel UI; orchestration must be designed with a cancel pathway |

---

## Recommended Workflow

1. **Decide if orchestration is the right shape.** Multi-stage, multi-human, multi-day → yes. Single user, single decision → screen flow. No human → autolaunched flow chain.
2. **Map the stages.** What's the meaningful business milestone at the end of each stage?
3. **Per stage, list the steps.** Interactive (user takes action) vs background (system runs). Steps within a stage run in parallel.
4. **For each interactive step, decide the assignee model.** Running user / specific user / queue / formula-derived. Document the formula and test the null case.
5. **For each stage, decide if an evaluation flow is needed.** Default is "all steps complete = stage complete"; add evaluation flow when additional gating is required.
6. **Plan the cancel pathway.** Orchestrations have no direct cancel UI; design an admin-pathway from the start.
7. **Test the long-running case.** Save an in-flight orchestration; modify a referenced flow definition; verify the orchestration still resumes correctly.

---

## Review Checklist

- [ ] Process shape (linear / branching / parallel) is named explicitly.
- [ ] Each step is classified Interactive or Background.
- [ ] Each interactive step's assignee model is documented (running user / specific / queue / formula).
- [ ] Formula-derived assignees handle the null / inactive-user case.
- [ ] Stage exit criteria are explicit (default vs evaluation flow).
- [ ] Long-running orchestrations have a re-evaluation gate that re-checks source record state.
- [ ] Cancel pathway exists (no orchestration without a documented exit-from-mistake plan).
- [ ] Work-item visibility — users know where to find their assigned items.
- [ ] Test plan covers the rare-but-real cases: assignee deactivation, source record change mid-orchestration, flow definition update.

---

## Salesforce-Specific Gotchas

1. **No direct cancel UI for in-flight orchestrations.** Cancel pathway must be designed in. (See `references/gotchas.md` § 1.)
2. **Formula-derived assignee returning null leaves the step stuck.** Add fallback logic. (See `references/gotchas.md` § 2.)
3. **Modifying a screen-flow definition referenced by an in-flight Work Item** can cause confusing UI / errors at resume time. (See `references/gotchas.md` § 3.)
4. **Inactive user as assignee** — Work Item is created but the user can't open it. (See `references/gotchas.md` § 4.)
5. **Stages run sequentially, steps within a stage run in parallel** — confusing this produces ordering bugs. (See `references/gotchas.md` § 5.)
6. **Background steps don't surface errors to users** — fault path + admin notification is required (see `flow/flow-error-notification-patterns`). (See `references/gotchas.md` § 6.)
7. **Evaluation flows that throw exceptions hold the orchestration** — they don't fall through to stage completion. (See `references/gotchas.md` § 7.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Orchestration metadata | The top-level orchestration with stages, steps, connectors, evaluation flows |
| Per-step flow definitions | Each interactive / background step is a separate flow file |
| Assignee documentation | Per interactive step, the model + fallback for null/inactive |
| Cancel pathway | Documented admin-action that cleans up in-flight orchestrations |
| Test plan | Long-running, mid-orchestration record change, assignee deactivation |

---

## Related Skills

- `flow/flow-best-practices` — single-flow runtime; orchestration uses these flows as building blocks.
- `flow/flow-error-notification-patterns` — background-step errors need fault paths and admin notification.
- `flow/flow-time-based-patterns` — Wait elements inside individual orchestration step flows; Scheduled Paths for delays between stages.
- `admin/approval-process-design` — the older single-step-approval mechanism; consult if the requirement is genuinely single-step.
