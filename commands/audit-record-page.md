# /audit-record-page — LEGACY ALIAS (Wave 3b-2)

> **Deprecation notice:** this command is now an alias. It invokes
> [`audit-router`](../agents/audit-router/AGENT.md) with
> `--domain=lightning_record_page` and emits this deprecation notice.
> Switch to `/audit-router` at your convenience. The alias still ships (redirect table: `agents/_shared/RUNTIME_VS_BUILD.md`).

## Canonical form

```
/audit-router --domain lightning_record_page --object <ApiName> --target-org <alias>
```

## Alias behavior

`/audit-record-page <args>` is equivalent to `/audit-router --domain lightning_record_page <args>`.

Rule table preserved in [`classifiers/lightning_record_page.md`](../agents/_shared/harnesses/audit_harness/classifiers/lightning_record_page.md).

## See also

- [`/audit-router`](./audit-router.md) — canonical router entry point
- [`agents/_shared/RUNTIME_VS_BUILD.md`](../agents/_shared/RUNTIME_VS_BUILD.md#deprecated-slash-command-redirects) — deprecated-command redirect table
