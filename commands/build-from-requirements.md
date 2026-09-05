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
                                      ........................ GATE G1 (answers)
2  Plan      /plan-build            -> scope, fit-gap, decisions (each citing a
                                      decision-tree branch), milestones, steps
3  Verify    /verify-plan           -> three adversarial lenses per step:
                                      executability, grounding, testability
                                      ........................ GATE G2 (plan)
4  Build     /run-build <milestone> -> per step: runner -> tester -> doc keeper;
                                      then the milestone acceptance report
                                      ........................ GATE G3 (per milestone)
5  Repeat    stage 4 per milestone until the last one is accepted
```

A gate is a human. Agents never approve one — `scripts/build_plan.py gate` is
the only writer of a gate record, and the workflows return the command for you
to run rather than running it.

## The exact sequence

```bash
# 1. Clarify — writes plan.json (status "clarifying") and CLARIFICATIONS.md
/clarify-requirements "<the requirement, or a path to a worksheet/backlog>"

# 2. Answer — in CLARIFICATIONS.md, or accept every proposed default in one action.
#    Questions are never capped. Then record G1:
python3 scripts/build_plan.py gate .sfskills/builds/<build-id>/plan.json clarifications approve \
  --by "<you>" --notes "answers complete"

# 3. Plan — scope, decisions, milestones, steps; status -> "planned"
/plan-build .sfskills/builds/<build-id>

# 4. Verify the plan — adversarial; status -> "verified" or "plan-rejected"
/verify-plan .sfskills/builds/<build-id>

# 5. Read the blockers. If rejected: fix, re-plan (a new plan version), re-verify.
#    If verified, record G2 — this is the plan approval:
python3 scripts/build_plan.py gate .sfskills/builds/<build-id>/plan.json plan approve \
  --by "<you>" --notes "plan approved"

# 6. Build the first milestone
/run-build .sfskills/builds/<build-id> M1

# 7. Read the acceptance report, tick the manual checklist, record G3
cat .sfskills/builds/<build-id>/reports/MILESTONE-M1-REPORT.md
python3 scripts/build_plan.py gate .sfskills/builds/<build-id>/plan.json milestone:M1 approve \
  --by "<you>" --notes "<what you checked>"

# 8. Next milestone. Repeat 6-7 until the last one is accepted.
/run-build .sfskills/builds/<build-id> M2
```

Each workflow returns the exact `gate_command` for its stage, read from
`build_plan.py gate --help` at run time — use that form if it differs from the
shape sketched above.

## Where the files live

`plan.json` is the only shared state. Every agent in the loop reads it before
acting and updates only the fields it owns. `PLAN.md`, `CLARIFICATIONS.md` and
the milestone reports are **rendered** from it by `scripts/build_plan.py` —
never hand-edit a rendered view; edit the plan and re-render.

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
└── reports/                  milestone acceptance reports
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
- **No secrets in the build directory.** Envelopes redact per
  `agents/_shared/DELIVERABLE_CONTRACT.md`.

## How to extend it

Two extension points, both in the contract.

**A new step type** — `standards/build-orchestration.md` § 4:

1. Add one row to the § 4 table: type, owning agents, artefacts, the molecular
   tests the tester runs.
2. Make sure the owning agent exists in the roster with `class: runtime` and a
   status that is not `deprecated` (`agents/_shared/SKILL_MAP.md`).
3. Optionally add a checker the tester can call, as a skill-local
   `skills/<domain>/<slug>/scripts/check_*.py` (stdlib-only).

Nothing else changes. The planner reads that table and the roster to assign
agents, and `build_plan.py validate` rejects a plan whose `agent` is not an
active roster id or whose `type` is not a row in the table.

**New behaviour in the loop** — § 8, the determinism rules that any change must
keep:

- `scripts/build_plan.py` stays the single writer of derived views and gate
  records (`init`, `validate`, `render`, `next`, `set-status`, `gate`,
  `status`). Agents call it; they never re-implement it.
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
