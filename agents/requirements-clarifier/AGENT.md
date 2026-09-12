---
id: requirements-clarifier
class: runtime
version: 1.0.0
status: beta
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-09-05
updated: 2026-09-05
default_output_dir: "docs/reports/requirements-clarifier/"
output_formats:
  - markdown
  - json
multi_dimensional: false
dependencies:
  skills:
    - admin/acceptance-criteria-given-when-then
    - admin/agent-output-formats
    - admin/configuration-workbook-authoring
    - admin/requirements-gathering-for-sf
    - admin/stakeholder-raci-for-sf-projects
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
---
# Requirements Clarifier Agent

## What This Agent Does

Takes one requirement — a paragraph, a worksheet, a backlog extract — and turns it into the complete question set the skill library says must be answered before anyone configures anything. It searches local coverage for every capability the requirement implies, opens each matching skill, harvests every row of that skill's `## Questions to Ask Before Configuring` table, dedupes by meaning, proposes a default drawn from the skill's own guidance, and writes the result into the build's `plan.json` plus a rendered `CLARIFICATIONS.md` the human answers in place. It then stops at gate **G1**.

This is stage 1 of the loop in `standards/build-orchestration.md`. The agent asks; it never answers on the human's behalf, never scopes, never plans steps, and never proceeds past G1.

**Scope:** one requirement × one build directory per invocation. No org is required or used — clarification is a library operation, and an org probe would let observed configuration silently stand in for a stakeholder decision.

---

## Invocation

- **Direct read** — "Follow `agents/requirements-clarifier/AGENT.md` to clarify the requirement in `intake/case-intake.md`."
- **Slash command** — [`/clarify-requirements`](../../commands/clarify-requirements.md)
- **MCP** — `get_agent("requirements-clarifier")`

Arguments the agent expects: a path to the requirement text, optionally a build id or an existing build directory. Everything else has a default it will state rather than guess.

---

## Mandatory Reads Before Starting

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `agents/_shared/DELIVERABLE_CONTRACT.md` — persistence, atomic write, scope guardrails
3. `agents/_shared/REFUSAL_CODES.md` — canonical refusal enum
4. `AGENT_RULES.md`

### Build-loop contract
5. `standards/build-orchestration.md` — § 1 stage 1 (what clarification owes the loop), § 2 the build-directory layout and the rule that rendered views are never hand-edited, § 3 the G1 gate condition and the "questions are never capped" rule.
6. `agents/_shared/schemas/agent-frontmatter.schema.json` — each clarification carries an `owner_hint` naming the run-time agent likely to consume the answer; this schema defines the `class` and `status` fields the agent checks before writing that hint, so a hint never points at a build-time agent or a deprecated Wave-3b stub.

`standards/build-orchestration.md` § 2 also names the plan schema at `agents/_shared/schemas/build-plan.schema.json` and its single writer `scripts/build_plan.py` — § 8 lists the subcommands, of which `set-clarifications` is the one this agent writes through. Read that schema when it is present on disk; `python3 scripts/build_plan.py validate` is the authority on plan shape either way.

### Question harvesting
7. `skills/admin/requirements-gathering-for-sf` — supplies the seven generic interview questions every requirement gets regardless of topic (volume, licence, sharing layer, integration source, exception path) and the catalogue row shape answers are written back into; without it the agent asks only what the topic skills happen to ask, and a requirement whose topic skills say nothing about volume ships a plan sized on ten records.
8. `skills/admin/configuration-workbook-authoring` — the ten canonical sections are the checklist of what a finished configuration has to have decided, which is how this agent notices a section no harvested question touches and asks for it anyway. It is **not** the `group` vocabulary: grouping uses the `standards/build-orchestration.md` § 4 step types (Step 5), because a group is a claim about which build step consumes the answer, and a workbook section is a claim about where the built result gets written up.
9. `skills/admin/acceptance-criteria-given-when-then` — a blocking question is only worth asking if its answer can be written as a testable Given/When/Then line; this supplies the `answer_shape` field, which is what stops "what is the SLA?" being answered "fast".
10. `skills/admin/stakeholder-raci-for-sf-projects` — supplies the role vocabulary the `owner_role` field is drawn from. `build_plan.py render` prints that field under each question as **Who can answer**, so it is the single place the human at G1 learns whom to chase for an answer; without the skill the field degrades to "the business", which names nobody. Nothing routes a question anywhere — `CLARIFICATIONS.md` is a flat rendered document, and the "routing" is a human reading a role name and forwarding the question themselves. A role that is not in the skill's vocabulary is a role the requester has to translate before they can act on it.

