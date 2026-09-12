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
`set-verification`, `set-milestone`, `set-status`, `amend-step`, `gate`,
`ensure-gates`. A surgical JSON edit is a defect, not a shortcut: it is how a
plan acquires a shape the validator never saw.

`set-plan` refuses to run while the build is `verified`, `approved`, `building`
or `done` (`PLAN_FROZEN_STATUSES`) — replacing scope/milestones/steps wholesale
mid-build would discard recorded gates. That leaves no writer for the ordinary
case of a pending step's declared fields turning out to be wrong once the build
is under way (a missing output path, a manifest member typo in a test
description, a spaced value in `inputs{}`, a checker to add to
`acceptance_tests[]`). `build_plan.py amend-step <plan> <step-id> --file
<amendment.json> --by <who> --reason "<why>"` is that writer: it replaces one
or more of `inputs`, `outputs`, `acceptance_tests`, `skills`, `templates`,
`decision_trees`, `notes`, `title` on a single step, wholesale per field (no
merge). It is scoped narrowly on purpose — refused unless the build status is
`building` or `approved`, the step's own status is still `pending` or
`blocked` (a step that has already run is rebuilt via `documented` ->
`running`, or reset via `failed` -> `pending`, never amended in place), and the
step's own `step:<id>` gate, if it carries one, is not yet `approved` (an
amendment would invalidate what the human signed off; reject that gate first).
It **never** touches `human_gates[]`, a step's `status`, or `runs[]` — those
stay `gate`'s and `set-status`'s alone — and it records what changed (who,
when, why, which fields, their prior values) in the step's `amendments[]`
before re-validating the whole plan, refusing the write if the result carries
any ERROR.

`--prose-only` is a narrower mode for the case that keeps recurring once a
build has steps behind it: a test's `description` or a step's `notes` turns
out to have narrated the wrong outcome, even though the test itself (its
`type`/`command`/`expected`/`scope`) still runs exactly as intended.
`amend-step --prose-only` accepts `--file` holding only `notes` and/or an
`acceptance_tests` array of the same length with every index's structural
fields unchanged (only `description` may differ), and in exchange allows the
step to be at any status except `running` and does not require an
already-approved `step:<id>` gate to be rejected first — prose does not
invalidate a signature. The amendment record carries `"prose_only": true` so
`amendments[]` distinguishes a text correction from a substantive one.

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
├── skills -> ../../../skills # symlink written by init/ensure-gates so declared checker commands resolve here
├── artefacts/<step-id>/      # what each step produced (metadata XML, Apex, Flow, JSON)
├── tests/<step-id>/          # tester outputs (checker stdout, results.json)
├── envelopes/<step-id>/      # each agent run's JSON envelope (validate with scripts/validate_envelope.py)
├── inputs/<stage-or-step>/   # JSON handed to build_plan.py set-* --file (not envelopes)
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
| `docs` | `config-workbook-author`, `story-drafter` | `build-doc-keeper` (workbook, traceability, deploy order, UAT pack, acceptance criteria), `story-drafter` (the story backlog), `metadata-builder` (the build-level `package.xml`) | workbook, traceability matrix, story backlog, `uat-test-cases.yaml`, the compiled acceptance criteria, `package.xml`, the deploy-order note | workbook linter; `check_uat_case.py` over the compiled pack; manifest consistency against the milestone's artefacts |
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

In a design-only build every one of them is a `metadata-builder` step, with one split inside the `docs` row: `metadata-builder` writes the `package.xml` and the per-step deploy-order note, while the workbook, the traceability matrix and the compiled build-wide deploy order are `build-doc-keeper`'s — it is the agent that wrote those rows step by step, and `config-workbook-author` is `requires_org: true` and therefore ineligible here.

The UAT test-case pack (`uat-test-cases.yaml`) and the compiled acceptance-criteria document are `build-doc-keeper`'s too, on the same compile run and for the same reason: they are collations of records the build already holds — the `manual` acceptance tests on every step and milestone, and the per-story criteria in the story backlog — written in the shapes `skills/admin/uat-test-case-design` and `skills/admin/acceptance-criteria-given-when-then` define in their `references/worked-examples.md`. `story-drafter` owns the story backlog itself and the criteria inside it; its Output Contract names no case pack and no standalone criteria file, so a plan that declares either on a `story-drafter` step declares an output that agent does not produce.

