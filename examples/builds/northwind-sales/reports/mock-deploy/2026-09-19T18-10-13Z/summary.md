# Mock deploy result

- org: `sfskills-dev`
- mode: `source`
- api version: `62.0` (highest of: M1-S01=62.0, M1-S02=62.0, M2-S01=62.0, M2-S02=62.0, M2-S03=62.0, M2-S04=62.0, M2-S05=62.0, M3-S01=62.0, M3-S02=62.0, M3-S05=62.0)
- files: 43 file(s) copied, 20 skipped (package.xml/notes)
- status: **Failed**
- checkOnly: `True`
- components: 38 total, 39 ok, 0 error(s)

| Type | Component | Result |
|---|---|---|
|  | package.xml | ok |
| ApexClass | OpportunityApprovalController | ok |
| ApexClass | OpportunityApprovalService | ok |
| ApexClass | OpportunityApprovalServiceTest | ok |
| ApexClass | OpportunityApprovalSubmitAction | ok |
| ApexClass | TestDataFactory | ok |
| ApprovalProcess | Opportunity.Discount_Approval | ok |
| BusinessProcess | Opportunity.Enterprise_Sales_Process | ok |
| BusinessProcess | Opportunity.Renewal_Sales_Process | ok |
| CustomField | Opportunity.Approval_Status__c | ok |
| CustomField | Opportunity.Discount__c | ok |
| CustomObject | Opportunity | ok |
| CustomPermission | Bypass_Opportunity_Sales_Validation | ok |
| EmailFolder | Sales_Approvals | ok |
| EmailTemplate | Sales_Approvals/Discount_Approval_Request | ok |
| EmailTemplate | Sales_Approvals/Discount_Approved | ok |
| EmailTemplate | Sales_Approvals/Discount_Rejected | ok |
| FlexiPage | Opportunity_Enterprise_Record_Page | ok |
| Layout | Opportunity-Opportunity Enterprise Layout | ok |
| Layout | Opportunity-Opportunity Renewal Layout | ok |
| LightningComponentBundle | discountApprovalPanel | ok |
| PathAssistant | Enterprise_Opportunity_Path | ok |
| PathAssistant | Renewal_Opportunity_Path | ok |
| PathAssistantSettings | PathAssistant | ok |
| PermissionSet | Enterprise_Sales_Record_Types | ok |
| PermissionSet | Sales_Ops_Validation_Bypass | ok |
| Profile | Sales User | ok |
| RecordType | Opportunity.Enterprise | ok |
| RecordType | Opportunity.Renewal | ok |
| StandardValueSet | OpportunityStage | ok |
| ValidationRule | Opportunity.Opportunity_Discount_Requires_Approval | ok |
| ValidationRule | Opportunity.Opportunity_Products_Required_At_Propose | ok |
| Workflow | Opportunity | ok |
| WorkflowAlert | Opportunity.Notify_Owner_Discount_Approved | ok |
| WorkflowAlert | Opportunity.Notify_Owner_Discount_Rejected | ok |
| WorkflowFieldUpdate | Opportunity.Clear_Approval_Status | ok |
| WorkflowFieldUpdate | Opportunity.Set_Approval_Status_Approved | ok |
| WorkflowFieldUpdate | Opportunity.Set_Approval_Status_Pending | ok |
| WorkflowFieldUpdate | Opportunity.Set_Approval_Status_Rejected | ok |

- tests: level RunSpecifiedTests · run 0 · passed 0 · failed 6 · coverage 32.4%

## Test failures

| Class | Method | Message | Stack (first line) |
|---|---|---|---|
| OpportunityApprovalServiceTest | belowThresholdOpportunityIsRefusedByEntryCriteria | System.QueryException: sObject type 'Opportunity' is not supported. If you are attempting to use a custom object, be sure to append the '__c' after the entity name. Please reference your WSDL or the describe call for the appropriate names. | Class.OpportunityApprovalService.submitBatch: line 79, column 1 |
| OpportunityApprovalServiceTest | controllerReturnsTheServiceOutcomeToTheComponent | System.QueryException: sObject type 'Opportunity' is not supported. If you are attempting to use a custom object, be sure to append the '__c' after the entity name. Please reference your WSDL or the describe call for the appropriate names. | Class.OpportunityApprovalService.submitBatch: line 79, column 1 |
| OpportunityApprovalServiceTest | invocableReturnsOneResultPerRequestInInputOrder | System.QueryException: sObject type 'Opportunity' is not supported. If you are attempting to use a custom object, be sure to append the '__c' after the entity name. Please reference your WSDL or the describe call for the appropriate names. | Class.OpportunityApprovalService.submitBatch: line 79, column 1 |
| OpportunityApprovalServiceTest | secondSubmitWhilePendingIsRefusedWithAReason | System.QueryException: sObject type 'Opportunity' is not supported. If you are attempting to use a custom object, be sure to append the '__c' after the entity name. Please reference your WSDL or the describe call for the appropriate names. | Class.OpportunityApprovalService.submitBatch: line 79, column 1 |
| OpportunityApprovalServiceTest | submitsQualifyingOpportunityAsItsOwner | System.QueryException: sObject type 'Opportunity' is not supported. If you are attempting to use a custom object, be sure to append the '__c' after the entity name. Please reference your WSDL or the describe call for the appropriate names. | Class.OpportunityApprovalService.submitBatch: line 79, column 1 |
| OpportunityApprovalServiceTest | unreadableOpportunityIsReportedWithoutASubmission | System.QueryException: sObject type 'Opportunity' is not supported. If you are attempting to use a custom object, be sure to append the '__c' after the entity name. Please reference your WSDL or the describe call for the appropriate names. | Class.OpportunityApprovalService.submitBatch: line 79, column 1 |

## Coverage warnings

- OpportunityApprovalSubmitAction — Test coverage of selected Apex Class is 35.714%, at least 75% test coverage is required
- OpportunityApprovalService — Test coverage of selected Apex Class is 28.846%, at least 75% test coverage is required

## Coverage by class

| Class | Type | Lines | Uncovered | Coverage | |
|---|---|---|---|---|---|
| OpportunityApprovalService | Class | 52 | 37 | 28.8% | UNDER 75% |
| OpportunityApprovalSubmitAction | Class | 14 | 9 | 35.7% | UNDER 75% |
| OpportunityApprovalController | Class | 2 | 0 | 100.0% |  |
- classes under 75%: 2 (RunSpecifiedTests and RunLocalTests require every class at 75% — see Coverage warnings)
