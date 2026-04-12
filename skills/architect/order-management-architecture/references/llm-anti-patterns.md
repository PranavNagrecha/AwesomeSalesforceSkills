# LLM Anti-Patterns — Order Management Architecture

Common mistakes AI coding assistants make when generating or advising on Order Management Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating OMS Routing as a Simple "Pick Nearest Warehouse" Rule Without OCI Wiring

**What the LLM generates:** "Configure your FulfillmentLocations with addresses, and OMS will automatically route orders to the nearest warehouse based on the customer's shipping address."

**Why it happens:** LLMs conflate OMS routing with generic shipping optimization logic. Training data on e-commerce order management often describes location-selection as distance-based and implicit. OMS routing is not automatic and does not operate on geographic proximity without explicit configuration.

**Correct pattern:**

```
OMS routing requires ALL of:
1. Omnichannel Inventory (OCI) provisioned — inventory signal
2. FulfillmentLocation records with OCI location IDs mapped
3. An orchestrating Flow subscribed to OrderSummaryCreatedEvent
4. The "Find Routes with Fewest Splits" Flow action wired into that Flow
5. OCI reservation logic with a retry path for eventual-consistency failures

Without OCI, all orders route to the single default location regardless
of FulfillmentLocation record count or configuration.
```

**Detection hint:** If the recommendation says OMS "automatically routes" or "selects the nearest location" without mentioning an orchestrating Flow or OCI query, flag it.

---

## Anti-Pattern 2: Assuming ensure-refunds Fires Automatically on Return Creation

**What the LLM generates:** "When you call submit-return, OMS will automatically process the refund. The customer will receive their refund after the return is confirmed."

**Why it happens:** Most e-commerce platforms couple return creation and refund issuance. LLMs generalize this pattern to OMS. In OMS, return creation (submit-return) and refund issuance (ensure-refunds) are explicitly decoupled and require separate invocations with a status transition gate between them.

**Correct pattern:**

```
submit-return → creates ReturnOrder (NO refund yet)
    ↓
ReturnOrder status transitions (warehouse confirms receipt)
    ↓
ensure-refunds invoked ONLY after ReturnOrder reaches target status
    ↓
Refund issued asynchronously via payment gateway
```

**Detection hint:** If the recommendation implies that `submit-return` completes the refund, or if `ensure-refunds` is not mentioned as a separate explicit step, flag it.

---

## Anti-Pattern 3: Designing Routing Logic at the Order Level Instead of the ODGS Level

**What the LLM generates:** "For each order, query the available fulfillment locations and assign the order to the location with the most available stock."

**Why it happens:** LLMs model routing as "order → location" because that is the intuitive customer-facing mental model. The OMS routing unit is the OrderDeliveryGroupSummary (ODGS), not the Order or OrderSummary. An order with multiple delivery groups (different ship-to addresses or fulfillment methods) must have each ODGS routed independently.

**Correct pattern:**

```apex
// Wrong: routing at OrderSummary level
for (OrderSummary os : orderSummaries) {
    assignLocation(os.Id);  // misses multiple delivery groups
}

// Correct: routing at ODGS level
for (OrderSummary os : orderSummaries) {
    List<OrderDeliveryGroupSummary> groups = [
        SELECT Id FROM OrderDeliveryGroupSummary
        WHERE OrderSummaryId = :os.Id
    ];
    for (OrderDeliveryGroupSummary odgs : groups) {
        routeDeliveryGroup(odgs.Id);  // fewest-splits action input
    }
}
```

**Detection hint:** If the routing logic iterates over OrderSummary records and assigns a location to the OrderSummary (not to individual ODGS records), the logic is at the wrong level.

---

## Anti-Pattern 4: Using Connected Commerce Order Routing for B2C Orgs

**What the LLM generates:** "Enable Connected Commerce Order Routing in your OMS settings to get advanced routing capabilities for your B2C storefront."

**Why it happens:** The Connected Commerce brand sounds like it covers all commerce scenarios. LLMs often do not distinguish between the two OMS routing variants by commerce type. Connected Commerce Order Routing is B2B-only; Growth Order Routing is required for B2C and mixed B2B+B2C scenarios.

**Correct pattern:**

```
B2B-only orgs:   Connected Commerce Order Routing
B2C orgs:        Growth Order Routing
B2B + B2C:       Growth Order Routing

The routing variant is provisioned at the org level.
Attempting to use Connected Commerce routing for B2C orders
will result in routing failures or unsupported operation errors.
```

**Detection hint:** If the recommendation suggests Connected Commerce Order Routing for a B2C or mixed scenario without qualification, flag it.

---

## Anti-Pattern 5: Ignoring OCI Eventual Consistency in Routing Flow Design

**What the LLM generates:** "Query OCI for available inventory, then create FulfillmentOrders for the locations returned by the fewest-splits calculation. If inventory shows as available, the reservation will succeed."

**Why it happens:** LLMs default to optimistic consistency assumptions. Training data on inventory systems often treats availability queries as authoritative. OCI is eventually consistent — an availability query returning a positive count does not guarantee that the subsequent reservation will succeed, especially under concurrent load.

**Correct pattern:**

```
[Query OCI availability]
    ↓
[Run fewest-splits calculation]
    ↓
[Attempt OCI reservation]
    ↓
[Decision: Reservation succeeded?]
    YES → Create FulfillmentOrders, advance to Allocated
    NO  → Publish RetryRouting__e event (retry after delay)
          After N retries → Create Process Exception record
          (do NOT fail the order on first reservation failure)
```

**Detection hint:** If the routing design has no branch for OCI reservation failure, or if it treats a positive availability query as a guarantee of successful reservation, the eventual-consistency failure path is missing.

---

## Anti-Pattern 6: Hardcoding Fulfillment Location IDs in Routing Flows

**What the LLM generates:** "In your routing Flow, use a decision element to check if LocationId equals '0Lq000000000001' for East warehouse or '0Lq000000000002' for West warehouse."

**Why it happens:** LLMs optimize for concrete, working code and hardcode IDs as the simplest path to a working example. In production OMS implementations, hardcoded location IDs make the architecture fragile — adding a new fulfillment location requires a Flow rebuild and deployment rather than a configuration change.

**Correct pattern:**

```
Store location references in custom metadata (FulfillmentLocationConfig__mdt)
or custom settings, keyed by a logical name (e.g., "EAST_WAREHOUSE").

Reference the metadata in the routing Flow by logical name, not by ID.
New locations are added by creating new metadata records — no Flow change
or deployment required.
```

**Detection hint:** If a routing Flow or Apex class contains hardcoded record IDs (patterns like `0Lq...` or `01t...`), the location topology is not configurable and will require code changes to update.
