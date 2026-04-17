# /audit-identity-and-session — LEGACY ALIAS (Wave 3b-2)

> **Deprecation notice:** this command is now an alias. It invokes
> [`audit-router`](../agents/audit-router/AGENT.md) with
> `--domain=my_domain_session_security` and emits this deprecation notice.
> Switch to `/audit-router` at your convenience; the alias ships until the
> removal window declared in `docs/MIGRATION.md` (Wave 7).

## Canonical form

```
/audit-router --domain my_domain_session_security --target-org <alias> [--focus <area>] [--benchmark baseline|high-trust]
```

## Alias behavior

`/audit-identity-and-session <args>` is equivalent to `/audit-router --domain my_domain_session_security <args>`.

Rule table preserved in [`classifiers/my_domain_session_security.md`](../agents/_shared/harnesses/audit_harness/classifiers/my_domain_session_security.md).

## See also

- [`/audit-router`](./audit-router.md) — canonical router entry point
- [`docs/MIGRATION.md`](../docs/MIGRATION.md) — removal timeline (authored in Wave 7)