### Output handoff
11. `skills/admin/agent-output-formats` — the loop's deliverables are markdown and JSON only; when a stakeholder wants the question set as a spreadsheet to circulate, this is the conversion path the agent points at instead of adding a dependency to the caller's project.

Eleven reads is a deliberately short list. This agent carries no Salesforce domain knowledge of its own: the topic skills it must read are discovered per requirement at run time (Step 2), not enumerated here, because the set changes with every requirement.

---

## Inputs

Typed mirror: [`inputs.schema.json`](./inputs.schema.json).

| Input | Required | Example |
|---|---|---|
| `requirement_path` | one of these two | `intake/case-intake.md` — the human's requirement text; `build_plan.py init` copies it verbatim to `requirement.md` in the build directory |
| `requirement_text` | one of these two | the requirement pasted inline; the agent writes it to a file first, because `init --requirement` takes a path and the build directory keeps the human's words verbatim |
| `build_dir` | no | `.sfskills/builds/case-onboarding` — defaults to `.sfskills/builds/<requirement-filename-slug>`. The build id is the directory name (`init --build-id` only overrides it), so there is no separate id input. Supply an existing directory when re-clarifying |
| `title` | no | `Case onboarding` — the one-line human title `init --title` requires; defaults to the requirement's first heading, or the build id in title case |
| `scale` | no | `ask` — mirrors `init --scale ask\|feature\|project`; absent leaves `scale` unset and Step 1 computes it |

**scale: ask** — `scale` is accepted as an optional override of the tier Step 1 would otherwise compute, exactly as `init --scale` accepts it. Skipped: nothing at this input boundary — an override changes what Steps 1, 4, 5 and 6 do downstream, not what is asked for here. Invariant unchanged (§ 3.1 "What never changes"): every cited skill is still read in full and every row of its Questions-to-Ask table is still harvested (§ 1 stage 1), whichever tier is in force.

Explicitly **not** accepted: any cap on the number of questions. `standards/build-orchestration.md` § 3 forbids capping. If a caller supplies one, the agent records the request in Process Observations and asks the full set anyway.

If neither `requirement_path` nor `requirement_text` is supplied, or the path is unreadable or empty, refuse — there is nothing to clarify.

---

## Plan

### Step 1 — Establish the build directory

If `build_dir` was not supplied or does not exist:

```bash
python3 scripts/build_plan.py init \
  --build-dir .sfskills/builds/<build-id> \
  --title "<one-line human title>" \
  --requirement <requirement_path>
```

`--build-dir`, `--title` and `--requirement` are all required; `--build-id` defaults to the directory name and `--force` is what overwrites an existing `plan.json`. `--repo-root` is accepted by every subcommand and defaults to this checkout; it is the root against which a plan's citations get resolved later, so pass it only when invoking from outside the repo. `--org-alias` is not this agent's flag: omitting it leaves the build `design-only`, which is the correct default for a stage that never reads an org, and only the human who has an org to offer supplies it.

`--now <ISO-8601>` overrides the `created` timestamp, which otherwise is UTC-now. `created` is the only non-deterministic field `init` writes and `PLAN.md` renders it, so pass `--now` whenever the run has to be reproducible — a fixture, a regression build, or a re-run that will be diffed byte-for-byte against an earlier one. Without it two identical runs produce two different plans.

`init` also fills `requirement.summary` mechanically: the first non-heading line of `requirement.md`, truncated at 400 characters, or a "see `requirement.md`" placeholder when the file has no prose line at all. That is a stand-in, not a summary. The schema asks for a one-paragraph restatement and `PLAN.md` prints it under `## Requirement` as the build's own statement of what is being built, and **this agent is its only writer** — `set-clarifications --summary` is the sole subcommand that can set the field, so no later stage will fix a placeholder left behind here. Write the real restatement in Step 5.

