---
name: privileged-access-management
description: "Design just-in-time elevation, break-glass accounts, and audit trails for Modify All Data / System Admin / Customize Application permissions. NOT for regular permission set design."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "system admin break glass account"
  - "too many modify all data users"
  - "just in time admin elevation"
  - "root account security salesforce"
tags:
  - pam
  - admin
  - sod
  - audit
inputs:
  - "Current admin user list"
  - "audit log retention capability"
outputs:
  - "PAM runbook"
  - "permission-set-group rotation policy"
  - "break-glass procedure"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-07-31
---

# Privileged Access Management (PAM)

PAM on Salesforce is three things: knowing exactly who holds admin-equivalent permissions today, replacing standing grants with elevation that ends by itself, and being able to prove both after the fact. The platform ships every primitive you need — `PermissionSetAssignment.ExpirationDate`, session-based permission set groups, `SetupAuditTrail` — but each has a documented behaviour that breaks a naive audit. The most common failure is an inventory query that returns a clean result because it silently excluded the rows that mattered.

---

## Before Starting

- Confirm the **Permission Set & Permission Set Group Assignments with Expiration Dates** setting is enabled. Without it, `ExpirationDate` is not the control you think it is.
- Confirm what "admin" means in this org. It is rarely the System Administrator profile alone — see the admin-equivalent permission table below.
- Confirm log retention: `SetupAuditTrail` represents Setup changes for at least the last 180 days. Anything longer is an Event Monitoring plus archive problem.
- Confirm the org's break-glass identities exist, are named to individual humans, and are not shared.

---

## Core Concepts

### Every profile is also a permission set

Salesforce maintains one underlying permission set per profile, flagged `IsOwnedByProfile = true`. That single fact decides whether your inventory query is correct: because a user is assigned to their profile's permission set, a query over `PermissionSetAssignment` captures **both** profile-granted and permission-set-granted permissions. Adding `WHERE PermissionSet.IsOwnedByProfile = false` — a very natural-looking filter — deletes the profile half of your findings.

### Permissions that are admin-equivalent in practice

| Permission field (`PermissionSet.*`) | Why it is privileged |
|---|---|
| `PermissionsModifyAllData` | Read, edit, and delete every record of every object, bypassing sharing and most FLS |
| `PermissionsViewAllData` | Read every record of every object; sufficient for a full data exfiltration |
| `PermissionsCustomizeApplication` | Change metadata, including automation that can move data or grant access |
| `PermissionsManageUsers` | Create users, reset passwords, and reassign profiles — a route to any other permission |
| `PermissionsDataExport` / `PermissionsExportReport` | Bulk extraction paths that leave a different trail from record-level reads |
| `PermissionsApiEnabled` | Converts every permission above into a scriptable one |
| `PermissionsPasswordNeverExpires` | Turns a compromised credential into a permanent one |

Salesforce's own published admin-detection query treats **Customize Application AND Modify All Data** together as the admin signature; the wider privileged set is the OR of the first four.

### Assignment expiration is a soft delete, not a revocation

`PermissionSetAssignment.ExpirationDate` is a `dateTime` field, createable, filterable, and updateable. What happens at expiry is the part that catches people:

| Behaviour | Documented consequence |
|---|---|
| The assignment row | Expired assignments are treated as soft-deletes |
| Ordinary SOQL | Does not return user assignment information for assignments that have expired |
| Retrieving them anyway | Requires the `ALL ROWS` clause |
| The user | Remains assigned to the permission set or group, but cannot access its permissions |
| Other grants | Permissions from non-expiring permission sets, groups, or the profile still apply |
| What cannot expire | Profiles and permission set licenses — expiration is not supported for either |

The practical trap: an "expired elevations" report written as ordinary SOQL returns zero rows and reads as a clean bill of health.

### Session-based activation is the tightest elevation primitive

A permission set or permission set group marked **Session Activation Required** (`PermissionSetGroup.HasActivationRequired = true`, API 53.0+) grants nothing until it is activated for a specific session. Activation is represented by `SessionPermSetActivation` — "a permission set assignment activated during an individual user session" — which ties `UserId` and `PermissionSetId` / `PermissionSetGroupId` to an `AuthSessionId`. It is queryable but not insertable through the ordinary DML path; the supported activation route is the Flow core action **Activate Session-Based Permission Set**, and a single flow cannot both activate and deactivate — those are separate flows.

