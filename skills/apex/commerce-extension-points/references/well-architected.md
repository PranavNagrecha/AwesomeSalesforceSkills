# Well-Architected Notes — Commerce Extension Points

## Relevant Pillars

- **Reliability** — Cart extensions execute synchronously inside the Commerce recalculation pipeline. Any unhandled exception fails the entire pipeline and blocks the buyer. Defensive coding, null checks, and graceful degradation (fall back to catalog price on ERP callout failure) are production requirements, not optional hardening.
- **Performance** — Extensions run inline during cart recalculation, which buyers experience directly as page load time. SOQL queries inside the hot loop of `calculate()` compound per-item. Use static maps or Platform Cache to pre-fetch lookup data outside the item iteration loop. Callout latency directly affects buyer-perceived checkout speed.
- **Security** — External callouts from before hooks must use Named Credentials or External Credentials — never hardcoded endpoint URLs or credentials in code. Cart item data (prices, quantities, product IDs) must not be logged to debug logs in production without data classification review, since it may include pricing or customer information.

## Architectural Tradeoffs

**Synchronous vs. Event-Driven Enrichment:** Performing external enrichment (pricing, inventory) synchronously inside the extension provides the strongest consistency guarantee — the cart reflects the live external state before the buyer sees it. The tradeoff is latency: a slow ERP or WMS callout directly increases checkout page load time. For high-latency external systems, consider whether approximate (cached) values with a "prices may vary" disclosure are acceptable, allowing the callout to be skipped or pre-fetched.

**Single Extension vs. Multiple Extensions per EPN:** The platform supports only one registered extension per EPN per store. This forces all pricing customizations into a single Apex class, which can become a maintenance burden. The correct architectural response is a chain-of-responsibility pattern inside the single class: a dispatcher that routes to modular handler classes based on product category, customer tier, or other criteria. This keeps the extension point wiring simple while allowing the internal logic to scale.

**Error Handling Strategy:** A cart extension that throws an unhandled exception fails the entire cart recalculation. For integrations with external systems, defensive fallback logic (log the failure, use catalog price) is typically preferable to allowing the exception to propagate. However, for inventory checks where over-ordering has business consequences, it may be correct to fail loudly and prevent checkout. The choice must be documented and aligned with the business owner.

## Anti-Patterns

1. **DML Inside Extension Hooks** — Attempting to insert audit records, update cart-adjacent objects, or log to custom objects inside `calculate()` is architecturally incompatible with the synchronous pipeline. It produces `System.DmlException` at runtime and fails checkout for all buyers. Use Platform Events to defer data writes outside the extension lifecycle.

2. **Async Escalation Inside the Extension** — Reaching for `@future` or `enqueueJob` to offload slow logic produces an immediate `System.AsyncException`. This pattern is common in trigger-based code but categorically wrong inside Commerce extensions. All logic must complete synchronously or be structured as a Platform Event + async subscriber outside the extension.

3. **One RegisteredExternalService Record Per Extension Deployment** — Creating a new metadata record for each deployment cycle instead of updating the existing record leads to silent overrides and orphaned records. Treat the `RegisteredExternalService` record as a singleton configuration artifact per EPN, updated in place when the implementation changes.

## Official Sources Used

- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- B2B Commerce Extensions — Available Extensions — https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2c_comm_dev_cart_calculate_extensions.htm
- Cart Calculate API — B2B Commerce Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2c_comm_dev_cart_calculate_api.htm
- Commerce Apex Reference — CartCalculate — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_namespace_CartExtension.htm
- Get Started with B2B Commerce Extensions — https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2c_comm_dev_cart_calculate_get_started.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
