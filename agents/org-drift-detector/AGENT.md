---
id: org-drift-detector
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
# Org Drift Detector — DEPRECATED (Wave 3b-2)

Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=org_drift`. The full rule set (library-prescribed patterns probed against the org, gap / bloat / fork / orphan / stale-skill classification, security-gap P0 escalation, Named-Credential-vs-Remote-Site drift) is preserved verbatim in [`classifiers/org_drift.md`](../_shared/harnesses/audit_harness/classifiers/org_drift.md). Legacy alias `/detect-drift` ships until Wave 7's `docs/MIGRATION.md` removal window.

## Plan

Deprecated — route to `/audit-router --domain org_drift --target-org <alias> [--scope <scope>] [--max-findings <N>]`.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
