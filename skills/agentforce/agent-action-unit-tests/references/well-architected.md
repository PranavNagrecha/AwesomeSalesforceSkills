# Well-Architected Notes — Agent Action Unit Tests

**Reliability:** the documented Invocable contract is that inputs and outputs match on
size and order. Asserting both, at a request count above one, is the only way that
contract is verified before an agent batches real traffic through the action.

**Operational Excellence:** the test class is the executable specification of the
action's error taxonomy. Every literal the class can assign to `reasonCode` gets exactly
one test, so a new branch cannot ship without a named, asserted failure mode.

## Official Sources Used

- InvocableMethod annotation — one per class, and "the Inputs and Outputs must match on both the size and the order" — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm
- InvocableVariable annotation — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableVariable.htm
- Apex Developer Guide — Testing Apex (Test.startTest/stopTest, async completion) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing.htm
- Testing HTTP Callouts with HttpCalloutMock — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_testing.htm
- Apex Governor Limits — 100 SOQL queries synchronous, 150 DML statements per transaction — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
