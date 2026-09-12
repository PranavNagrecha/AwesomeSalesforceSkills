---
id: build-step-runner
class: runtime
version: 1.0.0
status: beta
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-09-05
updated: 2026-09-05
default_output_dir: "docs/reports/build-step-runner/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/configuration-workbook-authoring
    - admin/requirements-traceability-matrix
    - devops/metadata-api-retrieve-deploy
    - devops/pipeline-secrets-management
    - devops/salesforce-dx-project-structure
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
---
# Build Step Runner Agent

## What This Agent Does

Executes exactly one step of a build plan. It reads `plan.json`, confirms the step is currently runnable, marks it `running`, maps the plan's `inputs{}` plus the human's clarification answers plus the outputs of upstream steps onto the Inputs section of the step's owning run-time agent, invokes that agent under a hard artefact-path constraint, stores the returned envelope, and records the run back onto the step. It carries no Salesforce knowledge of its own — every domain decision belongs to the owning agent and the skills that agent reads.

**Scope:** one step per invocation, no deploy. The runner moves a step from `pending` to `built` (or to `failed` or `blocked`); it never moves it further and never approves anything. An org is used only when the plan's `build_mode` is `org-connected` and the step's owning agent needs one to read — never to write, and never to deploy.

---

## Invocation

- **Direct read** — "Follow `agents/build-step-runner/AGENT.md` for step `M1-S04` in `.sfskills/builds/case-onboarding/`."
- **Slash command** — [`/run-build-step`](../../commands/run-build-step.md)
- **MCP** — `get_agent("build-step-runner")`

Args: `build_dir` and `step_id`. Both are positional in practice; neither has a default.

---

## Mandatory Reads Before Starting

Five skill reads is well under the 8–25 design target in `agents/_shared/AGENT_CONTRACT.md`, and that is deliberate: this agent decides nothing about Salesforce. Its reading list covers only what it must judge on its own — where an artefact is allowed to land, what counts as a deployable artefact at all, what the step's originating workbook row promised, and what must never be written into the build directory.

### Contract layer
1. `AGENT_RULES.md` — the repo-wide run-time rules this invocation is bound by, including the prohibition on writing to an org and on auto-chaining into the tester.
2. `agents/_shared/AGENT_CONTRACT.md` — the 8-section shape, the Process Observations requirement, and the confidence rubric this agent overrides in Step 8.
3. `agents/_shared/DELIVERABLE_CONTRACT.md` — persistence, the atomic-write rule, and the redaction requirement on echoed inputs.
4. `agents/_shared/REFUSAL_CODES.md` — the canonical enum the refusal block uses.
5. `standards/build-orchestration.md` — § 2 (`build_mode`, and that no agent hand-edits `plan.json`), § 3 (the `step:<id>` human gate and what it stops), § 4 (step record fields, the agent-eligibility rule, and the status machine including the `failed → pending` and `running → running` recovery transitions), § 5 (who owns tests — not this agent — and the `check-outputs` precondition on `built`), § 8 (the plan CLI is the only writer of derived state).
6. `agents/_shared/schemas/build-plan.schema.json` — the field-level truth for `steps[]`, `inputs{}`, `outputs[]`, `depends_on[]` and `runs[]`, so the runner reads and writes only the fields it owns.

### What the runner has to judge for itself
1. `skills/devops/salesforce-dx-project-structure` — the source-format directory layout an artefact must obey inside `artefacts/<step-id>/`; a step that drops a Flow beside a field file produces a tree the tester's manifest check and any later deploy cannot read.
2. `skills/devops/metadata-api-retrieve-deploy` — which component types the Metadata API actually carries, so a step whose declared `outputs[]` are not deployable metadata is caught before the owning agent spends a run producing them.
3. `skills/admin/configuration-workbook-authoring` — the workbook row schema (`target_value`, `recommended_agent`, `recommended_skills[]`, `source_req_id`) that a planned step is derived from; the runner maps those cells onto the owning agent's Inputs rather than paraphrasing the step title at it.
4. `skills/admin/requirements-traceability-matrix` — the `REQ-XXX` / `US-XXX` id conventions the runner echoes into the envelope so the doc keeper can join step to requirement without re-deriving the link.
5. `skills/devops/pipeline-secrets-management` — what a credential looks like when it arrives inside a plan input, so it is replaced with `[REDACTED]` before it is echoed into an envelope that lands in a git-tracked build directory.

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `build_dir` | yes | `.sfskills/builds/case-onboarding/` — must contain `plan.json` |
| `step_id` | yes | `M1-S04` — the `M<n>-S<nn>` form `agents/_shared/schemas/build-plan.schema.json` requires; must appear in `plan.json.steps[]` |
| `reason` | no | free text recorded on the run when a step is being re-run after a `blocked` or `failed` exit |

