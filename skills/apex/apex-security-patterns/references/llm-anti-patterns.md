# LLM Anti-Patterns — Apex Security Patterns

Common mistakes AI coding assistants make when generating or advising on Apex sharing, CRUD/FLS enforcement, and execution context security.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using 'without sharing' as the default sharing keyword

**What the LLM generates:**

```apex
public without sharing class AccountService {
    @AuraEnabled
    public static List<Account> getAccounts() {
        return [SELECT Id, Name, AnnualRevenue FROM Account];
    }
}
```

**Why it happens:** LLMs use `without sharing` to avoid "insufficient access" errors during development. For `@AuraEnabled` methods callable from LWC, this means every user sees every record regardless of their sharing rules, role hierarchy, or territory assignments — a serious data exposure risk.

**Correct pattern:**

```apex
public with sharing class AccountService {
    @AuraEnabled
    public static List<Account> getAccounts() {
        return [SELECT Id, Name, AnnualRevenue FROM Account WITH USER_MODE];
    }
}
```

**Detection hint:** `without sharing` on classes containing `@AuraEnabled` methods.

---

## Anti-Pattern 2: Enforcing CRUD/FLS on reads but not on writes

**What the LLM generates:**

```apex
// Read: properly secured
List<Account> accounts = [SELECT Id, Name FROM Account WITH USER_MODE];

// Write: no FLS enforcement
accounts[0].Secret_Field__c = 'overwritten';
update accounts; // Silently writes to fields the user cannot see
```

**Why it happens:** LLMs apply `WITH USER_MODE` or `WITH SECURITY_ENFORCED` to SOQL queries but forget that DML operations also require CRUD/FLS enforcement. A user who cannot see `Secret_Field__c` should not be able to write to it via an `@AuraEnabled` method.

**Correct pattern:**

```apex
// Read with FLS
List<Account> accounts = [SELECT Id, Name FROM Account WITH USER_MODE];

// Write with FLS — strip inaccessible fields before DML
accounts[0].Secret_Field__c = 'overwritten';
SObjectAccessDecision decision = Security.stripInaccessible(
    AccessType.UPDATABLE, accounts
);
update decision.getRecords();
```

**Detection hint:** `WITH USER_MODE` on SOQL but `update` or `insert` statements without `Security.stripInaccessible`, `as user`, or `AccessLevel.USER_MODE` in the same method. Do not count `WITH SECURITY_ENFORCED` as evidence the read is secured — it is the weaker clause below 67.0 and does not compile at all from 67.0 on.

---

## Anti-Pattern 3: Using inherited sharing when the class is called from system context

**What the LLM generates:**

```apex
public inherited sharing class RecordService {
    public static List<Account> getVisibleAccounts() {
        return [SELECT Id, Name FROM Account];
    }
}
```

**Why it happens:** LLMs recommend `inherited sharing` as a safe default. But `inherited sharing` inherits from the caller. If the caller is a trigger handler, Batch Apex, or a `without sharing` class, the service silently runs without sharing — which is the opposite of what the developer intended.

**Correct pattern:**

```apex
// Use 'with sharing' when the method serves user-facing entry points
public with sharing class RecordService {
    public static List<Account> getVisibleAccounts() {
        return [SELECT Id, Name FROM Account WITH USER_MODE];
    }
}

// Use 'inherited sharing' ONLY on reusable utility classes where the caller
// is documented and sharing behavior is intentionally delegated
```

**Detection hint:** `inherited sharing` on classes that are called from triggers, batch jobs, or scheduled classes where the effective context would be `without sharing`.

---

## Anti-Pattern 4: Checking CRUD with Schema.describe but not checking FLS

**What the LLM generates:**

```apex
if (Schema.sObjectType.Account.isAccessible()) {
    List<Account> accts = [SELECT Id, Name, AnnualRevenue FROM Account];
    // FLS on AnnualRevenue not checked — user may not have field access
}
```

**Why it happens:** LLMs check object-level CRUD (`isAccessible`, `isCreateable`) but skip field-level security checks. A user with object access but without FLS on `AnnualRevenue` still gets that field's data returned.

**Correct pattern:**

```apex
// Preferred: use WITH USER_MODE which checks both CRUD and FLS
List<Account> accts = [SELECT Id, Name, AnnualRevenue FROM Account WITH USER_MODE];

// Alternative: manual FLS check
if (Schema.sObjectType.Account.isAccessible()
    && Schema.sObjectType.Account.fields.AnnualRevenue.getDescribe().isAccessible()) {
    List<Account> accts = [SELECT Id, Name, AnnualRevenue FROM Account];
}
```

**Detection hint:** `isAccessible\(\)` or `isCreateable\(\)` at the object level without corresponding field-level `getDescribe().isAccessible()` checks, and no `WITH USER_MODE` on the query.

