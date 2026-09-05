# /verify-milestone — Cross-step verification + acceptance report for one milestone

Wraps [`agents/milestone-verifier/AGENT.md`](../agents/milestone-verifier/AGENT.md). Resolves every cross-artefact reference in the milestone, checks deploy order, merges the manifest, runs the milestone's acceptance tests, collects the manual checklist, and writes the acceptance report the human reads before approving the gate.

Prints the gate command. Never runs it.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Build directory?
   Example: .sfskills/builds/case-onboarding/

2. Milestone id?
   Example: M2   (every step in it must be `documented`)

3. Approver name (optional)?
   Used only to render the gate command line.
```

If either required input is missing, STOP. If any step in the milestone is not `documented`, STOP and list the steps with their statuses.

---

## Step 2 — Load the agent

Read `agents/milestone-verifier/AGENT.md` in full, plus its Mandatory Reads — `AGENT_RULES.md`, `standards/build-orchestration.md`, `agents/_shared/schemas/build-plan.schema.json`, and its seven skill reads.

---

## Step 3 — Execute the plan

Follow the 10-step plan exactly:

1. Precondition: every step `documented`, predecessor gate approved
2. Build the symbol inventory from this milestone and every earlier one
3. Resolve every reference — validation-rule formulas, assignment-rule criteria, permission-set field grants, Flow field references, entitlement-process milestone names, layout and path fields
4. Check the deployment order: objects → fields → picklists → record types → layouts → permission sets → sharing → automation → routing → SLA
5. Merge the step manifests into one milestone `package.xml`
6. Run the milestone's own acceptance tests
7. Collect every deferred manual test into one human checklist
8. State the optional, human-run validate-only command
9. Write `reports/MILESTONE-<id>-REPORT.md` and print the gate line
10. Score confidence

---

## Step 4 — Deliver the output

Return the Output Contract:

- Summary + verdict (`ready-for-gate` / `ready-with-findings` / `not-ready`) + confidence
- Reference-resolution table, with each unresolved reference and the deploy error it predicts
- Deployment-order verdict
- Merged manifest path, counts, and any conflicts
- Acceptance-test results
- The manual checklist
- The optional validate-only command, marked human-run
- The exact `build_plan.py gate` line, unrun
- Process Observations + Citations

---

## Step 5 — Recommend follow-ups

Suggest (but do not auto-invoke):

- `/score-deployment` when the human has an org to score the merged manifest against
- `/review-release-readiness` when this is the last milestone before a release

---

## What this command does NOT do

- Does not approve the gate — it prints the command for a named human to run.
- Does not deploy or run any `sf` command.
- Does not edit artefacts, test results or documentation, and does not verify more than one milestone per invocation.
