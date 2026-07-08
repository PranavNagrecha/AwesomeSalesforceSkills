---
name: agentforce-grid
description: "Use when designing or reasoning about an Agentforce Grid worksheet — the spreadsheet-like Agentforce workspace where rows are jobs and columns are sequential Data / AI / Action steps that process left to right — to run bulk record updates, generate insights, or test multi-turn AI conversations over CRM or Data Cloud (Data 360) data without Apex or Flow. Trigger keywords: Agentforce Grid, workbook, worksheet, grid column, data column, AI column, action column, bulk AI update, Flex Credits per row, metered compute. NOT for building the agent, its topics, or its actions themselves (use agentforce/* action and topic skills), NOT for single-record prompt design (use the prompt-builder skills), NOT for deployable metadata/Apex (Grid is a no-code Studio tool, not a metadata type), and NOT for AI governance/ethics policy (use admin/ai-ethics-and-governance-requirements)."
category: agentforce
salesforce-version: "Winter '26+"
well-architected-pillars:
  - Operational Excellence
  - Security
  - Reliability
triggers:
  - "bulk-update thousands of Account records with AI-generated summaries in a spreadsheet-style workspace"
  - "chaining a prompt template output into an Update Record action for every row in Agentforce"
  - "generating insights over CRM or Data Cloud data without writing Apex or a Flow"
  - "testing a multi-turn Agentforce conversation across many rows at once"
  - "estimating Flex Credits before running a bulk AI operation in Agentforce Grid"
tags:
  - agentforce-grid
  - agentforce
  - workbook-worksheet
  - bulk-ai
  - flex-credits
inputs:
  - "The bulk goal: bulk record update, insight generation, or multi-turn conversation test"
  - "The source records (a standard Salesforce object or a Data Cloud / Data 360 data model object) and any row filter"
  - "The AI step(s): a prompt template or a direct 'Use AI' instruction plus the model to run"
  - "The write-back target (object + field) if results are pushed back to Salesforce"
outputs:
  - "A worksheet design: ordered Data → AI → Action columns with left-to-right dependencies"
  - "A column-by-column plan mapping each step to its inputs, references, and run-for-each-row behavior"
  - "A Flex Credit / metering estimate reviewed before running the operation at scale"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-07
runtime_orphan: true
runtime_orphan_reason: "No current runtime agent authors or reviews Agentforce Grid worksheets; Grid is a no-code, spreadsheet-style bulk AI/data-ops tool in Agentforce Studio operated directly by admins/analysts, not an artifact any of the 47 runtime agents scaffold or audit."
---

# Agentforce Grid

This skill activates when a practitioner wants to move data and AI work in **bulk** through Agentforce Grid — a spreadsheet-like interface for chaining together CRM data, AI prompts, actions, and agents. It covers how a worksheet is structured (rows as jobs, columns as sequential Data / AI / Action steps), how columns reference each other left to right, and the metering/Flex-Credit considerations that make bulk runs a cost decision, not just a design one.

> **Maturity caveat.** Agentforce Grid was introduced in the Winter '26 release and its setup documentation is explicitly labeled **Beta** ("Set Up Agentforce Grid (Beta)"). Do not describe it as Generally Available; preserve the Beta caveat in any guidance you produce.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm Grid fits the job.** Grid is for *bulk* work — running the same chain of steps across many records (rows). For a single-record prompt or one interactive agent turn, use the prompt-builder / agent surfaces, not a worksheet.
- **Know the data source.** A worksheet's data columns query **standard Salesforce objects or Data Cloud (Data 360) data model objects**. Confirm the object and the row filter up front; the number of rows is the number of jobs, and every downstream AI/action column runs per row.
- **Treat it as metered.** Agentforce Grid usage is metered to account for the required compute resources, and it is metered **regardless of the AI lifecycle phase** in which it's used (test, build, or scale). Estimate Flex Credits before running a wide operation, not after.
- **Respect the running user's access.** Data columns read live CRM/Data Cloud data and action columns write back to Salesforce fields under the operating user's permissions — CRUD/FLS and sharing still apply.

---

## Core Concepts

### Workbooks, worksheets, rows, and columns

