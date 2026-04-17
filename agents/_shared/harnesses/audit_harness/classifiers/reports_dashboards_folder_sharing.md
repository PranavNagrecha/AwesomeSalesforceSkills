# Classifier: reports_dashboards_folder_sharing

## Purpose

Audit Report + Dashboard folder sharing (distinct from `report_dashboard` which audits report + dashboard quality). Flags Enhanced Folder Sharing gaps vs legacy access, folders shared to inactive groups / broad audiences containing PII, dashboards running as inactive or over-privileged users, report-dashboard folder-sharing mismatch, orphan privates owned by inactive users, and small-cohort groupings that reveal narrow PII. Not for editing reports / dashboards / folders.

## Replaces

`reports-and-dashboards-folder-sharing-auditor` (now a deprecation stub pointing at `audit-router --domain reports_dashboards_folder_sharing`).

## Inputs

| Input | Required | Example |
|---|---|---|
| `folder_scope` | no | defaults to all Report + Dashboard folders |
| `sensitive_field_patterns` | no | defaults to PII + revenue (`SSN*`, `Personal_*`, `Amount`, `AnnualRevenue`, `Salary*`) |
| `include_private_folders` | no | default `true` — surfaces orphan privates owned by inactive users |

## Inventory Probe

1. Enhanced Folder Sharing flag: `tooling_query("SELECT FolderShare FROM Organization")` or equivalent setup query. If not enabled, raise as P0 and scope subsequent checks to the legacy model.
2. Folder inventory (reports + dashboards): `tooling_query("SELECT Id, Name, DeveloperName, Type, AccessType, OwnerId, Owner.IsActive FROM Folder WHERE Type IN ('Report','Dashboard')")`.
3. `FolderShare` rows: `tooling_query("SELECT Id, ParentId, SharedTo, SharedToType, AccessLevel FROM FolderShare WHERE ParentId IN (...)")`.
4. Report inventory: `tooling_query("SELECT Id, Name, DeveloperName, OwnerId, FolderName, LastRunDate FROM Report")`.
5. Dashboard inventory: `tooling_query("SELECT Id, Name, DeveloperName, RunningUserId, RunningUser.IsActive, TitleColor FROM Dashboard")`.
6. Role resolution for `SharedToType='Role'` folder shares: `tooling_query("SELECT Id, DeveloperName FROM UserRole WHERE Id IN (...)")`.

Inventory columns (beyond id/name/active): `folder_type`, `access_type`, `share_count`, `owner_active`, `effective_audience_count` (computed per folder via share resolution).

