---
name: record-access-troubleshooting
description: "Diagnose why a user can or cannot see/edit a record: UserRecordAccess SOQL, Why Can a User Access This Record debug log, OWD, role hierarchy, sharing rules, manual/team/apex shares, implicit parent share. NOT for field-level security (use field-level-security-audit). NOT for designing sharing (use sharing-selection decision tree)."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
tags:
  - sharing
  - record-access
  - userrecordaccess
  - owd
  - troubleshooting
triggers:
  - "why can user see this record salesforce debug"
  - "userrecordaccess soql hasreadaccess hasedit"
  - "explain record access why user view edit"
  - "sharing rule not taking effect troubleshoot"
  - "manual share apex share missing record"
  - "owd private user cannot see record"
inputs:
  - User Id whose access is in question
  - Record Id in question
  - Expected access (view / edit / delete)
  - Object's OWD setting
outputs:
  - UserRecordAccess diagnostic query
  - Sharing chain trace
  - Remediation recommendation
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Record Access Troubleshooting

Activate when a user reports "I can't see this record" or "Why can this user edit this record?" Troubleshooting record access means tracing the sharing chain: OWD → role hierarchy → ownership → sharing rules → teams → manual shares → Apex shares → implicit parent share. This skill gives a deterministic diagnostic flow using `UserRecordAccess` SOQL and the "Sharing" access debug tool, not guesswork.

## Before Starting

- **Gather specifics.** User Id, Record Id, expected access (view/edit/delete), object OWD.
- **Identify the object's OWD.** Setup → Sharing Settings. Private / Public Read Only / Public Read/Write / Controlled by Parent.
- **Check profile/permset modify-all.** "Modify All Data" and "View All Data" bypass sharing entirely.

## Core Concepts

### UserRecordAccess (primary diagnostic)

```
SELECT RecordId, HasReadAccess, HasEditAccess, HasDeleteAccess,
       HasTransferAccess, HasAllAccess, MaxAccessLevel
FROM UserRecordAccess
WHERE UserId = '005...' AND RecordId = '001...'
```

Returns the effective access result but not the reason. Run this first.

### Explain Access button

On any record's Sharing detail page: "Why can this user access this record?" — lists the reason (Owner, Role Hierarchy, Sharing Rule X, Manual Share, Apex Managed Share, Implicit Parent). Available in Classic UI; Lightning has "Sharing Hierarchy."

### Sharing reason chain (order Salesforce evaluates)

1. **Admin bypass.** "View All Data" / "Modify All Data" / "View All" / "Modify All" on an object.
2. **Ownership.** The record owner has full access (unless the role says otherwise).
3. **Role hierarchy.** If enabled on the object, users above the owner's role inherit access.
4. **Sharing rules.** Ownership- and criteria-based rules grant read or read/write.
5. **Teams.** Account, Opportunity, Case teams.
6. **Manual shares.** UI "Share" button.
7. **Apex managed shares.** `__Share` rows with RowCause.
8. **Implicit parent share.** Child records on master-detail inherit parent access.
9. **Restriction rules.** Filter DOWN access — user might have access via the above but restriction rule denies.

### __Share objects

For every object with non-Public OWD, there's a `<Object>__Share` sharing table. Query it to see grants:

```
SELECT UserOrGroupId, AccessLevel, RowCause FROM Account__Share WHERE ParentId = '001...'
```

`RowCause`: Owner, Manual, Rule, Team, Implicit, <ApexRowCause>, etc.

### Restriction Rules

New-style restrictive filter on top of OWD. A user might have share access but see 0 rows because a restriction rule filters the query.

## Common Patterns

### Pattern: Minimal diagnostic query

```
SELECT RecordId, HasReadAccess, HasEditAccess, MaxAccessLevel
FROM UserRecordAccess
WHERE UserId = :uid AND RecordId = :rid
```

`MaxAccessLevel` returns "None", "Read", "Edit", "All".

### Pattern: Trace via __Share table

```
SELECT Id, UserOrGroupId, AccessLevel, RowCause, ParentId
FROM Account__Share
WHERE ParentId = :rid
ORDER BY RowCause
```

Join against Group / User to resolve the grantee.

### Pattern: Admin bypass check

```
SELECT PermissionsViewAllData, PermissionsModifyAllData
FROM PermissionSetAssignment
WHERE AssigneeId = :uid
```

If either is true, sharing is moot — explain the finding.

## Decision Guidance

| Symptom | Likely cause |
|---|---|
| User sees record they shouldn't | View All Data perm / sharing rule / role hierarchy |
| User can't see record they should | OWD Private + no sharing rule match |
| Sharing rule configured but no effect | Rule targets criteria user's records don't match |
| Lost access after ownership change | Manual shares cleared on transfer (not Apex shares with RowCause) |
| Child record inaccessible | Master-detail parent not shared (implicit parent) |
| Recent access removed | Restriction rule introduced |

## Recommended Workflow

1. Query `UserRecordAccess` for the user/record pair. Confirms current state.
2. If access is unexpected, check profile/permset for View/Modify All.
3. Open the record's Sharing detail → "Why can this user access?" — get the explicit reason.
4. Query `__Share` filtered by ParentId — enumerate all grants.
5. Check role hierarchy: `UserRole` of owner vs accessor.
6. Check for restriction rules on the object.
7. Document root cause and remediation (add sharing rule / remove permission / adjust OWD).

## Review Checklist

- [ ] `UserRecordAccess` query run first to confirm state
- [ ] Admin-bypass permissions ruled in/out
- [ ] `__Share` RowCause chain enumerated
- [ ] Role hierarchy relationship checked
- [ ] Restriction rules checked for the object
- [ ] Implicit-parent-share considered for child objects
- [ ] Remediation aligns with `sharing-selection` decision tree

## Salesforce-Specific Gotchas

1. **Manual shares disappear on ownership change.** Re-create as Apex managed share with a RowCause (survives transfer).
2. **"Grant Access Using Hierarchies" is per-object and defaults on.** Turning off for custom objects with Private OWD blocks role-based visibility.
3. **`UserRecordAccess` requires the query user to have `View All Data` OR be the target user.** Running as a sandbox admin works; running as a normal user impersonating will fail.
4. **Restriction Rules apply AFTER sharing is computed** — user may have a `__Share` row yet still see zero results.

## Output Artifacts

| Artifact | Description |
|---|---|
| UserRecordAccess diagnostic query | Drop-in SOQL for user/record pair |
| __Share trace query | Enumerates grant rows and causes |
| Sharing-chain narrative | Step-by-step reason write-up |
| Remediation recommendation | Cite `sharing-selection` branch |

## Related Skills

- `security/sharing-rules-patterns` — designing new sharing rules
- `security/apex-managed-sharing` — `__Share` inserts with RowCause
- `security/restriction-rules-patterns` — filter-down access
- `standards/decision-trees/sharing-selection.md` — overall sharing technology selection