Grid borrows the spreadsheet model but reimagines it for AI. Work is organized into **workbooks and worksheets** — "but reimagined for AI, with rows representing jobs while columns function as dynamic, sequential actions." A worksheet is the unit you build and run; a **Grid Worksheet is a distinct creatable artifact** within a Grid ("Create a Grid Worksheet").

- **Rows = jobs.** Each row is one record to process (e.g., one Account). The row count is your workload size.
- **Columns = sequential actions.** Columns execute **left to right**. A column can reference the output of columns to its left (via the `@` picker), so the worksheet is a left-to-right pipeline, not a free grid of independent cells. A column that runs per record is marked **Run For Each Row**.

### The three column types

Columns come in three kinds, chained in order:

- **Data columns** — import/query the source. They "query standard Salesforce objects or Data Cloud data model objects." In the builder this is the *Import Salesforce* path: select an object, choose fields, apply a filter, and cap rows with **Max Results**. This is almost always the leftmost column, because everything downstream reads from it.
- **AI columns** — a specialized action column that generates LLM content or runs agents. Two modes:
  - **Prompt Template** — run an existing prompt template (e.g., an "Account Summary" template) against an upstream column; output can be inspected as structured JSON in the Output Preview.
  - **Use AI** — give a direct LLM instruction and pick the model (e.g., convert an HTML field to Markdown). You choose the model that runs the transformation.
- **Action columns** — calculate formulas and update records. The **Update Record** action writes a processed value back to a Salesforce field (e.g., writing the generated Markdown into `Account.Description`).

### Left-to-right dependency ordering

Because columns process left to right and reference earlier columns, **order is the contract**. A data column feeds an AI column, whose output feeds another AI column or an action column that writes it back. An AI or action column can only consume columns positioned to its left — there is no way to reference a column that hasn't run yet.

### Metering and Flex Credits

Grid runs consume metered compute. "Testing through Agentforce Grid is metered to account for required compute resources," and that metering applies across the whole AI lifecycle, not just testing — "Agentforce Grid usage is metered regardless of the AI lifecycle phase in which it's used." Usage draws on **Flex Credits**, and a **Billing Calculator** estimates the credits-per-row cost before you run. Because every AI/action column runs once per row, cost scales with (rows × AI/action columns) — a small unit cost multiplied across a wide worksheet.

---

## Common Patterns

### Bulk enrichment / clean-up (Data → AI → Action)

**When to use:** you need to transform or summarize a field across many records and write the result back — e.g., convert stored HTML descriptions to Markdown, or generate a one-line summary per Account.

**How it works:** column 1 is a data column importing the object and fields (with a filter and Max Results). Column 2 is an AI column (Prompt Template or Use AI) referencing column 1's field. Column 3 is an Action column (Update Record) that writes column 2's output back to the target field. Preview a few rows before running the full set.

**Why not the alternative:** doing this in Apex or Flow means writing, testing, and deploying code for a one-off bulk operation; Grid keeps it no-code and inspectable row by row — but it is metered, so weigh Flex Credits against the effort saved.

### Insight generation (Data → AI, no write-back)

**When to use:** you want AI-generated insights across records for review, without mutating CRM data.

**How it works:** a data column plus one or more AI columns; stop there — no Update Record column. Read results in the Output Preview (JSON view available). This keeps the run read-only.

**Why not the alternative:** adding an action column when you only need to *look* at results writes data you didn't intend to change and spends credits on writes you don't need.

### Multi-turn conversation testing (bulk)

**When to use:** you want to test how an agent responds across many scenarios/rows at once, rather than one chat at a time.

**How it works:** rows carry the scenario inputs; AI columns run the agent/prompt per row so you can compare outputs side by side. Because this is still metered, treat a broad test run as a cost decision.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Same transform across many records, write results back | Data → AI → Action (Update Record) worksheet | Grid chains steps per row without code |
| You only need to *review* AI output, not change data | Data → AI columns, no action column | Avoids unintended writes and write-side credits |
| Source is Data Cloud / Data 360 data | Data column against a data model object | Grid data columns query DMOs as well as standard objects |
| One record or one interactive turn | Prompt builder / agent surface, not Grid | Grid's value is bulk (rows = jobs); a single row wastes the model |
| Transform needs a reusable, governed prompt | AI column in **Prompt Template** mode | Reuses an existing template instead of ad-hoc instructions |
| Quick, one-off transformation | AI column in **Use AI** mode with a chosen model | Direct instruction is faster than authoring a template |
| Deployable, repeatable production automation | Flow or Apex, not Grid | Grid is a no-code Studio tool, not a deployable metadata type |
| Run would touch a very large row set | Estimate Flex Credits first, narrow the filter | Cost scales with rows × AI/action columns; metered every phase |

