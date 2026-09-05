# /build-from-requirements — one requirement in, a verified build out

The overview command for the whole loop. You give a requirement in plain
English; the layer asks what it must ask, plans, verifies its own plan, then
builds milestone by milestone with a human gate at each seam.

It never deploys.

The contract is `standards/build-orchestration.md`. This page is the map; that
document is the authority.

## The five stages

```
1  Clarify   /clarify-requirements  -> every question the relevant skills say
                                      must be asked, with a proposed default
                                      answer, then `ingest-answers`
                                      ........................ GATE G1 (answers)
2  Plan      /plan-build            -> scope, fit-gap, decisions (each citing a
                                      decision-tree branch), milestones, steps
3  Verify    /verify-plan           -> three adversarial lenses per step:
                                      executability, grounding, testability
                                      ........................ GATE G2 (plan)
4  Build     /run-build <milestone> -> per step: runner -> tester -> doc keeper;
                                      then the milestone acceptance report
                                      (a step marked human_gate carries its own
                                      step:<id> gate before it may run)
                                      ........................ GATE G3 (per milestone)
5  Repeat    stage 4 per milestone until the last one is accepted
```

A gate is a human. Agents never approve one — `scripts/build_plan.py gate` is
the only writer of a gate record, and the workflows return the command for you
to run rather than running it.

## The exact sequence

```bash
# 1. Clarify — writes plan.json (status "clarifying") and CLARIFICATIONS.md.
#    The build is design-only unless it was init'd with --org-alias.
/clarify-requirements "<the requirement, or a path to a worksheet/backlog>"

# 2. Answer — in CLARIFICATIONS.md, on the `Answer:` line under each question,
#    or accept every proposed default in one action. Questions are never capped.
#    An answer may run to several lines: everything up to the next `### Q`
#    heading or a `---` rule belongs to it.

# 3. Read the answers back into plan.json. This is a step, not a formality:
#    nothing else moves an answer out of the rendered view, and the gate below
#    checks the ingested answers rather than the markdown.
python3 scripts/build_plan.py ingest-answers .sfskills/builds/<build-id>/plan.json
#    Add --allow-deferred if a blocking question was answered `DEFER: <reason>`.

# 4. Record G1. It is refused while any blocking question is still open:
python3 scripts/build_plan.py gate .sfskills/builds/<build-id>/plan.json clarifications approve \
  --by "<you>" --notes "answers complete"

# 5. Plan — scope, decisions, milestones, steps; status -> "planned"
/plan-build .sfskills/builds/<build-id>

# 6. Verify the plan — adversarial; status -> "verified" or "plan-rejected"
/verify-plan .sfskills/builds/<build-id>

# 7. Read the blockers. If rejected: fix, re-plan (a new plan version), re-verify.
#    If verified, record G2 — this is the plan approval, and it is refused
#    unless the plan status is exactly "verified":
python3 scripts/build_plan.py gate .sfskills/builds/<build-id>/plan.json plan approve \
  --by "<you>" --notes "plan approved"

# 8. Approve any step gate the plan asked for. A step with human_gate: true —
#    an access change, a deletion — will not run until you do, and `next` says
#    which ones are waiting:
python3 scripts/build_plan.py gate .sfskills/builds/<build-id>/plan.json step:M1-S03 approve \
  --by "<you>" --notes "<what you reviewed>"

# 9. Build the first milestone
/run-build .sfskills/builds/<build-id> M1

# 10. Read the acceptance report — the milestone verifier WRITES it at this
#     path; it is not rendered from plan.json. Tick the manual checklist, then
#     record G3. It is refused unless every step in M1 is documented, or
#     blocked with a reason (which it prints):
cat .sfskills/builds/<build-id>/reports/MILESTONE-M1-REPORT.md
python3 scripts/build_plan.py gate .sfskills/builds/<build-id>/plan.json milestone:M1 approve \
  --by "<you>" --notes "<what you checked>"

