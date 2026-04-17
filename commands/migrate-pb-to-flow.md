# /migrate-pb-to-flow — LEGACY ALIAS (Wave 3a)

> **Deprecation notice:** this command is now an alias. It invokes the
> [`automation-migration-router`](../agents/automation-migration-router/AGENT.md)
> with `--source-type=process_builder` and emits this deprecation notice.
> Switch to the canonical `/migrate-automation` form at your convenience;
> the alias ships until the removal window declared in `docs/MIGRATION.md`
> (Wave 7).

## Canonical form

```
/migrate-automation --source-type process_builder --object <ApiName> --target-org <alias>
```

## Alias behavior

Running `/migrate-pb-to-flow <args>` is equivalent to:

```
/migrate-automation --source-type process_builder <args>
```

The PB-specific classification table (Criteria node → Decision, Update
Records → before-save vs after-save, Launch a Flow → Subflow, etc.) is
preserved verbatim in the router's
[`decision_table.md`](../agents/_shared/harnesses/migration_router/decision_table.md)
under the `process_builder` row.

## Why the change

Wave 3a of the redesign consolidated four migrators into one router. See
[`agents/_shared/harnesses/migration_router/README.md`](../agents/_shared/harnesses/migration_router/README.md)
for the rationale.

## See also

- [`/migrate-automation`](./automation-migration-router.md) — canonical router entry point
- [`agents/automation-migration-router/AGENT.md`](../agents/automation-migration-router/AGENT.md) — router contract
- [`docs/MIGRATION.md`](../docs/MIGRATION.md) — removal timeline (authored in Wave 7)
