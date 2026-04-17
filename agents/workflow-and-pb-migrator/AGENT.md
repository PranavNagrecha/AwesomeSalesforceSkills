---
id: workflow-and-pb-migrator
class: runtime
version: 1.2.0
status: deprecated
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-17
deprecated_in_favor_of: automation-migration-router
---
# Workflow & Process Builder Migrator — DEPRECATED (Wave 3a)

Replaced by [`automation-migration-router`](../automation-migration-router/AGENT.md) with `--source-type=auto`.

## History

This agent was deprecated pre-Wave-3a in favor of the split
`workflow-rule-to-flow-migrator` and `process-builder-to-flow-migrator`
pair. Wave 3a consolidates all four back into one router with a
per-source-type decision table. The union-dispatch semantics this agent
originally offered are preserved as `source_type=auto`, which runs the
`wf_rule` and `process_builder` dispatches back-to-back against the same
object and flags any WFR + PB pair hitting the same action type on the
same field.

## What replaces this agent

Run the router:

```
/migrate-automation --source-type auto --object <ApiName> --target-org <alias>
```

Legacy alias: `/migrate-workflow-pb` still works and auto-invokes the
router with `source_type=auto` plus a one-line deprecation notice. Aliases
ship until the removal window declared in `docs/MIGRATION.md` (Wave 7).

See
[`agents/_shared/harnesses/migration_router/decision_table.md`](../_shared/harnesses/migration_router/decision_table.md)
for how `auto` dispatches the union and surfaces WFR↔PB conflicts.

## Removal timeline

This stub stays in the repo for two minor versions after the Wave-3a
commit. After that it is removed; the `docs/MIGRATION.md` table (Wave 7)
records the mapping permanently.

## Plan

Deprecated — no longer executable. Route to the router.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
