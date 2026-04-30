---
name: lookup-filter-cross-object-patterns
description: "Use when designing or repairing lookup filters that constrain a child lookup using fields from the parent record (or a sibling record on the same object). Triggers: 'limit lookup based on another field', 'cross-object lookup filter', 'lookup filter $Source vs $User'. NOT for filter logic on report types, list views, or duplicate matching rules."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - User Experience
triggers:
  - "lookup filter not narrowing the picker results"
  - "how do I limit a contact lookup to the account's contacts only"
  - "lookup filter referencing parent field stopped working after deploy"
  - "$Source field versus parent record field in lookup filter"
  - "required lookup filter blocking save on existing records"
tags:
  - lookup-filter
  - data-integrity
  - admin
  - cross-object
inputs:
  - "object and field names of the lookup, the parent (or related) object, and the constraint expression"
  - "whether the filter is required (block save) or optional (informational)"
  - "user profiles that should be exempt"
outputs:
  - "lookup filter definition snippet"
  - "rollout plan covering existing records that may now violate the filter"
  - "list of field-level visibility prerequisites"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-30
---

# Lookup Filter Cross Object Patterns

Activate when a user lookup picker shows too many records, when a filter referencing a parent field returns nothing, or when a deploy of a lookup filter blocks legitimate saves on existing data. The skill produces a Salesforce-compliant lookup filter definition, a backfill plan for legacy records that violate the new filter, and a profile-exemption strategy.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which object owns the lookup, which object the lookup points to, and what field on a *third* object you want to filter against. Cross-object filters can reference the parent of the source record (`$Source.Account.Region__c`) or a sibling record on the target's parent — but not arbitrary unrelated objects.
- Whether the filter must be **required** (block save) or **optional** (informational warning). Required filters are enforced for API and Apex saves; optional filters only narrow the lookup search dialog in the UI.
- Whether the org already has records whose current lookup value would fail the new filter. Required filters do not retroactively invalidate stored data, but they do block the next save until the value is corrected.

---

## Core Concepts

### `$Source` versus parent record reference

Lookup filters use `$Source` to refer to the record being edited (the *source* of the lookup). `$Source.AccountId` refers to a field on that record; `$Source.Account.Industry` traverses one level to the parent. The right-hand side can reference fields on the lookup's *target* record (no prefix needed — the field name is interpreted on the target object) or `$User` for the running user, `$Profile`, or `$Organization`. This three-axis grammar is the entire surface area; you cannot write SOQL or formula functions.

### Required versus optional filter

A required filter rejects saves that violate it (UI, API, Apex, Flow). An optional filter only filters the lookup dialog's search results — users can still type a record ID directly or paste a value via integration and the save will succeed. Optional filters are "guidance"; required filters are "enforcement."

### Field-level security and admin bypass

The admin bypass setting on the filter ("System administrators can bypass") only exempts the **System Administrator** profile, not custom admins. Granting "Modify All Data" on a permission set does not bypass the filter. Plan profile-by-profile rollout when the constraint is data-quality, not security.

---

## Common Patterns

### Pattern: child contact must belong to the case's account

**When to use:** Case.ContactId should only allow contacts on the same account as Case.AccountId.

**How it works:** On Case.ContactId, set filter `Contact.AccountId equals $Source.AccountId`. Mark required. Hide the contact lookup until the account is set, or use a validation rule to enforce ordering.

**Why not the alternative:** A validation rule alone fires only on save; the lookup picker still shows all contacts, so users keep picking wrong ones and getting save errors.

### Pattern: lookup constrained by current user's region

**When to use:** Opportunity.Account_Manager__c should only allow users whose region matches the opportunity owner's region.

**How it works:** Filter `User.Region__c equals $Source.Owner.Region__c`. Optional during data migration; switch to required after backfill.

### Pattern: temporary opt-out via profile bypass

**When to use:** A new required filter would block 12,000 legacy records on save.

**How it works:** Add a "Data Migration" profile to the bypass list. Migrate the bypass profile users only for the duration of cleanup, then remove the bypass.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Filter must enforce a data integrity rule across all entry points | Required + admin bypass off | API and Apex respect required filters |
| Filter exists to declutter the picker, not enforce | Optional | Users can still pick a record ID; no save-time enforcement is intended |
| The right-hand side needs a complex calc | Add a formula field on the source object, then reference it | Filters cannot call functions |
| Existing records will violate the new required filter | Stage as optional → backfill → flip to required | Required filters block the next save on any non-conforming record |

---

## Recommended Workflow

1. Identify the source object/field, the lookup target, and the third field providing the constraint. Confirm the relationship path is at most one hop on either side — lookup filters cannot traverse two-hop paths.
2. Write the filter as optional first. Deploy and use a report to count records that would fail if it became required.
3. If the failing-record count is non-zero, build a backfill (Data Loader, scheduled flow, or one-off Apex) before flipping to required.
4. Decide the admin-bypass policy. Default it OFF unless the team has a documented data-loading exception.
5. Migrate to required. Verify Profile-level field-level-security on every referenced field — the running user must be able to read every field cited on either side of the filter.
6. Document the filter in the data dictionary alongside the relationship; future deletions of referenced fields will cascade-fail without warning.

---

## Review Checklist

- [ ] Source, target, and constraint fields all readable by every profile that should save the source object
- [ ] Filter tested with a non-admin profile (admin bypass masks bugs)
- [ ] Existing records that violate the new filter counted and backfilled before flipping to required
- [ ] Filter logic survives a parent-record change — re-saving the source after parent edit still passes
- [ ] Deletion of any referenced field is gated by impact analysis (filter will silently break)

---

## Salesforce-Specific Gotchas

1. **Required filter only blocks the *next* save** — Existing non-conforming records sit fine until someone edits them, then fail. Surprise savings outages happen weeks after deploy.
2. **`$Source` does not traverse two parents deep** — `$Source.Account.Owner.Region__c` is rejected at design time. Add a formula field on Account that flattens the value first.
3. **Admin bypass is profile-scoped, not permission-set-scoped** — A user on a "Data Loader User" profile with PermissionSet "Modify All Data" still hits the filter unless their *profile* has bypass.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Lookup filter definition | The filter expression in `$Source.X` / target / `$User` grammar plus required/optional flag |
| Backfill plan | Report ID + Data Loader steps to fix legacy violators before flipping to required |
| Profile bypass log | Which profiles have admin bypass and why, for audit |

---

## Related Skills

- admin/validation-rules — when the constraint must run on every save regardless of UI path
- data/soql-query-optimization — when a related "filter by lookup" query becomes slow because of the extra join
