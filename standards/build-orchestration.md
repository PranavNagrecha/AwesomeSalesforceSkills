# Build Orchestration — from one requirement to a verified, tested Salesforce build

Status: **contract v1 (2026-09-05)**. This document is the authority for the
requirements-to-build layer. Agents, commands, scripts and workflows that take
part in a build follow it exactly; anything not covered here is decided by
`AGENT_RULES.md`, `agents/_shared/AGENT_CONTRACT.md` and
`agents/_shared/DELIVERABLE_CONTRACT.md`, in that order.

## 1. What the layer does

A human gives one requirement (a paragraph, a worksheet, a backlog). The layer:

1. **Clarifies** — asks every question the relevant skills say must be asked
   before configuring (their `## Questions to Ask Before Configuring` tables),
   with a proposed default per question. Unbounded in count; bounded by
   relevance. Stops for the human.
2. **Scopes and plans** — turns requirement + answers into a plan file: scope
   in/out, fit-gap, decisions (each citing a decision-tree branch), milestones,
   and steps. Every step names the run-time agent that will execute it, the
   skills it must read, the artefacts it produces, and its acceptance tests.
3. **Verifies the plan** — adversarial check that every step is executable by
   the named agent, every cited skill/template/tree exists, dependencies are
   ordered, and every acceptance test is runnable. Stops for the human.
4. **Builds, milestone by milestone** — for each step: the named agent builds
   the artefacts; a tester runs the molecular tests (skill checkers, XML
   well-formedness, manifest consistency, the step's acceptance tests); a doc
   keeper updates PLAN.md, the configuration workbook, the decisions log and
   the traceability matrix. After all steps of a milestone: a milestone
   verifier runs cross-step checks and produces the acceptance report. Stops
   for the human.
5. **Repeats** until the last milestone is accepted.

Nothing in the layer deploys to an org. Deploy is a human action outside the
loop; the layer produces deploy-ready artefacts, deploy order, and a
validate-only command the human may run.

## 2. The plan file is the only shared state

`.sfskills/builds/<build-id>/plan.json` — schema at
`agents/_shared/schemas/build-plan.schema.json`. Every agent in the loop reads
it before acting and updates only the fields it owns. Human-readable views
(`PLAN.md`, `CLARIFICATIONS.md`, `MILESTONE-<id>-REPORT.md`) are rendered from
it by `scripts/build_plan.py`; never hand-edit a rendered view.

Layout of a build directory:

```text
.sfskills/builds/<build-id>/
├── requirement.md            # the human's input, verbatim
├── plan.json                 # canonical state
├── PLAN.md                   # rendered
├── CLARIFICATIONS.md         # rendered; the human answers here OR in plan.json
├── decisions.md              # append-only decisions log (doc keeper)
├── traceability.md           # REQ → step → artefact → test (doc keeper)
├── workbook/                 # configuration workbook sections (doc keeper)
├── artefacts/<step-id>/      # what each step produced (metadata XML, Apex, Flow, JSON)
├── tests/<step-id>/          # tester outputs (checker stdout, results.json)
├── envelopes/<step-id>/      # each agent run's JSON envelope
└── reports/                  # milestone verification reports
```

Committed example: `examples/builds/case-onboarding/` — the canonical
end-to-end test case, built from
`skills/admin/case-management-setup/references/worked-example-case-intake.md`.

## 3. Lifecycle and human gates

| Stage | Who runs it | Produces | Gate (human) |
|---|---|---|---|
| Intake | `/clarify-requirements` → `requirements-clarifier` | `plan.json` (status `clarifying`), `CLARIFICATIONS.md` | **G1** answers: every `blocking` question answered or explicitly deferred |
| Plan | `/plan-build` → `build-planner` | scope, decisions, milestones, steps; status `planned` | none yet |
| Verify | `/verify-plan` → `plan-verifier` (adversarial, 3 lenses) | verdicts on plan; status `verified` or `plan-rejected` | **G2** plan approval |
| Build | `/run-build` → workflow `build-from-requirements` | per milestone: artefacts, tests, docs, report; status `building` | **G3** per milestone acceptance |
| Done | — | status `done` | — |

Rules:
- A gate is recorded in `plan.json.human_gates[]` with `status`, `by`, `at`, `notes`.
  Agents never approve a gate. `scripts/build_plan.py gate` is the only writer.
- The build workflow refuses to start a milestone whose predecessor gate is not
  `approved`, and returns after producing a milestone report so the human can act.
- Re-planning after a rejected gate is a new plan version (`plan.version` + 1);
  earlier versions stay in `plan.history[]`.
- Questions are never capped. A clarifier that thinks a question is needed asks
  it, marks it `blocking` or `informational`, and proposes a default. The human
  may accept all defaults in one action.

## 4. Steps and step types

A step is the unit of build. Each step has exactly one owning run-time agent
from the roster (`agents/_shared/SKILL_MAP.md`) and one step type:

| Step type | Owning agents (examples) | Artefacts | Molecular tests the tester runs |
|---|---|---|---|
| `object-model` | `object-designer` | CustomObject / CustomField XML, picklists | skill checkers for object/field/picklist skills; XML parse; package.xml consistency |
| `access` | `permission-set-architect`, `profile-to-permset-migrator` | PermissionSet / PSG / sharing XML | permission-set + sharing checkers; no ModifyAllData surprises |
| `automation` | `flow-builder`, `apex-builder`, `flow-orchestrator-designer` | Flow XML, Apex + tests | flow/apex checkers; Apex test class present; fault paths |
| `routing` | `assignment-and-auto-response-rules-designer`, `omni-channel-routing-designer`, `lead-routing-rules-designer` | AssignmentRules / Queue / routing XML | assignment-rules checker; queue membership; business hours present |
| `sla` | `entitlement-and-milestone-designer`, `business-hours-and-holidays-configurator` | EntitlementProcess / MilestoneType / BusinessHours XML | entitlements checker; timeTriggers sanity |
| `ui` | `path-designer`, `object-designer` (layouts) | Layout / FlexiPage / PathAssistant XML | layout + path checkers |
| `data` | `csv-to-object-mapper`, `data-loader-pre-flight` | mapping files, load plan | preflight checker; mapping resolves |
| `integration` | `bulk-migration-planner`, `integration-catalog-builder` | pattern decision, contracts | integration checkers |
| `docs` | `config-workbook-author`, `story-drafter` | workbook, stories | workbook linter |
| `custom` | any roster agent | declared in the step | declared in the step's `acceptance_tests` |

Adding a step type = one new row here + an agent in the roster + (optionally)
a checker the tester can call. Nothing else changes; the planner reads this
table and the roster to assign agents, and `build_plan.py validate` rejects a
plan whose `agent` is not an active roster id or whose `type` is not in the table.

Each step records: `id`, `milestone`, `type`, `title`, `agent`, `skills[]`
(must resolve), `templates[]`, `decision_trees[]`, `inputs{}`, `outputs[]`
(paths under `artefacts/<step-id>/`), `depends_on[]`, `acceptance_tests[]`,
`status`, `runs[]`.

Step status machine: `pending → running → built → tested → documented`, with
`failed` and `blocked` as side exits. `next` = steps whose `depends_on` are all
`documented`, in the current (approved) milestone.

## 5. Acceptance tests

Every step has ≥ 1 acceptance test; every milestone has ≥ 1. Types:

| type | runner | pass condition |
|---|---|---|
| `checker` | `python3 skills/<domain>/<slug>/scripts/check_*.py --manifest-dir artefacts/<step>` | exit 0 |
| `xml` | ElementTree parse of every `*.xml`/`*-meta.xml` in the step's artefacts | all parse |
| `manifest` | every artefact type/member appears in `package.xml`; no member without a file | consistent |
| `command` | any stdlib-only command declared in the plan (never `sf project deploy start`) | exit 0 |
| `manual` | a checklist line the human ticks at the milestone gate | ticked |

The tester never invents a test; it runs what the plan declares plus the
always-on `xml` and `manifest` checks. If a declared checker does not exist,
the step is `blocked`, not silently passed.

## 6. Roles (new run-time agents, Tier 4 — Orchestration)

| Agent | Slash | One job |
|---|---|---|
| `requirements-clarifier` | `/clarify-requirements` | search skills for the requirement, collect their Questions-to-Ask, dedupe, propose defaults, write G1 |
| `build-planner` | `/plan-build` | scope + fit-gap + decisions + milestones + steps from requirement + answers |
| `plan-verifier` | `/verify-plan` | refute the plan on three lenses: executability, grounding, testability |
| `build-step-runner` | `/run-build-step` | execute one step by invoking the step's owning agent with the plan's inputs, store artefacts + envelope |
| `step-tester` | `/test-build-step` | run the step's molecular tests, write `tests/<step>/results.json` |
| `build-doc-keeper` | `/keep-build-docs` | after a tested step: PLAN.md, workbook rows, decisions log, traceability |
| `milestone-verifier` | `/verify-milestone` | cross-step checks + acceptance report + G3 request |

All seven are `class: runtime`, `requires_org: false`, follow the 8-section
AGENT.md shape, and emit the standard envelope. They read skills like every
other agent; they do not embed Salesforce knowledge of their own.

## 7. Workflows

- `.claude/workflows/plan-verify.js` — args `{build_dir}`; three adversarial
  lenses in parallel (executability, grounding, testability) per step, then a
  synthesis agent writes verdicts into `plan.json.verification`. Returns the
  blocker list. Deterministic: no barrier except the final synthesis.
- `.claude/workflows/build-from-requirements.js` — args `{build_dir,
  milestone}`; refuses unless the preceding gate is approved; runs the
  milestone's steps as a dependency-ordered pipeline (runner → tester → doc
  keeper per step, with `depends_on` respected), then the milestone verifier;
  returns the report path and the G3 request. Never runs two steps that write
  the same artefact path concurrently.