Compared with a four-hour `ExpirationDate`, session activation removes the window entirely: the grant dies with the session rather than at a wall-clock time the user may not still be present for.

### Permission set group recalculation can silently defer a grant

`PermissionSetGroup.Status` takes the values **Updated** (current), **Outdated** (requires recalculation), **Updating** (recalculating), and **Failed**. An elevation granted against a group that is `Outdated` or `Failed` does not deliver the permissions the requester expected, and there is no error on the assignment. Check `Status` as part of the grant, not as part of the post-mortem.

---

## Common Patterns

### Pattern 1: Standing-privilege inventory that does not lie

**When to use:** the first question in every PAM engagement — who actually holds admin-equivalent access right now.

```sql
-- Admin signature: Customize Application AND Modify All Data, from profile OR permission set
SELECT Assignee.Id, Assignee.Username, Assignee.Name,
       PermissionSet.Label, PermissionSet.IsOwnedByProfile, PermissionSet.Profile.Name
FROM PermissionSetAssignment
WHERE PermissionSet.PermissionsCustomizeApplication = true
  AND PermissionSet.PermissionsModifyAllData = true
  AND Assignee.IsActive = true
```

```sql
-- Wider privileged population: any one of the four high-impact permissions
SELECT Assignee.Id, Assignee.Username, Assignee.Name,
       PermissionSet.PermissionsModifyAllData, PermissionSet.PermissionsCustomizeApplication,
       PermissionSet.PermissionsManageUsers, PermissionSet.PermissionsViewAllData,
       PermissionSet.IsOwnedByProfile
FROM PermissionSetAssignment
WHERE (PermissionSet.PermissionsModifyAllData = true
       OR PermissionSet.PermissionsCustomizeApplication = true
       OR PermissionSet.PermissionsManageUsers = true
       OR PermissionSet.PermissionsViewAllData = true)
  AND Assignee.IsActive = true
```

`IsOwnedByProfile` is selected, never filtered — it tells you *how* each user got the permission so you know whether the remediation is a profile change or an assignment removal.

**Why not query `PermissionSet` alone:** that returns the permission sets that carry the permission, not the people who hold it. A permission set with the flag and zero assignees is not a finding.

### Pattern 2: Time-boxed elevation with an honest expiry report

**When to use:** a request-and-approve workflow grants an elevated permission set group for a fixed window.

```apex
// Grant. ExpirationDate is a dateTime, so a relative offset is valid.
insert new PermissionSetAssignment(
    AssigneeId          = requesterId,
    PermissionSetGroupId = elevatedGroupId,
    ExpirationDate      = System.now().addHours(4)
);
```

```sql
-- Review. Without ALL ROWS this returns nothing and looks clean.
SELECT Id, ExpirationDate, IsRevoked, Assignee.Name, PermissionSet.Name
FROM PermissionSetAssignment
WHERE ExpirationDate != null
ALL ROWS
```

Before granting, confirm the target group is usable:

```sql
SELECT Id, DeveloperName, Status, HasActivationRequired FROM PermissionSetGroup
WHERE DeveloperName = 'PAM_Elevated'
```

Anything other than `Status = 'Updated'` means the grant may not deliver what the requester asked for.

**Why not a custom revoke scheduler:** the platform expires the assignment for you, and a scheduled job that fails silently leaves standing privilege behind — the exact outcome PAM exists to prevent.

### Pattern 3: Break-glass that produces evidence

**When to use:** two named humans need a path to full admin when normal elevation is unavailable.

1. Two accounts, each mapped to one named person. Never shared — a shared account destroys attribution, which is the only thing break-glass is for.
2. MFA and network restrictions on both, and no standing membership in any other privileged group.
3. Detection on use, not on request: a Transaction Security policy on the Login event for those user IDs, notifying a channel the security team actually watches. `security/transaction-security-policies` owns the policy mechanics.
4. Every use opens a review with a mandatory `SetupAuditTrail` extract for the window, correlated with `LoginHistory` for the same period.
5. Credential rotation on a fixed schedule and immediately after each use.

