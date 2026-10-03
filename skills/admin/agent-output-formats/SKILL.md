---
name: agent-output-formats
description: "Convert the canonical markdown+JSON deliverable of any SfSkills runtime agent into Excel, PDF, CSV, Notion card, ServiceNow ticket, or similar downstream format without adding dependencies to the consumer's project. NOT for an Agentforce action's output — use agentforce/agent-actions. NOT for exporting Salesforce data — use integration/bulk-api-2-patterns."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
tags:
  - agent-output
  - conversion
  - excel
  - pdf
  - csv
  - notion
  - servicenow
  - deliverable-contract
triggers:
  - "agent output to excel"
  - "convert agent report to pdf"
  - "export user-access-diff as spreadsheet"
  - "agent deliverable to notion"
  - "agent deliverable format conversion"
  - "turn the user-access-diff findings into a spreadsheet for the compliance board"
  - "send agent findings to ServiceNow or Jira without re-running the agent"
inputs:
  - The canonical deliverable pair (markdown + JSON envelope) from the agent run
  - The target format (excel, pdf, csv, notion, servicenow, jira, confluence)
  - The consumer's existing tooling (which conversion tools they already have installed)
outputs:
  - A recommended conversion path that does not require new dependencies
  - If no dependency-free path exists, a documented approach with the smallest possible dep footprint
  - Guidance on preserving auditability — the converted artifact references the canonical run_id
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Agent Output Formats

## Core principle — convert, don't regenerate

Every runtime agent produces a **canonical pair**: markdown + JSON envelope. That pair IS the source of truth. When a consumer asks for Excel/PDF/etc., the correct answer is to convert from that pair, not to re-run the agent with different instructions.

Reasons:

1. **Reproducibility** — the canonical deliverable is checked into `docs/reports/`. Six months later, anyone can regenerate the Excel from it. If the consuming AI regenerates by re-asking the agent, the output may differ due to LLM stochasticity.
2. **Auditability** — the `run_id` in the envelope is the tracking key. The Excel/PDF should reference it in its header, so "which run produced this?" is always answerable.
3. **Minimal dependencies** — reinstalling `exceljs`, `xlsxwriter`, `weasyprint`, etc. into a consumer's project every time someone wants a different format bloats their project's dependency tree.

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which run do you need converted: agent, `run_id`, and envelope path?" | Conversion must start from the canonical pair, and the `run_id` is the audit thread (Gotcha 9) | The exact envelope path and run | Every converted file traces back to one run |
| "Does the reader need only findings, or also what the run did not cover?" | Dropping `dimensions_skipped` makes a partial review look complete (Gotcha 3) | A findings sheet plus a coverage sheet, with confidence in the header | Reviewers see coverage gaps, as the contract requires |
| "Which agents will this conversion run against?" | Some envelopes carry `evidence` objects, others have no `findings` at all (Gotchas 1, 2) | One test envelope per agent shape | The script works for every agent, not only the first one tried |
| "Which tools already exist on the machine: jq, pandoc, a LaTeX engine, LibreOffice, Excel?" | PDF needs a LaTeX engine by default, and pandoc does not write CSV (Gotcha 7) | A conversion path using installed system tools | No project dependencies are added |
| "Will the output be opened in Excel, and does it hold long text or numeric Ids?" | Excel caps cells at 32,767 characters and numbers at 15 digits (Gotchas 5, 6) | Columns to drop or keep as text | The spreadsheet shows what the envelope says |

What proper configuration adds over "just exporting": a repeatable, dependency-free conversion that keeps the `run_id`, the confidence, and the coverage gaps visible in every format.

## Conversion decision tree

```
START: Consumer wants deliverable in format X.

Q1. Is X markdown or JSON?
    → Already the canonical form. No conversion needed; hand them the file path.

Q2. Is X a format the consumer's existing tooling handles natively?
    ├── Slack message / email body → paste the TL;DR + envelope-link from the markdown
    ├── Confluence / Notion / Obsidian → import the markdown directly (all support markdown import)
    ├── Jira / ServiceNow ticket → paste TL;DR in description + link the report file
    └── GitHub issue → embed markdown inline; link the report path
    → Prefer this path. Zero new dependencies.

Q3. Does the consumer want a "table"?
    ├── CSV: build it from the JSON envelope with `jq` (pandoc reads CSV but does not write it)
    ├── Excel: jq to CSV, then `soffice --headless --convert-to xlsx`, or open the CSV in Excel
    └── If jq is missing: recommend installing jq (1 tool, system-level)

Q4. Does the consumer want PDF?
    → `pandoc <report>.md -o <report>.pdf` — single command, no new project deps
    → pandoc uses LaTeX by default; without a LaTeX engine, pick another --pdf-engine
      or convert to HTML and print to PDF from a browser
    → If pandoc isn't available: recommend a system-wide install, NOT a project-level dep

Q5. Does the consumer want something format-specific (e.g. ServiceNow change ticket)?
    → Extract the fields from the JSON envelope (it's keyed for exactly this)
    → Template into the target system via its normal integration path
    → Do NOT ask the agent to regenerate in the target format
```

## Recommended Workflow

