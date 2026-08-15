# Consumer Responsibilities

**Status:** Wave 10 canonical doc. Defines what a consuming AI (Claude Code,
Cursor, an MCP client, Aider, Windsurf, anything else) MUST do when running a
run-time agent from this library.

If you are building a tool that consumes SfSkills agents, read this first, then
read the two files it implements:
[`agents/_shared/DELIVERABLE_CONTRACT.md`](../agents/_shared/DELIVERABLE_CONTRACT.md)
(the library-side contract) and
[`agents/_shared/schemas/output-envelope.schema.json`](../agents/_shared/schemas/output-envelope.schema.json)
(the schema every envelope validates against). Where this page and those two
disagree, they win — and one known disagreement is flagged in
[Known contract conflict](#known-contract-conflict-no-persist-and-the-schema).

*Verified 2026-08-15: every path, schema constraint, and test command below was
run against the working tree.*

---

## Why a consumer-side contract exists

The library's agents produce the right analysis when followed correctly. In
practice, consuming AIs frequently:

- Dump the full report into chat and never write a file, so the deliverable
  disappears when the session ends
- Omit the JSON envelope, so downstream tooling cannot consume the output
- Silently skip dimensions or partially cover them, so reports look complete
  when they are not
- Generate ad-hoc executable code to fill gaps, producing output nobody can
  reproduce

These are consumer-side behaviours. The library cannot enforce them inside
someone else's codebase, but it can document them precisely.

---

## The five non-negotiables

### 1. Write the deliverable to disk

Every run-time agent invocation produces two files:

```
docs/reports/<agent-id>/<run_id>.md      ← human-readable markdown
docs/reports/<agent-id>/<run_id>.json    ← machine-readable envelope
```

This is not a convention you can quietly reinterpret — the schema encodes it.
`report_path` is a required string matching `^docs/reports/[a-z0-9-]+/.+\.md$`
and `envelope_path` a required string matching the same prefix with `.json`. A
consumer that writes to `/tmp/`, to chat only, or to an agent-scoped hidden
directory produces an envelope that fails validation.

Use `<run_id>` as the filename stem, ISO-8601 with colons replaced by dashes
(`2026-08-15T09-32-11Z`). Writing to `<agent-id>.md` instead overwrites the
previous run and loses the history the contract exists to create.

A user may override the output directory per invocation; the library's default
(`docs/reports/`) is tracked in git by convention. The only invocation shape
that writes nothing is `--no-persist` — see section 5 and the conflict note
below.

### 2. Emit the JSON envelope in chat as a fenced block

Alongside the chat confirmation, emit the complete envelope. Nine fields are
required — `agent`, `mode`, `run_id`, `report_path`, `envelope_path`, `summary`,
`confidence`, `process_observations`, `citations` — and `additionalProperties`
is `false`, so a consumer that bolts on its own keys fails validation.

A complete envelope that validates today:

````
```json
{
  "agent": "user-access-diff",
  "mode": "single",
  "run_id": "2026-08-15T09-32-11Z",
  "report_path": "docs/reports/user-access-diff/2026-08-15T09-32-11Z.md",
  "envelope_path": "docs/reports/user-access-diff/2026-08-15T09-32-11Z.json",
  "summary": "Christina has a narrower access surface than Carrie: 15 object-CRUD asymmetries and 1 system-permission asymmetry (ViewSetup).",
  "confidence": "MEDIUM",
  "confidence_rationale": "12 of 14 dimensions fully compared; apex-classes was count-only and fls was not requested.",
  "dimensions_compared": [
    "profile", "permission-sets", "psg-components", "object-crud", "system-perms",
    "vf-pages", "flow-access", "custom-perms", "named-credentials",
    "public-groups", "queues", "territories"
  ],
  "dimensions_skipped": [
    { "dimension": "apex-classes",
      "reason": "SetupEntityAccess returned row counts; the detail query exceeded the probe bound",
      "state": "count-only" },
    { "dimension": "fls",
      "reason": "include_field_permissions was not set",
      "state": "not-run" }
  ],
  "process_observations": [
    { "category": "concerning",
      "severity": "medium",
      "observation": "Both users inherit ModifyAllData through a permission set group rather than a profile.",
      "evidence": { "source": "mcp_probe", "probe": "describe_permission_set", "count": 2 } }
  ],
  "citations": [
    { "type": "skill", "id": "admin/permission-sets-vs-profiles",
      "path": "skills/admin/permission-sets-vs-profiles/SKILL.md",
      "used_for": "Framing the profile-vs-permission-set split in the summary" },
    { "type": "probe", "id": "user-access-comparison",
      "path": "agents/_shared/probes/user-access-comparison.md",
      "used_for": "Both users' access rows" }
  ]
}
```
````

Two nested shapes catch consumers out, because both are `additionalProperties:
false` with their own required keys:

- **`process_observations[]`** needs `category` (`healthy` | `concerning` |
  `ambiguous` | `suggested_followup`), `severity` (`info` | `low` | `medium` |
  `high`), `observation` (10+ chars) and `evidence` — and `evidence` is an
  **object**, not a string. A free-text evidence line fails validation.
- **`citations[]`** needs `type` (`skill` | `template` | `standard` |
  `decision_tree` | `mcp_tool` | `probe`), `id` and `used_for` (5+ chars).
  `path` is optional and omitted for `mcp_tool` entries.

### 3. Reply with a short confirmation, NOT the full report

Bad:

> Here's your user access diff report. [3,000 lines of markdown tables in chat.]

Good:

> Report written to `docs/reports/user-access-diff/2026-08-15T09-32-11Z.md`.
> Envelope: `…/2026-08-15T09-32-11Z.json`.
> Confidence: MEDIUM. Dimensions compared: 12. Skipped: 2.
>
> Christina has a narrower access surface than Carrie: 15 object-CRUD
> asymmetries and 1 system-permission asymmetry (ViewSetup). Full detail in the
> report.
>
> ```json
> { …envelope… }
> ```

The chat is for confirmation plus the structured envelope. Details go in the
file.

### 4. Classify every dimension — no silent drops

For multi-dimensional agents (those declaring `multi_dimensional: true` in
frontmatter — 13 of the 48 run-time agents do), every dimension the agent COULD
cover must appear in either `dimensions_compared` or `dimensions_skipped`.

Partial coverage is not full coverage. `dimensions_skipped[].state` is a
three-way enum and each value means something specific:

| `state` | Meaning |
|---|---|
| `not-run` | The dimension was never queried |
| `count-only` | A count or summary came back; the detail did not |
| `partial` | Some rows came back; the set is known to be incomplete |

Two consequences worth internalising. First, if `dimensions_skipped` is
non-empty, `confidence` must be `MEDIUM` or `LOW` — the schema says so in its
own description of the field. Second, if you queried `SetupEntityAccess` and got
row counts but not detail, that is `state: "count-only"`, not a
`dimensions_compared` entry.

If you do not know what the dimensions are, read the agent's Output Contract
section — it enumerates them. `user-access-diff`, for example, names 14.

### 5. Respect scope guardrails

The canonical data surface for every agent is:

- its declared probe recipes, under
  [`agents/_shared/probes/`](../agents/_shared/probes/) (6 recipes plus a
  README today), and
- the MCP tool set registered in
  `mcp/sfskills-mcp/src/sfskills_mcp/server.py` (38 tools).

Do NOT:

- generate ad-hoc Node/Python/Apex to substitute for a missing probe query;
- install new dependencies into the user's project (`npm install exceljs`,
  `pip install xlsxwriter`) to convert output;
