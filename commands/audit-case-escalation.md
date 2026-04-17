# /audit-case-escalation — LEGACY ALIAS (Wave 3b-2)

> **Deprecation notice:** this command is now an alias. It invokes
> [`audit-router`](../agents/audit-router/AGENT.md) with
> `--domain=case_escalation` and emits this deprecation notice. Switch to
> `/audit-router` at your convenience; the alias ships until the removal
> window declared in `docs/MIGRATION.md` (Wave 7).

## Canonical form

```
/audit-router --domain case_escalation --target-org <alias>
```

## Alias behavior

`/audit-case-escalation <args>` is equivalent to `/audit-router --domain case_escalation <args>`.

Rule table preserved in [`classifiers/case_escalation.md`](../agents/_shared/harnesses/audit_harness/classifiers/case_escalation.md).

## See also

- [`/audit-router`](./audit-router.md) — canonical router entry point
- [`docs/MIGRATION.md`](../docs/MIGRATION.md) — removal timeline (authored in Wave 7)
