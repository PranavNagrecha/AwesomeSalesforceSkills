---
name: cpq-integration-with-erp
description: "Use this skill when designing or troubleshooting an integration between Salesforce CPQ and an ERP system (SAP, Oracle, NetSuite, Microsoft Dynamics). Covers the canonical order transmission trigger, pricing data mastery strategy, amendment delta-quantity handling, and non-blocking inventory checks during quoting. NOT for generic Salesforce-to-ERP integration without CPQ, standard Quote-to-ERP patterns that do not involve SBQQ objects, or CPQ-internal configuration such as pricing rules, bundles, or guided selling."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Security
  - Operational Excellence
triggers:
  - "how do I send a CPQ order to SAP or NetSuite when the deal is won"
  - "CPQ order is not showing up in our ERP after the quote is closed"
  - "when exactly should we trigger the ERP fulfillment call from Salesforce CPQ"
  - "how to sync ERP pricing into Salesforce CPQ without creating price book drift"
  - "CPQ amendment or renewal order is creating a duplicate full order in ERP instead of a delta quantity"
  - "inventory availability check during CPQ quoting is timing out or throwing a callout error"
  - "ERP integration is querying QuoteLineItem but returning empty results from CPQ quotes"
tags:
  - cpq
  - erp
  - integration
  - order-management
  - pricing
  - mulesoft
  - sbqq
  - amendment
  - inventory
  - quote-to-cash
inputs:
  - ERP system name and version (SAP S/4HANA, Oracle EBS, NetSuite, Microsoft Dynamics 365)
  - Integration middleware in use (MuleSoft, Dell Boomi, custom Apex callout, Heroku Connect)
  - CPQ edition and any active plugins (Quote Calculator Plugin, Renewal settings)
  - Order management workflow — which Order.Status value triggers fulfillment
  - Pricing mastery decision — is ERP or CPQ the system of record for pricing?
  - Amendment and renewal handling requirements
outputs:
  - Integration trigger point decision (Order.Status value that signals ERP readiness)
  - CPQ-to-ERP data mapping specification (SBQQ objects to ERP document types)
  - Pricing sync architecture recommendation (real-time fetch vs scheduled batch)
  - Amendment delta-quantity routing design
  - Async inventory check pattern for CPQ quoting
  - Review checklist for CPQ-ERP integration readiness

dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# CPQ Integration with ERP

This skill activates when an architect or practitioner must design, implement, or troubleshoot a data and process integration between Salesforce CPQ and a back-office ERP system. It covers the canonical trigger point for order transmission, pricing data mastery strategy, amendment order delta handling, and non-blocking inventory availability checks during quoting.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the exact `Order.Status` value that represents "ERP-ready" with the business process owner. This is almost always a custom status such as `Activated` or `Submitted to ERP`, not the quote-close event.
- The most common wrong assumption is that triggering ERP transmission on quote close (or Opportunity `Closed Won`) is equivalent to triggering on Order activation. It is not — the Order object may not yet exist when the quote closes.
- Key platform constraints: QCP (Quote Calculator Plugin) runs in a restricted Apex context that does not permit HTTP callouts. Inventory checks requiring an ERP API call cannot be embedded in QCP. CPQ stores quote lines on `SBQQ__QuoteLine__c`, not `QuoteLineItem`.

---

## Core Concepts

### The ERP Trigger Point Is Order Activation, Not Quote Close

The most common integration design error is triggering ERP transmission when a CPQ quote reaches `Closed Won` or `Approved`. The correct trigger is **Order record activation** — a field value change on the Salesforce `Order` object (e.g., `Status = Activated`) after the Order has been generated from the approved quote.

Quote close fires while the order is still being generated and validated. ERP systems receiving partial or pre-validated order data produce fulfillment errors that are hard to trace. The Order record, by contrast, carries the full line-item detail required by ERP document types (Sales Order, Purchase Order) and has a stable queryable state.