- invoke the agent's logic against a data source the probe recipe does not name.

If the user asks for a format the agent does not support (Excel, PDF), see
[`skills/admin/agent-output-formats`](../skills/admin/agent-output-formats/SKILL.md)
— that skill covers converting the canonical deliverable without polluting the
project.

---

## The `--no-persist` opt-out

Interactive users sometimes want a quick answer without adding reports to their
repo:

```
Run user-access-diff for users A and B, --no-persist.
```

In this mode, per
[`agents/_shared/lib/emit_deliverable.md`](../agents/_shared/lib/emit_deliverable.md):

- Skip the file writes.
- Render the full markdown inline in chat.
- Still emit the JSON envelope as a fenced block.
- Set `report_path` and `envelope_path` to `null`.

This is the only invocation shape where a deliverable does not land on disk.
Deprecated agents (`status: deprecated`) are separately exempt — they emit a
redirect to their replacement, which honours the full contract itself.

### Known contract conflict: `--no-persist` and the schema

An envelope with `report_path: null` and `envelope_path: null` **does not
validate**. Both fields are in `required` and both are typed `"string"` with a
`^docs/reports/…` pattern, so `null` fails on two counts:

```bash
python3 - <<'PY'
import json, pathlib, jsonschema, warnings; warnings.filterwarnings("ignore")
schema = json.loads(pathlib.Path('agents/_shared/schemas/output-envelope.schema.json').read_text())
store = {json.loads(p.read_text())['$id']: json.loads(p.read_text())
         for p in pathlib.Path('agents/_shared/schemas').glob('*.json')
         if '$id' in json.loads(p.read_text())}
res = jsonschema.RefResolver.from_schema(schema, store=store)
env = {"agent": "user-access-diff", "mode": "single",
       "run_id": "2026-08-15T09-32-11Z",
       "report_path": None, "envelope_path": None,
       "summary": "Christina has a narrower access surface than Carrie.",
       "confidence": "MEDIUM", "process_observations": [], "citations": []}
for e in jsonschema.Draft7Validator(schema, resolver=res).iter_errors(env):
    print(list(e.path), e.message)
PY
# -> ['report_path'] None is not of type 'string'
# -> ['envelope_path'] None is not of type 'string'
```

