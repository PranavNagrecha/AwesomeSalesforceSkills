---
name: mass-transfer-ownership
description: "Use when re-assigning record OwnerId across many records — territory realignment, employee departure, region split, integration cleanup. Triggers: 'mass transfer accounts', 'reassign opportunities to new owner', 'transfer all records on user deactivation', 'OwnerId migration', 'mass transfer records tool', 'bulk owner change', 'transfer before deactivating user', 'account team lost after owner change', 'assignment rule overrode my OwnerId column', 'defer sharing calculations', 'roll back an owner transfer'. NOT for auto-assigning new records — use admin/assignment-rules. NOT for territory assignment data — use data/territory-data-alignment."
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
  - "reassign all open opportunities from a departing sales rep"
  - "account team members disappeared after we changed the account owner"
  - "data loader owner update fired the assignment rule and re-routed the cases"
  - "users still cannot see the records they now own after a mass transfer"
  - "bulk update OwnerId for 100k records without locking the org"
  - "roll back a mass owner transfer that went to the wrong user"
  - "previous owner can still see opportunities we transferred away from them"
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
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Mass Transfer Ownership

Activate when an admin needs to move a non-trivial volume of records (typically >100, often tens of thousands) from one or more current owners to one or more new owners. The skill produces a transfer plan covering tool selection, child-record cascading rules, sharing recalculation timing, and a rollback path.

---

## Before Starting

Gather this context before working on anything in this domain:

- Volume per object (Accounts, Opportunities, Contacts, Cases, custom objects). Above ~250k records on a single object, sharing recalc dominates the timeline and a maintenance window is required. UNVERIFIED (2026-09-04): the ~250k figure is a practitioner heuristic, not a published limit — no Salesforce limit document states a record count at which recalculation becomes the bottleneck, because it depends on the org's sharing rule count, role depth, and group membership. Measure it in a full sandbox rather than trusting the number.
- Whether the transfer is a single-source-to-single-target swap, a many-to-many remap (e.g., a CSV mapping old owner → new owner), or a queue-to-user / user-to-queue move. Each uses different tooling.
- Whether child records should follow. Account.OwnerId reassignment can optionally cascade to child Cases and Opportunities through the Mass Transfer tool's checkboxes; Data Loader does not cascade — every child object must be transferred explicitly.
- Whether the org has Apex triggers, validation rules, or workflow rules that fire on Owner change. These can fail or send unwanted notifications during a 50,000-record transfer.

---

## Questions to Ask Before Configuring

Ask all seven before a single row is written. Each one maps to a documented platform behaviour
in `references/gotchas.md`; skipping one does not remove the behaviour, it just means the tool
decides for you.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which objects are in scope, and must the children follow the parent?" | No API path cascades. Each child object is a separate job, and the order matters. | The ordered job list, parents before children |
| "Does the incoming owner already have read access to the parent Accounts?" | A child transfer fails without it, and access errors from bulk operations are not logged at all — you get failures with no diagnostic trail (Gotcha 8) | A `UserRecordAccess` sample of 200 parents and a parents-first sequence |
| "Do Account or Opportunity team members have to survive the move?" | The two objects behave differently and neither behaves the way admins expect (Gotchas 6, 7) | A team snapshot taken beforehand, plus a re-add step or a written acceptance |
| "Should assignment rules fire during the transfer?" | On Case and Lead, the Data Loader assignment-rule setting discards the `OwnerId` column you built (Gotcha 9) | A per-tool setting recorded in the run sheet and verified against `success.csv`, not the row count |
| "Must the new owner be notified by email?" | The Bulk API job body has no email header; only Apex `DMLOptions` can send it | A tool choice driven by the notification requirement, not by volume alone |
| "What is the org-wide default per object, and is deferred sharing calculation available yet?" | The feature is off until Salesforce Support enables it, and resuming is the slow half (Gotcha 13) | A support case with lead time, and a window sized for the resume rather than the write |
| "What triggers a rollback, and who calls it?" | Re-running the CSV restores `OwnerId` and nothing else | A pre-captured `Id, Old_OwnerId` file plus an explicit list of what rollback cannot undo |

