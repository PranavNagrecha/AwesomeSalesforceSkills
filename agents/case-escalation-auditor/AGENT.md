---
id: case-escalation-auditor
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
# Case Escalation Auditor — DEPRECATED (Wave 3b-2)

Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=case_escalation`. The full rule set (missing assignment defaults, black-hole queues, expired entitlements, milestone violation rates, business-hour overlap, stale escalation targets) is preserved verbatim in [`classifiers/case_escalation.md`](../_shared/harnesses/audit_harness/classifiers/case_escalation.md). Legacy alias `/audit-case-escalation` ships until Wave 7's `docs/MIGRATION.md` removal window.

## Plan

Deprecated — route to `/audit-router --domain case_escalation --target-org <alias>`.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
