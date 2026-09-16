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

amend-step --add-checker <skill-id> appends the standard checker test for a cited skill's scripts/check_*.py (the § 5 warning's remedy) without hand-writing the array.

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
`validate` passes. `--force` preserves a hand-written `README.md` at
`dest-dir`'s root across the replace — the build never produces one, so a
wipe-and-copy must not discard the operator's prose about the example.
When nothing is kept, export writes a generated README.md stub from the plan (title, tier, status, gates, counts, reports) for the operator to edit.

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

Gate records keep a per-gate `history[]` of prior states (oldest first): whenever
`gate` overwrites an already-decided record, the previous `{status, by, at,
notes}` is appended first, so a re-sign never erases the original signature
from the machine record. `gate <plan> <gate> resign --by … --notes …` records
new evidence for a standing approval without changing any decision (status stays
`approved`; no milestone, build, or step status moves) — it is the path for a
milestone re-verified after a repair (the § 8 re-verification path) when the
verdict did not change. Use `approve` / `reject` only when the decision itself
changes.

## 3.1 Ceremony scales to the ask

§ 3 is one shape and its guarantees are not negotiable. What varies is how much
ceremony they cost. `plan.json` carries an optional `scale` — `ask`, `feature`
or `project` — and it selects the ceremony, never the guarantees. A plan with no
`scale` is `project`, so every build written before this section behaves exactly
as it did.

### The sizing rule — deterministic, and printed

`requirements-clarifier` takes four counts from `requirement.md` and its Step 2
searches, before it harvests a question: **D** distinct metadata types that
need **their own step** — their own agent, their own tests, or their own
position in deploy order — **not** every metadata type the finished build will
touch. A supporting artefact a single step legitimately ships alongside its
primary type never raises D: a `$Permission` bypass's CustomPermission +
PermissionSet riding along with the validation rule that reads them, a field's
list-view entry, a flow's custom label. **S** cited skills carrying a
`## Questions to Ask Before Configuring` table (after dedupe), **O** distinct
objects named, **X** whether an integration or a data migration is implied (an
external system, an inbound or outbound API, a bulk load). The clarifier
re-checks the tier exactly **once**, after the answers land, against what the
answers actually require rather than what Step 2 guessed — re-tiering upward
only when an answer requires a genuinely new step (its own agent, tests, or
deploy-order position), never for a supporting artefact an existing step
absorbs — and prints the recount in the same sizing-line format.

| Signal | `ask` | `feature` | `project` |
|---|---|---|---|
| D metadata types | ≤ 2 | 3–6 | ≥ 7 |
| S skills with a question table | ≤ 3 | 4–8 | ≥ 9 |
| O objects named | ≤ 1 | 2–3 | ≥ 4 |
| X integration / migration | no | implied | implied, plus a load or a second system |

The tier is the **highest** tier any single signal reaches — not an average and
not a vote. Automation on its own never bumps a tier: "write me an Apex trigger"
is D=2, S≤3, O=1, X=no, and it is an `ask`. Crossing a system boundary always
does, because a contract with someone else's system is the thing no checker can
settle. When a count cannot be taken — the requirement names no object, the
searches are ambiguous about which skills apply — **round up, never down**: an
over-ceremonied small ask costs minutes, an under-ceremonied large one ships an
unasked question. A human overrides with `init --scale <tier>`; the override is
recorded verbatim, and the clarifier still prints the counts that disagreed with
it. The printed line, quoted into the report rather than recounted:

```text
scale: ask (D=1 metadata type, S=2 skills with question tables, O=1 object, integration=no; no override)
```

### The three tiers

