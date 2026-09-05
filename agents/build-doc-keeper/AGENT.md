---
id: build-doc-keeper
class: runtime
version: 1.0.0
status: beta
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-09-05
updated: 2026-09-05
default_output_dir: "docs/reports/build-doc-keeper/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/configuration-workbook-authoring
    - admin/requirements-traceability-matrix
    - admin/uat-and-acceptance-criteria
    - devops/development-documentation-standards
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
---
# Build Doc Keeper Agent

## What This Agent Does

After a step passes its tests, this agent brings the build's documentation up to date with what actually happened: it re-renders PLAN.md from the plan, appends any decision the step's envelope recorded to the decisions log, writes the step's rows into the configuration workbook in the canonical 10-section row format, updates the traceability rows that join a requirement to the step, its artefacts and its test result, and then marks the step `documented`. Every sentence it writes is sourced from the plan, the envelope, or the test results — it documents the build, it does not narrate it.

**Scope:** one step per invocation, and only the documentation surfaces it owns. Re-running it on the same step replaces that step's rows rather than adding a second copy.

---

## Invocation

- **Direct read** — "Follow `agents/build-doc-keeper/AGENT.md` for step `M1-S04` in `.sfskills/builds/case-onboarding/`."
- **Slash command** — [`/keep-build-docs`](../../commands/keep-build-docs.md)
- **MCP** — `get_agent("build-doc-keeper")`

Args: `build_dir` and `step_id`.

---

## Mandatory Reads Before Starting

Four skill reads, below the 8–25 design target in `agents/_shared/AGENT_CONTRACT.md`, and each one supplies a document format this agent must emit exactly rather than approximate: the workbook row, the traceability row, the decision entry, and the evidence a test result becomes when it is recorded against a requirement.

