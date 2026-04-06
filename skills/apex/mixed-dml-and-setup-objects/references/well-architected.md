# Well-Architected Notes — Mixed DML and Setup Objects

## Relevant Pillars

- **Reliability** — Mixed DML errors are runtime failures that can crash otherwise correct business logic. Proper transaction boundary design prevents unexpected failures in production and test suites.
- **Security** — The mixed DML restriction exists to protect sharing model integrity. Setup object changes affect org-wide permissions, and allowing them in the same transaction as data DML could produce records with inconsistent access grants. Respecting this boundary upholds the principle that security state is always consistent when data is committed.
- **Operational Excellence** — Clear patterns for handling mixed DML reduce debugging time and prevent brittle test suites. Teams that understand the restriction write more maintainable automation.

## Architectural Tradeoffs

- **Synchronous consistency vs. async deferral:** In production, moving setup DML to `@future` means the setup change is eventually consistent, not immediately consistent. If downstream logic depends on the setup object existing (e.g., querying the new User), it must account for the async delay or use platform events to coordinate.
- **Test simplicity vs. test accuracy:** Using `System.runAs()` in tests adds structural overhead but accurately reflects the transaction isolation that production code must also respect. Skipping it leads to tests that pass locally but fail when integrated.
- **Centralized factory vs. inline setup:** Centralizing mixed DML handling in a test data factory (see `test-data-factory-patterns`) reduces duplication but requires all developers to use the factory consistently.

## Anti-Patterns

1. **Ignoring the restriction until tests fail** — developers who do not classify DML targets upfront end up debugging cryptic runtime errors. Proactive classification during design prevents wasted cycles.
2. **Wrapping all test DML in System.runAs() indiscriminately** — using `System.runAs()` everywhere obscures which DML actually requires isolation. It should be used precisely for setup-object DML, not as a blanket wrapper.
3. **Using try/catch to swallow MIXED_DML_OPERATION** — catching the exception does not fix the underlying problem. The DML that threw the exception did not commit, so the data is incomplete.

## Official Sources Used

- Apex Developer Guide: sObjects That Cannot Be Used Together in DML Operations — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dml_non_mix_sobjects.htm
- Apex Developer Guide: Mixed DML Operations in Test Methods — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dml_non_mix_sobjects_test_methods.htm
- Apex Developer Guide: System.runAs — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_tools_runas.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
