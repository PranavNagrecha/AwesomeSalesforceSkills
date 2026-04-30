---
name: mass-transfer-ownership
description: "Use when re-assigning record OwnerId across many records — territory realignment, employee departure, region split, integration cleanup. Triggers: 'mass transfer accounts', 'reassign opportunities to new owner', 'transfer all records on user deactivation', 'OwnerId migration'. NOT for assignment rules, queue routing, or single-record manual transfer."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "transfer 5000 accounts to a new owner"
  - "deactivate user but keep their records assigned"
  - "territory realignment OwnerId migration"
  - "Mass Transfer Records tool too slow for the dataset"
  - "owner change cascading to child records"
tags:
  - ownership
  - data-management
  - migration
  - admin
inputs:
  - "source criteria (owner, territory, region, queue) for the records to transfer"
  - "target OwnerId or user-mapping CSV"
  - "objects in scope and whether children should follow the parent"
outputs:
  - "transfer plan covering ownership cascade, sharing recalc, and integration impact"
  - "rollback / audit log strategy"
  - "executed transfer (Mass Transfer tool, Data Loader update, or Apex)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-30
---

# Mass Transfer Ownership

Activate when an admin needs to move a non-trivial volume of records (typically >100, often tens of thousands) from one or more current owners to one or more new owners. The skill produces a transfer plan covering tool selection, child-record cascading rules, sharing recalculation timing, and a rollback path.

---

## Before Starting

Gather this context before working on anything in this domain:

- Volume per object (Accounts, Opportunities, Contacts, Cases, custom objects). Above ~250k records on a single object, sharing recalc dominates the timeline and a maintenance window is required.
- Whether the transfer is a single-source-to-single-target swap, a many-to-many remap (e.g., a CSV mapping old owner → new owner), or a queue-to-user / user-to-queue move. Each uses different tooling.
- Whether child records should follow. Account.OwnerId reassignment can optionally cascade to child Cases and Opportunities through the Mass Transfer tool's checkboxes; Data Loader does not cascade — every child object must be transferred explicitly.
- Whether the org has Apex triggers, validation rules, or workflow rules that fire on Owner change. These can fail or send unwanted notifications during a 50,000-record transfer.

---

## Core Concepts

### Tool selection

| Tool | Best for | Limit |
|---|---|---|
| Setup → Data Management → Mass Transfer Records | <50k records on standard objects (Accounts, Leads, Opportunities), simple one-to-one reassignment, with cascade-to-children checkboxes | UI-only, no CSV mapping; many-to-many requires repeated runs |
| Data Loader Update | Any object, any volume, mapping CSV | No cascade — each child object is its own job; emits triggers and workflow |
| Apex (`Database.update` with `AllOrNone=false`) | Many-to-many remap with conditional logic, suppression of email notifications, batched sharing recalc | Requires careful governor-limit-aware batching |
| Anonymous Apex Batch (`Database.Batchable`) | >250k records where sharing recalc would otherwise lock the org | Asynchronous; needs progress monitoring |

### Sharing recalculation

Owner changes trigger sharing recalculation for the record and its children if the org-wide default is not Public Read/Write. On large objects, recalc can extend the transaction by hours. For >100k records, Salesforce recommends using *Defer Sharing Calculations* (a feature you must request via Support) so the transfer completes first and recalc runs in a controlled window.

### Cascade behavior

Account ownership change cascades to child Cases, Contacts, and Opportunities only when the Mass Transfer Records tool's "Transfer ... " checkboxes are ticked. API-driven updates (Data Loader, Apex) do **not** cascade. If you want child records to follow the parent through API, you must update each child object as a separate operation.

---

## Common Patterns

### Pattern: user departure cleanup

**When to use:** A sales rep is terminated. Reassign all their open Accounts, Opportunities, and Cases to their manager before deactivating the user.

**How it works:** Query `OwnerId = '005...'` per object. Use Data Loader Update with a single OwnerId column. Run before deactivation — Salesforce blocks deactivation if the user owns active records or is referenced as a default owner.

**Why not the alternative:** Mass Transfer Records works for Accounts but won't transfer Cases or custom objects in one pass.

### Pattern: territory realignment via mapping CSV

