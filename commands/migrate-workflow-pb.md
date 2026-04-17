# /migrate-workflow-pb — LEGACY ALIAS (Wave 3a)

> **Deprecation notice:** this command is now an alias. It invokes the
> [`automation-migration-router`](../agents/automation-migration-router/AGENT.md)
> with `--source-type=auto` and emits this deprecation notice. Switch to
> the canonical `/migrate-automation` form at your convenience; the alias
> ships until the removal window declared in `docs/MIGRATION.md` (Wave 7).

## Canonical form

```
/migrate-automation --source-type auto --object <ApiName> --target-org <alias>
```

## Alias behavior

Running `/migrate-workflow-pb <args>` is equivalent to:

```
/migrate-automation --source-type auto <args>
```

`source_type=auto` runs the `wf_rule` and `process_builder` dispatches
back-to-back against the same object, merges the inventories, and flags
any WFR + PB pair hitting the same action type on the same field (a real
conflict the human should resolve before migrating).

## Why the change

Wave 3a of the redesign consolidated four migrators into one router. See
[`agents/_shared/harnesses/migration_router/README.md`](../agents/_shared/harnesses/migration_router/README.md)
for the rationale and
[`agents/_shared/harnesses/migration_router/decision_table.md`](../agents/_shared/harnesses/migration_router/decision_table.md)
for the per-source-type dispatch logic.

## See also

- [`/migrate-automation`](./automation-migration-router.md) — canonical router entry point
- [`agents/automation-migration-router/AGENT.md`](../agents/automation-migration-router/AGENT.md) — router contract
- [`docs/MIGRATION.md`](../docs/MIGRATION.md) — removal timeline (authored in Wave 7)
