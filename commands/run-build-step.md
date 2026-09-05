# /run-build-step — Execute one step of a build plan

Wraps [`agents/build-step-runner/AGENT.md`](../agents/build-step-runner/AGENT.md). Invokes the step's owning run-time agent with the plan's inputs, stores the artefacts and the envelope, and records the run on the step.

One step per invocation. Nothing here deploys.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Build directory?
   Example: .sfskills/builds/case-onboarding/   (must contain plan.json)

2. Step id?
   Example: M1-S04

3. Reason (optional)?
   Only when re-running a step after a `blocked` or `failed` exit.
```

If either required input is missing, STOP.

---

## Step 2 — Load the agent

Read `agents/build-step-runner/AGENT.md` in full, plus everything in its Mandatory Reads — `AGENT_RULES.md`, `standards/build-orchestration.md`, `agents/_shared/schemas/build-plan.schema.json`, and its five skill reads.

---

## Step 3 — Execute the plan

Follow the 9-step plan exactly:

1. Load `plan.json` and locate the step
2. Confirm the step appears in `python3 scripts/build_plan.py next <build_dir>/plan.json` — refuse if not, except for a `failed` or `blocked` step being re-run with a `reason` (those are never in `next`, which lists `pending` steps only)
3. `set-status … running`
4. Read the owning agent's `## Inputs` section
5. Map plan `inputs{}` + clarification answers + upstream step outputs onto it
6. Invoke the owning agent — Agent tool with `subagent_type` = the agent id in Claude Code; read its AGENT.md and execute its Plan inline in any other host — under the artefacts-only-under-`artefacts/<step-id>/` constraint
7. Store the returned envelope under `envelopes/<step-id>/` and reconcile the artefacts against the step's declared outputs
8. `set-status … built` with the run fields, or `blocked` when the owning agent reports a skill gap or an ambiguity
9. Score confidence

---

## Step 4 — Deliver the output

Return the Output Contract:

- Summary + confidence
- The owning agent's envelope, verbatim, and where it was stored
- Artefact paths produced, each marked declared or undeclared
- The exact `set-status` command line that was run
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

Suggest (but do not auto-invoke):

- `/test-build-step` on the step just built
- `/keep-build-docs` once that step is `tested`

---

## What this command does NOT do

- Does not deploy, and never runs `sf project deploy start`.
- Does not run the step's tests or write any build documentation.
- Does not approve a gate or process more than one step.