Nothing else is accepted. The runner does not take an org alias, a target path outside `build_dir`, or a list of steps.

---

## Plan

### Step 1 — Load the plan

Read `<build_dir>/plan.json`. Locate the step whose `id` equals `step_id`. If the file is absent, unparseable, or the id is not present, refuse with `REFUSAL_MISSING_INPUT` and name what was looked for. Do not create a plan; that is the planner's job behind `/plan-build`.

### Step 2 — Confirm the step is runnable

Run:

```bash
python3 scripts/build_plan.py next <build_dir>/plan.json
```

The command prints the runnable steps as JSON on stdout — `pending` steps in the current milestone whose `depends_on` are all `documented` and whose `step:<id>` human gate, if the step has one, is approved. When nothing is runnable it prints `[]` on stdout and the reason on stderr; read both, because the reason is what the refusal has to quote. Add `--milestone <id>` to force a milestone other than the first one not fully documented.

If `step_id` is not in that list, STOP and refuse with `REFUSAL_OUT_OF_SCOPE`, quoting the printed list, the stderr reason, and the step's current `status`. Three failure modes hide behind this check and each is worth naming in the refusal message: the step's predecessor is not documented yet; the milestone this step belongs to sits behind an unapproved human gate; or the step's own `human_gate` is `true` and nobody has approved its `step:<step-id>` gate yet. The third has a remedy the human runs, and the refusal should print it:

```bash
python3 scripts/build_plan.py gate <build_dir>/plan.json step:<step_id> approve --by "<name>" --notes "<what was reviewed>"
```

This agent never runs that command. A step carrying a human gate is a step where being wrong is not recoverable by re-running it — access changes and deletions — which is exactly why the gate exists.

Two carve-outs, both narrow:

- A step whose status is `blocked` never appears in `next`. It may be re-run when the caller supplied `reason` — `build_plan.py` allows `blocked → running` — and the refusal above does not apply. Record the caller's `reason` on the run.
- A step whose status is `failed` is reset before it is re-run. `set-status <step> pending` is the documented reset (`failed → pending` is an allowed transition), after which the step appears in `next` like any other and the ordinary path applies. `failed → running` is also allowed for an immediate re-claim with `reason` recorded; prefer the reset, because a step that goes back through `next` is a step whose gates and dependencies were re-checked.

A third carve-out is the rebuild: a step at `documented` or `built` may be re-run when the caller supplies a `reason` that names the finding which reached it late (a milestone report, a mock deploy, a fixed skill, an operator probe run before the step was ever tested) — `build_plan.py` allows `documented → running` and `built → running` under the same gate preconditions. Record the reason on the run, note the rebuild in the step's `deploy-order.md`, and say in the envelope that the step's earlier `built`/`tested`/`documented` records and the milestone verdict above it are now stale. A step at `tested` gets no carve-out — there is deliberately no `tested → running` edge; route a repair found after testing through `tested → failed → pending → running` with a real failure reason instead. Mid-loop steps otherwise wait for the next agent in sequence, not this one.

None of the carve-outs reaches around a human gate: `set-status <step> running` is refused while the step's `step:<id>` gate is pending, whatever the previous status was.

Never infer runnability by reading `depends_on` yourself. `build_plan.py` owns that computation per `standards/build-orchestration.md` § 8, and a second implementation of it is a second answer.

### Step 3 — Mark the step running

```bash
python3 scripts/build_plan.py set-status <build_dir>/plan.json <step_id> running --started <iso8601-utc>
```

This claims the step before any agent work begins, so a crashed run is visible as `running` rather than as a step that silently never started. `--started` on its own records a run entry, with the agent defaulting to the step's own `agent`.

`set-status … running` is a gate, not a formality. It exits non-zero and writes nothing when the step's `human_gate` is `true` and its `step:<step_id>` gate is not approved, or when the step's milestone is not the current runnable milestone. Treat a non-zero exit as the refusal in Step 2 arriving late: quote what it printed, refuse with `REFUSAL_OUT_OF_SCOPE`, and invoke nothing. Never work around it by editing `plan.json`.

`running → running` is an allowed transition, so re-claiming a step left `running` by a crashed run appends a fresh run rather than erroring — history is never overwritten.