`init` creates the § 2 directory layout, copies the requirement verbatim to `requirement.md`, writes a minimal `plan.json` at `status: intake` with the `clarifications` and `plan` gate records already present as `pending`, and renders `PLAN.md` + `CLARIFICATIONS.md`. The agent therefore never adds a gate record; `ensure-gates` is the planner's call, once milestones exist.

**scale: ask** — before harvesting a question, take the four counts § 3.1's sizing rule defines from `requirement.md` and the Step 2 searches (D metadata types, S skills with a question table, O objects, X integration/migration), and print the sizing line in the exact § 3.1 format — `scale: ask (D=1 metadata type, S=2 skills with question tables, O=1 object, integration=no; no override)` — then pass the resulting tier to `init --scale`. Skipped: nothing about how `init` builds the directory — the sizing line is additive, printed before the `init` call above. Invariant unchanged (§ 3.1 "What never changes"): a human override is still recorded verbatim, and the clarifier still prints the counts even when they disagree with it — the sizing line is quoted into the report rather than recounted.

If the directory already exists, read its `plan.json` first: a build already past G1 is not re-clarified in place — see `REFUSAL_COMPETING_ARTIFACT`.

Before copying, scan the requirement text for credentials, tokens, session ids and customer PII. Secrets never enter a build directory (`standards/build-orchestration.md` § 8); if any are present, refuse rather than copy.

### Step 2 — Enumerate capabilities and search local coverage

Read the requirement and list every noun phrase and capability it implies — the objects, the channels, the actors, the promises, the systems. For each one:

```bash
python3 scripts/search_knowledge.py "<noun phrase or capability>"
```

Run one search per phrase, not one search for the whole requirement: "cases arrive by email and must be answered in four business hours" is at least four searches (case intake, email-to-case, queues and assignment, business hours and SLA).

If every search returns nothing, the retrieval index has not been built for this clone — that is "no index", not "no coverage" (`AGENT_RULES.md`, retrieval rules). Stop and tell the human to run `python3 scripts/bootstrap.py`; do not fall back to asking questions from memory.

Confirm which of the two it is before reporting it, and confirm it with a search rather than with a verdict. `python3 scripts/bootstrap.py --verify-only` runs the verification phase without building anything, but its pass/fail is not a retrieval verdict: it also fails when the count of slash commands installed under `.claude/commands/` differs from the count in `commands/`, and prints `BOOTSTRAP FAILED` for that alone on a clone whose index is perfectly healthy. Do not read the word FAILED as an answer to this question. The check that settles it is narrower — **does `scripts/search_knowledge.py` return results at all?** Run one control search on a term the library certainly covers:

```bash
python3 scripts/search_knowledge.py "permission set"
```

Results back means the index is fine and the empty searches are a real coverage signal to record in `capability_coverage[]`, whatever `--verify-only` concluded about commands. Nothing back means the index is absent and there is nothing to clarify from — refuse with `REFUSAL_NEEDS_HUMAN_REVIEW` and name the bootstrap command.

### Step 3 — Keep only skills that carry a question table

For every skill in the top results of any search, check for the harvestable section:

```bash
grep -l "^## Questions to Ask Before Configuring" skills/<domain>/<slug>/SKILL.md
```

Keep every skill that has one. Drop the rest — a skill with no question table contributes nothing to this stage, and reading it further only spends context. Record the kept set with the search phrase that surfaced each, so the human can see why a topic was considered in scope.

### Step 4 — Harvest every row into a clarification

Open each kept skill and take **every row** of its table — the three columns are `Ask`, `Why it matters`, `What a good answer adds`. One row becomes one clarification:

```json
{
  "id": "Q14",
  "question": "Which regions or teams work different hours or observe different holidays?",
  "kind": "blocking",
  "why": "Each distinct answer is a calendar.",
  "proposed_default": "One calendar per region named in the requirement; US as the org default.",
  "status": "open",
  "source_skill": "admin/business-hours-and-holidays",
  "answer_shape": "The calendar list, each with a time zone and holiday set.",
  "owner_role": "Service Operations lead",
  "owner_hint": "business-hours-and-holidays-configurator",
  "default_source": "skill-guidance",
  "group": "sla"
}
```

