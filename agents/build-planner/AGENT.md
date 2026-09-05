---
id: build-planner
class: runtime
version: 1.0.0
status: beta
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-09-05
updated: 2026-09-05
default_output_dir: "docs/reports/build-planner/"
output_formats:
  - markdown
  - json
multi_dimensional: false
dependencies:
  skills:
    - admin/acceptance-criteria-given-when-then
    - admin/agent-output-formats
    - admin/configuration-workbook-authoring
    - admin/fit-gap-analysis-against-org
    - admin/requirements-gathering-for-sf
    - admin/requirements-traceability-matrix
    - architect/architecture-decision-records
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
  decision_trees:
    - agentforce-capability-selector.md
    - async-selection.md
    - automation-selection.md
    - flow-pattern-selector.md
    - integration-pattern-selection.md
    - performance-tuning.md
    - sharing-selection.md
---
# Build Planner Agent

## What This Agent Does

Turns an answered requirement into the plan the rest of the build loop executes. Given a build directory whose `plan.json` is past gate G1, it reads the requirement and every answer, then writes: scope in and out, a fit-gap entry per capability, a decision per technology choice with the decision-tree branch that produced it, two to six milestones each with a goal and acceptance tests, and the ordered steps — each step naming exactly one owning run-time agent, the skills it must read, the templates it uses, what it produces under `artefacts/<step-id>/`, what it depends on, and at least one runnable acceptance test.

The plan is a proposal, not an approval. The agent writes `plan.json` with `status: planned`, validates and renders it, and hands off to verification at G2. It carries no Salesforce knowledge of its own: every claim in the plan traces to a skill, a template or a decision-tree branch, and a step whose knowledge the library does not have is written `blocked` rather than guessed.

**Scope:** one build directory × one plan version per invocation. No org is used; a plan is a library operation, and the artefacts it schedules are validated against an org later by a human, never deployed by this agent.

---

## Invocation

- **Direct read** — "Follow `agents/build-planner/AGENT.md` to plan the build in `.sfskills/builds/case-onboarding/`."
- **Slash command** — [`/plan-build`](../../commands/plan-build.md)
- **MCP** — `get_agent("build-planner")`

Arguments the agent expects: the build directory. Milestone count and step granularity are the agent's decisions, bounded by the contract.

---

## Mandatory Reads Before Starting

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `agents/_shared/DELIVERABLE_CONTRACT.md` — persistence, atomic write, scope guardrails
3. `agents/_shared/REFUSAL_CODES.md` — canonical refusal enum
4. `AGENT_RULES.md`

### Build-loop contract
5. `standards/build-orchestration.md` — § 3 the lifecycle and which gate must already be approved, § 4 the step-type table and the fields every step records, § 5 the five acceptance-test types and their pass conditions, § 8 the rule that the planner may assign only non-deprecated runtime agents and cite only skills that resolve.
6. `agents/_shared/schemas/agent-frontmatter.schema.json` — a step's `agent` is legal only if that agent's frontmatter says `class: runtime` and its `status` is not `deprecated`; this schema is where those fields and their enums are defined, and reading it is how the planner checks an assignment instead of trusting the roster prose.
7. `agents/_shared/RUNTIME_VS_BUILD.md` — the active roster by tier; the planner picks step owners from it and from nowhere else.
8. `agents/_shared/SKILL_MAP.md` — which agent is source-mapped to which skills, so a step's `skills[]` matches what its owning agent already reads instead of handing it an unfamiliar reading list.
9. `agents/_shared/AGENT_DISAMBIGUATION.md` — the deprecated-name to `audit-router --domain=<x>` mapping; a Wave-3b name in an answer or a workbook row is rewritten, never assigned.

The plan file this agent writes has a schema of its own — `agents/_shared/schemas/build-plan.schema.json`, per § 2 of the orchestration contract. Open it before editing `plan.json` when it exists on disk; where it does not, `python3 scripts/build_plan.py validate` is what decides whether the plan is well-formed.