**Borrowing a roster agent from outside Tier 4.** `story-drafter` is a Tier-2 agent with no build-layer clause in its contract: it takes `discovery_artifact_path`, `discovery_artifact_kind` and `feature_scope`, and it persists to its own `default_output_dir`. That does not make it ineligible. The planner maps those inputs from the build directory into the step's `inputs{}` and declares the step's outputs under `artefacts/<step-id>/`; `build-step-runner` relocates what the agent wrote onto those declared paths and records the move. The same accommodation applies to any roster agent a plan borrows for a step, on two conditions:

1. **Read the Inputs table *and* the Escalation / Refusal Rules section, not either alone.** The table states what the agent needs; the refusal section states what it does when it does not get it, and the two are authored separately — an input the table marks "yes for design" is often the same one a single refusal line turns into a stop before the agent reads the plan. `sandbox-strategy-designer` is the standing case: five inputs are mandatory for a design run (`mode`, `team_size`, `concurrent_workstreams`, `release_cadence`, `data_sensitivity`) and its Escalation section reads, in full, "No team size / cadence → refuse." Every input either section makes mandatory is mapped into `inputs{}` from an answered clarification, from `requirement.md`, or from a `depends_on` step's outputs. When one exists nowhere on file the step is `blocked` with `blocked_reason: "borrowed agent requires <inputs>"`, naming them.
2. **Declare only outputs the agent's Output Contract names.** A borrowed agent produces what its contract says it produces; a path in `outputs[]` with no counterpart there is an artefact nobody writes, `check-outputs` never confirms it, and the step cannot reach `built`. Re-own the step, or move the output to the agent that does declare it. This condition wins over § 5's declare-a-manifest rule wherever the two meet, and the one place they meet — `apex-builder`, whose Output Contract names no `package.xml` — is settled in § 5 under **The Apex exception**: the Apex step declares its classes and their meta XML, and the build-level manifest step aggregates the members.

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
`failed` and `blocked` as side exits. Three more transitions exist for recovery:
`failed → pending` (reset a step for retry), `running → running` (re-claim a
step on resume, which appends a run rather than overwriting one), and
`documented → running` (rebuild a finished step after a finding that reached it
late — a milestone report, a mock deploy, a skill fix). A rebuild appends a run
with the caller's `reason`, drops the step back to `built` when it completes so
the tester and doc-keeper run again, and leaves the milestone above it stale
until `/verify-milestone` is re-run; it never reaches around a pending
`step:<id>` gate. `next` still
offers `pending` steps only — steps whose `depends_on` are all `documented`, in
the current (approved) milestone, excluding any step whose `step:<id>` human
gate is not approved.

## 5. Acceptance tests

Every step has ≥ 1 acceptance test; every milestone has ≥ 1. Types:

| type | runner | pass condition |
|---|---|---|
| `checker` | the command as declared in the plan — default form `python3 skills/<domain>/<slug>/scripts/check_*.py --manifest-dir artefacts/<step>`; a checker that takes a positional path or `--file` is declared with that form instead. Carries an optional `scope` of `step` (default) or `build` — see **Checker scope** below | exit 0 **and** `check-outputs` ok |
| `xml` | ElementTree parse of every `*.xml`/`*-meta.xml` in the step's artefacts | all parse |
| `manifest` | every artefact type/member appears in `package.xml`; no member without a file | consistent |
| `command` | a stdlib-only `python3 …` command declared in the plan, over a path in the repo or the build dir (never a deploy — see the deny-list below) | exit 0 |
| `manual` | a checklist line the human ticks at the milestone gate | ticked |