---

## Anti-Pattern 5: Returning full SObjects from @AuraEnabled methods without field stripping

**What the LLM generates:**

```apex
@AuraEnabled
public static Account getAccount(Id accountId) {
    return [SELECT Id, Name, Phone, SSN__c, CreditScore__c
            FROM Account WHERE Id = :accountId];
}
```

**Why it happens:** LLMs select all fields the component might need. But `@AuraEnabled` methods serialize the entire SObject to the client, including sensitive fields the user should not see. Even if the LWC does not display `SSN__c`, it is in the response payload and visible in browser dev tools.

**Correct pattern:**

```apex
@AuraEnabled
public static Account getAccount(Id accountId) {
    List<Account> accounts = [
        SELECT Id, Name, Phone, SSN__c, CreditScore__c
        FROM Account WHERE Id = :accountId WITH USER_MODE
    ];
    if (accounts.isEmpty()) return null;

    // Strip fields the user cannot access before returning to client
    SObjectAccessDecision decision = Security.stripInaccessible(
        AccessType.READABLE, accounts
    );
    return (Account) decision.getRecords()[0];
}
```

**Detection hint:** `@AuraEnabled` methods that return SObject or `List<SObject>` without `Security.stripInaccessible` or `WITH USER_MODE`.

---

## Anti-Pattern 6: Hardcoding a Profile or Permission Set name for access checks

**What the LLM generates:**

```apex
@AuraEnabled
public static void deleteAccounts(List<Id> accountIds) {
    User currentUser = [SELECT Profile.Name FROM User WHERE Id = :UserInfo.getUserId()];
    if (currentUser.Profile.Name != 'System Administrator') {
        throw new AuraHandledException('Only admins can delete accounts');
    }
    delete [SELECT Id FROM Account WHERE Id IN :accountIds];
}
```

**Why it happens:** LLMs use Profile names for access checks because they appear in many examples. Profile names are not stable across orgs, are locale-dependent, and this approach bypasses the platform's permission model entirely. Custom permissions are the correct mechanism.

**Correct pattern:**

```apex
@AuraEnabled
public static void deleteAccounts(List<Id> accountIds) {
    if (!FeatureManagement.checkPermission('Can_Bulk_Delete_Accounts')) {
        throw new AuraHandledException('Insufficient permissions for bulk delete');
    }
    // Use with sharing + CRUD check
    delete [SELECT Id FROM Account WHERE Id IN :accountIds WITH USER_MODE];
}
```

**Detection hint:** `Profile\.Name` comparison or hardcoded profile strings like `'System Administrator'` in access-control logic.

---

## Anti-Pattern 7: Asserting a default access mode without reading the class's apiVersion

**What the LLM generates:**

```apex
// Advice given for a class whose .cls-meta.xml was never opened:
// "Apex runs in system mode by default, so FLS is NOT enforced unless you
//  add WITH USER_MODE." -- or, just as wrong, the flat inverse:
// "Apex now runs in user mode, so this query is already secure."
public class NightlySyncBatch implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext ctx) {
        return Database.getQueryLocator('SELECT Id, Territory__c FROM Account');
    }
}
```

**Why it happens:** The model has one default memorised and applies it everywhere. Both defaults are real, but each is true only for part of the corpus: at API 67.0 and later SOQL, SOSL, DML, and `Database` methods run in user mode; at 66.0 and earlier they run in system mode. The gate is the `apiVersion` in the class's `.cls-meta.xml`, not the org's release, so a Summer '26 org runs both kinds side by side. The pre-67.0 answer over-warns and tells the user to add enforcement that is already there. The blanket 67.0 answer is worse: it certifies a 58.0 class as secure when nothing is enforced, and it omits the opt-in that integration, batch, and platform-utility code now needs — recompiled at 67.0, the query above silently returns only the rows the running user can see.

**Correct pattern:**

```apex
// State the version you read, then apply the matching row.
// NightlySyncBatch.cls-meta.xml: <apiVersion>67.0</apiVersion>
// reason: nightly territory sync must span all accounts, not the job owner's.
return Database.getQueryLocator(
    'SELECT Id, Territory__c FROM Account WITH SYSTEM_MODE'
);
```

If the `.cls-meta.xml` is not in scope, say which row you assumed rather than picking a default. The matrix is [Apex security idiom by API version](../../../../agents/_shared/AGENT_CONTRACT.md#apex-security-idiom-by-api-version).

**Detection hint:** Any answer containing "Apex runs in system mode by default" or "Apex runs in user mode by default" with no `apiVersion` cited in the same answer. Also flag advice that adds `WITH USER_MODE` "for security" to a class already at 67.0+ (a no-op), and elevated-access classes bumped to 67.0 with no `WITH SYSTEM_MODE` / `AccessLevel.SYSTEM_MODE` added.