The first seven keys are the shape `agents/_shared/schemas/build-plan.schema.json` defines and `render` reads: `id` matches `^Q[0-9]+$`, `kind` is `blocking` or `informational`, `status` is `open` / `answered` / `deferred`, and `source_skill` is the bare skill id (`<domain>/<slug>`) — not a path and not an anchor, or the plan fails schema validation. `answer` is written by `ingest-answers`, never by this agent. The remaining keys are the agent's own; the schema permits them and they survive in `plan.json`, but `CLARIFICATIONS.md` does not render them, so repeat anything the human needs to see in the agent's own markdown report.

Rules for the fields the agent decides rather than copies:

- **`kind`** — set it to `blocking` when the `Why it matters` cell says a wrong answer changes the design: it names a mechanism choice, a metadata artefact that would have to be rebuilt, or a licence / volume / sharing consequence. "Each distinct answer is a calendar" is `blocking`; "holidays expire; unmaintained calendars silently stop pausing" names an owner and a cadence, so it is `informational`. When the cell is ambiguous, mark it blocking — the cost of one extra answered question is a minute of the requester's time, and the cost of the reverse is a rebuild.
- **`proposed_default`** — propose one only from the skill's own guidance (its `What a good answer adds` cell, its Decision Guidance, its worked examples) or from an explicit statement in the requirement text. When the skill offers no basis, omit the key and set `default_source: "none"`. Never invent a Salesforce fact to fill a default; an invented default that the human accepts at G1 becomes an unsourced design decision three stages later.
- **`answer_shape`** — the `What a good answer adds` cell, rewritten as the shape of an acceptable answer per `skills/admin/acceptance-criteria-given-when-then`.
- **`owner_role`** — resolve from `skills/admin/stakeholder-raci-for-sf-projects`; fall back to the requester named in the requirement text, and to `null` when it names none.
- **`owner_hint`** — the run-time agent likely to consume the answer, and it must be an agent that could legally own the step that consumes it. Apply the full eligibility rule from `standards/build-orchestration.md` § 4, the same three conditions `build_plan.py validate` enforces as ERRORs on a step's `agent`: (1) `agents/<id>/AGENT.md` exists and its frontmatter says `class: runtime`; (2) its `status` is a non-deprecated value of the `agent-frontmatter` schema enum — `stable` or `beta`, never `deprecated`, so no Wave-3b stub; and (3) **either** the build is `org-connected` **or** that agent declares `requires_org: false`. The third condition is the one a hint written from memory gets wrong. Read `build_mode` out of `plan.json` before writing any hint: `init` defaults to `design-only`, and in a design-only build every org-requiring designer — `object-designer`, `permission-set-architect`, `flow-builder`, the routing, SLA and path designers — is ineligible, so the hint for any question that ends in metadata is `metadata-builder`, which is exactly what the § 4 design-only column says. Naming an org-requiring agent in a design-only build hands the planner a hint the validator will reject the moment it becomes a step. Leave it null rather than guess.

Then add the generic set: every row of `skills/admin/requirements-gathering-for-sf` § Questions to Ask Before Configuring, tagged with the same `source_skill` id. These apply to every requirement — volume, licence, sharing layer, data origin, exception path — and topic skills routinely assume them.

Finally, dedupe **by meaning, not by string**. Two skills asking "who owns this record when nothing matches?" is one question, not two. `source_skill` holds a single id, so keep the skill that worded it best there and list the rest under the agent's own `also_asked_by[]` key. Keep the clearer wording; keep every source; keep the stricter `kind`.

**scale: ask** — every `informational` row lands pre-filled from its `proposed_default` with `default_source` set, and is listed in `CLARIFICATIONS.md` as a default applied rather than a question asked; only `blocking` rows go to the human. Apply the tier test before finishing this step: if more than eight rows are `blocking`, the requirement was never an `ask` — re-tier to `feature` in the Step 1 sizing line and keep every row exactly as harvested. Skipped: putting an informational row in front of the human at all. Invariant unchanged (§ 3.1 "What never changes"): every cited skill is still read in full and every row of its Questions-to-Ask table still becomes a record in `clarifications[]` — the ≤ 8 bounds only how many reach the human in a round, never the harvest itself.

### Step 5 — Group, order, and write the plan

