# Well-Architected Notes — Test Class Standards

## Relevant Pillars

### Reliability

Reliable Salesforce delivery depends on tests that catch functional regressions before deployment. Weak tests allow defects into production even when code coverage is technically acceptable.

Tag findings as Reliability when:
- negative paths are untested
- bulk-sensitive logic has only single-record tests
- async or callout behaviors are not asserted correctly

### Operational Excellence

Operational Excellence improves when the test suite is deterministic, maintainable, and easy to extend. Factories, `@testSetup`, and explicit mocks reduce noise and make failures actionable.

Tag findings as Operational Excellence when:
- test setup is duplicated or inconsistent
- `SeeAllData=true` creates environment-specific fragility
- tests are difficult to diagnose because they do not clearly express intent

## Architectural Tradeoffs

- **Factory reuse vs test-local readability:** shared factories reduce duplication, but each test still needs clear local intent.
- **Broad fixtures vs focused setup:** a large baseline fixture is convenient until it obscures what a test actually depends on.
- **Coverage speed vs behavioral depth:** shallow tests run quickly but miss the failure modes that matter in Salesforce deployments.

## Anti-Patterns

1. **Coverage-only testing** — line execution without behavior verification.
2. **Org-data-dependent tests** — `SeeAllData=true` as a shortcut instead of isolated setup.
3. **Unmocked integration tests** — attempting real callouts or avoiding meaningful callout assertions altogether.

## Official Sources Used

Each bullet names the claim it backs.

- [Apex Developer Guide — Using Test Setup Methods](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_testsetup_using.htm) — backs the claim that every test method, `@TestSetup` included, runs as its own transaction and reinitialises the class's static context, so state cannot be handed between methods through a static (apexdev L41032-L41034).
- [Apex Developer Guide — Using Limits, startTest, and stopTest](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_tools_start_stop_test.htm) — backs the claim that `startTest` *adds* a governor context rather than refreshing it, that each method may call it once, and that async work runs synchronously at `stopTest` (apexdev L41443-L41456).
- [Apex Developer Guide — Testing HTTP Callouts / Performing DML Operations and Mock Callouts](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_wsdl2apex_testing.htm) — backs the claim that test methods do not support real callouts, and that `Test.startTest` must precede `Test.setMock` when the test performed DML first (apexdev L34819-L34821, L35135-L35141).
- [Apex Developer Guide — Using the runAs Method](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_tools_runas.htm) — backs the claim that `runAs` enforces the target user's sharing and FLS regardless of the test class's sharing mode, is confined to test methods, and consumes a DML statement per call (apexdev L41331-L41339).
- [Apex Developer Guide — IsTest(SeeAllData=true) Annotation](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_istest.htm) — backs the claim that `SeeAllData=true` removes `@TestSetup` support from the class, overrides a method-level `SeeAllData=false`, and cannot be combined with `IsParallel=true` (apexdev L5812-L5824, L6272-L6273).
- [Apex Developer Guide — Unit Test Considerations / Isolation of Test Data](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_data_access.htm) — backs the claim that some standard objects are not creatable in a test and that field-history and feed-tracking records cannot be created at all, because test methods never commit (apexdev L40772-L40782).
- [Platform Events Developer Guide — Deliver Test Event Messages](https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_test.htm) — backs the claim that a platform event published in a test is not delivered to its subscriber until `Test.getEventBus().deliver()` runs, once per downstream hop (apexdev L17912-L17940, L29673-L29674).
- [Apex Reference Guide — `System.Assert` class](https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_Assert.htm) — backs the claim that `Assert` message arguments must be `String`, unlike the legacy `System.assert*` overloads.
- [Salesforce Developers blog — Write Clear and Intentional Apex Assertions with the New Assert Class](https://developer.salesforce.com/blogs/2022/11/write-clear-and-intentional-apex-assertions-with-the-new-assert-class) — backs the Winter '23 introduction date and the statement that the legacy assertion methods remain supported.
- [Apex Developer Guide — Stub API](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_stub_api.htm) — backs the list of members the Stub API cannot mock (static, `@future`, private, property, trigger, inner class, system type, `Batchable`, private-constructor-only).
- [Apex Reference Guide — `System.StubProvider` interface](https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_System_StubProvider.htm) — backs the `handleMethodCall` signature shown in `references/examples.md`.
- [Salesforce Well-Architected — Reliable](https://architect.salesforce.com/well-architected/trusted/reliable) — backs the pillar framing used above for regression risk and suite determinism.
