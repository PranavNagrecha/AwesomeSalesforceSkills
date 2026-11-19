# /audit-sharing — LEGACY ALIAS (Wave 3b-2)

> **Deprecation notice:** this command is now an alias. It invokes
> [`audit-router`](../agents/audit-router/AGENT.md) with `--domain=sharing`
> and emits this deprecation notice. Switch to `/audit-router` at your
> convenience. The alias still ships (redirect table: `agents/_shared/RUNTIME_VS_BUILD.md`).

## Canonical form

```
/audit-router --domain sharing --scope <object:<Name>|org> --target-org <alias>
```

## Alias behavior

`/audit-sharing <args>` is equivalent to `/audit-router --domain sharing <args>`.

Rule table preserved in [`classifiers/sharing.md`](../agents/_shared/harnesses/audit_harness/classifiers/sharing.md).

## See also

- [`/audit-router`](./audit-router.md) — canonical router entry point
- [`agents/_shared/RUNTIME_VS_BUILD.md`](../agents/_shared/RUNTIME_VS_BUILD.md#deprecated-slash-command-redirects) — deprecated-command redirect table
