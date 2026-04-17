# /govern-field-history — LEGACY ALIAS (Wave 3b-2)

> **Deprecation notice:** this command is now an alias. It invokes
> [`audit-router`](../agents/audit-router/AGENT.md) with
> `--domain=field_audit_trail_history_tracking` and emits this deprecation
> notice. Switch to `/audit-router` at your convenience; the alias ships
> until the removal window declared in `docs/MIGRATION.md` (Wave 7).

## Canonical form

```
/audit-router --domain field_audit_trail_history_tracking --target-org <alias> [--regulated-profile <profile>]
```

## Alias behavior

`/govern-field-history <args>` is equivalent to `/audit-router --domain field_audit_trail_history_tracking <args>`.

Rule table preserved in [`classifiers/field_audit_trail_history_tracking.md`](../agents/_shared/harnesses/audit_harness/classifiers/field_audit_trail_history_tracking.md).

## See also

- [`/audit-router`](./audit-router.md) — canonical router entry point
- [`docs/MIGRATION.md`](../docs/MIGRATION.md) — removal timeline (authored in Wave 7)
