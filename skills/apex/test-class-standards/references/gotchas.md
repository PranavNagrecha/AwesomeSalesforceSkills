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