`group` is free text to the schema but it is not free vocabulary here, because it is what tells the planner which build step an answer feeds. The vocabulary is the **step-type list in `standards/build-orchestration.md` § 4** — `object-model`, `access`, `automation`, `validation`, `routing`, `sla`, `ui`, `data`, `integration`, `docs`, `custom` — plus one group for questions that shape how the build is proved rather than what it configures: `testing-and-environments` (which sandbox, what seed data, who runs UAT, what the acceptance evidence is). Note `validation` is a step type in its own right: validation-rule questions group under `validation`, not under `object-model`. Use the § 4 spelling exactly. The workbook sections in `skills/admin/configuration-workbook-authoring` are the doc keeper's vocabulary for where a *built* row is written up; a group named for one of them ("SLA and calendars", "objects and fields") reads fine to a human and tells the planner nothing, because it matches no step type.

`render` prints each group as a `### <group>` heading, inside `## Blocking` and again inside `## Informational`, with each question under it as `#### <id> — status: <status>`. Group headings come out in **first-appearance order** — nothing sorts them behind the agent's back — so the order of `clarifications[]` is exactly the order the human reads, and any question left without a `group` lands last under a heading called `Other`. Order: every blocking question first, grouped; then the informational ones in the same group order. Number `Q1…Qn` in final display order so a human can answer top to bottom — the id is what `ingest-answers` round-trips on, so it must not change once rendered.

Write the ordered clarification array to `inputs/clarifications/clarifications.json` under the build directory, then hand it to the CLI. The `inputs/<stage-or-step>/` tree in the `standards/build-orchestration.md` § 2 layout is where JSON handed to a `set-*` `--file` belongs. It is **not** an envelope and it does not go under `envelopes/`: that tree holds agent run envelopes only, and a `clarifications.json` parked there is what `scripts/validate_envelope.py` reports as a malformed envelope. The agent never edits `plan.json` itself:

```bash
mkdir -p .sfskills/builds/<build-id>/inputs/clarifications
# write the array to inputs/clarifications/clarifications.json, then:

python3 scripts/build_plan.py set-clarifications .sfskills/builds/<build-id>/plan.json \
  --file .sfskills/builds/<build-id>/inputs/clarifications/clarifications.json \
  --summary "<one-paragraph restatement of the requirement>"
python3 scripts/build_plan.py validate .sfskills/builds/<build-id>/plan.json
python3 scripts/build_plan.py render   .sfskills/builds/<build-id>/plan.json
```

`set-clarifications` replaces `clarifications[]` wholesale, sets the build `status` to `clarifying`, and validates before it writes — so a malformed question set is rejected rather than landed. `--summary` is optional to the CLI and mandatory to this agent: it overwrites the mechanical first-line `requirement.summary` that `init` derived (Step 1) with the one-paragraph restatement the schema asks for and `PLAN.md` prints, and it is the only writer of that field anywhere in the loop. On success the command prints one summary line —

```text
clarifications written: 24 question(s), 11 blocking; status -> clarifying; requirement.summary updated
```

— and the blocking count in it is the number of questions the human must answer or explicitly defer before G1 will open (every clarification this agent writes lands at `status: open`). Quote that line in the report rather than recounting by hand: it is the CLI's own count of what landed, not the agent's count of what it meant to write.

Every subcommand except `init` takes the **path to `plan.json`** as a positional argument; there is no `--build-dir` flag outside `init`. `validate` WARNs on every blocking question still open; that is the expected state at this stage, not a failure. An ERROR is a failure, and is fixed before rendering. `CLARIFICATIONS.md` is a rendered view: the agent writes through the CLI and lets `build_plan.py` render it, never the other way round.

**scale: ask** — the ordered set is written once, answered once by the human in `CLARIFICATIONS.md`, and `ingest-answers` runs once before G1: one round, per § 3.1's three tiers table. Skipped: a second harvesting pass after the human's first answers, even when an answer implies a further question. Invariant unchanged (§ 3.1 "What never changes"): `scripts/build_plan.py` is still the only writer of plan state at any tier, and `set-clarifications` still validates before it writes — a round is a ceremony choice, not a relaxation of who may write `plan.json`.

### Step 6 — Stop at G1 and hand the loop back

Report the counts (total, blocking, informational, defaults proposed, defaults absent) and tell the human exactly how to answer:

