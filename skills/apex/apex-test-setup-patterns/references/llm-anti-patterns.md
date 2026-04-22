# LLM Anti-Patterns — Apex Test Setup Patterns

Common mistakes AI coding assistants make when structuring Apex tests.

## Anti-Pattern 1: Duplicating setup data in every test method

**What the LLM generates:**

```
@IsTest static void testA() {
    Account a = new Account(Name = 'X');
    insert a;
    // ...
}
@IsTest static void testB() {
    Account a = new Account(Name = 'X');
    insert a;
    // ...
}
```

**Why it happens:** Model doesn't reason about test-class lifecycle.

**Correct pattern:**

```
@TestSetup
static void setup() {
    insert new Account(Name = 'X');
}

Runs once per class. Each method starts with a fresh rollback-to-setup
snapshot. Duplication wastes CPU budget and inflates test time linearly
with method count.
```

**Detection hint:** Identical `insert` blocks at the top of every `@IsTest` method.

---

## Anti-Pattern 2: Omitting Test.startTest / Test.stopTest around async

**What the LLM generates:**

```
@IsTest static void testQueueable() {
    System.enqueueJob(new MyQueueable());
    System.assertEquals(1, [SELECT COUNT() FROM Task]);
}
```

**Why it happens:** Model treats async enqueue like DML.

**Correct pattern:**

```
Test.startTest();
System.enqueueJob(new MyQueueable());
Test.stopTest();  // Queueable runs synchronously HERE
System.assertEquals(1, [SELECT COUNT() FROM Task]);

Without startTest/stopTest, the Queueable is still registered but
runs AFTER the test method completes — assertions fire against
pre-execution state and silently pass.
```

**Detection hint:** `System.enqueueJob` / `@future` / `Database.executeBatch` in a test without `Test.startTest`.

---

## Anti-Pattern 3: `SeeAllData=true` to "fix" a failing test

**What the LLM generates:** `@IsTest(SeeAllData=true)` when setup data is cumbersome.

**Why it happens:** Model takes the path of least resistance.

**Correct pattern:**

```
SeeAllData=true couples the test to org state — it will pass in one
sandbox and fail in another. It's also disallowed for most new
tests since API v24.

Instead:
- Create a TestDataFactory class
- Seed exactly the data the test needs in @TestSetup
- Use System.runAs for user-context tests

The only legitimate uses: testing against org-wide objects that
cannot be inserted (Pricebook2 standard pricebook).
```

**Detection hint:** `@IsTest(SeeAllData=true)` on a new test class.

---

## Anti-Pattern 4: Mixing user-DML with Account-DML without runAs

**What the LLM generates:**

```
insert new User(...);
insert new Account(OwnerId = u.Id);  // MIXED_DML_OPERATION
```

**Why it happens:** Model forgets that User/UserRole/Group are "setup objects."

**Correct pattern:**

```
System.runAs(new User(Id = UserInfo.getUserId())) {
    insert new User(...);
}
insert new Account(...);   // now legal

The runAs wrapper flushes the setup DML in a separate transaction
context, letting non-setup DML proceed in the outer frame.
```

**Detection hint:** Test inserts both `User` (or `Group`/`UserRole`) and a standard sObject in the same transaction without a `System.runAs` guard.

---

## Anti-Pattern 5: Asserting on `Trigger.new` via `@TestVisible` static

**What the LLM generates:**

```
public class Handler {
    @TestVisible private static List<Account> processed = new List<Account>();
    public void handle(List<Account> accs) { processed.addAll(accs); ... }
}

@IsTest static void t() {
    insert new Account(Name = 'X');
    System.assertEquals(1, Handler.processed.size());
}
```

**Why it happens:** Model uses `@TestVisible` as a testing swiss army knife.

**Correct pattern:**

```
@TestVisible is for injecting config/flags, not exposing internals
to avoid designing a proper assertion. Prefer asserting on side-effects:

System.assertEquals(1, [SELECT COUNT() FROM Account WHERE SomeFlag__c = true]);

Leaking internal state couples tests to implementation. When the
handler refactors, tests break even though behavior is unchanged.
```

**Detection hint:** `@TestVisible` on a collection/queue that tests then read to assert.
