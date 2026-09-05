# /keep-build-docs — Update the build's docs after a tested step

Wraps [`agents/build-doc-keeper/AGENT.md`](../agents/build-doc-keeper/AGENT.md). Re-renders PLAN.md, appends the step's decisions, writes its configuration-workbook rows, updates traceability, and marks the step `documented`.

Idempotent: re-running on the same step replaces that step's rows rather than duplicating them.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Build directory?
   Example: .sfskills/builds/case-onboarding/

2. Step id?
   Example: M1-S04   (its status in plan.json must be `tested`)
```

If either is missing, STOP. If the status is not `tested`, STOP and say which status was found.

---

## Step 2 — Load the agent

Read `agents/build-doc-keeper/AGENT.md` in full, plus its Mandatory Reads — `AGENT_RULES.md`, `standards/build-orchestration.md`, `agents/_shared/schemas/build-plan.schema.json`, and its four skill reads (workbook row format, RTM columns, documentation standards, acceptance evidence).

---

## Step 3 — Execute the plan

Follow the 10-step plan exactly:

1. Precondition + read the envelope and the test results
2. `python3 scripts/build_plan.py render <build_dir>/plan.json` to regenerate PLAN.md
3. Append to `decisions.md` any decision the envelope actually recorded — dated, attributed, cited
4. Write the workbook rows for the step's type into `workbook/`, in the 10-section row format, one row per addressable artefact
5. Give every row its deployment-order position
6. Give every row its verification step
7. Update `traceability.md`: requirement / clarification id → step → artefact paths → test result
8. Apply the replace-by-key rule so a re-run cannot duplicate rows
9. `set-status … documented`
10. Score confidence

---

## Step 4 — Deliver the output

Return the Output Contract:

- Summary + confidence
- The workbook rows written, in the canonical row format
- The traceability rows written
- Decisions appended (or an explicit "none")
- Which rows were replaced versus newly written
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

Suggest (but do not auto-invoke):

- `/verify-milestone` once every step in the milestone is `documented`
- `/author-config-workbook` when the build's workbook is compiled into a release-level document

---

## What this command does NOT do

- Does not deploy.
- Does not build, edit or delete artefacts, and does not re-run tests.
- Does not hand-edit a rendered view, approve a gate, or document more than one step per invocation.
