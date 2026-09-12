# Mock deploy result

- org: `sfskills-dev`
- mode: `manifest`
- api version: `67.0` (highest of: M1-S01=67.0, M1-S02=67.0, M1-S05=67.0)
- files: 52 file(s) copied, 8 skipped (package.xml/notes)
- status: **Failed**
- checkOnly: `True`
- components: 39 total, 40 ok, 0 error(s)

| Type | Component | Result |
|---|---|---|
|  | package.xml | ok |
| ApexClass | CaseTriggerHandler | ok |
| ApexClass | IntegrationFailureResendTest | ok |
| ApexClass | IntegrationFailureTriggerHandler | ok |
| ApexClass | MockHttpResponseGenerator | ok |
| ApexClass | TestDataFactory | ok |
| ApexClass | TestUserFactory | ok |
| ApexClass | Tier2ChannelHealthQueueable | ok |
| ApexClass | Tier2ChannelHealthSchedulable | ok |
| ApexClass | Tier2ChannelHealthTest | ok |
| ApexClass | Tier2EscalationService | ok |
| ApexClass | Tier2EscalationServiceTest | ok |
| ApexClass | Tier2WebhookFinalizer | ok |
| ApexClass | Tier2WebhookQueueable | ok |
| ApexClass | Tier2WebhookQueueableTest | ok |
| ApexTrigger | CaseTrigger | ok |
| ApexTrigger | IntegrationFailureTrigger | ok |
| CustomField | Case.Tier2_Notified_At__c | ok |
| CustomField | Integration_Failure__c.Attempt_Count__c | ok |
| CustomField | Integration_Failure__c.Case_Number__c | ok |
| CustomField | Integration_Failure__c.Case__c | ok |
| CustomField | Integration_Failure__c.Endpoint__c | ok |
| CustomField | Integration_Failure__c.Error_Message__c | ok |
| CustomField | Integration_Failure__c.HTTP_Status__c | ok |
| CustomField | Integration_Failure__c.Last_Attempted_At__c | ok |
| CustomField | Integration_Failure__c.Request_Payload__c | ok |
| CustomField | Integration_Failure__c.Resend__c | ok |
| CustomField | Integration_Failure__c.Response_Body__c | ok |
| CustomField | Integration_Failure__c.Severity__c | ok |
| CustomField | Integration_Failure__c.Status__c | ok |
| CustomField | Tier2_Escalation__e.Case_Link__c | ok |
| CustomField | Tier2_Escalation__e.Case_Number__c | ok |
| CustomField | Tier2_Escalation__e.Escalated_At__c | ok |
| CustomField | Tier2_Escalation__e.Severity__c | ok |
| CustomField | Tier2_Escalation__e.Subject__c | ok |
| CustomObject | Integration_Failure__c | ok |
| CustomObject | Tier2_Escalation__e | ok |
| ExternalCredential | OnCall_Tool_EC | ok |
| NamedCredential | OnCall_Tool | ok |
| PermissionSet | Tier2_Webhook_Admin | ok |

- tests: level RunSpecifiedTests · run 29 · passed 28 · failed 1 · coverage 74.0%

## Test failures

| Class | Method | Message | Stack (first line) |
|---|---|---|---|
| Tier2EscalationServiceTest | ownerChangeToTier2QueueEscalatesAndStamps | System.AssertException: Assertion Failed: A successful escalation writes no failure row: Expected: 0, Actual: 2 | Class.Tier2EscalationServiceTest.ownerChangeToTier2QueueEscalatesAndStamps: line 122, column 1 |
