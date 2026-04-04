---
name: test-data-factory-patterns
description: "Use when designing or building reusable Apex test data factories: @IsTest utility classes, SObject hierarchy construction, bulk data generation, portal user factories with System.runAs(), and @testSetup methods. NOT for test class structure and assertions (use apex/test-class-standards) or for loading data into sandboxes (use devops/data-seeding-for-testing)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I build a reusable test data factory class in Apex"
  - "test is failing with MIXED_DML_OPERATION when creating a portal user"
  - "my Apex tests are fragile because they depend on org data using SeeAllData=true"
  - "how do I create test data for 200 records to test a trigger at bulk scale"
  - "all my tests broke after an admin added a validation rule to Account"
tags:
  - apex-testing
  - test-data-factory
  - test-setup
  - bulk-testing
  - portal-users
inputs:
  - "Object hierarchy being tested (parent-child relationships)"
  - "Whether the test involves setup objects (User, Profile) or portal/community users"
  - "Bulk size requirements (e.g., 200 records per trigger batch)"
  - "Whether shared baseline data or per-test variation is needed"
outputs:
  - "Apex @IsTest utility class with factory methods for each SObject type"
  - "Pattern guidance for @testSetup vs per-method factory calls"
  - "Portal user factory pattern using System.runAs()"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Test Data Factory Patterns

This skill activates when a practitioner needs to build reusable, bulk-safe Apex test data factories. A well-structured factory class reduces duplication across test methods, enforces consistent record creation, and handles the Salesforce-specific constraints that break naive test data approaches — particularly Mixed DML for portal users and the incompatibility between `@isTest(SeeAllData=true)` and `@testSetup`.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify all SObject types the test suite needs. Map the hierarchy: parent objects must be created before child objects.
- Determine whether the tests involve **setup objects** (User, UserRole, PermissionSet, Group) alongside **non-setup objects** (Account, Case, etc.). If yes, the Mixed DML restriction applies and requires `System.runAs()`.
- Decide on the data sharing model: `@testSetup` for a shared baseline that is reset between test methods, vs factory method calls in each test for per-test variation.
- Check the governor limit budget: 150 DML statements per test transaction, 10,000 rows per DML call. Bulk factories must stay within these limits.

---

## Core Concepts

### @IsTest Utility Class and Code Size

Factory classes decorated with `@IsTest` are excluded from the org's code size limit (6 MB of Apex code). This means you can have large, comprehensive factory classes without impacting your org's Apex footprint. The `@IsTest` annotation on the class — not just on individual methods — is what triggers the exclusion.

```apex
@IsTest
public class TestDataFactory {
  // Excluded from org code size limit
  public static Account createAccount(String name, Boolean doInsert) {
    Account a = new Account(Name = name);
    if (doInsert) insert a;
    return a;
  }
}
```

### @testSetup: Shared Baseline

The `@testSetup` method runs once per test class before any test method. It inserts records into the database. Each test method then sees those records as if they were freshly inserted (Salesforce resets the database state between test methods using a savepoint/rollback mechanism).

Use `@testSetup` for records that all test methods share and that would be expensive to recreate per method (e.g., an Account hierarchy with 50 records, a complex Product + Pricebook structure).

**Constraint:** `@isTest(SeeAllData=true)` is **incompatible** with `@testSetup`. You cannot use both on the same test class. If you must use `SeeAllData=true` for a specific reason, you lose `@testSetup` and must create data in each test method.

### Mixed DML Restriction and Portal Users

Salesforce prevents inserting setup objects (User, UserRole, PermissionSet, Group, GroupMember) in the same DML transaction as non-setup objects. This restriction exists to prevent sharing model recalculation mid-transaction.

Common scenario that triggers the error: creating a portal user (a User record) and the Account/Contact it belongs to in the same transaction.

The fix is `System.runAs()`. Wrap User insertions inside a `System.runAs(adminUser)` block. Non-setup DML outside the `runAs` block, setup DML inside.

```apex
@IsTest
static void testPortalUserScenario() {
  // Step 1: Create non-setup objects first
  Account acc = TestDataFactory.createAccount('Portal Customer', true);
  Contact con = TestDataFactory.createContact(acc.Id, 'Jane', 'Doe', true);

  // Step 2: Create User (setup object) inside runAs
  User portalUser;
  System.runAs(new User(Id = UserInfo.getUserId())) {
    portalUser = TestDataFactory.createPortalUser(con.Id);
    insert portalUser;
  }

  // Step 3: Test the portal user's access
  System.runAs(portalUser) {
    // assertions here
  }
}
```

### Bulk Factory Design

Tests that validate trigger behavior must test at bulk scale (200 records). Factory methods should accept a count parameter and return a List, not a single record.

```apex
public static List<Case> createCases(Id accountId, Integer count, Boolean doInsert) {
  List<Case> cases = new List<Case>();
  for (Integer i = 0; i < count; i++) {
    cases.add(new Case(
      AccountId = accountId,
      Subject = 'Test Case ' + i,
      Status = 'New'
    ));
  }
  if (doInsert) insert cases;
  return cases;
}
```

Always use a single `insert cases` statement for bulk records — never loop and insert one by one (this hits the 150 DML statement limit and misses bulk trigger testing).

---

## Common Patterns

### Layered Factory Class

**When to use:** A test suite that creates multiple related objects (Account > Contact > Opportunity > Quote).

**How it works:**
Create one factory method per SObject type. Each method takes required fields as parameters, applies sensible defaults for required-but-uninteresting fields, and optionally inserts. Call factory methods in dependency order.

