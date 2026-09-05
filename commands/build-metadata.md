# /build-metadata — Build one declarative step of a build plan into deploy-ready metadata

Wraps [`agents/metadata-builder/AGENT.md`](../agents/metadata-builder/AGENT.md). Reads the step's cited skills, writes source-format `-meta.xml` under `artefacts/<step-id>/` plus a `package.xml` fragment and a deploy-order note, then runs the cited skills' own checkers until they exit 0.

One step per invocation. Nothing here deploys, and nothing here writes Apex.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Build directory?
   Example: .sfskills/builds/case-onboarding/   (must contain plan.json)

2. Step id?
   Example: M1-S03   (its `agent` in plan.json must be metadata-builder)

3. API version (optional)?
   Defaults to the plan's api_version, then 62.0.
```

If either required input is missing, STOP. If the step's `agent` is some other agent, STOP and name it — run that agent instead.

---

## Step 2 — Load the agent

Read `agents/metadata-builder/AGENT.md` in full, plus everything in its Mandatory Reads — `AGENT_RULES.md`, `standards/build-orchestration.md`, `agents/_shared/schemas/build-plan.schema.json`, and the eight admin skills whose element sets the agent is trusted to write from. Then read the skills the *step* cites, which are authoritative for the step.

---

## Step 3 — Execute the plan

Follow the 10-step plan exactly:

1. Load the step; confirm `agent` is `metadata-builder` and `type` is a § 4 row
2. Confirm the type is one this agent owns in design-only mode
3. Read each cited skill's `SKILL.md`, its deployable-XML reference, its `templates/`, and its gotchas — building the element inventory; a skill with no such reference blocks the step with `skill-gap`
4. Answer each cited skill's Questions-to-Ask rows from step inputs → clarification answers → upstream artefacts → the requirement
5. Write the metadata under `artefacts/<step-id>/`, every element name taken from the inventory
6. Write the `package.xml` fragment
7. Write `deploy-order.md`, ending with the validate-only command for the human
8. Run every cited skill's `check_*.py --manifest-dir artefacts/<step-id>` and repair the XML until each exits 0 (three passes maximum), then parse every emitted file
9. `python3 scripts/build_plan.py check-outputs <plan> <step-id>` — the last self-check before returning; set the terminal status only when running standalone rather than under `/run-build-step`
10. Score confidence

---

## Step 4 — Deliver the output

Return the Output Contract:

- Summary + confidence
- Artefact inventory — path, metadata type, the skill reference each element set came from, declared or not
- Decision record — question, answer, which source supplied it, which element it determined
- Checker results — command line, exit code, repair passes
- The `check-outputs` JSON, verbatim
- The deploy-order note
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

Suggest (but do not auto-invoke):

- `/test-build-step` on the step just built
- `/keep-build-docs` once that step is `tested`
- `/build-apex` when an `automation` step turned out to need Apex

---

## What this command does NOT do

- Does not deploy or validate against an org; the validate-only command is text for a human to run.
- Does not write Apex — use `/build-apex`.
- Does not run the step's acceptance tests, approve a gate, or process more than one step.
- Does not invent a metadata element name — an element no cited skill documents blocks the step with `skill-gap`.
