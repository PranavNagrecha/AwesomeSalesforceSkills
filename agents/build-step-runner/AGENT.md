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

**Scope:** one step per invocation, no org connection, no deploy. The runner moves a step from `pending` to `built` (or to `blocked`); it never moves it further and never approves anything.

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
5. `standards/build-orchestration.md` — § 4 (step record fields and the status machine), § 5 (who owns tests — not this agent), § 8 (the plan CLI is the only writer of derived state).
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

The command prints the runnable steps as JSON on stdout — `pending` steps in the current milestone whose `depends_on` are all `documented`. When nothing is runnable it prints `[]` on stdout and the reason on stderr; read both, because the reason is what the refusal has to quote. Add `--milestone <id>` to force a milestone other than the first one not fully documented.

If `step_id` is not in that list, STOP and refuse with `REFUSAL_OUT_OF_SCOPE`, quoting the printed list, the stderr reason, and the step's current `status`. Two failure modes hide behind this check and both are worth naming in the refusal message: the step's predecessor is not documented yet, or the milestone this step belongs to sits behind an unapproved human gate.

One carve-out, and only one: a step whose status is `failed` or `blocked` never appears in `next`, because `next` lists `pending` steps only. Such a step may be re-run when the caller supplied `reason` — `build_plan.py` allows `failed → running` and `blocked → running` — and the refusal above does not apply. Record the caller's `reason` on the run. A step at `built`, `tested` or `documented` gets no carve-out: re-running it is a re-plan decision, not this agent's.

Never infer runnability by reading `depends_on` yourself. `build_plan.py` owns that computation per `standards/build-orchestration.md` § 8, and a second implementation of it is a second answer.

### Step 3 — Mark the step running

```bash
python3 scripts/build_plan.py set-status <build_dir>/plan.json <step_id> running --started <iso8601-utc>
```

This claims the step before any agent work begins, so a crashed run is visible as `running` rather than as a step that silently never started.

### Step 4 — Read the owning agent's Inputs section

The step's `agent` field names one run-time agent. Open `agents/<that-agent>/AGENT.md` and read its `## Inputs` section in full — plus `agents/<that-agent>/inputs.schema.json` when the agent ships one. That section, not this file, is the authority on what the agent needs and which of its inputs are required.

### Step 5 — Build the input map

For each row in the owning agent's Inputs table, resolve a value from exactly these three sources, in priority order:

| Source | Where it comes from | Notes |
|---|---|---|
| Step inputs | `plan.json.steps[].inputs{}` | the planner's explicit binding — always wins |
| Clarification answers | the answered questions in `plan.json` (rendered as `CLARIFICATIONS.md`) | matched by the question's recorded id, never by fuzzy text match |
| Upstream step outputs | `outputs[]` of steps this one lists in `depends_on`, resolved to real paths under `artefacts/<upstream-step-id>/` | pass the path, not the file contents |

Rules that make this mapping reviewable rather than improvised:

- A required input of the owning agent with no value from any of the three sources is a hard stop. Refuse with `REFUSAL_MISSING_INPUT`, naming the agent, the input, and the three places that were searched. Never invent a value, and never let the owning agent default it silently.
- An optional input with no value is left unset. Record it in the envelope's `inputs_received` as absent so the owning agent's own confidence rubric can account for it.
- If the owning agent requires `target_org_alias` (its frontmatter says `requires_org: true`), STOP with `REFUSAL_INPUT_AMBIGUOUS`: this loop is org-free by contract, so a step assigned to an org-requiring agent is a planning defect, not something the runner works around.
- Anything matching a credential shape per `skills/devops/pipeline-secrets-management` is replaced with `[REDACTED]` before it is echoed anywhere.

### Step 6 — Invoke the owning agent

The invocation is host-specific; the constraint on it is not.

- **In Claude Code:** call the Agent tool with `subagent_type` set to the step's agent id.
- **In any other host:** read `agents/<that-agent>/AGENT.md` end to end, including everything in its own Mandatory Reads, and execute its Plan inline.

Either way the instruction handed to the owning agent carries three clauses, verbatim in substance:

1. Write every artefact under `<build_dir>/artefacts/<step_id>/` and nowhere else. No file outside that directory, in either the build directory or the user's repo.
2. Return the output envelope defined by `agents/_shared/schemas/output-envelope.schema.json`, including its own confidence, Process Observations and citations.
3. Do not deploy, do not run any `sf` write command, and do not invoke another agent.