The MuleSoft Accelerator for SAP uses a platform event or Order status change data capture (CDC) event as the trigger — not a quote-level webhook.

### CPQ Quote Lines Are on SBQQ__QuoteLine__c, Not QuoteLineItem

Salesforce CPQ stores quote line detail on the custom object `SBQQ__QuoteLine__c`. The standard Salesforce object `QuoteLineItem` is **not populated** by CPQ. Any ERP integration that queries `QuoteLineItem` to retrieve CPQ product, quantity, or pricing data will return zero rows.

When the Order is generated from a CPQ quote, CPQ creates `OrderItem` records (standard object) linked to the `Order`. ERP integrations should consume `OrderItem` from the activated Order for order-time data. Quote-time data lives on `SBQQ__QuoteLine__c`.

Key fields on `SBQQ__QuoteLine__c` relevant to integration:
- `SBQQ__Product__c` — product reference
- `SBQQ__Quantity__c` — ordered quantity
- `SBQQ__NetPrice__c` — final priced amount after discounts
- `SBQQ__SubscriptionType__c` — differentiates one-time from recurring lines

### Pricing Mastery and Avoiding Price Book Drift

When ERP is the pricing master, two patterns are used:

**Synchronous fetch at calculation time:** The QCP or a custom Apex price rule calls out to the integration layer to fetch current ERP pricing during quote calculation. This keeps CPQ always aligned with ERP but introduces latency and availability dependency. Callouts from QCP are supported (unlike inventory checks), but must complete within governor limit windows.

**Scheduled batch sync:** A nightly or hourly batch job reads ERP pricing and upserts CPQ `PricebookEntry` records. Simpler operationally but introduces a staleness window. Acceptable when ERP prices change weekly or less frequently.

Maintaining a full copy of ERP pricing in CPQ price books without a controlled sync job causes drift within weeks due to discounting, promotions, and manual edits on either side.

### Amendment Orders Are Delta Quantities, Not Net-New Totals

When a CPQ subscription is amended (e.g., adding 5 seats to an existing 20-seat deal), CPQ generates an Amendment Order with `OrderItem.Quantity = 5` (the delta), not `25` (the new total). ERP systems that interpret every CPQ Order as a net-new order will create a duplicate fulfillment for 5 units instead of updating the existing subscription.

The integration must detect the Order type by checking `SBQQ__AmendedContract__c` on the originating quote or `Order.SBQQ__Contracted__c`. When an amendment is detected, the ERP integration must route to an "update existing contract" or "incremental release" transaction rather than a new Sales Order.

---

## Common Patterns

### Pattern 1: Order Activation Event to ERP via Platform Events

**When to use:** The integration middleware (MuleSoft, Boomi) can subscribe to Salesforce platform events or change data capture (CDC). The business requires reliable, at-least-once delivery with retry.

**How it works:**
1. A Flow publishes a platform event (`Order_Activated__e`) when `Order.Status` transitions to the configured activated value.
2. MuleSoft (or the middleware) subscribes to the platform event channel.
3. The middleware queries the activated Order and its `OrderItem` records.
4. The middleware maps `OrderItem` fields to the ERP Sales Order document schema.
5. For amendments, the middleware checks `Order.SBQQ__Contracted__c` and routes to the ERP delta-update API.
6. ERP confirmation (order number, status) is written back to Salesforce via REST or a second platform event as an external reference ID.

**Why not the alternative (quote-close trigger):** Quote close precedes Order generation. The `Order` object does not yet exist when the quote closes in some configurations, so the middleware cannot query `OrderItem` at that moment. Even when the Order exists, it may not yet have all line items written.

### Pattern 2: Async Inventory Check via Invocable Action and LWC Button

**When to use:** Sales reps need to see inventory availability on the CPQ quote screen before submitting. QCP callout restrictions prevent synchronous inventory calls from the calculation engine.