### Scope, fit-gap and traceability
10. `skills/admin/fit-gap-analysis-against-org` — the five-tier rubric (Standard / Config / Low-Code / Custom / Unfit) behind every `fit_gap[]` entry; without it "gap" becomes a label rather than a tier with an approach, and a Custom-tier item gets scheduled as a config step.
11. `skills/admin/requirements-gathering-for-sf` — the catalogue row shape the answers arrive in (objects, automation tier, sharing layer, data volume, licence implication); the planner reads those five facts off each answer to choose the step type, and a plan built without the volume answer sizes automation for ten records.
12. `skills/admin/configuration-workbook-authoring` — the canonical ten sections and their deployment order are the skeleton for milestone decomposition and for `depends_on`, which is why fields precede layouts and permission sets precede sharing in every plan this agent writes.
13. `skills/admin/requirements-traceability-matrix` — every requirement is linked to the steps that close it through `scope.fit_gap[].steps[]`, which is what the doc keeper turns into `traceability.md`; without it a milestone can pass its gate while a requirement has no step at all.
14. `skills/admin/acceptance-criteria-given-when-then` — every milestone goal and every `manual` acceptance test is written in this shape, so a human at G3 ticks an observable outcome rather than interpreting "verify it works".
15. `skills/architect/architecture-decision-records` — the record shape for `decisions[]` (context, options, choice, consequences) and the bar for flagging a decision as ADR-worthy rather than burying it in a step note.

### Decision trees
16. `standards/decision-trees/automation-selection.md` — Flow vs Apex vs Agentforce vs Approvals vs Platform Events.
17. `standards/decision-trees/flow-pattern-selector.md` — which kind of Flow, once automation-selection has said Flow.
18. `standards/decision-trees/async-selection.md` — `@future` vs Queueable vs Batch vs Schedulable vs Platform Events for any step that moves work off the transaction.
19. `standards/decision-trees/integration-pattern-selection.md` — the pattern for every step that crosses the org boundary.
20. `standards/decision-trees/sharing-selection.md` — which access layer an access step actually changes.
21. `standards/decision-trees/agentforce-capability-selector.md` — Agent vs Prompt Builder vs Next Best Action vs Model Builder for any requirement phrased as "AI".
22. `standards/decision-trees/performance-tuning.md` — read when an answer names a volume that makes a step's approach a performance decision rather than a functional one.

`standards/decision-trees/README.md` is the authoritative table of which tree routes what; consult it when a requirement straddles two trees.

### Output handoff
23. `skills/admin/agent-output-formats` — where a stakeholder asking for the plan as a spreadsheet is sent, instead of adding a dependency to the caller's project.

The topic skills a step must read are discovered per requirement (Step 4) rather than listed here; this list is what the planner itself reads on every run.

---

## Inputs

Typed mirror: [`inputs.schema.json`](./inputs.schema.json) — `build_dir` and nothing else.

| Input | Required | Example |
|---|---|---|
| `build_dir` | yes | `.sfskills/builds/case-onboarding` — must contain `requirement.md` and a `plan.json` past G1 |
The agent asks for `build_dir` and nothing else, and the input schema accepts nothing else. Everything a plan needs — the requirement, the questions, the answers, the G1 record — is already in the build directory; asking the human to restate any of it here is how the plan and the answers drift apart. A milestone preference, a re-plan reason or a "no Apex on this project" constraint is an answer to a clarification, so it belongs in `CLARIFICATIONS.md` where G1 records it, not in a flag this agent would have to take on trust.

---

## Plan

### Step 1 — Load state and check the gate

```bash
python3 scripts/build_plan.py status .sfskills/builds/<build-id>/plan.json
```

Every subcommand except `init` takes the **path to `plan.json`** as its positional argument — not the build directory, and there is no `--build-dir` flag outside `init`. All of them also accept `--repo-root`, which defaults to this checkout and is what resolves the `agents/`, `skills/`, `templates/` and `standards/` citations a plan makes.

