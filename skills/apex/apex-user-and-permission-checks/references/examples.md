# Examples — Apex User And Permission Checks

## Example 1: Feature Gated By Custom Permission

**Context:** Finance wants "Bulk Refund" exposed to a small group of users, with the set of grantees changing occasionally (new hires, shifting teams). Currently the Apex class hardcodes `Profile.Name == 'Finance Manager'`.

**Problem:** When a new hire needs access, admins must clone the profile or add the user to that profile. Cloning breaks the check; adding disrupts other permissions. A permission set is what admins want, but the hardcoded check ignores permission-set-based grants.

**Solution:**

```apex
public with sharing class BulkRefundService {
    public static void initiate(Set<Id> paymentIds) {
        if (!FeatureManagement.checkPermission('Perform_Bulk_Refund')) {
            throw new NoAccessException('You lack permission to perform bulk refunds.');
        }
        // proceed with refund logic using WITH USER_MODE
    }
}
```

Admins assign `Perform_Bulk_Refund` to `PermSet_Finance_PowerUser`; grantees are managed via permission-set assignment.

**Why it works:** Single source of truth, rename-proof, admin-manageable. The check respects any assignment path (Profile, Permission Set, Permission Set Group).

---

## Example 2: Async Job Checks Originator's Permission

**Context:** A Queueable processes a large refund batch. The job needs to confirm the user who kicked it off had permission at the time of invocation.

**Problem:** `FeatureManagement.checkPermission` inside the Queueable checks the async context user — frequently the same, but in chained or scheduled invocations different.

**Solution:**

```apex
public class BulkRefundQueueable implements Queueable {
    private final Id initiatorId;
    private final Set<Id> paymentIds;

    public BulkRefundQueueable(Id initiatorId, Set<Id> paymentIds) {
        this.initiatorId = initiatorId;
        this.paymentIds = paymentIds;
    }

    public void execute(QueueableContext ctx) {
        if (!hasCustomPermission(initiatorId, 'Perform_Bulk_Refund')) {
            throw new NoAccessException(
                'Originating user no longer has permission.');
        }
        // proceed
    }

    public static Boolean hasCustomPermission(Id userId, String devName) {
        Integer assignments = [
            SELECT COUNT() FROM PermissionSetAssignment psa
            WHERE psa.AssigneeId = :userId
            AND psa.PermissionSetId IN (
                SELECT ParentId FROM SetupEntityAccess
                WHERE SetupEntityType = 'CustomPermission'
                AND SetupEntityId IN (
                    SELECT Id FROM CustomPermission WHERE DeveloperName = :devName
                )
            )
        ];
        return assignments > 0;
    }
}
```

**Why it works:** The check is pinned to `initiatorId` at dequeue time, not to whoever the async context happens to resolve to.

---

## Example 3: UserType-Aware Data Visibility

**Context:** A Case handler displays different information to internal agents and Customer Community users.

**Problem:** Practitioners reach for Profile checks (`'Customer Community User'`) which miss other community licenses and break on custom profile names.

**Solution:**

```apex
public with sharing class CaseVisibility {
    public static Boolean isExternal() {
        UserType t = UserInfo.getUserType();
        // Standard is internal; everything else (Partner, CspLitePortal, etc.) is external.
        return t != UserType.Standard;
    }

    public static List<String> visibleFieldApiNames() {
        return isExternal()
            ? new List<String>{ 'Subject', 'Status', 'CreatedDate' }
            : new List<String>{ 'Subject', 'Status', 'CreatedDate',
                                'InternalNotes__c', 'Escalation_Score__c' };
    }
}
```

**Why it works:** `UserType` enum is license-aware and stable. One branch covers all external license flavors.

---

## Anti-Pattern: Profile Name String Check

**What practitioners do:**

```apex
if (UserInfo.getProfileId() == [SELECT Id FROM Profile WHERE Name = 'System Administrator' LIMIT 1].Id) {
    // admin-only path
}
```

**What goes wrong:** Profile name can be renamed or cloned. The SOQL runs every call. Admins with "Modify All Data" via a permission set are misclassified as non-admin.

**Correct approach:** `FeatureManagement.checkPermission('ModifyAllData')` (a built-in permission check).

---

## Anti-Pattern: Caching `checkPermission` Result In A Static

**What practitioners do:**

```apex
private static Boolean canRefund = FeatureManagement.checkPermission('Perform_Bulk_Refund');
```

**What goes wrong:** The static initializer fires once on first class load of the transaction. In long-running async jobs that pull configuration changes mid-run, the cached value is stale.

**Correct approach:** Call `checkPermission` at the decision site. It's cheap.
