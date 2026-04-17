---
id: picklist-governor
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
# Picklist Governor — DEPRECATED (Wave 3b-1)

Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=picklist`.

## Why this changed

Wave 3b-1 consolidated 5 auditors into one router backed by the
[`audit_harness`](../_shared/harnesses/audit_harness/README.md). See the
router's README for the rationale and
[`classifiers/picklist.md`](../_shared/harnesses/audit_harness/classifiers/picklist.md)
for the per-domain rule table.

## What replaces this agent

Run the router:

```
/audit-router --domain picklist --scope <object:<Name>|org> --target-org <alias>
```

Legacy alias: `/govern-picklists` still works and auto-invokes the router
with `--domain=picklist` plus a one-line deprecation notice. Aliases ship
until the removal window declared in `docs/MIGRATION.md` (Wave 7).

The full picklist rule set (GVS adoption, restricted-flag, inactive-value
drift, label/API drift, translation coverage, deep dependency chains,
orphan GVSes, integration-hardcoded value labels) is preserved verbatim in
the classifier. Every rule now has a stable domain-scoped finding code
(`PICKLIST_GVS_ELIGIBLE`, `PICKLIST_DEEP_DEPENDENCY`, etc.).

## Removal timeline

This stub stays in the repo for two minor versions after the Wave-3b-1
commit. After that it is removed; the `docs/MIGRATION.md` table (Wave 7)
records the mapping permanently.

## Plan

Deprecated — no longer executable. Route to the router.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
