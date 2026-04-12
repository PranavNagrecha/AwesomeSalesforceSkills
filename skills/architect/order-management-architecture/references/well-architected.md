# Well-Architected Notes — Order Management Architecture

## Relevant Pillars

- **Reliability** — OMS fulfillment workflows must handle OCI reservation failures, routing engine unavailability, and payment gateway downtime without losing orders or issuing incorrect refunds. Retry queues, Process Exception records, and deferred refund patterns are the primary reliability mechanisms. The architecture must define explicit failure modes and recovery paths for every async operation.

- **Performance** — Routing transaction latency directly affects order confirmation time visible to customers. OCI availability queries, Flow invocations, and FulfillmentOrder creation DML all run within the order confirmation path. At peak volumes, routing must stay within governor limits and complete within acceptable latency bounds. Batch returns processing (ensure-refunds at scale) must be explicitly profiled to avoid CPU and callout limit exhaustion.

- **Operational Excellence** — New fulfillment locations, new routing rules (e.g., hazmat exclusions, carrier SLA tiers), and new return policies must be addable without rebuilding core routing flows. The architecture should parameterize location topology and routing rules so they can be updated through configuration rather than Flow or Apex changes. Hardcoded location IDs or routing conditions are an operational anti-pattern that creates change-management risk.

## Architectural Tradeoffs

**OCI consistency vs. routing accuracy:** OCI's eventually consistent model means routing decisions can act on slightly stale inventory counts. Architects can choose to accept occasional reservation failures (handled by retry logic) or to implement a more conservative routing strategy that queries OCI immediately before reservation (reducing staleness but adding latency). The retry-based approach is recommended for most orgs; synchronous double-check queries are warranted only for very high-value or limited-availability items.

**Routing complexity vs. operational simplicity:** The fewest-splits algorithm can produce optimal split decisions but requires OCI wiring, retry logic, and a well-configured location topology. For orgs with two or three fulfillment locations and low split-order frequency, a simpler priority-based routing rule (location A first, location B fallback) may be easier to operate and debug. Architects should recommend the fewest-splits approach when the business has demonstrated cost sensitivity to shipping splits, not as a default.

**Returns speed vs. fraud prevention:** Issuing refunds immediately on return creation is faster for legitimate customers but creates fraud risk. The deferred refund pattern (tied to warehouse receipt confirmation) is the architecturally correct approach per the OMS design intent but requires warehouse process discipline. Architects must make this tradeoff explicit and get business sign-off on which status triggers refund issuance.

## Anti-Patterns

1. **Routing without OCI** — Designing multi-location routing flows without provisioning Omnichannel Inventory produces a routing architecture that appears complete but silently routes everything to a single default location. All routing logic is effectively inert until OCI is provisioned and wired. This is the most common OMS architecture failure mode.

2. **Treating ensure-refunds as synchronous return processing** — Wiring ensure-refunds to fire immediately on return creation conflates the return acknowledgment step with the financial settlement step. This breaks the OMS intended control flow, creates fraud exposure, and makes it impossible to gate refunds on warehouse receipt confirmation after the fact.

3. **Order-level routing logic instead of ODGS-level** — Routing logic that operates on the OrderSummary as a whole rather than on each OrderDeliveryGroupSummary independently fails silently for multi-group orders. The failure is not detected in single-delivery-group testing and only surfaces in production when customers with multi-group orders receive incorrect or missing fulfillment.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Order Management Developer Guide v66.0 Spring '26 — https://developer.salesforce.com/docs/atlas.en-us.order_management_developer_guide.meta/order_management_developer_guide/
- Connect REST API Developer Guide — Fulfillment Orders — https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_order_management.htm
- Routing with Omnichannel Inventory — Salesforce Help — https://help.salesforce.com/s/articleView?id=sf.omnichannel_inventory_routing.htm