What a proper configuration adds over just doing it: the transfer moves exactly the records you
intended, with the team memberships, notifications, and assignment-rule behaviour you chose
rather than the ones each tool defaults to, and a rollback that is a column swap instead of an
investigation.

---

## Core Concepts

### Tool selection

| Tool | Best for | Limit |
|---|---|---|
| Setup → Data Management → Mass Transfer Records | <50k records on standard objects (Accounts, Leads, Opportunities), simple one-to-one reassignment, with cascade-to-children checkboxes | UI-only, no CSV mapping; many-to-many requires repeated runs |
| Data Loader Update | Any object, any volume, mapping CSV | No cascade — each child object is its own job; emits triggers and workflow |
| Apex (`Database.update` with `AllOrNone=false`) | Many-to-many remap with conditional logic, suppression of email notifications, batched sharing recalc | Requires careful governor-limit-aware batching |
| Anonymous Apex Batch (`Database.Batchable`) | Large volumes where sharing recalc would otherwise lock the org (the ~250k rule of thumb is unverified — see Before Starting); also the only path that can send the new-owner email | Asynchronous; needs progress monitoring. Default scope 200, `QueryLocator` scope max 2,000, 50 million record ceiling |

### Sharing recalculation

Owner changes trigger sharing recalculation for the record and its children if the org-wide default is not Public Read/Write. On large objects, recalc can extend the transaction by hours.

Deferral is real and deployable: `SharingSettings` exposes `deferGroupMembership` and `deferSharingRules` (API version 49.0 and later), and the Metadata API guide is explicit that "the defer sharing calculation feature isn't enabled by default. To enable it for your Salesforce org, contact Salesforce Customer Support." Setting either flag back to `false` automatically recalculates, and that recalculation "can take a significant amount of time to complete" — so the maintenance window belongs around the resume, not the write. The deploy artefact is in `references/metadata-examples.md` §5.

The ">100k records" trigger point for reaching for deferral is a heuristic. UNVERIFIED (2026-09-04): no Salesforce document names a volume at which deferral becomes necessary; the guides describe the feature and its cost but not a threshold. Treat 100k as a prompt to measure, not a rule.

### Ownership-change side effects the platform applies for you

An `OwnerId` update is not a field write. Four things happen alongside it, and only one of them
is optional:

| Effect | What the docs say |
|---|---|
| Share rows rewritten | The `Owner` row cause on the share table is read-only and maintained by the platform; it is rebuilt for the new owner and, above tens of thousands of rows, asynchronously |
| Previous Opportunity owner keeps read access | Their access falls to Read Only or the org-wide default, whichever is greater — the API gives you no say; the UI does, when they are on the opportunity team |
| Account team members can be dropped | Members added by a user whose access was group-based are removed on owner change, even with Keep Account Team enabled |
| Full save order re-runs, per record | Before-save flows, validation rules, duplicate rules, triggers, assignment rules, workflow, escalation, after-save flows, roll-up recalculation, and criteria-based sharing evaluation |

Only the assignment-rule step and the new-owner email are things you control. The rest are
platform behaviour — plan around them rather than trying to switch them off. Full grounding and
the failure each one produces is in `references/gotchas.md`.

### Cascade behavior

API-driven updates (Data Loader, Bulk API, Apex) do **not** cascade. If you want child records to follow the parent through the API, you must update each child object as a separate operation, parents first — the child counts in `references/metadata-examples.md` §1f tell you how many jobs that is.

The Setup Mass Transfer Records wizard is the exception, through its "Transfer …" checkboxes. UNVERIFIED (2026-09-04): the wizard's checkbox set — transfer open opportunities, open activities, notes and attachments, and which child objects each covers — is not described in the v62 Object Reference, Metadata API, Apex, Data Loader, Bulk API or App Limits PDFs. What the Object Reference does document is `OwnerChangeOptionInfo`: "Represents default and optional actions that can be performed when a record's owner is changed. Available in API version 35.0 and later, but to query for change owner metadata, use the OwnerChangeOptionInfo object in Tooling API instead." Query that object in the target org to see the options your objects actually expose, rather than assuming the checkbox list.

