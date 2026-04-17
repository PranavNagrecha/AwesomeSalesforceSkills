# /design-flow-orchestrator — Design or audit a Flow Orchestration

Wraps [`agents/flow-orchestrator-designer/AGENT.md`](../agents/flow-orchestrator-designer/AGENT.md). Produces stages, steps, work-item assignees, interactive/background step mix, transition criteria, and restart/recall behavior.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Mode? design | audit

2. Target org alias (required — agent probes existing Orchestrations + referenced subflows)?

3. Workflow description (for design)?
   Example: "3-stage contract review with legal, procurement, and customer sign-off"

4. Assignees per stage? (user | group | queue | formula-driven)

5. Restart / recall requirements?

6. SLA per stage (if any)?
```

If the description has fewer than 2 stages, STOP — this is a single Flow, not an Orchestration.

---

## Step 2 — Load the agent

Read `agents/flow-orchestrator-designer/AGENT.md` + mandatory reads (flow/orchestration-flows, flow/subflows-and-reusability, flow/screen-flows).

---

## Step 3 — Execute the plan

- Classify as Flow vs Orchestration (per standards/decision-trees/automation-selection.md).
- Decompose into stages.
- For each stage: steps, assignees, interactive/background mix, transitions.
- Map each step to an existing subflow or a new one.
- Emit restart/recall + cancellation semantics.

---

## Step 4 — Deliver the output

- Summary + confidence
- Stage/step diagram (mermaid)
- Per-step assignee + type
- Subflow mapping
- Restart/recall/cancellation behavior
- Audit findings (inactive stages, orphaned subflows, missing fault paths)
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/build-flow` for each subflow that doesn't yet exist
- `/analyze-flow` on the referenced subflows before deploying
- `/architect-perms` if orchestration runs as different user contexts

---

## What this command does NOT do

- Does not deploy Orchestrations.
- Does not build the screen flows / subflows referenced.
- Does not replace BPM platforms — flags when the requirement outgrows Orchestration.
