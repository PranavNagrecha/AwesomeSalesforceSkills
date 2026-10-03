# Mock deploy result

- org: `sfskills-dev`
- mode: `manifest`
- api version: `62.0` (highest of: M1-S01=62.0, M1-S02=62.0)
- files: 9 file(s) copied, 4 skipped (package.xml/notes)
- status: **Failed**
- checkOnly: `True`
- components: 9 total, 6 ok, 4 error(s)

| Type | Component | Result |
|---|---|---|
|  | package.xml | ok |
| BusinessProcess | Opportunity.Enterprise_Sales_Process | FAIL — Cannot specify a default on: Opportunity |
| BusinessProcess | Opportunity.Renewal_Sales_Process | FAIL — Cannot specify a default on: Opportunity |
| CustomField | Opportunity.Approval_Status__c | ok |
| CustomField | Opportunity.Discount__c | ok |
| Layout | Opportunity-Opportunity Enterprise Layout | FAIL — Layout must contain an item for required layout field: Probability |
| Layout | Opportunity-Opportunity Renewal Layout | FAIL — Layout must contain an item for required layout field: Probability |
| RecordType | Opportunity.Enterprise | ok |
| RecordType | Opportunity.Renewal | ok |
| StandardValueSet | OpportunityStage | ok |

- tests: level NoTestRun · run 0 · passed 0 · failed 0 · coverage n/a