---

## Common Patterns

### Pattern: user departure cleanup

**When to use:** A sales rep is terminated. Reassign all their open Accounts, Opportunities, and Cases to their manager before deactivating the user.

**How it works:** Query `OwnerId = '005...'` per object. Use Data Loader Update with a single OwnerId column. Run before deactivation. UNVERIFIED (2026-09-04): the claim that Salesforce *blocks* deactivation while the user owns active records is not stated in the Object Reference's `Deactivate Users` section or in any other v62 PDF checked; that section documents only that users can never be deleted and that Chatter subscriptions are soft-deleted. What it does state, and what matters here, is that "the user interface provides options to auto-remove a user from teams, but the removal isn't supported in API" — so an API-driven offboarding leaves the departing user on every account and opportunity team unless you delete those rows yourself. Sequence the transfer first regardless: it is the order that produces a clean result, whether or not the platform enforces it.

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

1. **Size it with the impact query set.** Run all seven queries in
   `references/metadata-examples.md` §1 — volume by owner, open vs closed, team rows,
   queue-owned rows, which objects even accept a queue owner, child counts that will not follow,
   and a `UserRecordAccess` transfer-access sample. Record every count in
   `templates/mass-transfer-ownership-template.md` §2, including the zeros you verified.
2. **Answer the seven questions above and fix the four policies** — cascade, teams,
   notification, assignment rules. Read `references/gotchas.md` 6, 7, 9 and 12 first; each
   describes a side effect that only becomes visible after the transfer, when it is expensive.
   Write the decisions into run sheet §3, per tool.
3. **Build and lint the plan file.** Export `Id, OwnerId, Old_OwnerId` per object — the
   `Old_OwnerId` column is the rollback, and it only exists if you capture it before the write.
   Then run `python3 scripts/check_mass_transfer_ownership.py --plan <file>`, which fails on
   duplicate ids, mixed key prefixes (two objects in one file), an owner that is neither `005`
   nor `00G`, and a missing rollback column. Snapshot the team objects in the same pass.
4. **Prepare the sharing window.** Retrieve `Sharing.settings` to source control, then apply the
   deferral flags from `references/metadata-examples.md` §5 if the volume and org-wide defaults
   warrant it. Suspend group membership last; you cannot change `deferSharingRules` while it is
   suspended. Schedule the window around the resume, not the write.
5. **Rehearse in a full sandbox, then execute parents before children.** Use the Bulk API 2.0
   job in §2 or the `process-conf.xml` bean in §3; move to the Batch Apex class in §4 when the
   run needs conditional logic or the new-owner email. Capture the job result files the same
   day — they are gone in seven.
6. **Verify with the §6 query set** and confirm Background Jobs holds no remaining sharing
   recalculation. Resume the deferral flags and re-check. `HasReadAccess = false` for the new
   owner means recalculation has not drained, not that the transfer failed.
7. **Close out the run sheet** — execution log, validation results, and §8 deviations, naming
   every side effect a rollback would not undo.

## Review Checklist

- [ ] Per-object volumes inventoried; tool chosen against the decision table
- [ ] Cascade policy explicit (children follow or stay)
- [ ] Notification policy explicit (suppress workflow emails during transfer)
- [ ] Triggers reviewed for OwnerId-change side effects (assignment rule re-fire, ownership-based sharing rule, etc.)
- [ ] Defer sharing recalc requested if volume warrants
- [ ] Rollback CSV captured (Old + New OwnerId by record ID) so a reverse update is one click
- [ ] Plan CSV linted clean: `python3 scripts/check_mass_transfer_ownership.py --plan <file>`
- [ ] Team membership snapshot taken (`AccountTeamMember`, `OpportunityTeamMember`) before the write
- [ ] New owner's read access to the in-scope parent Accounts sampled via `UserRecordAccess`
- [ ] Audit log saved (Data Loader success/error CSVs, or Apex DML log), and Bulk API job results pulled within the seven-day window

