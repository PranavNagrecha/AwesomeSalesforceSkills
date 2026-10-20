---
name: permission-set-expiration
description: "Use when an assignment must expire on a date, not stand forever. Trigger keywords: permission set expiration date, permission set group expiry, temporary access, time-boxed elevation, contractor access, ExpirationDate. NOT for PSG composition - use admin/permission-set-group-composition. NOT for muting mechanics - use security/permission-set-groups-and-muting. NOT for criteria-based auto-assignment - use admin/user-access-policies."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "how do I give a contractor access that switches itself off after 90 days"
  - "why did a user lose a permission overnight when nobody removed the assignment"
  - "set an expiration date on a permission set group assignment for one user"
  - "the expiration date option is missing from the assignment screen in Setup"
  - "find every permission set assignment expiring in the next 30 days"
  - "extend an assignment that is about to expire without unassigning and reassigning"
  - "the user still has the permission after the assignment expired"
  - "can a profile or a permission set license assignment carry an expiration date"
  - "audit who was granted temporary elevated access last quarter and when it ended"
tags:
  - permission-set-expiration
  - temporary-access
  - permission-set-assignment
  - privileged-access
  - access-review
  - user-management
inputs:
  - "Which permission set or permission set group is being time-boxed, and whether one user or a batch is being assigned"
  - "The business end date for the access, and the time zone that end date is measured in"
  - "Whether psaExpirationUIEnabled is on in the target org — the Setup assignment screen offers an expiration control only when it is"
  - "Whether the same permissions are also granted by the assignee's profile or by a second, non-expiring permission set"
  - "Whether user access policies are enabled — that adds IsRevoked and the UserAccessChange trail to every assignment row"
outputs:
  - "A time-boxed assignment plan naming the permission set or group, the assignee, the ExpirationDate, and the approver"
  - "SOQL audit queries for assignments expiring soon, assignments already inactive, and assignments revoked by policy"
  - "A deployable UserManagementSettings snippet that turns on the expiration UI"
  - "A renewal procedure that updates ExpirationDate in place instead of deleting and re-inserting the assignment"
  - "A Setup Audit Trail evidence plan for the grant, the extension, and the expiry"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Permission Set Expiration

This skill activates when access has an end date: contractor and vendor grants, on-call elevation, audit-season read access, a migration cutover role, or any permission a security review has agreed must not become standing privilege. It covers where the expiration is stored, what the platform does and does not take away when the date passes, which assignment types cannot carry an expiry at all, and how to audit the population before it silently drifts back to permanent.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Is the expiration UI turned on in this org?** `UserManagementSettings.psaExpirationUIEnabled` is documented as "Indicates if admins can use an updated user interface that includes an assignment expiration for permission sets and permission set groups (true) or not (false). The default value is `false`." It is available in API version 52.0 and later (api_meta 264 L132107-L132111). If nobody has turned it on, an admin clicking through Setup will not see an expiration control and will conclude the feature does not exist.
- **Is the permission granted anywhere else?** The Salesforce Security Guide is blunt about this: "To revoke a permission, you must remove all instances of the permission from the user." (Grounded in 262: salesforce_security_impl_guide L809 (Security Guide not yet published at 264).) An expiring assignment closes one grant path. If the profile or a second permission set also enables the permission, the user keeps it after the date passes and the elevation was never time-boxed at all.
- **Which object holds the grant?** `PermissionSetAssignment` carries `ExpirationDate`; `PermissionSetLicenseAssign` does not, and does not even support `update()` (object_reference 264 L220298; its fields L220309-L220372 carry no expiry). If the elevation depends on a permission set *license*, no expiry exists for it.
- **Are user access policies enabled?** With them on, `IsRevoked`, `LastCreatedByChangeId`, and `LastDeletedByChangeId` appear on the assignment (API version 57.0 and later; object_reference 264 L219761-L219762, L219780-L219782) and a policy-driven revocation leaves the assignment row in place rather than deleting it (L219895-L219896). Audit queries written for a plain org return the wrong population in a policy org.

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Is `psaExpirationUIEnabled` on in the target org, and will the admin work in Setup or through the API? | The Setup control is off by default (Gotcha 1) | A settings change in the release, or an API-only runbook |
| Which Setup path will the admin use to assign — the permission set's Manage Assignments or the user record? | Only one path offers the expiration step (Gotcha 2) | A click path that actually shows the date field |
| Is the elevated permission also on the profile or on another assigned permission set or group? | Expiry closes one grant; a second grant survives it (Gotcha 6) | A single-source grant, or an honest note that the expiry is decorative |
| Does the elevation depend on a permission set license, package license, or group membership? | Those grants have no expiry field at all (Gotcha 7) | A manual removal step owned by a named person |
| Are user access policies enabled, and how will lapsed and revoked rows be reported? | Expired and revoked rows both survive; revoked ones need `ALL ROWS` (Gotchas 3, 4) | Audit queries that cover `IsActive = false` and `IsRevoked = true` separately |
| Is the assignee an integration, guest or system user? | Those users are not in the Manage Assignments page (Gotcha 10) | A scripted, ticketed `PermissionSetAssignment` insert |
| Would a session-based permission set be the tighter control, and will it be placed in a group? | Inside a group it no longer requires activation (Gotcha 9) | A grant that keeps its session boundary |

