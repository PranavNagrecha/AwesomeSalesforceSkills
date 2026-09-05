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

4. Reproducible timestamp (optional)?
   `init --now <ISO-8601>` fixes the plan's `created` field, the only
   non-deterministic thing `init` writes and something `PLAN.md` renders. Ask
   for it when the build is a fixture, a regression case, or a re-run that
   will be diffed against an earlier one; otherwise let it default to UTC now.
```

Do **not** ask for an org. `init --org-alias` is what makes a build `org-connected`, and this stage never reads an org — a design-only build is the correct default here, and it is what decides which agents may later own a step.

If neither `requirement_path` nor `requirement_text` is supplied, or the path is unreadable or empty, refuse (`REFUSAL_MISSING_INPUT`) — there is nothing to clarify.

If the requirement text carries credentials, tokens, session ids or customer PII, refuse (`REFUSAL_SECURITY_GUARD`) and ask for a redacted version. Secrets never enter a build directory.

Do **not** accept a cap on the number of questions. `standards/build-orchestration.md` § 3 forbids capping; a cap request is recorded in Process Observations and the full set is asked anyway.

---

## Step 2 — Load the agent

Read `agents/requirements-clarifier/AGENT.md` and every Mandatory Read in its dependency block, including `standards/build-orchestration.md` § 1–3 and `agents/_shared/schemas/build-plan.schema.json`.

---

## Step 3 — Execute the plan

Follow the 7-step plan exactly:
1. Establish the build directory with `build_plan.py init --build-dir … --title … --requirement …` (all three required), plus `--now <ISO>` when the run must be reproducible. Note what `init` puts in `requirement.summary`: the first non-heading line of the requirement, truncated at 400 characters. That is a placeholder, and step 5 is the only chance to replace it
2. Enumerate capability phrases and run `python3 scripts/search_knowledge.py "<phrase>"` — one search per phrase, never one for the whole requirement. If every phrase comes back empty, settle "no index" versus "no coverage" with one control search on a term the library certainly covers (`search_knowledge.py "permission set"`), **not** with `bootstrap.py --verify-only`, which also prints `BOOTSTRAP FAILED` when the installed slash-command count merely differs from `commands/`
3. Keep only skills that carry a `## Questions to Ask Before Configuring` table; record the rest with the phrase that surfaced them
4. Harvest **every row** into a clarification: `kind` blocking or informational, `why`, `answer_shape`, `proposed_default` (from skill guidance or the requirement text only), `owner_role`, `owner_hint` — then add the generic set and dedupe by meaning. `owner_hint` obeys the `standards/build-orchestration.md` § 4 eligibility rule in full, `build_mode` included: in a design-only build the org-requiring designers are ineligible and a metadata question's hint is `metadata-builder`
5. Group with the § 4 **step-type** vocabulary (`object-model`, `access`, `automation`, `validation`, `routing`, `sla`, `ui`, `data`, `integration`, `docs`, `custom`) plus `testing-and-environments` — not workbook section names — order blocking-first, number `Q1…Qn`, then write the set through `set-clarifications`, followed by `validate` and `render`. The agent never hand-edits `plan.json`:

   ```bash
   mkdir -p .sfskills/builds/<build-id>/inputs/clarifications
   # write the ordered array to inputs/clarifications/clarifications.json, then:

   python3 scripts/build_plan.py set-clarifications .sfskills/builds/<build-id>/plan.json \
     --file .sfskills/builds/<build-id>/inputs/clarifications/clarifications.json \
     --summary "<one-paragraph restatement of the requirement>"
   ```

   `--summary` is the only writer of `requirement.summary` anywhere in the loop, so a placeholder left here is a placeholder `PLAN.md` prints for the rest of the build. The `--file` body is an **input**, not an envelope: it belongs under `inputs/<stage-or-step>/` and never under `envelopes/`, which holds run envelopes only. `set-clarifications` prints one summary line — `clarifications written: <n> question(s), <b> blocking; status -> clarifying; requirement.summary updated` — and `<b>` is the number of questions the human must answer or defer before G1 opens; quote that line rather than recounting
6. Report the counts and hand the loop back at G1 — the answering instructions in Step 5 below
7. Self-validate the run envelope with `python3 scripts/validate_envelope.py .sfskills/builds/<build-id>/envelopes/clarifications/<run_id>.json`; it must print `OK`, and nothing is returned until it does. Agent-specific payload (`clarifications[]`, `capability_coverage[]`, …) goes under the envelope's `extensions` object, never as top-level keys — the envelope schema is `additionalProperties: false` and rejects an unknown top-level name outright

---

## Step 4 — Deliver the output

