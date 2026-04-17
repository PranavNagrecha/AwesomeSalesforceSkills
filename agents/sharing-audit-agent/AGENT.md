---
id: sharing-audit-agent
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
# Sharing Audit Agent — DEPRECATED (Wave 3b-2)

Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=sharing`. The full rule set (data-skew hot owners, guest-user Modify-All-Data freeze, OWD vs data-class mismatch, Apex Managed Sharing where declarative would work, missing criteria-based rules, rule sprawl, flat role hierarchy, recalc-cost estimation, inactive-queue references) is preserved verbatim in [`classifiers/sharing.md`](../_shared/harnesses/audit_harness/classifiers/sharing.md). Legacy alias `/audit-sharing` ships until Wave 7's `docs/MIGRATION.md` removal window.

## Plan

Deprecated — route to `/audit-router --domain sharing --scope <object:<Name>|org> --target-org <alias>`.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