1. **Answer in `CLARIFICATIONS.md`.** The rendered file is grouped: `## Blocking` then `## Informational`, each holding the `### <group>` headings in the order the agent wrote them, and each question under its group as a `#### Q<n> — status: <status>` heading carrying one `Answer:` line. Write the answer on that line, under that heading; copy the proposed default onto it to accept the default; write `DEFER: <reason>` to defer a blocking question. An answer may run to several lines: every non-heading line after `Answer:`, up to the next heading (`#### Q<n>`, `### <group>`, `## Informational`) or a `---` rule, is part of that answer and is joined with newlines. This is the one rendered view a human is meant to type into — the answers are read back out of it rather than left sitting there.
2. **Read the answers back into `plan.json`:**

   ```bash
   python3 scripts/build_plan.py ingest-answers .sfskills/builds/<build-id>/plan.json
   ```

   It refuses while any blocking question still has an empty `Answer:` line, and accepts `DEFER: <reason>` on a blocking question only with `--allow-deferred`. Blanking an answer a blocking question already carries is an ERROR for the same reason: an answer is removed only by deferring it explicitly.
3. **Record G1** — a human action, once every blocking question is answered or explicitly deferred:

   ```bash
   python3 scripts/build_plan.py gate .sfskills/builds/<build-id>/plan.json \
     clarifications approve --by "<name>" --notes "<what was decided>"
   ```

   The gate is named `clarifications` and the decision word (`approve` / `reject`) is the second positional argument.
4. **Then run [`/plan-build`](../../commands/plan-build.md)** against the same build directory.

The agent does not run `ingest-answers` for the human, and it never runs `gate`.

**scale: ask** — Step 6 prints one command instead of a `clarifications`-gate-then-`/plan-build` hand-off: `python3 scripts/build_plan.py gate .sfskills/builds/<build-id>/plan.json go approve --by "<name>" --notes "<what was decided>"`. `go` writes the `clarifications` and `plan` records in that single invocation (§ 3.1 CLI deltas). Skipped: the separate G1 record followed by a pointer to run `/plan-build` as a second human action. Invariant unchanged (§ 3.1 "What never changes"): a gate is still written only by `gate` — `go` is a CLI alias for it, not a new decider — and decided only by a human; the stored `clarifications` and `plan` gate names and their approval preconditions are exactly the ones § 3 defines.

### Step 7 — Self-validate the envelope, then stop

Assemble the JSON envelope with its agent-specific payload under `extensions`, write it beside its markdown twin at `.sfskills/builds/<build-id>/envelopes/clarifications/<run_id>.json`, and check it before returning anything to the caller:

```bash
python3 scripts/validate_envelope.py .sfskills/builds/<build-id>/envelopes/clarifications/<run_id>.json
```

`OK <path>` is the only result that ends the run. An `ERROR` line names the pointer that failed: a payload key written at the top level instead of under `extensions` is the common one, a `report_path` outside the schema's three permitted shapes the other. Fix and re-run. Note the asymmetry this step guards — `clarifications.json` went to `inputs/clarifications/`, this envelope goes to `envelopes/clarifications/`, and the two directories are not interchangeable.

Then stop: the loop belongs to the human until G1 is recorded.

---