Pass the input map from Step 5, the step's `skills[]`, `templates[]` and `decision_trees[]` as the reading list the plan committed the step to, and the `acceptance_tests[]` as context — the owning agent builds so those tests can pass; it does not run them.

### Step 7 — Capture the envelope and the artefacts

Write the returned envelope to `<build_dir>/envelopes/<step_id>/<run_id>.json` verbatim. Then enumerate the files that now exist under `<build_dir>/artefacts/<step_id>/` and compare them against the step's declared `outputs[]`:

| Situation | What the runner records |
|---|---|
| Every declared output exists | clean built run |
| A declared output is missing | listed in the report and in Process Observations; confidence drops to MEDIUM |
| A file exists that no output declared | listed as an undeclared artefact; confidence drops to MEDIUM |
| A file was written outside `artefacts/<step_id>/` | LOW confidence, named explicitly, and flagged for the human — the constraint in Step 6 was violated |

The runner reports mismatches. It does not delete, move or edit what the owning agent produced.

### Step 8 — Set the terminal status

Read the owning agent's envelope. Two outcomes, and only two:

**Built.** The agent returned an envelope with no `refusal` block:

```bash
python3 scripts/build_plan.py set-status <build_dir>/plan.json <step_id> built \
  --run-agent <owning-agent-id> \
  --envelope envelopes/<step_id>/<run_id>.json \
  --result "<one-line outcome>" \
  --started <iso8601-utc>
```

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
| HIGH | the step was in `next` (or was a Step 2 re-run carve-out), every required input resolved from the plan, the envelope validates against the envelope schema, every declared output exists, and nothing was written outside `artefacts/<step_id>/` |
| MEDIUM | a declared output is missing, an undeclared artefact appeared, or an optional input had no value and the owning agent defaulted it |
| LOW | the envelope is missing or fails schema validation, a file landed outside the step's artefact directory, or the step was set `blocked` |

---

## Output Contract

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md` and `agents/_shared/schemas/output-envelope.schema.json`.

### Deliverables

1. **Summary** — the step id, its owning agent, the terminal status set, and the run id.
2. **Confidence** — HIGH / MEDIUM / LOW with the rationale keyed to the Step 9 table.
3. **The owning agent's envelope** — reproduced verbatim, plus the path it was stored at under `envelopes/<step-id>/`.
4. **Artefact paths produced** — every file now under `artefacts/<step-id>/`, each marked `declared` or `undeclared` against the step's `outputs[]`, with any declared-but-missing output listed separately.
5. **The `set-status` invocation** — the exact command line that was run, so the state transition is auditable from the report alone.
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
| `REFUSAL_OUT_OF_SCOPE` | The step is not in the `next` output and does not qualify for the Step 2 re-run carve-out — including the case where its milestone's predecessor gate is unapproved. Also: a caller asking for more than one step, for a deploy, or for a step whose owning agent id is not on the roster. |
| `REFUSAL_INPUT_AMBIGUOUS` | Two sources in Step 5 bind the same input to different values; the step's `agent` declares `requires_org: true`; the step's `outputs[]` name paths outside `artefacts/<step-id>/`. |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | The owning agent's refusal is neither a skill gap nor an ambiguity the plan can absorb — the plan itself needs revising, which is a re-plan and a new plan version, not a re-run. |

When the owning agent refuses with a skill gap or an ambiguity, the runner does not refuse: it sets the step `blocked` with that reason and returns normally. A blocked step is a recorded outcome, not an error.

---

## What This Agent Does NOT Do

- Does not deploy to an org, and never runs `sf project deploy start` or any other `sf` write command.
- Does not run the step's acceptance tests — that is `step-tester`.
- Does not write PLAN.md, the workbook, `decisions.md` or `traceability.md` — that is `build-doc-keeper`.
- Does not approve, request or record a human gate.
- Does not edit any `plan.json` field beyond the step status transitions and run record it sets through `build_plan.py`; it never hand-edits the file.
- Does not process more than one step per invocation, and does not auto-chain into the tester.
- Does not author Salesforce metadata itself, substitute for a blocked step, or freestyle guidance a skill does not carry.
- Does not invent a skill path — every citation resolves to a real file.
