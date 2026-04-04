# Examples — Custom Permissions

## Example 1: Beta Feature Access Gate

**Context:** A development team has built a new "Advanced Refund Workflow" inside an existing Case object. The feature is ready for pilot but not for all users. The team wants to control who sees it without a code deployment or a sandbox refresh.

**Problem:** Without a named access gate, the only options are hardcoding user IDs or using a Custom Setting — both require code changes to expand the rollout and are difficult to audit.

**Solution:**

1. Create the custom permission in Setup > Custom Permissions:
   - Label: `Advanced Refund Workflow`
   - API Name: `Advanced_Refund_Workflow`

2. Create a permission set `Pilot — Advanced Refund Workflow` and enable the custom permission inside it.

3. Assign the permission set to the ten pilot users.

4. In Apex, guard the business logic:

```apex
public class RefundController {
    @AuraEnabled(cacheable=true)
    public static Boolean hasRefundAccess() {
        return FeatureManagement.checkPermission('Advanced_Refund_Workflow');
    }

    @AuraEnabled
    public static void processRefund(Id caseId, Decimal amount) {
        if (!FeatureManagement.checkPermission('Advanced_Refund_Workflow')) {
            throw new AuraHandledException('Access denied: Advanced Refund Workflow permission required.');
        }
        // business logic here
    }
}
```

5. In the LWC template, conditionally render the UI panel:

```html
<template lwc:if={hasRefundAccess}>
    <c-refund-panel case-id={recordId}></c-refund-panel>
</template>
```

6. To expand the rollout, assign the same permission set to additional users — no code change needed.

**Why it works:** `FeatureManagement.checkPermission` reads the running user's effective permission set assignments in real time. The server-side guard in `processRefund` prevents API-level bypass even if someone inspects and replays the Lightning message. The permission set is the single source of truth for who has access.

---

## Example 2: Admin-Only Override Button Visibility

**Context:** A Service Cloud org has a "Close Case" button that fires a validation rule ensuring `Resolution__c` is populated before closure. Tier-3 support managers occasionally need to close cases without a resolution during escalation handoffs.

**Problem:** Deactivating the validation rule for managers means all users lose the enforcement. Using `$Profile.Name` in the rule is fragile and requires rule updates whenever a new manager profile is created.

**Solution:**

1. Create the custom permission:
   - Label: `Bypass Case Closure Validation`
   - API Name: `Bypass_Case_Closure_Validation`

2. Add it to the `Tier-3 Support Manager` permission set.

3. Update the validation rule on Case:

```
// Original rule (fires an error if closed without resolution):
// AND(ISPICKVAL(Status, "Closed"), ISBLANK(Resolution__c))

// Updated rule with custom permission bypass:
AND(
  NOT($Permission.Bypass_Case_Closure_Validation),
  ISPICKVAL(Status, "Closed"),
  ISBLANK(Resolution__c)
)
```

4. Optionally, show the "Override Close" button only to users with the permission using a formula field as a visibility hint (note: formula fields cannot enforce security, so the validation rule remains the enforcement layer):

```
// Formula field: Show_Override_Button__c (type: Boolean/Checkbox)
$Permission.Bypass_Case_Closure_Validation
```

**Why it works:** `NOT($Permission.Bypass_Case_Closure_Validation)` short-circuits the entire validation rule for any user with the permission. The validation rule itself remains active and enforces the rule for all other users. Adding or removing the permission set assignment is the only required change for any future role change — no rule editing needed.

---

## Example 3: Apex Unit Test Pattern for Custom Permissions

**Context:** A class uses `FeatureManagement.checkPermission` to gate a feature. A developer writes a test but the test always fails because the test user does not have the permission set assigned.

**Problem:** `FeatureManagement.checkPermission` returns `false` in test context unless the permission set is explicitly assigned to the test user.

**Solution:**

```apex
@IsTest
private class RefundControllerTest {

    @TestSetup
    static void setup() {
        // Create a test user
        User testUser = new User(
            LastName = 'Refund Tester',
            Email = 'refundtester@example.com',
            Username = 'refundtester@example.com.test',
            Alias = 'rtest',
            TimeZoneSidKey = 'America/New_York',
            LocaleSidKey = 'en_US',
            EmailEncodingKey = 'UTF-8',
            ProfileId = [SELECT Id FROM Profile WHERE Name = 'Standard User' LIMIT 1].Id,
            LanguageLocaleKey = 'en'
        );
        insert testUser;

        // Assign the permission set that holds the custom permission
        PermissionSet ps = [SELECT Id FROM PermissionSet WHERE Name = 'Pilot_Advanced_Refund_Workflow' LIMIT 1];
        insert new PermissionSetAssignment(
            AssigneeId = testUser.Id,
            PermissionSetId = ps.Id
        );
    }

    @IsTest
    static void testUserWithPermissionCanProcessRefund() {
        User testUser = [SELECT Id FROM User WHERE Username = 'refundtester@example.com.test' LIMIT 1];
        System.runAs(testUser) {
            // FeatureManagement.checkPermission now returns true
            Boolean hasAccess = RefundController.hasRefundAccess();
            System.assertEquals(true, hasAccess, 'User with perm set should have refund access');
        }
    }

    @IsTest
    static void testUserWithoutPermissionIsDenied() {
        // Standard running user in test context has no perm sets assigned
        Boolean hasAccess = RefundController.hasRefundAccess();
        System.assertEquals(false, hasAccess, 'Default test user should not have refund access');
    }
}
```

**Why it works:** The `PermissionSetAssignment` insert inside `System.runAs` makes the custom permission active for that test user. Without this, the permission evaluates to `false` regardless of what is configured in the org, which can produce misleading test results.

---

## Anti-Pattern: Using $Profile.Name to Gate Features

**What practitioners do:** Instead of creating a custom permission, they write validation rules and formula fields that check `$Profile.Name = "System Administrator"` or similar profile-name strings.

**What goes wrong:**
- Profile names can change (renamed by admins, different in sandbox vs production).
- Every new role or persona that needs access requires a rule edit.
- The logic spreads across many rules and formulas and becomes impossible to audit centrally.
- The bypass cannot be assigned to a specific user within a profile — it is all-or-nothing at the profile level.

**Correct approach:** Create a custom permission with a meaningful API name. Add it to a permission set. Check `$Permission.My_Permission` in formulas or `FeatureManagement.checkPermission('My_Permission')` in Apex. Assign or revoke access by managing permission set assignments — no code or rule changes needed.