**Why detection beats approval:** an approval gate that stands between an engineer and a production incident gets bypassed. Detection is unbypassable, and it is what the auditor asks for.

---

## Decision Guidance

| Situation | Recommended approach | Reason |
|---|---|---|
| Elevation for a single task in one sitting | Session-based permission set group | Grant dies with the session; no wall-clock window to leak |
| Elevation spanning hours or a shift | `PermissionSetAssignment.ExpirationDate` | Platform-enforced expiry, no custom scheduler to fail |
| Permanent elevation for a role | Neither — redesign the role | Standing privilege is the thing PAM exists to remove |
| Need to prove who had admin last quarter | `SetupAuditTrail` plus Event Monitoring archive | Setup Audit Trail covers at least the last 180 days |
| Need to expire a profile or a permission set license | Not supported | Expiration applies to permission sets and permission set groups only |
| Auditing expired or revoked assignments | SOQL with `ALL ROWS` | Expired assignments are soft-deleted and are otherwise invisible |
| Emergency full admin | Break-glass with detection | Attribution and alerting matter more than a pre-approval step |

---

## Recommended Workflow

1. Run the standing-privilege inventory (Pattern 1) and classify every row as profile-granted or assignment-granted. This is the baseline everything else is measured against.
2. Define tiers: daily-admin (no Modify All Data), elevated (time-boxed or session-based), break-glass (two named humans). Record which permissions live in each.
3. Move elevated access into a permission set group and pick the expiry mechanism — session activation for task-scoped work, `ExpirationDate` for shift-scoped work.
4. Confirm the group's `Status` is `Updated` and that assignment expiration is enabled org-wide before the first real grant.
5. Build detection: Transaction Security on break-glass login, plus a scheduled `ALL ROWS` review of expiring assignments and a `SetupAuditTrail` extract routed off-platform before the 180-day floor.
6. Re-run Pattern 1 quarterly and diff against the baseline. The metric is the count of standing admin-equivalent holders, and it should only go down.

---

## Review Checklist

- [ ] Inventory query selects `IsOwnedByProfile` rather than filtering on it
- [ ] Expiring-assignment reports use `ALL ROWS`, and were verified to return non-zero on a known expired grant
- [ ] Assignment expiration is enabled org-wide, and nobody is relying on it for a profile or a permission set license
- [ ] Elevated permission set group `Status` is `Updated` at grant time
- [ ] Break-glass accounts are one-per-named-human, MFA-enforced, and alert on login
- [ ] `SetupAuditTrail` is exported off-platform on a cadence shorter than its 180-day floor
- [ ] Every standing admin-equivalent holder has a documented owner and review date
- [ ] Session-based activation was evaluated before defaulting to a time-boxed assignment

---

## Deep Dives

`references/examples.md` — inventory, time-boxed elevation, break-glass detection. `references/gotchas.md` — six failure modes, including the two that make a clean audit report meaningless. `references/llm-anti-patterns.md` — six wrong/right query pairs. `templates/privileged-access-management-template.md` — the PAM runbook worksheet.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Standing-admin inventory | One row per active user holding an admin-equivalent permission, with the grant path and `IsOwnedByProfile` |
| Tier definitions | Daily-admin / elevated / break-glass, each with its permission list and expiry mechanism |
| Elevation record | Request, approver, grant timestamp, expiry mechanism, and the observed revocation |
| Break-glass procedure | Named holders, invocation steps, detection wiring, and the mandatory post-use review |

---

## Related Skills

- `admin/permission-set-group-composition` — owns permission set group design, muting, and composition; this skill only consumes the group as an elevation unit.
- `security/transaction-security-policies` — owns the policy that detects break-glass login in real time.
- `security/event-monitoring` — owns event log retention and the archive that outlives Setup Audit Trail.
- `admin/permission-sets-vs-profiles` — owns the profile-to-permission-set decomposition that shrinks the standing-privilege baseline in the first place.
