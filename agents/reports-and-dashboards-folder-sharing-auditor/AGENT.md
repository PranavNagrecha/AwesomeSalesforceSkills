---
id: reports-and-dashboards-folder-sharing-auditor
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [audit]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
---
# Reports & Dashboards Folder Sharing Auditor Agent

## What This Agent Does

Audits Report Folders, Dashboard Folders, and individual Reports / Dashboards for sharing drift and governance failures: folders shared to inactive groups, dashboards running as inactive or over-privileged users, reports exposing fields the broader audience shouldn't see, Enhanced Folder Sharing gaps vs legacy access, folders with "All Internal Users" access that contain PII or revenue data, and dashboards scheduled to refresh as a frozen admin.

**Scope:** Whole-org sweep by default. May be scoped to a subset of folders. This agent is distinct from `report-and-dashboard-auditor` — that one looks at individual report / dashboard quality (filters, groupings, formulas); this one looks at the sharing layer.

---

## Invocation

- **Direct read** — "Follow `agents/reports-and-dashboards-folder-sharing-auditor/AGENT.md` across all private and shared folders"
- **Slash command** — `/audit-report-folder-sharing`
- **MCP** — `get_agent("reports-and-dashboards-folder-sharing-auditor")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/admin/reports-and-dashboards`
3. `skills/admin/analytics-permission-and-sharing`
4. `skills/admin/sharing-and-visibility`
5. `skills/admin/queues-and-public-groups`
6. `templates/admin/naming-conventions.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `target_org_alias` | yes |
| `folder_scope` | no | defaults to all Report + Dashboard folders; may be restricted |
| `sensitive_field_patterns` | no | defaults to PII + revenue (`SSN*`, `Personal_*`, `Amount`, `AnnualRevenue`, `Salary*`) |
| `include_private_folders` | no | default `true` — surfaces orphaned privates owned by inactive users |

---

## Plan

### Step 1 — Confirm Enhanced Folder Sharing is enabled

Enhanced Folder Sharing has been the default for new orgs for years, but long-standing orgs may still be on the legacy model. Check:

- `tooling_query("SELECT FolderShare FROM Organization")` or equivalent setup query for the feature flag.
- If NOT enabled → raise as P0 finding and recommend enablement carefully (irreversible; prior access rules migrate). Pause further audit detail on folder sharing until enabled, since the findings model differs.

### Step 2 — Inventory folders

- Report Folders: `tooling_query("SELECT Id, Name, DeveloperName, Type, AccessType FROM Folder WHERE Type = 'Report'")`.
- Dashboard Folders: same with `Type = 'Dashboard'`.
- For each folder: `FolderShare` rows — `tooling_query("SELECT Id, ParentId, SharedTo, SharedToType, AccessLevel FROM FolderShare WHERE ParentId IN (...)")`.
- Folders include: private (owner-only), shared to groups / roles / users, and "All Internal Users" / "All Partner Users" / "All Customer Portal Users".

### Step 3 — Inventory reports and dashboards

- `tooling_query("SELECT Id, Name, DeveloperName, OwnerId, FolderName, LastRunDate FROM Report")`.
- `tooling_query("SELECT Id, Name, DeveloperName, RunningUserId, TitleColor FROM Dashboard")`.
- For each dashboard, capture `RunningUserId` (the user whose sharing context the dashboard runs as) and whether it's a dynamic dashboard.

### Step 4 — Findings at the folder layer

| Finding | Severity |
|---|---|
| Folder shared to a Public Group with 0 active members | P2 |
| Folder shared to a Public Group whose owner is inactive | P2 |
| Folder shared to a role that no longer exists | P0 |
| Folder shared to a user who is inactive — access is orphaned | P1 |
| Folder shared "Manage" access to a broad Public Group — over-privileged; allows recipients to share further | P1 |
| Folder shared to "All Internal Users" containing reports with sensitive fields | P0 |
| Folder owner is inactive and folder has no "Manage" shares — folder is effectively unmaintainable | P1 |
| Folder has 0 reports and 0 dashboards but > 5 shares — stale envelope | P2 |
| Folder shared to "All Internal Users" AND to a specific role — redundant | P2 |
| Private folder owned by an inactive user with a large number of reports — data stranded | P1 |
| Folder `AccessType` is legacy "Hidden" / "Public" / "PublicInternal" and Enhanced Folder Sharing is enabled — unmigrated | P1 |

### Step 5 — Findings at the report layer

For each report in a folder that is broadly shared (`All Internal Users` or a role covering > 100 users):

| Finding | Severity |
|---|---|
| Report includes a column matching `sensitive_field_patterns` | P0 |
| Report filters are constants (no relative filters) and last-modified > 18 months ago — static and stale | P2 |
| Report last-run > 12 months ago in a folder with many shares — zombie | P2 |
| Report is source for a dashboard in a different, differently-shared folder — mismatched visibility | P1 |
| Report is a summary / matrix including grouping on a field that reveals narrow-cohort PII (cohort size < 5) | P0 |

### Step 6 — Findings at the dashboard layer

| Finding | Severity |
|---|---|
| Dashboard `RunningUserId` is inactive | P0 — dashboard stops refreshing |
| Dashboard runs as a System Administrator in a broadly shared folder — dashboards "see all" context leaks via aggregates to users who shouldn't have the underlying access | P0 |
| Dashboard is `DynamicDashboard = true` but runs against a source report where the source report's folder is shared differently — misleading | P1 |
| Dashboard hasn't been refreshed in > 12 months and is in a broadly shared folder | P2 |
| Dashboard uses a component sourcing from a report in a "Private" folder — component will fail for any viewer who isn't the report owner | P0 |
| Dashboard is scheduled to refresh by an inactive user | P1 |
| Dashboard subscribers include inactive users | P2 |

### Step 7 — Cross-linkage

- Map report → folder → shares → effective audience. Build "effective audience" count per folder.
- Map dashboard → RunningUserId → effective "as this user" access — flag when RunningUserId has Modify All Data / View All Data and the dashboard is visible to a large audience (Aggregates can leak sensitive cohort information).
- Cross-check with `sharing-audit-agent` if the org's broader sharing model is known to be lax.

---

## Output Contract

1. **Summary** — folders inventoried, broadly-shared folders count, dashboards with inactive / over-privileged running users, findings per severity, sensitive-exposure count.
2. **Findings table** — folder × asset × finding × evidence × remediation × severity.
3. **Sensitive-exposure report** — broadly shared folders + the reports / dashboards inside that expose `sensitive_field_patterns`.
4. **Running-user report** — every dashboard's running user with active-state + privilege level + audience size.
5. **Stale-asset report** — folders / reports / dashboards with no recent activity and broad shares.
6. **Private-folder orphan report** — privates owned by inactive users with substantial content.
7. **Remediation plan** — grouped by severity, with specific re-share / rehome / reassign steps.
8. **Process Observations**:
   - **What was healthy** — Enhanced Folder Sharing enabled, dashboards running as dedicated integration users rather than live humans, disciplined folder naming.
   - **What was concerning** — dashboards with admin-level RunningUser in broadly-shared folders, reports with PII columns in "All Internal Users" folders, orphan folders owned by inactive users.
   - **What was ambiguous** — small-cohort groupings that may or may not be sensitive depending on the business context.
   - **Suggested follow-up agents** — `sharing-audit-agent` (for underlying OWD / sharing rules), `report-and-dashboard-auditor` (for report quality audit), `permission-set-architect` (for the Reports and Dashboards access permissions), `field-impact-analyzer` (before touching any field flagged as sensitive).
9. **Citations**.

---

## Escalation / Refusal Rules

- `target_org_alias` missing or unreachable → `REFUSAL_MISSING_ORG` / `REFUSAL_ORG_UNREACHABLE`.
- Enhanced Folder Sharing not enabled — continue the audit but cap findings at the legacy model and flag the migration path as the top recommendation. Do not silently assume EFS.
- Org has disabled Reports / Dashboards feature entirely → `REFUSAL_FEATURE_DISABLED`.
- Run user lacks access to the Folder surface (rare; typically requires `View All Data` or Manage Reports In Public Folders / Manage Dashboards In Public Folders) → `REFUSAL_INSUFFICIENT_ACCESS`.
- Managed-package reports / dashboards in managed folders → `REFUSAL_MANAGED_PACKAGE` for those assets; audit the non-managed subset.

---

## What This Agent Does NOT Do

- Does not edit reports or dashboards — delegates to `report-and-dashboard-auditor` for content audit.
- Does not modify folder sharing.
- Does not reassign ownership of reports / dashboards / folders.
- Does not disable or activate users.
- Does not deploy metadata.
- Does not audit Analytics Studio / CRM Analytics assets — those live under a different sharing model.