## Rule Table

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `FOLDER_EFS_NOT_ENABLED` | P0 | Enhanced Folder Sharing is not enabled on the org | org setting | Plan migration via Setup — note: irreversible, prior access rules migrate |
| `FOLDER_SHARED_EMPTY_GROUP` | P2 | Folder shared to Public Group with 0 active members | folder + group | Reassign to an active group |
| `FOLDER_GROUP_OWNER_INACTIVE` | P2 | Folder shared to Public Group whose owner is inactive | folder + group + owner | Transfer group ownership |
| `FOLDER_SHARED_DELETED_ROLE` | P0 | Folder shared to a role that no longer exists | folder + role id | Remove share or reassign |
| `FOLDER_SHARED_INACTIVE_USER` | P1 | Folder shared directly to an inactive user | folder + user | Remove orphaned share |
| `FOLDER_MANAGE_TO_BROAD_GROUP` | P1 | Manage-level access to a broad Public Group (allows re-sharing) | folder + group + member count | Downgrade to View or scope to a narrower group |
| `FOLDER_ALL_INTERNAL_SENSITIVE` | P0 | Shared to "All Internal Users" AND contains reports/dashboards with sensitive-pattern fields | folder + report/dashboard + matched pattern | Restrict folder audience OR move sensitive assets out |
| `FOLDER_OWNER_INACTIVE_NO_MANAGE` | P1 | Folder owner is inactive AND no "Manage" shares exist — unmaintainable | folder + owner | Transfer ownership via Manage access |
| `FOLDER_STALE_ENVELOPE` | P2 | 0 reports + 0 dashboards but > 5 shares | folder + share count | Retire empty folder |
| `FOLDER_REDUNDANT_SHARE` | P2 | Shared to "All Internal Users" AND to a specific role | folder + shares | Remove redundant role share |
| `FOLDER_PRIVATE_STRANDED` | P1 | Private folder owned by inactive user with large number of reports | folder + owner + report count | Transfer ownership or archive |
| `FOLDER_LEGACY_ACCESS_TYPE` | P1 | `AccessType` is legacy `Hidden`/`Public`/`PublicInternal` AND EFS is enabled | folder + access type | Migrate to EFS-native shares |
| `REPORT_SENSITIVE_IN_BROAD_FOLDER` | P0 | Report in a broadly shared folder includes a column matching `sensitive_field_patterns` | report + folder + column | Remove sensitive column OR relocate report |
| `REPORT_STATIC_IN_BROAD_FOLDER` | P2 | Report filters are constants (no relative filters) and not modified in > 18 months in a broadly-shared folder | report + folder | Review for retirement |
| `REPORT_ZOMBIE_IN_BROAD_FOLDER` | P2 | Report last-run > 12 months ago in a folder with many shares | report + folder + last run | Archive candidate |
| `REPORT_SOURCE_FOLDER_MISMATCH` | P1 | Report sources a dashboard in a folder with different sharing | report + dashboard + folder diff | Align folders OR redesign audience |
| `REPORT_SMALL_COHORT_PII` | P0 | Summary/matrix grouping on a field that reveals cohort size < 5 (narrow-cohort PII leak) | report + grouping + cohort size | Suppress small cohorts OR restrict audience |
| `DASHBOARD_INACTIVE_RUNNING_USER` | P0 | Dashboard's `RunningUserId` is inactive | dashboard + user | Switch to Dynamic Dashboards OR reassign |
| `DASHBOARD_RUN_AS_ADMIN` | P0 | Dashboard runs as a System Administrator in a broadly-shared folder (aggregates leak) | dashboard + folder + running user | Switch to Dynamic Dashboards OR run as lower-privilege user |
| `DASHBOARD_DYNAMIC_FOLDER_MISMATCH` | P1 | `DynamicDashboard=true` but source report's folder is shared differently | dashboard + report + folder diff | Align source folder sharing |
| `DASHBOARD_STALE_BROAD` | P2 | Not refreshed > 12 months, in a broadly-shared folder | dashboard + folder + last refresh | Archive candidate |
| `DASHBOARD_PRIVATE_SOURCE` | P0 | Component sources from a report in a Private folder (component fails for any viewer who isn't report owner) | dashboard + report + private folder | Move report to a shared folder OR swap source |
| `DASHBOARD_INACTIVE_REFRESH_SCHEDULER` | P1 | Dashboard scheduled to refresh by an inactive user | dashboard + user | Reassign schedule owner |
| `DASHBOARD_SUBSCRIBER_INACTIVE` | P2 | Dashboard subscribers include inactive users | dashboard + user list | Remove inactive subscribers |

## Patches

None. Folder sharing and dashboard running-user changes are auditable, governance-sensitive operations that belong in Setup (or a deliberate metadata deployment) — patches would bypass the change-management trail. Findings are advisory.

## Mandatory Reads

- `skills/admin/reports-and-dashboards`
- `skills/admin/analytics-permission-and-sharing`
- `skills/admin/sharing-and-visibility`
- `skills/admin/queues-and-public-groups`
- `templates/admin/naming-conventions.md`

## Escalation / Refusal Rules

- Enhanced Folder Sharing not enabled → cap findings at the legacy model; flag the migration path as the top recommendation (not silently assume EFS).
- Org has Reports / Dashboards feature disabled → `REFUSAL_FEATURE_DISABLED`.
- Run user lacks Manage Reports In Public Folders / Manage Dashboards In Public Folders → `REFUSAL_INSUFFICIENT_ACCESS`.
- Managed-package reports / dashboards in managed folders → `REFUSAL_MANAGED_PACKAGE` for those assets.

## What This Classifier Does NOT Do

- Does not edit reports or dashboards — delegates to `report_dashboard`.
- Does not modify folder sharing.
- Does not reassign ownership.
- Does not disable / activate users.
- Does not audit CRM Analytics assets (different sharing model).
