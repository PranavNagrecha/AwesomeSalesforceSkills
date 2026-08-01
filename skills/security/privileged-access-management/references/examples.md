# Examples — Privileged Access Management (PAM)

## Example 1: The standing-admin inventory that produced a different answer

**Context:** A regulated org reported "6 System Administrators" to its auditor, taken from a user list filtered by profile.

**Problem:** Profile name is not the permission. Two operations users had `Modify All Data` from a permission set, one integration profile carried `Customize Application`, and a legacy "Support Manager" profile had `View All Data`. None appeared in the profile-name count.

**Solution:** query the permission, not the label. Because Salesforce maintains one underlying permission set per profile, `PermissionSetAssignment` covers both grant paths in a single query.

```sql
SELECT Assignee.Id, Assignee.Username, Assignee.Name, Assignee.Profile.Name,
       PermissionSet.Label, PermissionSet.IsOwnedByProfile
FROM PermissionSetAssignment
WHERE PermissionSet.PermissionsCustomizeApplication = true
  AND PermissionSet.PermissionsModifyAllData = true
  AND Assignee.IsActive = true
ORDER BY Assignee.Name
```

Read the result like this:

| `IsOwnedByProfile` | What it means | Remediation |
|---|---|---|
| `true` | The permission comes from the user's profile | Move the user to a lesser profile, or decompose the profile |
| `false` | The permission comes from an explicit assignment | Remove the assignment, or re-grant it with an expiry |

**Why it works:** it measures the permission rather than a naming convention, and it distinguishes the two remediation paths in the same pass. Selecting `IsOwnedByProfile` is deliberate — filtering on it is the mistake that produced the original wrong answer.

**Extension:** widen to the OR form over `PermissionsModifyAllData`, `PermissionsCustomizeApplication`, `PermissionsManageUsers`, and `PermissionsViewAllData` for the full privileged population, and run the same shape against `PermissionsDataExport`, `PermissionsExportReport`, `PermissionsApiEnabled`, and `PermissionsPasswordNeverExpires` for the exfiltration-adjacent set.

---

## Example 2: Four-hour elevation, and the report that proves it expired

**Context:** An approved ticket grants the `PAM_Elevated` permission set group for the duration of a change window.

**Problem:** The previous process granted the group permanently and relied on a human to remove it. Six months of tickets had left eleven standing grants.

**Solution:**

```apex
public with sharing class ElevationService {
    public class ElevationException extends Exception {}

    public static Id grant(Id requesterId, String groupDeveloperName, Integer hours) {
        PermissionSetGroup psg = [
            SELECT Id, Status FROM PermissionSetGroup
            WHERE DeveloperName = :groupDeveloperName LIMIT 1
        ];
        // Outdated / Updating / Failed groups do not deliver their permissions.
        if (psg.Status != 'Updated') {
            throw new ElevationException('Group ' + groupDeveloperName + ' status is ' + psg.Status);
        }
        PermissionSetAssignment psa = new PermissionSetAssignment(
            AssigneeId           = requesterId,
            PermissionSetGroupId = psg.Id,
            ExpirationDate       = System.now().addHours(hours)
        );
        insert psa;
        return psa.Id;
    }
}
```

The status guard is the part teams skip. `PermissionSetGroup.Status` is documented with the values **Updated**, **Outdated**, **Updating**, and **Failed**; assigning against anything but `Updated` succeeds at the DML level and still leaves the requester without the permissions.

**The review query — note `ALL ROWS`:**

```sql
SELECT Id, ExpirationDate, IsRevoked, Assignee.Name, Assignee.Username,
       PermissionSet.Name, PermissionSetGroupId
FROM PermissionSetAssignment
WHERE ExpirationDate != null
ORDER BY ExpirationDate DESC
ALL ROWS
```

**Failure path if you omit `ALL ROWS`:** expired assignments are treated as soft-deletes and ordinary SOQL does not return them. The report comes back empty, which reads as "no elevations outstanding" rather than "the query cannot see them". This is the single most misleading result in Salesforce PAM reporting.

**What expiry does and does not do:** at expiry the user remains assigned to the permission set or group but cannot access its permissions. Permissions they hold through non-expiring permission sets, groups, or their profile continue to apply — so expiry narrows the elevation, it does not reset the user to zero.

---

## Example 3: Session-based elevation instead of a wall-clock window

**Context:** A support engineer needs `View All Data` on Case for the length of one escalation, typically 20 minutes.

**Problem:** A four-hour `ExpirationDate` leaves three and a half hours of unused privilege attached to a live session. If the engineer walks away, so does the window.

**Solution:** mark the permission set group **Session Activation Required** and activate it per session.

```sql
-- Confirm the group is session-based before wiring the flow
SELECT Id, DeveloperName, Status, HasActivationRequired
FROM PermissionSetGroup
WHERE DeveloperName = 'Support_Escalation'
```

Then build **two** flows — the platform does not allow activation and deactivation in the same flow:

| Flow | Core action | When it runs |
|---|---|---|
| `Activate_Support_Escalation` | Activate Session-Based Permission Set | Engineer clicks "Take escalation" |
| `Deactivate_Support_Escalation` | Deactivate the session-based permission set | Escalation closed, or engineer clicks "Release" |

Audit what was actually active:

```sql
SELECT Id, UserId, PermissionSetId, PermissionSetGroupId, AuthSessionId, Description
FROM SessionPermSetActivation
```

`SessionPermSetActivation` is documented as "a permission set assignment activated during an individual user session", and its `AuthSessionId` ties the grant to one session, so the evidence trail is per-session rather than per-day.

**Why it works:** the grant is bounded by the session rather than by a clock the requester is not watching. `HasActivationRequired` is available in API version 53.0 and later, so confirm the org's API version before designing around it.

---

## Example 4: Break-glass detection and the post-use evidence pack

**Context:** Two break-glass accounts, `breakglass.ana@` and `breakglass.raj@`, each mapped to one named person.

**Problem:** Use was discovered during the quarterly review, weeks after the fact. There was no way to reconstruct what had been changed.

**Solution — detection first, evidence second:**

1. Transaction Security policy on the Login event, scoped to those two user IDs, notifying the on-call security channel. Policy mechanics belong to `security/transaction-security-policies`.
2. On every alert, open a review and attach the Setup change extract for the window:

```sql
SELECT CreatedDate, CreatedBy.Username, Action, Section, Display, DelegateUser
FROM SetupAuditTrail
WHERE CreatedDate = LAST_N_DAYS:1
ORDER BY CreatedDate DESC
```

`Action` is the change category — the documented example is `PermSetCreate` for creating a permission set — and `Display` is the full description, such as "Created permission set MAD: with user license Salesforce". `DelegateUser` is populated when a Login-As user performed the action and is blank otherwise, which is how you tell a real break-glass login from an admin impersonating someone.

3. Correlate with `LoginHistory` for the same window to capture `SourceIp`, `LoginType`, and `Browser`.
4. Rotate the credential immediately after use, not on the next scheduled rotation.

**Retention constraint:** `SetupAuditTrail` represents Setup changes for at least the last 180 days. Any obligation longer than that needs the extract routed off-platform on a cadence shorter than the floor — see `security/event-monitoring`.

**Why one account per human:** a shared break-glass account still produces the alert, but the `SetupAuditTrail` rows all name the same username. Attribution is the entire value of the control, and sharing removes it.