```apex
@IsTest
public class TestDataFactory {
  public static Account createAccount(String name, Boolean doInsert) {
    Account a = new Account(
      Name = name,
      BillingCity = 'San Francisco',
      BillingState = 'CA',
      BillingCountry = 'US'
    );
    if (doInsert) insert a;
    return a;
  }

  public static Contact createContact(Id accountId, String firstName, String lastName, Boolean doInsert) {
    Contact c = new Contact(
      AccountId = accountId,
      FirstName = firstName,
      LastName = lastName,
      Email = firstName + '.' + lastName + '@test.example.com'
    );
    if (doInsert) insert c;
    return c;
  }

  public static Opportunity createOpportunity(Id accountId, String name, Date closeDate, Boolean doInsert) {
    Opportunity o = new Opportunity(
      AccountId = accountId,
      Name = name,
      StageName = 'Prospecting',
      CloseDate = closeDate != null ? closeDate : Date.today().addDays(30)
    );
    if (doInsert) insert o;
    return o;
  }
}
```

**Why not hardcode data in each test:** Duplication means a required field change (added validation rule) breaks dozens of test methods. A single factory change fixes all tests at once.

### @testSetup with Per-Test Variation

**When to use:** Tests share a baseline structure but need per-test variation (e.g., all tests need an Account, but some tests need an Account with Status=Active and others with Status=Inactive).

**How it works:**
1. `@testSetup` creates the shared baseline.
2. Each test method queries for the baseline records and applies variations via DML update.

```apex
@testSetup
static void setup() {
  Account acc = TestDataFactory.createAccount('Shared Account', true);
  TestDataFactory.createCases(acc.Id, 50, true);
}

@IsTest
static void testActiveCases() {
  Account acc = [SELECT Id FROM Account LIMIT 1];
  List<Case> cases = [SELECT Id, Status FROM Case WHERE AccountId = :acc.Id];
  // apply per-test variation
  for (Case c : cases) c.Status = 'New';
  update cases;
  // test logic here
}
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| All tests share the same baseline data | `@testSetup` + factory calls | Fastest test execution; database reset is automatic per test method |
| Tests need independent, varying data | Factory method calls per test method | No risk of test interference; each test owns its data |
| Creating portal/community users | `System.runAs()` wrapping User insert | Required to avoid Mixed DML exception |
| Bulk trigger testing (200 records) | Single `insert List<SObject>` in factory | Tests the actual trigger bulk behavior; avoids 150 DML limit |
| Org has required custom fields on Account | Add required fields to factory defaults with dummy values | Prevents validation rule failures in tests |
| Testing with specific Profile | Query the Profile by Name in `@testSetup`, pass Id to user factory | Avoids hardcoding Profile IDs which differ between orgs |

---

## Recommended Workflow

1. Map the SObject hierarchy needed by the test suite. Identify parent-to-child order.
2. Check for required fields on each SObject (validation rules, required field configuration). Add these to factory method defaults.
3. Identify whether any test creates setup objects (User, UserRole). If yes, plan the `System.runAs()` wrapping.
4. Create a single `@IsTest` factory class. Add one static method per SObject type. Use `Boolean doInsert` parameter for flexibility.
5. Add bulk factory methods (accepting a count parameter, returning List) for any SObject that a trigger fires on.
6. In test classes, use `@testSetup` for shared baseline data. Use per-test factory calls only for data that varies between tests.
7. Run all tests after factory changes and verify no test uses `@isTest(SeeAllData=true)` alongside `@testSetup`.

---

## Review Checklist

- [ ] Factory class is annotated `@IsTest` at the class level (excluded from code size limit)
- [ ] Factory methods use `Boolean doInsert` parameter to allow building records without inserting
- [ ] Required fields and validation-rule-required fields are populated in factory defaults
- [ ] Portal/community user creation wraps User insert in `System.runAs()`
- [ ] Bulk factory methods insert via a single DML call, not one record at a time
- [ ] No test class uses both `@isTest(SeeAllData=true)` and `@testSetup`
- [ ] Profile IDs are queried by Name, not hardcoded

---

## Salesforce-Specific Gotchas

1. **`@isTest(SeeAllData=true)` incompatibility with `@testSetup`** — using both on the same test class throws a compile-time error. `SeeAllData=true` was designed for legacy tests that needed access to org data; `@testSetup` creates isolated test data. They cannot coexist. Remove `SeeAllData=true` whenever possible.
2. **Mixed DML: User + Account/Contact in same transaction** — this is the most common factory test failure. The error message is `MIXED_DML_OPERATION: DML operation on setup object is not permitted after you have updated a non-setup object`. Fix by separating User inserts into a `System.runAs()` block.
3. **`@testSetup` records are shared but reset between tests** — changes made by one test method (e.g., updating a record's Status) do not persist to the next test method. Salesforce rolls back DML from each test method while keeping `@testSetup` records. This is intentional but surprises developers who expect test method order to matter.
4. **Required fields change without notice** — an admin can add a validation rule that makes a previously optional field required. This silently breaks factory methods that omit that field. Run your full test suite after every metadata deployment, not just after code changes.
5. **Querying Profile by Name is org-specific** — Profile Names differ between sandbox and production if the profile was renamed. Always query `[SELECT Id FROM Profile WHERE Name = :profileName LIMIT 1]` — never hardcode a Profile ID. This ensures the factory works across environments.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| TestDataFactory.cls | @IsTest utility class with one factory method per SObject, bulk variants, and portal user factory using runAs |
| @testSetup usage guide | When to use shared baseline vs per-test factory calls, with trade-off explanation |

---

## Related Skills

- apex/test-class-standards — test class structure, assertion patterns, code coverage strategy
- devops/data-seeding-for-testing — loading data into sandboxes and scratch orgs for integration testing
- apex/apex-managed-sharing — when factory creates users needing specific sharing context