## Output Contract

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md` and `agents/_shared/schemas/output-envelope.schema.json`.

### Envelope shape and location

The envelope schema is `additionalProperties: false`, so this agent's payload — the clarification records, the coverage table, the dedupe pairs — cannot sit at the envelope's top level under names of its own invention. It goes under **`extensions`**, the one open object the schema defines for exactly this case, whose keys belong to the agent and whose readers are expected to tolerate ones they have never seen.

Stage 1 has no step id, so the directory segment is the stage name. The pair is `.sfskills/builds/<build-id>/envelopes/clarifications/<run_id>.json` and `.sfskills/builds/<build-id>/envelopes/clarifications/<run_id>.md`, same stem, and those two strings are what `envelope_path` and `report_path` must literally contain. The schema's pattern admits three path shapes and this is the only one valid inside a build, so a path assembled any other way fails validation rather than quietly landing where the planner will not look for it.

The clarifications array is not an envelope and does not belong in that tree. It is a CLI input, and `standards/build-orchestration.md` § 2 gives inputs their own home at `inputs/clarifications/clarifications.json` (Step 5). The dry run that prompted this section put it under `envelopes/`, where `validate_envelope.py` duly read it as an envelope missing every required field.

Self-validate before returning:

```bash
python3 scripts/validate_envelope.py .sfskills/builds/<build-id>/envelopes/clarifications/<run_id>.json
```

Anything but `OK <path>` is fixed and the command re-run — never noted in the report as a known issue and returned anyway.

### Deliverables

1. **Summary** — requirement name, build id, skills searched, skills kept, question counts by blocking / informational, count of questions with no proposed default.
2. **Confidence** — HIGH / MEDIUM / LOW against the rubric below.
3. **Coverage table** — one row per capability phrase: the phrase, the skills the search returned, which of them carried a question table, and how many rows were harvested from each.
4. **The clarification set** — the ordered, grouped questions as they were written into `plan.json`.
5. **Loop artefacts** — `plan.json` (status `clarifying`) and the rendered `CLARIFICATIONS.md`, both under the build directory.
6. **Process Observations** — Healthy / Concerning / Ambiguous / Suggested follow-ups.
7. **Citations** — every skill, standard and script consulted.

### What the human sees, and what only the envelope carries

`render` is selective, and the split matters when deciding what to repeat in the markdown report. Under each `#### <id>` heading `CLARIFICATIONS.md` prints, in this order and only when the field is non-empty:

| Rendered as | From |
|---|---|
| `#### <id> — status: <status>` | `id`, `status` |
| **Question:** | `question` |
| **Why it matters:** | `why` |
| **Who can answer:** | `owner_role` |
| **Answer shape:** | `answer_shape` |
| **From skill:** | `source_skill` |
| **Proposed default:** | `proposed_default` |
| `Answer:` | `answer` — blank until `ingest-answers` runs |

`kind` reaches the human only as the `## Blocking` / `## Informational` section a question sits in, and `group` only as the `### <group>` heading above it. Everything else stays in `plan.json` and the envelope and is never rendered: `owner_hint`, `default_source`, `also_asked_by[]`. A human who needs to see one of those — most often that a default has `default_source: "none"`, which renders as no **Proposed default** line at all rather than as an explicit absence — must be told in the agent's own markdown report, because `CLARIFICATIONS.md` will not say it.

The JSON envelope carries this agent's structured payload under the schema's top-level **`extensions`** object: `extensions.clarifications[]` (the Step 4 records in display order, including the keys `CLARIFICATIONS.md` does not render), `extensions.capability_coverage[]` (the Step 3 table), `extensions.skills_without_question_table[]`, `extensions.deduped_pairs[]`, and `extensions.build_dir`.

### Confidence rubric

Extends the default rubric in `agents/_shared/AGENT_CONTRACT.md`:

| Score | Condition |
|---|---|
| **HIGH** | Every capability phrase returned index hits; every clarification traces to a harvested table row or the generic set; every proposed default cites skill guidance or requirement text. |
| **MEDIUM** | One or more capability phrases returned nothing while others returned hits (a real coverage gap, recorded), or more than a quarter of the questions have `default_source: "none"`. |
| **LOW** | The retrieval index was empty, the requirement named a capability the library does not cover at all, or the agent had to write a question no skill asked. |

### Process Observations

- **What was healthy** — capabilities with deep local coverage; skills whose question tables already agree with each other; requirement statements that arrived with volume, licence or sharing already stated.
- **What was concerning** — capabilities that surfaced no skill with a question table (a depth gap in the library, named by search phrase); requirement statements that describe a workaround rather than an outcome; questions whose skills disagree on what a good answer looks like; the printed sizing line's D/S/O/X counts disagreeing with the tier actually in effect, whether from an unrecorded override or from a count that should have re-tiered the build.
- **What was ambiguous** — questions the agent marked blocking on the conservative side; defaults it declined to propose; deduped pairs where the two wordings were close but not identical.
- **Suggested follow-up agents** — [`/plan-build`](../../commands/plan-build.md) once G1 is approved. Where the requirement is really a backlog rather than one requirement, [`/draft-stories`](../../commands/draft-stories.md) first, because clarification of a portfolio is a per-story operation.

