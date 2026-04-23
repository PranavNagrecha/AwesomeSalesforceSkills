# LLM Anti-Patterns — Apex User And Permission Checks

## Anti-Pattern 1: Profile-Name String Check

**What the LLM generates:**

```apex
Profile p = [SELECT Name FROM Profile WHERE Id = :UserInfo.getProfileId() LIMIT 1];
if (p.Name == 'System Administrator') { /* admin path */ }
```

**Why it happens:** LLMs reach for intuitive identity checks. Profile name is the first thing that comes to mind.

**Correct pattern:** `FeatureManagement.checkPermission('ModifyAllData')` or a dedicated custom permission. No Profile SOQL needed.

**Detection hint:** SOQL selecting `Profile.Name` followed by a string equality branch.

---

## Anti-Pattern 2: Running User Assumption In Async

**What the LLM generates:**

```apex
public class RefundQueueable implements Queueable {
    public void execute(QueueableContext ctx) {
        if (!FeatureManagement.checkPermission('Refund')) return;
        // ...
    }
}
```

**Why it happens:** LLMs treat async context as equivalent to the enqueuing context. `checkPermission` inside the async job resolves to the async context user, not the enqueuer.

**Correct pattern:** Capture the originator's Id as a member and check permissions with a SOQL against their assignments.

**Detection hint:** `FeatureManagement.checkPermission` inside any `execute(...)`, `@future`, or scheduled `execute` block.

---

## Anti-Pattern 3: Hardcoded Permission Set Name

**What the LLM generates:**

```apex
PermissionSetAssignment psa = [SELECT Id FROM PermissionSetAssignment
    WHERE AssigneeId = :UserInfo.getUserId()
    AND PermissionSet.Name = 'Finance_Power_User' LIMIT 1];
if (psa != null) { /* gate */ }
```

**Why it happens:** LLMs don't know Custom Permissions are the proper abstraction above permission sets.

**Correct pattern:** Create a Custom Permission; gate on `FeatureManagement.checkPermission`. Admins can reassign the permission to any PS without code changes.

**Detection hint:** SOQL on `PermissionSetAssignment` with `PermissionSet.Name` string literal.

---

## Anti-Pattern 4: Caching `checkPermission` Result Across Transactions

**What the LLM generates:**

```apex
public class Cache {
    public static final Boolean CAN_REFUND =
        FeatureManagement.checkPermission('Refund');
}
```

**Why it happens:** LLMs optimize for "don't call twice." Static initialization is per-transaction in Apex, which is fine, but mutating perms mid-long-running job hits stale state.

**Correct pattern:** Call at the decision site; it's cheap.

**Detection hint:** `static final Boolean` or `@InvocableVariable` storing a `checkPermission` result.

---

## Anti-Pattern 5: Not Handling Undefined Permissions

**What the LLM generates:**

```apex
if (FeatureManagement.checkPermission('Typoed_Perm_Name')) {
    // never runs
}
```

**Why it happens:** LLMs don't know typos return false without warning.

**Correct pattern:** Add a deployment-time validation test that uses a known-good user and asserts every used permission returns `true`.

**Detection hint:** Free-text permission names with no corresponding deployment test.

---

## Anti-Pattern 6: `System.runAs(UserInfo.getUserId())` In Tests

**What the LLM generates:**

```apex
@IsTest
static void testRefund() {
    System.runAs(new User(Id = UserInfo.getUserId())) {
        BulkRefundService.initiate(paymentIds);
    }
}
```

**Why it happens:** LLMs use the test-runner user (usually a System Admin) as the `runAs` target, defeating the purpose of authorization testing.

**Correct pattern:** Create a low-privilege test user and `System.runAs(lowPrivUser)`.

**Detection hint:** `runAs(new User(Id = UserInfo.getUserId()))` or `runAs(UserInfo.getUserId())` in any test that gates on permissions.

---

## Anti-Pattern 7: Treating `UserInfo.getUserType()` As A String

**What the LLM generates:**

```apex
if (UserInfo.getUserType() == 'Standard') { /* internal */ }
```

**Why it happens:** LLMs don't know `getUserType()` returns a `UserType` enum, not a string.

**Correct pattern:** `if (UserInfo.getUserType() == UserType.Standard) { ... }`.

**Detection hint:** `UserInfo.getUserType()` compared to a string literal.

---

## Anti-Pattern 8: Relying On `UserInfo.isMultiCurrencyOrganization()` For Auth

**What the LLM generates:** Using miscellaneous `UserInfo` convenience methods as proxies for permissions.

**Why it happens:** LLMs mix identity/environment info with authorization.

**Correct pattern:** Use custom permissions for authorization; use `UserInfo` only for identity and environment facts.

**Detection hint:** `UserInfo` methods in security-sensitive `if` conditions.