A configured time-box built from these answers has one grant path, a date in a stated time zone, and an audit query that finds it after it lapses; an assignment dated from the request alone often leaves the same permission standing elsewhere.

---

## Core Concepts

### The expiry is a field on the assignment row

`PermissionSetAssignment` "represents a user's assignment to a permission set or permission set group" and is available in API version 22.0 and later. Its supported calls are `create()`, `delete()`, `describeSObjects()`, `query()`, `retrieve()`, and `update()`. Access to the object requires View Setup and Configuration, Assign Permission Sets, or Manage User (object_reference 264 L219697, L219701, L219706-L219708).

| Field | Type — Properties | What it means for time-boxing |
|---|---|---|
| `ExpirationDate` | `dateTime` — Create, Filter, Nillable, Sort, **Update** | "The date that the assignment of the permission set or permission set group expires for the specified user." API version 52.0 and later. Nillable, so an assignment with no end date is the same row with this field null (object_reference 264 L219742-L219745). |
| `IsActive` | `boolean` — Defaulted on create, Filter, Group, Sort | "Indicates whether the assignment is active (`true`) or not (`false`). Defaults to `false`." API version 52.0 and later. Not createable and not updateable — the platform sets it (L219750-L219753). Filter on it; never try to write it. |
| `IsRevoked` | `boolean` — Defaulted on create, Filter, Group, Sort, Update | "Indicates whether the assignment was revoked (`true`) or not (`false`)." Present only when user access policies are enabled. API version 57.0 and later (L219758-L219762). |
| `AssigneeId` | `reference` (User) — Create, Filter, Group, Sort | No Update. Retargeting an assignment to a different user is a delete plus an insert. |
| `PermissionSetId` | `reference` — Create, Filter, Group, Nillable, Sort | No Update. Swapping which permission set is granted is a delete plus an insert. |
| `PermissionSetGroupId` | `reference` — Create, Filter, Group, Nillable, Sort | No Update. API version 45.0 and later. One row grants the whole group. |
| `LastCreatedByChangeId` / `LastDeletedByChangeId` | `reference` (UserAccessChange) | Populated only when user access policies are enabled. API version 57.0 and later. `UserAccessChange.Source` carries, "for example, `UserAccessPolicyId`." (object_reference 264 L300147) |

The Object Reference's blanket instruction — "To update an assignment, delete an existing assignment and insert a new one" (object_reference 264 L219864-L219865) — is about the Create-only fields above. `ExpirationDate` is the exception: it is explicitly updateable, which is why extending an expiry is a one-field update, not a re-assignment. See `references/gotchas.md` Gotcha 2 for what the delete-and-insert route costs you.

### Expiry closes one door, not the room

Expiry ends *this assignment*. It does not audit the rest of the user's access. A permission that is also on the profile, on a second permission set, or inside a permission set group the user is still assigned to survives the date unchanged. Time-boxing therefore only works when the elevated permission lives in exactly one place — which is the whole argument for a narrow, single-purpose elevation permission set rather than hanging an expiry on a broad job-function group.

### What can and cannot carry an expiration date

| Grant mechanism | Expiry supported? | Evidence |
|---|---|---|
| Permission set assignment | **Yes** | `PermissionSetAssignment.ExpirationDate`, API version 52.0 and later |
| Permission set group assignment | **Yes** | Same field, same row — the description names "the permission set or permission set group" |
| Permission set **license** assignment | **No** | `PermissionSetLicenseAssign` has no `ExpirationDate`, and its supported calls are `create()`, `delete()`, `describeSObjects()`, `query()`, `retrieve()` — no `update()` |
| Profile | **No** | A profile is a lookup on the User record; there is no assignment object to hang a date on |
| Muting permission set | **No** | `MutingPermissionSet` "is used in conjunction with `PermissionSetGroup`" (object_reference 264 L187698) — it is a component of a group, never assigned to a user, so there is no assignment row |
| Public group or queue membership | **No** | `GroupMember` has exactly two fields, `GroupId` and `UserOrGroupId`, and does not support `update()` (object_reference 264 L155436, L155448, L155462) |
| Package license | **No** | No expiration field on the assignment; user access policies can Grant or Revoke a `PackageLicense`, but with no date attached (`UserPackageLicense` fields, object_reference 264 L303662-L303757; policy types, api_meta 264 L141703) |

