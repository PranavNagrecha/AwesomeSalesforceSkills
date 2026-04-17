# /audit-list-views — LEGACY ALIAS (Wave 3b-2)

> **Deprecation notice:** this command is now an alias. It invokes
> [`audit-router`](../agents/audit-router/AGENT.md) with
> `--domain=list_view_search_layout` and emits this deprecation notice.
> Switch to `/audit-router` at your convenience; the alias ships until the
> removal window declared in `docs/MIGRATION.md` (Wave 7).

## Canonical form

```
/audit-router --domain list_view_search_layout --target-org <alias> [--object-scope <list>]
```

## Alias behavior

`/audit-list-views <args>` is equivalent to `/audit-router --domain list_view_search_layout <args>`.

Rule table preserved in [`classifiers/list_view_search_layout.md`](../agents/_shared/harnesses/audit_harness/classifiers/list_view_search_layout.md).

## See also

- [`/audit-router`](./audit-router.md) — canonical router entry point
- [`docs/MIGRATION.md`](../docs/MIGRATION.md) — removal timeline (authored in Wave 7)
