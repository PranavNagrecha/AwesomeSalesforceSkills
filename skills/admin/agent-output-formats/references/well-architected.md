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

- Salesforce Architects — Well-Architected Framework: https://architect.salesforce.com/design/architecture-framework/well-architected
- Pandoc — Universal document converter: https://pandoc.org/MANUAL.html
- jq — Command-line JSON processor: https://jqlang.github.io/jq/manual/
- Salesforce Help — Reporting & Dashboards: https://help.salesforce.com/s/articleView?id=sf.reports_dashboards.htm
