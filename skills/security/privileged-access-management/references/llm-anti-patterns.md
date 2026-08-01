# LLM Anti-Patterns — Privileged Access Management (PAM)

## Anti-Pattern 1: Filtering the inventory on `IsOwnedByProfile = false`

**What the LLM generates:**

```sql
-- WRONG - drops every admin whose privilege comes via their profile
SELECT Assignee.Username, PermissionSet.Label
FROM PermissionSetAssignment
WHERE PermissionSet.PermissionsModifyAllData = true
  AND PermissionSet.IsOwnedByProfile = false
```

**Why it happens:** the `PermissionSet` reference has an example ending `WHERE IsOwnedByProfile = FALSE`, meant to list sets that are not profile-owned. Transplanted into an assignment audit it removes half the answer: in API version 25.0 and later every profile has a permission set holding its permissions.

**Correct pattern:**

```sql
-- RIGHT - select the grant path, never filter on it
SELECT Assignee.Username, PermissionSet.IsOwnedByProfile, PermissionSet.Profile.Name
FROM PermissionSetAssignment
WHERE PermissionSet.PermissionsModifyAllData = true AND Assignee.IsActive = true
```

**Detection hint:** `IsOwnedByProfile` in a `WHERE` clause is wrong by construction. It belongs in `SELECT`, where it says whether remediation is a profile change or an assignment removal.

---

## Anti-Pattern 2: Querying `UserPermissionAccess` for somebody else

**What the LLM generates:**

```apex
// WRONG - UserPermissionAccess has no user field to filter on
Boolean targetHasMad = [SELECT PermissionsModifyAllData
                        FROM UserPermissionAccess
                        WHERE UserId = :targetUserId].PermissionsModifyAllData;
```

**Why it happens:** the name reads like a per-user access matrix. It represents "the permissions accessibility for a current user", supports only `describeSObjects()` and `query()`, and is aimed at API users without `PermissionsViewSetup` checking their own session.

**Correct pattern:**

```apex
// RIGHT - the assignment graph is queryable for any user
List<PermissionSetAssignment> hits = [
    SELECT Id FROM PermissionSetAssignment
    WHERE AssigneeId = :targetUserId AND PermissionSet.PermissionsModifyAllData = true];
Boolean targetHasMad = !hits.isEmpty();
```

**Detection hint:** a `UserPermissionAccess` query filtered by user is fabricated. The replacement needs View Setup and Configuration, Assign Permission Sets, or Manage User to return rows.

---

## Anti-Pattern 3: Aggregating `SetupAuditTrail`

**What the LLM generates:**

```sql
-- WRONG - aggregate queries are not supported on this object
SELECT COUNT(Id), CreatedBy.Username
FROM SetupAuditTrail
WHERE CreatedDate = LAST_N_DAYS:30
GROUP BY CreatedBy.Username
```

**Why it happens:** "changes per admin" is the first question after a break-glass event, and every other audit object supports `GROUP BY`. The reference: `SELECT count() FROM SetupAuditTrail` works, `SELECT count(Id) FROM SetupAuditTrail` fails. It is also "not a supported standard controller".

**Correct pattern:**

```apex
// RIGHT - select rows, aggregate outside SOQL
Map<String, Integer> byAdmin = new Map<String, Integer>();
for (SetupAuditTrail r : [SELECT CreatedBy.Username, DelegateUser
                          FROM SetupAuditTrail WHERE CreatedDate = LAST_N_DAYS:30]) {
    String who = r.DelegateUser != null ? r.DelegateUser : r.CreatedBy.Username;
    byAdmin.put(who, byAdmin.containsKey(who) ? byAdmin.get(who) + 1 : 1);
}
```

**Detection hint:** `GROUP BY`, `COUNT(Id)`, or `standardController="SetupAuditTrail"` will not run; supported calls are `query()` and `retrieve()` only.

---

## Anti-Pattern 4: Updating a `PermissionSetAssignment` to re-target a grant

**What the LLM generates:**

```apex
// WRONG - AssigneeId and PermissionSetGroupId are Create-only
PermissionSetAssignment psa = [SELECT Id FROM PermissionSetAssignment WHERE Id = :assignmentId];
psa.AssigneeId = newOwnerId;  psa.PermissionSetGroupId = newGroupId;
update psa;
```

**Why it happens:** the object lists `update()` among its supported calls, inviting an updateable-looking edit. The field properties say otherwise: `AssigneeId`, `PermissionSetId`, and `PermissionSetGroupId` are Create-only. Only `ExpirationDate` and `IsRevoked` carry Update; the usage section says to delete the existing assignment and insert a new one.

**Correct pattern:**

```apex
// RIGHT - re-target = delete + insert
delete [SELECT Id FROM PermissionSetAssignment WHERE Id = :assignmentId];
insert new PermissionSetAssignment(AssigneeId = newOwnerId,
                                   PermissionSetGroupId = newGroupId,
                                   ExpirationDate = System.now().addHours(4));
```

**Detection hint:** an `update` touching anything but `ExpirationDate` or `IsRevoked` here is wrong, and nothing warns you.

---

## Anti-Pattern 5: Folding a session-based permission set into a group "to simplify assignment"

**What the LLM generates:**

```text
# WRONG - activation requirement on the member, not on what you assign
PermissionSet      PAM_Elevated_Session  HasActivationRequired = true
PermissionSetGroup PAM_Elevated          HasActivationRequired = false  (contains it)
Assign PAM_Elevated -> permissions apply all session, no activation, no error
```

**Why it happens:** grouping is standard advice for reducing assignment sprawl. The `SessionPermSetActivation` reference notes the exception: session-based permission sets included in a permission set group do not require session-based activation for users assigned to the group.

**Correct pattern:**

```sql
-- RIGHT - HasActivationRequired belongs on the group (API 53.0+)
SELECT Id, DeveloperName, Status, HasActivationRequired
FROM PermissionSetGroup
WHERE DeveloperName = 'PAM_Elevated'
```

**Detection hint:** a design that sets `HasActivationRequired` on a permission set and then assigns a group has no session control. Check the flag on the record the assignment points at, and confirm `Status` is `Updated`.

---

## Anti-Pattern 6: Putting per-object permission names on `PermissionSet`

**What the LLM generates:**

```sql
-- WRONG - these are ObjectPermissions fields, not PermissionSet fields
SELECT Id, Name
FROM PermissionSet
WHERE PermissionsModifyAllRecords = true OR PermissionsViewAllRecords = true
```

**Why it happens:** org-wide and per-object permissions are named almost identically. `PermissionsModifyAllRecords` and `PermissionsViewAllRecords` are real, but live on `ObjectPermissions`, scoped by `SobjectType`, and the first also requires `PermissionsRead`, `PermissionsDelete`, `PermissionsEdit`, and `PermissionsViewAllRecords`. `PermissionSet` exposes one boolean per permission, whose count varies by org and license type.

**Correct pattern:**

```sql
-- RIGHT - OR in the org-wide grant, as the reference's own example does
SELECT ParentId, Parent.Label, SobjectType, Parent.PermissionsModifyAllData
FROM ObjectPermissions
WHERE SobjectType = 'Opportunity'
  AND (PermissionsModifyAllRecords = true OR Parent.PermissionsModifyAllData = true)
```

**Detection hint:** run `describeSObjects()` against `PermissionSet` before accepting any permission field name — the reference names it as the way to get the list. A "who has full access to X" answer omitting "Modify All Data" is incomplete.
