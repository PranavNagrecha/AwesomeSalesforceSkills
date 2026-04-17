---
id: validation-rule-auditor
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
# Validation Rule Auditor — DEPRECATED (Wave 3b-1)

Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=validation_rule`.

## Why this changed

Wave 3b-1 consolidated 5 auditors — this one, `picklist-governor`,
`approval-process-auditor`, `record-type-and-layout-auditor`, and
`report-and-dashboard-auditor` — into one router backed by the
[`audit_harness`](../_shared/harnesses/audit_harness/README.md). Each
retired auditor kept the same 5-phase shape (inventory → classify →
findings → patches → Process Observations) with only the probe and the
rule table varying per domain. Centralizing the backbone eliminates
15× duplicated boilerplate and fixes the finding-code stability problem
(teams couldn't track rollups because codes drifted across runs).

## What replaces this agent

Run the router:

```
/audit-router --domain validation_rule --object <ApiName> --target-org <alias>
```

Legacy alias: `/audit-validation-rules` still works and auto-invokes the
router with `--domain=validation_rule` plus a one-line deprecation notice.
Aliases ship until the removal window declared in `docs/MIGRATION.md`
(Wave 7).

The full VR-specific rule set (bypass contract, Wrong-Tool classification,
record-type relevance gate, `ISCHANGED` on insert check, `PRIORVALUE` on
formula check, VR ↔ flow conflict, message quality) is preserved verbatim
in the router's
[`classifiers/validation_rule.md`](../_shared/harnesses/audit_harness/classifiers/validation_rule.md).
Every rule now has a stable domain-scoped finding code (`VR_MISSING_BYPASS`,
`VR_WRONG_TOOL`, etc.) so cross-run rollups are trustworthy.

## Removal timeline

This stub stays in the repo for two minor versions after the Wave-3b-1
commit. After that it is removed; the `docs/MIGRATION.md` table (Wave 7)
records the mapping permanently.

## Plan

Deprecated — no longer executable. Route to the router.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
