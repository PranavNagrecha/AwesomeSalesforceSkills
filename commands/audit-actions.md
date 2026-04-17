# /audit-actions — LEGACY ALIAS (Wave 3b-2)

> **Deprecation notice:** this command is now an alias for the AUDIT mode
> of the retired `quick-action-and-global-action-auditor`. It invokes
> [`audit-router`](../agents/audit-router/AGENT.md) with `--domain=quick_action`
> and emits this deprecation notice. The DESIGN mode migrates separately
> to Wave 3c's `designer_base` harness (as `action-designer`). Switch to
> `/audit-router` at your convenience; the alias ships until the removal
> window declared in `docs/MIGRATION.md` (Wave 7).

## Canonical form

```
/audit-router --domain quick_action --target-org <alias>
```

## Alias behavior

`/audit-actions <args>` is equivalent to `/audit-router --domain quick_action <args>`.

Rule table preserved in [`classifiers/quick_action.md`](../agents/_shared/harnesses/audit_harness/classifiers/quick_action.md).

## See also

- [`/audit-router`](./audit-router.md) — canonical router entry point
- [`docs/MIGRATION.md`](../docs/MIGRATION.md) — removal timeline (authored in Wave 7)
