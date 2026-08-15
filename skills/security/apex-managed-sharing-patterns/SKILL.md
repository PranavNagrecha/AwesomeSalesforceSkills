---
name: apex-managed-sharing-patterns
description: "Grant row-level access programmatically via __Share records when declarative sharing rules cannot express the policy. NOT for OWD, role hierarchy, or criteria-based sharing rule design — use admin/sharing-and-visibility."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "need to share records based on data from another object"
  - "grant access when a custom field flips to a value"
  - "reciprocal sharing between two users on a record"
  - "manual share using apex"
tags:
  - sharing
  - apex
  - row-level-security
inputs:
  - "Target SObject"
  - "policy rule describing who sees the record and why"
outputs:
  - "Apex class that maintains __Share rows with RowCause and access levels"
  - "tests proving access is granted and revoked"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Apex Managed Sharing Patterns

Apex managed sharing writes rows into an object's `__Share` table with a
developer-defined **Apex sharing reason**, so the platform maintains those rows
across owner changes instead of reclaiming them. It is the last mechanism in the
record-access model, reached only when org-wide defaults, the role hierarchy,
sharing rules, teams, and manual sharing cannot express the policy.

The one constraint that determines whether this skill applies at all:

> "Apex sharing reasons and Apex managed sharing recalculation are only available
> for custom objects."
> — Apex Developer Guide, *Understanding Sharing*

If the record needing programmatic access is an Opportunity, Account, Case, or any
other standard object, Apex managed sharing is **not available**. You can still
insert `OpportunityShare` rows from Apex, but they are user managed (manual)
shares with `RowCause = 'Manual'`, and the platform deletes them the moment the
record owner changes. Establish which side of that line you are on before
designing anything.

---

## Before Starting

Answer these four questions. Three of the four regularly kill the design.

1. **Is the target a custom object?** If not, Apex managed sharing is off the
   table. Route to the built-in team feature (`AccountTeamMember`,
   `OpportunityTeamMember`, `CaseTeamMember`), to criteria-based sharing rules, or
   accept manual-share lifecycle and plan the re-grant on owner change.

2. **Is the object on the detail side of a master-detail relationship?** Detail
   records have no `__Share` object at all; their access is derived from the master
   and the relationship's sharing setting. Changing that is a data-model migration,
   not a configuration change.

3. **What is the org-wide default?** A share row must grant access *more*
   permissive than the OWD or the platform rejects it. On a Public Read/Write
   object no share row of any level is valid, and on Public Read Only a `Read`
   share is rejected.

4. **Can a declarative mechanism still do this?** The Salesforce Security Guide
   allows "up to 300 total sharing rules for each object, including up to 50
   criteria-based or guest user sharing rules." Teams routinely reach for code
   long before they are anywhere near that. Read
   [`standards/decision-trees/sharing-selection.md`](../../../standards/decision-trees/sharing-selection.md)
   and cite the branch that sent you here.

---

## Core Concepts

### The share object

Every shareable object has a companion sObject. Standard objects use
`AccountShare`, `ContactShare`, `OpportunityShare`, `CaseShare`, `LeadShare`.
Custom objects use `MyObject__Share`. Every share row has four meaningful fields:

| Field | Notes |
|---|---|
| `ParentId` | The shared record's Id. Not updateable. On standard-object share sObjects this is named for the object, e.g. `OpportunityId`. |
| `UserOrGroupId` | Target user, public group, role-derived sharing group, or territory group. Not updateable. Cannot be an unauthenticated guest user. |
| `AccessLevel` | `Read`, `Edit`, or `All`. `All` is internal-only and cannot be granted. `None` exists on `AccountShare` only. On standard objects the field is named for the object, e.g. `OpportunityAccessLevel`. |
| `RowCause` | Why access was granted. Determines who may alter the row. Not updateable. |

### RowCause is the whole point

`RowCause` is what separates a share the platform maintains from a share the
platform throws away.

| Sharing type | `RowCause` value | Lifecycle |
|---|---|---|
| Owner | `Owner` | Platform-maintained |
| Role hierarchy | *(derived at runtime, no row)* | Not stored |
| Sharing rule | `Rule` | Rebuilt on recalculation |
| Opportunity/Account/Case team | `Team` | Platform-maintained |
| Territory rule | `TerritoryRule` | Platform-maintained |
| Implicit parent/child | `ImplicitParent` / `ImplicitChild` | Platform-maintained, not writable |
| Manual sharing | `Manual` | **Deleted when record owner changes** |
| Apex managed sharing | *developer-defined, e.g.* `Recruiter__c` | **Maintained when record owner changes or is deactivated** |

