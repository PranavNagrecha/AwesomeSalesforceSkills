# Well-Architected Notes — CPQ Integration with ERP

## Relevant Pillars

- **Reliability** — The order transmission trigger must be idempotent and resilient. Platform events provide at-least-once delivery with replay capability. The integration must write the ERP order number back to Salesforce so duplicate transmissions can be detected and suppressed. Amendment routing must be deterministic to avoid duplicate ERP fulfillment records.

- **Performance** — Synchronous ERP callouts at CPQ quote calculation time introduce latency directly into the quoting user experience. If ERP API response times exceed ~2 seconds, use a scheduled pricing sync batch rather than a real-time QCP fetch. Inventory checks must be fully async — QCP callouts are not permitted by the platform.

- **Security** — ERP credentials (API keys, OAuth tokens) must be stored in Salesforce Named Credentials, not hardcoded in Apex or Custom Metadata. The ERP API endpoint must be whitelisted in Remote Site Settings or CSP Trusted Sites. Field-level security on `SBQQ__QuoteLine__c` financial fields (NetPrice, Discount) must be reviewed — integration service accounts should have read access only unless write-back of ERP confirmation data is required.

- **Operational Excellence** — Price sync jobs must be idempotent and logged. Dead-letter handling for failed order transmissions must be defined before go-live. ERP order numbers written back to Salesforce enable support teams to trace a quote through to fulfillment without accessing ERP directly. Amendment detection logic must be tested as part of the integration acceptance test suite, not left to post-go-live discovery.

## Architectural Tradeoffs

**Real-time QCP pricing fetch vs scheduled batch sync:**
Real-time fetch keeps CPQ aligned with ERP at all times but creates an availability dependency — if the ERP pricing API is down, CPQ quotes cannot be calculated. Scheduled batch sync introduces a staleness window but decouples the quoting user experience from ERP availability. Choose based on how frequently ERP prices change and how much staleness is acceptable in the business process.

**Platform events vs polling for order transmission:**
Platform events provide push-based, near-real-time delivery with replay and at-least-once guarantee. Polling (e.g., a scheduled MuleSoft job that queries `Order` every 5 minutes for newly activated records) is simpler to implement but introduces latency, wastes API calls on empty queries, and can miss records if the query filter is not carefully designed. Platform events are preferred for production integrations with SLA requirements.

**Apex callout for ERP writeback vs MuleSoft outbound:**
Writing the ERP order number back to Salesforce via a direct Apex REST call from ERP is simple but couples ERP to Salesforce credentials. Using MuleSoft as the broker for both directions keeps credential management centralized and simplifies error handling. For high-volume orgs, the outbound Salesforce REST API call rate limits are less restrictive than inbound Apex callout governor limits.

## Anti-Patterns

1. **Triggering ERP on quote close** — Quote close precedes Order generation. The Order and its line items may not yet exist. This is the single highest-impact integration design error in CPQ-ERP projects. Always trigger on `Order.Status` reaching the agreed activated value, using a Record-Triggered Flow or platform event.

2. **Treating all CPQ Orders as net-new ERP Sales Orders** — CPQ amendment Orders carry delta quantities. Without amendment detection, the ERP accumulates duplicate fulfillment records for every mid-term contract change. This creates billing, inventory, and reporting inconsistencies that require manual ERP corrections. Build amendment routing before the first go-live, not after.

3. **Querying QuoteLineItem for CPQ data** — CPQ does not populate `QuoteLineItem`. Queries against it return zero rows. Any integration relying on `QuoteLineItem` will silently transmit empty orders to ERP. Always use `SBQQ__QuoteLine__c` for quote-time data and `OrderItem` for order-time data.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- MuleSoft Accelerator for SAP — Quote-to-Cash: https://www.mulesoft.com/exchange/com.mulesoft.accelerators/mulesoft-accelerator-for-sap/
- Get Started with Salesforce CPQ API: https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_api_get_started.htm
- Salesforce Integration Patterns and Practices: https://developer.salesforce.com/docs/atlas.en-us.integration_patterns_and_practices.meta/integration_patterns_and_practices/integ_pat_intro_overview.htm
