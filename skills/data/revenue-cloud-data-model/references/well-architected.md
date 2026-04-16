# Well-Architected Notes — Revenue Cloud Data Model

## Relevant Pillars

- **Reliability** — Amendment creates new BillingSchedule records, not updates. Integrations that assume a single BillingSchedule per OrderItem will miss amendment history and produce incorrect billing reports. Design data consumers to aggregate across the full lifecycle.
- **Operational Excellence** — FinanceTransaction is read-only and system-generated. Accounting integrations must be designed to read and export these records, not write back. Any attempt to correct accounting via FinanceTransaction DML will fail.
- **Security** — Invoice and FinanceTransaction data is sensitive financial information. CRUD/FLS on these objects must be scoped to financial processing roles only.

## Architectural Tradeoffs

**ERP Integration via CDC vs. Scheduled Batch:** ERP integrations that consume Revenue Cloud billing data can use Change Data Capture on Invoice and Payment objects (near-real-time, via Pub/Sub API) or scheduled batch SOQL queries. CDC is more responsive but adds streaming infrastructure complexity. Batch is simpler but introduces reporting lag.

**Aggregate Billing History vs. Current-State Queries:** For billing history across amendments, always aggregate all BillingSchedule records per asset. Current-state queries (LIMIT 1 by date) will miss amendment periods. Design BI models to aggregate, not to find the single "latest" record.

**BillingScheduleGroup Granularity:** Invoice consolidation is controlled by BillingScheduleGroup. Fine-grained grouping (one group per OrderItem) produces many invoices. Coarse grouping (one group per Order) consolidates billing onto fewer invoices. Design grouping policy based on customer billing preferences before deployment.

## Anti-Patterns

1. **Querying blng__* Objects in RLM Orgs** — Using legacy Salesforce Billing managed package object names in native RLM orgs causes query failures. Always confirm the product and use standard API object names.

2. **DML on FinanceTransaction** — FinanceTransaction cannot be created or updated via API. Accounting integrations must read these records and push data to ERP — they cannot write back.

3. **LIMIT 1 BillingSchedule Queries for Amended Assets** — Assets with multiple amendments have multiple BillingSchedule records. Fetching only the latest misrepresents the billing history. Design queries to aggregate across the full lifecycle.

## Official Sources Used

- Revenue Cloud Data Model Gallery — https://architect.salesforce.com/diagrams/template-gallery/revenue-cloud-category
- Billing Invoice Data Model — https://architect.salesforce.com/diagrams/data-models/billing-invoice
- Payments Data Model — https://architect.salesforce.com/diagrams/data-models/payments
- BillingSchedule Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_billingschedule.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
