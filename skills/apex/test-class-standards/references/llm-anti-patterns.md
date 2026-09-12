# LLM Anti-Patterns — Test Class Standards

Common mistakes AI coding assistants make when generating or advising on Apex test classes.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using SeeAllData=true to avoid test data setup

**What the LLM generates:**

```apex
@IsTest(SeeAllData=true)
static void testAccountUpdate() {
    Account a = [SELECT Id, Name FROM Account LIMIT 1];
    a.Status__c = 'Active';
    update a;
    System.assertNotEquals(null, a.Id);
}
```

**Why it happens:** LLMs use `SeeAllData=true` to skip creating test data. This makes tests non-deterministic — they depend on existing org data that varies between sandboxes, scratch orgs, and developer orgs. Tests that pass in one environment fail in another.

**Correct pattern:**

```apex
@IsTest
static void testAccountUpdate() {
    Account a = TestDataFactory.createAccount('Test Corp');
    insert a;

    a.Status__c = 'Active';
    update a;

    Account updated = [SELECT Status__c FROM Account WHERE Id = :a.Id];
    System.assertEquals('Active', updated.Status__c, 'Status should be Active after update');
}
```

**Detection hint:** `SeeAllData\s*=\s*true` — should only be used for specific scenarios like PricebookEntry or standard price book testing.

---

## Anti-Pattern 2: Writing tests with no assertions (coverage-only tests)

**What the LLM generates:**

```apex
@IsTest
static void testMyService() {
    Account a = new Account(Name = 'Test');
    insert a;
    MyService.processAccount(a.Id);
    // No assertions — test just verifies it doesn't throw
}
```

**Why it happens:** LLMs generate tests that exercise code paths for coverage but do not verify behavior. These tests provide 75% coverage while proving nothing — they pass even when the code is completely broken, as long as it does not throw an unhandled exception.

**Correct pattern:**

```apex
@IsTest
static void testMyService_updatesStatusToProcessed() {
    Account a = new Account(Name = 'Test', Status__c = 'New');
    insert a;

    Test.startTest();
    MyService.processAccount(a.Id);
    Test.stopTest();

    Account result = [SELECT Status__c FROM Account WHERE Id = :a.Id];
    System.assertEquals('Processed', result.Status__c, 'processAccount should set status to Processed');
}
```

**Detection hint:** Test methods with no `System.assert`, `System.assertEquals`, or `System.assertNotEquals` calls.

---

## Anti-Pattern 3: Not using Test.startTest() and Test.stopTest() for async operations

**What the LLM generates:**

```apex
@IsTest
static void testBatch() {
    // Setup test data
    List<Account> accounts = TestDataFactory.createAccounts(200);
    insert accounts;

    Database.executeBatch(new MyBatch());
    // No Test.startTest/stopTest — batch may not execute
    System.assertEquals(200, [SELECT COUNT() FROM Account WHERE Status__c = 'Done']);
}
```

**Why it happens:** LLMs forget that async Apex (Batch, Queueable, @future) only executes synchronously in tests when dispatched between `Test.startTest()` and `Test.stopTest()`. Without these boundaries, the batch job may not run and assertions against its side effects fail.

**Correct pattern:**

```apex
@IsTest
static void testBatch() {
    List<Account> accounts = TestDataFactory.createAccounts(200);
    insert accounts;

    Test.startTest();
    Database.executeBatch(new MyBatch(), 200);
    Test.stopTest();

    System.assertEquals(200, [SELECT COUNT() FROM Account WHERE Status__c = 'Done']);
}
```

**Detection hint:** `Database.executeBatch` or `System.enqueueJob` in tests without `Test.startTest()` / `Test.stopTest()` boundaries.

---

## Anti-Pattern 4: Creating a monolithic TestDataFactory with hardcoded field values

**What the LLM generates:**

```apex
public class TestDataFactory {
    public static Account createAccount() {
        return new Account(
            Name = 'Test Account',
            Industry = 'Technology',
            BillingState = 'CA',
            Phone = '555-0100',
            Status__c = 'Active'
        );
    }
}
```

**Why it happens:** LLMs create factory methods that hardcode every field value. When a test needs a different status or industry, it either overrides fields (undermining the factory) or another factory method is created. The factory becomes rigid and bloated.

**Correct pattern:**

```apex
public class TestDataFactory {
    public static Account createAccount(String name) {
        return new Account(Name = name);
    }

    public static Account createAccount(String name, Map<String, Object> overrides) {
        Account a = new Account(Name = name);
        for (String field : overrides.keySet()) {
            a.put(field, overrides.get(field));
        }
        return a;
    }
}

// Usage:
Account a = TestDataFactory.createAccount('Test Corp',
    new Map<String, Object>{ 'Industry' => 'Finance', 'Status__c' => 'Inactive' }
);
```

**Detection hint:** Test factory methods that return objects with 5+ hardcoded field values and no parameterization.

---

## Anti-Pattern 5: Not testing bulk behavior (only testing with a single record)

**What the LLM generates:**

