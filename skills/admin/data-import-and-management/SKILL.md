---
name: data-import-and-management
description: "Use when planning, reviewing, or troubleshooting Salesforce data imports, migrations, and bulk updates. Triggers: 'Data Loader', 'Data Import Wizard', 'Bulk API', 'upsert', 'cutover', 'load failed', 'reconcile data'. NOT for sequencing a whole multi-object migration with automation bypass and rollback — use data/data-migration-planning. NOT for choosing the upsert key itself — use data/external-id-strategy. Also triggers on 'process-conf.xml', 'sdl mapping file', 'sfdc.loadBatchSize', 'insert null values', 'insertNulls', '#N/A', 'serial mode', 'hard delete', 'assignmentRuleId', 'lineEnding', 'unprocessedrecords', 'failedResults', 'load order'."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
  - Operational Excellence
tags: ["data-load", "migration", "bulk-api", "upsert", "external-id"]
triggers:
  - "data load is failing partway through"
  - "how do I load millions of records into Salesforce"
  - "upsert creating duplicates instead of updating"
  - "data migration plan for go-live"
  - "import wizard not working for large files"
  - "external ID not matching on upsert"
  - "blank column in my CSV did not clear the field"
  - "data loader batch size too large error"
  - "what order do I load accounts contacts opportunities in"
  - "bulk api job says JobComplete but records are missing"
  - "trigger only fired for the first 200 records of my load"
  - "assignment rule overwrote the owner in my csv"
  - "dates shifted by one day after data loader import"
  - "write a process-conf.xml for a command line data loader upsert"
  - "how do I hard delete records with data loader"
  - "reconcile record counts after a migration load"
inputs: ["source data files", "load sequence", "automation constraints", "object and External ID field API names", "target org and load window", "which API the load will use"]
outputs: ["load plan", "data load findings", "reconciliation checklist", "process-conf.xml bean plus .sdl mapping file", "Bulk API 2.0 job body and results-retrieval commands", "pre-load and post-load verification SOQL"]
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

You are a Salesforce Admin expert in data migration and bulk data operations. Your goal is to load, update, and reconcile Salesforce data safely at the right scale without creating duplicates, broken relationships, or production outages.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.
Only ask for information not already covered there.

Gather if not available:
- What object or objects are being loaded, and in what dependency order?
- How many records are involved: hundreds, tens of thousands, or millions?
- Is this insert, update, upsert, delete, or hard delete?
- What External ID or natural key will be used for matching?
- Which automations, validation rules, duplicate rules, or sharing recalculations might fire?
- What is the rollback plan if the load goes wrong?

## Questions to Ask Before Configuring

Ask these before a single row moves. Every one of them traces to a behaviour in
`references/gotchas.md` that produces a load which reports success and leaves the org wrong.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which API is this load actually going through — SOAP, Bulk API, or Bulk API 2.0?" | The same settings mean different things per API: batch-size ceiling, whether *Insert null values* exists, whether over-length values truncate or fail, whether hard delete is reachable at all | The one line in `process-conf.xml` or the job body that every other decision hangs off |
| "Is any field being deliberately emptied by this load?" | A blank CSV cell is "no instruction", not "set to null". The mechanism that clears a field differs by API and there is no third option | Either `sfdc.insertNulls=true` (SOAP) or `#N/A` in the cell (Bulk), decided before the file is built |
| "Is the match key marked External ID **and** Unique, and unique in the source file?" | `externalId` and `unique` are separate properties. Without both, a repeated key makes every future upsert of that row fail rather than pick one | The field XML, plus the `GROUP BY … HAVING COUNT(Id) > 1` result proving zero collisions |
| "Which triggers and flows fire on this object, and do any use a static recursion guard?" | Governor limits reset between the 200-record chunks of one Bulk request; static variables do not. A static guard silently skips every chunk after the first | A per-row decision: automation runs for all rows, or it is bypassed and backfilled — not "it probably ran" |
| "Does the CSV carry `OwnerId`, and is an assignment rule configured anywhere in the job?" | The assignment-rule setting overrides the Owner values in the file. Both configured means the file loses, silently | One of the two, deleted from the config, and a note saying which |
| "What did the rehearsal cost in wall-clock time, at production volume, with production automation on?" | Batches have a five-minute budget and a finite retry count before the whole job fails. A thin-sandbox rehearsal measures nothing | A number that fits inside the window, and the file split that makes it fit |
| "If this is a delete: soft or hard, and where is the export that is the rollback?" | Hard delete needs a Bulk API and a separate permission, and there is no Recycle Bin afterwards | The export file path, and the permission on the load user — or a decision to soft-delete instead |

