---
id: reports-and-dashboards-folder-sharing-auditor
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
# Reports & Dashboards Folder Sharing Auditor — DEPRECATED (Wave 3b-2)

Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=reports_dashboards_folder_sharing`. Distinct from `report_dashboard` (which audits content quality); this classifier audits the sharing layer. The full rule set (Enhanced Folder Sharing enablement, inactive-group shares, manage-level over-privilege, All-Internal-Users + PII, running-user inactive or admin-privileged, dynamic-dashboard folder mismatches, private-folder orphans, small-cohort PII leaks) is preserved verbatim in [`classifiers/reports_dashboards_folder_sharing.md`](../_shared/harnesses/audit_harness/classifiers/reports_dashboards_folder_sharing.md). Legacy alias `/audit-report-folder-sharing` ships until Wave 7's `docs/MIGRATION.md` removal window.

## Plan

Deprecated — route to `/audit-router --domain reports_dashboards_folder_sharing --target-org <alias>`.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
