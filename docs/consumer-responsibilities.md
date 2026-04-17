# Consumer Responsibilities

**Status:** Wave 10 canonical doc. Defines what a consuming AI (Claude Code, Cursor, MCP client, Aider, Windsurf, any other) MUST do when running a runtime agent from this library.

If you're building a tool that consumes SfSkills agents, read this first.

---

## Why a consumer-side contract exists

The library's agents produce the right analysis when followed correctly. But in practice, consuming AIs frequently:

- Dump the full report into chat and never write a file, so the deliverable disappears when the session ends
- Omit the JSON envelope, so downstream tooling can't consume the output programmatically
- Silently skip dimensions or partially cover them, so reports look complete when they're not
- Generate ad-hoc executable code to fill gaps, producing output no one can reproduce

These are consumer-side behaviors. The library can't enforce them in the consumer's codebase, but it can document them clearly and refuse to validate bundles against consumers that don't honor the contract.

This document names what honoring the contract looks like.

---

## The five non-negotiables

### 1. Write the deliverable to disk

Every runtime agent invocation produces two files:

```
docs/reports/<agent-id>/<run_id>.md      ← human-readable markdown
docs/reports/<agent-id>/<run_id>.json    ← machine-readable envelope
```

Use the default path unless the user explicitly overrides it. Do not write to `/tmp/`, chat-only, or agent-scoped hidden directories.

The sole exception is `--no-persist` mode — see section 5.

### 2. Emit the JSON envelope in chat as a fenced block

Alongside the chat confirmation, emit the complete envelope:

````
```json
{
  "agent": "user-access-diff",
  "run_id": "2026-04-17T21-14-05Z",
  "report_path": "docs/reports/user-access-diff/2026-04-17T21-14-05Z.md",
  ...
}
```
````

This gives any downstream AI (or human reviewer) the structured output inline, without needing to open the file. Format matters — the envelope is what automations key off.

### 3. Reply with a short confirmation, NOT the full report

Bad pattern:

> Here's your user access diff report. [3,000 lines of markdown tables in chat.]

Good pattern:

> Report written to `docs/reports/user-access-diff/2026-04-17T21-14-05Z.md`.
> Envelope: `docs/reports/user-access-diff/2026-04-17T21-14-05Z.json`.
> Confidence: MEDIUM. Dimensions compared: 10. Skipped: 3.
>
> Summary: Christina has a narrower access surface than Carrie; 15 CRUD asymmetries and 1 system-permission asymmetry (ViewSetup). Full detail in the report.
>
> ```json
> { ...envelope... }
> ```

The chat is for confirmation + the structured envelope. Details go in the file.

### 4. Classify every dimension — no silent drops

For multi-dimensional agents (those with `multi_dimensional: true` in frontmatter), every dimension the agent COULD cover must appear in either `dimensions_compared` or `dimensions_skipped`.

Partial coverage is NOT the same as full coverage. If you queried SetupEntityAccess and got row counts but not detail, that's `dimensions_skipped[].state: "count-only"` — not `dimensions_compared`.

If you don't know what the dimensions are, read the agent's Output Contract section. It enumerates them.

### 5. Respect scope guardrails

The canonical data surface for every agent is:
- Its declared probe recipes (under `agents/_shared/probes/`)
- The MCP tool set registered in `mcp/sfskills-mcp/src/sfskills_mcp/server.py`

Do NOT:
- Generate ad-hoc Node/Python/Apex to substitute for a missing probe query
- Install new dependencies into the user's project (`npm install exceljs`, `pip install xlsxwriter`, etc.) to convert output
- Invoke the agent's logic against a data source the probe recipe doesn't name

If the user asks for a format the agent doesn't support (Excel, PDF), see `skills/admin/agent-output-formats` — that skill describes converting the canonical deliverable to other formats without polluting the project.

---

## The `--no-persist` opt-out

Interactive users sometimes want a quick answer without cluttering their repo with reports. They invoke:

```
Run user-access-diff for users A and B, --no-persist.
```

In this mode:
- Skip the file writes.
- Render the full markdown inline in chat.
- Still emit the JSON envelope as a fenced block.
- Set `report_path` and `envelope_path` in the envelope to `null`.

This is the ONLY case where a deliverable doesn't land on disk. Any other invocation shape writes files.

---

## Refusals are still deliverables

When an agent refuses (hits an Escalation / Refusal rule, per `agents/_shared/REFUSAL_CODES.md`), the consuming AI still writes both files:

- The markdown records the refusal reason + any partial work done + the refusal code
- The envelope's `refusal` block is populated

This creates an auditable trail of WHY the agent refused. "The agent just didn't work" is not an acceptable outcome.

---

## Verification — am I doing this right?

A self-check for consuming AIs:

| Question | Expected answer |
|---|---|
| Did I write the markdown to `docs/reports/<agent-id>/<run_id>.md`? | Yes |
| Did I write the envelope to `docs/reports/<agent-id>/<run_id>.json`? | Yes |
| Is the envelope valid JSON matching `output-envelope.schema.json`? | Yes |
| Did my chat message avoid pasting the full markdown report inline? | Yes (short confirmation + envelope only) |
| For a multi-dimensional agent, are all dimensions accounted for? | Yes (in either `_compared` or `_skipped` arrays) |
| Did I generate disposable code to substitute for a probe query? | No |
| Did I install new dependencies in the user's project? | No |

Six "Yes"s and two "No"s → honoring the contract.

---

## Enforcement

The library can verify:
- Agent specs declare the contract (`test_deliverable_contract.py`)
- Bundles ship the contract doc + helper (bundle-completeness test)

The library cannot verify, from inside itself:
- Whether a specific consumer AI actually writes the files
- Whether the envelope is actually emitted as JSON

That's on the consumer's side. Running `scripts/smoke_test_agents.py` against a real org after using the agent is how YOU verify the contract is being honored — check `docs/reports/<agent-id>/` for files matching the expected shape.

---

## For consumer authors

Building a new tool that runs SfSkills agents? Your integration passes the contract when:

1. Default behavior writes to `docs/reports/<agent-id>/<run_id>.{md,json}`
2. `--no-persist` is supported as an opt-out
3. Chat replies are short (confirmation + envelope) by default
4. `dimensions_skipped` array is preserved verbatim through your tool's UI
5. Your tool does not silently modify the agent's probe recipes or Mandatory Reads at runtime

If your tool needs to transform the output (e.g., render the markdown in a UI), transform from the canonical file — don't regenerate from the agent's logic.

---

## See also

- `agents/_shared/DELIVERABLE_CONTRACT.md` — the library-side contract.
- `agents/_shared/lib/emit_deliverable.md` — copy-paste template for consumer AIs.
- `agents/_shared/schemas/output-envelope.schema.json` — envelope schema.
- `docs/multi-ai-parity.md` — parity across first-class consumers.
- `docs/installing-single-agents.md` — how consumers install agents.