---

## Salesforce-Specific Gotchas

1. **Deactivation does not clean up after itself** — the UI can auto-remove a departing user from teams; the API cannot, so an API offboarding leaves stale team rows behind. Always transfer, then strip team memberships, then deactivate. (See the departure pattern above for what is and is not documented about deactivation being blocked.)
2. **Sharing recalc can lock other writes** — On a 500k-record transfer, downstream sharing recalc can extend the lock; concurrent integrations may time out. Use deferred sharing recalc.
3. **Data Loader does not cascade ownership** — Updating Account.OwnerId leaves child Case.OwnerId untouched. Plan child object updates explicitly.
4. **OwnerId on a Queue is a `00G` prefix** — Some custom objects don't allow Queue ownership; check the object's "Allow Queues" before targeting `00G` IDs.
5. **AssignmentRuleHeader on the update toggles routing** — If you don't want assignment rules to fire during the migration, omit the header (Apex) or uncheck the Data Loader option.
6. **A transferred Opportunity stays visible to its old owner** — the previous owner keeps read access by design, and stays on the opportunity team when one exists. Revoking visibility is a separate pass.
7. **Account team members can vanish even with Keep Account Team on** — it depends on who added them. Snapshot before, diff after.

The full set, with the documented behaviour and the failure each produces, is in
`references/gotchas.md` (14 entries).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Per-object volume inventory | Counts and source criteria for each object in scope |
| Transfer execution plan | Ordered list of tool runs with cascade and notification settings |
| Rollback CSV | record-id, old-owner-id, new-owner-id — re-runnable in reverse |
| Validation queries | SOQL that should return zero rows post-transfer |
| Team snapshot | `AccountTeamMember` / `OpportunityTeamMember` rows exported before the write, for the post-transfer diff |
| Sharing deferral deploy | `Sharing.settings` with the two defer flags, retrieved before and restored after |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are about to run something: the impact query set, the Bulk API 2.0 job payload, the `process-conf.xml` bean, the Batch Apex class, the `Sharing.settings` deferral deploy, the verification queries, and the rollback plan |
| `references/gotchas.md` | Deciding the four policies, or explaining a transfer that "worked" but produced the wrong result — 14 documented behaviours with the failure each one causes |
| `references/examples.md` | You want a worked end-to-end run: a same-day departure and a 30-to-18 territory realignment, plus what the parallel-mode failure looks like in the error CSV |
| `references/well-architected.md` | Justifying the tool choice, the deferral decision, or the notification policy to a reviewer — and for the source list behind every claim in this package |
| `references/llm-anti-patterns.md` | Reviewing a transfer runbook an assistant generated, before anyone runs it |
| `templates/mass-transfer-ownership-template.md` | Starting a real transfer — the run sheet that becomes the audit trail |
| `scripts/check_mass_transfer_ownership.py` | Before every load: lints the plan CSV for duplicate ids, mixed objects, bad owner prefixes, and a missing rollback column |

---

## Related Skills

- `admin/user-management` — the offboarding checklist this transfer sits inside, and why deactivation is blocked until it completes
- `admin/enterprise-territory-management` — territory realignment is a different operation: it moves `UserTerritory2Association` rows, not `OwnerId`, and the two are often confused in the same request
- `admin/data-import-and-management` — Data Loader and Bulk API mechanics in general, including the Account Teams caveat that constrains §3 here
- `admin/sharing-and-visibility` — the sharing model this transfer perturbs: org-wide defaults, row causes, and what recalculation actually rebuilds
- `data/data-loader-and-tools` — choosing and configuring the loader itself
- `data/bulk-api-and-large-data-loads` — job sizing, batching, and the allocation budget for very large transfers
- `data/data-loader-batch-window-sizing` — sizing the batch parameter so sharing recalculation stays tractable
- `apex/batch-apex-patterns` — the batch scaffolding behind the §4 class, when the transfer needs code
- `security/record-access-troubleshooting` — when post-transfer users report missing records and you need to prove it is recalculation lag rather than a broken transfer