Return the Output Contract:
- Summary + confidence
- Coverage table (phrase → skills returned → which carried a question table → rows harvested)
- The ordered, grouped clarification set, blocking first
- What `CLARIFICATIONS.md` shows the human per question — **Question**, **Why it matters**, **Who can answer** (`owner_role`), **Answer shape**, **From skill**, **Proposed default** — and what it does not: `owner_hint`, `default_source` and `also_asked_by[]` live only in `plan.json` and the envelope, so repeat anything the human needs from them here
- The loop artefacts: `plan.json` at `status: clarifying`, rendered `CLARIFICATIONS.md`
- Process Observations (4 buckets)
- Citations

---

## Step 5 — Hand the loop back to the human

Tell the user, in this order:

1. **Answer in `CLARIFICATIONS.md`.** The file is grouped, not flat: two top-level sections, `## Blocking` then `## Informational`, each holding `### <group>` headings in the order the agent wrote them (a question with no group lands last under `Other`), and each question under its group as a `#### Q<n> — status: open` heading. The human answers under those `#### Qn` headings — one `Answer:` line per question, in place. Copy the proposed default onto the line to accept it; write `DEFER: <reason>` to defer a blocking question. An answer may run to several lines: everything after `Answer:` up to the next heading (`#### Q<n>`, `### <group>`, `## Informational`) or a `---` rule belongs to it.
2. **Read the answers back in:**

   ```bash
   python3 scripts/build_plan.py ingest-answers .sfskills/builds/<build-id>/plan.json
   ```

   Add `--allow-deferred` if any blocking question was deferred. Blanking an answer a blocking question already carries is an ERROR — an answer is withdrawn by deferring it, not by deleting it.
3. **Record G1** (a human action — the agent never runs this). It is refused while any `blocking` question is still `open`, so `ingest-answers` comes first:

   ```bash
   python3 scripts/build_plan.py gate .sfskills/builds/<build-id>/plan.json \
     clarifications approve --by "<name>" --notes "<what was decided>"
   ```

4. **Then run [`/plan-build`](./plan-build.md)** on the same build directory.

Where the requirement is really a backlog rather than one requirement, suggest [`/draft-stories`](./draft-stories.md) first — clarification of a portfolio is a per-story operation.

---

## Step 6 — Exporting the build as a committed example (optional, later)

`.sfskills/` is gitignored, so nothing under a build directory is committable where it sits. When a finished build is worth keeping as a worked example, `export` is the only way out — mention it when the user asks how to share or keep the build, not before:

```bash
python3 scripts/build_plan.py export .sfskills/builds/<build-id>/plan.json \
  examples/builds/<build-id>
```

It runs `validate` first and refuses to export a plan carrying any ERROR, copies the whole directory across — `plan.json`, the rendered views, `requirement.md`, `decisions.md`, `traceability.md`, and the `artefacts/`, `tests/`, `envelopes/`, `reports/` and `workbook/` trees — and prints the file count. An existing destination is refused unless `--force`, which replaces it outright rather than merging, so files a rebuilt plan no longer produces do not survive. Exporting a build still at `status: clarifying` is legal and exports exactly that: the question set and the human's answers, with no plan behind them.

---

## What this command does NOT do

- Does not deploy, probe an org, or touch an org at all.
- Does not approve a gate. `build_plan.py gate` is the only writer of `human_gates[]` and a human is the only decider.
- Does not answer its own questions — it proposes defaults and marks their source.
- Does not cap, trim or drop questions, and does not skip one whose answer seems obvious from the requirement; it proposes that reading as the default instead.
- Does not write scope, fit-gap, decisions, milestones or steps — that is [`/plan-build`](./plan-build.md).
- Does not hand-edit `plan.json`; `set-clarifications --file` is the writer of `clarifications[]`.
- Does not put a `--file` input under `envelopes/` — that tree holds run envelopes only, and `inputs/<stage-or-step>/` holds CLI inputs.
- Does not return an envelope that has not passed `scripts/validate_envelope.py`, and does not hang agent-specific keys off the envelope's top level instead of `extensions`.
- Does not hand-edit `CLARIFICATIONS.md`, `PLAN.md` or any other rendered view; it writes through the CLI and calls `build_plan.py render`.
- Does not invent a skill path — every `source_skill` resolves on disk before it is written.
- Does not write outside the build directory and its own report path.
- Does not auto-chain to the planner.

---

## Related

- `commands/plan-build.md` — the next stage, after G1
- `commands/verify-plan.md` — G2
- `commands/run-build.md` — building one milestone, after G2
- `standards/build-orchestration.md` — the contract (§ 1 stage 1, § 2 the build directory, § 3 gates)
