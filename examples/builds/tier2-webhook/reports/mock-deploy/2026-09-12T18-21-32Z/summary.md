# Mock deploy result

- org: `sfskills-dev`
- mode: `manifest`
- api version: `67.0` (highest of: M1-S01=67.0, M1-S02=67.0, M1-S05=67.0)
- files: 54 file(s) copied, 8 skipped (package.xml/notes)
- status: **Succeeded**
- checkOnly: `True`
- components: 40 total, 41 ok, 0 error(s)

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
| ApexClass | Tier2WebhookFinalizerTest | ok |
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

- tests: level RunSpecifiedTests · run 37 · passed 37 · failed 0 · coverage 89.9%