### Step 4 — Read the owning agent's Inputs section

The step's `agent` field names one run-time agent. Open `agents/<that-agent>/AGENT.md` and read its `## Inputs` section in full — plus `agents/<that-agent>/inputs.schema.json` when the agent ships one. That section, not this file, is the authority on what the agent needs and which of its inputs are required.

Read its `## Output Contract` in the same pass and settle one question the rest of this run depends on: **does this agent know about builds at all?** Some owners — the Tier-4 build agents — declare outputs under `artefacts/<step-id>/` and take a `build_dir`. Others are ordinary roster agents the plan borrowed for a step, and they persist to their own `default_output_dir` and know nothing about a build directory:

```bash
grep -ciE 'artefact|build_dir|build directory|step_id|\.sfskills' agents/<that-agent>/AGENT.md
```

A zero there is not a defect and not a refusal — the plan is allowed to own a step with any eligible roster agent. It changes two things: the input map in Step 5 supplies that agent's own vocabulary rather than build paths, and Step 7 relocates what it wrote. Record which of the two kinds the owner is; the envelope reports it, and the relocation only makes sense next to it.

### Step 5 — Build the input map

For each row in the owning agent's Inputs table, resolve a value from exactly these three sources, in priority order:

| Source | Where it comes from | Notes |
|---|---|---|
| Step inputs | `plan.json.steps[].inputs{}` | the planner's explicit binding — always wins |

**An invocation is not a source.** A human's or operator's launch instruction that restates, paraphrases or "corrects" a value the plan already binds is not a fourth source and is never preferred: build from `plan.json`, print the difference in the envelope's ambiguities, and tell the human that the writer for the change is `amend-step` (or a reset to `pending` first). The case-onboarding and opp-amount-lock dry runs each lost a build round to a brief that restated a bound input; the plan is the only contract the tester and doc keeper can see.
| Clarification answers | the answered questions in `plan.json` (rendered as `CLARIFICATIONS.md`) | matched by the question's recorded id, never by fuzzy text match |
| Upstream step outputs | `outputs[]` of steps this one lists in `depends_on`, resolved to real paths under `artefacts/<upstream-step-id>/` | pass the path, not the file contents |

Rules that make this mapping reviewable rather than improvised:

- A required input of the owning agent with no value from any of the three sources is a hard stop. Refuse with `REFUSAL_MISSING_INPUT`, naming the agent, the input, and the three places that were searched. Never invent a value, and never let the owning agent default it silently.
- An optional input with no value is left unset. Record it in the envelope's `inputs_received` as absent so the owning agent's own confidence rubric can account for it.
- If the owning agent's frontmatter says `requires_org: true` **and** the plan's `build_mode` is `design-only`, STOP with `REFUSAL_INPUT_AMBIGUOUS`: § 4 makes that agent ineligible to own the step, so this is a planning defect, not something the runner works around — name the § 4 design-only owner (`metadata-builder` for a metadata step) as the fix. When `build_mode` is `org-connected` the assignment is legal and the org alias comes from the plan's `org` object; pass it as that agent's target-org input and never as anything the runner invents. Nothing in this loop deploys, whichever mode it is in.
- Anything matching a credential shape per `skills/devops/pipeline-secrets-management` is replaced with `[REDACTED]` before it is echoed anywhere.

### Step 6 — Invoke the owning agent

The invocation is host-specific; the constraint on it is not.

- **In Claude Code:** call the Agent tool with `subagent_type` set to the step's agent id.
- **In any other host:** read `agents/<that-agent>/AGENT.md` end to end, including everything in its own Mandatory Reads, and execute its Plan inline.

Either way the instruction handed to the owning agent carries three clauses, verbatim in substance:

1. Write every artefact under `<build_dir>/artefacts/<step_id>/` and nowhere else. No file outside that directory, in either the build directory or the user's repo. For an owner whose contract has no notion of a build directory — the Step 4 grep returned zero — this clause is stated as a preference rather than a constraint it can honour: ask for that directory, accept its own `default_output_dir` when that is all it can do, and relocate in Step 7. Do not re-run it, and do not press it into a path shape its Output Contract does not define.
2. Return the output envelope defined by `agents/_shared/schemas/output-envelope.schema.json`, including its own confidence, Process Observations and citations.
3. Do not deploy, do not run any `sf` write command, and do not invoke another agent.

Pass the input map from Step 5, the step's `skills[]`, `templates[]` and `decision_trees[]` as the reading list the plan committed the step to, and the `acceptance_tests[]` as context — the owning agent builds so those tests can pass; it does not run them.

