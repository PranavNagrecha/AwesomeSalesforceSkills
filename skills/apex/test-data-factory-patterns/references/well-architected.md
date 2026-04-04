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
3. **Mixed DML without `System.runAs()`** — creating a User in the same transaction as Account or Contact causes `MIXED_DML_OPERATION` at runtime. The error often appears only in test runs, not in interactive execution, because the isolation is enforced differently. Always wrap User creation in `System.runAs()`.

## Official Sources Used

- Apex Developer Guide (Common Test Utility Classes) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_utility_classes.htm
- Apex Developer Guide (@testSetup) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_testsetup_using.htm
- Apex Developer Guide (Mixed DML Operations in Tests) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dml_non_mix_sobjects_test_methods.htm
- Apex Developer Guide (System.runAs) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_tools_runas.htm