### Turning on the Setup control

The toggle lives on the **User Management Settings** Setup page, and it is deployable. `UserManagementSettings` values are stored in `UserManagement.settings`; in the package manifest all org settings types are referenced by the name `Settings` (api_meta 264 L131941-L131947).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/settings/UserManagement.settings-meta.xml -->
<UserManagementSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <psaExpirationUIEnabled>true</psaExpirationUIEnabled>
    <userAccessPoliciesEnabled>true</userAccessPoliciesEnabled>
</UserManagementSettings>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/package.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>UserManagement</members>
        <name>Settings</name>
    </types>
    <version>67.0</version>
</Package>
```

There is only one settings file per settings component, so retrieve the org's existing `UserManagement.settings` and add the element rather than deploying the two-line file above over the top of whatever else is configured there. `userAccessPoliciesEnabled` is available in API version 58.0 and later and also defaults to `false` (api_meta 264 L132120-L132126; one settings file per component, L131947-L131948); include it only if the org has actually adopted policies.

### User Access Policies assign; they do not hold the clock

A user access policy is the supported no-code way to *make* assignments from user criteria — `UserAccessPolicy` is available in API version 57.0 and later and requires the **Manage User Access Policies** permission (api_meta 264 L141568, L141572). But the action shape is deliberately small. `UserAccessPolicyAction` has exactly three fields: `action` (`Grant` or `Revoke`), `target`, and `type` (`Group`, `PackageLicense`, `PermissionSet`, `PermissionSetGroup`, `PermissionSetLicense`, `Queue`) — api_meta 264 L141673-L141707. **There is no expiration attribute anywhere in the policy metadata.**

The consequence is architectural: a policy can express "everyone in this role gets this group" and "everyone who leaves this role loses it," but it cannot express "for ninety days." Criteria-driven revocation and date-driven expiry are two different controls. Use `admin/user-access-policies` for the first; use `ExpirationDate` for the second. A policy-driven revoke sets `IsRevoked = true` and leaves the row behind rather than deleting it, so `ALL ROWS` is required to see the revoked population — a date expiry and a policy revocation are two different terminal states and one audit query will not find both.

---

## Common Patterns

### Pattern: Single-Purpose Elevation Permission Set

**When to use:** A named individual needs one dangerous capability — Manage Users, an integration-user permission, an object's Delete — for a bounded period, and the org's job-function permission sets are too broad to expire safely.

**How it works:**
1. Build a permission set that contains only the elevated capability. Name it for the elevation, not for the person.
2. Assign it to the individual with `ExpirationDate` set to the agreed end instant.
3. Verify the capability is not simultaneously granted by the assignee's profile or by any other assigned permission set — if it is, the expiry buys nothing.
4. Record the approver and the business justification alongside the assignment; the platform stores the date, not the reason.
5. Let the date pass. Do not build a job to remove the assignment.

**Why not hang the expiry on the job-function group:** the group carries the user's normal, permanent access as well. When it expires, the user loses their day job, not just the elevation. Expiring a group assignment is correct only when the entire group is the temporary grant — a project role, a migration cutover role, an audit-window reader.

### Pattern: Renewal by Update, Not Re-Assignment

**When to use:** A contractor's engagement is extended and the assignment is close to expiring, or already inactive.

**How it works:** `ExpirationDate` is updateable. Query the assignment by `AssigneeId` and `PermissionSetId`, then update the single field with the new instant.

```apex
// Extend one contractor's elevation by another quarter.
PermissionSetAssignment psa = [
    SELECT Id, ExpirationDate, IsActive
    FROM PermissionSetAssignment
    WHERE AssigneeId = :contractorId
      AND PermissionSet.Name = 'PS_Temp_ManageUsers'
    LIMIT 1
];
psa.ExpirationDate = newEndInstant;
update psa;
```

**Why not delete and re-insert:** a new row resets the assignment's creation audit and breaks any reporting keyed on the original grant. It also risks a window where the user has no assignment at all if the insert fails. Re-insert only when the *target* changes — a different user, a different permission set, a different group — because those fields are Create-only.

### Pattern: Expiry-Aware Access Review

**When to use:** A quarterly or SOX-style access review must show which elevations are live, which are about to lapse, and which already have.

**How it works:** three queries, run together, because no single one covers the population.

```soql
-- 1. Live elevations with a scheduled end, next 30 days first.
--    IsActive = true is load-bearing: without it, NEXT_N_DAYS:30 also
--    returns every assignment that already lapsed.
SELECT Id, Assignee.Name, Assignee.Username, PermissionSet.Name,
       PermissionSetGroup.DeveloperName, ExpirationDate, IsActive
