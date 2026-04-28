# /audit-router

Invoke the [audit-router](../agents/audit-router/AGENT.md) agent. Wave 3b-1 of the redesign (see [plan file](/Users/pranavnagrecha/.claude/plans/keen-napping-wombat.md)).

## Synopsis

```
/audit-router --domain <domain> --target-org <alias> [domain-specific args]
```

## Supported domains (15 total — Wave 3b-1 shipped 5, Wave 3b-2 shipped the remaining 10)

| `--domain` | Replaces | Classifier |
|---|---|---|
| `validation_rule` | `validation-rule-auditor` | [validation_rule.md](../agents/_shared/harnesses/audit_harness/classifiers/validation_rule.md) |
| `picklist` | `picklist-governor` | [picklist.md](../agents/_shared/harnesses/audit_harness/classifiers/picklist.md) |
| `approval_process` | (consolidated; stub removed) | [approval_process.md](../agents/_shared/harnesses/audit_harness/classifiers/approval_process.md) |
| `record_type_layout` | `record-type-and-layout-auditor` | [record_type_layout.md](../agents/_shared/harnesses/audit_harness/classifiers/record_type_layout.md) |
| `report_dashboard` | `report-and-dashboard-auditor` | [report_dashboard.md](../agents/_shared/harnesses/audit_harness/classifiers/report_dashboard.md) |
| `case_escalation` | `case-escalation-auditor` | [case_escalation.md](../agents/_shared/harnesses/audit_harness/classifiers/case_escalation.md) |
| `lightning_record_page` | `lightning-record-page-auditor` | [lightning_record_page.md](../agents/_shared/harnesses/audit_harness/classifiers/lightning_record_page.md) |
| `list_view_search_layout` | `list-view-and-search-layout-auditor` | [list_view_search_layout.md](../agents/_shared/harnesses/audit_harness/classifiers/list_view_search_layout.md) |
| `quick_action` | `quick-action-and-global-action-auditor` (audit mode) | [quick_action.md](../agents/_shared/harnesses/audit_harness/classifiers/quick_action.md) |
| `reports_dashboards_folder_sharing` | `reports-and-dashboards-folder-sharing-auditor` | [reports_dashboards_folder_sharing.md](../agents/_shared/harnesses/audit_harness/classifiers/reports_dashboards_folder_sharing.md) |
| `field_audit_trail_history_tracking` | `field-audit-trail-and-history-tracking-governor` | [field_audit_trail_history_tracking.md](../agents/_shared/harnesses/audit_harness/classifiers/field_audit_trail_history_tracking.md) |
| `sharing` | `sharing-audit-agent` | [sharing.md](../agents/_shared/harnesses/audit_harness/classifiers/sharing.md) |
| `org_drift` | `org-drift-detector` | [org_drift.md](../agents/_shared/harnesses/audit_harness/classifiers/org_drift.md) |
| `my_domain_session_security` | `my-domain-and-session-security-auditor` | [my_domain_session_security.md](../agents/_shared/harnesses/audit_harness/classifiers/my_domain_session_security.md) |
| `prompt_library` | `prompt-library-governor` | [prompt_library.md](../agents/_shared/harnesses/audit_harness/classifiers/prompt_library.md) |

Note: `quick-action-and-global-action-auditor` had a `design` mode that is NOT part of the audit router. Design mode migrates to Wave-3c's `designer_base` harness (as `action-designer`).

## Legacy alias commands

Each alias invokes the router with a preset `--domain` and emits a one-line deprecation notice. Aliases ship until the removal window declared in `docs/MIGRATION.md` (Wave 7).

| Alias | Equivalent to |
|---|---|
| `/audit-validation-rules` | `/audit-router --domain validation_rule ...` |
| `/govern-picklists` | `/audit-router --domain picklist ...` |
| `/audit-approvals` | `/audit-router --domain approval_process ...` |
| `/audit-record-types` | `/audit-router --domain record_type_layout ...` |
| `/audit-reports` | `/audit-router --domain report_dashboard ...` |

## What it does

Uniform output envelope across every domain: inventory + findings (with stable domain-scoped codes like `VR_MISSING_BYPASS`, `PICKLIST_NO_GVS`, `APPROVAL_INACTIVE_APPROVER`) + optional mechanical patches + Process Observations + citations. See [`agents/audit-router/AGENT.md`](../agents/audit-router/AGENT.md) for the full contract and [`output_schema.md`](../agents/_shared/harnesses/audit_harness/output_schema.md) for the envelope shape.

## Safety

- Router never modifies the org, never deploys, never executes Apex.
- Refusal codes are canonical (`agents/_shared/REFUSAL_CODES.md`).
- Every finding code must be declared in its classifier's Rule Table; the router may not invent codes.
- Citation gate enforces that every skill / template / decision-tree / probe the classifier cites resolves to a real path.

## See also

- [`agents/_shared/harnesses/audit_harness/`](../agents/_shared/harnesses/audit_harness/) — harness + classifiers
- [`agents/_shared/harnesses/audit_harness/severity_rubric.md`](../agents/_shared/harnesses/audit_harness/severity_rubric.md) — P0/P1/P2 definitions + finding-code convention
- [`agents/_shared/REFUSAL_CODES.md`](../agents/_shared/REFUSAL_CODES.md) — canonical refusal codes