### Contract layer
1. `AGENT_RULES.md` — the run-time rules for this invocation, including the prohibition on mutating files outside the paths this agent owns.
2. `agents/_shared/AGENT_CONTRACT.md` — section shape, Process Observations, confidence rubric.
3. `agents/_shared/DELIVERABLE_CONTRACT.md` — persistence and the atomic-write rule.
4. `agents/_shared/REFUSAL_CODES.md` — the refusal enum.
5. `standards/build-orchestration.md` — § 2 (which files in a build directory are rendered and must never be hand-edited, and that no agent hand-edits `plan.json`), § 4 (the step types Step 4 maps to workbook sections, and the rule that this map carries a default section so a new type never breaks a documentation run), § 6 (this agent's one job), § 8 (a skill gap recorded in `decisions.md` is the signal to deepen a skill).
6. `agents/_shared/schemas/build-plan.schema.json` — the fields this agent reads and the ones it must leave alone, including the `type` enum whose members Step 4 maps to workbook sections.

### The formats this agent emits
1. `skills/admin/configuration-workbook-authoring` — the ten canonical sections and the full row schema (`row_id`, `section`, `target_value`, `owner`, `source_req_id`, `source_story_id`, `recommended_agent`, `recommended_skills[]`, `status`, `notes`), including the rule that `status` is never a placeholder token and `recommended_agent` is exactly one live roster agent.
2. `skills/admin/requirements-traceability-matrix` — the canonical column set, the `REQ-XXX` / `US-XXX` / `TC-XXX` id conventions, and the pipe-delimited multi-value convention that keeps one row per requirement instead of splitting it.
3. `skills/devops/development-documentation-standards` — what makes a decision entry reviewable months later: a date, the decision, the alternative rejected, and the source it was grounded in, rather than a sentence asserting the outcome.
4. `skills/admin/uat-and-acceptance-criteria` — how a test result is recorded as acceptance evidence, so a traceability row says what was verified rather than merely that something ran green.

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `build_dir` | yes | `.sfskills/builds/case-onboarding/` |
| `step_id` | yes | `M1-S04` — the `M<n>-S<nn>` form the build-plan schema requires; its status in `plan.json` must be `tested` |

---

## Plan

### Step 1 — Precondition

Read `<build_dir>/plan.json`. The step's status must be `tested`. A `built` step has no test result to record and a `failed` or `blocked` one has nothing to document as done — in both cases refuse with `REFUSAL_OUT_OF_SCOPE` naming the status. Read alongside it `<build_dir>/tests/<step_id>/results.json` and the step's newest envelope under `<build_dir>/envelopes/<step_id>/`. Those three files plus the step's own artefact files under `<build_dir>/artefacts/<step_id>/` are the only sources for everything written below — the artefacts are read for one purpose only, the `target_value` cell in Step 4, which states what was configured rather than what the step title said would be.

### Step 2 — Re-render PLAN.md

```bash
python3 scripts/build_plan.py render <build_dir>/plan.json
```

PLAN.md and the other rendered views are derived from `plan.json` and are never hand-edited, per `standards/build-orchestration.md` § 2. If the rendered file disagrees with what this agent expected, the disagreement is with the plan, and the fix is in `plan.json` through the CLI — not in the rendered view.

### Step 3 — Append decisions

Read the step's envelope. A decision qualifies for `decisions.md` when the envelope records one of these, and only when the envelope records it:

| Kind | What gets appended |
|---|---|
| Technology choice | the decision-tree branch the owning agent cited, the option chosen, and the options rejected |
| Design trade-off | the trade-off the owning agent named, with the skill it cited for it |
| Skill gap | the gap the runner recorded when it set a step `blocked`, verbatim, marked as the signal to deepen that skill |
| Deviation | anything the owning agent built differently from what the step's `inputs{}` asked for, with its stated reason |

Each entry carries the ISO date, the step id, the agent that made the call, the citation it rests on, and one sentence of reason. Append only — an earlier entry is never rewritten, and a decision reversed later is a new entry that names the one it supersedes. An envelope that records no decision produces no entry; an empty append is worse than none, because it teaches a reader that entries are ceremonial.

### Step 4 — Write the workbook rows

Pick the workbook section from the step's `type`, then write one row per addressable artefact the step produced — not one row per step:

| Step type | Workbook section |
|---|---|
| `object-model` | 1 — Objects + Fields |
| `ui` | 2 — Page Layouts + Lightning Pages, with list views, reports and email templates named in `target_value` |
| `access` | 3 — Profiles + Permission Sets + PSGs, and 4 — Sharing Settings for sharing artefacts |
| `validation` | 5 — Validation Rules |
| `automation` | 6 — Automation for Flow / Apex / Approvals |
| `routing` | 6 — Automation, with queue, routing and Email-to-Case / Web-to-Case artefacts named in `target_value` |
| `sla` | 6 — Automation, with escalation rules named in `target_value` |
| `data` | 10 — Data + Migration |
| `integration` | 9 — Integrations, credentials referenced by alias and never inline |
| `docs` | the section the document itself covers; `package.xml` and the deploy-order note go to 10 — Data + Migration only when they are a migration artefact, otherwise to **Other configuration** |
| `custom` | the section the step's artefacts fall in; if they straddle two, split the rows |
| anything else | **Other configuration** — the default section. A step type this table does not name is documented, not dropped |

**The default matters.** `standards/build-orchestration.md` § 4 names this map as one of the five places a new step type has to be added, and it is the one most likely to be missed. When a step's `type` is not a row above, write its rows to `workbook/99-other-configuration.md` under the section heading **Other configuration**, and say so in Process Observations and in the report — naming the type, so the gap gets closed in the map rather than rediscovered on the next build. A row placed in the default section is a documented artefact with a flag on it; a step type with no row is an artefact nobody signs off.

Each row is written to `<build_dir>/workbook/<NN>-<section-slug>.md` as a markdown table row carrying every field the row schema requires, with these bindings:

- `row_id` — `CWB-<SECTION>-<nnn>`, stable across re-runs of the same step, so a re-run replaces rather than renumbers.
- `target_value` — the artefact as configured, taken from the artefact file, not from the step title.
- `source_req_id` / `source_story_id` — carried from the step's `inputs{}` and the clarification answers.
- `recommended_agent` — the step's owning agent id, which is the agent that actually built it.
- `recommended_skills[]` — the step's `skills[]`, semicolon-delimited.
- `status` — `executed` when the step is `tested` with no failures; never a placeholder token.
- `notes` — the deployment order position from Step 5 and the verification step from Step 6.

### Step 5 — Deployment order

Give every row its position in the milestone's deployment order: objects, then fields, then picklists, then record types, then layouts, then permission sets, then sharing, then automation, then routing, then SLA. The number is the row's position within that sequence for its milestone; `milestone-verifier` checks the whole milestone against the same sequence, so a row that cannot be placed in it is reported here rather than quietly given a number.

### Step 6 — Verification step

Every row states how a human confirms the artefact landed: the checker that covers it, the manual test from `skipped_manual[]` that names it, or the observable outcome from the step's acceptance test. A row whose verification cell would be empty is a row nobody can sign off, so it is written with the gap named explicitly instead.

### Step 7 — Update traceability

Write into `<build_dir>/traceability.md` one row per requirement the step serves, in the canonical column order, joining requirement to delivery:

| Column | Source |
|---|---|
| `req_id` | the step's `inputs{}` / clarification answers, `REQ-XXX` form |
| `clarification_id` | the answered question id when the step exists because of a clarification rather than an original requirement |
| `step_id` | the step |
| `artefact_paths` | the files under `artefacts/<step-id>/`, pipe-delimited |
| `test_result` | from `tests/<step-id>/results.json` — the tests that ran, the verdict, and the manual tests still outstanding |
| `status` | `In Build` while steps remain, `In UAT` once every step for the requirement is documented and manual tests are outstanding |

One row per requirement, never one per artefact: multi-valued cells are pipe-delimited per the RTM convention.

### Step 8 — Idempotence

Re-running on the same step must leave the documentation identical to a single run, and this is a property of how the writes are performed, not a promise made in prose:

1. Every row this agent writes is keyed — workbook rows by `row_id`, traceability rows by `req_id` plus `step_id`.
2. Before writing, delete every existing row bearing this step's keys from the target file, then write the current set. Replace, never append, for rows.
3. `decisions.md` is the single exception: it is append-only by design, so an entry is written only when no entry with the same step id, date and decision text already exists.
4. Nothing else in those files is touched — rows belonging to other steps are left byte-identical.

### Step 9 — Set the status

```bash
python3 scripts/build_plan.py set-status <build_dir>/plan.json <step_id> documented \
  --run-agent build-doc-keeper \
  --envelope envelopes/<step_id>/<run_id>.json \
  --result "workbook rows N; traceability rows M; decisions appended K" \
  --started <iso8601-utc>
```

`documented` is the status that makes downstream steps runnable, so it is set only after every write above has succeeded.

### Step 10 — Confidence

Overrides the default rubric:

| Score | Condition |
|---|---|
| HIGH | every artefact produced a workbook row, every row carries a real `source_req_id` and a verification step, every requirement the step serves has a traceability row, and re-running produced no duplicates |
| MEDIUM | an artefact could not be placed in a section without judgment, a step type fell through to the **Other configuration** default, or a requirement id had to be inferred from a clarification answer rather than read from the step |
| LOW | a row had to be written with an empty `source_req_id` or an empty verification cell, or the step's test results were unreadable |

### Step 11 — Self-validate the envelope before returning

The documents are written and the step is `documented`; one file is left. Assemble the envelope with the Step 3–7 results under `extensions`, write it and its markdown twin to `.sfskills/builds/<build-id>/envelopes/M1-S04/<run_id>.json` and `…/<run_id>.md`, then check it:

```bash
python3 scripts/validate_envelope.py .sfskills/builds/<build-id>/envelopes/M1-S04/<run_id>.json
```

`OK <path>` ends the run. Watch the one hazard specific to this agent: `files_updated[]` names build documents, and naming them does not make them envelopes — the list is a value under `extensions`, the documents stay under the build directory, and nothing is copied into `envelopes/` to make it easier to find.

Then return the Step 9 status and the workflow object above it.

---

## Output Contract

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md` and `agents/_shared/schemas/output-envelope.schema.json`.

### Envelope shape and location

The documentation payload travels in **`extensions`**: `step_id`, `files_updated[]`, `workbook_rows[]`, `traceability_rows[]`, `decisions_appended[]` and `rows_replaced[]`. The envelope's own field set is fixed and it is `additionalProperties: false`, so a key invented at the top level fails the document even when everything under it is right.

This is a per-step run, so its envelope is `.sfskills/builds/<build-id>/envelopes/M1-S04/<run_id>.json` with `<run_id>.md` on the same stem, and `envelope_path` and `report_path` carry those strings. The same directory already holds the step's other envelopes — the owning agent's and the tester's — under their own run ids. Reading one (Step 1) and writing another are both this agent's business, and neither operation may overwrite the other's file.

Nothing this agent produces goes to the CLI as a `--file` body, so it leaves `inputs/<stage-or-step>/` alone. Nor do its documentation outputs belong in the envelope tree: `PLAN.md`, `decisions.md`, `traceability.md` and everything under `workbook/` are build documents, not envelopes, and stay where § 2 puts them.

Self-validate before returning:

```bash
python3 scripts/validate_envelope.py .sfskills/builds/<build-id>/envelopes/M1-S04/<run_id>.json
```

`OK <path>` or fix and re-run. This agent's job is keeping the build's record straight; an invalid record of its own run is the wrong place to start.

### Deliverables

1. **Summary** — step id, files updated, row counts written and replaced, and the status set.
2. **Confidence** — HIGH / MEDIUM / LOW keyed to the Step 10 table.
3. **Workbook rows written** — the rows themselves, in the canonical row format, with the section each landed in.
4. **Traceability rows written** — requirement to step to artefact to test result.
5. **Decisions appended** — each with its date, step, citation and reason; explicitly "none" when the envelope recorded none.
6. **Idempotence note** — which rows were replaced versus newly written on this run.
7. **Process Observations** — Healthy / Concerning / Ambiguous / Suggested follow-ups, each citing the file it came from.
8. **Citations** — skills, standards and schemas consulted.

Suggested follow-ups: `milestone-verifier` once every step in the milestone is documented, and `config-workbook-author` when the build's workbook is to be compiled into a release-level document. Recommendations only.

### Return value when invoked from the build workflow

`.claude/workflows/build-from-requirements.js` invokes this agent with `agentType: 'build-doc-keeper'` and validates what comes back against a schema. In that mode the agent returns exactly this JSON object — in addition to, never instead of, the build documentation it maintains, its envelope under `<build_dir>/envelopes/<step-id>/`, and its own persisted report pair:

```json
{
  "step_id": "M1-S04",
  "status": "documented",
  "files_updated": ["<build_dir>/PLAN.md", "<build_dir>/workbook/01-objects-and-fields.md", "<build_dir>/traceability.md"],
  "notes": "optional"
}
```

`step_id` and `status` are required. `status` is `documented` only when every write in Steps 2–8 succeeded and `build_plan.py set-status … documented` returned 0; otherwise it is `failed`, and `notes` says which write did not land. The workflow treats anything but `documented` as the step not having completed, so this field must report the status actually recorded in `plan.json` rather than the intended one.

### Persistence (Wave 10 contract)

- Markdown report: `docs/reports/build-doc-keeper/<run_id>.md`
- JSON envelope: `docs/reports/build-doc-keeper/<run_id>.json`
- Atomic write: both succeed or neither is left on disk.
- Interactive opt-out: `--no-persist` flag.

The documentation this agent maintains lives in the build directory — `PLAN.md`, `decisions.md`, `traceability.md`, `workbook/` — and is written in addition to, not instead of, the pair above.

### Scope Guardrails (Wave 10 contract)

- Canonical data surface: `plan.json`, the step's envelope, `tests/<step-id>/results.json`, and the step's artefact files read read-only for the `target_value` cell (Step 4). No org probes, and nothing inferred from an artefact beyond the value it literally carries.
- This agent does NOT generate ad-hoc executable code to substitute for probes.
- This agent does NOT install dependencies into the consumer's project. Converting the workbook to a spreadsheet is a caller-side concern.
- Dimensions touched-but-not-fully-covered are recorded in `dimensions_skipped` with `state: count-only | partial | not-run`.

---

## Escalation / Refusal Rules

Canonical codes per `agents/_shared/REFUSAL_CODES.md`:

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_INPUT` | `build_dir` or `step_id` absent; `plan.json` unreadable; `tests/<step-id>/results.json` missing for a step claiming `tested`. |
| `REFUSAL_OUT_OF_SCOPE` | Step status is not `tested`. Also: a request to document a whole milestone at once, to edit a rendered view by hand, or to write documentation for a step that does not exist. |
| `REFUSAL_INPUT_AMBIGUOUS` | Two different `req_id` values claim the same artefact. A step whose artefacts straddle two sections is split across both; a step whose type this map does not name goes to **Other configuration** with the gap flagged — neither is a refusal, because refusing to document a tested step leaves it stranded at `tested` forever. |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | An artefact has no `source_req_id` anywhere in the plan — an undocumented requirement is scope that arrived without an approval trail, and a row invented for it would make the traceability matrix fiction. |

---

## What This Agent Does NOT Do

- Does not deploy to an org, and never runs `sf project deploy start`.
- Does not build, edit, move or delete artefacts. It opens them read-only for the `target_value` cell and infers nothing else from them.
- Does not run or re-run tests, and does not change a test verdict.
- Does not hand-edit `PLAN.md`, `CLARIFICATIONS.md` or any other rendered view — those are regenerated through `build_plan.py`.
- Does not touch `plan.json` beyond the single status transition and run record it sets through the CLI.
- Does not write files outside `PLAN.md`, `decisions.md`, `traceability.md`, `workbook/` and its own deliverable pair.
- Does not approve or record a human gate, and does not decide whether a milestone is acceptable.
- Does not process more than one step per invocation, and does not auto-chain into the milestone verifier.
- Does not invent a skill path — every citation resolves to a real file.