FROM PermissionSetAssignment
WHERE IsActive = true
  AND ExpirationDate != NULL
  AND ExpirationDate <= NEXT_N_DAYS:30
ORDER BY ExpirationDate ASC

-- 2. Standing privilege: elevation permission sets assigned with NO end date.
SELECT Id, Assignee.Name, PermissionSet.Name, ExpirationDate
FROM PermissionSetAssignment
WHERE ExpirationDate = NULL
  AND PermissionSet.Name LIKE 'PS_Temp_%'

-- 3. Policy-revoked rows, which are NOT deleted and NOT returned without ALL ROWS.
SELECT Id, ExpirationDate, Assignee.Name, PermissionSet.Name
FROM PermissionSetAssignment
WHERE IsRevoked = true ALL ROWS
```

Query 2 is the one that finds the failure. Every org that adopts time-boxing accumulates elevation permission sets assigned without a date, because the API path makes `ExpirationDate` optional and nillable and nothing rejects the insert.

---

## Decision Guidance

| Situation | Recommended approach | Reason |
|---|---|---|
| One person needs one capability for a fixed window | Single-purpose permission set + `ExpirationDate` | Narrow grant means expiry actually revokes something |
| A whole project role is temporary | Permission set group assignment + `ExpirationDate` | One row expires the entire aggregate grant |
| Access should end when a user attribute changes, not on a date | User access policy with a `Revoke` action | Policy actions have no date; criteria are the trigger. See `admin/user-access-policies` |
| Access must end the moment the session does | Session-based permission set | Tighter than any wall-clock date. Note: session-based permission sets included in a permission set group do not require activation for users assigned to the group (object_reference 264 L264383) |
| The elevation depends on a permission set *license* | No expiry exists — build a manual removal step | `PermissionSetLicenseAssign` has no `ExpirationDate` and no `update()` |
| The permission is also on the profile | Fix the profile first, then time-box | Expiry cannot remove a grant it does not own |
| An engagement is extended | `update` the `ExpirationDate` field | The field is updateable; delete-and-insert is only needed for Create-only fields |
| Reporting must show elevations that already ended | Filter `IsActive = false` and add `ALL ROWS` | The state, not the row's existence, is what changes. `ALL ROWS` is correct whether or not lapsed rows are hidden — see `references/gotchas.md` Gotcha 3 |
| You are tempted to write a nightly job that unassigns | Use `ExpirationDate` | A scheduled job fails silently and leaves standing privilege behind — the exact outcome the control exists to prevent |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm the org can express an expiry.** Check `UserManagementSettings` for `psaExpirationUIEnabled`. If it is `false` and the admin will work through Setup, turn it on first — the metadata snippet above is deployable. Also record whether `userAccessPoliciesEnabled` is on, because it changes which fields exist on the assignment.
2. **Locate every grant of the target permission.** Enumerate the assignee's profile, all assigned permission sets, and all assigned permission set groups. If the elevated permission appears more than once, either narrow the grant or accept that the expiry is decorative and say so out loud.
3. **Choose the unit of expiry.** A single-purpose permission set for an individual capability; a permission set group only when the entire group is the temporary grant. Never attach an expiry to a permission set that also carries the user's day-to-day access.
4. **Set `ExpirationDate` as an explicit instant.** The field is a `dateTime`. Through the API, write a full timestamp so the cutoff is unambiguous; through Setup, confirm what clock time and time zone the org's assignment screen applies before you promise an auditor a cutoff time. Do not assume the two paths resolve to the same moment.
5. **Record the decision outside the platform record.** The assignment stores a date, not an approver or a justification. Capture both in the request ticket or in the workbook produced by `templates/permission-set-expiration-template.md`.
6. **Verify the expiry landed and schedule the review.** Re-query the assignment and confirm `ExpirationDate` is populated. Run the three access-review queries above and confirm the new row appears in query 1 and not in query 2. Read `references/gotchas.md` before writing any reporting that assumes an expired assignment disappears.
7. **Run the checker script** — `python3 skills/admin/permission-set-expiration/scripts/check_permission_set_expiration.py --plan <plan.json>` to validate the assignment plan's field shape before anyone loads it.

---

## Review Checklist

Run through these before marking a time-boxed elevation complete:

- [ ] `psaExpirationUIEnabled` state confirmed in the target org and recorded in the change ticket
- [ ] The elevated permission is granted by exactly one assignment — profile and all other permission sets checked
- [ ] The expiring assignment does not also carry the user's normal job access
- [ ] `ExpirationDate` is populated, and the instant is written down in a stated time zone
- [ ] The approver and business justification are recorded outside the assignment row
- [ ] The elevation permission set is named for the elevation, not for the individual
- [ ] The access-review queries return the new assignment in the "expiring soon" set and nothing unexpected in the "no end date" set
- [ ] Reporting that counts assignments filters on `IsActive`, uses `ALL ROWS` when hunting lapsed rows, and covers `IsRevoked` separately if user access policies are enabled
- [ ] No scheduled Flow or Apex job was created to duplicate what `ExpirationDate` already does
- [ ] Setup Audit Trail is being exported on a cadence shorter than 180 days, since setup entity records are deleted after that — Grounded in 262: salesforce_security_impl_guide L4975 (Security Guide not yet published at 264).

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviours that cause real production problems. `references/gotchas.md` carries ten of these in full, with the mechanism and the recovery; items 1-4 and 6 below summarise five of them, and item 5 is stated in full here.

1. **The Setup control is off by default** — `psaExpirationUIEnabled` defaults to `false`, so an admin can work through the assignment screens and never see an expiration option while the API field has existed since API version 52.0 (api_meta 264 L132110-L132111).
2. **The two Setup paths are not equivalent** — the Security Guide's expiration step appears in the permission-set-side *Manage Assignments → Add Assignments* flow, not in the user-record-side *Edit Assignments* procedure. Admins who always start from the user record will not find it. Grounded in 262: salesforce_security_impl_guide L2055, and the user-record procedure L2028-L2036 has no expiration step (Security Guide not yet published at 264).
3. **Liveness is a state, not the row's existence** — `IsActive` is the platform-owned, read-only flag that carries it. Any report or integration that treats "an assignment row exists" as "the user has access" reads a lapsed elevation as live.
4. **Setup Audit Trail still labels the expiration-date entry beta** — in the Summer '26 Security Guide the tracked change reads "Permission set (or group) changes to the assignment expiration date (beta)". Confirm the entry appears in your org before relying on it as audit evidence. Grounded in 262: salesforce_security_impl_guide L5034 (Security Guide not yet published at 264). Whether Winter '27 drops the beta label is not known from the corpus.
5. **The bulk Setup flow caps removal at 1,000 users at a time** — relevant when an expiry experiment has to be unwound by hand across a large population. Grounded in 262: salesforce_security_impl_guide L2069 (Security Guide not yet published at 264).
6. **Guest, integration, and system users are not in the Manage Assignments UI** — "Certain types of users, such as guest, Self-Service, integration, and system users, aren't available in the Manage Assignments page. To view or manage these users, use the `PermissionSetAssignment` API object." Time-boxing an integration user's elevation is an API-only operation. Grounded in 262: salesforce_security_impl_guide L2042 (Security Guide not yet published at 264).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Time-boxed assignment plan | Permission set or group, assignee, `ExpirationDate` instant, approver, justification, review date |
| Access-review query set | The three SOQL queries covering expiring-soon, no-end-date, and policy-revoked populations |
| `UserManagement.settings-meta.xml` | Deployable settings file enabling `psaExpirationUIEnabled` |
| Renewal procedure | Single-field `update` on `ExpirationDate`, with the delete-and-insert cases called out |
| Checker script output | Field-shape validation of the assignment plan before it is loaded |

---

## Related Skills

- `admin/permission-set-group-composition` — decides what goes *inside* a permission set group; read it before choosing a group as the unit of expiry
- `security/permission-set-groups-and-muting` — muting mechanics; a muting permission set is a group component and can never carry an expiry
- `admin/user-access-policies` — criteria-driven grant and revoke; the automated assignment path that has no date attribute
- `admin/permission-set-architecture` — how to shape a single-purpose elevation permission set narrow enough that expiring it means something
- `security/privileged-access-management` — the surrounding control: approval, break-glass, session-based alternatives, and the audit trail
- `admin/user-management` — deactivation and offboarding, which is the other half of not leaving standing access behind
