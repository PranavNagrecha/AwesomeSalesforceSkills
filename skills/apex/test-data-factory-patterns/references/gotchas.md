# Gotchas — Test Data Factory Patterns

Non-obvious test-context behaviors that break factories in real suites. "Apex Guide" means the Apex Developer Guide, Version 67.0 (Summer '26), chapters Testing Apex and Working with Data in Apex. "Limits" means the Salesforce Developer Limits and Allocations Quick Reference, release 262.

## Gotcha 1: Static Variables Set in `@testSetup` Are Gone in Every Test Method

**What happens:** The factory stores the inserted Account Id in a static variable during `@testSetup`, and every test method finds it null.

**When it occurs:** "Every test method, including the test setup method, runs as a separate transaction. The static context of the test class is reinitialized before each transaction begins." Records survive into each test method; in-memory values do not.

**How to avoid:** Query the setup records in each test method, for example by a unique Name the factory sets. Never cache Ids or maps in statics during `@testSetup`.

**Source:** Apex Guide, Using Test Setup Methods.

---

## Gotcha 2: Changes and Deletions of `@testSetup` Records Roll Back After Each Method

**What happens:** A test expects to see the update an earlier test method made to a setup record and fails, or a developer avoids deleting setup records to "keep the hierarchy consistent".

**When it occurs:** "If a test method changes those records, such as record field updates or record deletions, those changes are rolled back after each test method finishes execution. The next executing test method gets access to the original unmodified state of those records." The guide's own example deletes a setup Account in one method and asserts it still exists in the next. An earlier version of this file claimed the opposite for updates and warned against deleting setup records; both statements were wrong.

**How to avoid:** Design every test method to start from the setup baseline. Delete or update setup records freely when the test needs it. Never rely on test method order.

**Source:** Apex Guide, Using Test Setup Methods (description and CommonTestSetup example).

---

## Gotcha 3: One `SeeAllData=true` Method Disables `@testSetup` for the Whole Class

**What happens:** A developer adds `@IsTest(SeeAllData=true)` to a single method to read a price book, and the class's `@testSetup` stops working.

**When it occurs:** "If the test class or a test method has access to organization data by using the @isTest(SeeAllData=true) annotation, test setup methods aren't supported in this class." A class can also have only one test setup method, and "if a fatal error occurs during the execution of a test setup method ... the entire test class fails". UNVERIFIED (2026-10-03): whether the SeeAllData conflict appears at save time or at run time is not stated.

**How to avoid:** Move the method that needs org data into its own class, or create the data in the factory. Keep `@testSetup` free of assertions that can fail for reasons unrelated to the class under test.

**Source:** Apex Guide, Using Test Setup Methods (Test Setup Method Considerations); Using the isTest(SeeAllData=True) Annotation.

---

## Gotcha 4: Mixed DML Is About Setup Objects, Not About Every User Insert

**What happens:** A test that inserts an Account and then a user with a role, a `PermissionSetAssignment`, or a `GroupMember` fails with a mixed DML error. Another team wraps every user insert in `System.runAs` without knowing which case needed it.

**When it occurs:** DML on setup objects (the Apex Guide list includes Group, GroupMember, PermissionSet, PermissionSetAssignment, QueueSObject, User, UserRole, UserTerritory2Association, and others) cannot be mixed with DML on other sObjects in one transaction. For `User`, the guide allows an insert alongside other sObjects "when UserRoleId is specified as null" (API 15.0+), and an update when fields such as `UserRoleId`, `IsActive`, `ForecastEnabled`, `IsPortalEnabled`, `Username`, and `ProfileId` are not changed.

**How to avoid:** In test methods, enclose the setup-object DML in a `System.runAs` block, or perform it in an `@future` method the test calls; both are documented. Keep a dedicated user factory method that does this internally.

**Source:** Apex Guide, sObjects That Cannot Be Used Together in DML Operations; Mixed DML Operations in Test Methods.

---

## Gotcha 5: Tests Pass in a Deployment and Fail in the UI

**What happens:** A validation deploy succeeds, and the same test class fails with mixed DML when a developer runs it from Setup or the Developer Console.

**When it occurs:** "Because validation for mixed DML operations is skipped during deployment, there can be a difference in the number of test failures when tests are deployed versus when run in the user interface."

**How to avoid:** Run the suite both ways before release. Treat any mixed DML failure seen in the UI as a real defect even if deployments pass.

**Source:** Apex Guide, Mixed DML Operations in Test Methods (Note).

---

## Gotcha 6: `System.runAs` Enforces Permissions and Costs a DML Statement

**What happens:** A factory that loops `System.runAs` per user hits the DML statement limit, or a test written as "admin context" starts failing on field access inside a `runAs` block.

**When it occurs:** "Every call to runAs counts against the total number of DML statements issued in the process." Inside the block, "the user's sharing rules and object-level and field-level permissions are enforced, regardless of the sharing mode ... of the test class." The method ignores user license limits, so tests can create users even when the org has no spare licenses. The Apex Reference adds that `runAs` "implicitly inserts the user that is passed in as parameter if the user has been instantiated, but not inserted yet". Decide in one place whether the factory or `runAs` inserts a given user.

**How to avoid:** Create all setup records in one `runAs` block. Grant the test user the permission sets the code under test requires before entering `runAs`. Budget `runAs` calls inside the 150-statement limit.

**Source:** Apex Guide, Using the runAs Method; Apex Reference, System Class `runAs(userSObject)`; Limits, Per-Transaction Apex Limits (150 DML statements, 10,000 DML rows).

---

## Gotcha 7: Cross-Object `Owner` References Return Null in Isolated Tests

**What happens:** A factory or class under test reads `Account.Owner.IsActive` and gets null in a test, while the same code works in the org.

**When it occurs:** "When working with data silo Apex tests, cross-object field references using the Owner relationship aren't supported. Due to this limitation, SELECT Owner.IsActive FROM Account returns null when run within a data silo Apex test."

**How to avoid:** Query the owner `User` record directly by `OwnerId` in code paths that tests exercise, or assert on `OwnerId` instead of owner fields.

**Source:** Apex Guide, Isolation of Test Data from Organization Data in Unit Tests (Data Access Considerations).

---

## Gotcha 8: Custom Settings and Most Org Data Are Invisible Without Setup Data

**What happens:** Code under test reads a hierarchy custom setting and gets defaults, so a feature flag that is on in the org is off in tests.

**When it occurs:** Custom settings data "is treated as data for the purposes of Apex test isolation", so tests see it only with `SeeAllData=true`. By default tests can see objects used to manage the org, such as `User`, `Profile`, `Organization`, `RecordType`, and `ApexClass`, but not standard or custom object data.

**How to avoid:** Give the factory a method that inserts the custom setting records the code needs, and call it from `@testSetup`. Query `Profile` and `RecordType` freely; they are visible.

**Source:** Apex Guide, Custom Settings (Note); Isolation of Test Data from Organization Data in Unit Tests.

---

## Gotcha 9: Validation Rules and Unique Fields Run in Tests

**What happens:** An admin adds a validation rule requiring `BillingCountry`, and every test that creates an Account fails with `FIELD_CUSTOM_VALIDATION_EXCEPTION`. A factory that inserts two `CollaborationGroup` records with the same name fails even with `SeeAllData=true`.

**When it occurs:** Test DML runs the same validation as production DML. The Apex Guide notes that inserting duplicates of an sObject with unique constraints fails "whether your test is annotated with IsTest(SeeAllData=true), or not". An earlier version of this file suggested `Test.startTest()` changes validation behavior; no fetched source supports that, and it is removed.

**How to avoid:** Populate every required and rule-constrained field in factory defaults, and generate unique values (for example, a counter or `DateTime.now().getTime()` suffix) for unique fields and usernames. Run the full suite after every metadata deployment, not only after code changes.

**Source:** Apex Guide, Isolation of Test Data from Organization Data in Unit Tests (unique constraints example); Using the runAs Method (unique UserName pattern).

---

## Gotcha 10: Field History and Feed Tracked Changes Cannot Be Created in Tests

**What happens:** A factory tries to build `AccountHistory` rows to test a history report and gets nothing.

**When it occurs:** "Field history tracking records can't be created in test methods because they require other sObject records to be committed first", and the same applies to `FeedTrackedChange`.

**How to avoid:** Abstract the history read behind a method that tests can stub, or assert on the parent record changes instead of history rows.

**Source:** Apex Guide, Isolation of Test Data from Organization Data in Unit Tests (limitations list).

---

## Gotcha 11: Bulk Factories Must Use One DML Statement

**What happens:** A factory method inserts records one at a time in a loop, and a test that asks for 200 records hits the DML statement limit.

**When it occurs:** Each `insert` inside a loop is a separate DML statement, and the per-transaction limit is 150. The limit on rows is 10,000 per transaction, not per call.

**How to avoid:** Build a `List<SObject>` in the loop and insert it once. That is also the only way a trigger test exercises the bulk code path.

**Source:** Limits, Per-Transaction Apex Limits; Apex Guide, Common Test Utility Classes for Test Data Creation (TestDataFactory example inserts lists).
