---
name: mixed-dml-and-setup-objects
description: "Use when encountering or preventing MIXED_DML_OPERATION errors caused by DML on setup objects (User, UserRole, PermissionSet, Group, GroupMember) in the same transaction as non-setup objects. Triggers: 'MIXED_DML_OPERATION', 'setup object DML error', 'cannot insert User and Account together', 'System.runAs mixed DML', '@future setup object workaround'. NOT for general async Apex patterns — see async-apex. NOT for test data factory structure — see test-data-factory-patterns."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
triggers:
  - "MIXED_DML_OPERATION error when inserting User and Account in same test"
  - "how to insert setup and non-setup objects in one transaction"
  - "System.runAs workaround for mixed DML in test class"
  - "cannot update PermissionSetAssignment and custom object together"
  - "@future method to avoid mixed DML restriction"
  - "mixed DML error in @testSetup method"
tags:
  - mixed-dml
  - setup-objects
  - system-runas
  - future-method
  - test-isolation
inputs:
  - "which setup objects are involved (User, UserRole, PermissionSet, Group, GroupMember, etc.)"
  - "whether the code runs in test context or production context"
  - "the non-setup objects that share the transaction"
outputs:
  - "refactored code that separates setup and non-setup DML into compliant transaction boundaries"
  - "test class pattern using System.runAs() to isolate setup object DML"
  - "production code pattern using @future to defer setup object DML"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Mixed DML and Setup Objects

Use this skill when Apex code performs DML on both setup objects and non-setup objects in the same transaction. Salesforce enforces a hard runtime restriction that prevents this combination because setup object changes (permissions, roles, group membership) affect org-wide access calculations that must complete before non-setup record sharing can be evaluated. Violating this restriction throws the `MIXED_DML_OPERATION` runtime error.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify every SObject type touched by DML in the transaction. Classify each as setup or non-setup. The full setup object list includes: User, UserRole, Group, GroupMember, PermissionSet, PermissionSetAssignment, PermissionSetGroup, QueueSObject, ObjectTerritory2Association, Territory2, UserTerritory2Association, CustomPermission (when inserted via PermissionSetAssignment), and UserPackageLicense.
- Determine whether the code runs in a test context or production context, because the workarounds differ.
- Check whether the setup object DML is truly required in the same logical operation or can be deferred without breaking business logic.

---

## Core Concepts

### Why the Restriction Exists

When a setup object is modified (e.g., a User is inserted or a PermissionSetAssignment is created), Salesforce must recalculate org-wide sharing, role hierarchy access, and permission grants before any subsequent record-level operations are valid. Allowing non-setup DML in the same transaction would produce an inconsistent sharing state: records might be created under permissions that have not finished propagating. The platform prevents this by throwing `MIXED_DML_OPERATION` at runtime.

### Setup vs. Non-Setup Classification

Setup objects are those whose changes affect the security and sharing model: User, UserRole, Group, GroupMember, PermissionSet, PermissionSetAssignment, QueueSObject, and territory-related objects. Everything else — Account, Contact, Case, custom objects — is a non-setup object. The classification is not configurable; it is enforced by the platform kernel.

### The Two Workarounds

There are exactly two supported workarounds, each suited to a different execution context:

1. **`System.runAs()` in test methods** — wraps setup-object DML in a separate transaction context. This is the standard test-class solution.
2. **`@future` methods in production code** — defers setup-object DML to an asynchronous transaction. This is the only supported production solution.

There is no synchronous production workaround. You cannot trick the platform with try/catch, savepoints, or nested queueables within the same transaction.

---

## Common Patterns

### Pattern 1: System.runAs() in Test Classes

**When to use:** A test method needs both non-setup records (Account, Contact, Case) and setup records (User, PermissionSetAssignment) in the same test.

**How it works:** Create non-setup records first outside any `System.runAs()` block. Then wrap setup-object DML inside a `System.runAs(adminUser)` block, which creates a new transaction context for DML purposes.

```apex
@IsTest
static void testMixedObjectScenario() {
    // Non-setup DML first
    Account acc = new Account(Name = 'Test Corp');
    insert acc;

    // Setup DML inside System.runAs()
    User testUser;
    System.runAs(new User(Id = UserInfo.getUserId())) {
        testUser = new User(
            FirstName = 'Test', LastName = 'Runner',
            Email = 'test@example.com',
            Username = 'testrunner' + DateTime.now().getTime() + '@example.com',
            Alias = 'trun', TimeZoneSidKey = 'America/New_York',
            LocaleSidKey = 'en_US', EmailEncodingKey = 'UTF-8',
            LanguageLocaleKey = 'en_US',
            ProfileId = [SELECT Id FROM Profile WHERE Name = 'Standard User' LIMIT 1].Id
        );
        insert testUser;
    }

    // Now use testUser for assertions or further non-setup work
    System.runAs(testUser) {
        Contact con = new Contact(AccountId = acc.Id, LastName = 'Smith');
        insert con;
        System.assertNotEquals(null, con.Id);
    }
}
```

**Why not the alternative:** Inserting User and Account in the same scope without `System.runAs()` throws `MIXED_DML_OPERATION` even in test context.

### Pattern 2: @future for Production Setup-Object DML

**When to use:** Production code must create or update a setup object as a side effect of non-setup object processing (e.g., auto-provisioning a User when an Account is created).

**How it works:** Move the setup-object DML into an `@future` method. The caller performs non-setup DML synchronously, then calls the future method to handle setup objects in a separate transaction.

