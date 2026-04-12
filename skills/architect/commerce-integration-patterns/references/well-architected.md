# Well-Architected Notes — Commerce Integration Patterns

## Relevant Pillars

- **Security** — The payment architecture's PCI isolation requirement is a hard security constraint: raw card data must never transit Salesforce. Named Credentials are mandatory for all external API credentials (ERP, shipping, tax engine, payment gateway). OAuth 2.0 flows for ERP/PIM integration authentication must use Connected Apps with least-privilege scopes. Storing API keys in Custom Settings or hardcoded in Apex violates this pillar.
- **Reliability** — CartExtension calculators execute synchronously in the checkout critical path. A callout that times out or throws an unhandled exception fails the entire cart calculation for the customer. Calculators must implement graceful fallback behavior: if the ERP pricing callout fails, fall back to Salesforce price book prices and log the failure rather than propagating an exception to the storefront. Shipping and inventory calculators should similarly degrade gracefully.
- **Integration** — Commerce integration uses platform-native extension points (CartExtension namespace, RegisteredExternalService metadata) rather than ad hoc workarounds. PIM sync uses the upsert-with-External-ID pattern for idempotency. Each external system is integrated through exactly one designated extension point — no duplicate registration per EPN per store.
- **Performance** — CartExtension callouts add latency to every cart page load and checkout step. Callout timeout configuration should reflect acceptable checkout latency budgets (typically 5–10 seconds maximum). Where real-time accuracy is not required (e.g., published catalog pricing vs. customer-specific contract pricing), batch or cached approaches are preferable to synchronous callouts.
- **Operational Excellence** — RegisteredExternalService metadata records must be tracked in source control alongside the Apex calculator classes they reference. PIM sync jobs must log partial failures via a Platform Event or custom error object for operational visibility. Named Credential configurations should be documented in deployment runbooks.

## Architectural Tradeoffs

### Real-Time vs. Batch for Pricing and Inventory

Synchronous ERP callouts from CartExtension calculators provide real-time accuracy but add latency to every cart interaction and introduce a hard dependency on ERP availability. If the ERP is unavailable, checkout is degraded or blocked. The alternative — batch-syncing prices and inventory into Salesforce objects and reading from those — eliminates the availability dependency and adds no checkout latency, but introduces staleness risk (prices and stock levels may lag by minutes to hours).

The recommended pattern is a hybrid: batch-sync catalog and standard prices nightly, and use CartExtension callouts only for customer-specific contract pricing or live inventory that cannot tolerate staleness. This minimizes the ERP dependency surface in the checkout critical path.

### Single CartExtension Class vs. Delegated Architecture

Because only one class per EPN per store is allowed, that class bears responsibility for all pricing (or shipping, or inventory) logic for the store. For complex orgs with multiple pricing tiers, multiple ERP sources, or mixed product types, this can produce a monolithic calculator class. The tradeoff is between extensibility (favor separate classes per concern) and the platform constraint (one class per EPN). The correct response is to design the single registered class as a dispatcher/facade that delegates to separate service classes — not to attempt multiple registrations.

### SOM vs. Custom OMS Integration

Salesforce Order Management provides pre-built fulfillment workflow nodes and payment lifecycle management. It adds significant platform capability but requires a separate license and configuration investment. For merchants with an existing OMS (SAP, Manhattan, Oracle WMS), integrating Commerce with the existing OMS via outbound Platform Events or a MuleSoft flow is often preferable to adopting SOM. This avoids dual-ownership of order lifecycle and reduces license cost. The correct architecture decision depends on whether the existing OMS can be reliably called at order placement time.

## Anti-Patterns

1. **Callout After DML in CartExtension Calculator** — Placing an HTTP callout anywhere in `calculate()` after a DML statement, `FOR UPDATE` query, or other uncommitted-work operation causes `System.CalloutException` at runtime. The mitigation is strict ordering: all callouts before any DML, always.

2. **Multiple RegisteredExternalService Records for the Same EPN and Store** — Registering two classes for the same EPN and store produces non-deterministic behavior — only one is invoked, and which one varies. The mitigation is auditing registrations before deployment and merging logic into the existing registered class using a dispatcher pattern.

3. **Insert Without External ID in PIM Sync** — Using `insert` rather than `upsert` with an External ID for PIM product sync produces duplicate `Product2` records on every re-run. Duplicates cause pricing and search inconsistencies in the storefront. The mitigation is defining an External ID field before the first sync and using `Database.upsert()` exclusively.

4. **Hardcoded API Credentials in Apex** — Storing ERP, tax engine, shipping, or payment gateway API keys directly in Apex code, Custom Settings, or Custom Metadata values that are not Named Credentials creates security risk and complicates credential rotation. Named Credentials with per-environment credential records are the correct pattern.

5. **Assuming SOM Is Always Licensed** — Designing the Commerce integration with SOM-dependent fulfillment workflow nodes without confirming SOM licensing at project scoping leads to integration gaps discovered late in implementation. Always confirm SOM license status and document the capture/refund ownership decision in the architecture record.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- B2B Commerce and D2C Commerce Developer Guide — Payment Architecture — https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2b_b2c_comm_payment_architecture.htm
- B2B Commerce Extensions — Cart Calculate API — https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2b_b2c_comm_cart_calculate_api.htm
- Salesforce Commerce Extensions — Get Started — https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2b_b2c_comm_extensions_get_started.htm