**How it works:**
1. A custom LWC component on the CPQ quote page presents a "Check Availability" button.
2. The button fires an Apex invocable action (outside QCP) that performs the HTTP callout to the ERP inventory API.
3. Results are stored on custom fields on `SBQQ__QuoteLine__c` (e.g., `Inventory_Status__c`, `Available_Qty__c`).
4. The CPQ quote page displays the stored values — it does not show live data inline in the QCP.

**Why not a QCP callout:** QCP runs in a restricted Apex execution context. Direct HTTP callouts from QCP methods are not supported and throw `System.CalloutException: Callout not allowed from this context`. This is a platform limitation, not a configuration option.

### Pattern 3: Scheduled Pricing Sync with Conflict Detection

**When to use:** ERP pricing changes are infrequent (weekly or monthly), latency tolerance is high, and the integration team cannot support synchronous QCP-time fetches.

**How it works:**
1. A scheduled Apex batch job or MuleSoft scheduled flow queries ERP pricing data via API.
2. The job upserts `PricebookEntry` records using `Product2.ProductCode` as the external ID match key.
3. A conflict detection step compares the incoming ERP price against the current CPQ price before writing. If the delta exceeds a configured threshold (e.g., >5%), the job logs a `Price_Sync_Alert__c` record for manual review rather than silently overwriting.
4. The job is idempotent — re-running produces the same result.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| ERP needs order data after quote approval | Order activation platform event to middleware to ERP | Ensures full OrderItem data is available; reliable retry via middleware |
| ERP is pricing master, prices change daily | Synchronous QCP callout to integration layer at calculation time | Eliminates staleness window; acceptable if ERP API is fast and available |
| ERP is pricing master, prices change weekly | Scheduled batch sync to PricebookEntry | Simpler; reduces ERP API call volume; staleness acceptable |
| Amendment order detected | Route to ERP delta-update API, not new Sales Order | CPQ amendment Orders carry delta quantity; net-new ERP order creates duplicates |
| Inventory check required during quoting | Async invocable action and LWC button, store results on quote line | QCP callout restriction; synchronous inline check is not supported |
| ERP integration queries QuoteLineItem | Redirect queries to SBQQ__QuoteLine__c or activated OrderItem | QuoteLineItem is not populated by CPQ |
| ERP trigger is set to Opportunity Closed Won | Move trigger to Order.Status activated value | Order may not exist at quote-close time |

---

## Recommended Workflow

1. **Establish the trigger point and data contract.** Confirm with stakeholders that Order activation (not quote close) is the ERP trigger. Document the exact `Order.Status` value and the `OrderItem` fields required by the ERP document type (product code, quantity, unit price, currency, ship-to address).

2. **Decide pricing mastery and sync strategy.** If ERP is the pricing master, choose synchronous QCP fetch (for daily price changes) or scheduled batch sync (for weekly changes). Document the staleness tolerance. If CPQ is the pricing master, define how ERP pulls prices (read-only API access to Salesforce).

3. **Design amendment detection logic.** Before building order transmission, add a branching condition that checks for amendment indicators (`SBQQ__AmendedContract__c` on the quote, or Order type flags). Define the ERP delta-update API call and its idempotency key.

4. **Build the async inventory check if required.** Create the invocable Apex action that calls the ERP inventory API. Add the LWC button component to the CPQ quote page layout. Store results on `SBQQ__QuoteLine__c` custom fields. Do not attempt to embed this in QCP.

5. **Implement error handling and retry.** Define the dead-letter queue or retry strategy in middleware. ERP callouts must have timeout handling. Write ERP-side order numbers back to the Salesforce Order as an external reference ID for deduplication.

6. **Test amendment and renewal scenarios explicitly.** Create a CPQ amendment and confirm the integration routes to the delta-update path. Verify the quantity in ERP equals the delta, not the cumulative total.

7. **Review object references and run the checker script.** Confirm all SOQL queries use `SBQQ__QuoteLine__c` for quote-time data and `OrderItem` for order-time data. Run `scripts/check_cpq_integration_with_erp.py --manifest-dir path/to/metadata` to catch common misconfigurations.

