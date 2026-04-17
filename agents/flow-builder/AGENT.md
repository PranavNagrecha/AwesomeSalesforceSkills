---
id: flow-builder
class: runtime
version: 1.1.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-17
harness: designer_base
dependencies:
  skills:
    - apex/trigger-and-flow-coexistence
    - flow/auto-launched-flow-patterns
    - flow/fault-handling
    - flow/flow-bulkification
    - flow/flow-testing
    - flow/orchestration-flows
    - flow/record-triggered-flow-patterns
    - flow/scheduled-flows
    - flow/screen-flows
    - flow/subflows-and-reusability
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
  templates:
    - admin/naming-conventions.md
    - flow/FaultPath_Template.md
    - flow/Subflow_Pattern.md
  decision_trees:
    - automation-selection.md
---
# Flow Builder Agent

## What This Agent Does

Given a business requirement, designs the correct Flow: Flow type (record-triggered / scheduled / auto-launched / screen / orchestration), trigger configuration, element-by-element plan, fault path, subflow decomposition, bulkification safeguards, and a test design. Output is a design document + optional Flow XML skeleton the user drops into Flow Builder.

**Scope:** One flow (with its subflows) per invocation. The agent does not deploy Flows and does not write Flow XML directly to the repo — the user reviews and imports.

---

## Invocation

