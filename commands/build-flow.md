# /build-flow — Design a Flow (any type) from a business requirement

Wraps [`agents/flow-builder/AGENT.md`](../agents/flow-builder/AGENT.md). Returns the Flow type decision, element plan, subflow plan, fault path, bulkification notes, and test matrix.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Requirement (plain English, one or two sentences)?
   Example: "When a Case is created on a Platinum-tier Account, route to the Platinum Support queue and notify the account owner"

2. Target object (if implied by the requirement)?
   Example: Case

3. Target org alias (required — agent checks for existing automation)?

4. Trigger context (optional)?
   before-save / after-save / scheduled / screen / autolaunched
   (Inferred from the requirement if omitted)

5. Expected volume (optional)?
   small / medium / high (drives bulkification emphasis)

6. Include the Flow XML skeleton in the output? yes / no
   (Default: no — design doc only)
```

---

## Step 2 — Load the agent

Read `agents/flow-builder/AGENT.md` + mandatory reads, especially `standards/decision-trees/automation-selection.md` (the Flow-vs-Apex-vs-Agentforce gate).

---

## Step 3 — Execute the plan

1. Run the automation-selection decision tree — may route to a different tool entirely
2. Probe for existing automation (`list_flows_on_object`, `tooling_query` on ApexTrigger)
3. Decompose into elements
4. Subflow plan
5. Bulkification review
6. Test design
7. Emit the design

---

## Step 4 — Deliver the output

- Summary (Flow type chosen + confidence)
- Element plan (table)
- Subflow plan
- Fault path
- Bulkification notes
- Test matrix
- XML skeleton (only if requested)
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/analyze-flow` (existing Wave-1 agent) after the flow is deployed
- `/gen-tests` (existing) for any invocable Apex the flow calls
- `/scan-security` (existing) if the flow does callouts
- `/audit-validation-rules` if the agent flagged VR-vs-flow conflicts

---

## What this command does NOT do

- Does not deploy the flow.
- Does not modify existing flows.
- Does not build invocable Apex actions (use `/refactor-apex` or the relevant SfSkills skill directly).
- Does not replace `/analyze-flow` for audit workloads.