# 11. Next milestone. Repeat 9-10 until the last one is accepted.
/run-build .sfskills/builds/<build-id> M2
```

Each workflow returns the exact `gate_command` for its stage, read from
`build_plan.py gate --help` at run time — use that form if it differs from the
shape sketched above.

## Where the files live

`plan.json` is the only shared state. Every agent in the loop reads it before
acting and updates only the fields it owns — through a `build_plan.py`
subcommand, never by hand-editing the file. `PLAN.md` and `CLARIFICATIONS.md`
are **rendered** from it by `scripts/build_plan.py`; never hand-edit a rendered
view; change the plan through the CLI and re-render. The milestone acceptance
reports are the exception: `milestone-verifier` **writes** them, then records
each path with `build_plan.py set-milestone --report-path`.

```text
.sfskills/builds/<build-id>/
├── requirement.md            the human's input, verbatim
├── plan.json                 canonical state — the only shared state
├── PLAN.md                   rendered
├── CLARIFICATIONS.md         rendered; you answer here or in plan.json
├── decisions.md              append-only decisions log (doc keeper)
├── traceability.md           REQ -> step -> artefact -> test (doc keeper)
├── workbook/                 configuration workbook sections (doc keeper)
├── artefacts/<step-id>/      what each step produced (metadata XML, Apex, Flow, JSON)
├── tests/<step-id>/          tester output (checker stdout, results.json)
├── envelopes/<step-id>/      one JSON envelope per agent run
└── reports/                  milestone acceptance reports (written, not rendered)
```

`examples/builds/case-onboarding/` is the committed end-to-end example, produced
by running the loop rather than written by hand.

Everything outside the build directory is **read-only to a build**: `skills/`,
`agents/`, `templates/`, `standards/`, `registry/`, `docs/`. A build consumes
the library; it never edits it.

## The seven agents

| Agent | Slash | One job |
|---|---|---|
| `requirements-clarifier` | `/clarify-requirements` | collect the skills' Questions-to-Ask, dedupe, propose defaults |
| `build-planner` | `/plan-build` | scope, fit-gap, decisions, milestones, steps |
| `plan-verifier` | `/verify-plan` | refute the plan on three lenses |
| `build-step-runner` | `/run-build-step` | execute one step, store artefacts + envelope |
| `step-tester` | `/test-build-step` | run the step's molecular tests |
| `build-doc-keeper` | `/keep-build-docs` | PLAN.md, workbook, decisions, traceability |
| `milestone-verifier` | `/verify-milestone` | cross-step checks, acceptance report, G3 request |

They read skills like every other run-time agent. They hold no Salesforce
knowledge of their own — if a step needs a fact no cited skill states, the
runner marks it `blocked` with reason `skill-gap` and the doc keeper records it.
That is the signal to deepen a skill with `/add-skill`, never to freestyle.

They are the loop; they are not the builders. A step is owned by a roster agent
chosen per `standards/build-orchestration.md` § 4, and which one depends on the
plan's `build_mode`. Most designer agents need an org, so a **design-only**
build — the default — routes metadata steps to `metadata-builder`, which builds
from the cited skills' `references/metadata-examples.md` and `templates/`. A
build init'd with `--org-alias` is **org-connected**, and the designer agents
own their own rows again.

## What never happens

- **No deploy.** Not by an agent, not by a test, not by a workflow. Deploy is a
  human action outside the loop. The layer produces deploy-ready artefacts, a
  deploy order, and a validate-only command you may choose to run.
- **No agent-approved gate.** Agents report gate commands; humans record them.
- **No invented test.** The tester runs what the plan declares plus the
  always-on XML and manifest checks. A declared checker that does not exist
  blocks the step rather than passing it.
- **No freestyled pattern.** A step that cannot cite a skill, template or
  decision-tree branch for what it is doing fails the grounding lens at G2.
- **No concurrent writes to one path.** `/run-build` partitions each round into
  conflict-free batches before running anything.
- **No silent truncation.** Every bound the loop applies is logged: capped
  rounds, skipped steps, lenses that returned nothing.
- **No hand-edited rendered view.** `build_plan.py render` owns them.
- **No hand-edited `plan.json`.** Every field an agent owns has a subcommand
  that writes it: `set-clarifications`, `set-plan`, `set-verification`,
  `set-milestone`, `set-status`, `gate`, `ensure-gates`.
- **No step advancing on an empty directory.** `set-status … built` is refused
  unless `check-outputs` confirms every declared output exists, is non-empty
  and parses; `set-status … tested` needs `results.json` saying `passed: true`.
- **No deploy smuggled into a test.** `validate` ERRORs on a test command
  matching the deny-list — `sf … deploy`, `sfdx`, `force:source:deploy`,
  `curl`, `wget`, a pipe into a shell, `bash -c`, `python3 -c`, `rm -rf`,
  `git push` — and on a `checker` whose script is not on disk.
- **No secrets in the build directory.** Envelopes redact per
  `agents/_shared/DELIVERABLE_CONTRACT.md`.

## How to extend it

Two extension points, both in the contract.

**A new step type** — `standards/build-orchestration.md` § 4. It is five edits,
not one, and the contract lists them so none is discovered later:

1. The § 4 table and the artefact map under it: type, owning agents, the
   design-only owner, artefacts, the molecular tests the tester runs.
2. `STEP_TYPES` in `scripts/build_plan.py`.
3. The `type` enum in `agents/_shared/schemas/build-plan.schema.json`.
4. The step-type list in `agents/build-planner/AGENT.md` Step 6.
5. The step-type → workbook-section map in `agents/build-doc-keeper/AGENT.md`
   Step 4. That map carries a default section, **Other configuration**, so a
   type missed here degrades to a flagged row rather than a failed run.

Plus: an owning agent in the roster with `class: runtime`, a non-deprecated
`status` from the frontmatter-schema enum, and `requires_org: false` if it is to
own steps in a design-only build (`agents/_shared/SKILL_MAP.md`). A checker the
tester can call — a stdlib-only skill-local
`skills/<domain>/<slug>/scripts/check_*.py` — is optional.

`build_plan.py validate` rejects a plan whose `agent` is not eligible or whose
`type` is not a row in the table.

**New behaviour in the loop** — § 8, the determinism rules that any change must
keep:

- `scripts/build_plan.py` stays the single writer of plan state, derived views
  and gate records: `init`, `validate`, `render`, `ingest-answers`, `next`,
  `set-status`, `check-outputs`, `gate`, `status`, `ensure-gates`,
  `set-clarifications`, `set-plan`, `set-verification`, `set-milestone`. Agents
  call it; they never re-implement it and never hand-edit `plan.json`.
- Every agent invocation is recorded in `plan.json.steps[].runs[]` with its
  envelope path. Re-running a step **appends** a run; history is never
  overwritten. This is what makes the loop resumable.
- The planner may only assign agents that exist and are active, and may only
  cite skills that resolve on disk.
- Skills stay the source of Salesforce truth. A knowledge gap is a `skill-gap`
  block, not an improvisation.
- Secrets never enter the build directory.

Adding a stage to a workflow means editing `.claude/workflows/plan-verify.js` or
`.claude/workflows/build-from-requirements.js`. Keep every `agent()` call
idempotent — the loop is resumable precisely because re-running a step reports
its existing status instead of redoing the work.

## Quality bar

```bash
python3 scripts/validate_repo.py                 # agent shape, citations, doc counts
python3 -m pytest tests/test_build_plan.py       # the plan script
```

Plus: the committed example under `examples/builds/case-onboarding/` validates,
and was produced by running the loop.

## Related

- `standards/build-orchestration.md` — the contract this implements
- `commands/run-build.md` — the per-milestone build command
- `agents/_shared/AGENT_CONTRACT.md`, `agents/_shared/DELIVERABLE_CONTRACT.md`
- `standards/decision-trees/README.md` — what the planner's decisions must cite
- `commands/add-skill.md` — where a `skill-gap` block sends you