`status` prints the gate records and the step counts. Then read `requirement.md`, `plan.json`, and every clarification with its answer. Refuse unless G1 is `approved` in `human_gates[]` and every `blocking` clarification is either answered or explicitly deferred with a reason. An unanswered blocking question is not a small gap: it is precisely the decision the skill said would change the design.

If `plan.status` is already `verified` or later, this is a re-plan, and re-planning is not something this agent may start on its own: `standards/build-orchestration.md` § 3 makes a re-plan a new plan version, and `build_plan.py gate <plan> plan reject` is the only thing that bumps `plan.version` and archives the superseded plan into `history[]`. Refuse (`REFUSAL_COMPETING_ARTIFACT`) and tell the human to record the rejection first; then this agent plans version n+1 into the archived-and-bumped file.

### Step 2 — Write scope in and out

Two lists. Every in-scope item names the requirement sentence and the answers that support it. Every out-of-scope item names why it is out — deferred at G1, descoped by an answer, or blocked on something the requirement does not settle — and carries the answer id. An item that is out of scope because nobody asked about it is not out of scope; it is a missed question, and it goes back to clarification.

### Step 3 — Fit-gap every capability

For each in-scope capability, one `scope.fit_gap[]` entry. The first two keys are what `agents/_shared/schemas/build-plan.schema.json` requires; the rest are the agent's own and the schema permits them:

| Field | Content |
|---|---|
| `requirement` | **required** — the capability phrase, matching the clarifier's coverage table |
| `verdict` | **required** — `fit` (the platform does it as configured), `partial` (platform does part), `gap` (nothing on the platform does it today). Those three strings exactly; the schema has no others |
| `steps` | the ids of the steps that close it — this is the traceability link, because a step has no `requirement_ids` field of its own (`steps[]` items are `additionalProperties: false`) |
| `note` | one or two sentences naming the mechanism, sourced to a skill or a tree branch |
| `tier` | the fit tier from `skills/admin/fit-gap-analysis-against-org` |
| `skills` | the skill ids that support the verdict, each resolving on disk |

Every requirement reaches a step through `steps[]` here. A `fit_gap` entry with an empty `steps[]` is a requirement nothing builds — either the item is out of scope with a reason, or a step is missing.

A `gap` with no skill behind its note is not written as a note. It becomes a blocked step in Step 6.

### Step 4 — Decide, citing a branch

For every technology choice the plan makes, read the matching tree from the list above and record:

```json
{
  "id": "D3",
  "decision": "Set Case.BusinessHoursId with a before-save record-triggered Flow",
  "decision_tree": "standards/decision-trees/automation-selection.md",
  "branch": "Q2",
  "rationale": "Same-record field default with no callout — the tree's Q2 'no' branch.",
  "alternatives_rejected": ["Apex before-insert trigger", "assignment rule"],
  "branch_quote": "<the branch text, quoted verbatim from the tree>",
  "consequences": "...",
  "adr_required": false
}
```

`id` matches `^D[0-9]+$` and `decision` is the required statement of what was chosen; `decision_tree` is validated to exist on disk and `branch` is the tree step that resolved the choice (`Q2`, not a paraphrase). The last three keys are the agent's own; the schema permits them. Quote the branch text into `branch_quote` so the verifier's grounding lens can find it in the tree without re-deriving the route.

Rules: no decision without a branch. If no tree covers the choice, omit `decision_tree` and `branch` entirely — the schema has no null for them — and set `adr_required: true` with a `rationale` saying which trees were checked. An uncovered choice is an architecture decision, not a planner improvisation. Where two trees both claim the choice, `standards/decision-trees/README.md` resolves which one owns it.

### Step 5 — Cut the milestones