```apex
public class UserProvisioningService {

    public static void provisionUserForAccount(Id accountId, String email) {
        // Non-setup DML runs synchronously in the caller's transaction
        // Setup DML is deferred
        createUserAsync(accountId, email);
    }

    @future
    private static void createUserAsync(Id accountId, String email) {
        Profile stdProfile = [SELECT Id FROM Profile
                              WHERE Name = 'Customer Community User' LIMIT 1];
        Contact con = [SELECT Id, FirstName, LastName
                       FROM Contact WHERE AccountId = :accountId LIMIT 1];
        User u = new User(
            ContactId = con.Id,
            FirstName = con.FirstName, LastName = con.LastName,
            Email = email, Username = email + '.portal',
            Alias = con.LastName.left(8), ProfileId = stdProfile.Id,
            TimeZoneSidKey = 'America/New_York',
            LocaleSidKey = 'en_US', EmailEncodingKey = 'UTF-8',
            LanguageLocaleKey = 'en_US'
        );
        insert u;
    }
}
```

**Why not the alternative:** There is no synchronous workaround in production code. Queueable jobs that run in the same transaction do not help; only a genuinely separate transaction (via @future or a separate Queueable enqueued from a clean context) avoids the restriction.

### Pattern 3: @testSetup with Mixed Object Needs

**When to use:** Multiple test methods in a class need the same baseline of both setup and non-setup records.

**How it works:** In the `@testSetup` method, create non-setup records first, then wrap setup-object DML in `System.runAs()`.

```apex
@testSetup
static void setupData() {
    Account acc = new Account(Name = 'Shared Test Account');
    insert acc;

    System.runAs(new User(Id = UserInfo.getUserId())) {
        Profile p = [SELECT Id FROM Profile
                     WHERE Name = 'Standard User' LIMIT 1];
        User u = new User(
            FirstName = 'Shared', LastName = 'TestUser',
            Email = 'shared@example.com',
            Username = 'sharedtest' + DateTime.now().getTime() + '@example.com',
            Alias = 'shrd', ProfileId = p.Id,
            TimeZoneSidKey = 'America/New_York',
            LocaleSidKey = 'en_US', EmailEncodingKey = 'UTF-8',
            LanguageLocaleKey = 'en_US'
        );
        insert u;
    }
}
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Test class needs User + business records | `System.runAs()` wrapping setup DML | Creates separate transaction context; no async overhead in tests |
| Test class needs PermissionSetAssignment + records | `System.runAs()` wrapping PSA insert | Same mixed DML restriction applies to all setup objects |
| Production trigger auto-provisions a User | `@future` method for User insert | Only async separation works in production |
| Production code assigns permission sets after record creation | `@future` or Queueable for PSA insert | Must run in separate transaction |
| Batch job needs to create Users alongside records | Separate the DML into two batch classes or use @future from execute() | Batch execute() is still one transaction per chunk |

---

## Recommended Workflow

Step-by-step instructions for resolving or preventing mixed DML issues:

1. **Classify all DML targets** — list every SObject that undergoes insert, update, delete, or upsert in the transaction. Tag each as setup or non-setup.
2. **Confirm the violation** — if setup and non-setup objects are modified in the same execution context, a `MIXED_DML_OPERATION` error will occur. Identify which DML statement triggers the conflict.
3. **Choose the workaround** — if the code is a test class, use `System.runAs()`. If the code is production logic, use `@future` or Queueable.
4. **Refactor the code** — move setup-object DML into the chosen isolation boundary. Ensure the non-setup DML runs first (or in a separate scope) so that any record IDs needed by the setup DML are already committed.
5. **Test the fix** — run the affected test class. Confirm no `MIXED_DML_OPERATION` errors. Confirm that both setup and non-setup records are created correctly.
6. **Verify async behavior (production only)** — if using `@future`, confirm the method is testable via `Test.startTest()` / `Test.stopTest()` to force synchronous execution in tests.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All DML targets classified as setup or non-setup
- [ ] No setup and non-setup DML share the same synchronous execution context
- [ ] Test classes use `System.runAs()` to isolate setup-object DML
- [ ] Production code uses `@future` or Queueable for setup-object DML
- [ ] `@future` methods are tested with `Test.startTest()` / `Test.stopTest()` boundaries
- [ ] User creation uses unique username (e.g., timestamp suffix) to avoid duplicate conflicts
- [ ] `@testSetup` methods also respect the mixed DML boundary

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **PermissionSetAssignment is a setup object** — developers often forget that assigning a permission set is setup DML. Inserting a `PermissionSetAssignment` in the same transaction as a custom object record throws the same error as inserting a `User`.
2. **System.runAs() only works in test context** — calling `System.runAs()` in production code does not create a separate DML context. It only changes the running user for permission checks. The mixed DML workaround behavior is exclusive to test execution.
3. **Queueable chaining does not help within the same transaction** — enqueueing a Queueable from inside a trigger still runs the enqueue DML in the current transaction. The Queueable itself runs later, but if you perform setup DML before the enqueue, the error fires before the Queueable is even submitted.
4. **@testSetup is subject to the same restriction** — the `@testSetup` method runs as a single transaction. You must use `System.runAs()` inside it if you need both setup and non-setup records.
5. **The restriction applies to all DML operations, not just insert** — updating a User's role and updating an Account in the same transaction also triggers the error. Delete and undelete count too.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Refactored Apex class or test class | Code with setup and non-setup DML properly separated into compliant transaction boundaries |
| @future helper method | Async method that encapsulates setup-object DML for production use cases |

---

## Related Skills

- `test-data-factory-patterns` — covers factory methods that handle mixed DML in reusable test utilities
- `async-apex` — covers @future and Queueable patterns in depth, including chaining and limits
- `trigger-framework` — relevant when triggers perform setup-object DML as side effects
- `order-of-execution-deep-dive` — explains transaction boundaries and when DML contexts separate