| | `ask` | `feature` | `project` |
|---|---|---|---|
| Clarification scope | only the cited skills' Questions-to-Ask rows, each with its proposed default; **one** round; ≤ 8 put to the human as blocking | those, plus one question per decision tree whose scope the requirement straddles (`standards/decision-trees/`); blocking questions are **not** capped at this tier — an integration feature legitimately asks 20–30 — answered in **one** round (a second round only when answers contradict each other); the tier is re-checked afterward only by the D/S/O/X recount (below), never by how many questions were asked | unchanged: every row of every cited skill plus the generic `admin/requirements-gathering-for-sf` set |
| Plan shape | 1 milestone, 1 step | 1 milestone, ≤ 5 steps | unchanged: 2–6 milestones |
| Verification | verifier runs **once** — three lenses over the one step, refutation-only; no re-plan round unless a blocker is CRITICAL (below) | ≤ 2 rounds | unchanged |
| Gates | two human decisions: `go` and `accept` | `clarifications`, `plan`, `milestone:M1` — plus a `step:<id>` record for every step the planner marks `human_gate: true` (credentials, permission sets, deletions), as § 3 requires | unchanged |
| Documentation | envelopes + one `RUN.md`; `decisions.md` appended at every scale (append-only and cheap — a one-step build still makes decisions); workbook and traceability skipped, `RUN.md` carries the artefact↔test rows | workbook optional, traceability required | unchanged |

**The `feature` plan-shape ceiling of ≤ 5 steps does not count the aggregating
Apex manifest step.** § 5's **The Apex exception** requires a build-level
`docs` step, owned by `metadata-builder`, whenever an Apex `automation` step
exists — it is the only place that Apex step's `ApexClass`/`ApexTrigger`
members reach a `package.xml`, and skipping it to stay under five steps would
leave the always-on `manifest` check with nothing to read. A `feature` plan
with five functional steps and this one manifest step is sized correctly, not
six-over-the-limit; `set-plan`/`validate`'s § 3.1 sizing-rule check is a WARN
only, never an ERROR (§ 3.1 "CLI deltas": an ERROR here would turn a re-tier
into a re-plan), so a plan carrying this step and reading the WARN applies the
carve-out by inspection rather than needing the CLI to special-case the count.

The ≤ 8 is **not** a cap on the harvest. § 3's "questions are never capped" and
the schema's "Never capped" both still hold: every row of every cited question
table still becomes a record in `clarifications[]`. `scale` decides only how
many are put to the human *in a round*. At `ask` the informational rows land
pre-filled from their `proposed_default` with `default_source` set and are
listed in `CLARIFICATIONS.md` as defaults applied; the blocking ones are asked.
If more than eight rows are blocking, the requirement was never an `ask`: the
clarifier re-tiers to `feature`, says so in the sizing line, and drops nothing.
The bound is a tier test, not a truncation.

This eight-blocking test applies at **`ask` only** — it is the signal that an
`ask` was mis-sized and belongs at `feature`. It has no analogue at `feature`:
a `feature` build is never re-tiered to `project` by counting blocking
questions, no matter how many land (20–30 blocking rows on an integration
feature is expected, not a signal). The only re-tier signal at any tier,
including from `feature` upward, is the D/S/O/X recount in "The sizing rule"
above, applied once, after the answers land, to what the answers actually
require — never applied by analogy from a question count.

**CRITICAL**, at `ask`, means exactly a refutation on the executability or
grounding lens — an ineligible agent, a skill or template that does not resolve,
a declared checker not on disk, a decision with no tree branch. Those earn one
re-plan. A testability refutation on the single step's own tests is fixed in
place with `amend-step` and recorded there; anything softer is a warning printed
at the `go` gate for the human to weigh.

### What never changes, at any scale

- Every cited skill is read in full and every row of its Questions-to-Ask table is harvested (§ 1 stage 1).
- Checkers run verbatim from the build directory, deny-list cleared, never rewritten (§ 5).
- Every agent run writes a validated envelope under `envelopes/<stage-or-step>/` (§ 2, § 8).
- `check-outputs` still gates `built`; `tests/<step>/results.json` with `"passed": true` still gates `tested`.
- `scripts/build_plan.py` is still the only writer of plan state. No hand edit, at any tier.
- Nothing deploys. `scripts/mock_deploy.py --dry-run` is still the human's own validation and its `summary.md` still the evidence a gate rests on — at `ask` it is the one command `RUN.md` ends with.
- A gate is still written only by `gate` and decided only by a human. Merging two gate records into one decision does not make an agent the decider of either.

