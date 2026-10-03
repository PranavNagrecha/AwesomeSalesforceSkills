# Well-Architected Notes — Test Data Factory Patterns

## Relevant Pillars

- **Reliability** — A well-structured factory class makes the test suite reliable. Tests that create their own data are isolated from org data changes, from other test methods, and from environment differences between sandbox and production. Tests that use `SeeAllData=true` are fragile because they depend on what data happens to exist in the org.
- **Operational Excellence** — A centralized factory class means that required field changes, validation rule additions, or data model evolution require changes in one place, not in every test class that creates that object. This is the primary operational value of the factory pattern.

## Architectural Tradeoffs

**`@testSetup` shared baseline vs per-test factory calls:** `@testSetup` is faster (runs once per class) but creates a shared state that tests must modify per-test via update. Per-test factory calls are slower but each test is fully independent. For large test suites (50+ test methods), `@testSetup` is worth the shared-state complexity. For small suites, per-test factory calls are simpler.

**Factory depth: full hierarchy vs minimal valid record:** A factory that creates the full Account > Contact > Opportunity > Quote hierarchy on every call is convenient but slow. A minimal factory that only creates what the test specifically needs is faster but requires more setup per test. Teams with slow test suites should profile factory overhead and consider lazy/on-demand hierarchy creation.

## Anti-Patterns

1. **`@isTest(SeeAllData=true)`** — tests that read from org data are fragile, environment-specific, and cannot run in scratch orgs. They break when an admin changes data or when the test runs in a sandbox with different records. Use factory methods to create all test data.
2. **Hardcoded record IDs in factories** — hardcoding RecordTypeId, ProfileId, or RoleId values that are org-specific causes tests to fail when deployed to any other org. Always query by Name or DeveloperName.
3. **Mixed DML without `System.runAs()`**: DML on setup objects (a user with a role, a permission set assignment, a group member) in the same transaction as Account or Contact DML raises a mixed DML error. The Apex Developer Guide notes that mixed DML validation is skipped during deployment, so the same suite can pass a deploy and fail when run in the UI. Enclose setup DML in `System.runAs()`.

## Official Sources Used

Fetched and read on 2026-10-03 (release 262, Summer '26, API 67.0).

- Apex Developer Guide, Version 67.0: Isolation of Test Data from Organization Data in Unit Tests, Using the isTest(SeeAllData=True) Annotation, Loading Test Data, Common Test Utility Classes for Test Data Creation, Using Test Setup Methods (and Test Setup Method Considerations), Using the runAs Method, sObjects That Cannot Be Used Together in DML Operations, Mixed DML Operations in Test Methods, Custom Settings (test isolation note). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Salesforce Developer Limits and Allocations Quick Reference, release 262: Per-Transaction Apex Limits (150 DML statements, 10,000 DML rows). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf
- Apex Reference Guide, Version 67.0: System Class `runAs(userSObject)` (implicit insert, license limits, mixed DML note). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_reference_guide.pdf
- Salesforce Well-Architected Overview, archived 2026-06-16. http://web.archive.org/web/20260616115029/https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Listed by an earlier version of this skill and not re-fetched on 2026-10-03 (the atlas pages return a script shell): Apex Developer Guide topic pages apex_testing_utility_classes.htm, apex_testing_testsetup_using.htm, apex_dml_non_mix_sobjects_test_methods.htm, apex_testing_tools_runas.htm under https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/. The same content was read in the PDF above.
