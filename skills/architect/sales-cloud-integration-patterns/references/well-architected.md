# Well-Architected Notes — Sales Cloud Integration Patterns

## Relevant Pillars

- **Reliability** — Sales Cloud integrations are the pipeline between revenue-generating systems. An ERP sync failure means orders do not get fulfilled. A marketing sync failure means leads go cold. Every integration path needs retry logic, dead-letter queues, and reconciliation jobs that detect and correct drift without manual intervention.

- **Security** — Integration users have broad API access to Account, Opportunity, Order, and Contact data. Use Named Credentials to avoid storing secrets in code. Apply field-level security on the integration user's profile to restrict access to only the fields the integration needs. Encrypt sensitive fields (Tax ID, payment terms) at rest. Ensure partner portal integrations use sharing rules and not org-wide open access.

- **Scalability** — Product catalog syncs and initial Account loads can reach hundreds of thousands of records. Use Bulk API 2.0 for large data volumes. Design incremental sync (delta loads based on LastModifiedDate) rather than full table scans. Ensure External ID fields are indexed for efficient upsert performance at scale.

- **Performance** — Bidirectional syncs that fire triggers on every field update create unnecessary processing. Use field-level change detection to sync only when mastered fields change. Avoid synchronous callouts in trigger context; use Queueable or platform events for outbound integration to keep user-facing transactions fast.

- **Operational Excellence** — Integration health must be visible. Log every sync batch with record counts, success/failure ratios, and error details to a custom IntegrationLog object. Set up alerts for sync failure rates exceeding thresholds. Maintain a reconciliation dashboard that compares record counts between Salesforce and external systems.

## Architectural Tradeoffs

**Point-to-point vs middleware:** Point-to-point integrations (Apex callouts, platform events consumed by external systems) are simpler for 1-2 integrations but create a maintenance burden at scale. Middleware (MuleSoft, Dell Boomi) adds cost and complexity but provides centralized logging, transformation, and routing. Choose middleware when three or more external systems need to consume the same Sales Cloud data.

**Real-time vs batch:** Real-time sync (CDC, platform events) provides fresh data but increases API call volume and requires robust error handling for transient failures. Batch sync (scheduled Apex, Bulk API) is simpler to manage and debug but introduces data staleness. Use real-time for order fulfillment and lead routing; use batch for product catalog and account master data.

**Standard objects vs CPQ managed package:** Standard Quote/Order objects are simpler and have no license cost but lack advanced pricing, discount schedules, and contract amendment workflows. CPQ provides these features but introduces managed-package dependencies and a parallel set of objects (SBQQ__Quote__c, SBQQ__QuoteLine__c). The integration layer must map to whichever object model is in use; mixing both in the same org creates confusion.

## Anti-Patterns

1. **God integration user with System Administrator profile** — Granting the integration user full admin access violates least privilege. If the integration credentials are compromised, the attacker has unrestricted access to all data. Instead, create a dedicated integration profile with object and field permissions limited to exactly what the sync requires.

2. **No reconciliation process** — Building an integration without a periodic reconciliation job means drift goes undetected. Records that fail to sync due to transient errors are never retried. Over time, the two systems diverge silently. Always include a scheduled comparison that checks record counts, checksums, or last-modified timestamps between systems.

3. **Treating all objects the same direction** — Assuming every object flows the same way (e.g., all from ERP to Salesforce or all from Salesforce to ERP). In reality, Accounts may be bidirectional, Orders unidirectional outbound, and Leads unidirectional inbound. Applying a single pattern to all objects causes data loss or unnecessary complexity.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Integration Patterns and Practices — https://developer.salesforce.com/docs/atlas.en-us.integration_patterns_and_practices.meta/integration_patterns_and_practices/integ_pat_intro.htm
- Sales Cloud Overview — https://help.salesforce.com/s/articleView?id=sf.sales_core.htm
