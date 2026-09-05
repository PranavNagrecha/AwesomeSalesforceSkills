# /plan-build — Turn an answered requirement into an executable build plan

Wraps [`agents/build-planner/AGENT.md`](../agents/build-planner/AGENT.md). Takes a build directory whose `plan.json` is past gate **G1** and writes the plan the rest of the loop executes: scope in and out, a fit-gap entry per capability, a decision per technology choice with the decision-tree branch that produced it, two to six milestones, and the ordered steps — each naming exactly one owning run-time agent, the skills it must read, what it produces under `artefacts/<step-id>/`, what it depends on, and at least one runnable acceptance test. Stage 2 of the loop in [`standards/build-orchestration.md`](../standards/build-orchestration.md).

The plan is a proposal, not an approval. It ends at `status: planned` and hands off to [`/verify-plan`](./verify-plan.md).

---

## Step 1 — Collect inputs

Ask the user:

```
1. Build directory (required)?
   .sfskills/builds/<build-id> — produced by /clarify-requirements. Must
   contain requirement.md and a plan.json whose 'clarifications' gate is
   approved.
```

That is the whole input list, by design. Everything a plan needs — the requirement, the questions, the answers, the G1 record — is already in the build directory. A milestone preference, a re-plan reason or a "no Apex on this project" constraint is an answer to a clarification and belongs in `CLARIFICATIONS.md`, where G1 records it.

If `build_dir` is missing or holds no `plan.json` / `requirement.md`, refuse (`REFUSAL_MISSING_INPUT`) and send the user to [`/clarify-requirements`](./clarify-requirements.md).

Check the gate before planning:

```bash
python3 scripts/build_plan.py status .sfskills/builds/<build-id>/plan.json
```

Refuse (`REFUSAL_NEEDS_HUMAN_REVIEW`) unless G1 is `approved` and every `blocking` clarification is answered or explicitly deferred. An unanswered blocking question is precisely the decision the skill said would change the design.

Re-planning is allowed from exactly one status: `plan-rejected`, where the rejected gate has already bumped `plan.version` and archived the old plan into `history[]`. Refuse (`REFUSAL_COMPETING_ARTIFACT`) at `verified`, `approved`, `building` or `done` — re-planning in place would discard a recorded gate — and tell the user that `build_plan.py gate <plan> plan reject` is what creates the next version.

---

## Step 2 — Load the agent

Read `agents/build-planner/AGENT.md` and every Mandatory Read in its dependency block — including `standards/build-orchestration.md` § 3–5 and § 8, `agents/_shared/RUNTIME_VS_BUILD.md`, `agents/_shared/SKILL_MAP.md`, `agents/_shared/AGENT_DISAMBIGUATION.md`, and `agents/_shared/schemas/build-plan.schema.json`.

---

## Step 3 — Execute the plan

Follow the 7-step plan exactly:
1. Load state and check the gate
2. Write scope in and out, each item citing the answer that put it there
3. Fit-gap every in-scope capability (`requirement`, `verdict`, `steps[]`, tier, note)
4. Decide, citing a decision-tree branch for every technology choice — no branch, no decision
5. Cut two to six milestones in workbook deployment order, each with a Given/When/Then goal and its own acceptance test
6. Write the steps: one owning agent each — `class: runtime`, a `status` that is a valid non-deprecated value of the agent-frontmatter enum (`stable` or `beta`), and `requires_org: false` unless the plan's `build_mode` is `org-connected` — a `type` from the § 4 table (`object-model`, `access`, `validation`, `automation`, `routing`, `sla`, `ui`, `data`, `integration`, `docs`, `custom`), skills that resolve on disk, concrete outputs under `artefacts/<step-id>/`, `depends_on`, `human_gate`, and at least one acceptance test whose runner exists
7. `set-plan --file`, then `ensure-gates`, then `validate`, then `render` — fix every ERROR and re-run until `validate` exits 0. The plan body is written through the CLI, never by hand-editing `plan.json`

Three rules govern step 6: **agents only from the active roster and only when eligible for this `build_mode`; skills only when they resolve on disk; no freestyle Salesforce claims.** A step whose knowledge no skill covers is written with `status: "blocked"` and `blocked_reason: "skill-gap"`, naming what was searched. That is the signal to deepen a skill, never a licence to write the claim from memory.

**Who owns a step depends on `build_mode`.** Most designer agents in the § 4 table declare `requires_org: true`, so in a `design-only` build — the default — they are ineligible and the owner is the table's **design-only owner** column: `metadata-builder` for every metadata step type, `apex-builder` for Apex automation, `story-drafter` for workbook and story docs, `bulk-migration-planner` for data and integration. `metadata-builder` builds from the step's cited skills' `references/metadata-examples.md` and `templates/`, so give it the reading list the designer agent would have had. In an `org-connected` build (`init --org-alias`) the designer agents own their rows again.

Validation rules are the `validation` type; escalation rules are `sla`; list views, reports and email templates are `ui`; Email-to-Case and Web-to-Case are `routing`; `package.xml` and the deploy-order note are `docs`.

---

## Step 4 — Deliver the output

Return the Output Contract:
- Summary + confidence (build id, plan version, milestone count, step count by type, blocked steps, `validate` exit status)
- Scope table, in and out
- Fit-gap table
- Decisions, each with its tree and quoted branch
- Milestones and steps in dependency order, with acceptance tests and the `human_gate` flag visible
- Blocked steps with the search phrases that found nothing — the depth-wave worklist
- Process Observations (4 buckets)
- Citations

---

## Step 5 — Hand the loop back

Report `validate`'s exit status, then tell the user to run **[`/verify-plan`](./verify-plan.md)** on the same build directory. Verification is not optional: G2 is what `/run-build` refuses to start without, and the verifier is adversarial by design — the planner does not get to bless its own plan.

Suggest, but never auto-invoke: [`/assess-waf`](./assess-waf.md) when a decision was recorded with `adr_required: true`; [`/run-fit-gap`](./run-fit-gap.md) when the requirement is really a backlog and needs org-grounded tiers.

---

## What this command does NOT do

- Does not deploy, probe an org, or touch an org at all.
- Does not approve a gate. `ensure-gates` adds missing gate records as `pending`, which the schema requires; `build_plan.py gate` is the only writer of a gate decision and a human the only decider.
- Does not invent a skill path, a template path, a decision-tree branch or an agent id — every one is checked on disk before it is written into a step.
- Does not assign a build-time agent, a deprecated agent, an agent whose `status` is off the frontmatter-schema enum, or an org-requiring agent in a `design-only` build.
- Does not hand-edit `plan.json` — `set-plan --file` writes the plan body and `ensure-gates` writes the pending gate records (one per milestone, plus a `step:<id>` gate per human-gated step).
- Does not write a Salesforce claim no skill supports — the step is `blocked` with `blocked_reason: skill-gap` instead.
- Does not execute a step, run a checker against artefacts, or write anything under `artefacts/`.
- Does not answer an unanswered clarification itself.
- Does not bump `plan.version` or write `history[]` — a rejected plan gate is what creates the next version, and `plan-rejected` is the one status this command re-plans from.
- Does not hand-edit `PLAN.md` or any other rendered view.
- Does not auto-chain to the verifier or to any step's owning agent.

---

## Related

- `commands/clarify-requirements.md` — G1, which must come first
- `commands/verify-plan.md` — G2, which comes next
- `commands/run-build.md` — building one milestone, after G2
- `standards/build-orchestration.md` — the contract (§ 4 step types, § 5 acceptance tests, § 8 determinism rules)
