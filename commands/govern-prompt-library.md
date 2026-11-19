# /govern-prompt-library — LEGACY ALIAS (Wave 3b-2)

> **Deprecation notice:** this command is now an alias. It invokes
> [`audit-router`](../agents/audit-router/AGENT.md) with
> `--domain=prompt_library` and emits this deprecation notice. Switch to
> `/audit-router` at your convenience. The alias still ships (redirect table: `agents/_shared/RUNTIME_VS_BUILD.md`).

## Canonical form

```
/audit-router --domain prompt_library --target-org <alias> [--scope <filter>]
```

## Alias behavior

`/govern-prompt-library <args>` is equivalent to `/audit-router --domain prompt_library <args>`.

Rule table preserved in [`classifiers/prompt_library.md`](../agents/_shared/harnesses/audit_harness/classifiers/prompt_library.md).

## See also

- [`/audit-router`](./audit-router.md) — canonical router entry point
- [`agents/_shared/RUNTIME_VS_BUILD.md`](../agents/_shared/RUNTIME_VS_BUILD.md#deprecated-slash-command-redirects) — deprecated-command redirect table
