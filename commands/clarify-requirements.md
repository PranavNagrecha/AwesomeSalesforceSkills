# /clarify-requirements — Ask every question the skills say must be asked before configuring

Wraps [`agents/requirements-clarifier/AGENT.md`](../agents/requirements-clarifier/AGENT.md). Takes one requirement — a paragraph, a worksheet, a backlog extract — searches local coverage for every capability it implies, harvests every row of every matching skill's `## Questions to Ask Before Configuring` table, dedupes by meaning, proposes a default per question, and writes the set into `plan.json` plus a rendered `CLARIFICATIONS.md` the human answers in place. Stage 1 of the loop in [`standards/build-orchestration.md`](../standards/build-orchestration.md); it stops at gate **G1** and never answers its own questions.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Requirement (required)?
   Either a path to the requirement text (`requirement_path`), or the
   requirement pasted inline (`requirement_text`). One of the two — not both.

2. Build directory (optional)?
   Defaults to .sfskills/builds/<requirement-filename-slug>. The build id is
   the directory name. Supply an existing directory to re-clarify it.

3. Title (optional)?
   The one-line human title `build_plan.py init --title` requires. Defaults to
   the requirement's first heading, or the build id in title case.
```

If neither `requirement_path` nor `requirement_text` is supplied, or the path is unreadable or empty, refuse (`REFUSAL_MISSING_INPUT`) — there is nothing to clarify.

If the requirement text carries credentials, tokens, session ids or customer PII, refuse (`REFUSAL_SECURITY_GUARD`) and ask for a redacted version. Secrets never enter a build directory.

Do **not** accept a cap on the number of questions. `standards/build-orchestration.md` § 3 forbids capping; a cap request is recorded in Process Observations and the full set is asked anyway.

---

## Step 2 — Load the agent

Read `agents/requirements-clarifier/AGENT.md` and every Mandatory Read in its dependency block, including `standards/build-orchestration.md` § 1–3 and `agents/_shared/schemas/build-plan.schema.json`.

---

## Step 3 — Execute the plan

Follow the 6-step plan exactly:
1. Establish the build directory with `build_plan.py init --build-dir … --title … --requirement …` (all three required)
2. Enumerate capability phrases and run `python3 scripts/search_knowledge.py "<phrase>"` — one search per phrase, never one for the whole requirement
3. Keep only skills that carry a `## Questions to Ask Before Configuring` table; record the rest with the phrase that surfaced them
4. Harvest **every row** into a clarification: `kind` blocking or informational, `why`, `answer_shape`, `proposed_default` (from skill guidance or the requirement text only), `owner_role`, `owner_hint` — then add the generic set and dedupe by meaning
5. Group by workbook section, order blocking-first, number `Q1…Qn`, write `plan.json` at `status: clarifying`, then `validate` and `render`
6. Report the counts and stop at G1

---

## Step 4 — Deliver the output

Return the Output Contract:
- Summary + confidence
- Coverage table (phrase → skills returned → which carried a question table → rows harvested)
- The ordered, grouped clarification set, blocking first
- The loop artefacts: `plan.json` at `status: clarifying`, rendered `CLARIFICATIONS.md`
- Process Observations (4 buckets)
- Citations

---

## Step 5 — Hand the loop back to the human

Tell the user, in this order:

1. **Answer in `CLARIFICATIONS.md`** — one `Answer:` line per question. Copy the proposed default onto the line to accept it; write `DEFER: <reason>` to defer a blocking question.
2. **Read the answers back in:**

   ```bash
   python3 scripts/build_plan.py ingest-answers .sfskills/builds/<build-id>/plan.json
   ```

   Add `--allow-deferred` if any blocking question was deferred.
3. **Record G1** (a human action — the agent never runs this):

   ```bash
   python3 scripts/build_plan.py gate .sfskills/builds/<build-id>/plan.json \
     clarifications approve --by "<name>" --notes "<what was decided>"
   ```

4. **Then run [`/plan-build`](./plan-build.md)** on the same build directory.

Where the requirement is really a backlog rather than one requirement, suggest [`/draft-stories`](./draft-stories.md) first — clarification of a portfolio is a per-story operation.

---

## What this command does NOT do

- Does not deploy, probe an org, or touch an org at all.
- Does not approve a gate. `build_plan.py gate` is the only writer of `human_gates[]` and a human is the only decider.
- Does not answer its own questions — it proposes defaults and marks their source.
- Does not cap, trim or drop questions, and does not skip one whose answer seems obvious from the requirement; it proposes that reading as the default instead.
- Does not write scope, fit-gap, decisions, milestones or steps — that is [`/plan-build`](./plan-build.md).
- Does not hand-edit `CLARIFICATIONS.md`, `PLAN.md` or any other rendered view; it writes `plan.json` and calls `build_plan.py render`.
- Does not invent a skill path — every `source_skill` resolves on disk before it is written.
- Does not write outside the build directory and its own report path.
- Does not auto-chain to the planner.

---

## Related

- `commands/plan-build.md` — the next stage, after G1
- `commands/verify-plan.md` — G2
- `commands/run-build.md` — building one milestone, after G2
- `standards/build-orchestration.md` — the contract (§ 1 stage 1, § 2 the build directory, § 3 gates)
