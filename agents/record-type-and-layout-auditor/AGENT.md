---
id: record-type-and-layout-auditor
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
# Record Type & Layout Auditor — DEPRECATED (Wave 3b-1)

Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=record_type_layout`.

## Why this changed

Wave 3b-1 consolidated 5 auditors into one router backed by the
[`audit_harness`](../_shared/harnesses/audit_harness/README.md). See the
router's README for the rationale and
[`classifiers/record_type_layout.md`](../_shared/harnesses/audit_harness/classifiers/record_type_layout.md)
for the per-domain rule table.

## What replaces this agent

Run the router:

```
/audit-router --domain record_type_layout --object <ApiName> --target-org <alias>
```

Legacy alias: `/audit-record-types` invokes the router with
`--domain=record_type_layout` plus a one-line deprecation notice. Aliases
ship until the removal window declared in `docs/MIGRATION.md` (Wave 7).

The full RT + Layout rule set (proliferation, Master Layout as primary,
orphan RTs, inactive RT still referenced by flows or VRs, picklist-value
divergence across RTs, missing Lightning Record Pages for persona RTs,
inactive Business Process attachments) is preserved verbatim in the
classifier. Every rule has a stable domain-scoped finding code
(`RT_PROLIFERATION`, `RT_ORPHAN`, `RT_INACTIVE_REFERENCED`, etc.).

## Removal timeline

This stub stays in the repo for two minor versions after the Wave-3b-1
commit. After that it is removed; the `docs/MIGRATION.md` table (Wave 7)
records the mapping permanently.

## Plan

Deprecated — no longer executable. Route to the router.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