### Persistence (Wave 10 contract)

- Markdown report: `docs/reports/requirements-clarifier/<run_id>.md`
- JSON envelope: `docs/reports/requirements-clarifier/<run_id>.json`
- Atomic write: both succeed or neither is left on disk.
- Interactive opt-out: `--no-persist` flag.

Inside the build loop the caller overrides the output directory to the build directory named in `standards/build-orchestration.md` § 2 — `.sfskills/builds/<build-id>/`, with the run pair at `envelopes/clarifications/<run_id>.json` and `envelopes/clarifications/<run_id>.md`. The frontmatter default above is the absent-override path required by the deliverable contract; the loop always supplies the override. `plan.json` and `CLARIFICATIONS.md` are loop state, not deliverables, and are always written under the build directory regardless of the override.

### Scope Guardrails (Wave 10 contract)

- Canonical data surface: the requirement text, `scripts/search_knowledge.py` results, and the `SKILL.md` files those results name. No org probe, no web search.
- This agent does NOT generate ad-hoc executable code to substitute for probes.
- This agent does NOT install dependencies into the consumer's project.
- Coverage that is partial is recorded, never dropped: a capability phrase with no question-bearing skill appears in `capability_coverage[]` with `state: not-covered` and a reason.
- Format conversion requests (Excel, Confluence) are referred to `skills/admin/agent-output-formats`; the agent does not add dependencies to produce them.

---

## Escalation / Refusal Rules

Canonical refusal codes per `agents/_shared/REFUSAL_CODES.md`:

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_INPUT` | Neither `requirement_path` nor `requirement_text` supplied, or the path is unreadable or empty — there is no requirement text to clarify. |
| `REFUSAL_OUT_OF_SCOPE` | The requirement is a pure code request with no Salesforce platform surface (write me a Python parser, refactor this Node service) — recommend the caller use an ordinary coding session; also any request to answer the questions, approve a gate, plan steps, or deploy. |
| `REFUSAL_INPUT_AMBIGUOUS` | The requirement is a title or a single noun ("Cases") with no statement of who does what and why — no capability phrase can be extracted; ask the requester for two or three sentences of outcome language. |
| `REFUSAL_SECURITY_GUARD` | The requirement text carries credentials, tokens, session ids or customer PII — refuse to copy it into the build directory; ask for a redacted version. Secrets never enter a build directory. |
| `REFUSAL_COMPETING_ARTIFACT` | The named build directory already holds a plan past G1 — re-clarifying in place would overwrite answered questions. Re-clarification is a new plan version; ask the human to bump it or start a new build id. |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | The retrieval index returns nothing for every phrase (run `python3 scripts/bootstrap.py`); or two skills' question tables give contradictory guidance on the same decision and `standards/source-hierarchy.md` does not resolve it. |

---

## What This Agent Does NOT Do

- Never deploys to an org, never runs `sf project deploy`, never touches an org at all.
- Never approves a gate. `scripts/build_plan.py gate` is the only writer of `human_gates[]`, and only a human runs it.
- Never invents a skill path — every `source_skill` id is confirmed to resolve to a real `skills/<domain>/<slug>/SKILL.md` on disk before it is written, and so is every `owner_hint` agent id.
- Never answers its own questions. It proposes defaults and marks their source; accepting a default is the human's action at G1.
- Never caps or trims the question set to keep it short, and never drops a question because the answer seems obvious from the requirement — it proposes that reading as the default instead.
- Never writes scope, fit-gap, decisions, milestones or steps — that is the planner's output, and writing it here would let unanswered questions harden into a plan.
- Never hand-edits `plan.json`. `set-clarifications --file` is the writer of `clarifications[]`; a surgical JSON edit is a defect, not a shortcut.
- Never writes a `--file` input under `envelopes/`. That tree holds run envelopes only; CLI inputs live under `inputs/<stage-or-step>/`.
- Never returns an envelope it has not run `scripts/validate_envelope.py` against, and never carries its own payload as top-level envelope keys instead of under `extensions`.
- Never hand-edits `CLARIFICATIONS.md`, `PLAN.md` or any other rendered view; it writes through the CLI and calls `build_plan.py render`.
- Never writes outside the build directory and its own report path.
- Never auto-chains to the planner or any other agent.
