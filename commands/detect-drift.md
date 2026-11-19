# /detect-drift — LEGACY ALIAS (Wave 3b-2)

> **Deprecation notice:** this command is now an alias. It invokes
> [`audit-router`](../agents/audit-router/AGENT.md) with `--domain=org_drift`
> and emits this deprecation notice. Switch to `/audit-router` at your
> convenience. The alias still ships (redirect table: `agents/_shared/RUNTIME_VS_BUILD.md`).

## Canonical form

```
/audit-router --domain org_drift --target-org <alias> [--scope <apex|flow|integration|security|all>] [--max-findings N]
```

## Alias behavior

`/detect-drift <args>` is equivalent to `/audit-router --domain org_drift <args>`.

Rule table preserved in [`classifiers/org_drift.md`](../agents/_shared/harnesses/audit_harness/classifiers/org_drift.md).

## See also

- [`/audit-router`](./audit-router.md) — canonical router entry point
- [`agents/_shared/RUNTIME_VS_BUILD.md`](../agents/_shared/RUNTIME_VS_BUILD.md#deprecated-slash-command-redirects) — deprecated-command redirect table
