# /decide-salesforce — Compare viable Salesforce options with evidence, hard gates, sensitivity, and reversibility

Wraps [`agents/salesforce-decision-facilitator/AGENT.md`](../agents/salesforce-decision-facilitator/AGENT.md). The command produces a recommendation or experiment/defer/no-change posture; it does not approve or implement the choice.

---

## Step 1 — Collect inputs

Require:

```text
1. What single decision must be made?
2. What measurable outcome must the winning option achieve?
3. What are the hard constraints, preferences, and non-goals?
```

Collect when available: known options, target org/project/release/workload, data volume, evidence, weights, deadline, source boundary, and stopping point (`recommendation`, `experiment-plan`, or `adr-ready`).

Refuse or split the run when the request contains multiple independent decisions. Do not require an org for a conceptual decision; never guess one when org state changes feasibility.

---

## Step 2 — Load the agent

Read `agents/salesforce-decision-facilitator/AGENT.md` and every Mandatory Read. Validate inputs against `agents/salesforce-decision-facilitator/inputs.schema.json`.

---

## Step 3 — Execute the decision lifecycle

1. Frame one decision and route through the narrowest decision tree/specialist skill.
2. Build the evidence ledger and viable options.
3. Apply hard gates before weighted scoring.
4. Test weight/evidence sensitivity, risk, and reversibility.
5. Return `recommend`, `conditional-recommend`, `experiment`, `defer`, `no-change`, or `refuse`.

Capture every consulted skill, tree, source, target evidence item, and MCP tool in the envelope.

---

## Step 4 — Deliver the output

Conform to `agents/_shared/DELIVERABLE_CONTRACT.md`:

- Markdown: `docs/reports/salesforce-decision-facilitator/<run_id>.md`
- JSON: `docs/reports/salesforce-decision-facilitator/<run_id>.json`
- Atomic pair, short chat confirmation, and fenced JSON envelope preview
- `--no-persist` allowed for an exploratory run

The report includes the decision frame, routing record, evidence ledger, options, gates, weighted matrix, sensitivity, risks, recommendation, validation actions, and optional ADR handoff.

---

## Step 5 — Recommend one follow-up

After a human accepts the choice, recommend `architect/architecture-decision-records`. When evidence remains load-bearing, recommend the single validation experiment or specialist analysis that resolves it first.

---

## What this command does NOT do

- Does not deploy, mutate, activate, assign, approve, or execute Salesforce changes.
- Does not invent target-org state, licenses, volume, weights, or evidence.
- Does not replace a narrow canonical decision tree with a generic matrix.
- Does not mark an ADR Accepted or chain another agent automatically.
