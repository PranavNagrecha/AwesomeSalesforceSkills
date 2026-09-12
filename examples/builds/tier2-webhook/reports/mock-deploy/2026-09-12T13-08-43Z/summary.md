# Mock deploy result

- org: `sfskills-dev`
- mode: `manifest`
- api version: `67.0` (highest of: M1-S01=67.0, M1-S02=67.0, M1-S05=67.0)
- files: 50 file(s) copied, 8 skipped (package.xml/notes)
- status: **Failed**
- checkOnly: `True`
- components: 38 total, 39 ok, 0 error(s)

| Type | Component | Result |
|---|---|---|
|  | package.xml | ok |
| ApexClass | CaseTriggerHandler | ok |
| ApexClass | IntegrationFailureResendTest | ok |
| ApexClass | IntegrationFailureTriggerHandler | ok |
| ApexClass | MockHttpResponseGenerator | ok |
| ApexClass | TestDataFactory | ok |
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

- tests: level RunSpecifiedTests · run 2 · passed 0 · failed 28 · coverage 34.9%

## Test failures

| Class | Method | Message | Stack (first line) |
|---|---|---|---|
| IntegrationFailureResendTest | aResendIsNotSuppressedByARecentNotification | System.DmlException: Operation failed due to fields being inaccessible on Sobject Integration_Failure__c, check errors on Exception or Result! | Class.IntegrationFailureResendTest.seed: line 35, column 1 |
| IntegrationFailureResendTest | aRowWithNoCaseIsIgnored | System.DmlException: Operation failed due to fields being inaccessible on Sobject Integration_Failure__c, check errors on Exception or Result! | Class.IntegrationFailureResendTest.seed: line 35, column 1 |
| IntegrationFailureResendTest | aRowWithNoStoredPayloadStillResends | System.DmlException: Operation failed due to fields being inaccessible on Sobject Integration_Failure__c, check errors on Exception or Result! | Class.IntegrationFailureResendTest.seed: line 35, column 1 |
| IntegrationFailureResendTest | clearingResendDoesNotReEnqueue | System.DmlException: Operation failed due to fields being inaccessible on Sobject Integration_Failure__c, check errors on Exception or Result! | Class.IntegrationFailureResendTest.seed: line 35, column 1 |
| IntegrationFailureResendTest | theResendReplaysTheStoredIdempotencyKey | System.DmlException: Operation failed due to fields being inaccessible on Sobject Integration_Failure__c, check errors on Exception or Result! | Class.IntegrationFailureResendTest.seed: line 35, column 1 |
| IntegrationFailureResendTest | tickingResendReEnqueuesAndResolvesTheRow | System.DmlException: Operation failed due to fields being inaccessible on Sobject Integration_Failure__c, check errors on Exception or Result! | Class.IntegrationFailureResendTest.seed: line 35, column 1 |
| Tier2ChannelHealthTest | aQuietWindowWithNoEscalationsRaisesNoAlert | System.DmlException: Operation failed due to fields being inaccessible on Sobject Case, check errors on Exception or Result! | Class.Tier2ChannelHealthTest.seed: line 49, column 1 |
| Tier2ChannelHealthTest | alertPathDependsOnTheOrgWideAddressPrerequisite | System.DmlException: Operation failed due to fields being inaccessible on Sobject Case, check errors on Exception or Result! | Class.Tier2ChannelHealthTest.seed: line 49, column 1 |
| Tier2ChannelHealthTest | belowBothThresholdsRaisesNoAlert | System.DmlException: Operation failed due to fields being inaccessible on Sobject Case, check errors on Exception or Result! | Class.Tier2ChannelHealthTest.seed: line 49, column 1 |
| Tier2ChannelHealthTest | moreThanThreeFailuresInAnHourRaisesTheBurstAlert | System.DmlException: Operation failed due to fields being inaccessible on Sobject Case, check errors on Exception or Result! | Class.Tier2ChannelHealthTest.seed: line 49, column 1 |
| Tier2ChannelHealthTest | noActiveRecipientRecordsAWarningFailureRowAndSendsNothing | System.DmlException: Operation failed due to fields being inaccessible on Sobject Case, check errors on Exception or Result! | Class.Tier2ChannelHealthTest.seed: line 49, column 1 |
| Tier2ChannelHealthTest | noSuccessInTwentyFourHoursWhileEscalationsOccurredRaisesTheSilentAlert | System.DmlException: Operation failed due to fields being inaccessible on Sobject Case, check errors on Exception or Result! | Class.Tier2ChannelHealthTest.seed: line 49, column 1 |
| Tier2ChannelHealthTest | productionCronIsHourlyOnTheHour | System.DmlException: Operation failed due to fields being inaccessible on Sobject Case, check errors on Exception or Result! | Class.Tier2ChannelHealthTest.seed: line 49, column 1 |
| Tier2ChannelHealthTest | queryBudgetStaysFlatAtBulkVolume | System.DmlException: Operation failed due to fields being inaccessible on Sobject Case, check errors on Exception or Result! | Class.Tier2ChannelHealthTest.seed: line 49, column 1 |
| Tier2ChannelHealthTest | rosterResolutionReturnsTheDistinctActiveAssigneeEmails | System.DmlException: Operation failed due to fields being inaccessible on Sobject Case, check errors on Exception or Result! | Class.Tier2ChannelHealthTest.seed: line 49, column 1 |
| Tier2ChannelHealthTest | scheduleCreatesAWaitingCronTriggerAndDispatchesTheQueueable | System.DmlException: Operation failed due to fields being inaccessible on Sobject Case, check errors on Exception or Result! | Class.Tier2ChannelHealthTest.seed: line 49, column 1 |
| Tier2ChannelHealthTest | subjectAndBodyNameTheRuleThatFired | System.DmlException: Operation failed due to fields being inaccessible on Sobject Case, check errors on Exception or Result! | Class.Tier2ChannelHealthTest.seed: line 49, column 1 |
| Tier2EscalationServiceTest | aNotificationOlderThanTheWindowIsNotSuppressed | System.QueryException: No such column 'Tier2_Notified_At__c' on entity 'Case'. If you are attempting to use a custom field, be sure to append the '__c' after the custom field name. Please reference your WSDL or the describe call for the appropriate names. | Class.Tier2EscalationServiceTest.cases: line 47, column 1 |
| Tier2EscalationServiceTest | aRecentlyNotifiedCaseIsSuppressed | System.QueryException: No such column 'Tier2_Notified_At__c' on entity 'Case'. If you are attempting to use a custom field, be sure to append the '__c' after the custom field name. Please reference your WSDL or the describe call for the appropriate names. | Class.Tier2EscalationServiceTest.cases: line 47, column 1 |
| Tier2EscalationServiceTest | aSaveThatDoesNotChangeOwnerIsIgnored | System.QueryException: No such column 'Tier2_Notified_At__c' on entity 'Case'. If you are attempting to use a custom field, be sure to append the '__c' after the custom field name. Please reference your WSDL or the describe call for the appropriate names. | Class.Tier2EscalationServiceTest.cases: line 47, column 1 |
| Tier2EscalationServiceTest | bulkOwnerChangeStillEnqueuesExactlyOneJob | System.QueryException: No such column 'Tier2_Notified_At__c' on entity 'Case'. If you are attempting to use a custom field, be sure to append the '__c' after the custom field name. Please reference your WSDL or the describe call for the appropriate names. | Class.Tier2EscalationServiceTest.cases: line 47, column 1 |
| Tier2EscalationServiceTest | ownerChangeToAUserIsNotAnEscalation | System.QueryException: No such column 'Tier2_Notified_At__c' on entity 'Case'. If you are attempting to use a custom field, be sure to append the '__c' after the custom field name. Please reference your WSDL or the describe call for the appropriate names. | Class.Tier2EscalationServiceTest.cases: line 47, column 1 |
| Tier2EscalationServiceTest | ownerChangeToTier2QueueEscalatesAndStamps | System.QueryException: No such column 'Tier2_Notified_At__c' on entity 'Case'. If you are attempting to use a custom field, be sure to append the '__c' after the custom field name. Please reference your WSDL or the describe call for the appropriate names. | Class.Tier2EscalationServiceTest.cases: line 47, column 1 |
| Tier2WebhookQueueableTest | aCaseNotifiedInsideTheWindowIsSkippedByTheJobToo | System.DmlException: Operation failed due to fields being inaccessible on Sobject Case, check errors on Exception or Result! | Class.Tier2WebhookQueueableTest.aCaseNotifiedInsideTheWindowIsSkippedByTheJobToo: line 177, column 1 |
| Tier2WebhookQueueableTest | authFailurePointsTheReaderAtThePrincipalGrant | System.DmlException: Operation failed due to fields being inaccessible on Sobject Integration_Failure__c, check errors on Exception or Result! | Class.Tier2WebhookFinalizer.recordAttempt: line 178, column 1 |
| Tier2WebhookQueueableTest | permanentFailureRecordsTheAttemptAndDoesNotStamp | System.DmlException: Operation failed due to fields being inaccessible on Sobject Integration_Failure__c, check errors on Exception or Result! | Class.Tier2WebhookFinalizer.recordAttempt: line 178, column 1 |
| Tier2WebhookQueueableTest | successStampsTheCaseAndWritesNoFailureRow | System.DmlException: Operation failed due to fields being inaccessible on Sobject Integration_Failure__c, check errors on Exception or Result! | Class.Tier2WebhookFinalizer.recordAttempt: line 178, column 1 |
| Tier2WebhookQueueableTest | transientFailureOnTheLastAttemptIsAbandonedRatherThanRetried | System.DmlException: Operation failed due to fields being inaccessible on Sobject Integration_Failure__c, check errors on Exception or Result! | Class.Tier2WebhookFinalizer.recordAttempt: line 178, column 1 |

## Manifest drift

None — the steps' merge matches `reports/MILESTONE-M1-package.xml`.
