# Well-Architected Notes — Revenue Recognition Requirements

## Relevant Pillars

- **Reliability** — Revenue recognition configuration must produce consistent, auditable GL records across every Order activation, Finance Period close, and contract amendment. Unreliable schedule generation (e.g., Finance Period gaps) creates silent failures that surface only during period-end reconciliation, often after material misstatement has already occurred.
- **Operational Excellence** — Finance Period maintenance, amendment reconciliation, and SSP validation must be operationalized as repeatable processes — not one-time admin tasks. Orgs that treat revenue recognition setup as a one-time configuration invariably accumulate period gaps, stale rules, and unreconciled amendment schedules.
- **Security** — `blng__RevenueTransaction__c` and `blng__RevenueSchedule__c` records are GL-sensitive data. Access must be restricted to Finance and system integration users. Field-level security should prevent ad hoc edits to recognition amounts, GL account codes, and period references by non-Finance users.
- **Performance** — Revenue schedule generation and Finance Period close processing execute as batch jobs. For orgs with large Order volumes, Finance Period close batch jobs can exhaust governor limits if Finance Periods are created with overlapping date ranges or if too many schedules are open simultaneously. Design Finance Period boundaries to be non-overlapping and close periods sequentially.
- **Scalability** — For orgs with thousands of active subscriptions, `blng__RevenueTransaction__c` record volume grows proportionally with the number of Finance Periods closed. Plan for SOQL and report query performance against this object early — add indexes on `blng__FinancePeriod__c` and `blng__RevenueSchedule__c` lookup fields if query times degrade.

## Architectural Tradeoffs

**Immediate vs. Rateable treatment** — Immediate recognition is simpler to configure and generates no long-running schedule, but it is only correct for products where the full performance obligation is satisfied at point of sale. Using Immediate for subscription products to simplify configuration is an ASC 606 compliance violation that creates audit risk. Choose Rateable for any performance obligation satisfied over time, even if Finance initially requests simplicity.

**Daily Proration vs. Equal Distribution** — Daily Proration produces ASC 606-correct amounts for partial months but generates more complex period-boundary calculations that are harder to validate manually. Equal Distribution is simpler to verify but will misstate revenue in any month where the subscription starts or ends mid-period. For customer-facing SaaS subscriptions with variable start dates, Daily Proration is the correct default.

**Single consolidated ERP integration vs. per-period event streaming** — Some organizations integrate `blng__RevenueTransaction__c` records into the ERP as they are created (event-driven). Others batch-export at month-end. Event-driven integration provides real-time GL accuracy but requires robust error handling for failed transactions. Batch export is simpler but means the ERP is always one period behind until the export runs. Choose based on Finance's close timeline requirements.

## Anti-Patterns

1. **Configuring Revenue Recognition Rules after Order activation** — Setting `blng__RevenueRecognitionRule__c` on Product2 after Orders are already activated does not retroactively generate revenue schedules for those Orders. The rule is only evaluated at Order activation time. Orgs that configure rules after go-live must handle the backlog of activated Orders without schedules through a Finance-approved manual process, not an automated re-run.

2. **Treating Finance Period creation as a one-time setup task** — Finance Periods must be created ahead of each fiscal year. Orgs that create only the current year's periods during implementation hit a silent wall when January of the next year arrives: new Orders activate without revenue schedules because no Finance Periods exist for the new year. Establish a Finance Period creation process (ideally automated via a scheduled batch) that runs 30–60 days before the new fiscal year begins.

3. **Using Data Loader to bulk-edit blng__RevenueSchedule__c or blng__RevenueTransaction__c records** — These objects are system-managed. Bulk edits bypass the Billing engine's internal consistency checks, corrupt recognized-amount tracking, and produce GL imbalances that are extremely difficult to unwind. Configuration corrections must always flow through the proper Salesforce Billing processes (close schedule, correct rule, re-activate).

## Official Sources Used

- Understanding the Revenue Recognition Process — https://help.salesforce.com/s/articleView?id=sf.blng_revenue_recognition_overview.htm
- Revenue Recognition Treatments — https://help.salesforce.com/s/articleView?id=sf.blng_revenue_recognition_treatments.htm
- Revenue Distribution Methods — https://help.salesforce.com/s/articleView?id=sf.blng_revenue_distribution_methods.htm
- blng__RevenueRecognitionRule__c — Salesforce Billing Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.billing_dev_guide.meta/billing_dev_guide/billing_dev_guide_revenue_recognition_rule.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
