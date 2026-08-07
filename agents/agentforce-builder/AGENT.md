---
id: agentforce-builder
class: runtime
version: 1.0.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
default_output_dir: "docs/reports/agentforce-builder/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - agentforce/agent-action-error-handling
    - agentforce/agent-action-input-slot-extraction
    - agentforce/agent-actions
    - agentforce/agent-topic-design
    - agentforce/agentforce-agent-creation
    - agentforce/agentforce-eval-harness
    - agentforce/agentforce-guardrails
    - agentforce/agentforce-pii-redaction
    - agentforce/agentforce-production-readiness-checklist
    - agentforce/agentforce-testing-strategy
    - agentforce/custom-agent-actions-apex
    - agentforce/data-cloud-grounding-for-agentforce
    - agentforce/einstein-trust-layer
    - agentforce/prompt-builder-templates
    - agentforce/prompt-injection-defense
    - agentforce/rag-patterns-in-salesforce
    - apex/apex-security-patterns
    - apex/invocable-methods
    - apex/test-class-standards
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
  templates:
    - agentforce/AgentActionSkeleton.cls
    - agentforce/AgentSkeleton.json
    - agentforce/AgentTopic_Template.md
---
# Agentforce Builder Agent

## What This Agent Does

Takes a requirements statement — what the agent action should do, for whom, on which object — and scaffolds a complete Agentforce action: the `@InvocableMethod` Apex class using `templates/agentforce/AgentActionSkeleton.cls`, the matching topic YAML using `templates/agentforce/AgentTopic_Template.md`, a JSON agent definition derived from `templates/agentforce/AgentSkeleton.json`, and a starter golden eval using `evals/framework.md`. Also produces the test class for the Apex action.

**Scope:** One action per invocation. Produces scaffolds, not deploys.

---

## Invocation

- **Direct read** — "Follow `agents/agentforce-builder/AGENT.md` — I need an action that summarizes the last 10 cases for an account"
- **Slash command** — [`/build-agentforce-action`](../../commands/build-agentforce-action.md)
- **MCP** — `get_agent("agentforce-builder")`

---

