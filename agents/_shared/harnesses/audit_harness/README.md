# Harness: audit_harness

**Status:** Wave 3b shared harness.
**Consumed by:** [`agents/audit-router/AGENT.md`](../../../audit-router/AGENT.md).
**Replaces:** ~15 single-mode auditor agents whose logic was 80% duplicated boilerplate.

## Why this exists

The retired auditors — `validation-rule-auditor`, `picklist-governor`, `approval-process-auditor`, `record-type-and-layout-auditor`, `report-and-dashboard-auditor`, and 10 more in Wave 3b-2 — all performed the same five phases in the same order:

1. **Inventory** (domain-specific probe)
2. **Classify** each row against a P0/P1/P2 rule set
3. **Emit findings** + (optional) mechanical patches
4. **Process Observations** (healthy / concerning / ambiguous / follow-ups)
5. **Escalation rules** (scope limits, refusal conditions)

They diverged only on **Step 1's probe** and **Step 2's rule table**. Every other concern — finding severity enum, process-observations format, citation block, refusal codes — was duplicated verbatim across 15 AGENT.md files. Every change cost 15 edits.

This harness owns the four common phases. The router cites the harness documents for the shared concerns and uses a per-domain **classifier markdown file** to dispatch the probe + rule-set logic.

## Files in this harness

| File | Purpose |
|---|---|
| `README.md` (this file) | Architecture + file index |
| `output_schema.md` | Canonical output envelope (findings / patches / observations / citations). Reviewed and approved at Wave 3b-1 user-approval gate #4. |
| `severity_rubric.md` | P0 / P1 / P2 definitions + finding-code naming convention (`<DOMAIN>_<SNAKE_CASE>`) |
| `classifier_contract.md` | What each `classifiers/<domain>.md` file MUST contain and in what order |
| `classifiers/<domain>.md` | One per audit domain. Holds the inventory probe, rule table, patch templates, mandatory skills, refusal conditions. |

## Shipping order

- **Wave 3b-1**: harness core + 5 classifiers (validation_rule, picklist, approval_process, record_type_layout, report_dashboard).
- **Wave 3b-2**: remaining 10 classifiers (case_escalation, lightning_record_page, list_view_search_layout, quick_action, reports_dashboards_folder_sharing, field_audit_trail_history_tracking, sharing, org_drift, my_domain_session_security, prompt_library).

Splitting the wave keeps each commit reviewable. The output_schema + classifier_contract are frozen after Wave 3b-1; Wave 3b-2 only adds classifier files.

## Non-goals

- Not a Python library. Every file here is plain markdown the agent's LLM reads.
- Not a runtime. The MCP server does not execute audits — the router returns plans, humans act.
- Not a schema for new audit domains. Adding a new domain requires (a) a new `classifiers/<domain>.md`, (b) a new entry in the router's domain list, (c) reviewer sign-off. The harness does not auto-extend.
