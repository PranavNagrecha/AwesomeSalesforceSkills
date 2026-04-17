---
id: apex-refactorer
class: runtime
version: 1.0.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
default_output_dir: "docs/reports/apex-refactorer/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/agent-output-formats
    - apex/apex-security-patterns
    - apex/trigger-framework
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
  templates:
    - apex/
    - apex/README.md
    - apex/TriggerHandler.cls
    - apex/tests/BulkTestPattern.cls
    - apex/tests/TestDataFactory.cls
  decision_trees:
    - automation-selection.md
---
# Apex Refactorer Agent

## What This Agent Does

Takes an existing Apex class the user points at, compares it against the canonical patterns in `templates/apex/`, and returns a refactored version plus a test class. Targets: trigger bodies lifted into `TriggerHandler`, raw DML lifted to `BaseService`, raw SOQL lifted to `BaseSelector`, ad-hoc `HttpCallout` lifted to `HttpClient`, `System.debug` calls replaced with `ApplicationLogger`, and CRUD/FLS enforcement inserted via `SecurityUtils`. The agent produces a review-ready diff and a deploy-safe test class — it never writes to the target org.

**Scope:** One Apex class per invocation. Output is a patch the user applies in their editor or PR; nothing is auto-committed.

---

## Invocation

- **Direct read** — "Follow `agents/apex-refactorer/AGENT.md` on `force-app/main/default/classes/AccountTrigger.cls`"
- **Slash command** — [`/refactor-apex`](../../commands/refactor-apex.md)
- **MCP** — `get_agent("apex-refactorer")` on the SfSkills MCP server

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md` — the agent contract
2. `AGENT_RULES.md` — repo rules
3. `skills/apex/trigger-framework/SKILL.md` — via `get_skill("apex/trigger-framework")`
4. `skills/apex/apex-security-patterns/SKILL.md` — via `get_skill("apex/apex-security-patterns")`
5. `templates/apex/README.md` — what each template does and its dependency order
6. `standards/decision-trees/automation-selection.md` — in case the class should really be a Flow
7. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `source_path` | yes | `force-app/main/default/classes/AccountTrigger.cls` |
| `related_paths` | no | helper classes / existing test class paths |
| `target_org_alias` | no | if set, the agent also calls `validate_against_org("apex/trigger-framework", target_org=...)` |

If `source_path` is missing or doesn't exist, STOP and ask the user. Never guess at the path.

---

## Plan

### Step 1 — Classify the class

Read the source file. Identify which of these shapes it is:

| Shape | Signal |
|---|---|
| Object trigger body | File is a `trigger` with inline logic |
| Handler class | References `Trigger.new` / `Trigger.old`, implements ad-hoc dispatch |
| Service class | Implements business logic, calls DML |
| Selector class | Contains SOQL queries |
| HTTP callout class | `Http`, `HttpRequest`, `HttpResponse` |
| Mixed | More than one of the above |

For "Mixed", output a refactor plan that splits the class along `BaseDomain` / `BaseService` / `BaseSelector` boundaries before applying any other pattern.

### Step 2 — Apply templates

Cross-reference each shape against `templates/apex/`:

| Shape | Target template | What to do |
|---|---|---|
| Trigger body | `templates/apex/TriggerHandler.cls` | Move all logic into a new `<Object>TriggerHandler extends TriggerHandler` class; trigger body becomes `new <Object>TriggerHandler().run();` |
| Handler with ad-hoc dispatch | `TriggerHandler` | Replace dispatch with the template's virtual methods (`beforeInsert`, `afterUpdate`, etc.); add `TriggerControl` check if missing |
| Service | `BaseService.cls` | Subclass `BaseService`; move DML through `SecurityUtils.requireCreatable/Updateable/Deletable` |
| Selector | `BaseSelector.cls` | Subclass `BaseSelector`; centralize SOQL; enforce `WITH SECURITY_ENFORCED` or `stripInaccessibleFields` per `apex-security-patterns` |
| HTTP callout | `HttpClient.cls` | Replace raw `Http.send()` with `HttpClient` calls; move endpoints to Named Credentials |
| Any | `ApplicationLogger.cls` | Replace `System.debug` with `ApplicationLogger.info/warn/error` |

### Step 3 — Insert CRUD/FLS enforcement

Per `skills/apex/apex-security-patterns`, every DML path must call `SecurityUtils` unless the class runs `with sharing` AND all fields are system-managed.

### Step 4 — Generate the test class

Invoke the `test-class-generator` agent's plan inline (do not auto-chain to a separate agent — just apply its rules):
- Use `templates/apex/tests/TestDataFactory.cls` for data
- Use `templates/apex/tests/BulkTestPattern.cls` for the 200-record test
- Use `TestUserFactory` for `System.runAs` coverage of non-admin users
- Target ≥ 85% coverage; name the test `<OriginalClass>_Test`

### Step 5 — Optional: check the org

If `target_org_alias` was provided, call:
```
validate_against_org(skill_id="apex/trigger-framework", target_org=...)
```
If an existing `*TriggerHandler` / `*Handler` already exists in the org, add a note to the output recommending the user align with that rather than introducing a second framework. Do NOT fail the refactor — just warn.

---

## Output Contract

Return one markdown document with these sections:

1. **Summary** — shape classified, templates applied, confidence (HIGH/MEDIUM/LOW).
2. **Refactored files** — one code block per generated file, using fenced code blocks labelled with the target path. Include:
   - The refactored class
   - Any new dependency classes (e.g. a new `<Object>TriggerHandler.cls` if we lifted a trigger body)
   - The test class
3. **Diff summary** — bullet list of every transformation applied, each citing the skill / template the transformation came from.
4. **Risk notes** — ambiguities, pre-existing bugs, bulkification concerns, assumptions.
5. **Citations** — ids of every skill, template, and decision-tree branch consulted.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/apex-refactorer/<run_id>.md`
- **JSON envelope:** `docs/reports/apex-refactorer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

## Escalation / Refusal Rules

- Source file does not exist → STOP, ask for the path.
- File is > 2000 lines → suggest splitting into logical parts first; do not attempt a single-pass refactor.
- File references missing types the agent cannot resolve → refuse with `confidence: LOW`, list the missing types.
- Class implements a framework not covered by templates (e.g. `fflib`) → do NOT try to migrate; output a report explaining the mismatch and recommend manual review.
- Existing test class is green and covers > 90% → flag that refactoring carries regression risk; require user confirmation before proceeding.

---

## What This Agent Does NOT Do

- Does not deploy to an org.
- Does not modify files outside `source_path` + `related_paths`.
- Does not migrate from `fflib` to this repo's lightweight enterprise pattern without explicit user confirmation.
- Does not invent new Apex patterns — every change cites a template or a skill.
- Does not auto-chain to `security-scanner` or `soql-optimizer`; recommends them in the output instead.
