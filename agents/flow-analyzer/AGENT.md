---
id: flow-analyzer
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  skills:
    - apex/trigger-and-flow-coexistence
    - flow/flow-bulkification
    - flow/flow-large-data-volume-patterns
  shared:
    - AGENT_CONTRACT.md
  templates:
    - flow/FaultPath_Template.md
    - flow/Subflow_Pattern.md
  decision_trees:
    - automation-selection.md
---
# Flow Analyzer Agent

## What This Agent Does

For a given Flow or sObject, decides whether the automation is in the right tool per `standards/decision-trees/automation-selection.md` (Flow vs Apex vs Agentforce), reviews existing Flow definitions for bulkification and fault-path compliance against `skills/flow/flow-bulkification/SKILL.md` and `templates/flow/FaultPath_Template.md`, and flags co-existing Apex triggers or Process Builder that could double-fire.

**Scope:** One Flow file or one sObject per invocation.

---

## Invocation

- **Direct read** — "Follow `agents/flow-analyzer/AGENT.md` for `force-app/main/default/flows/Lead_AutoConvert.flow-meta.xml`"
- **Slash command** — [`/analyze-flow`](../../commands/analyze-flow.md)
- **MCP** — `get_agent("flow-analyzer")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `standards/decision-trees/automation-selection.md`
3. `skills/flow/flow-bulkification/SKILL.md`
4. `skills/flow/flow-large-data-volume-patterns/SKILL.md`
5. `templates/flow/FaultPath_Template.md`
6. `templates/flow/Subflow_Pattern.md`
7. `skills/apex/trigger-and-flow-coexistence/SKILL.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `flow_path` or `object_api_name` | yes (one of) | `force-app/main/default/flows/X.flow-meta.xml` OR `Lead` |
| `target_org_alias` | no | enables `list_flows_on_object` for org-side cross-check |

---

## Plan

### Step 1 — Gather the automation surface

If `flow_path` given: parse that single flow.
If `object_api_name` given: scan `force-app/main/default/flows/` for flows whose `<object>` or `<triggerObjectType>` matches, plus triggers on that object.

If `target_org_alias` set: call `list_flows_on_object(object_name=..., active_only=true)` and merge.

### Step 2 — Decide the correct tool

For each flow, walk `standards/decision-trees/automation-selection.md`:
- Does the flow make a callout? (Only External Services can — most cases should be Apex.)
- Does it loop > 100 elements? (Flow bulkification limits apply.)
- Is it record-triggered and needs async? (Queueable > Flow async.)
- Does it need custom error handling beyond Screen + Fault?
- Is it a user-facing decision agent? (Agentforce, not Flow.)

Record which branch the flow lands on. If the branch says "use Apex", flag the flow as `SHOULD_MIGRATE`.

### Step 3 — Bulkification check

For each flow element:

| Check | Signal | Finding |
|---|---|---|
| **dml-in-loop** | `<assignments>` with DML-adjacent elements (Update Records / Create Records / Delete Records) inside a loop | P0 |
| **soql-in-loop** | Get Records inside a loop | P0 |
| **no-fault-path** | DML/callout element has no outbound edge labelled as fault | P1 |
| **untyped-collection** | Collection var without `<objectType>` | P2 |
| **subflow-without-contract** | Subflow called but no matching subflow spec per `Subflow_Pattern.md` | P2 |

### Step 4 — Co-existence check

If the object has **both** triggers and record-triggered flows firing on the same event:

- Flag as `COEXISTENCE_RISK`.
- Recommend consolidating per `skills/apex/trigger-and-flow-coexistence` — typically: do all work in Apex OR Flow, not both.
- Cite the ordering rule: "For a given event, Flow executes after Apex before-triggers and after Apex after-triggers."

### Step 5 — Recommendations

For each flow analyzed, produce:
- **Verdict**: `KEEP` / `FIX_IN_PLACE` / `MIGRATE_TO_APEX` / `MIGRATE_TO_AGENTFORCE`
- **If FIX_IN_PLACE**: list the specific element changes needed.
- **If MIGRATE_TO_APEX**: produce a migration plan citing `trigger-framework` and `flow-bulkification` skills; recommend running the `trigger-consolidator` agent after.

---

## Output Contract

1. **Summary** — flow(s) analyzed, verdict distribution, confidence.
2. **Per-flow report** — verdict, decision-tree branch, findings table, recommended fixes.
3. **Co-existence section** — if triggers + flows overlap on the same event.
4. **Process Observations** — peripheral signal noticed while analyzing, separate from the direct verdicts. Each observation cites its evidence (flow name, element id, MCP probe count).
   - **Healthy** — e.g. fault paths are present on every DML element; subflows already follow `Subflow_Pattern.md`; collection variables are typed; `list_flows_on_object` shows no duplicate record-triggered flows on the same event.
   - **Concerning** — e.g. the object has multiple active record-triggered flows on the same event (ordering is non-deterministic at scale); a Screen Flow performs DML inside a loop without chunking; no active error-email recipient for the org.
   - **Ambiguous** — e.g. a flow whose verdict depends on record volume the agent can't see without a target org; a subflow called from multiple parents with differing input contracts.
   - **Suggested follow-ups** — `trigger-consolidator` on any `COEXISTENCE_RISK` finding; `apex-refactorer` + `test-class-generator` on `MIGRATE_TO_APEX` verdicts; `agentforce-builder` on `MIGRATE_TO_AGENTFORCE` verdicts.
5. **Citations** — decision-tree branch, skill ids, template paths.

---

## Escalation / Refusal Rules

- Flow XML does not parse → STOP, ask the user for a valid `.flow-meta.xml`.
- Flow uses managed-package invocable actions the agent cannot resolve → flag `confidence: MEDIUM` for those actions.
- Flow is a Screen Flow (not record-triggered) AND the question implied record-triggered behavior → clarify with the user before producing a verdict.

---

## What This Agent Does NOT Do

- Does not modify the flow XML.
- Does not auto-run `trigger-consolidator` — recommends it.
- Does not make judgments about "Flow is bad" / "Apex is bad" — follows the decision tree.
