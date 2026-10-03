# Mock deploy result

- org: `sfskills-dev`
- mode: `manifest`
- api version: `62.0` (highest of: M1-S01=62.0, M1-S02=62.0, M2-S01=62.0, M2-S02=62.0, M2-S03=62.0, M2-S04=62.0, M2-S05=62.0)
- files: 18 file(s) copied, 14 skipped (package.xml/notes)
- status: **Failed**
- checkOnly: `True`
- components: 18 total, 17 ok, 2 error(s)

| Type | Component | Result |
|---|---|---|
|  | package.xml | ok |
| BusinessProcess | Opportunity.Enterprise_Sales_Process | ok |
| BusinessProcess | Opportunity.Renewal_Sales_Process | ok |
| CustomField | Opportunity.Approval_Status__c | ok |
| CustomField | Opportunity.Discount__c | ok |
| CustomPermission | Bypass_Opportunity_Sales_Validation | ok |
| Layout | Opportunity-Opportunity Enterprise Layout | ok |
| Layout | Opportunity-Opportunity Renewal Layout | ok |
| PathAssistant | Enterprise_Opportunity_Path | ok |
| PathAssistant | Renewal_Opportunity_Path | ok |
| PathAssistantSettings | PathAssistant | ok |
| PermissionSet | Enterprise_Sales_Record_Types | ok |
| PermissionSet | Sales_Ops_Validation_Bypass | ok |
| Profile | Sales User | FAIL — No default record type specified for recordTypeVisibility: Opportunity.
 To make the '--master--' record type the default, set visible on all record types to false. |
| RecordType | Opportunity.Enterprise | ok |
| RecordType | Opportunity.Renewal | ok |
| StandardValueSet | OpportunityStage | ok |
| ValidationRule | Opportunity.Opportunity_Discount_Requires_Approval | ok |
| ValidationRule | Opportunity.Opportunity_Products_Required_At_Propose | FAIL — Validation rule description cannot be longer than 255 characters long. |

- tests: level NoTestRun · run 0 · passed 0 · failed 0 · coverage n/a