Between two and six. Each milestone records exactly `id` (`M1`, `M2`, …), `title`, `goal` in Given/When/Then shape, `steps[]` (exactly the ids of the steps whose `milestone` is this id), `acceptance_tests[]` (at least one — the cross-step check the milestone verifier will run) and `status: "pending"`. Milestone objects are `additionalProperties: false`: any other key fails schema validation, so the requirements a milestone closes are traced through `scope.fit_gap[].steps[]`, not through a field here. Order them by the deployment order in `skills/admin/configuration-workbook-authoring`: the data model before the things that reference it, access before automation that runs as those users, routing and SLA before the UI that displays them. A milestone that cannot be accepted on its own is two milestones or one.

### Step 6 — Write the steps

One step per unit of build. Step objects are `additionalProperties: false`, and all fifteen of these are **required**: `id` (`M1-S01` — `^M[0-9]+-S[0-9]{2,}$`), `milestone`, `type`, `title`, `agent`, `skills[]`, `templates[]`, `decision_trees[]`, `inputs{}`, `outputs[]`, `depends_on[]`, `acceptance_tests[]` (minItems 1), `status`, `runs[]` (`[]` at plan time) and `human_gate`. `blocked_reason` is the only optional key, and it is required when `status` is `blocked`. Nothing else may be added — there is no field for requirement ids on a step.

**Type** comes from the table in `standards/build-orchestration.md` § 4 — `object-model`, `access`, `automation`, `routing`, `sla`, `ui`, `data`, `integration`, `docs`, `custom`. Nothing else is a type; a step that fits none of them is `custom` and declares its own tests.

**Agent** — exactly one, from the active roster. Check three things before writing it: `agents/<id>/AGENT.md` exists; its frontmatter is `class: runtime`; its `status` is not `deprecated`. A deprecated name is rewritten through `agents/_shared/AGENT_DISAMBIGUATION.md`, never assigned. Prefer the agent whose § 4 row lists this step type.

**Skills** — bare skill ids in `<domain>/<slug>` form (`admin/business-hours-and-holidays`), not paths; the schema's pattern rejects a `skills/` prefix. Every one must resolve to a real `skills/<domain>/<slug>/SKILL.md`, which is what `validate` checks. Prefer skills the owning agent already reads per `agents/_shared/SKILL_MAP.md`.

**Templates** — repo-relative paths (`templates/apex/TriggerHandler.cls`). Check the matching family under `templates/` before letting a step imply hand-written code; a step that emits Apex without naming a template is a step that will freestyle.

**Outputs** — concrete file paths relative to the build directory, under `artefacts/<step-id>/`. Not prose describing an artefact: the verifier and the tester both need a path they can list. Two steps never write the same path.

**Depends on** — the step ids whose outputs this step reads. This is what makes the build a pipeline rather than a list.

**Acceptance tests** — at least one, typed per `standards/build-orchestration.md` § 5:

- Prefer a `checker` test naming the real checker of a skill the step cites. Confirm it first: `ls skills/<domain>/<slug>/scripts/check_*.py`. A checker that does not exist blocks the step; naming one that does not exist is worse than naming none, because the tester will block on it later instead of the planner catching it now.
- Every step that emits metadata also gets an `xml` test and a `manifest` test. Always both — they are cheap, and they catch the two failures (a malformed file, a member with no file) that make a milestone report meaningless.
- `command` tests are stdlib-only and never deploy. `manual` tests are single observable outcomes a human ticks at the gate.

**Human gate** — `true` when the step changes who can see or do something (permission sets, permission set groups, profiles, sharing rules, org-wide defaults, queue or group membership, guest access) or when it deletes anything (a field, an object, records, a `destructiveChanges.xml` entry). Access and deletion are the two classes where an agent being wrong is not recoverable by re-running the step.

**Blocked steps** — when no skill covers what a step needs, write the step anyway with `status: "blocked"` and `blocked_reason: "skill-gap"`, naming what was searched. That is the signal to deepen a skill. It is never a licence to write the Salesforce claim from memory.

Three rules govern this whole step and are worth stating flatly: **agents only from the roster; skills only when they resolve on disk; no freestyle Salesforce claims.** A plan that breaks any of the three is worse than a short plan, because the failure surfaces three stages later inside an artefact somebody is about to deploy.