---

## Recommended Workflow

Step-by-step instructions for a practitioner working in Agentforce Grid:

1. **Frame the bulk goal** — decide whether the run is a bulk update, insight generation, or a multi-turn test, and confirm Grid (not a single-record surface) is the right tool.
2. **Create the worksheet and its data column** — create a Grid worksheet, add a data column importing the source object (or Data Cloud DMO), select only the fields you need, apply a row filter, and set **Max Results** to bound the job count.
3. **Add the AI column(s)** — choose Prompt Template (reusable) or Use AI (direct instruction + model), and reference the upstream data column with the `@` picker so it runs for each row.
4. **Add the action column if writing back** — add an Update Record column that maps the AI column's output to the target object/field; omit it entirely for read-only insight runs.
5. **Estimate cost and preview** — review the Flex Credit / Billing Calculator estimate for the row count, then preview a few rows (inspect JSON output) before committing.
6. **Run and verify** — run the worksheet, confirm write-backs landed on the intended field, and spot-check for FLS/sharing gaps or truncated/incorrect AI output.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The task is genuinely bulk (multiple rows/jobs) — a single-record job doesn't belong in Grid
- [ ] Columns are ordered left to right; every `@` reference points to a column to its left
- [ ] The leftmost column is a data column (standard object or Data Cloud DMO) with a row filter and Max Results
- [ ] AI columns declare a mode (Prompt Template with a template, or Use AI with a chosen model)
- [ ] Read-only insight runs have **no** Update Record column; write-backs map to the correct object/field
- [ ] A Flex Credit / Billing Calculator estimate was reviewed for the actual row count before running
- [ ] The operating user's CRUD/FLS/sharing covers every field read and every field written
- [ ] Guidance preserves the **Beta** caveat and does not claim GA

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Cost scales with rows × columns** — every AI and action column runs once per row, so a modest per-row credit cost multiplies fast across a wide worksheet on a large row set. Estimate before running, and bound rows with Max Results and a filter.
2. **Metered in every phase, not just "test"** — it's tempting to assume experimentation is free. Agentforce Grid usage is metered regardless of the AI lifecycle phase (test, build, or scale); a broad exploratory run spends Flex Credits.
3. **Left-to-right ordering is the contract** — a column can only reference outputs of columns to its left. Reordering or inserting a column can silently break a downstream reference; validate the dependency chain after any edit.
4. **Action columns mutate live data** — an Update Record column writes to real Salesforce fields under the running user's permissions. A wrong field mapping or an over-broad filter can overwrite production data at scale; preview first.
5. **Beta surface** — Grid's setup is documented as Beta and was introduced in Winter '26; behavior, limits, and UI can change. Don't hard-code assumptions or promise GA-level stability.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Worksheet design (`templates/grid-worksheet-spec.example.json`) | A JSON plan of the ordered Data / AI / Action columns, their references, and metering acknowledgement — lintable with the checker script |
| `templates/agentforce-grid-template.md` | A fill-in planning worksheet for scoping a Grid run before building it |
| `scripts/check_agentforce_grid.py` | Stdlib linter that validates a worksheet spec: known column types, left-to-right references, write-back back-references, and a metering acknowledgement |

---

## Related Skills

- `agentforce/agentforce-custom-lightning-types` — customize the *UI* of an agent action's Apex input/output; unrelated to Grid's bulk-ops workspace but part of the same Agentforce surface.
- `admin/ai-ethics-and-governance-requirements` — the governance/ethics policy layer for AI usage; Grid is the operational tool, this is the guardrail.
- `data/data-cloud-data-model-objects` — modeling the Data Cloud / Data 360 data model objects that a Grid data column can query.
