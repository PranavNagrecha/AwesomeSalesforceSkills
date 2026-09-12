# Mock deploy — tier2-webhook M1 in progress (validation only, nothing deployed)

## Run 1 — 2026-09-12, source mode, M1-S01 + M1-S02 (API 67.0)

`python3 scripts/mock_deploy.py plan.json --org-alias sfskills-dev --step M1-S01 --step M1-S02`

**Failed — 23 components, 22 ok, 2 errors.** M1-S01's object, twelve fields, the Case field and the platform event all
validated on first contact; the Named Credential validated. The failures:

| Component | Error |
|---|---|
| `ExternalCredential OnCall_Tool_EC` | `The parameter type "AuthHeader" requires these fields: ParameterValue.` |
| `PermissionSet Tier2_Webhook_Admin` | `The OnCallToolNamedPrincipal parameter value doesn't exist or you may not have permission to access it.` |

**S2-F-02 (HIGH, build + skill + clarifier).** An `AuthHeader` external-credential parameter must carry `parameterValue`
(the header's formula, e.g. `{!$Credential.<EC>.<ParamName>}`). The builder omitted it deliberately because no answer
named the parameter the API key is stored under — the clarifier never asked it, and never asked the endpoint URL
either (driver's log 26). The cited skill's example carries a dangling `$Credential.Partner_Orders_EC.ApiToken` with
no declared parameter (27). Remedy: the requester supplies both facts (recorded on the step by amendment); the skill
gains two Questions-to-Ask rows, a corrected example and a checker rule (AuthHeader without `parameterValue` → ERROR
with the org's text); rebuild M1-S02.

**S2-F-03 (cascade).** The permission set's `externalCredentialPrincipalAccesses` grant names the principal of the
credential that failed in the same deploy; expected to clear once the External Credential validates (re-check in run 2).

## Run 2 — 2026-09-12, source mode, M1-S01 + M1-S02 after the S2-F-02 rebuild (API 67.0)

**Succeeded — 23 total, 24 ok, 0 error(s).**
S2-F-02 closed (the AuthHeader formula parses on deploy); S2-F-03 was a cascade and cleared with it. Runtime header behaviour is confirmed at UAT.

## Run 3 — 2026-09-12, source mode, M1-S01 … M1-S04 (the Apex steps compiled by the org; API 67.0)

**Failed — 39 total, 29 ok, 11 error(s).**

| Component | Error |
|---|---|
| ApexClass | CaseTriggerHandler | FAIL — Dependent class is invalid and needs recompilation:
| ApexClass | IntegrationFailureResendTest | FAIL — field 'Request_Payload__c' can not be filtered in a query call |
| ApexClass | IntegrationFailureResendTest | FAIL — field 'Request_Payload__c' can not be filtered in a query call |
| ApexClass | IntegrationFailureTriggerHandler | FAIL — Dependent class is invalid and needs recompilation:
| ApexClass | Tier2EscalationService | FAIL — Method was removed after version 58.0: getSalesforceBaseUrl |
| ApexClass | Tier2EscalationServiceTest | FAIL — Dependent class is invalid and needs recompilation:
| ApexClass | Tier2WebhookFinalizer | FAIL — Dependent class is invalid and needs recompilation:
| ApexClass | Tier2WebhookQueueable | FAIL — Method was removed after version 58.0: getSalesforceBaseUrl |
| ApexClass | Tier2WebhookQueueableTest | FAIL — Dependent class is invalid and needs recompilation:
| ApexTrigger | CaseTrigger | FAIL — Variable does not exist: CaseTriggerHandler |
| ApexTrigger | IntegrationFailureTrigger | FAIL — Variable does not exist: IntegrationFailureTriggerHandler |


Triage: eleven errors, two roots, the rest cascade (`Dependent class is invalid`, `Variable does not exist: <handler>`).
M1-S04's four classes compiled clean.

**S2-F-04 (HIGH, build + skill).** `URL.getSalesforceBaseUrl()` — `Method was removed after version 58.0` — used by
`Tier2EscalationService` and `Tier2WebhookQueueable` for the link back to the Case. At API 67.0 the replacement is
`URL.getOrgDomainUrl()`. The skill example that carries the old method is the source to fix.

**S2-F-05 (MEDIUM, build + skill).** `IntegrationFailureResendTest` filters a SOQL query on `Request_Payload__c`
(Long Text Area) — `field 'Request_Payload__c' can not be filtered in a query call`. Long/rich text areas cannot be
filtered, grouped or sorted; the test must select and assert instead. `apex/test-class-standards` and
`admin/object-creation-and-design` gain the rule.

## Run 4 — 2026-09-12, source mode, M1-S01 … M1-S04 after the S2-F-04/S2-F-05 rebuild (API 67.0)

**Succeeded — 38 total, 39 ok, 0 error(s).**
Every Apex class and trigger of M1-S03 and M1-S04 compiled; S2-F-04 and S2-F-05 closed by the org.

## Run 5 — 2026-09-12, MANIFEST mode, milestone M1 (M1-S01 … M1-S05; the merged package.xml is what deploys; API 67.0)

**Succeeded — 38 total, 39 ok, 0 error(s).**
The build-level manifest (33 members incl. 13 ApexClass + 2 ApexTrigger) validates as a unit: this is the shape a real deployment would use.