```apex
@IsTest
static void testTrigger() {
    Account a = new Account(Name = 'Single Record');
    insert a;
    // Only tests with 1 record — trigger works for 1 but fails at 200
}
```

**Why it happens:** LLMs generate the simplest test case with one record. Triggers and services may pass with 1 record but fail with 200 due to SOQL-in-loops, DML-in-loops, or map key collisions. Bulk tests catch these governor limit violations.

**Correct pattern:**

```apex
@IsTest
static void testTrigger_bulk() {
    List<Account> accounts = new List<Account>();
    for (Integer i = 0; i < 200; i++) {
        accounts.add(new Account(Name = 'Bulk Test ' + i));
    }

    Test.startTest();
    insert accounts; // Fires trigger with 200 records
    Test.stopTest();

    System.assertEquals(200, [SELECT COUNT() FROM Account WHERE Name LIKE 'Bulk Test%']);
}
```

**Detection hint:** All test methods in a trigger test class that only insert or update 1-2 records.

---

## Anti-Pattern 6: Running as the test-execution user instead of a specific user profile

**What the LLM generates:**

```apex
@IsTest
static void testAuraMethod() {
    Account a = new Account(Name = 'Test');
    insert a;
    List<Account> results = AccountController.getAccounts();
    // Running as system admin — FLS and sharing issues hidden
}
```

**Why it happens:** LLMs run tests as the current user (usually System Administrator), which has all permissions. FLS restrictions, sharing rules, and CRUD violations are invisible. The test passes in development but the component fails for standard users in production.

**Correct pattern:**

```apex
@IsTest
static void testAuraMethod_asStandardUser() {
    Profile stdProfile = [SELECT Id FROM Profile WHERE Name = 'Standard User'];
    User testUser = new User(
        Alias = 'stdt', Email = 'stduser@test.com',
        EmailEncodingKey = 'UTF-8', LastName = 'Testing',
        LanguageLocaleKey = 'en_US', LocaleSidKey = 'en_US',
        ProfileId = stdProfile.Id, TimeZoneSidKey = 'America/Los_Angeles',
        Username = 'stduser' + Datetime.now().getTime() + '@test.com'
    );
    insert testUser;

    Account a;
    System.runAs(testUser) {
        a = new Account(Name = 'Test');
        insert a;

        Test.startTest();
        List<Account> results = AccountController.getAccounts();
        Test.stopTest();

        System.assert(!results.isEmpty(), 'Standard user should see their own accounts');
    }
}
```

**Detection hint:** Test methods for `@AuraEnabled` or REST resource methods that never use `System.runAs()` with a non-admin user.

---

## Anti-Pattern 7: Treating `System.runAs` as an optional security nicety when the code under test enforces user mode

**What the LLM generates:**

```apex
@IsTest
private class Tier2EscalationServiceTest {

    @TestSetup
    static void seed() {
        // Mixed-DML fence. The LLM has seen this idiom and believes it is "the runAs part".
        System.runAs(new User(Id = UserInfo.getUserId())) {
            insert new Group(Name = 'Tier 2', DeveloperName = 'Tier_2', Type = 'Queue');
        }
        insert TestDataFactory.createCases(200, null, null);
    }

    @IsTest
    static void escalationStampsTheCase() {
        // Runs as whoever is deploying. Tier2EscalationService queries WITH USER_MODE.
        List<Case> due = [SELECT Id, Tier2_Notified_At__c FROM Case LIMIT 2];
        Test.startTest();
        Tier2EscalationService.escalate(due);
        Test.stopTest();
        Assert.areEqual(2, [SELECT COUNT() FROM Case WHERE Tier2_Notified_At__c != NULL]);
    }
}
```

**Why it happens:** the model has absorbed "tests should use `runAs` to check FLS and sharing" as a quality suggestion — something that makes a good test better — and prioritises it below assertions, bulk coverage, and mocking. It has separately absorbed `System.runAs(new User(Id = UserInfo.getUserId()))` as the mixed-DML fix, and the presence of that block makes the class *look* like it handles user context. Both beliefs are load-bearing and both are wrong here. When the code under test enforces user mode, `runAs` is not a quality improvement, it is a compile-and-deploy dependency: the test suite is the first user-mode caller the code ever has, and it runs at validation time. Anti-Pattern 6 describes the same missing construct with a milder consequence (a test that passes for the wrong reason); this is the version where the deploy does not happen at all.

**Correct pattern:** build the user with `templates/apex/tests/TestUserFactory.cls`, assign the permission set(s) the deployment ships, and put the assertions inside `System.runAs(testUser)` — full worked class in `references/examples.md` Example 5. The minimum shape:

```apex
@TestSetup
static void seed() {
    User agent;
    System.runAs(new User(Id = UserInfo.getUserId())) {          // mixed-DML fence only
        agent = TestUserFactory.createUser('Standard User',
            new List<String>{ 'Tier2_Webhook_Admin' });          // the permission set this build ships
    }
    System.runAs(agent) { insert TestDataFactory.createCases(200, null, null); }
}

@IsTest
static void escalationStampsTheCase() {
    System.runAs([SELECT Id FROM User WHERE Alias LIKE 'tu%' ORDER BY CreatedDate DESC LIMIT 1]) {
        // ... query, act, assert, all as the permissioned user
    }
}
```