---

## Review Checklist

- [ ] ERP trigger is set to Order activation status change, not quote close or Opportunity stage
- [ ] Integration queries `SBQQ__QuoteLine__c` for quote-line data, not `QuoteLineItem`
- [ ] Integration queries `OrderItem` on the activated Order for order transmission data
- [ ] Amendment orders are detected and routed to ERP delta-update API, not net-new Sales Order creation
- [ ] Inventory checks are implemented as async invocable actions with LWC button, not QCP callouts
- [ ] Pricing sync strategy (real-time fetch or batch) is documented with staleness tolerance
- [ ] ERP order number is written back to Salesforce Order as external reference for deduplication
- [ ] Middleware retry and dead-letter handling are configured
- [ ] Multi-currency edge cases are tested if the org uses multi-currency

---

## Salesforce-Specific Gotchas

1. **QCP context does not permit HTTP callouts** — The Quote Calculator Plugin executes in a restricted Apex context. Attempting an HTTP callout (e.g., to an ERP inventory API) from a QCP method throws `System.CalloutException: Callout not allowed from this context`. Inventory checks must be implemented outside QCP using an invocable action triggered by a button or flow.

2. **QuoteLineItem is empty for CPQ quotes** — CPQ bypasses the standard `QuoteLineItem` object entirely. All CPQ quote line data resides on `SBQQ__QuoteLine__c`. Integrations built by teams unfamiliar with CPQ frequently query `QuoteLineItem` via SOQL and get zero rows, then incorrectly assume the quote has no line items.

3. **Amendment Orders carry delta quantity, not cumulative total** — A CPQ amendment adding 10 seats to an existing 50-seat subscription generates an Order with `OrderItem.Quantity = 10`. If the ERP creates a new Sales Order for 10, the ERP subscription record shows 10 seats instead of 60. The integration must detect amendment Orders and route them to an ERP contract-update or incremental-release transaction.

4. **Quote close does not guarantee Order existence** — CPQ Order generation can be asynchronous after quote close in some configurations. Triggering ERP transmission on `Opportunity.StageName = Closed Won` or `SBQQ__Quote__c.SBQQ__Status__c = Approved` may fire before the Order object has been created, resulting in no Order data to transmit and a silent failure.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Integration trigger point decision | Documents which Order.Status value signals ERP readiness and why |
| CPQ-to-ERP data mapping | Maps SBQQ__QuoteLine__c / OrderItem fields to ERP document fields |
| Pricing sync architecture decision | Records chosen sync strategy, staleness tolerance, and conflict-detection rules |
| Amendment routing design | Documents how amendment vs net-new Orders are distinguished and routed |
| Async inventory check design | Documents LWC and invocable Apex pattern for non-blocking inventory display |

---

## Related Skills

- architect/sales-cloud-integration-patterns — broad Sales Cloud integration patterns including unidirectional Quote-to-Order-to-ERP; use alongside this skill for middleware and error-handling guidance
- architect/cpq-architecture-patterns — CPQ-internal architecture (bundles, pricing rules, QCP design); use before this skill to ensure CPQ configuration is stable before integration work begins
- architect/integration-framework-design — middleware selection (MuleSoft vs Boomi vs custom Apex), error handling, retry design; use for the middleware layer specifics

---

## Official Sources Used

- MuleSoft Accelerator for SAP — Quote-to-Cash: https://www.mulesoft.com/exchange/com.mulesoft.accelerators/mulesoft-accelerator-for-sap/
- Pricing and Calculation Package Settings (CPQ): https://help.salesforce.com/s/articleView?id=sf.cpq_pricing_calculation_package_settings.htm
- Get Started with Salesforce CPQ API: https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_api_get_started.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Integration Patterns and Practices: https://developer.salesforce.com/docs/atlas.en-us.integration_patterns_and_practices.meta/integration_patterns_and_practices/integ_pat_intro_overview.htm