The instruction and the schema were written at different times and nobody
reconciled them. Until they are, a consumer cannot simultaneously honour
`--no-persist` as written and pass schema validation. Follow the instruction —
it is what the library-side helper says and what the agents are told to do — and
treat schema validation as applying to persisted runs only. Do not invent a
placeholder path to make the validator green; that puts a lie in the envelope.

---

## Refusals are still deliverables

When an agent refuses (per
[`agents/_shared/REFUSAL_CODES.md`](../agents/_shared/REFUSAL_CODES.md), which
defines 16 codes), the consuming AI still writes both files:

- the markdown records the refusal reason, any partial work done, and the code;
- the envelope's `refusal` block is populated — `code` and `message` are
  required, `remediation_hint` is optional. When `refusal` is set, the schema
  permits the other deliverable fields to be absent.

"The agent just didn't work" is not an acceptable outcome. A refusal with a code
is an auditable one.

---

## Verification — am I doing this right?

A self-check for consuming AIs. **Five "yes" and two "no" is a passing run.**

| Question | Expected |
|---|---|
| Did I write the markdown to `docs/reports/<agent-id>/<run_id>.md`? | Yes |
| Did I write the envelope to `docs/reports/<agent-id>/<run_id>.json`? | Yes |
| Does the envelope validate against `output-envelope.schema.json`? | Yes (persisted runs — see the `--no-persist` conflict above) |
| Did my chat reply avoid pasting the full markdown report inline? | Yes |
| For a multi-dimensional agent, is every dimension in `_compared` or `_skipped`? | Yes |
| Did I generate disposable code to substitute for a probe query? | No |
| Did I install new dependencies in the user's project? | No |

---

## Enforcement

The library verifies, from inside itself:

| What | How | Status 2026-08-15 |
|---|---|---|
| Every run-time agent spec declares the contract — `default_output_dir`, `output_formats`, the `DELIVERABLE_CONTRACT.md` mandatory read, an Output Contract section with Persistence and Scope Guardrails, and enumerated dimensions when `multi_dimensional: true` | `cd mcp/sfskills-mcp && python3 -m unittest tests.test_deliverable_contract` | 7 tests, OK |
| An exported agent bundle is self-contained, and ships `DELIVERABLE_CONTRACT.md` + `emit_deliverable.md` (`scripts/export_agent_bundle.py:167–175`) | `cd mcp/sfskills-mcp && python3 -m unittest tests.test_agent_bundle` | 3 tests, OK |

The library cannot verify, from inside itself, whether a specific consumer
actually writes the files or emits the envelope. That is on the consumer.

**Verify it yourself by inspecting the output, not by running a harness.** Run
the agent, then list `docs/reports/<agent-id>/` for a matched `.md`/`.json` pair
and validate the JSON against `output-envelope.schema.json`. Note that
`scripts/smoke_test_agents.py` does **not** do this — it validates AGENT.md
structure, probe executability and a *synthetic* envelope against the schema,
and writes its output to `docs/validation/`. It never reads `docs/reports/`, so
it cannot tell you whether your integration honoured the contract on a real run.

---

## For consumer authors

Building a new tool that runs SfSkills agents? Your integration passes the
contract when:

1. Default behaviour writes to `docs/reports/<agent-id>/<run_id>.{md,json}`.
2. `--no-persist` is supported as an opt-out.
3. Chat replies are short (confirmation + envelope) by default.
4. The `dimensions_skipped` array is preserved verbatim through your UI —
   including the `state` value, which is the part that carries the meaning.
5. Your tool does not silently modify the agent's probe recipes or Mandatory
   Reads at runtime.

If your tool needs to transform the output (rendering the markdown in a UI, for
example), transform from the canonical file — do not regenerate from the agent's
logic.

---

## See also

- [`agents/_shared/DELIVERABLE_CONTRACT.md`](../agents/_shared/DELIVERABLE_CONTRACT.md) — the library-side contract.
- [`agents/_shared/lib/emit_deliverable.md`](../agents/_shared/lib/emit_deliverable.md) — copy-paste template for consumer AIs.
- [`agents/_shared/schemas/output-envelope.schema.json`](../agents/_shared/schemas/output-envelope.schema.json) — envelope schema, with `observation.schema.json` and `citation.schema.json` beside it.
- [`agents/_shared/REFUSAL_CODES.md`](../agents/_shared/REFUSAL_CODES.md) — the 16 refusal codes.
- [`multi-ai-parity.md`](./multi-ai-parity.md) — parity across first-class consumers.
- [`installing-single-agents.md`](./installing-single-agents.md) — how consumers install agents.
