---
name: apex-test-setup-patterns
description: "@TestSetup method semantics: one-time creation per test class, isolation behavior, @TestVisible, System.runAs, Test.startTest/stopTest governor reset, mixed-DML boundaries. NOT for building a test data factory (use test-data-factory-patterns). NOT for mocking callouts (use apex-http-callout-mocking)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
tags:
  - apex
  - testing
  - testsetup
  - runas
  - governor-limits
triggers:
  - "@testsetup method apex runs once per test class"
  - "test setup data visibility across test methods"
  - "test.startest test.stoptest governor limit reset"
  - "@testvisible private field apex test access"
  - "system.runas mixed dml setup vs hierarchy"
  - "testsetup fails test class aborts all tests"
inputs:
  - Test class objective
  - Shared data volume per test method
  - User-context test requirements
outputs:
  - "@TestSetup block with factory calls"
  - runAs scope plan
  - startTest/stopTest governor reset placement
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-22
---

# Apex Test Setup Patterns

Activate when writing or reviewing an Apex test class. `@TestSetup` controls one-time data creation shared across every test method, `Test.startTest()`/`Test.stopTest()` define the governor-reset boundary, and `System.runAs` defines which user the test impersonates. Getting any of these wrong produces tests that pass flakily, misreport coverage, or exercise the wrong user context.

## Before Starting

- **Decide what goes in setup vs per-test.** Setup data is rolled back after the class finishes, not after each method — but each method sees a fresh rollback-to-setup snapshot.
- **Plan the runAs scope.** Setup runs as the test-class user unless wrapped in `System.runAs`.
- **Identify governor-reset needs.** Any async/bulk work inside `Test.startTest()` gets its own 100-callout / 100-SOQL / etc. budget.

## Core Concepts

### @TestSetup

```
@IsTest
private class AccountServiceTest {
    @TestSetup
    static void setup() {
        Account[] accs = new List<Account>{
            new Account(Name = 'A1'),
            new Account(Name = 'A2')
        };
        insert accs;
    }

    @IsTest static void testFoo() {
        Account a = [SELECT Id FROM Account WHERE Name = 'A1'];
        // ...
    }
}
```

Runs once per test class before any test method. Each test method starts with setup-state data; changes made inside a test method are rolled back after that method completes.

### Test.startTest() / Test.stopTest()

```
Test.startTest();
// Code inside gets a fresh set of governor limits.
// Any async jobs enqueued here (Queueable, future, Batch) run synchronously at stopTest().
Test.stopTest();
```

Critical for two reasons:
1. **Governor reset** — isolates setup work from the code-under-test's limit budget.
2. **Async flush** — future/Queueable/Batch jobs registered before `stopTest` execute synchronously when `stopTest` is called.

### @TestVisible

Annotation on a `private` member that makes it visible to test classes (but NOT to production code). Use when tests need to inject state or call a helper that shouldn't be `public`.

```
public class OrderService {
    @TestVisible private static Integer retryCount = 3;
    @TestVisible private static Boolean simulateFailure = false;
}
```

### System.runAs

```
User u = [SELECT Id FROM User WHERE Profile.Name = 'Standard User' LIMIT 1];
System.runAs(u) {
    // DML as that user; CRUD/FLS/Sharing enforced per their profile
}
```

Also the only way around **mixed DML** — setup-object DML (User, UserRole, Group) cannot coexist with non-setup DML in a test unless isolated via `System.runAs(new User(Id = UserInfo.getUserId()))`.

### Mixed DML workaround

```
System.runAs(new User(Id = UserInfo.getUserId())) {
    insert new User(...);  // setup-object DML
}
insert new Account(...);    // non-setup DML — now legal
```

## Common Patterns

### Pattern: Setup with runAs for ownership

```
@TestSetup
static void setup() {
    User u = TestUserFactory.createStandardUser();
    insert u;
    System.runAs(u) {
        insert new Account(Name = 'Owned by u');
    }
}
```

### Pattern: startTest for async flush

```
@IsTest static void testQueueable() {
    Test.startTest();
    System.enqueueJob(new MyQueueable());
    Test.stopTest();  // Queueable runs synchronously here
    System.assertEquals(1, [SELECT COUNT() FROM Task]);
}
```

### Pattern: @TestVisible injection for failure simulation

```
@IsTest static void testRetryOnFailure() {
    OrderService.simulateFailure = true;  // @TestVisible flag
    // assert retries
}
```

## Decision Guidance

| Situation | Approach |
|---|---|
| Multiple tests share identical data | `@TestSetup` |
| Each test needs unique/customized data | Per-method inline creation |
| Exercising async (future/Queueable/Batch) | Wrap in `Test.startTest/stopTest` |
| Need to test a different user's perspective | `System.runAs(u)` |
| Mixed setup + non-setup DML | `System.runAs` guard around setup-object DML |
| Override a private internal flag | `@TestVisible` |

## Recommended Workflow

1. Identify data common to every test method → move to `@TestSetup`.
2. Create users in `@TestSetup` via a `TestUserFactory` inside `System.runAs(new User(Id = UserInfo.getUserId()))` to avoid mixed DML.
3. Per-method: wrap code-under-test in `Test.startTest()` / `Test.stopTest()`.
4. For async, enqueue before `stopTest`; assert results after.
5. For user-perspective tests, use `System.runAs(u) { ... }` inside the method.
6. Use `@TestVisible` sparingly — prefer dependency injection via method params.
7. Never use `SeeAllData=true` on new tests.

## Review Checklist

- [ ] `@TestSetup` used for shared data (not repeated per method)
- [ ] Setup-object DML (User, Role, Group) isolated via `System.runAs`
- [ ] `Test.startTest/stopTest` wraps code-under-test
- [ ] Async jobs flushed at `stopTest`
- [ ] No `SeeAllData=true`
- [ ] `@TestVisible` used only where DI isn't feasible
- [ ] Setup method itself does not depend on org data

## Salesforce-Specific Gotchas

1. **If `@TestSetup` throws, all test methods in the class fail.** Keep setup focused; move optional data to per-method builders.
2. **`Test.stopTest()` resets limits only once per test method.** You cannot nest start/stop pairs.
3. **`@TestSetup` runs once — not once per method.** Static variables set inside setup persist across methods.
4. **Mixed DML rule doesn't apply in `@TestSetup`** when `System.runAs` isn't present — the initial setup user context allows it. But if you enter a `runAs` block you're back to mixed-DML constraints.

## Output Artifacts

| Artifact | Description |
|---|---|
| Test class with `@TestSetup` | Shared data block |
| runAs wrapper patterns | User-context isolation + mixed-DML guards |
| `Test.startTest/stopTest` placement | Governor + async flush discipline |

## Related Skills

- `apex/test-data-factory-patterns` — shared data factory design
- `apex/apex-http-callout-mocking` — mocking HTTP in tests
- `apex/apex-system-runas` — user-context testing details
