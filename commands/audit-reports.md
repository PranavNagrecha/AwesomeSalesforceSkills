# /audit-reports — LEGACY ALIAS (Wave 3b-1)

> **Deprecation notice:** this command is now an alias. It invokes the
> [`audit-router`](../agents/audit-router/AGENT.md) with
> `--domain=report_dashboard` and emits this deprecation notice. Switch to
> the canonical `/audit-router` form at your convenience; the alias ships
> until the removal window declared in `docs/MIGRATION.md` (Wave 7).

## Canonical form

```
/audit-router --domain report_dashboard --target-org <alias> [--folder-filter <FolderName>]
```

## Alias behavior

Running `/audit-reports <args>` is equivalent to:

```
/audit-router --domain report_dashboard <args>
```

The analytics rule table (stale reports, orphan folder owners, dashboard
running-user posture including Modify-All-Data, folder oversharing with
PII, tabular-over-limit, shadow copies, undocumented reports) is preserved
verbatim in
[`classifiers/report_dashboard.md`](../agents/_shared/harnesses/audit_harness/classifiers/report_dashboard.md).

## Why the change

Wave 3b-1 of the redesign consolidated 5 auditors into one router.
See [`agents/_shared/harnesses/audit_harness/README.md`](../agents/_shared/harnesses/audit_harness/README.md)
for the rationale.

## See also

- [`/audit-router`](./audit-router.md) — canonical router entry point
- [`agents/audit-router/AGENT.md`](../agents/audit-router/AGENT.md) — router contract
- [`docs/MIGRATION.md`](../docs/MIGRATION.md) — removal timeline (authored in Wave 7)
