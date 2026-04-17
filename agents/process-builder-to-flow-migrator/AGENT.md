---
id: process-builder-to-flow-migrator
class: runtime
version: 1.1.0
status: deprecated
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-17
deprecated_in_favor_of: automation-migration-router
---
# Process Builder → Flow Migrator — DEPRECATED (Wave 3a)

Replaced by [`automation-migration-router`](../automation-migration-router/AGENT.md) with `--source-type=process_builder`.

## Why this changed

Wave 3a consolidated the four automation migrators — this one,
`workflow-rule-to-flow-migrator`, `approval-to-flow-orchestrator-migrator`,
and `workflow-and-pb-migrator` — into one router with a per-source-type
decision table. See
[`agents/_shared/harnesses/migration_router/README.md`](../_shared/harnesses/migration_router/README.md)
for the rationale.

## What replaces this agent

Run the router:

```
/migrate-automation --source-type process_builder --object <ApiName> --target-org <alias>
```

Legacy alias: `/migrate-pb-to-flow` still works and auto-invokes the router
with `source_type=process_builder` plus a one-line deprecation notice.
Aliases ship until the removal window declared in `docs/MIGRATION.md`
(Wave 7).

The PB-specific classification table (Criteria node → Decision, Update
Records → before-save vs after-save, Launch a Flow → Subflow, etc.) is
preserved verbatim in the router's
[`decision_table.md`](../_shared/harnesses/migration_router/decision_table.md)
under the `process_builder` row.

## Removal timeline

This stub stays in the repo for two minor versions after the Wave-3a
commit. After that it is removed; the `docs/MIGRATION.md` table (Wave 7)
records the mapping permanently.

## Plan

Deprecated — no longer executable. Route to the router.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
