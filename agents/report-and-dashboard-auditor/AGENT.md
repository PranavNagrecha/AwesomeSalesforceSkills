---
id: report-and-dashboard-auditor
class: runtime
version: 1.1.0
status: deprecated
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-17
deprecated_in_favor_of: audit-router
---
# Report & Dashboard Auditor — DEPRECATED (Wave 3b-1)

Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=report_dashboard`.

## Why this changed

Wave 3b-1 consolidated 5 auditors into one router backed by the
[`audit_harness`](../_shared/harnesses/audit_harness/README.md). See the
router's README for the rationale and
[`classifiers/report_dashboard.md`](../_shared/harnesses/audit_harness/classifiers/report_dashboard.md)
for the per-domain rule table.

## What replaces this agent

Run the router:

```
/audit-router --domain report_dashboard --target-org <alias> [--folder-filter <FolderName>]
```

Legacy alias: `/audit-reports` invokes the router with
`--domain=report_dashboard` plus a one-line deprecation notice. Aliases
ship until the removal window declared in `docs/MIGRATION.md` (Wave 7).

The full analytics rule set (stale reports, orphan folder owners,
dashboard inactive running user, Modify-All-Data dashboard running user,
folder oversharing with PII columns, tabular-over-limit, no-filter-on-
high-volume-object, shadow copies, undocumented reports) is preserved
verbatim in the classifier. Every rule has a stable domain-scoped finding
code (`DASHBOARD_INACTIVE_RUNNING_USER`, `FOLDER_ALL_USERS_PII`,
`REPORT_STALE`, etc.).

## Removal timeline

This stub stays in the repo for two minor versions after the Wave-3b-1
commit. After that it is removed; the `docs/MIGRATION.md` table (Wave 7)
records the mapping permanently.

## Plan

Deprecated — no longer executable. Route to the router.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