### CLI deltas

- `init --scale ask|feature|project` — optional; unset leaves `scale` absent, and the clarifier's first pass sets it. Echoed on the `init` summary beside `build mode:`.
- `set-scale <plan> ask|feature|project --by <who>` — the clarifier's writer for a build `init` already created without `--scale`; allowed only while `status` is `intake` or `clarifying`, before `set-plan` has written a body (re-tiering a planned build is a re-plan, not a scale change). Refuses a change to an already-set scale unless `--force`, printing the old → new tier.
- Schema: `scale`, an optional top-level string with enum `["ask","feature","project"]`. No other schema change; absent = `project`.
- `validate` applies the tier's plan shape as **WARNs only** — a `scale: ask` plan with four steps warns and names the sizing rule. An ERROR here would turn a re-tier into a re-plan. It also warns when a step lists an open clarification under inputs.answers with no assumptions[] row applying a default to that step. It also warns when a step cites a skill whose scripts/check_*.py is declared as a checker test neither on the step nor on its milestone.
- `ensure-gates` reads `scale`: at `ask` it adds `milestone:M1` and **no** `step:` record, because the single step is written `human_gate: false`.
- `set-clarifications` reads `scale`: at `ask`, an incoming `open` informational row with a `proposed_default` and no `answer` is written `answer: <that default>`, `status: answered`, and `default_source` stamped `"proposed_default (scale: ask)"` when the row did not already carry one — the writer enforces the pre-fill guarantee itself rather than trusting every caller to have done it; blocking rows and rows already answered are untouched, and a later `ingest-answers` can still overwrite a filled default.
- `gate go …` and `gate accept …` are aliases legal only when `scale` is `ask`: `go` writes the `clarifications` and `plan` records in one invocation under one `--by` / `--at` / `--notes`, atomically — every member's precondition is checked against one plan snapshot before any of them is written, so a refusal on either leaves both untouched; `plan` is legal only once the build status is `verified`, which at scale `ask` the planner reaches without a prior G1 approval, because the human's answers to the blocking clarifications already **are** G1 in substance, and `go` simply signs the paperwork for both, together, once the verifier has passed the plan; `accept` writes `milestone:M1`. The stored gate **names** are unchanged, so the § 3 name pattern, every approval precondition and every rejection behaviour apply exactly as written.
- `status` prints `scale: <tier>` on the build-mode line (`project (default)` when absent). The schema is `additionalProperties: false` at the top level, so a human override is not persisted: `init` echoes `(human override: init --scale)` once, and `status` never prints an override marker.
- `render` emits `RUN.md` at the build root when `scale` is `ask`: what was built, every artefact path, the checker commands with their exit codes, the defaults applied and the assumptions they became, the `manual` acceptance lines, and the `mock_deploy.py` command to run next. It is a rendered view — never hand-edited. It is **not** added to `docs{}`, which is `additionalProperties: false`; a `docs.run` key is a separate schema change and is not made here.

### Agent deltas