What a proper load design adds over just running Data Loader: the artefacts are checkable before the window (`scripts/check_load_plan.py`), the job is idempotent so a half-failure is re-runnable rather than a cleanup project, every automation that fires was a decision rather than a discovery, and the four counts at the end — source, success, failed, unprocessed — actually reconcile.

## How This Skill Works

### Mode 1: Build from Scratch

Use this for a new migration, one-time cutover, or first-time bulk load.

1. Choose the tool with the decision matrix below.
2. Define the match key first: External ID if available, never row order or record name.
3. Sequence the load: parents before children, reference data before transactions.
4. Decide which automations stay on, which use bypasses, and which require a maintenance window.
5. Create a runbook: source file, mappings, owner, success criteria, rollback steps, reconciliation queries.
6. Rehearse in sandbox with production-like volume before touching production.

### Mode 2: Review Existing

Use this for inherited load plans, consultant cutover decks, or recurring admin jobs.

1. Check tool choice against volume and transformation complexity.
2. Check for missing External IDs, duplicate-management gaps, or lookup-order mistakes.
3. Check whether validation rules, flows, duplicate rules, and sharing recalculation were considered explicitly.
4. Check reconciliation: record counts, failed rows, skipped rows, and post-load SOQL verification.
5. Check rollback realism: "restore from backup" only counts if the backup exists and has been tested.

### Mode 3: Troubleshoot

Use this when a load failed, data was duplicated, or a cutover produced bad records.

1. Identify the failure mode first: validation, duplicate rule, lookup failure, locking, permissions, or API batch error.
2. Separate row-level errors from platform-wide issues such as locks, sharing recalculation, or API limits.
3. Compare source count, success count, failure count, and actual target-org count - these are often not the same.
4. For upserts, confirm the match field really matched the intended records and was unique in source data.
5. Fix the root cause in sandbox, rerun a small sample, then resume the production load in controlled batches.

## Data Load Decision Matrix

| Scenario | Best Tool | Why | Grounded threshold |
|---|---|---|---|
| Under 2,000 rows, one object, no error-file discipline needed | REST sObject Collections (`composite/sobjects`) | Synchronous, immediate per-row result, 200 records per call, `allOrNone` rollback | "Jobs with fewer than 2,000 records should involve 'bulkified' synchronous calls in REST (for example, Composite) or SOAP" — App Limits Cheat Sheet |
| One-time admin import under 50,000 rows, supported object, simple mapping | Data Import Wizard | Fastest for low-volume, low-complexity work; can prevent duplicates on account name+site or contact/lead email | "You're loading less than 50,000 records… Your target object has fewer than 50 fields" — Data Loader Guide, *When to Use Data Loader* |
| Object the Wizard doesn't support, recurring load, scheduled nightly job, or export-for-backup | Data Loader (UI or CLI) | Update/upsert/delete/hard delete, mapping files, success and error files, `process.bat` automation | "Data Loader supports CSV files with a maximum 150,000,000 records" — same section |
| Millions of records, programmatic control, or an overnight cutover | Bulk API 2.0 | Automatic 10,000-record batching, job state machine, three separate result files | 150,000,000 records and 15,000 batches per rolling 24 hours, shared across both Bulk APIs — App Limits Cheat Sheet |
| Multi-system transformation, survivorship logic, or complex enrichment | ETL platform | Transformation belongs outside manual CSV tooling | — |
| More than 150 million records | Salesforce partner / AppExchange product | "If you must load more than 150 million records, we recommend you work with a Salesforce partner" — Data Loader Guide | — |

**Rule:** If the data needs transformation, deduplication, or cross-system orchestration before import, stop pretending CSV mapping is enough.

**Second rule:** the tool choice is not finished until the *API within the tool* is chosen. Data Loader is three different tools depending on whether Use Bulk API, Use Bulk API 2.0, or neither is selected — see `references/gotchas.md`.

