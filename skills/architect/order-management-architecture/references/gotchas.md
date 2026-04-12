# Gotchas — Order Management Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Without OCI Provisioning, OMS Has No Real-Time Inventory Signal and Routes to a Single Default Location

**What happens:** When Omnichannel Inventory (OCI) is not provisioned, the `Find Routes with Fewest Splits` Flow action has no inventory availability data to work with. It does not throw an error or warn that OCI is missing. Instead, it silently routes all orders to the single default fulfillment location configured on the org. Multi-location routing never executes.

**When it occurs:** Any org that configures OMS routing flows without first provisioning OCI. Testing in a sandbox with a single fulfillment location will not surface this issue because single-location routing works correctly with or without OCI.

**How to avoid:** Verify OCI provisioning as the first step in any OMS architecture engagement. Confirm that OCI location IDs are mapped to FulfillmentLocation records before activating routing flows. If OCI cannot be provisioned within the project timeline, design a single-location architecture explicitly and document the OCI dependency as a future-phase requirement.

---

## Gotcha 2: OCI Availability Is Eventually Consistent — Reservation Failures Are a Normal Code Path

**What happens:** OCI availability queries return inventory counts that may be seconds to low minutes stale under concurrent order load. Two orders requesting the last unit of the same SKU can both receive an availability count of 1 from their queries. Only one reservation will succeed; the second will fail. If the routing Flow does not have a retry or fallback path for reservation failure, the second order is stuck — no FulfillmentOrder is created and no error surfaces to operations staff.

**When it occurs:** Any high-volume scenario with concurrent orders for the same popular SKU. Promotional events, flash sales, and holiday peaks amplify this substantially. Even at moderate volumes (100+ orders/hour for a single SKU), reservation collisions occur.

**How to avoid:** Design the routing Flow to treat reservation failure as an expected code path, not an error. Implement a retry queue using a Platform Event (e.g., `RetryRouting__e`) with a short delay (30–60 seconds) before re-querying OCI and re-attempting the fewest-splits calculation. After N retries, escalate to a Process Exception record for manual operations review. Do not design the Flow to fail the order on first reservation failure.

---

## Gotcha 3: The ensure-refunds Job Does Not Fire Until ReturnOrder Is Explicitly Progressed

**What happens:** Calling the `submit-return` Connect API action creates ReturnOrder and ReturnOrderLineItem records but does NOT issue a refund. The `ensure-refunds` job is completely decoupled from return creation. If no process transitions the ReturnOrder to the status that triggers ensure-refunds invocation, the refund is never issued. The customer sees their return request acknowledged but the refund never arrives.

**When it occurs:** Any OMS implementation where the ReturnOrder status machine is not explicitly designed and implemented. This is surprisingly common — practitioners assume returns and refunds are a single operation because that is how most e-commerce platforms work.

**How to avoid:** Design and implement a complete ReturnOrder status machine before go-live. Define the status that triggers ensure-refunds invocation (typically `Received` or `Closed`), build a Record-Triggered Flow or Apex trigger that fires on that status transition, and test the full returns-to-refund path end-to-end in a sandbox. Do not treat `submit-return` success as proof that refund issuance will work.

---

## Gotcha 4: FulfillmentOrder Creation Is Not Automatic — Routing Must Be Wired

**What happens:** OMS does not automatically create FulfillmentOrders when an OrderSummary is created. The routing and FulfillmentOrder creation steps must be explicitly wired in an orchestrating Flow or Apex process that subscribes to the `OrderSummaryCreatedEvent` platform event or polls OrderSummary status. If this wiring is absent, OrderSummary records are created but no FulfillmentOrders appear and orders never move toward fulfillment.

**When it occurs:** Any new OMS implementation where the team focuses on OrderSummary creation (the storefront integration step) but does not build the downstream routing Flow. This is especially common in phased implementations where fulfillment automation is deferred to a later sprint that is then deprioritized.

**How to avoid:** Include routing Flow activation as a hard dependency for any OMS go-live checklist. After creating a test OrderSummary in QA, verify that FulfillmentOrders are created within the expected time window before declaring the integration working. A successful OrderSummary creation without corresponding FulfillmentOrders indicates the routing wiring is missing or inactive.

---

## Gotcha 5: OrderDeliveryGroupSummary Is the Routing Unit — Order-Level Routing Logic Misses Multi-Group Orders

**What happens:** Routing logic written at the Order or OrderSummary level works correctly for orders with a single delivery group (single ship-to address) but silently produces incorrect FulfillmentOrder assignments for orders with multiple delivery groups (e.g., ship-to-home items and pick-up-in-store items in the same order). Each OrderDeliveryGroupSummary (ODGS) must be routed independently because different delivery groups may go to different locations.

**When it occurs:** Architects who model the routing logic as "given an order, assign a fulfillment location" rather than "given a delivery group, assign a fulfillment location." This misunderstanding is common because the customer-facing concept of an "order" is a single purchase event, but the OMS routing unit is the ODGS.

**How to avoid:** Build all routing logic to iterate over ODGS records associated with an OrderSummary, not over the OrderSummary itself. The `Find Routes with Fewest Splits` action takes an ODGS ID as its primary input — this is the correct signal that ODGS-level routing is required. Verify routing behavior for test orders that contain items from different delivery groups before go-live.
