---
name: record-access-troubleshooting
description: "Diagnose why a user can or cannot see/edit a record: UserRecordAccess SOQL, Why Can a User Access This Record debug log, OWD, role hierarchy, sharing rules, manual/team/apex shares, implicit parent share. NOT for remediating a CRUD/FLS finding — use apex/apex-stripinaccessible-and-fls-enforcement. NOT for designing the sharing model itself — use admin/sharing-and-visibility."
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
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-08-01
---

# Record Access Troubleshooting

Reach for this the moment someone says "this record won't show up for me" — or the inverse, "why on earth can this user edit that?" It walks the sharing chain in a fixed order using a `UserRecordAccess` query plus the Sharing debug tool, so the answer comes from evidence rather than from guessing which grant fired.

## Before Starting

- Have four things in hand: the User Id, the Record Id, the access level the user expected, and the object's org-wide default (Setup → Sharing Settings).
- Rule out the blunt instruments first. "Modify All Data" and "View All Data" on the profile or a permission set skip the sharing model altogether, and no amount of tracing rules will explain access that came from one of them.

## Core Concepts

### UserRecordAccess (primary diagnostic)

```
SELECT RecordId, HasReadAccess, HasEditAccess, HasDeleteAccess,
       HasTransferAccess, HasAllAccess, MaxAccessLevel
FROM UserRecordAccess
WHERE UserId = '005...' AND RecordId = '001...'
```

Start here. It tells you what access the user effectively has, though not where that access came from.

### Finding out *why* access was granted

For the *why*, open the record's Sharing detail and use "Why can this user access this record?", which names the grant responsible. Classic exposes it as a dedicated button; in Lightning the equivalent lives under "Sharing Hierarchy."

### The order access is evaluated in

Access accumulates down this list, so trace it in order and stop at the first thing that accounts for what you observed:

1. Administrative bypass — View All Data / Modify All Data, or their object-level counterparts
2. Record ownership
3. The role hierarchy, but only where "Grant Access Using Hierarchies" is switched on for the object
4. Sharing rules, both ownership-based and criteria-based
5. Team membership — Account, Opportunity, and Case teams
6. Shares granted by hand
7. Apex managed shares, visible as `__Share` rows carrying a RowCause
8. Implicit shares inherited from a master-detail parent
9. Restriction rules, which run the other way: they subtract, and can deny access that everything above just granted

### __Share objects

Every object with a non-Public OWD has a share object, but **standard and custom objects
name their share object and its fields differently** — getting this wrong is the most common
reason a diagnostic query fails to compile.

| | Standard object | Custom object |
|---|---|---|
| Share object | `AccountShare`, `OpportunityShare`, `CaseShare` — append `Share`, no underscores | `Project__Share` — replace the `__c` suffix with `__Share` |
| Parent lookup field | `AccountId`, `OpportunityId`, `CaseId` — `<Object>Id` | `ParentId` |
| Access level field | `AccountAccessLevel`, `OpportunityAccessLevel` — `<Object>AccessLevel` | `AccessLevel` |
| Custom Apex sharing reason | **Not available** | Available |

```
-- Standard object
SELECT UserOrGroupId, AccountAccessLevel, RowCause FROM AccountShare WHERE AccountId = '001...'

-- Custom object
SELECT UserOrGroupId, AccessLevel, RowCause FROM Project__Share WHERE ParentId = 'a01...'
```

`RowCause` values: Owner, Manual, Rule, Team, Implicit, and — **on custom objects only** —
a declared Apex sharing reason. The Apex Developer Guide states plainly: "Apex sharing reasons
and Apex managed sharing recalculation are only available for custom objects."
`Account__Share` does not exist in any org.

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
-- Standard object (note AccountId / AccountAccessLevel, not ParentId / AccessLevel)
SELECT Id, UserOrGroupId, AccountAccessLevel, RowCause, AccountId
FROM AccountShare
WHERE AccountId = :rid
ORDER BY RowCause

-- Custom object
SELECT Id, UserOrGroupId, AccessLevel, RowCause, ParentId
FROM Project__Share
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
- [ ] If a restriction rule is the control, every Apex/Flow entry point to the object has been confirmed to run in user mode — restriction rules aren't applied for code executed in System Mode
- [ ] Implicit-parent-share considered for child objects
- [ ] Remediation aligns with `sharing-selection` decision tree

## Salesforce-Specific Gotchas

1. **Manual shares disappear on ownership change.** Re-create as Apex managed share with a RowCause (survives transfer).
2. **"Grant Access Using Hierarchies" is per-object and defaults on.** Turning off for custom objects with Private OWD blocks role-based visibility.
3. **`UserRecordAccess` requires the query user to have `View All Data` OR be the target user.** Running as a sandbox admin works; running as a normal user impersonating will fail.
4. **Restriction Rules apply AFTER sharing is computed** — user may have a `__Share` row yet still see zero results. They are also bypassed entirely in System Mode, and by `View All Records`/`View All Data`/`Modify All Records`/`Modify All Data`.

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
