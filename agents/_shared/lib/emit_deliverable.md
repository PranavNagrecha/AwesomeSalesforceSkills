# emit_deliverable — consumer helper for Wave 10 deliverables

Copy-paste pattern for the consuming AI (Claude Code, Cursor, MCP client, etc.) to honor the Wave 10 Deliverable Contract. Not executable code — a template the AI follows verbatim.

Read alongside `agents/_shared/DELIVERABLE_CONTRACT.md`.

---

## The pattern in 5 steps

### 1. Generate a `run_id` at invocation time

```
run_id = "2026-04-17T21-14-05Z"   # ISO-8601 compact, colons → dashes
```

One per run. Forms the filename stem.

### 2. Build the markdown report

Standard header block on every report:

```markdown
# <Agent Name> — Report

**Agent:** `<agent-id>` (version `<semver>`)
**Run ID:** `<run_id>`
**Date:** <YYYY-MM-DD>
**Mode:** `<single|design|audit|…>`
**Org:** `<alias>` (API v<nn>) — if `requires_org: true`
**Confidence:** <HIGH|MEDIUM|LOW>

---

## TL;DR

<One paragraph. The deliverable in a single screen.>

---

<rest of agent-specific content>

---

## Envelope

Canonical structured output at `<envelope_path>`. Inline preview:

\`\`\`json
<JSON envelope content>
\`\`\`
```

### 3. Build the JSON envelope

Conforms to `agents/_shared/schemas/output-envelope.schema.json`. Minimum shape:

```json
{
  "agent": "<agent-id>",
  "mode": "<mode-used>",
  "run_id": "<run_id>",
  "report_path": "docs/reports/<agent-id>/<run_id>.md",
  "envelope_path": "docs/reports/<agent-id>/<run_id>.json",
  "input_fixture": {
    "<field>": "<value or [REDACTED]>"
  },
  "summary": "...",
  "confidence": "HIGH|MEDIUM|LOW",
  "confidence_rationale": "...",
  "dimensions_compared": ["..."],
  "dimensions_skipped": [
    {
      "dimension": "...",
      "state": "count-only|not-run|partial",
      "reason": "...",
      "confidence_impact": "LOW|MEDIUM|NONE",
      "retry_hint": "..."
    }
  ],
  "findings": [],
  "process_observations": [],
  "citations": []
}
```

### 4. Write atomically

Pseudocode the consuming AI follows:

```
# Compute paths.
report_dir = "docs/reports/<agent-id>/"
report_path = report_dir + "<run_id>.md"
envelope_path = report_dir + "<run_id>.json"

# Make the directory.
ensure directory report_dir exists

# Write report first (bigger file, more likely to fail on disk-full).
write report_path with markdown content

# Write envelope.
try:
    write envelope_path with JSON content
except:
    # Atomic roll-back: remove the markdown.
    delete report_path
    re-raise
```

If the consuming AI cannot guarantee atomic rollback (e.g., running in a pure-chat interface), it emits both artifacts in the chat as fenced blocks AND writes the markdown as a single operation, then the envelope as a second operation with an explicit check. The user's final message should confirm both files exist.

### 5. Reply in chat with short confirmation + envelope preview

Pattern:

```
Report written to `docs/reports/<agent-id>/<run_id>.md`.
Envelope: `docs/reports/<agent-id>/<run_id>.json`.
Confidence: <LEVEL>. Dimensions compared: <N>. Skipped: <M>.

Summary: <one sentence>.

\`\`\`json
<envelope JSON>
\`\`\`
```

NOT the full report in chat. The full report is in the file.

---

## The `--no-persist` exception

Interactive / exploratory invocations may use `--no-persist` in the input:

```
Run <agent> with inputs X, Y, --no-persist.
```

When set:
- Do NOT write files.
- Show the full markdown report inline.
- Still emit the JSON envelope as a fenced block.
- `report_path` and `envelope_path` in the envelope are `null`.

---

## When the agent refuses

A refusal is still a deliverable. Write the files:

- Markdown contains the refusal reason + any partial findings + the refusal code (`REDUNDANT_INPUT`, `ORG_UNREACHABLE`, etc.).
- Envelope includes `refusal: { code: "...", message: "...", remediation_hint: "..." }` per the schema.

Chat confirmation names the refusal:

```
Report (refusal) written to `docs/reports/<agent-id>/<run_id>.md`.
Refusal code: <CODE>. <one-line remediation>.
```

Consumers can audit refusals the same way they audit successes — they leave an auditable trail.

---

## Common mistakes consuming AIs make

| Mistake | Fix |
|---|---|
| Dumping the whole markdown into chat instead of writing to disk | Always write first; chat gets the short confirmation. |
| Omitting the JSON envelope when the run is "interactive" | Envelope is REQUIRED in chat as a fenced block even when `--no-persist` is set. |
| Using colons in the filename timestamp (`21:14:05Z`) | Replace colons with dashes — `21-14-05Z` — for filesystem safety. |
| Writing the markdown to `<agent-id>.md` (no run_id) | Overwrites prior runs. Use `<run_id>.md` so history is preserved. |
| Running the agent and replying "here are the results" in prose, no file, no JSON | Every deliverable is a file + envelope pair. No exceptions except `--no-persist`. |
| Collapsing a count-only dimension into `dimensions_compared` | If you only got counts, it's `dimensions_skipped[].state: count-only`. |
| Generating ad-hoc Node/Python/Apex to substitute for a missing probe query | Extend the probe recipe in a PR. Do not fill gaps with disposable code. |

---

## See also

- `agents/_shared/DELIVERABLE_CONTRACT.md` — the contract this helper implements.
- `agents/_shared/schemas/output-envelope.schema.json` — the JSON schema every envelope validates against.
- `docs/consumer-responsibilities.md` — what a consuming AI must do.
- `skills/admin/salesforce-object-queryability` — classifying the reasons dimensions get skipped.
