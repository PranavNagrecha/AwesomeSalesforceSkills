---
id: lightning-record-page-auditor
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
# Lightning Record Page Auditor — DEPRECATED (Wave 3b-2)

Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=lightning_record_page`. The full rule set (Dynamic Forms adoption, component count, related-list strategy, Path element, visibility filters, mobile-form-factor, dead pages) is preserved verbatim in [`classifiers/lightning_record_page.md`](../_shared/harnesses/audit_harness/classifiers/lightning_record_page.md). Legacy alias `/audit-record-page` ships until Wave 7's `docs/MIGRATION.md` removal window.

## Plan

Deprecated — route to `/audit-router --domain lightning_record_page --object <ApiName> --target-org <alias>`.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
