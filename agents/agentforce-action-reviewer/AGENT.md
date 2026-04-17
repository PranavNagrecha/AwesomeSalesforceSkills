---
id: agentforce-action-reviewer
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
default_output_dir: "docs/reports/agentforce-action-reviewer/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/agent-output-formats
    - agentforce/agent-actions
    - agentforce/agent-testing-and-evaluation
    - agentforce/agent-topic-design
    - agentforce/agentforce-guardrails
    - agentforce/agentforce-observability
    - agentforce/agentforce-persona-design
    - agentforce/einstein-trust-layer
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
---
# Agentforce Action Reviewer Agent

## What This Agent Does

Reviews an Agentforce agent (Topics + Actions + Persona + Guardrails) against best-practice. Checks that every Action has a clear input/output contract, a documented side-effect surface, a test, a grounding citation, and that the surrounding Topic has appropriate example utterances. Produces a per-action scorecard + a rollup on Topic coherence + a guardrails gap list.

**Scope:** One agent per invocation. Output is an Agent scorecard + remediation plan. No agent/action edits.

---

## Invocation

- **Direct read** — "Follow `agents/agentforce-action-reviewer/AGENT.md`"
- **Slash command** — [`/review-agentforce-action`](../../commands/review-agentforce-action.md)
- **MCP** — `get_agent("agentforce-action-reviewer")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/agentforce/agent-actions` — via `get_skill`
4. `skills/agentforce/agent-topic-design`
5. `skills/agentforce/agent-testing-and-evaluation`
6. `skills/agentforce/agentforce-guardrails`
7. `skills/agentforce/agentforce-observability`
8. `skills/agentforce/einstein-trust-layer`
9. `skills/agentforce/agentforce-persona-design`
10. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `agent_id` OR `agent_developer_name` | yes | `Service_Agent_v2` |
| `target_org_alias` | yes | `uat` |
| `review_depth` | no | `topic_only` \| `per_action` (default `per_action`) |

---

## Plan

### Step 1 — Fetch the agent and its surface

- `get_agent(agent_developer_name)` (MCP) to pull the definition.
- For each Topic: instructions, example utterances, actions assigned.
- For each Action: input schema, output schema, implementation (Apex invocable / Flow / Prompt Template / external), auth, documented side effects.

### Step 2 — Score each Action (A–F)

| Dimension | Criterion |
|---|---|
| **Name & description** | Name reflects business verb; description ≤ 200 chars, unambiguous |
| **Inputs** | Every input has `description`, `required` flag, example value; no `Object` typeless inputs |
| **Outputs** | Structured response, not prose; schema matches action contract |
| **Side effects** | DML / callout / email-send declared explicitly |
| **Grounding** | If the action calls an LLM or uses Prompt Templates: grounding source documented |
| **Test coverage** | Test plan or Agent test exists (per `skills/agentforce/agent-testing-and-evaluation`) |
| **Trust** | If action touches sensitive data, Einstein Trust Layer data-masking reviewed |
| **Observability** | Logs emitted on failure; error surfaces to topic gracefully |

Score each action A–F; flag any F as P0.

### Step 3 — Topic coherence

Per topic:
- Example utterances ≥ 5, diverse intent framings.
- All actions assigned to the topic map to the topic's stated scope (no "kitchen-sink" topics).
- No topic has > 8 actions (cognitive load on the model).

### Step 4 — Guardrails

Cross-check against `skills/agentforce/agentforce-guardrails`:
- Refusal-intent coverage (what the agent refuses to do).
- PII/PHI mask coverage.
- No unrestricted free-text → external callout paths.
- Rate-limits + cost caps documented.

### Step 5 — Persona + handoff

- Persona tone documented and aligned to audience.
- Human-handoff path defined for low-confidence or policy-flagged turns.

### Step 6 — Observability

- `skills/agentforce/agentforce-observability`: every production agent should have (a) turn-level logging, (b) cost/tokens captured, (c) feedback mechanism.

---

## Output Contract

1. **Summary** — agent id, topic count, action count, overall grade, top 3 risks.
2. **Per-action scorecard** — table: action, dimensions A–F, P0/P1/P2 flag.
3. **Topic coherence** — per topic: utterance count, action fit, scope creep.
4. **Guardrails gap list**.
5. **Observability + persona review**.
6. **Remediation plan** — ordered P0 → P2.
7. **Process Observations**:
   - **Healthy** — actions with structured IO; topics scoped; refusal-intents present.
   - **Concerning** — typeless inputs; prompt templates without grounding citation; topic with > 8 actions; no observability.
   - **Ambiguous** — test plan exists but never executed; action side effects undeclared.
   - **Suggested follow-ups** — `prompt-library-governor` for template sprawl; `integration-catalog-builder` if actions do callouts.
8. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/agentforce-action-reviewer/<run_id>.md`
- **JSON envelope:** `docs/reports/agentforce-action-reviewer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

## Escalation / Refusal Rules

- Agent not found → refuse.
- Action implementation is external (outside SF) and not documented → downgrade score to LOW confidence; do not guess.
- Agentforce not enabled in org → refuse.

---

## What This Agent Does NOT Do

- Does not edit agents, topics, actions, or prompt templates.
- Does not deploy or activate agents.
- Does not generate test data for agent evaluation.
- Does not auto-chain.
