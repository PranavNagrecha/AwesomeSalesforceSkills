# Well-Architected Notes — Commerce Payment Integration

## Relevant Pillars

### Security (Primary)

The payment integration domain is Security-first by necessity. PCI DSS requirements mean raw cardholder data must never reach Salesforce servers. The platform-enforced architecture — cross-domain client-side capture followed by tokenization — is the primary Security pillar implementation. All gateway API credentials must be stored in Named Credentials, never in Custom Settings, Custom Metadata, or hardcoded strings. Apex debug logging must be reviewed to ensure no token values or gateway request bodies containing sensitive references are written to debug logs at verbose levels.

### Reliability

Every `RequestType` branch in `processRequest` must return a typed, non-null response. An unhandled branch causes silent checkout failure. The adapter must handle gateway API errors gracefully — returning `GatewayErrorResponse` with a descriptive message rather than throwing an unhandled exception, which would surface as a confusing system error to the buyer. Retry logic for transient gateway failures must be designed to avoid duplicate authorizations.

### Operational Excellence

The adapter should log gateway reference numbers and result codes to a custom platform event or custom object for reconciliation, without logging sensitive payment method details. Test coverage for all six `RequestType` branches ensures operational confidence. Deployment checklists should include end-to-end sandbox checkout tests before production promotion.

### Performance

The `processRequest` method runs synchronously in the checkout transaction. Callout timeouts must be set explicitly on `HttpRequest` to avoid hanging checkouts during gateway outages. Multi-step gateway flows that require sequential callouts increase the risk of hitting governor limits under load.

### Scalability

The adapter itself is stateless and horizontally scales with Salesforce's infrastructure. Scalability concerns are primarily at the gateway API level: rate limits, concurrency constraints, and the gateway's own throughput limits. Document the target gateway's rate limits in the project architecture decision record.

---

## Architectural Tradeoffs

**Custom adapter vs AppExchange package:** A custom `CommercePayments` adapter gives full control over business logic, error handling, and response mapping, but creates a long-term maintenance obligation. An AppExchange package reduces time-to-value and shifts maintenance to the ISV, but limits customization. Choose the custom path only when no package covers the target gateway.

**Synchronous adapter vs async post-processing:** The `processRequest` method must return synchronously. Any post-transaction enrichment (fraud scoring, risk assessment, order analytics) should be triggered via Platform Events from the adapter or via Order lifecycle hooks — not inline in the adapter, where CPU time and callout limits apply.

**Named Credential vs Custom Settings for gateway credentials:** Named Credentials are the only acceptable approach. Custom Settings are stored in plaintext in the database and visible in query output. Named Credentials store credentials in an encrypted credential store and are not queryable or visible in debug logs.

---

## Anti-Patterns

1. **Raw card data through Apex** — Routing card numbers, CVV, or expiry through any Apex method, including the payment adapter, brings Salesforce into PCI DSS scope and violates the platform's payment integration terms of service. The provider-hosted cross-domain capture component is mandatory.

2. **Hardcoded gateway credentials** — Storing API keys or authentication tokens in Apex constants, Custom Settings, or Custom Metadata Type fields that are queryable brings credentials into audit scope and creates rotation risk. Use Named Credentials exclusively.

3. **Using sfdc_checkout.CartPaymentAuthorize for new LWR store integrations** — This legacy interface is only invoked for Aura-based B2B checkout flows. Implementing it for a modern LWR store results in an adapter that is never called. All new custom payment integrations for B2B Commerce and D2C Commerce must use `CommercePayments.PaymentGatewayAdapter`.

---

## Official Sources Used

- B2B Commerce and D2C Commerce Developer Guide — Payment Architecture: https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/comm_dev_payments_architecture.htm
- B2B Commerce and D2C Commerce Developer Guide — Commerce Payment Gateway: https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/comm_dev_payments_gateway.htm
- Apex Developer Guide — Payment Gateway Adapters: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_commercepayments_adapter.htm
- Apex Reference Guide — CommercePayments Namespace: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_namespace_CommercePayments.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
