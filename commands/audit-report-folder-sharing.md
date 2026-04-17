# /audit-report-folder-sharing — LEGACY ALIAS (Wave 3b-2)

> **Deprecation notice:** this command is now an alias. It invokes
> [`audit-router`](../agents/audit-router/AGENT.md) with
> `--domain=reports_dashboards_folder_sharing` and emits this deprecation
> notice. Distinct from `/audit-reports` (which audits content quality);
> this alias audits the sharing layer. Switch to `/audit-router` at your
> convenience; the alias ships until the removal window declared in
> `docs/MIGRATION.md` (Wave 7).

## Canonical form

```
/audit-router --domain reports_dashboards_folder_sharing --target-org <alias>
```

## Alias behavior

`/audit-report-folder-sharing <args>` is equivalent to `/audit-router --domain reports_dashboards_folder_sharing <args>`.

Rule table preserved in [`classifiers/reports_dashboards_folder_sharing.md`](../agents/_shared/harnesses/audit_harness/classifiers/reports_dashboards_folder_sharing.md).

## See also

- [`/audit-router`](./audit-router.md) — canonical router entry point
- [`/audit-reports`](./audit-reports.md) — content-quality sibling (different `--domain`)
- [`docs/MIGRATION.md`](../docs/MIGRATION.md) — removal timeline (authored in Wave 7)
