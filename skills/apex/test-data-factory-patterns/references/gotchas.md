# Gotchas — Test Data Factory Patterns

## 1. @testSetup Records Are Rolled Back Between Test Methods But NOT Between Runs

**What happens:** A test class uses `@testSetup` to create 200 Cases. Test method A updates 50 of them to Status=Closed. Test method B queries all Cases and expects 200 open cases — but gets only 150 because Test A's updates persisted within the test run.

**Why:** Salesforce uses a transaction savepoint to roll back DML from each test method. The `@testSetup` data is preserved because it was created before the savepoint. Changes made BY a test method (update, delete) DO roll back after that method completes. However, if Test A updates records and those updates are within `@testSetup`'s scope, the test isolation is correct.

The actual gotcha: tests that DELETE `@testSetup` records — the delete rolls back but leaves the factory in an inconsistent state for complex hierarchies. Design tests to update, not delete, `@testSetup` records.

**How to avoid:** Never delete `@testSetup` records in test methods. Use status fields or other indicators to simulate deletion semantics.

---

## 2. Validation Rules Added After Factory Is Written Break All Tests

**What happens:** The factory creates Account records with only `Name` populated. An admin adds a validation rule requiring `BillingCountry` to be a valid ISO country code. Every single test that creates an Account now fails with `FIELD_CUSTOM_VALIDATION_EXCEPTION`.

**Why:** Validation rules apply in test context by default (unless the test uses `Test.startTest()/Test.stopTest()` with specific DML options, which is not standard). The factory had no reason to include `BillingCountry` when the validation rule didn't exist.

**How to avoid:** When adding validation rules to standard objects, always check which factory methods create that object and add the required field. A CI/CD gate that runs all tests after every metadata deployment catches this before production.

---

## 3. Profile and RecordType IDs Are Org-Specific

**What happens:** A developer hardcodes `ProfileId = '00e50000000rFxy'` (the admin profile ID from their sandbox) in the factory. The tests pass in the developer's sandbox and fail in every other environment with "invalid profile ID".

**Why:** Profile IDs, RecordType IDs, and RoleId values are generated per-org. A 15-character ID from one org is not valid in another org.

**How to avoid:** Always query by Name: `[SELECT Id FROM Profile WHERE Name = 'Standard User' LIMIT 1]`. Cache the result in a `static final` in the factory class so it is queried once per test run.

---

## 4. Bulk Factory Insertions Must Use a Single DML Call

**What happens:** A factory method uses a loop to insert records one at a time:
```apex
for (Integer i = 0; i < count; i++) {
  insert new Case(Subject = 'Test ' + i, ...);
}
```
A test that calls this with count=200 hits the 150 DML statement limit and fails.

**Why:** Salesforce allows 150 DML statements per transaction. Each `insert` in a loop is one DML statement.

**How to avoid:** Build a List of records in the loop and execute a single `insert records` after the loop. This is also required to test trigger bulk behavior — triggers fire once per batch when you bulk insert, which is the production scenario.