Models: Opus for planner / verifier / milestone verifier; the step's owning
agent runs at the session model; Sonnet is acceptable for the tester and doc
keeper. Fable is never invoked at run time.

## 8. Determinism and extendability rules

- `scripts/build_plan.py` (stdlib-only) is the single writer of derived views
  and gate records: `init`, `validate`, `render`, `ingest-answers`, `next`,
  `set-status`, `gate`, `status`, `ensure-gates`. Agents call it; they do not
  re-implement it.
- Every agent invocation in the loop is recorded in `plan.json.steps[].runs[]`
  with the envelope path. Re-running a step appends a run; it never overwrites
  history.
- The planner may only assign agents that exist with `class: runtime` and
  `status != deprecated`; it may only cite skills that resolve on disk.
- Skills stay the source of Salesforce truth. If a step needs knowledge no
  skill has, the runner marks the step `blocked` with `reason: skill-gap` and
  the doc keeper records the gap in `decisions.md` — that is the signal to
  deepen a skill, never to freestyle.
- Secrets never enter the build directory; envelopes redact per the
  deliverable contract.

## 9. Quality bar for this layer

- `python3 scripts/validate_repo.py` passes (agent shape, citations resolve,
  doc counts).
- `python3 -m pytest tests/test_build_plan.py` passes.
- The committed example build under `examples/builds/case-onboarding/` was
  produced by running the loop, not written by hand; its `plan.json` validates.
