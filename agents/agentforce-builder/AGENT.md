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
dependencies:
  skills:
    - agentforce/agent-actions
    - agentforce/agent-topic-design
    - agentforce/einstein-trust-layer
  shared:
    - AGENT_CONTRACT.md
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

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/agentforce/agent-actions/SKILL.md` (or closest via `search_skill`)
3. `skills/agentforce/agent-topic-design/SKILL.md`
4. `skills/agentforce/einstein-trust-layer/SKILL.md`
5. `templates/agentforce/AgentActionSkeleton.cls`
6. `templates/agentforce/AgentTopic_Template.md`
7. `templates/agentforce/AgentSkeleton.json`
8. `evals/framework.md`

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
