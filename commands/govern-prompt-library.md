# /govern-prompt-library — LEGACY ALIAS (Wave 3b-2)

> **Deprecation notice:** this command is now an alias. It invokes
> [`audit-router`](../agents/audit-router/AGENT.md) with
> `--domain=prompt_library` and emits this deprecation notice. Switch to
> `/audit-router` at your convenience; the alias ships until the removal
> window declared in `docs/MIGRATION.md` (Wave 7).

## Canonical form

```
/audit-router --domain prompt_library --target-org <alias> [--scope <filter>]
```

## Alias behavior

`/govern-prompt-library <args>` is equivalent to `/audit-router --domain prompt_library <args>`.

Rule table preserved in [`classifiers/prompt_library.md`](../agents/_shared/harnesses/audit_harness/classifiers/prompt_library.md).

## See also

- [`/audit-router`](./audit-router.md) — canonical router entry point
- [`docs/MIGRATION.md`](../docs/MIGRATION.md) — removal timeline (authored in Wave 7)
