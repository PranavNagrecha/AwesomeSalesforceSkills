---
id: apex-refactorer
class: runtime
version: 1.1.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-28
default_output_dir: "docs/reports/apex-refactorer/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - apex/apex-class-decomposition-pattern
    - apex/apex-collections-patterns
    - apex/apex-cpu-and-heap-optimization
    - apex/apex-design-patterns
    - apex/apex-dml-patterns
    - apex/apex-dynamic-soql-binding-safety
    - apex/apex-hardcoded-id-elimination
    - apex/apex-mocking-and-stubs
    - apex/apex-named-credentials-patterns
    - apex/apex-queueable-patterns
    - apex/apex-security-patterns
    - apex/apex-stripinaccessible-and-fls-enforcement
    - apex/apex-trigger-bypass-and-killswitch-patterns
    - apex/apex-with-without-sharing-decision
    - apex/async-apex
    - apex/batch-apex-patterns
    - apex/callouts-and-http-integrations
    - apex/error-handling-framework
    - apex/fflib-enterprise-patterns
    - apex/field-level-security-in-async-contexts
    - apex/governor-limits
    - apex/mixed-dml-and-setup-objects
    - apex/order-of-execution-deep-dive
    - apex/recursive-trigger-prevention
    - apex/soql-fundamentals
    - apex/soql-null-ordering-patterns
    - apex/soql-security
    - apex/test-class-standards
    - apex/test-data-factory-patterns
    - apex/trigger-framework
    - devops/code-coverage-orphan-class-cleanup
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
  probes:
    - apex-references-to-field.md
  templates:
    - apex/
    - apex/ApplicationLogger.cls
    - apex/BaseDomain.cls
    - apex/BaseSelector.cls
    - apex/BaseService.cls
    - apex/HttpClient.cls
    - apex/README.md
    - apex/SecurityUtils.cls
    - apex/TriggerControl.cls
    - apex/TriggerHandler.cls
    - apex/tests/BulkTestPattern.cls
    - apex/tests/MockHttpResponseGenerator.cls
    - apex/tests/TestDataFactory.cls
    - apex/tests/TestRecordBuilder.cls
    - apex/tests/TestUserFactory.cls
  decision_trees:
    - automation-selection.md
    - async-selection.md
    - sharing-selection.md
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

Breadth note (`AGENT_CONTRACT.md` Mandatory Reads rule 4): 31 skill reads, above the 8–25 design target. A refactor rewrites whichever layers the input class actually touches, and the agent cannot know which those are until it has read the class. Triggers, async surfaces, callouts, SOQL, DML, security and the test rebuild are each a *possible* refactor target on any given run, so the reads are conditional-but-mandatory rather than uniformly consumed.

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `agents/_shared/DELIVERABLE_CONTRACT.md`
4. `agents/_shared/REFUSAL_CODES.md`

### Architecture / decomposition
5. `skills/apex/apex-design-patterns` — the target shape a refactor moves toward; without it 'cleaner' is undefined
6. `skills/apex/apex-class-decomposition-pattern` — Domain/Service/Selector split decision
7. `skills/apex/fflib-enterprise-patterns` — recognize fflib-shaped code; do NOT auto-migrate
8. `templates/apex/README.md` — template dependency order
9. `skills/devops/code-coverage-orphan-class-cleanup` — delete orphan classes to lower coverage denominator instead of stubbing tests

### Triggers & order
10. `skills/apex/trigger-framework` — the handler shape a multi-trigger or logic-in-trigger refactor lands on
11. `skills/apex/recursive-trigger-prevention` — a refactor that consolidates triggers changes re-entry behaviour — the guard has to move with it
12. `skills/apex/apex-trigger-bypass-and-killswitch-patterns` — the bypass hook a consolidated handler must keep, or the org loses its only escape valve
13. `skills/apex/order-of-execution-deep-dive` — reordering handler calls is only safe if the save-order semantics are preserved

### Async surfaces (refactor target candidates)
14. `skills/apex/async-apex` — sync→async is one of this agent's largest refactors and changes the transaction, not just the timing
15. `skills/apex/apex-queueable-patterns` — the default landing surface for a `@future` method being modernised
16. `skills/apex/batch-apex-patterns` — the landing surface when a loop must become chunked; `getQueryLocator` semantics decide feasibility
17. `standards/decision-trees/async-selection.md`
18. `skills/apex/field-level-security-in-async-contexts` — When refactoring sync Apex into async, preserve the originating user's FLS — async hops change the running user

### Callouts (refactor to HttpClient + Named Credentials)
19. `skills/apex/callouts-and-http-integrations` — the callout shapes to be refactored onto `templates/apex/HttpClient.cls`
20. `skills/apex/apex-named-credentials-patterns` — endpoints and headers moved out of code — the credential half of a callout refactor

### SOQL refactor targets
21. `skills/apex/soql-fundamentals` — the query surface being rewritten, including clauses whose meaning changes when they move
22. `skills/apex/soql-security` — a refactor must not quietly drop `WITH USER_MODE`; that is a regression, not a simplification
23. `skills/apex/apex-dynamic-soql-binding-safety` — the bind-variable rewrite for concatenated queries encountered during the refactor
24. `skills/apex/apex-collections-patterns` — the map/set idioms behind every query- and DML-out-of-loop refactor
25. `skills/apex/soql-null-ordering-patterns` — explicit NULLS clause + Id tiebreaker for stable order

### DML / transactions
26. `skills/apex/apex-dml-patterns` — partial-success vs all-or-none semantics change when DML is hoisted out of a loop
27. `skills/apex/mixed-dml-and-setup-objects` — consolidating DML can accidentally put setup and non-setup writes in one transaction

