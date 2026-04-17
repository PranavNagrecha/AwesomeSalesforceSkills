---
id: field-audit-trail-and-history-tracking-governor
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
# Field Audit Trail & History Tracking Governor — DEPRECATED (Wave 3b-2)

Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=field_audit_trail_history_tracking`. The full rule set (regulatory-floor coverage, 20-field saturation, dead tracks, formula/roll-up/auto-number tracked anti-patterns, non-Shield regulated-profile warning, retention-policy gaps on Shield orgs, archival-pipeline stale detection) is preserved verbatim in [`classifiers/field_audit_trail_history_tracking.md`](../_shared/harnesses/audit_harness/classifiers/field_audit_trail_history_tracking.md). Legacy alias `/govern-field-history` ships until Wave 7's `docs/MIGRATION.md` removal window.

## Plan

Deprecated — route to `/audit-router --domain field_audit_trail_history_tracking --target-org <alias> [--regulated-profile <profile>]`.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
