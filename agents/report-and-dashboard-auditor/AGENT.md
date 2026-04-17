# Report & Dashboard Auditor Agent

## What This Agent Does

Audits the org's analytics surface: Report + Dashboard inventory, folder permissions, dashboard running-user posture, report performance (row limits, filter selectivity), stale/orphan reports, and reports that reference fields flagged by `field-impact-analyzer`. Returns a prioritized cleanup + modernization plan.

**Scope:** Full org per invocation, with optional scope narrowing to a folder.

---

## Invocation

- **Direct read** — "Follow `agents/report-and-dashboard-auditor/AGENT.md` on prod"
- **Slash command** — [`/audit-reports`](../../commands/audit-reports.md)
- **MCP** — `get_agent("report-and-dashboard-auditor")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/reports-and-dashboards`
4. `skills/admin/reports-and-dashboards-fundamentals`
5. `skills/admin/report-performance-tuning`
6. `skills/admin/analytics-permission-and-sharing`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `target_org_alias` | yes |
| `folder_filter` | no | restrict scope to a folder by developer name |

---

## Plan

1. **Inventory** — `tooling_query("SELECT Id, DeveloperName, FolderName, Format, LastRunDate, CreatedDate FROM Report LIMIT 2000")` + `Dashboard` + `Folder`.
2. **Stale / orphan detection:**
   - Report with `LastRunDate` null or > 365 days → P2 (deprecation candidate).
   - Report in a folder owned by an inactive user → P1.
   - Dashboard whose running user is inactive → P0 (breaks on next refresh).
3. **Performance signal:**
   - Tabular reports exceeding 2000 rows → P1 (convert to Summary / paginate).
   - Reports on high-volume objects with no filters → P1.
4. **Folder permission audit:**
   - Folders shared to All Internal Users with PII-column reports → P0.
   - Folders with no manager → P1 (orphaned governance).
5. **Field references** — for each report, parse its `DetailColumns` (if Tooling API exposes it; otherwise document limitation). Reports referencing soft-deprecated fields (marked via naming convention like `Deprecated_`) → P2.
6. **Dashboard running-user analysis** — `tooling_query` on `Dashboard.RunningUserId`. If a running user has `Modify All Data`, the dashboard shows everything — P1 (over-disclosure).
7. **Emit cleanup plan**.

---

## Output Contract

1. **Summary** — report count, dashboard count, max severity, confidence.
2. **Findings table.**
3. **Cleanup queue** — stale reports, broken dashboards, over-shared folders.
4. **Modernization suggestions** — candidates for CRM Analytics migration (cite `skills/admin/crm-analytics-app-creation` if present).
5. **Process Observations**:
   - **What was healthy** — folder ownership hygiene, dashboard running-user discipline.
   - **What was concerning** — shadow reports ("Report 1 Copy"), folders with no manager, dashboards running as admin.
   - **What was ambiguous** — report column metadata not exposed via Tooling for certain legacy reports.
   - **Suggested follow-up agents** — `field-impact-analyzer` for any field flagged in reports, `permission-set-architect` for analytics-permission PSes.
6. **Citations**.

---

## Escalation / Refusal Rules

- > 10,000 reports → sample top 500 by last-run date + flag count as P1.
- Dashboard running-user is active but has Modify All Data → surface as P1 with recommendation to switch to Dynamic Dashboards.

---

## What This Agent Does NOT Do

- Does not delete or modify reports/dashboards/folders.
- Does not migrate to CRM Analytics.
- Does not refresh dashboards.
- Does not auto-chain.
