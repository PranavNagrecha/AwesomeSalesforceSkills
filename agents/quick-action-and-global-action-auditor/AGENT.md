---
id: quick-action-and-global-action-auditor
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
# Quick Action & Global Action Auditor — DEPRECATED (Wave 3b-2)

Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=quick_action` for the audit mode. The `design` mode migrates separately to Wave 3c's `designer_base` harness (as `action-designer`). The audit rule set (deleted-field refs, deactivated Flows, orphan VF pages, deleted LWCs, invisible actions not surfaced on any layout, duplicate/standard-mirror actions, predefined-value field-gone checks, unresolved merge fields in SuccessMessage, VF-backed de-emphasis candidates) is preserved verbatim in [`classifiers/quick_action.md`](../_shared/harnesses/audit_harness/classifiers/quick_action.md). Legacy alias `/audit-actions` ships until Wave 7's `docs/MIGRATION.md` removal window.

## Plan

Deprecated — route to `/audit-router --domain quick_action --target-org <alias>` for audits. Design mode will be routed through Wave 3c.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
