# /audit-approvals — LEGACY ALIAS (Wave 3b-1)

> **Deprecation notice:** this command is now an alias. It invokes the
> [`audit-router`](../agents/audit-router/AGENT.md) with
> `--domain=approval_process` and emits this deprecation notice. Switch to
> the canonical `/audit-router` form at your convenience; the alias ships
> until the removal window declared in `docs/MIGRATION.md` (Wave 7).

## Canonical form

```
/audit-router --domain approval_process --audit-scope <org|object:<Name>|process:<Name>> --target-org <alias>
```

## Alias behavior

Running `/audit-approvals <args>` is equivalent to:

```
/audit-router --domain approval_process <args>
```

The approval-specific rule table (broken-reference checks, concurrent-
automation conflicts, stale in-flight detection, migration-fitness
verdicts) is preserved verbatim in
[`classifiers/approval_process.md`](../agents/_shared/harnesses/audit_harness/classifiers/approval_process.md).

`migrate_to_orchestrator` verdicts route to Wave-3a's
[`/migrate-automation --source-type approval_process`](./automation-migration-router.md).

## Why the change

Wave 3b-1 of the redesign consolidated 5 auditors into one router.
See [`agents/_shared/harnesses/audit_harness/README.md`](../agents/_shared/harnesses/audit_harness/README.md)
for the rationale.

## See also

- [`/audit-router`](./audit-router.md) — canonical router entry point
- [`agents/audit-router/AGENT.md`](../agents/audit-router/AGENT.md) — router contract
- [`docs/MIGRATION.md`](../docs/MIGRATION.md) — removal timeline (authored in Wave 7)
