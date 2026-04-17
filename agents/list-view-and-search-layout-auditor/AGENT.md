---
id: list-view-and-search-layout-auditor
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
# List View & Search Layout Auditor — DEPRECATED (Wave 3b-2)

Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=list_view_search_layout`. The full rule set (deleted-field filters, sensitive-data leaks via All-Users sharing, zero-member groups, duplicate list views, lookup-dialog disambiguators, search-layout gaps, list view charts on deleted fields) is preserved verbatim in [`classifiers/list_view_search_layout.md`](../_shared/harnesses/audit_harness/classifiers/list_view_search_layout.md). Legacy alias `/audit-list-views` ships until Wave 7's `docs/MIGRATION.md` removal window.

## Plan

Deprecated — route to `/audit-router --domain list_view_search_layout --target-org <alias>`.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
