# Mock deploy result

- org: `sfskills-dev`
- mode: `source`
- api version: `62.0` (highest of: M1-S01=62.0, M1-S02=62.0, M2-S01=62.0, M2-S02=62.0, M2-S03=62.0, M2-S04=62.0, M2-S05=62.0, M3-S01=62.0, M3-S02=62.0, M3-S05=62.0)
- files: 43 file(s) copied, 20 skipped (package.xml/notes)
- status: **Succeeded**
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

- tests: level RunSpecifiedTests · run 6 · passed 6 · failed 0 · coverage 95.6%

## Coverage by class

| Class | Type | Lines | Uncovered | Coverage | |
|---|---|---|---|---|---|
| OpportunityApprovalService | Class | 52 | 3 | 94.2% |  |
| OpportunityApprovalController | Class | 2 | 0 | 100.0% |  |
| OpportunityApprovalSubmitAction | Class | 14 | 0 | 100.0% |  |
- classes under 75%: 0
