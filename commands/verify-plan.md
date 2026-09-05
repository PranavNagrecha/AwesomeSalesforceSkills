# /verify-plan — Try to refute the plan before a human approves it

Wraps [`agents/plan-verifier/AGENT.md`](../agents/plan-verifier/AGENT.md). For every step in `plan.json` it runs three independent adversarial lenses — **executability** (can the named agent actually produce these outputs from these inputs, and is it eligible to own the step in this `build_mode`?), **grounding** (do the cited skills, templates and decision-tree branches contain what the step claims?), and **testability** (is every acceptance test runnable, and would it fail on a bad build?) — records a verdict per (step, lens), writes `plan.json.verification`, sets the plan to `verified` or `plan-rejected`, and stops at gate **G2** with the exact approval command for a human to run. Stage 3 of the loop in [`standards/build-orchestration.md`](../standards/build-orchestration.md).

A lens that cannot be shown to hold is `refuted`, not passed. The default is disbelief: the cost of an unverified step is discovered three stages later, inside an artefact somebody is about to deploy.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Build directory (required)?
   .sfskills/builds/<build-id> — must contain a plan.json at status
   'planned' (or 'verified', when re-checking after an edit).

2. Step id (optional)?
   e.g. M1-S02. Verify one step instead of the whole plan.

3. Lens (optional)?
   executability | grounding | testability. Verify one lens instead of all
   three.
```

`step_id` and `lens` narrow a single fanned-out worker to one (step, lens) pair. Supplied together or alone, the run is read-only: it emits verdict objects and never touches `plan.json`.

If `build_dir` is missing or holds no `plan.json`, refuse (`REFUSAL_MISSING_INPUT`). If `plan.status` is neither `planned` nor `verified`, refuse (`REFUSAL_INPUT_AMBIGUOUS`) — a `clarifying` plan has nothing to verify, an `approved` or `building` plan is past this gate, and a `plan-rejected` plan needs a new version from [`/plan-build`](./plan-build.md) first.

---

## Step 2 — Choose the path

Two ways to run this, and they produce the same verdict objects.

**Workflow (default for a plan of more than a couple of steps)** — three lenses per step in parallel, no barrier until the synthesis:

```
Workflow { scriptPath: ".claude/workflows/plan-verify.js",
           args: { build_dir: ".sfskills/builds/case-onboarding" } }
```

| arg | required | effect |
|---|---|---|
| `build_dir` | yes | the build directory |

The workflow loads and validates the plan, fans out one `plan-verifier` agent per (step, lens) pair, then runs a single synthesis agent that records the verdicts with `build_plan.py set-verification --file`, renders the views and returns the blocker list plus the G2 command. A lens agent that dies returns `refuted` by default — an unverified lens is never a silent pass. It is re-runnable: the synthesis replaces this plan version's `verification` block rather than appending to it.

One difference worth knowing: the workflow has no separate cross-step phase. `build_plan.py validate` at load covers the DAG, the milestone membership and the per-step and per-milestone test minimums, and each executability lens gets the whole plan's step skeleton so it can see output collisions and ordering from its own step's side. The traceability sweep in the agent's Step 5 — every requirement reaching a step and a test — is the one check no fanned-out worker performs, so run the inline path when that is what you need to confirm.

**Inline (a small plan, or one step you want to re-check by hand)** — read `agents/plan-verifier/AGENT.md` and run its 6-step plan in one session: all three lenses for every step in sequence, then the same synthesis.

---

## Step 3 — Execute the plan

Follow the 6-step plan exactly:
1. Load the plan and reject on mechanics first — `python3 scripts/build_plan.py validate .sfskills/builds/<build-id>/plan.json`. A plan that does not validate cannot be verified
2. Executability lens, per step
3. Grounding lens, per step
4. Testability lens, per step
5. Cross-step checks — every requirement reaches a step and a test; no two steps write the same output path; the dependency graph is acyclic; every milestone has an acceptance test and at least one step
6. Synthesise, then write the block through `python3 scripts/build_plan.py set-verification <plan> --file <verification>.json --outcome verified|plan-rejected` — which writes `verification` and sets the build status and touches nothing else — then `validate`, `render`, and stop at G2. Nobody hand-edits `plan.json`

Every verdict is one object of exactly this shape — the same shape the workflow requires from each fanned-out worker:

```json
{"step_id": "M1-S02", "lens": "grounding", "verdict": "pass" | "refuted",
 "blockers": [{"problem": "…", "evidence": "…", "fix": "…"}],
 "warnings": [{"problem": "…", "fix": "…"}],
 "evidence": ["paths listed or read, commands run and what they printed"]}
```

`pass` is earned only when every check in that lens was confirmed by something the agent read or ran. "Probably fine", "presumably exists" and "the agent will figure it out" are all `refuted`. A verdict with no evidence is not a verdict.

---

## Step 4 — Deliver the output

Return the Output Contract:
- Summary + confidence (build id, plan version, steps verified, lenses run, blocker and warning counts, resulting status)
- Verdict matrix — steps down, three lenses across
- Blockers, each with step, lens, evidence and remedy, ordered by milestone
- Warnings, same shape, non-blocking
- Cross-step results
- The gate line — the exact `build_plan.py gate` command, or the rejection and what to fix
- Process Observations (4 buckets)
- Citations

---

## Step 5 — Hand the loop back

**If the plan was rejected**, name the blockers and send the user back to [`/plan-build`](./plan-build.md). G2 stays unapproved and [`/run-build`](./run-build.md) will refuse to start.

**If the plan was verified**, print the G2 command for the human to run — the agent never runs it:

```bash
python3 scripts/build_plan.py gate .sfskills/builds/<build-id>/plan.json \
  plan approve --by "<name>" --notes "<what was checked>"
```

`gate plan approve` is refused unless the status is exactly `verified` — so it is an approval of a verified plan or of nothing. Approving it sets the build status to `approved`, which is what `build_plan.py next` and `/run-build` require before a milestone may start. Then:

```
/run-build .sfskills/builds/<build-id> M1
```

Suggest, but never auto-invoke: [`/assess-waf`](./assess-waf.md) when blockers cluster around one architectural decision rather than around individual steps.

---

## What this command does NOT do

- Does not deploy, probe an org, or touch an org at all.
- Does not approve a gate, and does not write a gate record. It prints the G2 command; a human runs it.
- Does not fix the plan. It refutes; [`/plan-build`](./plan-build.md) repairs. Editing a step here would mean the same agent wrote and blessed it.
- Does not mark a lens `pass` because it looks plausible. Unshown is refuted, and a lens that did not run is refuted with the reason.
- Does not invent a skill path, a template path, an agent id or a decision-tree branch — a branch it cannot find in the cited tree is a refutation, not a near-miss.
- Does not execute a step's acceptance tests against artefacts; it verifies that they could run, which is a different job from running them.
- Does not write under `artefacts/` or `tests/`, and does not hand-edit `plan.json`, `PLAN.md` or any other rendered view — `set-verification --file` is the one write it makes.
- Does not verify more than one plan version per invocation, and does not auto-chain to the planner or to the build workflow.

---

## Related

- `commands/plan-build.md` — the stage before, and where a rejected plan goes back to
- `commands/run-build.md` — building one milestone, after G2
- `standards/build-orchestration.md` — the contract (§ 3 gates, § 5 tests, § 7 workflows)
- `.claude/workflows/plan-verify.js` — the workflow this runs