`step-tester` executes a declared `checker` command verbatim once the
deny-list below has cleared it, and never rewrites it — no flag is appended,
removed or re-ordered, and no path is substituted. It runs the command **from
the build directory**: `init` (and `ensure-gates`, for builds that predate
this) give the build directory a `skills` symlink to the repo's `skills/`, so
the declared `skills/<domain>/<slug>/scripts/check_x.py` and
`--manifest-dir artefacts/<step-id>` both resolve exactly as written. From the
repo root the checker path resolves but `artefacts/` does not, and a correct
step reads as failing. A checker invoked with an
argument its own parser does not define exits on a usage error, which reads as
a failing step when nothing about the artefacts is wrong.

> **Follow-up: converge checker argument forms.** `--manifest-dir <dir>` is the
> form this layer standardises on and every new skill checker should take it.
> Three predate it and are declared with their own form until they are changed:
> `skills/admin/email-templates-and-alerts/scripts/check_email_templates.py`
> (positional `paths…`),
> `skills/admin/user-story-writing-for-salesforce/scripts/check_invest.py`
> (positional `path`) and
> `skills/admin/configuration-workbook-authoring/scripts/check_workbook.py`
> (`--workbook`, with `--file` as its alias). Meanwhile `validate` WARNs — it
> does not ERROR — on a `checker` command with no `--manifest-dir`, saying the
> checker declares a non-standard argument form and the tester will run it
> verbatim.

### Checker scope

**The literal command governs.** `step-tester` runs the declared `command`
string exactly as written and substitutes no path, so the tree a checker
actually reads is the one spelled into that string — never the one `scope`
names. `scope` is the plan's declared **intent** for the test: it states which
tree the author meant the exit code to stand for, and `render` prints it beside
the command so a reader of PLAN.md can see that claim without re-deriving it
from the flags. A `checker` acceptance test may carry one:

| `scope` | The `--manifest-dir` the command itself must carry | When to declare it |
|---|---|---|
| `step` (default, and what is assumed when the field is absent) | `artefacts/<step-id>` — the step's own artefacts | the checker's assertions are all satisfiable inside one step's output |
| `build` | `artefacts` — the whole tree | the checker asserts a link between files that different steps write |

**Intent and command must agree.** A test declaring no `scope` while passing
`--manifest-dir artefacts` is not thereby build-scoped; it is a test whose
declared reading and executed reading disagree, and nothing downstream can tell
which of the two its exit code stands for. `validate` WARNs on the
disagreement; `agents/build-planner/AGENT.md` Step 6 writes the two in
agreement in the first place, and the plan verifier's testability lens refutes
a test where they diverge. A checker taking a positional path, `--file` or
`--workbook` rather than `--manifest-dir` carries no path for `scope` to
disagree with — declare the scope the test's reading actually needs and say in
its `description` which tree that is.

**At milestone level the scope is always `build`.** A milestone acceptance test
runs once every step in the milestone is documented, and exists to assert what
no single step owns, so it reads the whole `artefacts/` tree by definition —
`validate` passes no step type when it checks a milestone's tests, and there is
no narrower reading for `scope` to select. Declaring it on a milestone test is
redundant rather than wrong. A milestone test whose command points inside one
step's directory is a step test filed at the wrong level: move it onto that
step, or widen the command to `artefacts`.

**Cross-referential checkers.** Some checkers assert a relationship spanning
two metadata files that the plan assigns to two different steps. Run at step
scope, such a checker sees one half of the pair and either fires on a correct
artefact or falls silent on a broken one — both of which look like a working
test until someone runs the build. Four in the library behave this way today,
and this is the documented list `validate` warns against:

| Checker | The cross-reference it asserts |
|---|---|
| `check_escalation_rules.py` | an escalation action's `assignedTo` → a queue or user another step created |
| `check_omni_channel_routing_setup.py` | a routing configuration → the queue it pushes from, and a service channel → its presence statuses |
| `check_list_views_and_compact_layouts.py` | a compact layout → the `compactLayoutAssignment` on the `CustomObject` and record types, which belong to the object-model step |
| `check_permission_set_architecture.py` | a permission set's object and field permissions → the object metadata another step wrote |

When one of these is declared on a `routing`, `sla` or `access` step at `scope:
"step"`, `validate` WARNs and names the two remedies: declare `"scope":
"build"` on that test, or carry the assertion in a milestone acceptance test
running the same checker across `artefacts/`. Whichever is chosen, the step's
test `description` says which one carries the cross-reference, so a reader is
not left inferring it from the exit code. The list is hard-coded rather than
detected, so a checker that becomes cross-referential is added here and in
`agents/build-planner/AGENT.md` Step 6 in the same change.

