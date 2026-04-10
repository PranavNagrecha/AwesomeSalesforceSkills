# Well-Architected Notes — Billing Integration Apex

## Relevant Pillars

- **Security** — Payment gateway credentials must never appear in Apex source code or custom metadata in plain text. Use Named Credentials for all gateway endpoint authentication. Ensure `blng__Payment__c` records storing tokenized payment methods are protected with field-level security and object permissions restricted to the integration user and billing team profiles. Apply sharing rules carefully — payment data is sensitive. Validate that session IDs used in Connect REST API self-callouts are not persisted or logged.
- **Performance** — `blng.TransactionAPI` methods each make an HTTP callout to an external gateway; latency is dominated by the gateway response time, typically 200ms–2s per call. Do not call `TransactionAPI` in bulk synchronous loops. Async patterns (Queueable) are mandatory, not optional, for volume scenarios. Monitor `blng__PaymentGatewayLog__c` record count growth for orgs processing high transaction volumes — archive or delete old log records to avoid performance degradation in SOQL queries.
- **Scalability** — The Connect REST API 200-schedule-per-call limit is a hard ceiling. Design invoice generation services with chunking built in from the start, not retrofitted when volume grows. Queueable chains are limited to a depth of 5 concurrent jobs per transaction; for very high volume, use Batch Apex to drive Queueable dispatches rather than recursive chaining.
- **Reliability** — Gateway callout failures are silent unless explicitly handled. `blng.TransactionAPI` result objects return a `success` boolean and `errorMessage` field — always check these and persist failures to a log record or Platform Event so operations teams can identify and retry failed transactions. Implement idempotency checks before retrying gateway calls to avoid duplicate charges.
- **Operational Excellence** — Log all gateway interaction results to `blng__PaymentGatewayLog__c` (the Billing package writes these automatically through the adapter interface) or to custom log objects for non-adapter callouts. Use Platform Events or custom notification mechanisms to alert on gateway failures in near-real-time rather than discovering issues in batch reconciliation runs.

## Architectural Tradeoffs

### Synchronous vs. Asynchronous TransactionAPI Execution

The core architectural constraint is that `blng.TransactionAPI` cannot share a transaction with DML. This forces an async-first architecture. The tradeoff is latency: a Queueable job adds queue processing time (typically seconds to minutes depending on org load) before the gateway is called. For user-facing payment flows where immediate feedback is expected, consider using Continuation callouts (available in Visualforce and Aura) to preserve synchronous user experience while isolating the callout from DML. For background subscription processing, the Queueable pattern is preferred.

### Connect REST API vs. Invoice Run Batch

The Connect REST API provides targeted, on-demand invoice generation with precise schedule control. The standard Invoice Run batch processes all eligible schedules across the org. The tradeoff is granularity vs. simplicity: the API requires chunking logic and async callout handling; the batch is simpler to configure but cannot be scoped to a subset of schedules. For milestone-based billing or event-triggered invoicing, the API is the correct choice. For standard periodic billing across all active subscriptions, the Invoice Run batch is more operationally appropriate.

### Custom Gateway Adapter vs. Direct Trigger Callout

Implementing `blng.PaymentGateway` routes all transaction lifecycle calls through the Billing package's internal machinery, which creates `blng__PaymentGatewayLog__c` records, updates `blng__Payment__c` status fields, and drives reconciliation reports. Direct trigger-based callouts bypass this, reducing coupling to the package but losing all built-in observability and reconciliation features. For orgs that use Billing's native reports and reconciliation workflows, the adapter pattern is strongly preferred.

## Anti-Patterns

1. **Synchronous TransactionAPI in Triggers** — Calling `blng.TransactionAPI` methods directly in a trigger handler body that also performs DML on Billing records causes `CalloutException` and full transaction rollback. This pattern is undeployable in production at any volume. Always offload gateway calls to an async context.

2. **Hardcoded Gateway Credentials in Apex** — Embedding API keys, bearer tokens, or endpoint URLs directly in Apex source code exposes credentials in version control and Salesforce debug logs. Use Named Credentials for endpoint management and `Protected` Custom Metadata Types for any configuration that must be stored in metadata. Rotate credentials without code changes.

3. **Unbounded Schedule ID Lists to Connect REST API** — Querying all active billing schedules and passing the entire result set to the invoice generation API without a size check fails silently or with an HTTP 400 when the count exceeds 200. This produces zero invoices for the entire run despite no visible error in some implementations. Always enforce the 200-limit explicitly in code.

## Official Sources Used

- Salesforce Billing Developer Guide — InvoiceAPI Class: https://developer.salesforce.com/docs/atlas.en-us.billing.meta/billing/billing_dev_invoice_api.htm
- Salesforce Billing Developer Guide — TransactionAPI Class: https://developer.salesforce.com/docs/atlas.en-us.billing.meta/billing/billing_dev_transaction_api.htm
- Salesforce Billing Developer Guide — Global Payment API: https://developer.salesforce.com/docs/atlas.en-us.billing.meta/billing/billing_dev_global_payment_api.htm
- Salesforce Billing Developer Guide — Payment Gateway Adapter: https://developer.salesforce.com/docs/atlas.en-us.billing.meta/billing/billing_dev_gateway_adapter.htm
- Connect REST API — Create Invoices (commerce/invoices): https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_commerce_invoices.htm
- Apex Developer Guide — Making Callouts: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