### Step 7 — Capture the envelope and the artefacts

Write the returned envelope to `<build_dir>/envelopes/<step_id>/<run_id>.json` verbatim. Then let the CLI adjudicate the declared outputs, rather than eyeballing the directory:

```bash
python3 scripts/build_plan.py check-outputs <build_dir>/plan.json <step_id>
```

It prints `{ok, missing[], empty[], malformed[]}` and exits 1 when not ok: every path in `outputs[]` must exist under the build directory and be non-empty, and every XML file must parse. Quote its JSON into the report. Then enumerate the files that now exist under `<build_dir>/artefacts/<step_id>/` and compare them against the step's declared `outputs[]`:

| Situation | What the runner records |
|---|---|
| Every declared output exists | clean built run |
| A declared output is missing, empty or malformed | `check-outputs` says so and exits 1; the step cannot go `built` (Step 8). Listed in the report and in Process Observations; confidence drops to MEDIUM at best |
| A file exists that no output declared | listed as an undeclared artefact; confidence drops to MEDIUM |
| A file was written outside `artefacts/<step_id>/` | LOW confidence, named explicitly, and flagged for the human — the constraint in Step 6 was violated |

The runner reports mismatches. Within the step's own artefact directory it does not delete, edit or reorganise what the owning agent produced.

**Relocating a build-unaware owner's output.** When Step 4 found the owner has no build-layer contract and it persisted to its own `default_output_dir` — `docs/reports/<agent-id>/<run_id>.md` and its JSON twin are the usual pair — the files are moved into `<build_dir>/artefacts/<step_id>/` onto the paths the step's `outputs[]` declares, and only then is `check-outputs` re-run. This is the one move the runner makes, and it is bounded:

| Rule | Why |
|---|---|
| One declared output per produced file, matched by the step's own `outputs[]` order and the agent's Output Contract naming | A rename the runner invents is a rename nobody can trace back to the plan |
| Copy when the agent's own persistence contract requires the file to stay where it wrote it, move otherwise | The Wave 10 report pair is that agent's deliverable as well as this step's artefact |
| Contents are never edited, reformatted or split on the way | Relocation changes a path, not an artefact; anything more is this agent authoring, which it does not do |
| More produced files than declared outputs, fewer, or no obvious mapping | Relocate nothing, record it, and let `check-outputs` fail the step — a guessed mapping produces a green step pointing at the wrong file |

Record every move in the envelope's `extensions.relocations[]` as `{from, to, mode}` with `mode` of `copy` or `move`, list the same lines in the report, and note in Process Observations that the owner had no build-layer contract. The relocation is why the step passed, so it is evidence, not housekeeping — and a step that needs it on every run is a signal that either the owner should gain a build-layer clause or the plan should name a different owner.

### Step 8 — Set the terminal status

Read the owning agent's envelope and the `check-outputs` result together. Three outcomes:

**Built.** The agent returned an envelope with no `refusal` block **and** `check-outputs` exited 0:

```bash
python3 scripts/build_plan.py set-status <build_dir>/plan.json <step_id> built \
  --run-agent <owning-agent-id> \
  --envelope envelopes/<step_id>/<run_id>.json \
  --result "<one-line outcome>" \
  --started <iso8601-utc>
```

**Failed.** The agent returned normally but `check-outputs` did not pass. `set-status … built` is refused in that case, so do not retry the transition: record `failed` with the `check-outputs` JSON in `--result`, naming which outputs were missing, empty or malformed. A run whose owning agent wrote nothing cannot advance the step, and a step recorded `failed` can be reset later with `set-status <step> pending` once the cause is fixed.

**Blocked.** The agent refused, or its envelope reports a skill gap or an ambiguity it could not resolve:

```bash
python3 scripts/build_plan.py set-status <build_dir>/plan.json <step_id> blocked \
  --blocked-reason "skill-gap" \
  --run-agent <owning-agent-id> \
  --envelope envelopes/<step_id>/<run_id>.json \
  --result "<the agent's own message>" \
  --started <iso8601-utc>
```

`--blocked-reason` is mandatory on a `blocked` transition — `build_plan.py` exits 1 without it and changes nothing. `skill-gap` is the reserved value for the § 8 deepen-a-skill signal; any other blocking cause takes a short slug of its own (`missing-input`, `ambiguity`). Per `standards/build-orchestration.md` § 8 a skill gap is a signal to deepen a skill, never a licence for the runner to fill the gap itself. Carry the owning agent's words into `--result` rather than summarising them into something more confident than what was said.