The tester never invents a test; it runs what the plan declares plus the
always-on `xml` and `manifest` checks. If a declared checker does not exist,
the step is `blocked`, not silently passed. The always-on `manifest` check
**fails** — it does not skip — when the step's type is a metadata type
(`object-model`, `access`, `validation`, `automation`, `routing`, `sla`, `ui`)
and no `package.xml` exists under the step's artefacts or those of a step it
depends on. The one carve-out is the `apex-builder`-owned `automation` step
described under **The Apex exception** below: its members live in the
build-level manifest, so the check records skipped-not-applicable and names
that step rather than failing.

**Every `metadata-builder`-owned metadata step declares
`artefacts/<step-id>/package.xml` in its `outputs[]`.** `metadata-builder`
writes one on every run, but an agent-side guarantee is invisible to a reader
of `plan.json` and invisible to `check-outputs`, which only ever confirms paths
the plan declared. Declaring it turns the manifest the tester reads into a file
the plan promised and the CLI verifies, on all seven metadata types alike.

**The Apex exception, and why it is not an exemption.** `apex-builder` is the
other design-only owner of an `automation` step, and its Output Contract names
no manifest — it produces class bodies, their `.cls-meta.xml` / `.trigger-meta.xml`
siblings, an integration note, a governor-limit budget and a test plan. Section 4
condition 2 forbids declaring an output the owning agent does not produce, so an
`apex-builder` step that declared `package.xml` would be caught between the two
rules. It does not declare one. It declares its `.cls` / `.trigger` files and
their meta XML, and the build-level manifest step — type `docs`, owned by
`metadata-builder` — aggregates its `ApexClass` and `ApexTrigger` members into
the build's `package.xml` alongside every other step's, and `depends_on` the
Apex step to do it. Because that dependency runs the other way, the Apex step
has no manifest of its own to read: its always-on `manifest` check records
skipped-not-applicable, naming the build-level manifest step that carries its
members, rather than failing for the absence of a local file. The rule is
unchanged for every `metadata-builder`-owned step of any of the seven metadata
types.

`validate` enforces three constraints on declared tests, all ERRORs:

1. **Deploy deny-list.** No acceptance-test `command` may match, case-insensitively:

   ```text
   \bsf\b[^|;&]*\bdeploy\b|\bsfdx\b|force:(source|mdapi):deploy|\bcurl\b|\bwget\b|\|\s*(ba)?sh\b|bash\s+-c|python3?\s+-c|\brm\s+-rf\b|\bgit\s+push\b
   ```

   The layer never deploys, never fetches, never pipes a download into a shell,
   never inlines a `-c` program the reviewer cannot read, and never pushes.

   The one org-facing check the layer offers is validation, and it is the
   human's to run, not an agent's: `scripts/mock_deploy.py <plan.json>
   --org-alias <alias> --milestone <id> [--mode source|manifest]` assembles the
   selected steps' artefacts into a source tree and runs `sf project deploy
   start --dry-run` (`checkOnly: true` — the flag is hard-coded and the script
   has no deploy option). Run it after a milestone verifies and before the G3
   decision; its `summary.md` under `reports/mock-deploy/<ts>/` is evidence for
   the gate. Manifest mode is the only check that reads the merged
   `package.xml`. The case-onboarding example shows why it matters: three
   milestones' worth of green checkers let five platform rules through that
   only the org caught (`examples/builds/case-onboarding/reports/MOCK-DEPLOY-M1.md`).
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
  `render`, `ingest-answers`, `next`, `set-status`, `amend-step`,
  `check-outputs`, `gate`, `status`, `ensure-gates`, `set-clarifications`
  (which also takes `--summary "<paragraph>"`, the only writer of
  `requirement.summary`), `set-plan`, `set-verification`, `set-milestone`,
  `export`. Agents call it; they do not re-implement it, and they do not edit
  `plan.json` by hand.
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
