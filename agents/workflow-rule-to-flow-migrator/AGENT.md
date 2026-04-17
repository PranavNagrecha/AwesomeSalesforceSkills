---
id: workflow-rule-to-flow-migrator
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
# Workflow Rule → Flow Migrator — DEPRECATED (Wave 3a)

Replaced by [`automation-migration-router`](../automation-migration-router/AGENT.md) with `--source-type=wf_rule`.

## Why this changed

Wave 3a of the redesign consolidated four automation migrators — this one,
`process-builder-to-flow-migrator`, `approval-to-flow-orchestrator-migrator`,
and `workflow-and-pb-migrator` — into one router. The four shared 80% of
their logic (inventory → classify → design → parallel-run → rollback); the
duplicated backbone made every edit cost four commits and drifted in small
ways across the quartet. The router centralizes the backbone in
[`agents/_shared/harnesses/migration_router/`](../_shared/harnesses/migration_router/README.md)
and dispatches on a single source-type decision table.

## What replaces this agent

Run the router:

```
/migrate-automation --source-type wf_rule --object <ApiName> --target-org <alias>
```

Legacy alias: `/migrate-wfr-to-flow` still works and auto-invokes the router
with `source_type=wf_rule` plus a one-line deprecation notice. Aliases ship
until the removal window declared in `docs/MIGRATION.md` (Wave 7).

The WFR-specific classification table (Field Update → before-save vs
after-save, Time Trigger → Scheduled Path, Outbound Message → refuse, etc.)
is preserved verbatim in the router's
[`decision_table.md`](../_shared/harnesses/migration_router/decision_table.md)
under the `wf_rule` row.

## Removal timeline

This stub stays in the repo for two minor versions after the Wave-3a commit
to keep the citation graph valid and preserve file history. After that it
is removed; the `docs/MIGRATION.md` table (Wave 7) records the mapping
permanently.

## Plan

Deprecated — no longer executable. Route to the router.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
