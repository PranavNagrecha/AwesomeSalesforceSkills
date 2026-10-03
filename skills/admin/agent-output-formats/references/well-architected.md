# Well-Architected Notes — Agent Output Formats

## Relevant Pillars

- **Operational Excellence** — Standard conversion paths mean the team answers "how do I turn this into Excel?" once, not every time. Runbook knowledge compounds.
- **Reliability** — Converting from the canonical pair preserves the `run_id` thread, so audit questions ("which run produced this Excel?") are always answerable. Regeneration breaks that thread.

## Architectural Tradeoffs

### Convert vs regenerate

| Convert (from canonical) | Regenerate (re-ask the agent) |
|---|---|
| Deterministic — same input → same output | Stochastic — LLM output drifts |
| Cheap — shell command | Expensive — LLM call |
| Preserves run_id lineage | Creates a new run_id |
| Depends on standard CLI tools | Depends on LLM availability |

Rule: convert by default. Regenerate only when the canonical pair is missing or when the agent's logic itself has been updated.

### System-level vs project-level conversion tools

| System-level (`pandoc`, `jq`, `csv2xlsx` in `~/bin/`) | Project-level (`exceljs` in `package.json`) |
|---|---|
| Installed once per developer | Installed per project |
| No project-level drift | Drifts with project releases |
| Available for every project | Project-scoped |

Rule: conversion tools belong at system level. Project-level deps are for the project's business logic, not downstream report formatting.

## Anti-Patterns

1. **Regenerating instead of converting** — wastes LLM calls, drifts output, breaks audit trail. Fix: convert from the canonical pair.

2. **Installing `exceljs`/`openpyxl` in the consumer's project** — bloats the dep tree. Fix: conversion tools live in `~/bin/` or as system installs.

3. **Stripping `run_id` during conversion** — breaks the "which run produced this?" audit thread. Fix: every converted artifact references the run_id in its header.

4. **Adding output formats to AGENT.md** — turns every agent into a format-conversion engine. Fix: agent outputs are stable (markdown + JSON). Conversion is downstream.

5. **Deleting the canonical pair after conversion** — loses the reproducibility property. Fix: converted artifacts are additive, never replacements.

## Official Sources Used

Read for this revision (2026-10-03):

- Deliverable Contract, local path `agents/_shared/DELIVERABLE_CONTRACT.md`. Canonical pair, `run_id` conventions, multi-dimensional rule and `dimensions_skipped`, scope guardrails (no dependencies in the consumer's project), atomic write, persistence path override.
- Output Envelope Schema, local path `agents/_shared/schemas/output-envelope.schema.json`. Required fields, optional `findings` and `deliverables`, `evidence` typed as an object, `dimensions_skipped` fields.
- jq 1.7 Manual: https://jqlang.github.io/jq/manual/. Invoking jq (`-f` / `--from-file`), Format strings and escaping (`@csv`), Convert to/from JSON (`tojson`), Alternative operator (`//`).
- Pandoc User's Guide: https://pandoc.org/MANUAL.html. Creating a PDF (LaTeX default, `--pdf-engine`), `--metadata`, input formats (CSV is an input format) and output formats (no CSV writer).
- LibreOffice Help, Starting LibreOffice Software With Parameters: https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html. `--convert-to`, `--outdir`.
- RFC 4180, Common Format and MIME Type for CSV Files: https://www.rfc-editor.org/rfc/rfc4180.txt. Quoting rules 6 and 7.
- Microsoft Support, Excel specifications and limits: https://support.microsoft.com/en-us/office/excel-specifications-and-limits-1672b34d-7043-467e-8e27-269d656771c3. 32,767 characters per cell, 1,048,576 rows, 15-digit precision.
- Microsoft Support, EXACT function: https://support.microsoft.com/en-us/office/exact-function-d3087698-fc15-4a15-9631-12575cf29926. Case-sensitive comparison.
- Einstein Discovery REST API Developer Guide (Spring '26), local corpus `knowledge/imports/bi-dev-guide-rest-sdd.md`. Org and Object Identifiers (15-character case-sensitive Ids, 18-character case-insensitive Ids).

Listed in the original version and not re-read:

- Salesforce Architects, Well-Architected Framework: https://architect.salesforce.com/design/architecture-framework/well-architected (HTTP 404 on 2026-10-03)
- Salesforce Help, Reporting & Dashboards: https://help.salesforce.com/s/articleView?id=sf.reports_dashboards.htm (Salesforce Help does not fetch).