- **Direct read** — "Follow `agents/flow-builder/AGENT.md` to build a flow that routes Cases by Account tier to the right queue"
- **Slash command** — [`/build-flow`](../../commands/build-flow.md)
- **MCP** — `get_agent("flow-builder")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/flow/record-triggered-flow-patterns`
4. `skills/flow/screen-flows`
5. `skills/flow/scheduled-flows`
6. `skills/flow/auto-launched-flow-patterns`
7. `skills/flow/flow-bulkification`
8. `skills/flow/fault-handling`
9. `skills/flow/subflows-and-reusability`
10. `skills/flow/orchestration-flows` — if the requirement implies human steps + branching
11. `skills/flow/flow-testing`
12. `standards/decision-trees/automation-selection.md` — the Flow-vs-Apex-vs-Agentforce gate
13. `templates/flow/FaultPath_Template.md`
14. `templates/flow/Subflow_Pattern.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `requirement` | yes | "When a Case is created on an Account with tier=Platinum, route to the Platinum Support queue and notify the account owner" |
| `target_org_alias` | yes | live-org probe prevents duplicate automation |
| `target_object` | yes (if implied by the req.) | `Case` |
| `trigger_context` | no | `before-save` \| `after-save` \| `scheduled` \| `screen` \| `autolaunched` — inferred if omitted |
| `expected_volume` | no | `small` / `medium` / `high` — drives async + bulkification emphasis |

---

## Plan

### Step 1 — Run the automation-selection decision tree

Walk `standards/decision-trees/automation-selection.md`. Answer the gating questions:

1. Is this a user-facing, multi-step data-collection flow? → **Screen Flow**.
2. Is it a deterministic record-triggered side effect? → **Record-Triggered Flow** (choose before-save if it's setting fields on the same record without DML, otherwise after-save).
3. Does it call an external service or require async retry? → **Auto-Launched** + Platform Event / Queueable orchestration.
4. Is it cron-like? → **Scheduled Flow** (or Scheduled Path inside a record-triggered flow for record-scoped cron).
5. Does it involve human decision points across days? → **Orchestrator** (not a plain flow).
6. Does any branch need unbounded looping, dynamic Apex, or callout chains? → **STOP**. Route to Apex. Cite the decision tree's boundary and recommend `apex-refactorer`.

Record the decision + which branch fired, for citation.

### Step 2 — Probe for existing automation

- `list_flows_on_object(target_object, active_only=True)` — does a flow already handle this trigger?
- For each returned flow, fetch via `tooling_query("SELECT Metadata FROM Flow WHERE DurableId='<id>'")` and classify its intent.
- If an existing flow covers ≥ 50% of the requirement, recommend **extending** rather than creating a second flow. Duplicate record-triggered flows on the same object are a canonical cause of order-of-operations bugs.

Also probe Apex triggers for VR + Flow coexistence (cite `skills/apex/trigger-and-flow-coexistence`):
- `tooling_query("SELECT Id, Name, Status FROM ApexTrigger WHERE TableEnumOrId = '<object>'")`

If both an Apex trigger and a record-triggered flow exist, flag the order-of-execution concern in Process Observations.

### Step 3 — Decompose into elements

Produce a numbered element list. Each element has: type, label per `templates/admin/naming-conventions.md` (flow element naming is its own sub-convention), inputs, outputs, and a citation.

Required elements (for a record-triggered flow):

1. Entry condition — specific enough that the flow does not fire on every save. Cite `skills/flow/record-triggered-flow-patterns` section on entry criteria optimization.
2. Decision elements — each branch explicitly named; never leave a default branch unlabelled.
3. Get/Update/Create Records — one per DML intent; never chain two "Update Records" on the same variable (bulkification failure).
4. Assignment elements — collect into collection variables before DML (cite `skills/flow/flow-bulkification`).
5. Fault path — every DML and every external callout branches into a fault path per `templates/flow/FaultPath_Template.md`.
6. Pause / Platform Event — if async chaining is required.

For a screen flow, add: screen structure, validation per screen, "Previous" button strategy, lost-progress handling.

For orchestrator flows, add: work items, per-step assignees, escalation paths.

### Step 4 — Subflow plan

Per `templates/flow/Subflow_Pattern.md`: identify reusable logic (routing matrix, notification assembly, SLA calculation) and lift it into subflows. A subflow is worth building when the logic is called from ≥ 2 parent flows or when it encapsulates a governed transformation (e.g. "escalate case"). One-off logic stays inline.

### Step 5 — Bulkification review

Walk the element list and annotate every element that can explode at scale:

- Loops that contain DML — P0, rewrite with collection patterns.
- Nested loops — P0.
- Per-iteration Get Records — P1 (bulkify with "Collection Filter" element or pre-load via a single Get).
- Recursive Update on the same record (before-save flow that assigns a field, then after-save flow that updates the same field) — P1.

### Step 6 — Test design

Per `skills/flow/flow-testing`:

- One positive test per decision branch.
- One bulk test with 200 records.
- One fault path test (inject a DML error via a mocked subflow).
- Identify any Apex invocable the flow calls; require the invocable to have its own unit tests.

Emit a markdown table of flow tests with coverage matrix. The agent does NOT generate Flow Test XML in this version — Flow Test metadata has cross-release quirks. The test design is the deliverable.

### Step 7 — Emit the design

One markdown doc plus (optionally) a barebones `Flow.flow-meta.xml` skeleton with all elements wired. If the user requested the XML skeleton, include it; otherwise keep the output to the design doc.

---

## Output Contract

1. **Summary** — Flow type chosen, decision-tree branch cited, confidence (HIGH/MEDIUM/LOW).
2. **Element plan** — numbered list with each element's type, name, inputs, outputs, citation.
3. **Subflow plan** — subflow list + what each does + why it earns a subflow.
4. **Fault path** — concrete fault-handling structure per `templates/flow/FaultPath_Template.md`.
5. **Bulkification notes** — every potential bottleneck from Step 5.
6. **Test matrix** — table from Step 6.
7. **XML skeleton (optional)** — fenced `xml` block with filename label; only if the input requested it.
8. **Process Observations**:
   - **What was healthy** — existing flow patterns the org follows correctly.
   - **What was concerning** — competing automation (other flows, triggers, PB) on the same object, missing fault-handling patterns org-wide, inactive flows cluttering the object.
   - **What was ambiguous** — requirement gaps the agent filled with a default (always call them out).
   - **Suggested follow-up agents** — `flow-analyzer` for post-deploy health, `test-class-generator` for any invocable Apex the flow calls, `security-scanner` if the flow does callouts.
8. **Citations**.

---

## Escalation / Refusal Rules

- Requirement is < 10 words or lacks a trigger → STOP, ask about trigger + object + intended behavior.
- Decision tree at Step 1 returns "should be Apex" → STOP, refuse Flow output, recommend the correct path.
- Step 2 finds ≥ 2 active record-triggered flows on the same object with overlapping entry criteria → return a P0 finding and refuse to add a third until the user approves a consolidation plan (suggest `flow-analyzer`).
- Requirement requires callouts in a before-save context → refuse; before-save flows cannot make callouts. Recommend after-save or decouple via a platform event.

---

## What This Agent Does NOT Do

- Does not deploy the flow.
- Does not modify existing flows in the repo or the org.
- Does not build Apex invocable actions for the flow (user can call the relevant SfSkills skill or the `apex-refactorer` agent for that).
- Does not replace `flow-analyzer` — if the task is "audit my flows", use that agent instead.
- Does not auto-chain.