## Mandatory Reads Before Starting

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md` § Run-time Agents — the repo-wide hard rules this run is bound by: never write to the org, never auto-chain to another agent, never cite a skill path that does not resolve. `AGENT_CONTRACT.md` says what this file must contain; `AGENT_RULES.md` says what the agent may do while executing it.
3. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)

### Action, topic & agent authoring (Steps 1–4)
4. `skills/agentforce/agent-actions` — the action contract Step 2 emits against — input/output slots, idempotency, what an action may not do
5. `skills/agentforce/agent-topic-design` — Step 3's classifier prompt and scope boundary; a topic with a vague classifier routes the wrong action at runtime
6. `skills/agentforce/agentforce-agent-creation` — the agent definition Step 4 fills in — how topics, actions and channels actually bind
7. `skills/agentforce/custom-agent-actions-apex` — `@InvocableMethod` shape for an agent action: List-in / List-out, `callout=true` only when it really calls out
8. `skills/agentforce/agent-action-input-slot-extraction` — tune invocable input descriptions for slot extraction quality — the label text is the thing the LLM actually reads
9. `skills/agentforce/agent-action-error-handling` — Step 2 requires a user-readable error, never a stack trace; this is the pattern for turning an exception into one
10. `skills/agentforce/prompt-builder-templates` — grounding-source syntax for the topic's declared sObject and fields

### Trust, grounding & guardrails
11. `skills/agentforce/einstein-trust-layer` — why Step 1 forces a confirmation step on write actions, and what masking the Trust Layer does and does not do for you
12. `skills/agentforce/agentforce-guardrails` — turns each `trust_constraints` entry into an enforceable scope-boundary line rather than a comment
13. `skills/agentforce/agentforce-pii-redaction` — the concrete mechanism behind `no-pii-in-prompt` / `mask-email` constraints
14. `skills/agentforce/prompt-injection-defense` — grounded record data is untrusted input; a retrieval action that concatenates it into the prompt is exploitable
15. `skills/agentforce/rag-patterns-in-salesforce` — retrieval shape for read-only actions — what to ground on and how much
16. `skills/agentforce/data-cloud-grounding-for-agentforce` — when the grounding source is Data Cloud rather than an sObject, the retrieval and permission model both change

### Apex quality of the emitted action
17. `skills/apex/invocable-methods` — the bulk semantics Step 5's `invoke-with-200-parents` test asserts
18. `skills/apex/apex-security-patterns` — Step 2 requires `with sharing` / `USER_MODE` and `SecurityUtils`-guarded DML on every emitted path
19. `skills/apex/test-class-standards` — Step 5's test class is held to the same bar as any other Apex; agent actions are not exempt

### Testing, evaluation & readiness (Steps 5–6)
20. `skills/agentforce/agentforce-testing-strategy` — what is worth asserting about a non-deterministic action, beyond the four named Apex cases
21. `skills/agentforce/agentforce-eval-harness` — the golden-eval file Step 6 emits — case shape, assertions, rubric
22. `skills/agentforce/agentforce-production-readiness-checklist` — the gap list between a scaffold and something that can face a customer; belongs in the output, not discovered later

### Templates & eval framework
23. `templates/agentforce/AgentActionSkeleton.cls`
24. `templates/agentforce/AgentTopic_Template.md`
25. `templates/agentforce/AgentSkeleton.json`
26. `evals/framework.md`

---

## Inputs (ask for all five upfront)

| Input | Example |
|---|---|
| `action_name` | `Summarize Account Cases` |
| `primary_object` | `Account` (the sObject the action grounds on) |
| `actor` | `Service Agent` / `Sales Rep` / `Customer` |
| `intent` | "Show a 3-bullet summary of the 10 most recent cases for the given account" |
| `trust_constraints` | `no-pii-in-prompt`, `mask-email`, `no-external-callout`, etc. |

---

## Plan

### Step 1 — Classify the action

Tag it with one or more of:

| Category | Signal |
|---|---|
| **Read-only retrieval** | Intent is "show" / "summarize" / "list" | 
| **Write action** | Intent is "create" / "update" / "close" |
| **Composite** | Intent includes retrieval + write |
| **External callout** | Requires data not in Salesforce |

Write actions require explicit user confirmation step in the topic per `einstein-trust-layer`. Callouts require a Named Credential — if `trust_constraints` includes `no-external-callout`, refuse the callout and flag.

### Step 2 — Apex action class

Subclass `AgentActionSkeleton`. Requirements:
- `@InvocableMethod` with `label`, `description`, `iconName`, and `callout=true` only if the action hits an external system.
- `Request` inner class with `@InvocableVariable(required=true label='X' description='...')` for each input.
- `Response` inner class with `@InvocableVariable` for each output.
- Input validation up-front; return a user-readable error message, never a stack trace.
- All SOQL via `with sharing` OR `USER_MODE`, whichever the action's `actor` requires.
- All DML guarded with `SecurityUtils` from the templates.
- Logging via `ApplicationLogger.info("agentforce.<action_name>", message, context)` for every invocation.

### Step 3 — Topic YAML

Use `AgentTopic_Template.md` as the shape. Fill in:
- `name` = action_name
- `classifier prompt` = when the agent should route to this action (≤ 2 sentences)
- `scope boundary` = what the action must NOT do (≥ 3 explicit items drawn from `trust_constraints`)
- `grounding sources` = the sObject + fields the action reads
- `confirmation required` = true for write/composite actions

### Step 4 — Agent definition JSON

Fill `AgentSkeleton.json`:
- `actions[]` = the new action id
- `topics[]` = the new topic id
- `trust` = the constraints the user provided
- `channels` = keep default (can be narrowed later)

### Step 5 — Test class

Produce a test class following `test-class-generator`'s rules. Additional test cases specific to Agentforce actions:
- **invoke-with-null-input** — returns validation error, not exception
- **invoke-with-200-parents** — bulk-safe (InvocableMethod receives a List)
- **runAs-allowed-actor** — the designated actor can invoke
- **runAs-wrong-actor** — other actors get a user-readable permission error, not a silent empty response

### Step 6 — Golden eval

Produce a starter `evals/golden/agentforce__<action-slug>.md` with 3 P0 cases per `evals/framework.md`. At minimum:
- Happy path for the canonical record
- Null / missing grounding data
- Trust constraint violation (e.g. attempts to return masked PII)

Do not auto-commit — return the eval as part of the output bundle.

---

## Output Contract

1. **Action summary** — name, category (read-only / write / composite / callout), actor, primary object.
2. **Generated files** — one fenced code block per file, labelled with its target path:
   - `force-app/main/default/classes/<ActionName>.cls` + `.cls-meta.xml`
   - `force-app/main/default/classes/<ActionName>_Test.cls` + `.cls-meta.xml`
   - `force-app/main/default/agents/<AgentName>/topics/<TopicName>.yml`
   - `force-app/main/default/agents/<AgentName>/<AgentName>.agent-meta.xml` (derived from the JSON skeleton)
   - `evals/golden/agentforce__<action-slug>.md`
3. **Trust checklist** — confirms each constraint is encoded in the topic scope + validated in tests.
4. **Citations** — skill ids, template paths.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/agentforce-builder/<run_id>.md`
- **JSON envelope:** `docs/reports/agentforce-builder/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a caller-side concern — the conversion-path pointer lives in `agents/_shared/DELIVERABLE_CONTRACT.md` § See also.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

## Escalation / Refusal Rules

- Trust constraints include `no-external-callout` but the intent requires one → refuse; produce an analysis of what source of truth would need to move into SF first.
- `primary_object` is not a valid sObject in the SKILL corpus → flag and ask for clarification.
- Intent is write-heavy (updates / deletes) AND actor is `Customer` → refuse; recommend a Screen Flow with explicit user confirmation step instead.

---

## What This Agent Does NOT Do

- Does not deploy to an org.
- Does not run the generated eval (the eval script is the user's call).
- Does not modify existing agents / topics — only creates new ones.
- Does not invent trust constraints — passes them through from the user.
