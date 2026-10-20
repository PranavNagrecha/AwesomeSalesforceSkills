# LLM Anti-Patterns — Apex User And Permission Checks

## Anti-Pattern 1: Profile-Name String Check

**What the LLM generates:**

```apex
Profile p = [SELECT Name FROM Profile WHERE Id = :UserInfo.getProfileId() LIMIT 1];
if (p.Name == 'System Administrator') { /* admin path */ }
```

**Why it happens:** LLMs reach for intuitive identity checks. Profile name is the first thing that comes to mind.

**Correct pattern:** a dedicated custom permission checked with `FeatureManagement.checkPermission('<CustomPermissionApiName>')` — the argument is a custom permission API name (apexref 262 L215460), so `'ModifyAllData'` is not a documented use. No Profile SOQL needed.

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

**Why it happens:** LLMs don't anticipate silent denial. Whether an undefined name returns `false` rather than throwing is UNVERIFIED (2026-10-20); the reference documents only enabled (true) / disabled (false) (apexref 262 L215465).

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

## Anti-Pattern 7: Treating `UserInfo.getUserType()` As An Enum

**What the LLM generates:**

```apex
if (UserInfo.getUserType() == UserType.Standard) { /* internal */ }
```

**Why it happens:** Corrected 2026-10-20 — this entry previously had it backwards. `getUserType()` is `public static String getUserType()` (apexref 262 L243456-243460); there is no `UserType` enum to compare against.

**Correct pattern:** `if (UserInfo.getUserType() == 'Standard') { ... }` — values per User.UserType (object_reference 264 L300019-300037).

**Detection hint:** `UserType.` followed by a value name, or a `UserType` variable assigned from `getUserType()`.

---

## Anti-Pattern 8: Relying On `UserInfo.isMultiCurrencyOrganization()` For Auth

**What the LLM generates:** Using miscellaneous `UserInfo` convenience methods as proxies for permissions.

**Why it happens:** LLMs mix identity/environment info with authorization.

**Correct pattern:** Use custom permissions for authorization; use `UserInfo` only for identity and environment facts. `isMultiCurrencyOrganization()` "Specifies whether the organization uses multiple currencies" (apexref 262 L243541-243542) — it says nothing about the user.

**Detection hint:** `UserInfo` methods in security-sensitive `if` conditions.
