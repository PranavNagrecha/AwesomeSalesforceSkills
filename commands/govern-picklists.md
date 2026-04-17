# /govern-picklists — LEGACY ALIAS (Wave 3b-1)

> **Deprecation notice:** this command is now an alias. It invokes the
> [`audit-router`](../agents/audit-router/AGENT.md) with `--domain=picklist`
> and emits this deprecation notice. Switch to the canonical `/audit-router`
> form at your convenience; the alias ships until the removal window
> declared in `docs/MIGRATION.md` (Wave 7).

## Canonical form

```
/audit-router --domain picklist --scope <object:<Name>|org> --target-org <alias>
```

## Alias behavior

Running `/govern-picklists <args>` is equivalent to:

```
/audit-router --domain picklist <args>
```

The picklist-specific rule table (GVS adoption, restricted-flag, inactive-
value drift, translation coverage, dependent-picklist chains, integration-
usage heuristic) is preserved verbatim in
[`classifiers/picklist.md`](../agents/_shared/harnesses/audit_harness/classifiers/picklist.md).

## Why the change

Wave 3b-1 of the redesign consolidated 5 auditors into one router.
See [`agents/_shared/harnesses/audit_harness/README.md`](../agents/_shared/harnesses/audit_harness/README.md)
for the rationale.

## See also

- [`/audit-router`](./audit-router.md) — canonical router entry point
- [`agents/audit-router/AGENT.md`](../agents/audit-router/AGENT.md) — router contract
- [`docs/MIGRATION.md`](../docs/MIGRATION.md) — removal timeline (authored in Wave 7)