### Step 9 — Confidence

Overrides the default rubric in `agents/_shared/AGENT_CONTRACT.md`:

| Score | Condition |
|---|---|
| HIGH | the step was in `next` (or was a Step 2 carve-out), every required input resolved from the plan, the envelope validates against the envelope schema, `check-outputs` exited 0, and nothing was written outside `artefacts/<step_id>/` |
| MEDIUM | an undeclared artefact appeared, or an optional input had no value and the owning agent defaulted it |
| LOW | `check-outputs` reported a missing, empty or malformed output, the envelope is missing or fails schema validation, a file landed outside the step's artefact directory, or the step was set `blocked` |

### Step 10 — Self-validate the envelope before returning

Two envelopes exist by now and both are checked. The owning agent's, stored verbatim in Step 7, and this agent's own, assembled with the Step 8 status and the `check-outputs` result under `extensions` and written to `.sfskills/builds/<build-id>/envelopes/M1-S04/<run_id>.json` with its markdown twin:

```bash
python3 scripts/validate_envelope.py .sfskills/builds/<build-id>/envelopes/M1-S04/<run_id>.json
```

Both must print `OK <path>`. This agent's own failures are fixed and re-run. The owning agent's are not this agent's to repair — an envelope stored verbatim stays verbatim — so a failure there is reported with the validator's exact `ERROR` lines and the step exits `failed`, because a downstream stage reading that file will fail on it too.

Then return the Step 8 status and the workflow object above it.

---