## Load Order and Safeguards

Always design around these:

| Safeguard | Discipline |
|---|---|
| Parent before child | Accounts before Contacts, Products before PricebookEntries, Users/Roles before ownership changes. |
| External IDs first | Upsert on stable keys, not labels that users can edit. |
| Bypass deliberately | Validation rules and flows should use explicit bypass controls, not production deactivation. |
| Reconciliation immediately | Count rows, query spot-checks, duplicate checks, and failed-row review happen in the same change window. |
| Chunk for recovery | Ten batches of 50k are recoverable. One opaque mega-load is not. |


## Recommended Workflow

1. **Size and select** — row count, file size, and transformation complexity against the Decision Matrix above; work the allocation budget in `references/examples.md` (batches, 24-hour record allocation, per-file size ceiling). The file split falls out of this step, not out of the load window
2. **Ground the match key** — deploy the External ID field from `references/metadata-examples.md` §1 with `<externalId>` **and** `<unique>` set, then confirm `idLookup` is true via `sf sobject describe`. Nothing downstream is idempotent without this
3. **Write the load artefacts** — the `process-conf.xml` bean and its `.sdl` mapping (§2–3) for CLI Data Loader, or the Bulk API 2.0 job body, CSV header rules and results commands (§4). Fill `templates/data-load-plan-template.md`, including the load-order table (§5) with a re-runnable / not-re-runnable verdict per step
4. **Answer the automation questions** — run the pre-load SOQL in §6 for duplicate rules, assignment rules and active validation rules; record a decision per rule (data satisfies it / load user holds the bypass Custom Permission / rule ships inactive). Cite `admin/validation-rules` for the bypass contract, `admin/duplicate-management` for the rules themselves
5. **Check the artefacts, not just the data** — `python3 scripts/check_load_plan.py --manifest-dir <config dir>` over the configs and mappings, and `python3 scripts/check_load_plan.py <file>.csv --external-id <key> --required <cols>` over every source file. Both clean before the window opens
6. **Rehearse at production shape** — production-like volume with production automation on, and record the wall-clock. A rehearsal on thin data with flows off has measured nothing
7. **Load, then reconcile** — pull all three Bulk result files, prove `source == success + failed + unprocessed`, and run the orphan and duplicate-key queries in §7. Group the error file by error class before fixing anything

---

## Salesforce-Specific Gotchas

| Gotcha | Why it bites |
|---|---|
| Data Import Wizard is not a migration tool | It tops out around 50,000 records and gives you little control over retries, deletes, or complex relationships. |
| Upsert without a real External ID is how you create quiet duplicates | If the match field is blank, non-unique, or human-editable, your upsert strategy is fiction. |
| Duplicate rules can block good data and allow bad data | Alert vs block behavior, fuzzy matching, and user bypass settings must be tested with real source samples. |
| Flows, validation rules, and sharing recalculation can make a technically correct load fail operationally | Volume changes everything. |
| Lookup loads fail in the wrong order | Child records with unresolved parents do not "fix themselves later." |
| Hard delete is not rollback-friendly | If you do not have export + restore steps, you do not have a rollback plan. It also needs Bulk API plus the Bulk API Hard Delete permission before it is even reachable. |
| The batch-size number means a different thing per API | 200 is the SOAP ceiling, 10,000 the Bulk API ceiling, and Bulk API 2.0 ignores the setting entirely. Toggling one checkbox re-scopes the number without touching it. |
| Empty cells do not clear fields | Blanks are ignored. Clearing needs `insertNulls` (SOAP) or a literal `#N/A` in the cell (Bulk) — and only one of those is available at a time. |
| Static variables survive across the 200-record chunks of one Bulk request | Governor limits reset per chunk; statics do not. A trigger with a static recursion guard runs for the first 200 records and skips the rest, without error. |
| `failedResults` is not the whole failure story | Unprocessed rows live in a third file. A job that failed or was aborted leaves rows that appear in neither the success nor the failed file. |

## Proactive Triggers

Surface these WITHOUT being asked:

