# Gotchas — Test Class Standards

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Async Work Finishes At `Test.stopTest()`, Not Before

**What happens:** A test enqueues a Queueable, immediately queries the database, and finds no updates.

**When it occurs:** Async code is exercised without a proper `Test.startTest()` / `Test.stopTest()` boundary.

**How to avoid:** Place the action under test between `startTest()` and `stopTest()`, and assert after `stopTest()`.

---

## Gotcha 2: `SeeAllData=true` Masks Missing Setup

**What happens:** The test passes in one sandbox because existing Accounts, Record Types, or custom settings happen to exist. The deployment then fails in another org.

**When it occurs:** Teams use live org data as a shortcut instead of building factories or isolated setup.

**How to avoid:** Default to isolated test data. If `SeeAllData=true` is truly required, document the reason and keep the test as narrow as possible.

---

## Gotcha 3: Mixed DML Can Break Perfectly Good Tests

**What happens:** A test creates a `User` and setup-related records alongside normal business records and gets a Mixed DML exception.

**When it occurs:** Permission, role, queue, or user setup is created in the same transaction as non-setup object DML.

**How to avoid:** Separate setup-object creation patterns appropriately, and design factories with user setup in mind when security context matters.

---

## Gotcha 4: Assertion-Light Tests Create False Confidence

**What happens:** Coverage looks healthy, but a production regression slips through because the tests only assert on counts or `System.assert(true)`.

**When it occurs:** Teams optimize for deployment thresholds instead of behavior contracts.

**How to avoid:** Assert on specific field values, thrown exceptions, related records, and failure-path outcomes.

---

## Gotcha 5: The Stub API Cannot Mock Every Apex Member

**What happens:** A developer reaches for `Test.createStub()` to fake a static utility method, a private helper, or a trigger, and the stub silently fails to intercept the call or throws at stub-creation time.

**When it occurs:** The mocked type exposes the collaboration point as a static or `@future` method, a private method, a property getter/setter, a trigger, an inner class, a system type, a class that implements the `Batchable` interface, or a class that has only private constructors — none of which the Stub API supports. The mocked type must also be in the same namespace as the `Test.createStub()` call.

**How to avoid:** Design the seam you want to mock as a non-static, non-private instance method on a top-level class. If a static utility must be substituted, wrap it behind an injectable instance method, or fall back to a hand-written test double for that specific case.

---

## Gotcha 6: `Assert` Messages Must Be Strings

**What happens:** Code that passed an sObject or other object as the message argument to `System.assertEquals` fails to compile when mechanically converted to the `Assert` class.

**When it occurs:** Migrating legacy assertions where the third argument was a non-`String` object; the legacy `System.assert*` methods tolerated arbitrary objects, but the `Assert` methods require a `String` message.