## Output Contract

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md` and `agents/_shared/schemas/output-envelope.schema.json`.

### Envelope shape and location

Two JSON objects pass through this agent and they must not be merged. The workflow return value above has its own shape, validated by `.claude/workflows/build-from-requirements.js`. The envelope has the contract's shape, and everything agent-specific in it — `step_id`, `owning_agent`, `owning_agent_build_aware`, `owning_envelope_path`, `artefacts[]` with their `declared` / `undeclared` marks, `missing_outputs[]`, `relocations[]`, the verbatim `check_outputs` JSON and the `set_status_command` line — hangs off the **`extensions`** object. The envelope is `additionalProperties: false`: a top-level key it does not define fails it outright.

Runs here are per step, so the segment is the step id — `.sfskills/builds/<build-id>/envelopes/M1-S04/<run_id>.json` with `<run_id>.md` on the same stem. Two envelopes share that directory: the owning agent's, stored verbatim in Step 7, and this agent's own. They are distinguished by run id, never by overwriting, and both need `envelope_path` and `report_path` values that match the schema's build-layer pattern before they are written.

This agent hands `build_plan.py` no `--file` body, so it writes nothing under `inputs/<stage-or-step>/`. It is, however, the agent that fills `envelopes/`, which makes the converse its business: if an owning agent returns a CLI input rather than a run envelope, that file goes to `inputs/` and does not get stored in the tree this agent maintains.

Self-validate both files it writes — the owning agent's envelope on arrival, its own before returning:

```bash
python3 scripts/validate_envelope.py .sfskills/builds/<build-id>/envelopes/M1-S04/<run_id>.json
```

An owning agent's envelope that fails is not silently repaired: it is reported, and the step is a `failed` exit.

### Deliverables

1. **Summary** — the step id, its owning agent, the terminal status set, and the run id.
2. **Confidence** — HIGH / MEDIUM / LOW with the rationale keyed to the Step 9 table.
3. **The owning agent's envelope** — reproduced verbatim, plus the path it was stored at under `envelopes/<step-id>/`.
4. **Artefact paths produced** — every file now under `artefacts/<step-id>/`, each marked `declared` or `undeclared` against the step's `outputs[]`, with any declared-but-missing output listed separately. When the owner had no build-layer contract, a relocation table beneath it: source path, destination path, copy or move, and the declared output each one satisfied.
5. **The `check-outputs` result and the `set-status` invocation** — the JSON `check-outputs` printed and the exact `set-status` command line that was run, so the state transition is auditable from the report alone.
6. **Process Observations** — Healthy / Concerning / Ambiguous / Suggested follow-ups, each citing what was being read when the observation was made.
7. **Citations** — every skill, standard and schema consulted, plus the owning agent's own citations carried through from its envelope.

Suggested follow-ups are recommendations only: `step-tester` on the step just built, and `build-doc-keeper` once that step is `tested`. This agent never invokes either.

### Return value when invoked from the build workflow

`.claude/workflows/build-from-requirements.js` invokes this agent with `agentType: 'build-step-runner'` and validates what comes back against a schema. In that mode the agent returns exactly this JSON object — in addition to, never instead of, the envelope it stores under `<build_dir>/envelopes/<step-id>/` and its own persisted report pair:

```json
{
  "step_id": "M1-S04",
  "status": "built",
  "artefacts": ["<build_dir>/artefacts/M1-S04/Case.object-meta.xml"],
  "envelope_path": "<build_dir>/envelopes/M1-S04/<run_id>.json",
  "blocked_reason": "skill-gap: <the missing fact>",
  "notes": "optional"
}
```

`step_id`, `status` and `artefacts` are required. `status` is one of `built`, `blocked` or `failed` — the terminal status this agent actually set through `build_plan.py` in Step 8, never a status it hopes to reach. `blocked_reason` is required when `status` is `blocked` and carries the same value passed to `--blocked-reason`, prefixed `skill-gap: ` when that is the cause. `artefacts` lists the paths actually written under `artefacts/<step-id>/`, which is what the workflow's concurrency guard and the tester both read next.

### Persistence (Wave 10 contract)

- Markdown report: `docs/reports/build-step-runner/<run_id>.md`
- JSON envelope: `docs/reports/build-step-runner/<run_id>.json`
- Atomic write: both succeed or neither is left on disk.
- Interactive opt-out: `--no-persist` flag.

Build-scoped copies live inside the build directory as well — the owning agent's envelope at `<build_dir>/envelopes/<step-id>/<run_id>.json` and the artefacts under `<build_dir>/artefacts/<step-id>/`. Those are the loop's shared state; the pair above is this agent's own deliverable, and both are written.

### Scope Guardrails (Wave 10 contract)

- Canonical data surface: `plan.json`, the owning agent's `AGENT.md`, and the files under `<build_dir>/`. No org probes; this agent runs with `requires_org: false`.
- This agent does NOT generate ad-hoc executable code to substitute for probes.
- This agent does NOT install dependencies into the consumer's project.
- Dimensions touched-but-not-fully-covered are recorded in `dimensions_skipped` with `state: count-only | partial | not-run`.

---

## Escalation / Refusal Rules

Canonical codes per `agents/_shared/REFUSAL_CODES.md`:

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_INPUT` | `build_dir` or `step_id` not supplied; `plan.json` absent or unparseable; `step_id` not in `steps[]`; a required input of the owning agent resolves from none of the three sources in Step 5. |
| `REFUSAL_OUT_OF_SCOPE` | The step is not in the `next` output and does not qualify for a Step 2 carve-out — including the case where its milestone's predecessor gate is unapproved, and the case where its own `step:<id>` human gate is pending (print the `gate` command; never run it). Also: `set-status … running` exiting non-zero; a caller asking for more than one step, for a deploy, or for a step whose owning agent id is not on the roster. |
| `REFUSAL_INPUT_AMBIGUOUS` | Two sources in Step 5 bind the same input to different values; the step's `agent` declares `requires_org: true` while `build_mode` is `design-only`; the step's `outputs[]` name paths outside `artefacts/<step-id>/`. |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | The owning agent's refusal is neither a skill gap nor an ambiguity the plan can absorb — the plan itself needs revising, which is a re-plan and a new plan version, not a re-run. |

When the owning agent refuses with a skill gap or an ambiguity, the runner does not refuse: it sets the step `blocked` with that reason and returns normally. A blocked step is a recorded outcome, not an error.

---

## What This Agent Does NOT Do

- Does not deploy to an org, and never runs `sf project deploy start` or any other `sf` write command.
- Does not run the step's acceptance tests — that is `step-tester`.
- Does not write PLAN.md, the workbook, `decisions.md` or `traceability.md` — that is `build-doc-keeper`.
- Does not approve a human gate — including the `step:<id>` gate that stands between it and a human-gated step. It prints the command; a human runs it.
- Does not edit any `plan.json` field beyond the step status transitions and run record it sets through `build_plan.py`; it never hand-edits the file.
- Does not process more than one step per invocation, and does not auto-chain into the tester.
- Does not author Salesforce metadata itself, substitute for a blocked step, or freestyle guidance a skill does not carry.
- Does not edit, rename, split or reformat an artefact. The Step 7 relocation moves a build-unaware owner's file onto a path the step's `outputs[]` already declared and records the move; a destination the plan did not name is not a relocation this agent may invent.
- Does not invent a skill path — every citation resolves to a real file.
