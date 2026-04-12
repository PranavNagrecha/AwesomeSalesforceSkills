# Examples — Order Management Architecture

## Example 1: OCI-Wired Split-Order Routing for a Multi-Warehouse B2C Org

**Context:** A B2C retailer operates four fulfillment warehouses (East, Central, West, and a liquidation center). Orders frequently contain 3–5 line items. The retailer's shipping SLA requires minimizing split shipments to keep costs below $8/order average.

**Problem:** Without explicit OCI wiring, the OMS routing Flow routes every order to the East warehouse as the single configured default. When East is out of stock on an item, the order is stuck — no fallback logic exists. Shipping costs also spike because East fulfills orders regardless of customer proximity.

**Solution:**

The architect designs a routing Flow triggered by `OrderSummaryCreatedEvent` platform event:

```
[OrderSummaryCreatedEvent fires]
    |
    v
[Flow: Get OrderDeliveryGroupSummary for new OrderSummary]
    |
    v
[Flow: Query OCI availability for all SKUs at all 4 locations]
    |
    v
[Flow: Call "Find Routes with Fewest Splits" action with ODGS + OCI results]
    |
    v
[Decision: Single location can fulfill all items?]
    YES → Create 1 FulfillmentOrder for winning location
    NO  → Create N FulfillmentOrders for fewest-splits set
    |
    v
[OCI: Reserve quantities for winning location(s)]
    |
    v
[Decision: Reservation succeeded for all items?]
    YES → Advance FulfillmentOrders to Allocated
    NO  → Publish RetryRouting__e platform event; retry in 30s
```

OCI location IDs are stored on custom fields on the FulfillmentLocation object to enable the OCI query step to look up the correct location reference without hardcoding.

**Why it works:** The fewest-splits action has real inventory data from OCI for all four locations, so it can compare them and select the single location or pair of locations that minimizes split shipments. The retry path on reservation failure handles eventual-consistency race conditions without failing the order.

---

## Example 2: ReturnOrder State Machine with Deferred Refund

**Context:** A fashion e-commerce merchant has a 30-day return policy. Customers initiate returns via the storefront; warehouse staff physically receive and inspect returned goods before a refund is issued. The merchant needs assurance that refunds never fire before goods are received.

**Problem:** The initial implementation wired `ensure-refunds` to fire immediately when a ReturnOrder was created by the storefront's `submit-return` call. Customers received refund confirmation within seconds of submitting a return request, before any goods were received. The merchant began seeing refund fraud where customers claimed returns and received refunds without sending items back.

**Solution:**

The architect defines a ReturnOrder status machine with an explicit warehouse confirmation gate:

```
submit-return (Connect API)
    |
    v
ReturnOrder.Status = "Submitted"
    (Customer receives "Return Initiated" email)
    |
    v
Warehouse scan / OMS agent action
    |
    v
ReturnOrder.Status = "In Transit"
    |
    v
Warehouse receives package, scans barcode
    |
    v
ReturnOrder.Status = "Received"
    (Triggers: Record-Triggered Flow on ReturnOrder)
    |
    v
[Flow: Invoke ensure-refunds Connect API action]
    |
    v
ReturnOrder.Status = "Closed"
    (Customer receives "Refund Issued" email)
```

The Record-Triggered Flow fires on ReturnOrder after-save when `Status CHANGED TO "Received"`. It calls the `ensureRefunds` Connect API action. The flow catches errors from the payment gateway and creates a Process Exception record if the refund call fails, enabling a service agent to manually retry.

**Why it works:** The ensure-refunds call is explicitly gated on physical receipt confirmation. Fraud requires warehouse staff to mark goods as received before the refund fires. The Process Exception fallback ensures no refund silently fails without a human review queue item.

---

## Anti-Pattern: Assuming Routing Executes Automatically

**What practitioners do:** An architect provisions OMS, creates FulfillmentLocation records, configures OCI, and expects orders to automatically route to the nearest location. They test the storefront checkout, observe that OrderSummary records are created, and close the sprint — assuming FulfillmentOrders will appear.

**What goes wrong:** No FulfillmentOrders are ever created. OrderSummary records accumulate in `Created` status indefinitely. Orders never advance to fulfillment. The merchant ships nothing.

**Correct approach:** OMS does not create FulfillmentOrders automatically. An orchestrating Flow or Apex process must subscribe to `OrderSummaryCreatedEvent` (or poll on OrderSummary status) and explicitly call the routing action and FulfillmentOrder creation steps. This Flow must be explicitly built, activated, and tested. Verifying that an OrderSummary was created is not sufficient to confirm routing is working — verify that FulfillmentOrders are also created.