- `requirements-clarifier` — **Inputs** (accept `scale`); **Step 1** (compute, print, pass to `init`); **Step 4** (`ask`: informational rows pre-filled from their defaults, plus the eight-blocking tier test, plus the one-time post-answer recount once `ingest-answers` runs); **Step 5** (one round, same one-time recount noted against the write-the-plan flow); **Step 6** (`ask`: print the single `gate go` command instead of G1-then-`/plan-build`).
- `build-planner` — **Step 5** ("between two and six" becomes exactly 1 at `ask` and at `feature`); **Step 6** (`ask`: one step, `human_gate: false`); **Step 7** (`ask`: `render` also writes `RUN.md`).
- `plan-verifier` — **Step 1** (a one-step plan is a plan); **Step 4** (`ask`: an `expected` observable only in a deployed org is a WARN, not a refutation, on the org-only manual test row — unchanged at `feature`, where the same row is a WARN for the same reason: the tester has no other way to exercise a manual acceptance test than the human's own UAT pass); **Step 6** (`ask`: one round, refutation-only, the CRITICAL list above, no second pass; `feature`: up to two rounds, and CRITICAL is narrower than at `ask` — a refutation earns a re-plan only when **the step would produce wrong or ungrounded artefacts**, the bar the verifier actually applies at this tier, rather than every executability/grounding refutation `ask`'s stricter list names).
- `build-doc-keeper` — **Step 4** (`ask`: `RUN.md` rows instead of workbook sections; `decisions.md` is still appended, exactly as at every other scale; leave the `traceability.md` stub alone).
- `milestone-verifier` — **the report** (`ask`: one page, and it is the `accept` gate's evidence).
- `build-step-runner` and `step-tester` — **no branch.** A step is a step at every scale, and that is the point.

### Worked example — "add a validation rule so Opportunity Amount can't go down after Closed Won"

1. `init` prints `scale: ask (D=1, S=2, O=1, integration=no)`.
2. Clarifier harvests `admin/validation-rules` and `admin/formula-fields`: five blocking rows — which profiles are exempt (default: none), does it fire on insert as well as update (default: update only), do integration users get the same rule (default: yes), where does the error show (default: on the Amount field), what does it say (default: the skill's worded example). Informational rows land pre-filled.
3. Human accepts all five defaults in `CLARIFICATIONS.md`, then `ingest-answers`. **[read 1]**
4. Planner: 1 milestone, 1 step `M1-S01`, type `validation`, agent `metadata-builder`, skill `admin/validation-rules`, outputs the rule XML plus `package.xml`, tests: the skill's checker, always-on `xml` and `manifest`, one `manual` line.
5. Verifier: three lenses, one round, no blockers; status `verified`.
6. **Decision 1** — `gate go approve`, after the one-page `PLAN.md`. **[read 2]**
7. `/run-build-step`: `metadata-builder` writes the rule; `check-outputs` passes; `built`.
8. `/test-build-step`: the checker runs verbatim; `results.json` `"passed": true`; `tested`.
9. Doc keeper renders `RUN.md`; milestone verifier writes the one-page report.
10. **Decision 2** — `gate accept approve`, after `RUN.md`. **[read 3]**
11. Printed, never run: `python3 scripts/mock_deploy.py <plan.json> --org-alias <alias> --milestone M1`.

**Two human decisions, one answer edit, three files read** — `CLARIFICATIONS.md`, `PLAN.md`, `RUN.md`, plus `reports/mock-deploy/<ts>/summary.md` if the human runs the dry run. `examples/builds/case-onboarding/` is the same loop at `scale: project`.

### The driver's log

Every scenario, at every scale, records how the loop was to drive, appended to
`reports/drivers-log.md`. This is the human-experience grade, and it is the
evidence this section is working; five lines, one block per run:

```text
scale:     ask (D=1 S=2 O=1 X=no; override: none)
questions: 5 asked · 5 defaults accepted · 0 deferred · rounds 1
gates:     go approved 14:02 · accept approved 14:19 · rejections 0 · re-plans 0
reads:     CLARIFICATIONS.md, PLAN.md, RUN.md (3 files)
minutes:   clarify 3 · plan+verify 4 · build+test 6 · read+decide 4 · total 17
```

A run whose `minutes` or `reads` are out of proportion to its `scale` is a
defect in this section, not in the driver.

## 4. Steps and step types

A step is the unit of build. Each step has exactly one owning run-time agent
from the roster (`agents/_shared/SKILL_MAP.md`) and one step type. The owner
depends on `build_mode`: the designer agents in the second column mostly
declare `requires_org: true`, so in a `design-only` build the owner is the
third column instead.

| Step type | Owning agents, org-connected (examples) | Design-only owner | Artefacts | Molecular tests the tester runs |
|---|---|---|---|---|
| `object-model` | `object-designer` | `metadata-builder` | CustomObject / CustomField XML, picklists, record types | skill checkers for object/field/picklist skills; XML parse; package.xml consistency |
| `access` | `permission-set-architect`, `profile-to-permset-migrator` | `metadata-builder` | PermissionSet / PSG / sharing XML, including `NamedCredential`, `ExternalCredential`, `ExternalCredentialParameter`/principals, and the `PermissionSet` grants of principal access that authorise them | permission-set + sharing checkers; no ModifyAllData surprises |
| `validation` | `object-designer` | `metadata-builder` | ValidationRule XML (`validationRules/` under the object) | validation-rule checkers; every field token in the formula resolves; XML parse |
| `automation` | `flow-builder`, `apex-builder`, `flow-orchestrator-designer` | `metadata-builder` (declarative), `apex-builder` (Apex) | Flow XML, Apex + tests | flow/apex checkers; Apex test class present; fault paths |
| `routing` | `assignment-and-auto-response-rules-designer`, `omni-channel-routing-designer`, `lead-routing-rules-designer` | `metadata-builder` | AssignmentRules / Queue / routing XML; Email-to-Case and Web-to-Case intake settings | assignment-rules checker; queue membership; business hours present |
| `sla` | `entitlement-and-milestone-designer`, `business-hours-and-holidays-configurator` | `metadata-builder` | EntitlementProcess / MilestoneType / BusinessHours XML; EscalationRules | entitlements checker; timeTriggers sanity; escalation actions name a real queue or user |
| `ui` | `path-designer`, `object-designer` (layouts), `email-template-modernizer` (templates) | `metadata-builder` | Layout / FlexiPage / PathAssistant XML; ListView; Report + ReportFolder; EmailTemplate | layout + path checkers; list-view filter fields resolve; report + email-template checkers |
| `data` | `csv-to-object-mapper`, `data-loader-pre-flight` | `bulk-migration-planner` | mapping files, load plan | preflight checker; mapping resolves |
| `integration` | `bulk-migration-planner`, `integration-catalog-builder` | `bulk-migration-planner` | pattern decision, contracts | integration checkers |
| `docs` | `config-workbook-author`, `story-drafter` | `build-doc-keeper` (workbook, traceability, deploy order, UAT pack, acceptance criteria), `story-drafter` (the story backlog), `metadata-builder` (the build-level `package.xml`) | workbook, traceability matrix, story backlog, `uat-test-cases.yaml`, the compiled acceptance criteria, `package.xml`, the deploy-order note | workbook linter; `check_uat_case.py` over the compiled pack; manifest consistency against the milestone's artefacts |
| `custom` | any roster agent | any roster agent with `requires_org: false` | declared in the step | declared in the step's `acceptance_tests` |

**Apex row note.** Every `templates/apex/**` class an Apex step's classes or tests reference ships as a verbatim copy (with its meta XML) in that same step's outputs, or in a dedicated "Apex foundations" step the plan runs first when more than one Apex step shares the dependency — see `agents/build-planner/AGENT.md` Step 6 and `agents/apex-builder/AGENT.md`'s provenance check.

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
`failed` and `blocked` as side exits. Four more transitions exist for recovery:
`failed → pending` (reset a step for retry), `running → running` (re-claim a
step on resume, which appends a run rather than overwriting one),
`documented → running` (rebuild a finished step after a finding that reached it
late — a milestone report, a mock deploy, a skill fix), and `built → running`
(re-run a step that has not been tested yet — e.g. a repair an operator probe
found before the tester ran) under the same gate preconditions as
`documented → running`: the milestone's gates and the step's own `step:<id>`
gate must already be approved, and the re-run appends to `runs[]` exactly like
`documented → running` does. Both rebuild edges append a run
with the caller's `reason`, drop the step back to `built` when it completes so
the tester and doc-keeper run again, and leave the milestone above it stale
until `/verify-milestone` is re-run; neither reaches around a pending
`step:<id>` gate. There is deliberately no `tested → running` edge — a repair
found after testing goes `tested → failed → pending → running` with a real
failure reason, not a fabricated one used to route around this table. `next`
still offers `pending` steps only — steps whose `depends_on` are all
`documented`, in the current (approved) milestone, excluding any step whose
`step:<id>` human gate is not approved. `next` also prints, on stderr, which
cited checkers each offered step has not declared and the exact amend-step
`--add-checker` command that declares them.

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

**Exit-policy forms differ, too, and that is a second axis from the argument
form above.** The argument-form note is about how a checker is *pointed at*
its metadata; this one is about what makes it *exit non-zero* once it has
read that metadata, and the library has not converged on one answer. Four
shapes are in active use: **bare** (the checker exits non-zero on any finding
at all, with no severity knob); **`--min-severity ERROR`** (only findings at
or above the named severity fail the run, so a checker carrying only WARN-tier
findings exits 0 by design); **absence of `--strict`** (the checker is lenient
by default and a finding only fails the run once `--strict` is passed, so a
declared test that omits the flag is deliberately accepting the lenient
reading, not forgetting the flag); and **`--fail-on HIGH`** (a named-severity
threshold spelled as its own flag rather than folded into `--min-severity`).
Layered on top of the argument-form split, a checker may also take **`--src`**
as its path argument rather than `--manifest-dir`, a positional path, or
`--file`/`--workbook` — a fourth argument form alongside the three the
Follow-up above already names. Neither axis is a `validate` ERROR; a checker
test's declared `command` is run verbatim regardless of which forms it uses.
What `agents/build-planner/AGENT.md` Step 6 now requires is that a step's
test `description` says, in one line, which exit-policy form and which
empty-directory behaviour (does an `artefacts/<step-id>/` with nothing in it
exit 0 or non-zero?) that specific checker relies on — the same
`--help`-then-fixture-run discipline Step 6 already applies to the argument
form, extended to the flag that decides pass/fail. Converging every checker on one exit-policy form and one argument form is
real work, the same shape of work the Follow-up above already tracks for
argument forms — a library backlog this layer documents and does not gate on,
not a defect a plan is refuted for encountering.

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
   `package.xml`. The tree is copied whole — every file under
   `artefacts/<step>/` except `package.xml`, `*.md` notes and dotfiles — and
   deploys at the highest `<version>` any selected step's `package.xml`
   declares (`--api-version` overrides; `summary.md` records the choice), because
   a later step may legitimately need a newer API than the first one pinned.
   The case-onboarding example shows why it matters: three milestones' worth
   of green checkers let five platform rules through that only the org caught
   (`examples/builds/case-onboarding/reports/MOCK-DEPLOY-M1.md`), and M3's
   case settings added three more (`MOCK-DEPLOY-M3.md`). `--test-level
   {NoTestRun,RunSpecifiedTests,RunLocalTests}` (default `NoTestRun`, i.e.
   unchanged behaviour) lets Apex actually execute during that same `--dry-run`
   validation rather than only compile (S2-F-06: every prior tier2-webhook run
   carried `runTestsEnabled: false`), so a milestone report resting on a
   `mock_deploy.py` run should cite the test-level `summary.md` recorded for
   that run, not assume tests ran. The summary lists coverage per class and
   marks any class under 75%, the threshold RunSpecifiedTests/RunLocalTests
   apply per class, not only in aggregate.
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
  `results.json` records the hashes of the artefacts it tested (`artefact_hashes`), and `tested` is refused when they have changed.

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
  (the milestone verifier's verdict and report path). On a milestone already
  `accepted`, `set-milestone` does not move its status and touches no gate: it
  appends a `milestones[].reverifications[]` entry and updates `report_path`.
  That is the **re-verification** path — run it whenever a documented step in
  an accepted milestone is re-run (a repair after an org finding), because the
  earlier report and `reports/MILESTONE-<Mk>-package.xml` are stale from that
  moment; the verifier appends a dated section to the existing report and
  regenerates the merged manifest, and the gate is re-signed (reject, then
  approve with notes naming the new evidence) only if the verdict or the
  evidence changed what the human accepted.
- Every agent invocation in the loop is recorded in `plan.json.steps[].runs[]`,
  carrying the envelope path when `--envelope` names one actually written.
  Re-running a step appends a run; it never overwrites history. `set-status …
  --started <iso>` alone (no `--envelope`) records a run entry with no
  `envelope_path` rather than a fabricated one, with the agent defaulting to
  the step's own `agent`.
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