**When to use:** 30 territories collapsing to 18; each old owner maps to a new owner.

**How it works:** Build CSV `OldOwnerId, NewOwnerId`. Per object, build a SOQL query joined to the mapping (in a spreadsheet or via Apex). Update OwnerId via Data Loader. Defer sharing recalculation in advance for large volumes.

### Pattern: queue ↔ user transfer

**When to use:** Cases sitting in a queue need to be assigned to a specific user.

**How it works:** OwnerId can be a Queue ID (starts with `00G`) or a User ID (starts with `005`). Update through Data Loader the same way, but verify the target object has Queue support enabled in Setup.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| <50k records, standard object, parent-with-children cascade desired | Mass Transfer Records | Built-in cascade, no scripting |
| Any object, CSV-driven mapping, no cascade | Data Loader Update | Cleanest for one-table-at-a-time |
| >250k records on one object | Apex Batch + deferred sharing recalc | Avoids row-lock and recalc timeouts |
| Need to suppress notifications and trigger logic | Apex with custom-setting flag your triggers honor | Tool-based transfers fire triggers and workflows |

---

## Recommended Workflow

1. Inventory: per-object record counts under the source-owner criteria. Write to a planning doc.
2. Choose the tool from the decision table above. If mixed (e.g., Accounts via Mass Transfer + Cases via Data Loader), document each step with its order.
3. Decide the cascade policy: do child Cases/Opportunities/Contacts follow the parent Account? Tick the Mass Transfer checkboxes accordingly, or queue follow-up Data Loader jobs for each child object.
4. Decide the trigger/workflow policy: turn off email notifications via the "Send Email" checkbox (Mass Transfer Records UI), or set a custom-setting flag your triggers honor to short-circuit during the migration.
5. For >100k on a single object, request Defer Sharing Calculations from Support before starting; resume recalc in a maintenance window.
6. Execute in a sandbox first; capture timing and any trigger errors.
7. Run in production with `AllOrNone=false` (Apex) or "Continue on error" (Data Loader) so a single bad record doesn't stop the batch. Capture the success+error CSVs as the audit trail.
8. Validate: rerun the source-owner query — should return zero. Verify a sample of child-record ownership matches expectation.

---

## Review Checklist

- [ ] Per-object volumes inventoried; tool chosen against the decision table
- [ ] Cascade policy explicit (children follow or stay)
- [ ] Notification policy explicit (suppress workflow emails during transfer)
- [ ] Triggers reviewed for OwnerId-change side effects (assignment rule re-fire, ownership-based sharing rule, etc.)
- [ ] Defer sharing recalc requested if volume warrants
- [ ] Rollback CSV captured (Old + New OwnerId by record ID) so a reverse update is one click
- [ ] Audit log saved (Data Loader success/error CSVs, or Apex DML log)

---

## Salesforce-Specific Gotchas

1. **User deactivation blocks if records remain** — Salesforce refuses to deactivate users who own active records or are listed as default queue/owner. Always transfer before deactivating.
2. **Sharing recalc can lock other writes** — On a 500k-record transfer, downstream sharing recalc can extend the lock; concurrent integrations may time out. Use deferred sharing recalc.
3. **Data Loader does not cascade ownership** — Updating Account.OwnerId leaves child Case.OwnerId untouched. Plan child object updates explicitly.
4. **OwnerId on a Queue is a `00G` prefix** — Some custom objects don't allow Queue ownership; check the object's "Allow Queues" before targeting `00G` IDs.
5. **AssignmentRuleHeader on the update toggles routing** — If you don't want assignment rules to fire during the migration, omit the header (Apex) or uncheck the Data Loader option.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Per-object volume inventory | Counts and source criteria for each object in scope |
| Transfer execution plan | Ordered list of tool runs with cascade and notification settings |
| Rollback CSV | record-id, old-owner-id, new-owner-id — re-runnable in reverse |
| Validation queries | SOQL that should return zero rows post-transfer |

---

## Related Skills

- admin/user-management — context on user deactivation pre-conditions and transfer-before-deactivate sequencing
- data/data-loader-batch-window-sizing — sizing the Data Loader batch parameter to keep sharing recalc tractable
- security/record-access-troubleshooting — when post-transfer users report missing records (sharing recalc not yet completed)
