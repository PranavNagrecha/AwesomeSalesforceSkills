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
