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
  - "write a TestDataFactory class for my Apex tests"
  - "create test users with roles and permission sets without mixed DML errors"
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Test Data Factory Patterns

This skill activates when a practitioner needs to build reusable, bulk-safe Apex test data factories. A well-structured factory class reduces duplication across test methods, enforces consistent record creation, and handles the Salesforce-specific constraints that break naive test data approaches — particularly Mixed DML for portal users and the incompatibility between `@isTest(SeeAllData=true)` and `@testSetup`.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify all SObject types the test suite needs. Map the hierarchy: parent objects must be created before child objects.
- Determine whether the tests involve **setup objects** (User, UserRole, PermissionSet, PermissionSetAssignment, Group, GroupMember, and the rest of the Apex Developer Guide list) alongside **non-setup objects** (Account, Case, etc.). If yes, the Mixed DML restriction applies; wrap the setup DML in `System.runAs()`.
- Decide on the data sharing model: `@testSetup` for a shared baseline that is reset between test methods, vs factory method calls in each test for per-test variation.
- Check the governor limit budget: 150 DML statements and 10,000 DML rows per transaction, and every `System.runAs` call counts as a DML statement. Bulk factories must stay within these limits.

## Questions to Ask Before Configuring

Ask these before writing the factory; each answer changes its shape.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which objects do the tests create, and which required fields, validation rules, or duplicate rules apply to them in every target org?" | Validation and required-field rules run in tests; a missing field fails every test that creates the object | The default field values the factory must set | One place to fix when an admin adds a rule, instead of dozens of broken tests |
| "Do any tests create users, roles, permission set assignments, or group members?" | Those are setup objects; mixing their DML with Account or Case DML raises `MIXED_DML_OPERATION` unless it runs inside `System.runAs` | The list of setup objects and which tests need them | A user factory that never mixes DML, so the suite passes in the UI and in deployments |
| "Which data must every test share, and which must vary per test?" | `@testSetup` runs once per class and resets changes after each method; static variables set there do not survive | The split between `@testSetup` baseline and per-test factory calls | Faster tests that cannot leak state between methods |
| "Does any test need org data, such as a custom setting or a price book?" | Test data isolation hides org data, and `SeeAllData=true` on any method makes `@testSetup` unsupported for the class | Whether to create the data in setup instead | A suite that runs the same in a scratch org, a sandbox, and production |
| "What volume must trigger tests cover?" | Bulk behavior only shows when records are inserted in one DML statement | The count parameter each bulk factory method needs | Tests that exercise the same code path production bulk loads use |

What a proper configuration adds over "just inserting records in each test": required-field changes are fixed once, setup and non-setup DML never collide, the suite does not depend on org data, and bulk paths are tested at production volume.

---

## Core Concepts

### @IsTest Utility Class and Code Size

Factory classes decorated with `@IsTest` are excluded from the org's code size limit (6 MB of Apex code); the Apex Developer Guide says such classes "don't count against your organization limit of 6 MB for all Apex code". This means you can have large, comprehensive factory classes without impacting your org's Apex footprint. The `@IsTest` annotation on the class, not just on individual methods, is what triggers the exclusion.

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

The `@testSetup` method runs once per test class before any test method. Records it creates are available to every test method, and any change a test method makes to them (field updates or deletions) is rolled back after that method, so the next method sees the original records. Static variables set in `@testSetup` do not carry over: every test method runs as a separate transaction with freshly initialized static context.

Use `@testSetup` for records that all test methods share and that would be expensive to recreate per method (e.g., an Account hierarchy with 50 records, a complex Product + Pricebook structure).

**Constraint:** "If the test class or a test method has access to organization data by using the @isTest(SeeAllData=true) annotation, test setup methods aren't supported in this class." One `SeeAllData=true` method is enough to lose `@testSetup` for the whole class. A class can have only one `@testSetup` method, and a fatal error in it fails the entire class.

### Mixed DML Restriction and Portal Users

Salesforce prevents DML on setup objects (UserRole, PermissionSet, PermissionSetAssignment, Group, GroupMember, and others in the Apex Developer Guide list) in the same transaction as DML on non-setup objects, because those objects change the user's access to records. A `User` insert is allowed alongside other sObjects only when `UserRoleId` is null (API 15.0+); a `User` update is allowed only when fields such as `UserRoleId`, `IsActive`, `ProfileId`, `IsPortalEnabled`, and `Username` are not changed.

Common scenarios that trigger the error: creating a user with a role, assigning a permission set, or adding a group member in the same test transaction that inserts Accounts or Contacts. Validation for mixed DML is skipped during deployment, so a suite can pass a deploy and fail when run from the UI.

The documented fix in tests is `System.runAs()`: enclose the setup-object DML in a `System.runAs(adminUser)` block, or perform it in an asynchronous job the test calls. Inside a `runAs` block the user's sharing, object permissions, and field-level security are enforced.

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

Always use a single `insert cases` statement for bulk records. Looping and inserting one by one hits the 150 DML statement limit and never exercises the bulk trigger path.

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
| Creating users with a role, permission set assignments, or group members | `System.runAs()` around the setup DML | Those are setup objects; a role-less `User` insert alone is allowed alongside other sObjects |
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
7. Run `python3 skills/apex/test-data-factory-patterns/scripts/check_test_data_factory_patterns.py --apex-dir force-app/main/default/classes`, then run all tests from the UI as well as in a validation deploy, because mixed DML validation is skipped during deployment.

---

## Review Checklist

- [ ] Factory class is annotated `@IsTest` at the class level (excluded from code size limit)
- [ ] Factory methods use `Boolean doInsert` parameter to allow building records without inserting
- [ ] Required fields and validation-rule-required fields are populated in factory defaults
- [ ] Setup-object DML (users with roles, permission set assignments, group members) runs inside `System.runAs()`
- [ ] Bulk factory methods insert via a single DML call, not one record at a time
- [ ] No test class uses both `@isTest(SeeAllData=true)` and `@testSetup`
- [ ] Profile IDs are queried by Name, not hardcoded

---

## Salesforce-Specific Gotchas

1. **`@isTest(SeeAllData=true)` disables `@testSetup` for the class.** The Apex Developer Guide says test setup methods "aren't supported" when the class or any test method has `SeeAllData=true`. UNVERIFIED (2026-10-03): whether this surfaces as a compile error or a run-time failure is not stated in the guide. Remove `SeeAllData=true` whenever possible.
2. **Mixed DML: setup-object DML plus Account/Contact DML in one transaction.** This is the most common factory test failure (a user with a role, a permission set assignment, a group member). Fix by moving the setup DML into a `System.runAs()` block. UNVERIFIED (2026-10-03): the exact error text `MIXED_DML_OPERATION: DML operation on setup object is not permitted after you have updated a non-setup object` is not printed in the fetched guide.
3. **`@testSetup` records are shared but reset between tests.** Updates and deletions made by one test method are rolled back before the next one runs, and static variables set in `@testSetup` are reinitialized. Do not cache Ids in statics during setup; query them in each method.
4. **Required fields change without notice** — an admin can add a validation rule that makes a previously optional field required. This silently breaks factory methods that omit that field. Run your full test suite after every metadata deployment, not just after code changes.
5. **Profile and RecordType IDs are org-specific.** Query `[SELECT Id FROM Profile WHERE Name = :profileName LIMIT 1]` (Profile, RecordType, and User stay visible to tests without `SeeAllData`). Profile names can still differ if a profile was renamed, so keep the name in one constant.

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
