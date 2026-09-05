# /test-build-step — Run the molecular tests for one built step

Wraps [`agents/step-tester/AGENT.md`](../agents/step-tester/AGENT.md). Runs the always-on structural checks plus every acceptance test the plan declared for the step, writes `tests/<step-id>/results.json`, and moves the step to `tested` or `failed`.

The step must already be `built`. Artefacts are read-only to this command.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Build directory?
   Example: .sfskills/builds/case-onboarding/

2. Step id?
   Example: M1-S04   (its status in plan.json must be `built`)
```

If either is missing, STOP. If the status is anything but `built`, STOP and say which status was found.

---

## Step 2 — Load the agent

Read `agents/step-tester/AGENT.md` in full, plus its Mandatory Reads — `AGENT_RULES.md`, `standards/build-orchestration.md` § 5 in particular, `agents/_shared/schemas/build-plan.schema.json`, and its five skill reads.

---

## Step 3 — Execute the plan

Follow the 7-step plan exactly:

1. Check the precondition (status `built`)
2. Always-on `xml` — parse every `*.xml` / `*-meta.xml` under the step's artefacts
3. Always-on `manifest` — two-way consistency between `package.xml` and the files on disk. On a metadata step type (`object-model`, `access`, `validation`, `automation`, `routing`, `sla`, `ui`) with no `package.xml` in its own or its dependencies' artefacts, this **fails**; it does not skip
4. Each declared acceptance test by type: `checker` (run the path with `--manifest-dir`; it passes on exit 0 **and** `build_plan.py check-outputs` being ok; a checker that does not exist blocks the step), `command` (starts with `python3 `, stdlib-only, never a deploy and never anything on the § 5 deny-list), `manual` (collected for the milestone gate)
5. Write `tests/<step-id>/results.json` and `summary.md` — `passed: true` in that file is what `set-status … tested` requires, so write it truthfully and let the transition fail rather than adjusting it
6. `set-status … tested` on pass, `failed` with the failing test names in `--result`, or `blocked --blocked-reason "missing-checker"` for a checker the plan named but that does not exist
7. Score confidence

---

## Step 4 — Deliver the output

Return the Output Contract:

- Summary + confidence
- Results table (test, type, runner, exit code, verdict)
- Failure detail with the command lines and exit codes
- The manual checklist deferred to the milestone gate
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

Suggest (but do not auto-invoke):

- `/keep-build-docs` once the step is `tested`
- `/run-build-step` to re-run the step after a `failed` exit is addressed

---

## What this command does NOT do

- Does not deploy, and never runs `sf project deploy start` or `sf project deploy validate`.
- Does not edit the artefacts under test.
- Does not invent a test, tick a manual test, or approve a gate.
- Does not run anything matching the deploy deny-list in `standards/build-orchestration.md` § 5 — `sf … deploy`, `sfdx`, `force:source:deploy`, `curl`, `wget`, a pipe into a shell, `bash -c`, `python3 -c`, `rm -rf`, `git push` — it records the test refused-not-run instead.
- Does not hand-edit `plan.json`.
