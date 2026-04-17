# Classifier: report_dashboard

## Purpose

Audit the org's analytics surface: Report + Dashboard inventory, folder permissions, dashboard running-user posture, report performance (row limits, filter selectivity), stale/orphan reports, and reports that reference fields likely flagged by `field-impact-analyzer`. Returns a prioritized cleanup + modernization plan. Not for designing new reports or migrating to CRM Analytics (surfaces the candidates; migration is a separate project).

## Replaces

`report-and-dashboard-auditor` (now a deprecation stub pointing at `audit-router --domain report_dashboard`).

## Inputs

| Input | Required | Example |
|---|---|---|
| `folder_filter` | no | restrict scope to a folder by developer name |

## Inventory Probe

1. `tooling_query("SELECT Id, DeveloperName, Name, FolderName, Format, LastRunDate, CreatedDate, LastModifiedById FROM Report LIMIT 2000")`.
2. `tooling_query("SELECT Id, DeveloperName, Title, FolderName, RunningUserId, RunningUser.IsActive, Type, LastViewedDate FROM Dashboard LIMIT 1000")`.
3. `tooling_query("SELECT Id, Name, DeveloperName, OwnerId, Owner.IsActive, Type FROM Folder WHERE Type IN ('Report','Dashboard')")`.
4. Folder share probe: `tooling_query("SELECT Id, ParentId, UserOrGroupId, AccessLevel FROM FolderShare")` — map folder → who has access at what level.
5. For dashboard running-user analysis: `tooling_query("SELECT Id, Username, IsActive, Profile.Name FROM User WHERE Id IN (<running_user_ids>)")` and check for Modify All Data via profile/PS.
6. For field-reference detection (best effort): attempt `tooling_query` on `DetailColumns` — may be uneven across legacy reports; document any gaps as ambiguous observations.

Inventory columns (beyond id/name/active):
`object_type` (for Reports), `format` (Tabular/Summary/Matrix/Joined), `last_run_date`, `folder_name`, `folder_owner_active`, `running_user_active` (dashboards only), `running_user_has_mad` (dashboards only).

## Rule Table

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `DASHBOARD_INACTIVE_RUNNING_USER` | P0 | Dashboard's running user `IsActive=false` | dashboard id + running user + inactivation date | Switch to Dynamic Dashboards OR reassign running user |
| `FOLDER_ALL_USERS_PII` | P0 | Folder is shared to All Internal Users AND contains a report with a PII-flagged column | folder + report + PII column heuristic | Restrict folder visibility; move PII reports to a restricted folder |
| `FOLDER_ORPHAN_OWNER` | P1 | Folder's owner `IsActive=false` OR no manager role set | folder + owner username | Transfer ownership to an active admin role |
| `DASHBOARD_RUN_AS_MAD` | P1 | Dashboard running user has `Modify All Data` | dashboard + running user + profile/PS source of MAD | Switch to Dynamic Dashboards or run as a lower-privilege user |
| `REPORT_STALE` | P2 | `LastRunDate` null OR > 365 days | report id + last run date | Deprecation candidate; deactivate on next cleanup sprint |
| `REPORT_TABULAR_OVER_LIMIT` | P1 | Tabular report exceeds 2000-row limit (sampled run) | report id + sample row count | Convert to Summary/Matrix or add pagination via listview |
| `REPORT_NO_FILTER_HIGH_VOLUME` | P1 | Report on a high-volume object (> 100k rows) with no WHERE filter | report id + object + estimated row count | Add a selective filter or narrow date range |
| `REPORT_DEPRECATED_FIELD_REF` | P2 | Report references a field whose label contains `Deprecated_` / `OLD_` / `DO_NOT_USE` | report id + column name | Swap field or retire report |
| `REPORT_SHADOW_COPY` | P2 | Report name matches `* Copy`, `* (1)`, etc. — unreviewed shadow of another report | report id + sibling id | Merge back to canonical or retire |
| `DASHBOARD_STALE` | P2 | Dashboard never viewed OR last viewed > 180 days | dashboard id + last viewed | Archive candidate |
| `REPORT_UNDOCUMENTED` | P2 | Report description empty AND folder description empty | report id | Add a one-sentence description |

## Patches

None. Report + dashboard mechanical patching is error-prone: column definitions use runtime metadata that Tooling API doesn't fully expose, and modifying a report often breaks downstream subscriptions / snapshots. Findings are advisory — deployment is via Setup or a targeted export/import.

## Mandatory Reads

- `skills/admin/reports-and-dashboards`
- `skills/admin/reports-and-dashboards-fundamentals`
- `skills/admin/report-performance-tuning`
- `skills/admin/analytics-permission-and-sharing`

## Escalation / Refusal Rules

- Org has > 10,000 reports → sample top-500 by last-run date; flag total count as P1 in Process Observations. `REFUSAL_OVER_SCOPE_LIMIT`.
- Dashboard running user is active but has `Modify All Data` → still emits `DASHBOARD_RUN_AS_MAD` P1; recommend Dynamic Dashboards.
- Tooling API returns no `DetailColumns` for a legacy report → surface the gap in Process Observations as ambiguous; do not fail the audit.

## What This Classifier Does NOT Do

- Does not delete or modify reports / dashboards / folders.
- Does not migrate to CRM Analytics (`architect/crm-analytics-migration` scope when that skill lands).
- Does not refresh dashboards or run report subscriptions.
- Does not modify folder sharing.