**Detection hint:** grep the tree for `WITH USER_MODE`, `AccessLevel.USER_MODE`, `as user`, `as system`, `WITH SECURITY_ENFORCED` or `stripInaccessible` in non-test classes; then check whether the test classes beside them contain a `System.runAs` whose argument is anything other than `new User(Id = UserInfo.getUserId())`. `check_test_class_standards.py` automates exactly this as `user-mode-test-without-runas` (ERROR). A second, cheaper tell: the permission set is in `package.xml` and the string `PermissionSetAssignment` appears nowhere in the test classes.

---

## Anti-Pattern 8: A test data factory assigns a nullable lookup argument unconditionally

**What the LLM generates:**

```apex
public static List<Case> createCases(Integer count, Id accountId, Map<String, Object> overrides) {
    List<Case> out = new List<Case>();
    for (Integer i = 0; i < count; i++) {
        Case c = new Case(
            Subject   = 'Test Case ' + i,
            Status    = 'New',
            AccountId = accountId   // caller passed null — this still "sets" the field
        );
        applyOverrides(c, overrides);
        out.add(c);
    }
    return out;
}
```

**Why it happens:** the LLM treats a constructor field list as documentation of "the fields this object has," not as the literal set of fields the DML request will carry. It doesn't model that assigning a variable — even a null one — into a field marks that field populated on the sObject, indistinguishable from a real value once the constructor returns. This is invisible in every ordinary test because `Database.insert` in system mode ignores FLS entirely; the bug only fires once the DML runs as a real user (Gotcha 14), by which point the factory looks unrelated to the failure.

**Correct pattern:** construct the record without the lookup, then assign it conditionally — `if (accountId != null) { c.AccountId = accountId; }` — for every lookup argument in the factory, not only the one the current test happens to exercise. See `templates/apex/tests/TestDataFactory.cls`.

**Detection hint:** grep factory methods for `<Field> = <parameter>` inside an object constructor where `<parameter>` is a nullable `Id` argument. If the caller ever passes `null` for that argument and the class under test enforces user-mode DML, the seed will fail with `Operation failed due to fields being inaccessible on Sobject <Type>` naming exactly that field once probed with `getDmlFieldNames` (Gotcha 14).

---

## Anti-Pattern 9: Widening the persona's permission set to make a fixture insert succeed

**What the LLM generates:** a `@TestSetup` seed insert running inside `System.runAs(agent)` fails with `Operation failed due to fields being inaccessible on Sobject Case ... fieldNames: EntitlementId`, and the fix the model proposes is to add `EntitlementId` to the persona's permission set:

```xml
<!-- "fixing" the test by widening what the persona can do in production -->
<fieldPermissions>
    <editable>true</editable>
    <field>Case.EntitlementId</field>
    <readable>true</readable>
</fieldPermissions>
```

**Why it happens:** the model treats a fixture-insert failure inside `System.runAs(persona)` as proof the persona needs that field, because Gotcha 13 taught it that `runAs`-failures-on-DML mean "grant the missing permission." That heuristic is correct when the field is one the persona's own layout or process writes. It is wrong when the field is fixture plumbing — populated only so the test record is complete enough to exercise the logic under test, not because the persona's job requires setting it. The model has no signal distinguishing the two failure shapes, so it applies the Gotcha 13 fix uniformly and ships a persona with more access than any layout, process, or requirement asked for — silently reintroducing the mirror-image defect `admin/permission-sets-vs-profiles` Gotcha "An Object Grant Without Field Grants Is A Persona That Cannot Fill In A Form" describes, this time as an over-grant discovered by a test rather than an under-grant discovered by one.

**Correct pattern:** ask whether the field is on the persona's own layout, compact layout, or intake process before touching the permission set. If it is not, the fixture is the thing to fix, not the access model — seed it in system mode:

```apex
@TestSetup
static void seed() {
    User agent;
    System.runAs(new User(Id = UserInfo.getUserId())) {
        agent = TestUserFactory.createUser('Standard User',
            new List<String>{ 'Case_Agent_Core', 'Case_Tier1' });
    }
    // Fixture-only field (EntitlementId): not on the Tier 1 layout or intake
    // process, so it is not the persona's to grant. Seed in system mode.
    List<Case> cases = TestDataFactory.createCases(200, null,
        new Map<String, Object>{ 'EntitlementId' => testEntitlementId });
    TestDataFactory.insertAsSystem(cases);
}

@IsTest
static void agentEscalatesCase() {
    System.runAs(getSeededAgent()) {
        // only the action under test runs as the persona
    }
}
```

**Detection hint:** a permission-set edit made in direct response to a test failure, where the added field does not appear in the layout, compact layout, or intake process cited anywhere in the same PR or build step. Cross-check against `skills/admin/permission-sets-vs-profiles/scripts/check_access_model.py`'s `PSVP-FLS-01` finding history — a field added to silence a test failure without a matching layout citation is the tell.