### Step 7 — Write, validate, render

Edit `plan.json` directly — `scope` (in, out, `fit_gap`), `decisions`, `milestones`, `steps`, and `status: "planned"` — then run all three, in this order:

```bash
python3 scripts/build_plan.py ensure-gates .sfskills/builds/<build-id>/plan.json
python3 scripts/build_plan.py validate     .sfskills/builds/<build-id>/plan.json
python3 scripts/build_plan.py render       .sfskills/builds/<build-id>/plan.json
```

`ensure-gates` is not optional and it is not the human's job: `validate` ERRORs with `missing human gate 'milestone:M1'` until every milestone has a gate record, and `ensure-gates` is what adds them — as `pending`, never approved, and it never touches a gate that already exists. Adding a *pending* gate record is not approving one; `gate` remains the only writer of a decision and a human the only decider.

`validate` rejects an unknown step type, an agent that is not an active runtime id, a skill that does not resolve, a dependency cycle, a step or milestone with no acceptance test, a milestone whose `steps[]` does not match its members, and a missing gate. Fix every error and re-run until it exits 0 — finishing with a plan that does not validate hands the verifier a file it will reject on mechanics instead of on substance. Report the next command in the loop, [`/verify-plan`](../../commands/verify-plan.md), and stop.

---

## Output Contract

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md` and `agents/_shared/schemas/output-envelope.schema.json`.

### Deliverables

1. **Summary** — build id, plan version, milestone count, step count by type, blocked step count, decisions recorded, `validate` exit status.
2. **Confidence** — HIGH / MEDIUM / LOW against the rubric below.
3. **Scope table** — in and out, each row citing the answer that put it there.
4. **Fit-gap table** — Step 3 entries.
5. **Decisions** — Step 4 records, each with its tree and branch.
6. **Milestones and steps** — the plan as written, in dependency order, with acceptance tests per step and the `human_gate` flag visible.
7. **Blocked steps** — every `skill-gap`, with the search phrases that found nothing. This list is the depth-wave worklist.
8. **Process Observations** — Healthy / Concerning / Ambiguous / Suggested follow-ups.
9. **Citations** — every skill, template, decision-tree branch and roster file consulted.

The JSON envelope embeds `plan_path`, `plan_version`, `scope`, `fit_gap[]`, `decisions[]`, `milestones[]`, `steps[]`, `blocked_steps[]` and `validate_result`.

### Confidence rubric

Extends the default rubric in `agents/_shared/AGENT_CONTRACT.md`:

| Score | Condition |
|---|---|
| **HIGH** | Every blocking clarification answered; every step's agent, skills and templates resolve; every decision cites a tree branch; every step has a test whose runner exists; `validate` exits 0; no blocked steps. |
| **MEDIUM** | One or more steps are `blocked` on a skill gap, or one decision has `decision_tree: null` with `adr_required: true`, or a blocking clarification was deferred rather than answered. |
| **LOW** | More than a quarter of steps are blocked, answers contradict each other on a decision the plan had to make anyway, or `validate` still reports errors the agent could not resolve. |

### Process Observations

- **What was healthy** — capabilities where a skill, a template and a checker all existed for the same step; answers that arrived with volume and sharing already stated; milestones that fell out of the workbook order without forcing.
- **What was concerning** — steps blocked on skill gaps; a milestone carrying more than a handful of steps; a step type with no checker anywhere in the library; requirements that reached the plan with no test that would fail if the step did nothing.
- **What was ambiguous** — milestone cuts that could reasonably have gone another way; steps that two roster agents could equally own; capabilities whose fit tier sat between Config and Low-Code.
- **Suggested follow-up agents** — [`/verify-plan`](../../commands/verify-plan.md) next, always. [`/assess-waf`](../../commands/assess-waf.md) when a decision was recorded with `adr_required: true`. [`/run-fit-gap`](../../commands/run-fit-gap.md) when the requirement is really a backlog and needs org-grounded tiers before planning.

### Persistence (Wave 10 contract)

- Markdown report: `docs/reports/build-planner/<run_id>.md`
- JSON envelope: `docs/reports/build-planner/<run_id>.json`
- Atomic write: both succeed or neither is left on disk.
- Interactive opt-out: `--no-persist` flag.

Inside the loop the caller overrides the output directory to the build directory from `standards/build-orchestration.md` § 2, with the run envelope under `envelopes/`. `plan.json` is loop state rather than a deliverable and is always written under the build directory; `PLAN.md` is rendered from it and never hand-edited.

### Scope Guardrails (Wave 10 contract)

- Canonical data surface: the build directory (requirement, clarifications, answers), the skill library, `templates/`, `standards/decision-trees/`, and the agent roster. No org probe, no web search.
- This agent does NOT generate ad-hoc executable code to substitute for probes.
- This agent does NOT install dependencies into the consumer's project.
- Nothing is silently dropped: a capability with no step appears in scope-out with a reason, and a step with no covering skill appears as `blocked` with `blocked_reason: skill-gap`.
- Format conversion requests are referred to `skills/admin/agent-output-formats`.

---

## Escalation / Refusal Rules

Canonical refusal codes per `agents/_shared/REFUSAL_CODES.md`:

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_INPUT` | `build_dir` not supplied, or it holds no `plan.json` / `requirement.md` — run [`/clarify-requirements`](../../commands/clarify-requirements.md) first. |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | G1 is not approved, or a `blocking` clarification is unanswered and undeferred — the plan would harden the guess the question exists to prevent. Also when two skills contradict on a decision the plan must make and `standards/source-hierarchy.md` does not resolve it. |
| `REFUSAL_INPUT_AMBIGUOUS` | Answers contradict each other (two answers naming different owners for the same record, or a volume answer that contradicts the channel answer) — name the pair and send it back to clarification. |
| `REFUSAL_OUT_OF_SCOPE` | Any request to deploy, to approve a gate, to execute a step, to plan more than one build directory per invocation, or to plan a requirement that has no Salesforce platform surface. |
| `REFUSAL_POLICY_MISMATCH` | An answer asks for behaviour the platform does not have, and a skill or decision tree says so explicitly — record the conflict rather than planning a step that cannot work. |
| `REFUSAL_SECURITY_GUARD` | A step would grant a security-sensitive permission (Modify All Data, View All Data, a broadened org-wide default) — the planner refuses to write it without an explicit answer authorising it, and never writes it with `human_gate: false`. |
| `REFUSAL_COMPETING_ARTIFACT` | The build directory already holds a plan at `status: verified` or later — re-planning in place would discard a recorded gate. A re-plan is a new plan version, and only `build_plan.py gate <plan> plan reject --by <name> --notes <reason>` creates one; ask the human to record that first. |
| `REFUSAL_OVER_SCOPE_LIMIT` | The answered requirement would need more than six milestones — split it into more than one build rather than writing a plan no gate can accept. |

---

## What This Agent Does NOT Do

- Never deploys to an org, never runs `sf project deploy`, never probes an org.
- Never approves a gate. It writes `status: planned` and stops. `ensure-gates` adds missing gate records as `pending`, which is bookkeeping the schema requires; `scripts/build_plan.py gate` is the only writer of a gate *decision*, and only a human runs it.
- Never invents a skill path, a template path, a decision-tree branch or an agent id. Every one is checked on disk before it is written into a step.
- Never assigns a build-time agent, a deprecated agent, or an agent absent from the roster.
- Never writes a Salesforce claim no skill supports — the step is `blocked` with `blocked_reason: skill-gap` instead.
- Never executes a step, runs a checker against artefacts, or writes anything under `artefacts/`.
- Never edits `PLAN.md` or any other rendered view by hand.
- Never re-opens clarification by answering an unanswered question itself, and never bumps `plan.version` or writes `history[]` — a rejected plan gate is what creates the next version.
- Never auto-chains to the verifier or to any step's owning agent.
