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

Read for the 2026-10-03 revision:

- Apex Developer Guide (Spring '26 PDF), InvocableMethod and InvocableVariable annotations, Testing Queueable Jobs, Testing the Apex Scheduler, Performing DML Operations and Mock Callouts, Using the runAs Method, Execution Governors and Limits, Versioned Behavior Changes (savepoints in tests): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Quickstart Your Einstein Generative AI Solution (Generative AI guide, Spring '26 PDF), Create an Agent (the agent user): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/generative_ai.pdf
- Agentforce Developer Guide, Build Tests in Metadata API (`action_sequence_match`): https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-build-tests.html
- Salesforce CLI Command Reference, `apex run test` (`--class-names`, `--code-coverage`): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/sfdx_cli_reference.pdf
