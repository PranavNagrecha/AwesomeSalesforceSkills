# Mock deploy result

- org: `sfskills-dev`
- mode: `source`
- api version: `67.0` (highest of: M1-S01=67.0, M1-S02=67.0)
- files: 18 file(s) copied, 4 skipped (package.xml/notes)
- status: **Failed**
- checkOnly: `True`
- components: 23 total, 22 ok, 2 error(s)

| Type | Component | Result |
|---|---|---|
|  | package.xml | ok |
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
| ExternalCredential | OnCall_Tool_EC | FAIL — The parameter type "AuthHeader" requires these fields: ParameterValue. |
| NamedCredential | OnCall_Tool | ok |
| PermissionSet | Tier2_Webhook_Admin | FAIL — The OnCallToolNamedPrincipal parameter value doesn't exist or you may not have permission to access it. |
