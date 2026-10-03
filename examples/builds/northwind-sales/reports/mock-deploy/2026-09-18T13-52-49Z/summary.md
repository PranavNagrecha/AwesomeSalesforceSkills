# Mock deploy result

- org: `sfskills-dev`
- mode: `manifest`
- api version: `62.0` (highest of: M1-S01=62.0, M1-S02=62.0)
- files: 9 file(s) copied, 4 skipped (package.xml/notes)
- status: **Failed**
- checkOnly: `True`
- components: 9 total, 8 ok, 2 error(s)

| Type | Component | Result |
|---|---|---|
|  | package.xml | ok |
| BusinessProcess | Opportunity.Enterprise_Sales_Process | ok |
| BusinessProcess | Opportunity.Renewal_Sales_Process | ok |
| CustomField | Opportunity.Approval_Status__c | ok |
| CustomField | Opportunity.Discount__c | ok |
| Layout | Opportunity-Opportunity Enterprise Layout | FAIL — Field:StageName must be Required |
| Layout | Opportunity-Opportunity Renewal Layout | FAIL — Field:StageName must be Required |
| RecordType | Opportunity.Enterprise | ok |
| RecordType | Opportunity.Renewal | ok |
| StandardValueSet | OpportunityStage | ok |

- tests: level NoTestRun · run 0 · passed 0 · failed 0 · coverage n/a
