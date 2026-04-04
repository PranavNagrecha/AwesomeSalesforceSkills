---
name: data-import-and-management
description: "Use when planning, reviewing, or troubleshooting Salesforce data imports, migrations, and bulk updates. Triggers: 'Data Loader', 'Data Import Wizard', 'Bulk API', 'upsert', 'cutover', 'load failed', 'reconcile data'. NOT for ongoing integration architecture - use integration/ skills for that."
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
inputs: ["source data files", "load sequence", "automation constraints"]
outputs: ["load plan", "data load findings", "reconciliation checklist"]
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
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

| Scenario | Best Tool | Why |
|----------|-----------|-----|
| One-time admin import under 50,000 rows with simple field mapping | Data Import Wizard | Fastest option for low-volume, low-complexity work |
| Recurring admin load or large CSV updates | Data Loader | Handles more volume, supports update/upsert/delete, and gives error files |
| Millions of records, programmatic control, or overnight cutover | Bulk API / Bulk API 2.0 | Built for high-volume async processing |
| Multi-system transformation, survivorship logic, or complex enrichment | ETL platform | Transformation belongs outside manual CSV tooling |

**Rule:** If the data needs transformation, deduplication, or cross-system orchestration before import, stop pretending CSV mapping is enough.

## Load Order and Safeguards

Always design around these:

- **Parent before child**: Accounts before Contacts, Products before PricebookEntries, Users/Roles before ownership changes.
- **External IDs first**: Upsert on stable keys, not labels that users can edit.
- **Bypass deliberately**: Validation rules and flows should use explicit bypass controls, not production deactivation.
- **Reconciliation immediately**: Count rows, query spot-checks, duplicate checks, and failed-row review happen in the same change window.
- **Chunk for recovery**: Ten batches of 50k are recoverable. One opaque mega-load is not.


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Salesforce-Specific Gotchas

- **Data Import Wizard is not a migration tool**: It tops out around 50,000 records and gives you little control over retries, deletes, or complex relationships.
- **Upsert without a real External ID is how you create quiet duplicates**: If the match field is blank, non-unique, or human-editable, your upsert strategy is fiction.
- **Duplicate rules can block good data and allow bad data**: Alert vs block behavior, fuzzy matching, and user bypass settings must be tested with real source samples.
- **Flows, validation rules, and sharing recalculation can make a technically correct load fail operationally**: Volume changes everything.
- **Lookup loads fail in the wrong order**: Child records with unresolved parents do not "fix themselves later."
- **Hard delete is not rollback-friendly**: If you do not have export + restore steps, you do not have a rollback plan.

## Proactive Triggers

Surface these WITHOUT being asked:
- **No External ID or stable source key defined** -> Flag as Critical. The load is not safely repeatable.
- **Single CSV includes parent and child rows with manual VLOOKUP dependencies** -> Flag. That is fragile cutover design.
- **Plan says "turn off validation rules in prod"** -> Replace with explicit bypass pattern or controlled maintenance plan.
- **Duplicate rules were never tested with source data** -> Flag. Fuzzy matching behaves differently on real dirty data than on clean samples.
- **Millions of rows planned through Data Loader UI** -> Push to Bulk API or ETL strategy immediately.

## Output Artifacts

| When you ask for... | You get... |
|---------------------|------------|
| Tool recommendation | Data Import Wizard vs Data Loader vs Bulk API choice with rationale |
| Migration plan review | Risks, missing controls, load order, rollback gaps |
| Cutover runbook | Step-by-step execution plan with reconciliation checkpoints |
| Load failure triage | Root-cause path by error class with next corrective action |

## Related Skills

- **admin/duplicate-management**: Use when matching rules, duplicate rules, or survivorship design is the main problem. NOT for choosing load tooling or sequencing.
- **admin/validation-rules**: Use when validation logic or bypass design is blocking the load. NOT for end-to-end migration planning.
- **admin/change-management-and-deployment**: Use when the data load is coupled to a metadata release or rollback window. NOT for CSV-level field mapping and reconciliation.
