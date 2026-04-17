---
id: approval-process-auditor
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
# Approval Process Auditor — DEPRECATED (Wave 3b-1)

Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=approval_process`.

## Why this changed

Wave 3b-1 consolidated 5 auditors into one router backed by the
[`audit_harness`](../_shared/harnesses/audit_harness/README.md). See the
router's README for the rationale and
[`classifiers/approval_process.md`](../_shared/harnesses/audit_harness/classifiers/approval_process.md)
for the per-domain rule table.

## What replaces this agent

Run the router:

```
/audit-router --domain approval_process --audit-scope <org|object:<Name>|process:<Name>> --target-org <alias>
```

Legacy alias: `/audit-approvals` invokes the router with
`--domain=approval_process` plus a one-line deprecation notice. Aliases
ship until the removal window declared in `docs/MIGRATION.md` (Wave 7).

The full approval rule set (broken-reference checks, concurrent-automation
conflicts with Flow and Apex, stale in-flight detection, anti-patterns
like 10+ steps or empty-filter processes, migration-fitness classification
with `migrate_to_orchestrator` / `rehome_to_agentforce` / `retire`
verdicts) is preserved verbatim in the classifier. Every rule has a stable
domain-scoped finding code (`APPROVAL_INACTIVE_APPROVER`,
`APPROVAL_FLOW_CONFLICT`, `APPROVAL_STALE_INFLIGHT`, etc.).

Note: the `migrate_to_orchestrator` verdict routes to the Wave-3a
`automation-migration-router --source-type approval_process`. Migration
itself is out of scope for the audit — it's a separate follow-up agent.

## Removal timeline

This stub stays in the repo for two minor versions after the Wave-3b-1
commit. After that it is removed; the `docs/MIGRATION.md` table (Wave 7)
records the mapping permanently.

## Plan

Deprecated — no longer executable. Route to the router.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