**How to avoid:** Pass an explicit `String` message (call `String.valueOf(...)` if you were relying on an object's debug form). The legacy methods remain supported, so there is no need to migrate working tests purely for style.

---

## Gotcha 7: `@TestSetup` Is Not Allowed In A `SeeAllData=true` Class

**What happens:** A class is annotated `@IsTest(SeeAllData=true)` and its `@TestSetup` method silently stops being the shared fixture — the compiler rejects it, or the team deletes it and duplicates the setup into every method.

**When it occurs:** Someone adds `SeeAllData=true` to an existing class that already had a working `@TestSetup` method. "Test setup methods are supported only with the default data isolation mode for a test class. If the test class or a test method has access to organization data by using the `@IsTest(SeeAllData=true)` annotation, test setup methods aren't supported in this class" (apexdev L6272-L6273).

**How to avoid:** Treat `SeeAllData=true` as a whole-class decision that costs you the shared fixture, and split the one method that genuinely needs org data into its own class. Note also that `@IsTest(SeeAllData=false)` on a method inside a `SeeAllData=true` class is ignored (apexdev L5812-L5813), and that `SeeAllData=true` cannot be combined with `@IsTest(IsParallel=true)` (apexdev L5824), so one careless annotation drops the class out of the parallel pool.

---

## Gotcha 8: Static State Does Not Carry From `@TestSetup` Into A Test Method

**What happens:** A test seeds a static cache, a `Map` of record Ids, or a feature-flag singleton in `@TestSetup`, then reads it in a test method and finds it empty or back at its initializer value.

**When it occurs:** Any time state is passed between methods through a static rather than through the database. "Every test method, including the test setup method, runs as a separate transaction. The static context of the test class is reinitialized before each transaction begins" (apexdev L41032-L41034), and a static changed in one test method is not visible to the next (apexdev L40551-L40553).

**How to avoid:** Pass state through queried records, not statics. If the code under test caches in a static, assert that the cache repopulates from scratch rather than assuming a warm cache — and use `@TestVisible` to reset it explicitly at the top of the method that depends on it.

---

## Gotcha 9: `Test.setMock` Must Come After `Test.startTest()` When DML Ran First

**What happens:** A test inserts records, registers a callout mock, runs the method, and fails with an uncommitted-work error instead of receiving the mock response.

**When it occurs:** "By default, callouts aren't allowed after DML operations in the same transaction because DML operations result in pending uncommitted work that prevents callouts from executing" — the fix is that "the `Test.startTest` statement must appear before the `Test.setMock` statement", and the DML must sit outside the `startTest`/`stopTest` block (apexdev L35135-L35141).

**How to avoid:** Fix the order: DML, then `Test.startTest()`, then `Test.setMock(...)`, then the action, then `Test.stopTest()`. DML that happens *after* the mock callout needs no special handling.

---

## Gotcha 10: A Published Platform Event Is Not Delivered Until `Test.getEventBus().deliver()`

**What happens:** A test publishes a platform event and asserts on what the event trigger should have written. Nothing was written, because the subscriber never ran.

**When it occurs:** `EventBus.publish(...)` inside a test queues the message; the platform-event trigger fires only when the test explicitly delivers it (apexdev L29673-L29674). For a `BatchApexErrorEvent` raised by a failed batch job, the `deliver()` call belongs after `Test.stopTest()` (apexdev L17912-L17916).

**How to avoid:** Publish, call `Test.getEventBus().deliver()`, then assert. If the subscriber itself publishes a downstream event, add another `deliver()` for each hop (apexdev L17938-L17940). Capture the `EventBus.publish` result rather than discarding it, so a failed publish is visible in the test rather than showing up as a missing side effect.

---

## Gotcha 11: Every `System.runAs` Call Spends A DML Statement

**What happens:** A test that loops `System.runAs` over a set of users to prove per-profile visibility hits the 150-DML-statement limit before it finishes, and the failure looks unrelated to sharing.

**When it occurs:** "Every call to `runAs` counts against the total number of DML statements issued in the process" (apexdev L41339). A per-user loop therefore burns one statement per iteration on top of the DML the test itself performs.

**How to avoid:** Mint the users in bulk once (`TestUserFactory.createUsers`), then use a small fixed number of `runAs` blocks — one per access profile you actually need to distinguish — rather than one per record. Remember that inside a `runAs` block the user's sharing and object/field permissions are enforced regardless of the test class's `with sharing` mode (apexdev L41331-L41333).

---

## Gotcha 12: Some Records Cannot Be Created In A Test At All

**What happens:** A factory method for history, feed, or a non-createable standard object compiles, then fails at run time or silently inserts nothing, and the test that depends on it is quietly disabled.

**When it occurs:** "Some standard objects aren't creatable" (apexdev L40772); field history and `FeedTrackedChange` records "can't be created in test methods because they require other sObject records to be committed first" (apexdev L40776-L40782); and sObjects with unique constraints (`CollaborationGroup`, for example) reject duplicate inserts whether or not `SeeAllData=true` is set (apexdev L40773-L40775).

**How to avoid:** Check creatability before designing the fixture. Where the record genuinely cannot be made, test the layer above it against a stub or a mock instead of the record, and say so in a comment. `Test.loadData(Account.sObjectType, 'myResource')` (apexdev L40896-L40904) covers the separate case of bulk fixture data that is tedious to build in code but perfectly creatable.
