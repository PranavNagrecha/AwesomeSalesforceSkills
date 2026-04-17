# /audit-sharing — LEGACY ALIAS (Wave 3b-2)

> **Deprecation notice:** this command is now an alias. It invokes
> [`audit-router`](../agents/audit-router/AGENT.md) with `--domain=sharing`
> and emits this deprecation notice. Switch to `/audit-router` at your
> convenience; the alias ships until the removal window declared in
> `docs/MIGRATION.md` (Wave 7).

## Canonical form

```
/audit-router --domain sharing --scope <object:<Name>|org> --target-org <alias>
```

## Alias behavior

`/audit-sharing <args>` is equivalent to `/audit-router --domain sharing <args>`.

Rule table preserved in [`classifiers/sharing.md`](../agents/_shared/harnesses/audit_harness/classifiers/sharing.md).

## See also

- [`/audit-router`](./audit-router.md) — canonical router entry point
- [`docs/MIGRATION.md`](../docs/MIGRATION.md) — removal timeline (authored in Wave 7)
