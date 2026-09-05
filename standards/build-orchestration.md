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
it before acting and updates only the fields it owns.

`PLAN.md` and `CLARIFICATIONS.md` are **rendered** from the plan by
`scripts/build_plan.py render`; never hand-edit a rendered view.
`MILESTONE-<id>-REPORT.md` is **not** rendered: `milestone-verifier` writes it
directly, then records its path with `build_plan.py set-milestone <plan> <Mk>
--status verified|rejected --report-path <path>`. No other writer touches it.

No agent hand-edits `plan.json` either. Every field an agent owns has a
subcommand that writes it (§ 8) — `set-clarifications`, `set-plan`,
`set-verification`, `set-milestone`, `set-status`, `gate`, `ensure-gates`. A
surgical JSON edit is a defect, not a shortcut: it is how a plan acquires a
shape the validator never saw.

### Build mode

`plan.json` carries a required `build_mode`, and it decides which agents may
own a step:

| `build_mode` | Set by | What it means |
|---|---|---|
| `design-only` | `init`, which defaults to it | No org is on file. Only agents whose frontmatter says `requires_org: false` may own a step, so metadata steps go to `metadata-builder`, which builds artefacts from the cited skills' `references/metadata-examples.md` and `templates/` and runs their `scripts/check_*.py`. |
| `org-connected` | `init --org-alias <alias>`, which also stores `org: {"alias": "<alias>"}` | An org alias is on file, so the org-requiring designer agents in § 4 become eligible to own steps. The layer still never deploys; the alias exists so an owning agent may read the org, nothing more. |

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
└── reports/                  # milestone verification reports (written, not rendered)
```

Committed example: `examples/builds/case-onboarding/` — the canonical
end-to-end test case, built from
`skills/admin/case-management-setup/references/worked-example-case-intake.md`.
`.sfskills/` is gitignored, so a build becomes a committed example only through
`build_plan.py export <plan> <dest-dir>` (`--force` to replace an existing one),
which copies the whole build directory across and refuses to run until
`validate` passes.

## 3. Lifecycle and human gates

| Stage | Who runs it | Produces | Gate (human) |
|---|---|---|---|
| Intake | `/clarify-requirements` → `requirements-clarifier` | `plan.json` (status `clarifying`), `CLARIFICATIONS.md` | **G1** answers: every `blocking` question answered or explicitly deferred |
| Plan | `/plan-build` → `build-planner` | scope, decisions, milestones, steps; status `planned` | none yet |
| Verify | `/verify-plan` → `plan-verifier` (adversarial, 3 lenses) | verdicts on plan; status `verified` or `plan-rejected` | **G2** plan approval |
| Build | `/run-build` → workflow `build-from-requirements` | per milestone: artefacts, tests, docs, report; status `building` | **G3** per milestone acceptance, plus a `step:<id>` gate on every human-gated step |
| Done | — | status `done` | — |

Gate records live in `plan.json.human_gates[]` with `status`, `by`, `at`,
`notes`. There are four gate names, and the pattern is exact:

```text
^(clarifications|plan|milestone:M[0-9]+|step:M[0-9]+-S[0-9]{2,})$
```

Rules:

- Agents never approve a gate. `scripts/build_plan.py gate` is the only writer
  of a gate decision, and a human is the only decider.
- `ensure-gates` adds the missing records as `pending`: one per milestone, plus
  a `step:<step-id>` gate for **every step whose `human_gate` is `true`**.
  Adding a pending record is bookkeeping, not approval.
- A human-gated step is excluded from `next` until its `step:<id>` gate is
  `approved`; `next` prints the reason rather than silently shortening the list.
- `set-status <step> running` is **refused** (ERROR, nothing written) when the
  step's `human_gate` is true and its `step:<id>` gate is not approved, or when
  the step's milestone is not the current runnable milestone. The two refusals
  share one blocker check, so a step cannot be claimed around either gate.
- `gate clarifications approve` is refused while any clarification with
  `kind: blocking` is still `open`.
- `gate plan approve` is refused unless `plan.status` is `verified` — approval
  is of a verified plan or of nothing.
- `gate milestone:Mk approve` is refused unless `milestone:M(k-1)` and `plan`
  are both approved and every step in `Mk` is `documented`, or is `blocked`
  with a recorded reason — the blocked steps and their reasons are printed, so
  accepting a milestone with known gaps is a decision the human sees.
- `gate milestone:Mk reject` sets that milestone's status to `rejected` and
  leaves the build at `building`.
- `gate plan reject` and `gate clarifications reject` write even when semantic
  validation reports ERRORs — a rejection must be recordable on exactly the
  broken plan that earned it. Schema errors still block the write.
- The build workflow refuses to start a milestone whose predecessor gate is not
  `approved`, and returns after producing a milestone report so the human can act.
- Re-planning after a rejected gate is a new plan version (`plan.version` + 1);
  earlier versions stay in `plan.history[]`.
- Questions are never capped. A clarifier that thinks a question is needed asks
  it, marks it `blocking` or `informational`, and proposes a default. The human
  may accept all defaults in one action.

## 4. Steps and step types

A step is the unit of build. Each step has exactly one owning run-time agent
from the roster (`agents/_shared/SKILL_MAP.md`) and one step type. The owner
depends on `build_mode`: the designer agents in the second column mostly
declare `requires_org: true`, so in a `design-only` build the owner is the
third column instead.

| Step type | Owning agents, org-connected (examples) | Design-only owner | Artefacts | Molecular tests the tester runs |
|---|---|---|---|---|
| `object-model` | `object-designer` | `metadata-builder` | CustomObject / CustomField XML, picklists, record types | skill checkers for object/field/picklist skills; XML parse; package.xml consistency |
| `access` | `permission-set-architect`, `profile-to-permset-migrator` | `metadata-builder` | PermissionSet / PSG / sharing XML | permission-set + sharing checkers; no ModifyAllData surprises |
| `validation` | `object-designer` | `metadata-builder` | ValidationRule XML (`validationRules/` under the object) | validation-rule checkers; every field token in the formula resolves; XML parse |
| `automation` | `flow-builder`, `apex-builder`, `flow-orchestrator-designer` | `metadata-builder` (declarative), `apex-builder` (Apex) | Flow XML, Apex + tests | flow/apex checkers; Apex test class present; fault paths |
| `routing` | `assignment-and-auto-response-rules-designer`, `omni-channel-routing-designer`, `lead-routing-rules-designer` | `metadata-builder` | AssignmentRules / Queue / routing XML; Email-to-Case and Web-to-Case intake settings | assignment-rules checker; queue membership; business hours present |
| `sla` | `entitlement-and-milestone-designer`, `business-hours-and-holidays-configurator` | `metadata-builder` | EntitlementProcess / MilestoneType / BusinessHours XML; EscalationRules | entitlements checker; timeTriggers sanity; escalation actions name a real queue or user |
| `ui` | `path-designer`, `object-designer` (layouts), `email-template-modernizer` (templates) | `metadata-builder` | Layout / FlexiPage / PathAssistant XML; ListView; Report + ReportFolder; EmailTemplate | layout + path checkers; list-view filter fields resolve; report + email-template checkers |
| `data` | `csv-to-object-mapper`, `data-loader-pre-flight` | `bulk-migration-planner` | mapping files, load plan | preflight checker; mapping resolves |
| `integration` | `bulk-migration-planner`, `integration-catalog-builder` | `bulk-migration-planner` | pattern decision, contracts | integration checkers |
| `docs` | `config-workbook-author`, `story-drafter` | `story-drafter` (workbook, stories), `metadata-builder` (package.xml, deploy order) | workbook, stories, `package.xml`, the deploy-order note | workbook linter; manifest consistency against the milestone's artefacts |
| `custom` | any roster agent | any roster agent with `requires_org: false` | declared in the step | declared in the step's `acceptance_tests` |

**Agent eligibility.** A step's `agent` is legal only when all three hold:
`class: runtime`; `status` is a valid non-deprecated value of the
`agent-frontmatter` schema enum (`stable` or `beta`); and either `build_mode`
is `org-connected` or that agent declares `requires_org: false`.
`build_plan.py validate` enforces all three as ERRORs, and the plan verifier's
executability lens applies the same rule — so an org-requiring agent is not
refuted merely for requiring an org when the plan is `org-connected`.

**Where the commonly-missed artefacts live.** These are not new types; they are
rows of the types above, named here so a planner does not conclude the layer
has no home for them:

| Artefact | Step type |
|---|---|
| Validation rules | `validation` |
| Escalation rules (and their time triggers) | `sla` |
| List views | `ui` |
| Reports, dashboards and their folders | `ui` |
| Email templates | `ui` |
| Email-to-Case and Web-to-Case intake | `routing` |
| `package.xml` and the deploy-order note | `docs` |

In a design-only build every one of them is a `metadata-builder` step.

**Adding a step type is not one edit.** It touches, in this order: this table
and the artefact map above it; `STEP_TYPES` in `scripts/build_plan.py`; the
`type` enum in `agents/_shared/schemas/build-plan.schema.json`; the step-type
list in `agents/build-planner/AGENT.md` Step 6; and the step-type → workbook
section map in `agents/build-doc-keeper/AGENT.md` Step 4. The doc keeper's map
carries a default section — **Other configuration** — so a type added
everywhere else but missed there degrades to a placed row with a note rather
than to a failed documentation run. An owning agent must exist in the roster
for the new type, and a checker the tester can call is optional.

Each step records: `id`, `milestone`, `type`, `title`, `agent`, `skills[]`
(must resolve), `templates[]`, `decision_trees[]`, `inputs{}`, `outputs[]`
(paths under `artefacts/<step-id>/`), `depends_on[]`, `acceptance_tests[]`,
`status`, `human_gate`, `runs[]`.

Step status machine: `pending → running → built → tested → documented`, with
`failed` and `blocked` as side exits. Two more transitions exist for recovery:
`failed → pending` (reset a step for retry) and `running → running` (re-claim a
step on resume, which appends a run rather than overwriting one). `next` still
offers `pending` steps only — steps whose `depends_on` are all `documented`, in
the current (approved) milestone, excluding any step whose `step:<id>` human
gate is not approved.

## 5. Acceptance tests

Every step has ≥ 1 acceptance test; every milestone has ≥ 1. Types:

| type | runner | pass condition |
|---|---|---|
| `checker` | `python3 skills/<domain>/<slug>/scripts/check_*.py --manifest-dir artefacts/<step>` | exit 0 **and** `check-outputs` ok |
| `xml` | ElementTree parse of every `*.xml`/`*-meta.xml` in the step's artefacts | all parse |
| `manifest` | every artefact type/member appears in `package.xml`; no member without a file | consistent |
| `command` | a stdlib-only `python3 …` command declared in the plan, over a path in the repo or the build dir (never a deploy — see the deny-list below) | exit 0 |
| `manual` | a checklist line the human ticks at the milestone gate | ticked |

The tester never invents a test; it runs what the plan declares plus the
always-on `xml` and `manifest` checks. If a declared checker does not exist,
the step is `blocked`, not silently passed. The always-on `manifest` check
**fails** — it does not skip — when the step's type is a metadata type
(`object-model`, `access`, `validation`, `automation`, `routing`, `sla`, `ui`)
and no `package.xml` exists under the step's artefacts or those of a step it
depends on.

`validate` enforces three constraints on declared tests, all ERRORs:

1. **Deploy deny-list.** No acceptance-test `command` may match, case-insensitively:

   ```text
   \bsf\b[^|;&]*\bdeploy\b|\bsfdx\b|force:(source|mdapi):deploy|\bcurl\b|\bwget\b|\|\s*(ba)?sh\b|bash\s+-c|python3?\s+-c|\brm\s+-rf\b|\bgit\s+push\b
   ```

   The layer never deploys, never fetches, never pipes a download into a shell,
   never inlines a `-c` program the reviewer cannot read, and never pushes.
2. **Checker shape.** A `checker` test's `command` must match
   `^python3 skills/[a-z]+/[a-z0-9-]+/scripts/check_[a-z0-9_]+\.py\b`, and the
   file must exist on disk. A checker that does not exist is an ERROR at plan
   time, not a WARN — catching it here is one re-plan cheaper than catching it
   when the tester blocks the step.
3. **Command shape.** A `command` test must start with `python3 ` and reference
   a path under the repo or under the build directory.

**Outputs must exist.** `check-outputs <plan> <step-id>` confirms that every
path in the step's `outputs[]` exists under the build directory, is non-empty,
and — for `*.xml` / `*-meta.xml` — parses. It prints
`{ok, missing[], empty[], malformed[]}` and exits 1 when not ok. Two status
transitions depend on it:

- `set-status <step> built` is refused unless `check-outputs` passes, so a
  runner whose owning agent wrote nothing cannot advance the step.
- `set-status <step> tested` additionally requires
  `tests/<step-id>/results.json` to exist with `"passed": true`.

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
other agent; they do not embed Salesforce knowledge of their own. The same is
true of `metadata-builder`, the org-free builder that owns the metadata step
types in a design-only build (§ 4).

## 7. Workflows

- `.claude/workflows/plan-verify.js` — args `{build_dir}`; three adversarial
  lenses in parallel (executability, grounding, testability) per step, then a
  synthesis agent that writes the verdicts with `build_plan.py set-verification
  --file`. Returns the blocker list. Deterministic: no barrier except the final
  synthesis.
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

- `scripts/build_plan.py` (stdlib-only) is the single writer of plan state,
  derived views and gate records. Its subcommands: `init`, `validate`,
  `render`, `ingest-answers`, `next`, `set-status`, `check-outputs`, `gate`,
  `status`, `ensure-gates`, `set-clarifications` (which also takes `--summary
  "<paragraph>"`, the only writer of `requirement.summary`), `set-plan`,
  `set-verification`, `set-milestone`, `export`. Agents call it; they do not
  re-implement it, and they do not edit `plan.json` by hand.
- `python3 scripts/validate_envelope.py <envelope.json>` validates an agent's
  output envelope against `agents/_shared/schemas/output-envelope.schema.json`
  with its `urn:` sub-schema refs resolved (bare `jsonschema` cannot resolve
  them), so an agent in this loop can check its own envelope before writing it.
- The four `set-*` writers exist so no agent needs a hand edit:
  `set-clarifications <plan> --file <json>` (the clarifier's question set),
  `set-plan <plan> --file <json>` (the planner's scope / fit-gap / decisions /
  milestones / steps, in one validated write), `set-verification <plan> --file
  <json> --outcome verified|plan-rejected` (the verifier's block), and
  `set-milestone <plan> <Mk> --status verified|rejected --report-path <path>`
  (the milestone verifier's verdict and report path).
- Every agent invocation in the loop is recorded in `plan.json.steps[].runs[]`
  with the envelope path. Re-running a step appends a run; it never overwrites
  history. `set-status … --started <iso>` alone records a run entry, with the
  agent defaulting to the step's own `agent`.
- The planner may only assign agents that are eligible per § 4 — `class:
  runtime`, a non-deprecated `status` from the agent-frontmatter enum, and
  org-free unless `build_mode` is `org-connected` — and it may only cite skills
  that resolve on disk.
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
