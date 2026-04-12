# Well-Architected Notes — Fundraising Integration Patterns

## Relevant Pillars

- **Security** — Payment gateway integrations carry PCI DSS implications. The Salesforce.org Elevate model keeps the org out of PCI scope by handling tokenization in Elevate-managed infrastructure; bypassing Elevate by calling the payment processor directly from Apex re-enters the org into PCI scope. Wealth screening data (net worth estimates, real estate holdings) is sensitive PII that must be secured at the field level. Named Credentials are required for all outbound callouts to prevent credential exposure in Apex code or custom metadata.
- **Reliability** — Asynchronous payment callback patterns (Elevate Connect REST API, batch wealth screening jobs) introduce failure modes that synchronous integrations do not have. A failed Connect REST API call after payment processing leaves a `GiftTransaction` record without gateway metadata. Retry queues, idempotency keys on payment update calls, and reconciliation reports are required for production-grade reliability.
- **Operational Excellence** — Managed packages (iWave, DonorSearch, Classy) reduce long-term maintenance burden by handling API versioning and field schema updates. Custom implementations that replicate this functionality require manual updates on every vendor API change. The preferred pattern is: use the managed package where one exists; build only what the package cannot do.
- **Performance** — Bulk wealth screening submits thousands of Contact IDs to an external API. Without proper rate-limit awareness and batch job design, screening runs can exhaust daily API limits and block other integrations. Event platform syncs that fire on every transaction insert can create excessive callout volume; batching and Change Data Capture are preferred over per-record callouts.
- **Scalability** — The Connect REST API payment updates endpoint supports batch request bodies, enabling multiple `GiftTransaction` updates per call. Integrations that call the endpoint per-transaction at high gift volume will hit API governor limits. Design for batch calls from the outset.

## Architectural Tradeoffs

**Elevate vs. custom payment connector:** Elevate provides PCI compliance, a maintained Stripe integration, and no custom Apex maintenance cost. The tradeoff is lock-in to the Elevate-supported processor set and an additional license cost. Custom AppExchange connectors (Classy, iATS) offer processor flexibility but require partner relationship management and connector maintenance. Direct Apex-to-processor integrations offer maximum flexibility but introduce PCI scope, require security review, and add ongoing Apex maintenance.

**Managed package wealth screening vs. custom API integration:** Managed packages handle field mapping, versioning, and auth for wealth screening. The tradeoff is reduced flexibility in how scores are stored and exposed — the package controls the field names and the UI components. A custom integration can write scores to any field in any format but requires engineering resources to maintain as vendor APIs evolve.

**Marketing Cloud Connect vs. direct API email marketing:** Marketing Cloud Connect provides declarative sync configuration and journey builder integration. Direct API approaches (sending via Marketing Cloud API from Apex) bypass journey logic, lose behavioral tracking, and are harder to maintain. The Connect sync approach is preferred except in edge cases requiring programmatic email triggering from complex org-side logic.

## Anti-Patterns

1. **Using blng.PaymentGateway for NPSP/NPC payment integration** — This interface is Salesforce Billing-only. In NPSP or Nonprofit Cloud orgs, it does not compile and has no payment lifecycle hook. Use Elevate Connect REST API or an AppExchange payment connector instead.
2. **Direct DML insertion of GiftTransaction records from external systems** — External event platforms and fundraising tools that insert `GiftTransaction` records directly via REST API bypass the Elevate gift processing flow and leave records without required gateway metadata. Use a staging object and promote through the GiftEntry path.
3. **Hardcoding external API credentials in Apex or custom metadata** — Payment processor API keys, wealth screening API tokens, and email platform credentials stored in Apex string literals or custom metadata are accessible to any admin with metadata access. All external callout credentials must use Named Credentials.

## Official Sources Used

- Nonprofit Cloud Developer Guide — GiftTransaction and Connect REST API: https://developer.salesforce.com/docs/atlas.en-us.nonprofit_cloud_dev.meta/nonprofit_cloud_dev/nonprofit_cloud_fundraising_transactions.htm
- Salesforce.org Elevate Payment Services documentation: https://help.salesforce.com/s/articleView?id=sfdo.Elevate_Payment_Services.htm
- Connect REST API Reference — Fundraising: https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_fundraising.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
