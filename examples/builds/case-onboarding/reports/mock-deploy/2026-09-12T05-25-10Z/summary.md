# Mock deploy result

- org: `sfskills-dev`
- mode: `source`
- api version: `67.0` (highest of: M1-S01=62.0, M1-S02=62.0, M2-S01=62.0, M2-S02=62.0, M2-S03=62.0, M2-S04=62.0, M2-S05=62.0, M3-S01=62.0, M3-S02=62.0, M3-S03=67.0, M3-S04=67.0)
- files: 41 file(s) copied, 30 skipped (package.xml/notes)
- status: **Failed**
- checkOnly: `True`
- components: 42 total, 42 ok, 1 error(s)

| Type | Component | Result |
|---|---|---|
|  | package.xml | ok |
| AssignmentRule | Case.Case_Intake_Routing | ok |
| AssignmentRules | Case | ok |
| AutoResponseRule | Case.Case_Acknowledgement | FAIL — support-noreply@acme.example is an invalid From email address.: Email Address |
| AutoResponseRules | Case | ok |
| BusinessProcess | Case.Billing_Process | ok |
| BusinessProcess | Case.Support_Process | ok |
| CaseSettings | Case | ok |
| CompactLayout | Case.Case_Intake | ok |
| CustomField | Account.Region__c | ok |
| CustomField | Account.Support_Tier__c | ok |
| CustomField | Case.Severity__c | ok |
| CustomObject | Case | ok |
| CustomPermission | Bypass_Case_Intake_Validation | ok |
| EmailFolder | case_intake | ok |
| EmailTemplate | case_intake/Case_Acknowledgement | ok |
| EmailTemplate | case_intake/Case_Escalated_To_Tier2 | ok |
| Group | Billing_Team | ok |
| Group | Support_Tier_1 | ok |
| Group | Support_Tier_2 | ok |
| Layout | Case-Case Billing Layout | ok |
| Layout | Case-Case Support Layout | ok |
| PermissionSet | Case_Agent_Core | ok |
| PermissionSet | Case_Billing | ok |
| PermissionSet | Case_Intake_Integration | ok |
| PermissionSet | Case_Tier1 | ok |
| PermissionSet | Case_Tier2 | ok |
| PermissionSetGroup | PSG_Billing_Prod | ok |
| PermissionSetGroup | PSG_Tier1_Prod | ok |
| PermissionSetGroup | PSG_Tier2_Prod | ok |
| Profile | Acme Billing | ok |
| Profile | Acme Support Tier 1 | ok |
| Profile | Acme Support Tier 2 | ok |
| Queue | Billing | ok |
| Queue | Tier_1_General | ok |
| Queue | Tier_2_Engineering | ok |
| RecordType | Case.Billing | ok |
| RecordType | Case.Support | ok |
| SharingCriteriaRule | Case.Support_Cases_To_Tier_2 | ok |
| SharingRules | Case | ok |
| StandardValueSet | CaseOrigin | ok |
| ValidationRule | Case.Origin_Must_Be_Known | ok |
| ValidationRule | Case.Priority_Required_On_Agent_Save | ok |