1. **Confirm the canonical deliverable exists** — `docs/reports/<agent-id>/<run_id>.{md,json}`. If not, run the agent first.
2. **Check the consumer's tooling**: do they already have `jq`, `pandoc` (and a LaTeX engine), or LibreOffice (`soffice`)? Use what is installed; do not add project dependencies.
3. **Walk the decision tree above.**
4. **Produce the conversion command** — a one-liner the user runs in their shell, not code added to their project.
5. **Include the canonical `run_id`** in the converted artifact's header — so auditors can trace it back.
6. **Record the conversion path** in the team's docs — next person who asks has a precedent.

## Key patterns

### Pattern 1 — Markdown → PDF via pandoc

```bash
pandoc docs/reports/user-access-diff/2026-04-17T21-14-05Z.md \
    -o ~/Desktop/user-access-diff.pdf \
    --metadata title="User Access Diff — Christina vs Carrie" \
    --metadata date="2026-04-17"
```

Zero project dependencies added. Works because pandoc is a widely-available system tool.

### Pattern 2: JSON envelope → CSV → Excel via jq and LibreOffice

```bash
# Findings as CSV. Nested values (evidence objects) become JSON text, because
# @csv rejects objects; a missing findings array yields a header row only.
jq -r '.run_id as $run
  | (["run_id","id","severity","title","detail","recommendation","evidence"] | @csv),
    ((.findings // [])[] | [$run, .id, .severity, .title, .detail, .recommendation, .evidence]
      | map(if type == "object" or type == "array" then tojson else . end) | @csv)' \
    docs/reports/user-access-diff/2026-04-17T21-14-05Z.json \
    > ~/agent-exports/findings.csv

# Convert to xlsx with LibreOffice, a system tool.
soffice --headless --convert-to xlsx --outdir ~/agent-exports ~/agent-exports/findings.csv
```

Corrected 2026-10-03: the earlier filter (`map(keys) | add | unique` with `@csv`) fails on any finding that carries `evidence`, and the `csv2xlsx` command named earlier has no fetched documentation. The full tested script is in `references/examples.md`, Example 5.

Or, if the user has Excel open:
```bash
open /tmp/findings.csv          # macOS; Excel imports CSV natively
```

### Pattern 3 — Envelope → ServiceNow change request

Extract the fields ServiceNow needs from the envelope:

```bash
jq '{
    short_description: .summary,
    description: (.summary + "\n\nRun ID: " + .run_id +
                  "\nConfidence: " + .confidence +
                  "\nFull report: " + .report_path),
    priority: (if (.findings // []) | map(.severity) | any(. == "P0") then "1"
               elif (.findings // []) | map(.severity) | any(. == "P1") then "2"
               else "3" end)
}' docs/reports/<agent-id>/<run_id>.json
```

Paste the JSON into the ServiceNow integration payload. No project deps. (Corrected 2026-10-03: object values built with `+` need parentheses in jq, and `(.findings // [])` keeps deliverables-only envelopes from failing; both versions were run against sample envelopes.)

### Pattern 4 — Notion / Obsidian / Confluence import

All three accept markdown imports directly. The user uploads the `.md` file via the platform's UI.

Preservation tip: include the `run_id` as a frontmatter field at the top of the markdown report, so when the page is imported, the run_id survives as a property.

### Pattern 5 — When conversion requires a heavy dependency

Scenario: user wants interactive Excel with embedded formulas referencing cells.

- Don't install `exceljs` / `openpyxl` into their project.
- Recommend they open the CSV in Excel and author the formulas there — the CSV round-trips fine.
- If they insist on scripted generation, recommend a one-off Python script in `~/bin/` or a dedicated report-tool project — NOT the project where the agent was invoked.

## Bulk safety

When converting reports for multiple runs in a batch:

- Use `find docs/reports/<agent-id>/ -name '*.md' -exec pandoc ...` to iterate, not one-by-one invocations.
- If converting to a centralized destination (e.g. uploading 50 reports to Notion), respect API rate limits.
- Never batch-convert and delete the canonical markdown — always retain the source.

## Error handling

- Canonical deliverable missing → refuse to convert. Run the agent first.
- Conversion tool missing → recommend system-wide install, not project-local.
- Target format can't represent a field from the envelope (e.g. nested arrays in Excel) → flatten in the CSV step, not by regenerating.

## Well-Architected mapping

- **Operational Excellence** — standardized conversion paths reduce "how do I turn this into Excel?" support tickets.
- **Reliability** — conversion-not-regeneration preserves the canonical `run_id` as the auditable thread.

## Anti-patterns

1. **Re-asking the agent to regenerate in the new format.** The agent is an expensive LLM call. Conversion is a cheap shell command. Always convert from the canonical.

2. **Installing format-specific libraries into the user's project.** `exceljs`, `xlsxwriter`, `weasyprint` — these are conversion tools, not project dependencies. Install system-wide or run from a dedicated CLI project.

3. **Stripping the `run_id`.** The converted artifact must reference it somewhere (header, filename, metadata). Without it, nobody can trace which run the Excel came from.

4. **Opening up new output-format surfaces on the agent itself.** If someone asks for "JIRA native format" as an agent output, refuse. The agent outputs canonical markdown+JSON. JIRA conversion is downstream.

## Official Sources Used

- Salesforce Architects — Reporting & Analytics Patterns: https://architect.salesforce.com/
- Pandoc Documentation (third-party CLI): https://pandoc.org/MANUAL.html
- Salesforce Developer — REST API: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm
- Salesforce Help, External Services: https://help.salesforce.com/s/articleView?id=sf.external_services.htm (not re-read; Salesforce Help does not fetch)
- The sources read for the 2026-10-03 revision are listed in `references/well-architected.md`.