Manual shares written from Apex default to `RowCause = 'Manual'`, and the Apex
Developer Guide notes that "Only shares with this condition are removed when
ownership changes." That sentence is the entire business case for Apex managed
sharing.

### Apex sharing reasons

A sharing reason is metadata on the custom object with a label (shown in the
Reason column of the record's sharing detail) and a name used in code. Names
follow `MyReasonName__c` and are referenced as:

```apex
Schema.CustomObject__Share.RowCause.SharingReason__c
// e.g.
Schema.Job__Share.RowCause.Recruiter__c
```

Two operational facts about creating them:

- The **Apex Sharing Reasons** related list is Classic-only. The Apex Developer
  Guide: "Apex sharing reasons aren't available in Lightning Experience. Use
  Salesforce Classic to create sharing reasons within the UI." Deploy
  `SharingReason` metadata instead so the reason lives in source control.
- The name may contain only underscores and alphanumerics, must be unique in the
  org, must begin with a letter, must not end with an underscore, and must not
  contain two consecutive underscores.

### Permission to write shares

Writing `__Share` rows requires **Modify All Data** — quoted from the Apex Developer
Guide, with the consequences for a normal user's save path, in
[`references/gotchas.md`](references/gotchas.md).

This is not the same thing as `with sharing` / `without sharing`, which control
whether the *running user's* record access is enforced on queries and DML inside
the class. At API 67.0 database operations default to user mode and a bare class
defaults to `with sharing`; the correct construction is to leave the class
`with sharing` and make only the `__Share` DML explicit:

```apex
Database.insert(shares, false, AccessLevel.SYSTEM_MODE);
```

---

## Common Patterns

### Pattern A — trigger-driven grant and revoke

The default. A service class exposes `grantForRecords(List<SObject>)` and
`revokeForRecords(Set<Id>)`; an `after insert, after update` trigger calls both.
The revoke must filter on the application's own `RowCause` so it never deletes
`Owner`, `Rule`, `Team`, or end-user `Manual` rows. Full worked implementation in
[`references/examples.md`](references/examples.md), Example 1.

### Pattern B — asynchronous grant for bulk paths

When the fan-out is wide (one record shared to many users) or the load is an ETL
insert rather than an interactive save, move share DML into a Queueable or Batch
keyed on record Ids. A 200-record trigger batch sharing to 300 users each is
60,000 rows in one transaction, which exceeds the 10,000-record DML limit. Accept
the visible window in which the record exists and the access does not, and
document it.

### Pattern C — group sharing instead of user sharing

Share to a public group rather than to N users. One row per record per group
instead of N rows. The trade is that group membership becomes the thing you
maintain, and membership changes trigger their own asynchronous recalculation.
Prefer this above roughly 50 users per record.

### Pattern D — the recalculation class

A `Database.Batchable` class registered under **Object Manager → [object] → Apex
Sharing Recalculation** (Classic only). The platform runs it for you:

Changing a custom object's org-wide default re-runs every Apex recalculation class
registered against it — quoted and unpacked in
[`references/gotchas.md`](references/gotchas.md).

and, from the Security Guide, "When sharing is recalculated, Salesforce also runs
all Apex sharing recalculations." Without this class, an admin changing the OWD
silently destroys your access model. Treat it as mandatory.

---

## Decision Guidance

| Situation | Mechanism |
|---|---|
| Access follows record ownership | Nothing — the platform grants Full Access to the owner and the hierarchy above them |
| Access follows a field value, granted to a group or role | Criteria-based sharing rule |
| Access follows named users on a standard object | Built-in team (`AccountTeamMember` / `OpportunityTeamMember` / `CaseTeamMember`) |
| Access follows named users on a custom object, must survive owner change | **Apex managed sharing** with a custom sharing reason |
| Access follows named users, may be reclaimed on owner change | Manual share from Apex (`RowCause = 'Manual'`) — plan the re-grant |
| Access must be *removed* from users who would otherwise have it | Restriction rules, not sharing — sharing only grants |
| Target is an unauthenticated guest user | Guest user sharing rule — Apex cannot share to guests |

---

## Recommended Workflow

1. **Confirm the object is custom and its OWD is restrictive.** Verify the target
   sObject name ends in `__c`, is not the detail side of a master-detail
   relationship, and has an org-wide default of Private (or Public Read Only when
   you only grant Edit). If any of these fail, stop and route to the decision
   guidance table above.
2. **Create the Apex sharing reason as metadata**, one per distinct business
   reason for access, in `objects/<Object>__c/sharingReasons/<Reason>.sharingReason-meta.xml`.
   Deploy before the Apex that references it, or the class will not save.
3. **Write a service class with paired `grant` and `revoke`**, both bulk-safe,
   both scoped by `RowCause`, with the share DML in `AccessLevel.SYSTEM_MODE` and
   `Database.insert(..., false, ...)` so one bad row does not abort the batch.
   Treat `FIELD_FILTER_VALIDATION_EXCEPTION` mentioning `AccessLevel` as expected.
4. **Invoke from an `after insert, after update` trigger**, never `before` — the
   record has no Id in a before-insert context and `ParentId` is not updateable.
5. **Write the recalculation class** implementing `Database.Batchable<sObject>`
   and register it under Apex Sharing Recalculation. Add the registration to the
   sandbox post-refresh checklist.
6. **Test with `System.runAs`**, asserting both that the target user can query the
   record and that access disappears when the driving relationship is removed. A
   `__Share` row-count assertion proves nothing.

---

## Review Checklist

- [ ] Target object is custom; sharing reason metadata is in source control
- [ ] Org-wide default is more restrictive than every access level granted
- [ ] `grant` and `revoke` both exist; `revoke` filters on `RowCause`
- [ ] Trigger context is `after insert` / `after update`
- [ ] No DML inside a loop; `Database.insert(list, false, SYSTEM_MODE)` used
- [ ] `FIELD_FILTER_VALIDATION_EXCEPTION` on `AccessLevel` handled as non-error
- [ ] `Database.Batchable` recalculation class exists and is registered
- [ ] Tests use `System.runAs` and include a negative (revocation) assertion
- [ ] If Experience Cloud is or will be enabled: role-based group Ids use
      `RoleAndSubordinatesInternal`, not `RoleAndSubordinates`
- [ ] Fan-out per record measured; group sharing used where population is large

---

## Salesforce-Specific Gotchas

Full detail with quotes and reproduction conditions in
[`references/gotchas.md`](references/gotchas.md).

1. **Apex sharing reasons do not exist on standard objects.** The compile error on
   `Schema.OpportunityShare.RowCause.Anything__c` is the platform telling you the
   design is unavailable, not that a setting is missing.
2. **The sharing reason UI is Classic-only.** Lightning Experience never renders
   the Apex Sharing Reasons or Apex Sharing Recalculation related lists.
3. **A share not more permissive than the OWD is rejected** with
   `FIELD_FILTER_VALIDATION_EXCEPTION`. Relaxing an OWD converts every managed
   share in the org into an error.
4. **`AccessLevel.USER_MODE` on share DML works only for Modify All Data holders**
   — that is, in your admin sandbox but not for real users.
5. **An OWD change wipes shares** and re-runs registered Apex recalculation
   classes. No recalculation class means no rebuild.
6. **Unfiltered `__Share` deletes destroy other mechanisms' rows.** Rule rows come
   back on recalculation; end-user manual shares do not.
7. **Enabling digital experiences widens `RoleAndSubordinates` grants** to include
   portal subordinates automatically — an internal-only implementation becomes an
   external exposure with no code change.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Sharing policy statement | One sentence per reason: who gets access, at what level, driven by which field or relationship, and when it is withdrawn |
| `SharingReason` metadata | One file per reason under `objects/<Object>__c/sharingReasons/` |
| Share service class | Bulk-safe `grant` / `revoke` pair with `RowCause`-scoped DML and documented system-mode escape |
| Recalculation class + registration | `Database.Batchable` implementation plus the Object Manager registration step recorded in the post-refresh checklist |
| Access test class | `System.runAs` assertions covering grant, re-assignment, and revocation |

---

## Related Skills

- `security/dynamic-sharing-recalculation` — orchestrating recalculation windows
  around bulk loads and role reorgs, including Defer Sharing Calculations
- `security/record-access-troubleshooting` — diagnosing why one specific user can
  or cannot see one specific record
- `apex/apex-with-without-sharing-decision` — choosing the sharing keyword for the
  service class itself, which is a different question from share-row permission
