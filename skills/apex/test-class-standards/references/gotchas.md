# Gotchas — Test Class Standards

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Async Work Finishes At `Test.stopTest()`, Not Before

**What happens:** A test enqueues a Queueable, immediately queries the database, and finds no updates.

**When it occurs:** Async code is exercised without a proper `Test.startTest()` / `Test.stopTest()` boundary.

**How to avoid:** Place the action under test between `startTest()` and `stopTest()`, and assert after `stopTest()`.

---

## `SeeAllData=true` Masks Missing Setup

**What happens:** The test passes in one sandbox because existing Accounts, Record Types, or custom settings happen to exist. The deployment then fails in another org.

**When it occurs:** Teams use live org data as a shortcut instead of building factories or isolated setup.

**How to avoid:** Default to isolated test data. If `SeeAllData=true` is truly required, document the reason and keep the test as narrow as possible.

---

## Mixed DML Can Break Perfectly Good Tests

**What happens:** A test creates a `User` and setup-related records alongside normal business records and gets a Mixed DML exception.

**When it occurs:** Permission, role, queue, or user setup is created in the same transaction as non-setup object DML.

**How to avoid:** Separate setup-object creation patterns appropriately, and design factories with user setup in mind when security context matters.

---

## Assertion-Light Tests Create False Confidence

**What happens:** Coverage looks healthy, but a production regression slips through because the tests only assert on counts or `System.assert(true)`.

**When it occurs:** Teams optimize for deployment thresholds instead of behavior contracts.

**How to avoid:** Assert on specific field values, thrown exceptions, related records, and failure-path outcomes.

---

## The Stub API Cannot Mock Every Apex Member

**What happens:** A developer reaches for `Test.createStub()` to fake a static utility method, a private helper, or a trigger, and the stub silently fails to intercept the call or throws at stub-creation time.

**When it occurs:** The mocked type exposes the collaboration point as a static or `@future` method, a private method, a property getter/setter, a trigger, an inner class, a system type, a class that implements the `Batchable` interface, or a class that has only private constructors — none of which the Stub API supports. The mocked type must also be in the same namespace as the `Test.createStub()` call.

**How to avoid:** Design the seam you want to mock as a non-static, non-private instance method on a top-level class. If a static utility must be substituted, wrap it behind an injectable instance method, or fall back to a hand-written test double for that specific case.

---

## `Assert` Messages Must Be Strings

**What happens:** Code that passed an sObject or other object as the message argument to `System.assertEquals` fails to compile when mechanically converted to the `Assert` class.

**When it occurs:** Migrating legacy assertions where the third argument was a non-`String` object; the legacy `System.assert*` methods tolerated arbitrary objects, but the `Assert` methods require a `String` message.

**How to avoid:** Pass an explicit `String` message (call `String.valueOf(...)` if you were relying on an object's debug form). The legacy methods remain supported, so there is no need to migrate working tests purely for style.
