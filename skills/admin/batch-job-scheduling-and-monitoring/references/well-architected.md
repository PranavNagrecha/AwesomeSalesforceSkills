# Well-Architected Notes — Batch Job Scheduling And Monitoring

## Relevant Pillars

- **Operational Excellence** — Job monitoring is foundational to operational health. Teams that monitor `AsyncApexJob` actively can detect failures before downstream systems are impacted. Proactive failure notification via `finish()` is a core operational excellence practice.
- **Reliability** — Understanding concurrent job limits (5 Batch Apex) and designing scheduling windows to avoid contention prevents jobs from being stuck in Queued status. Reliable systems plan batch scheduling around these constraints.
- **Scalability** — As orgs grow, batch job volume and frequency increase. Hitting the concurrent job limit is a scalability indicator. Designing batch timing, scope sizes, and job priority helps the platform scale gracefully.

## Architectural Tradeoffs

- **Native Apex Jobs UI vs SOQL monitoring:** The Setup UI is convenient for quick checks but not queryable programmatically. SOQL against `AsyncApexJob` enables building dashboards, triggers, and alerts that the UI cannot. For operational maturity, build SOQL-based monitoring.
- **Email notifications vs centralized logging:** Sending email from `finish()` is simple but not scalable for orgs with many batch jobs. A centralized custom object log (e.g., `Job_Execution_Log__c`) queryable via reports and dashboards is preferable at scale.
- **Batch Apex vs Queueable for background processing:** Batch Apex is designed for large-volume record processing and has monitoring built in. Queueable is lighter weight and has less monitoring visibility. Choose Batch Apex for any job that processes hundreds of records or requires failure tracking.

## Anti-Patterns

1. **Not implementing failure notification in finish()** — Salesforce does not send alerts when batch jobs fail. A batch class without failure notification in `finish()` silently fails — admins discover failures only by checking Setup > Apex Jobs manually.
2. **Scheduling all batch jobs at the same time** — When multiple batch classes are all scheduled at midnight, they queue simultaneously and hit the 5-concurrent-job limit. Stagger job schedules (e.g., one job per 15 minutes) to ensure continuous progression.
3. **Assuming NumberOfErrors=0 means all records succeeded** — If the batch class swallows exceptions in `execute()` without re-throwing, chunks complete with no errors even when records fail. Implement explicit error logging using `Database.SaveResult` in execute() for accurate failure tracking.

## Official Sources Used

- Apex Developer Guide — Using Batch Apex — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_batch_interface.htm
- Apex Developer Guide — Apex Scheduler — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_scheduler.htm
- Salesforce Help — Monitor Apex Jobs — https://help.salesforce.com/s/articleView?id=sf.code_apex_job_monitor.htm&type=5
- Apex Developer Guide — Governor Limits — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
