# Mock deploy result

- org: `sfskills-dev`
- mode: `source`
- api version: `67.0` (highest of: M1-S01=67.0, M1-S02=67.0)
- files: 50 file(s) copied, 6 skipped (package.xml/notes)
- status: **Failed**
- checkOnly: `True`
- components: 39 total, 29 ok, 11 error(s)

| Type | Component | Result |
|---|---|---|
|  | package.xml | ok |
| ApexClass | CaseTriggerHandler | FAIL — Dependent class is invalid and needs recompilation:
 Class Tier2EscalationService : Method was removed after version 58.0: getSalesforceBaseUrl |
| ApexClass | IntegrationFailureResendTest | FAIL — field 'Request_Payload__c' can not be filtered in a query call |
| ApexClass | IntegrationFailureResendTest | FAIL — field 'Request_Payload__c' can not be filtered in a query call |
| ApexClass | IntegrationFailureTriggerHandler | FAIL — Dependent class is invalid and needs recompilation:
 Class Tier2WebhookQueueable : Method was removed after version 58.0: getSalesforceBaseUrl |
| ApexClass | MockHttpResponseGenerator | ok |
| ApexClass | TestDataFactory | ok |
| ApexClass | Tier2ChannelHealthQueueable | ok |
| ApexClass | Tier2ChannelHealthSchedulable | ok |
| ApexClass | Tier2ChannelHealthTest | ok |
| ApexClass | Tier2EscalationService | FAIL — Method was removed after version 58.0: getSalesforceBaseUrl |
| ApexClass | Tier2EscalationServiceTest | FAIL — Dependent class is invalid and needs recompilation:
 Class Tier2WebhookQueueable : Method was removed after version 58.0: getSalesforceBaseUrl |
| ApexClass | Tier2WebhookFinalizer | FAIL — Dependent class is invalid and needs recompilation:
 Class Tier2WebhookQueueable : Method was removed after version 58.0: getSalesforceBaseUrl |
| ApexClass | Tier2WebhookQueueable | FAIL — Method was removed after version 58.0: getSalesforceBaseUrl |
| ApexClass | Tier2WebhookQueueableTest | FAIL — Dependent class is invalid and needs recompilation:
 Class Tier2WebhookQueueable : Method was removed after version 58.0: getSalesforceBaseUrl |
| ApexTrigger | CaseTrigger | FAIL — Variable does not exist: CaseTriggerHandler |
| ApexTrigger | IntegrationFailureTrigger | FAIL — Variable does not exist: IntegrationFailureTriggerHandler |
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
