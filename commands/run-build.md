# /run-build — build one milestone of an approved plan

```
/run-build .sfskills/builds/case-onboarding M1
```

Takes a build directory and **one milestone id**. Runs every step in that
milestone — build, test, document — then verifies the milestone as a whole,
writes the acceptance report, and stops for you.

One milestone per invocation. That is not a limitation, it is the gate: G3 is
recorded per milestone, and nothing may start until the milestone before it is
accepted.

## What you need before running it

| | |
|---|---|
| `build_dir` | `.sfskills/builds/<build-id>` — produced by `/clarify-requirements` and `/plan-build` |
| `milestone` | one milestone id from `PLAN.md` |
| G2 approved | the plan-approval gate, recorded in `plan.json.human_gates[]` |
| previous G3 approved | every earlier milestone accepted |
| step gates approved | every step in the milestone with `human_gate: true` has its `step:<id>` gate approved, or it will not be offered |

If you do not know the milestone id or the gate state:

```bash
python3 scripts/build_plan.py status .sfskills/builds/<build-id>/plan.json
```

## The gate rule

**The workflow refuses to start rather than warning you.** Preflight reads
`plan.json` and stops with the specific missing thing if:

- the plan is not `approved` or `building` — approving **G2** is what moves it off `verified` (run `/verify-plan`, then record G2);
- **G2** is absent or not `approved`;
- any earlier milestone's **G3** is absent or not `approved`;
- the milestone has no step left to build.

A step with `human_gate: true` — an access change, a deletion — has a gate of
its own, and it does not stop the milestone: `next` simply does not offer that
step, and says why. Approve it the same way you approve any other gate:

```bash
python3 scripts/build_plan.py gate .sfskills/builds/<build-id>/plan.json \
  step:M1-S03 approve --by "<your name>" --notes "<what you reviewed>"
```

`set-status <step> running` is refused while that gate is pending, so no agent
can claim the step around it.

Agents never approve a gate. `scripts/build_plan.py gate` is the only writer of
a gate record and you are the only decider. If preflight refuses, the answer is
to fix the thing it names — not to re-run with a flag.

## Usage

```
Workflow { scriptPath: ".claude/workflows/build-from-requirements.js",
           args: { build_dir: ".sfskills/builds/case-onboarding",
                   milestone: "M1" } }
```

| arg | required | effect |
|---|---|---|
| `build_dir` | yes | the build directory |
| `milestone` | yes | the one milestone to build |
| `max_rounds` | no | dependency-wave guard, default 20. Raise it only for a milestone with a genuinely deeper dependency chain; it is a runaway backstop, not a coverage cap, and the run reports `stopped_because` when it hits it. |

## What happens

```
Preflight -> gate check; refuses unless the preceding gate is approved
Build     -> rounds of: `next` -> runner -> tester -> doc keeper, per step
Verify    -> cross-step checks, acceptance report, G3 request
```

Each round asks `build_plan.py next` which steps have all their `depends_on`
documented, then pipelines them: `build-step-runner` produces the artefacts,
`step-tester` runs the step's declared acceptance tests plus the always-on XML
and manifest checks, `build-doc-keeper` updates `PLAN.md`, the workbook,
`decisions.md` and `traceability.md`. A step only reaches the tester if it
built, and only reaches the doc keeper if its tests passed.

**Two steps that write the same path never run at the same time.** The `next`
agent reports each step's output paths and the workflow partitions the round
into conflict-free batches before running anything. A step that declares no
outputs runs alone, because nothing can prove it disjoint.

A step only reaches `built` when `build_plan.py check-outputs` confirms every
declared output exists, is non-empty and parses, and only reaches `tested` when
`tests/<step-id>/results.json` says `passed: true`. A run that produced nothing
cannot advance.

A step that fails or blocks is logged with its reason and excluded from later
rounds — the steps depending on it stop too. A round that documents nothing
stops the loop instead of retrying it.

**Resetting a failed step.** Fix whatever the reason named, then put the step
back in the queue:

```bash
python3 scripts/build_plan.py set-status .sfskills/builds/<build-id>/plan.json \
  M1-S03 pending --result "<what was fixed>"
```

`failed → pending` is an allowed transition and is the documented reset: the
step goes back through `next`, so its dependencies and its own gate are
re-checked before it runs again. Re-running `/run-build` on the same milestone
then picks it up. (`failed → running` is also allowed, for an immediate
re-claim; prefer the reset.) Nothing here rewrites history — every run stays in
`steps[].runs[]`.

A `blocked` step whose reason starts `skill-gap:` is the signal to deepen a
skill (`/add-skill`), never to freestyle the missing pattern. The doc keeper
records it in `decisions.md`.

## Afterwards

The workflow returns the report path and the exact G3 command. The milestone
verifier **writes** that report and records its path with `set-milestone`; it
is not rendered from `plan.json`, so it is the one build document that says
what the checks actually found. Read it first — it lists every test result,
every failed or blocked step, the manual checklist for you to tick, and the
deploy order:

```bash
cat .sfskills/builds/<build-id>/reports/MILESTONE-<id>-REPORT.md
```

Then record the gate yourself:

```bash
python3 scripts/build_plan.py gate .sfskills/builds/<build-id>/plan.json \
  milestone:<id> approve \
  --by "<your name>" --notes "<what you checked>"
```

(The returned `gate_command` is the authoritative form — it is read from
`build_plan.py gate --help` at run time.)

That approval is itself checked: it is refused unless the plan gate and the
previous milestone's gate are approved and every step in this milestone is
`documented`, or `blocked` with a recorded reason — which it prints, so
accepting a milestone with a known gap is a decision you see rather than one
you make by accident. `gate milestone:<id> reject` records the opposite: the
milestone goes to `rejected` and the build stays at `building`.

Then `/run-build <build_dir> <next-milestone>`.

`passed: false` means at least one step is not documented or a cross-step check
failed. Fix the named cause and re-run — completed steps are re-reported from
their existing status rather than rebuilt, and workflow resume replays the
agents that already succeeded.

## What it never does

- **Deploy.** Nothing in this layer touches an org. It produces deploy-ready
  metadata, a deploy order and a validate-only command you may run yourself.
- **Approve its own gate.** It reports the command; you run it — including the
  `step:<id>` gate in front of a human-gated step.
- **Hand-edit `plan.json`.** Every state change goes through a `build_plan.py`
  subcommand.
- **Write outside the build directory.** `skills/`, `agents/`, `templates/`,
  `registry/` and `docs/` are read-only to a build.
- **Invent a test.** The tester runs what the plan declares plus the always-on
  XML and manifest checks. A declared checker that does not exist blocks the
  step; it is never quietly skipped.
- **Build more than one milestone.**

## Related

- `commands/build-from-requirements.md` — the whole loop, and where this fits
- `commands/verify-plan.md` — the G2 step that must come first
- `standards/build-orchestration.md` — the contract (§ 3 gates, § 5 tests, § 7 workflows)
- `.claude/workflows/build-from-requirements.js` — the workflow this runs