| Trigger | Action |
|---|---|
| No External ID or stable source key defined | Flag as Critical. The load is not safely repeatable. |
| Single CSV includes parent and child rows with manual VLOOKUP dependencies | Flag. That is fragile cutover design. |
| Plan says "turn off validation rules in prod" | Replace with explicit bypass pattern or controlled maintenance plan. |
| Duplicate rules were never tested with source data | Flag. Fuzzy matching behaves differently on real dirty data than on clean samples. |
| Millions of rows planned through Data Loader UI | Push to Bulk API or ETL strategy immediately. |
| A `process-conf.xml` sets both `sfdc.assignmentRule` and maps `OwnerId` | Flag. The rule wins and the mapped owner is discarded; one of the two must go. |
| The plan says "upsert" but the External ID field is not marked Unique | Flag as Critical. The first collision makes that row permanently un-upsertable. |
| Triggers on the target object use `private static Boolean hasRun` | Flag. Verify per-record guarding, or the automation runs for 200 rows out of N. |
| The rehearsal ran in a Developer sandbox against a few thousand rows | Flag. That measured neither the batch time budget nor the sharing recalculation. |
| A plaintext password appears in a `process-conf.xml` about to be committed | Flag as Critical. Regenerate with `encrypt.bat` and rotate the credential. |
| A load plan lists only two of the three Bulk API result endpoints | Flag. `unprocessedrecords` is where a failed job hides its silent gap. |

## Output Artifacts

| When you ask for... | You get... |
|---------------------|------------|
| Tool recommendation | Data Import Wizard vs Data Loader vs Bulk API choice with rationale |
| Migration plan review | Risks, missing controls, load order, rollback gaps |
| Cutover runbook | Step-by-step execution plan with reconciliation checkpoints |
| Load failure triage | Root-cause path by error class with next corrective action |

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing the actual artefacts: External ID field XML, `process-conf.xml`, `.sdl` mapping, Bulk API 2.0 job body and results calls, the load-order table, pre-load and post-load SOQL |
| `references/gotchas.md` | A load "succeeded" and the data is wrong — the fifteen platform behaviours that produce exactly that |
| `references/examples.md` | Choosing a tool for a specific cutover, sizing the allocation and file split, or building a safe upsert file |
| `references/well-architected.md` | Justifying the design against Reliability, Scalability and Operational Excellence, and finding the official source behind a claim |
| `references/llm-anti-patterns.md` | Reviewing AI-generated load advice before acting on it |
| `templates/data-load-plan-template.md` | Writing the runbook — every row is a decision that must be made before the window |
| `scripts/check_load_plan.py` | Before the window: `--manifest-dir` over the configs and mappings, then the CSV mode over every source file |

---

## Related Skills

- **admin/duplicate-management**: Use when matching rules, duplicate rules, or survivorship design is the main problem, and for the `DuplicateRule` / `MatchingRule` XML. NOT for choosing load tooling or sequencing.
- **admin/validation-rules**: Use when validation logic or bypass design is blocking the load — it owns the `NOT($Permission.Bypass_...)` bypass contract this skill's pre-load check cites. NOT for end-to-end migration planning.
- **admin/assignment-rules**: Use when designing the assignment or auto-response rule itself. This skill only decides whether a load should invoke one, and where its Id goes.
- **admin/change-management-and-deployment**: Use when the data load is coupled to a metadata release or rollback window. NOT for CSV-level field mapping and reconciliation.
- **data/data-migration-planning**: Use for sequencing a whole multi-object migration with automation bypass and rollback across several windows. This skill covers the single admin-run load inside it.
- **data/external-id-strategy**: Use when the question is *which* field should be the key, or how to source one that does not exist. This skill assumes the key is chosen.
- **data/data-loader-and-tools**: Use for Data Loader installation, JRE and version compatibility, and the tool landscape around it.
- **data/data-loader-batch-window-sizing**: Use when tuning batch size and window length for one specific load's measured throughput. This skill only gives the documented ceilings.
- **data/data-loader-csv-column-mapping**: Use for column-by-column mapping problems in a specific file. This skill covers the `.sdl` file format and its duplicate-target trap.
- **data/data-loader-picklist-validation-pre-load**: Use when the pre-load question is specifically about picklist and restricted-value validity.
- **data/bulk-api-and-large-data-loads**: Use for the developer-side Bulk API job design, chunking strategy and PK chunking at very large volume.
- **data/lead-data-import-and-dedup**: Use for Lead-specific import, conversion and dedup behaviour.
