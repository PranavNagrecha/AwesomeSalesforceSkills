# Well-Architected Notes — NPSP Custom Rollups (CRLP)

## Relevant Pillars

- **Reliability** — CRLP rollup values are batch-driven and asynchronous. Reliable orgs schedule recalculation jobs with sufficient frequency, monitor batch completion, and verify values after bulk data operations. An org with stale rollup fields silently produces incorrect donor totals that affect gift officer decisions and reports.
- **Operational Excellence** — CRLP configuration is custom metadata and should be managed through version control and Metadata API deployments rather than manual UI recreation in each environment. Change history, peer review, and rollback capability all depend on treating CRLP definitions as code.
- **Performance** — Full recalculation batches process every summary record in the org and can run for hours in large orgs. Choosing the correct batch mode (Incremental for routine operation, Full only when necessary) prevents unnecessary load and reduces the risk of job timeouts or org performance degradation.
- **Security** — CRLP rollup fields on Contact and Account are visible according to standard Salesforce field-level security (FLS) rules. Rollup Definitions that expose sensitive financial aggregations (e.g., major donor totals) should be reviewed against the org's FLS configuration to ensure only authorized profiles can view them.
- **Scalability** — CRLP handles large record volumes better than legacy NPSP rollups, but the batch architecture means recalculation time grows with org size. Orgs with hundreds of thousands of Contacts should baseline recalculation run times and build that into operational planning.

---

## Architectural Tradeoffs

**Asynchronous vs. real-time rollup accuracy:** CRLP produces accurate values asynchronously via batch. Orgs that need real-time rollup display (e.g., a gift officer dashboard showing live giving totals as gifts are entered) cannot rely on CRLP alone. Options include supplementing with SOQL aggregates in Apex or LWC components that query live data, accepting eventual consistency for summary fields, or triggering single-record recalculation using the "Recalculate Rollups" button on high-priority records.

**Metadata API deployment vs. NPSP Settings UI:** The NPSP Settings UI is convenient for initial exploration but is not a reliable production change management path. Any change that will be promoted to production should go through version control and Metadata API deployment. This trades the speed of UI configuration for the reliability of a traceable, reviewable, rollback-capable process.

**Filter group granularity vs. maintenance overhead:** Fine-grained filter groups (e.g., a separate filter group per giving program) give precise rollup control but multiply the number of definitions to maintain. Coarse filter groups (e.g., "All Closed Won Donations") simplify maintenance but may not meet reporting requirements. Design filter groups around the business questions that need answering, not technical convenience.

---

## Anti-Patterns

1. **Enabling CRLP without a pre-migration dependency audit** — Enabling CRLP before auditing formula fields, flows, and Apex that read legacy NPSP rollup fields will silently break downstream automations. The correct pattern is to audit first, create replacement rollup definitions, then enable CRLP.

2. **Relying on Incremental recalculation after bulk data loads** — Incremental recalculation only processes records flagged as dirty by Opportunity DML. Bulk Data Loader imports and API inserts may not set this flag reliably. Always run a Full recalculation after any significant data import to ensure values are accurate.

3. **Recreating CRLP definitions manually per environment** — Manually recreating Rollup Definitions and Filter Groups in each sandbox and production environment produces configuration drift and undetectable errors. Treat CRLP custom metadata as code: retrieve it, store it in version control, and deploy it via the Metadata API.

---

## Official Sources Used

- Customizable Rollups Overview — NPSP Help — https://powerofus.force.com/s/article/NPSP-Customizable-Rollups-Overview
- Configure Customizable Rollups — NPSP Help — https://powerofus.force.com/s/article/NPSP-Configure-Customizable-Rollups
- Create Filter Groups — NPSP Help — https://powerofus.force.com/s/article/NPSP-Create-Filter-Groups
- Batch Job Modes for Customizable Rollups — NPSP Help — https://powerofus.force.com/s/article/NPSP-Batch-Job-Modes-for-Customizable-Rollups
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
