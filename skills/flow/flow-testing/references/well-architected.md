# Well-Architected Notes - Flow Testing

## Relevant Pillars

### Reliability

Reliable automation has repeatable evidence behind it. Flow tests, boundary tests, and
intentional fault-path coverage reduce release risk and make changes safer.

The platform gives you an evidence surface but not a gate: `DeployResult` returns
`flowCoverage` and `flowCoverageWarnings` (API version 44.0 and later), and
`FlowCoverageResult` names the elements no test reached in `elementsNotCovered`
(`api_meta.txt` L7600–7736). Reading that list per element is the reliability practice;
waiting for a threshold to stop a deploy is not, because for flows no such threshold is
documented.

### Operational Excellence

The fault route is the part of a flow that runs when the org is already having a bad day.
`FLOW_ELEMENT_FAULT` is the debug-log event that proves it ran, and it is emitted in the
Workflow category at WARNING and above (`apexdev.txt` L38789–38793) — so the log
configuration chosen during the incident decides whether the evidence exists.

## Architectural Tradeoffs

- **Fast debug validation vs durable regression assets:** debug is fast, while repeatable
  tests have far more long-term value.
- **Flow-only testing vs layered testing:** one layer is cheaper short term, but complex
  automations often need tests at more than one boundary.
- **Happy-path confidence vs broader path coverage:** wider coverage costs time now but
  avoids operational surprises later.
- **`FlowTest` vs Apex as the driver:** `FlowTest` is declarative, deployable and runs
  before activation, but reaches only three flow types, cannot mock an action call, and
  can assert only at `Start` and `Finish`. Apex reaches autolaunched flows with real
  inputs, `System.runAs` and callout mocks, but costs code and cannot start a
  record-triggered flow at all. The choice is made by flow type first, not by preference.
- **Inline record images vs an Apex data source:** `sobjectValue` JSON keeps a test
  self-contained and readable in review; `flowTestDataSources` with an `ApexClass` source
  (API version 66.0 and later) shares one factory across tests at the cost of a code
  dependency the admin cannot edit.

## Anti-Patterns

1. **Debug session treated as final proof** - no repeatable coverage exists after the
   investigation ends.
2. **No negative or fault-path cases** - the most operationally significant behavior
   remains unproven.
3. **Boundary dependencies assumed correct without their own tests** - orchestration
   coverage leaves custom logic gaps.
4. **A release gate that requires a FlowTest for every flow** - unsatisfiable for screen
   flows, which the type does not cover.
5. **Assertions grouped under one `errorMessage`** - the run reports a failure with no way
   to tell which condition caused it.

## Official Sources Used

- Metadata API Developer Guide — `FlowTest`, `FlowTestPoint`, `FlowTestAssertion`,
  `FlowTestCondition`, `FlowTestParameter`, `FlowTestReferenceOrValue`,
  `FlowTestDataSource` and the two sample definitions, `api_meta.txt` L73960–74470
  (supports the `.flowtest` suffix and `flowtests` folder, API 55.0 availability, the
  three supported flow types, `Start`/`Finish` as the only test points, the operator list
  with its version gates, `isUseMockOuput` being reserved, and every XML block in
  `references/metadata-examples.md` §2–§3).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `Flow` and `FlowStart`, `api_meta.txt` L68222–68425,
  L72400–72560, L70955–71180 (supports `triggerType`, `recordTriggerType`, `runInMode`,
  `FlowVersionStatus`, `faultConnector` and `storeOutputAutomatically` in
  `references/metadata-examples.md` §1 and §4, and Gotcha 10's "no `triggerType` means
  app-launched only").
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `DeployResult`, `FlowCoverageResult` and
  `FlowCoverageWarning`, `api_meta.txt` L7600–7753 (supports the coverage-evidence section
  above and the negative claim that no required flow-coverage percentage is documented).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `FlowDefinition`, `api_meta.txt` L73919–73940 (supports
  Gotcha 13: active version numbers in flow definitions override the status fields in the
  flows).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Apex Reference Guide — `Flow.Interview` class, `createInterview`, `getVariableValue`,
  `start()`, and the `flowtesting` namespace, `apexrefguide.txt` L157925–158190 (supports
  `references/metadata-examples.md` §5, Gotchas 9, 10 and 14, and the `sf flow run test`
  command).
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/
- Apex Developer Guide — Isolation of Test Data from Organization Data in Unit Tests,
  `apexdev.txt` L40724–40775 (supports Gotcha 11: the restriction applies to all code
  running in test context, including a flow the test fires).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Developer Guide — Debug Log Levels and the Workflow-category event table,
  `apexdev.txt` L38342–38900 (supports Gotcha 12: `FLOW_ELEMENT_FAULT` at WARNING and
  above, limit-usage events at FINER, levels cumulative from ERROR upward).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Developer Guide — Apex code coverage requirement, `apexdev.txt` L728, L773, L35283
  (supports Anti-Pattern 8: the 75% figure is stated for Apex code only).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Salesforce Help — Flow Testing Tool. **UNVERIFIED (2026-09-05):** help.salesforce.com
  cannot be fetched in this environment, so no claim in this package rests on it. Listed
  because it is where the Flow Builder click path, the Debug window's "Run as another
  user" option and the debug rollback behaviour are documented.
  https://help.salesforce.com/s/articleView?id=sf.flow_test.htm&type=5
- Salesforce Help — Per-Transaction Flow Limits, referenced from the `Flow.Interview`
  class page as the authority for the SOQL and DML limits that apply during flow execution
  (`apexrefguide.txt` L157938). **UNVERIFIED (2026-09-05):** the numbers themselves are not
  reproduced in any corpus file, so this package quotes none of them.
  https://help.salesforce.com/s/articleView?id=sf.flow_considerations_limit_transaction.htm&type=5
