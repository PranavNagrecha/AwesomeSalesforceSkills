# Mock deploy result

- org: `sfskills-dev`
- mode: `source`
- api version: `62.0` (highest of: M1-S01=62.0, M1-S02=62.0, M2-S01=62.0, M2-S02=62.0, M2-S03=62.0, M2-S04=62.0, M2-S05=62.0, M3-S01=62.0, M3-S02=62.0, M3-S05=62.0)
- files: 43 file(s) copied, 20 skipped (package.xml/notes)
- status: **Failed**
- checkOnly: `True`
- components: 51 total, 38 ok, 14 error(s)

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
| FlexiPage | Opportunity_Enterprise_Record_Page | FAIL — We couldn't retrieve the design time component information for component c:discountApprovalPanel. |
| Layout | Opportunity-Opportunity Enterprise Layout | ok |
| Layout | Opportunity-Opportunity Renewal Layout | ok |
| LightningComponentBundle | discountApprovalPanel | ok |
| LightningComponentBundle | markup://c:discountApprovalPanel | FAIL — [Line: 111, Col: 13] LWC1503: "getRecord" is a wire adapter and can only be used via the @wire decorator. |
| LightningComponentBundle | markup://c:discountApprovalPanel | FAIL — [Line: 119, Col: 13] LWC1503: "getRecord" is a wire adapter and can only be used via the @wire decorator. |
| LightningComponentBundle | markup://c:discountApprovalPanel | FAIL — [Line: 127, Col: 13] LWC1503: "getRecord" is a wire adapter and can only be used via the @wire decorator. |
| LightningComponentBundle | markup://c:discountApprovalPanel | FAIL — [Line: 135, Col: 13] LWC1503: "getRecord" is a wire adapter and can only be used via the @wire decorator. |
| LightningComponentBundle | markup://c:discountApprovalPanel | FAIL — [Line: 143, Col: 13] LWC1503: "getRecord" is a wire adapter and can only be used via the @wire decorator. |
| LightningComponentBundle | markup://c:discountApprovalPanel | FAIL — [Line: 159, Col: 13] LWC1503: "getRecord" is a wire adapter and can only be used via the @wire decorator. |
| LightningComponentBundle | markup://c:discountApprovalPanel | FAIL — [Line: 175, Col: 13] LWC1503: "getRecord" is a wire adapter and can only be used via the @wire decorator. |
| LightningComponentBundle | markup://c:discountApprovalPanel | FAIL — [Line: 191, Col: 13] LWC1503: "getRecord" is a wire adapter and can only be used via the @wire decorator. |
| LightningComponentBundle | markup://c:discountApprovalPanel | FAIL — [Line: 224, Col: 13] LWC1503: "getRecord" is a wire adapter and can only be used via the @wire decorator. |
| LightningComponentBundle | markup://c:discountApprovalPanel | FAIL — [Line: 254, Col: 13] LWC1503: "getRecord" is a wire adapter and can only be used via the @wire decorator. |
| LightningComponentBundle | markup://c:discountApprovalPanel | FAIL — [Line: 274, Col: 13] LWC1503: "getRecord" is a wire adapter and can only be used via the @wire decorator. |
| LightningComponentBundle | markup://c:discountApprovalPanel | FAIL — [Line: 292, Col: 13] LWC1503: "getRecord" is a wire adapter and can only be used via the @wire decorator. |
| LightningComponentBundle | markup://c:discountApprovalPanel | FAIL — [Line: 305, Col: 13] LWC1503: "getRecord" is a wire adapter and can only be used via the @wire decorator. |
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

- tests: level RunSpecifiedTests · run 0 · passed 0 · failed 0 · coverage n/a