### Governor / performance
28. `skills/apex/governor-limits` — the budget the refactor is meant to improve — and the one it must not silently worsen
29. `skills/apex/apex-cpu-and-heap-optimization` — CPU and heap, not SOQL count, are what a large-collection refactor usually fixes or breaks

### Security (refactor → SecurityUtils)
30. `skills/apex/apex-security-patterns` — the enforcement baseline a refactored class must still meet after the move
31. `skills/apex/apex-with-without-sharing-decision` — moving logic between classes changes the sharing context it runs in
32. `skills/apex/apex-stripinaccessible-and-fls-enforcement` — the FLS remediation to apply while the write path is already being touched
33. `skills/apex/apex-hardcoded-id-elimination` — a classic refactor target: id literals block sandbox parity and encode privilege assumptions
34. `standards/decision-trees/sharing-selection.md`

### Error handling
35. `skills/apex/error-handling-framework` — the exception taxonomy a refactored class logs against, so failures stay diagnosable

### Test rebuild after refactor
36. `skills/apex/test-class-standards` — the bar the rebuilt tests must meet, since a refactor invalidates the old ones
37. `skills/apex/test-data-factory-patterns` — refactored tests build data through the factory rather than re-inlining literals
38. `skills/apex/apex-mocking-and-stubs` — decomposition makes collaborators injectable; this is how the new seams get tested

### Templates
39. `templates/apex/TriggerHandler.cls`
40. `templates/apex/TriggerControl.cls`
41. `templates/apex/BaseService.cls`
42. `templates/apex/BaseSelector.cls`
43. `templates/apex/BaseDomain.cls`
44. `templates/apex/ApplicationLogger.cls`
45. `templates/apex/SecurityUtils.cls`
46. `templates/apex/HttpClient.cls`
47. `templates/apex/tests/BulkTestPattern.cls`
48. `templates/apex/tests/TestDataFactory.cls`
49. `templates/apex/tests/MockHttpResponseGenerator.cls`
50. `templates/apex/tests/TestRecordBuilder.cls`
51. `templates/apex/tests/TestUserFactory.cls`

### Probes
52. `agents/_shared/probes/apex-references-to-field.md` — for understanding field-impact before lifting selector queries

### Decision trees
53. `standards/decision-trees/automation-selection.md`

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
5. **Process Observations** — peripheral signal noticed during the refactor, separate from the direct diff.
   - **What was healthy** — base-class / framework already partially adopted; existing test class covers > 80% before refactor; existing Selector-equivalents in the codebase that the new shape can extend; consistent naming convention.
   - **What was concerning** — sharing keyword inferred but ambiguous (cite `apex-with-without-sharing-decision`); hardcoded IDs / secrets discovered (cite the matching skill); SOQL inside loops the agent could not safely rewrite; dynamic SOQL with string concatenation requiring `apex-dynamic-soql-binding-safety` follow-up; recursion guard absent on a multi-event handler.
   - **What was ambiguous** — whether `WITHOUT SHARING` is justified; whether existing Selector should be extended or a new one introduced; whether a Service/Domain/Selector split is warranted given current size.
   - **Suggested follow-up agents** — `security-scanner` (post-refactor FLS/CRUD verification); `soql-optimizer` (when new Selector emitted); `test-class-generator` (when test-class generation deferred); `trigger-consolidator` (when refactor reveals additional triggers on the same SObject); `score-deployment` (pre-deploy gate).
6. **Citations** — ids of every skill, template, and decision-tree branch consulted.

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
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a caller-side concern — the conversion-path pointer lives in `agents/_shared/DELIVERABLE_CONTRACT.md` § See also.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Dimensions for this agent: `class-shape` (trigger / handler / service / selector / callout / mixed), `templates-applied` (which canonical templates wired in), `crud-fls-enforcement`, `sharing-keyword`, `id-handling`, `secret-handling`, `dynamic-soql-safety`, `bulk-safety`, `transaction-boundaries`, `test-class-generation`. When the source file doesn't exercise a dimension, record it in `dimensions_skipped[]` with `state: not-run` and a one-line reason.

## Escalation / Refusal Rules

Canonical refusal codes per `agents/_shared/REFUSAL_CODES.md`:

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_INPUT` | `source_path` not provided. |
| `REFUSAL_INPUT_AMBIGUOUS` | `source_path` exists but file is empty / non-Apex / unreadable. |
| `REFUSAL_OVER_SCOPE_LIMIT` | File > 2000 lines — recommend pre-splitting; or refactor introduces > 6 new files in one pass. |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | (a) File references missing types the agent cannot resolve from `related_paths`; (b) class implements `fflib` or another framework outside the canonical templates — do NOT auto-migrate; (c) existing test class is green and covers > 90% — refactor risks regression. |
| `REFUSAL_OUT_OF_SCOPE` | Request to refactor managed-package class, request to deploy, request to refactor more than one class per invocation. |
| `REFUSAL_MANAGED_PACKAGE` | Source class is in a managed-package namespace. Recommend extension/wrapping pattern instead. |
| `REFUSAL_SECURITY_GUARD` | Refactor would silently drop an existing `with sharing` keyword, bypass an existing `SecurityUtils` call, or expose a previously-hidden secret. |
| `REFUSAL_POLICY_MISMATCH` | Decision-tree consultation shows the class should be a Flow / Platform Event / external service — recommend the appropriate agent (cite `automation-selection.md` branch). |

---

## What This Agent Does NOT Do

- Does not deploy to an org.
- Does not modify files outside `source_path` + `related_paths`.
- Does not migrate from `fflib` to this repo's lightweight enterprise pattern without explicit user confirmation.
- Does not invent new Apex patterns — every change cites a template or a skill.
- Does not auto-chain to `security-scanner` or `soql-optimizer`; recommends them in the output instead.
