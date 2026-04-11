---
name: commerce-order-management
description: "Use this skill for Salesforce Order Management (OMS) tasks: order lifecycle, OrderSummary creation and status, FulfillmentOrder creation and routing, returns, exchanges, cancellations, and platform event subscriptions. Trigger keywords: order management, OrderSummary, FulfillmentOrder, ReturnOrder, ensure-funds, ensure-refunds, submit-cancel, submit-return, adjust-item-submit. NOT for CPQ quote-to-order workflows, standard Salesforce Orders without OMS, or B2B/B2C storefront setup."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Performance
triggers:
  - "How do I create an OrderSummary from an activated Order in Salesforce OMS?"
  - "FulfillmentOrder is not being created or routed correctly — how do I set up fulfillment flows?"
  - "Customer wants to cancel or return items in an order — how do I use submit-cancel or submit-return?"
  - "ensure-funds or ensure-refunds jobs are failing silently — how do I handle payment errors in OMS?"
  - "OrderItemSummary quantity is wrong after I tried to update it with DML — why did it break?"
tags:
  - order-management
  - oms
  - order-summary
  - fulfillment-order
  - return-order
  - connect-api
  - platform-events
inputs:
  - "Activated Salesforce Order record (Status = Activated) with associated OrderItems and PricebookEntries"
  - "OrderLifeCycleType choice: MANAGED (OMS controls all mutations) or UNMANAGED (direct DML allowed)"
  - "Payment gateway or payment method setup (for ensure-funds / ensure-refunds flows)"
  - "Fulfillment location records and routing configuration"
  - "OMS license confirmation: Salesforce Order Management or Commerce license must be provisioned"
outputs:
  - "OrderSummary record with correct OrderLifeCycleType (immutable after creation)"
  - "FulfillmentOrder and FulfillmentOrderLineItem records routed to fulfillment locations"
  - "ChangeOrder records tracking pre/in/post-fulfillment quantity and price adjustments"
  - "ReturnOrder and ReturnOrderLineItem records for customer returns"
  - "Platform event subscription logic for FOStatusChangedEvent, OrderSumStatusChangedEvent, OrderSummaryCreatedEvent, ProcessExceptionEvent"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Commerce Order Management

This skill activates when a practitioner needs to set up or extend Salesforce Order Management (OMS): creating OrderSummary records from activated Orders, building FulfillmentOrder routing logic, processing cancellations and returns through Connect API actions, handling async payment jobs, and subscribing to OMS platform events. It covers only OMS-licensed orgs — it does NOT cover CPQ orders or standard Salesforce Orders outside of OMS.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has a Salesforce Order Management or Commerce license. OMS objects (OrderSummary, FulfillmentOrder, ReturnOrder) and Connect API order management actions are unavailable without it.
- Establish the `OrderLifeCycleType` for each OrderSummary before creation: MANAGED (all mutations must go through Connect API actions) or UNMANAGED (direct DML is allowed). This value is immutable after the OrderSummary record is created.
- Verify the upstream Order is in `Activated` status before triggering OrderSummary creation. A Draft or non-activated Order will not produce a valid OrderSummary.
- CPQ-generated Orders do NOT automatically create OrderSummary records and are not in scope for this skill.
- Payment gateway and payment method setup must be confirmed before testing ensure-funds or ensure-refunds flows.

---

## Core Concepts

### Order Lifecycle in OMS

The canonical OMS object chain is:

```
Order (Activated)
  └── OrderSummary (OrderLifeCycleType: MANAGED | UNMANAGED)
        ├── OrderItemSummary (one per OrderItem, represents product line)
        └── OrderDeliveryGroupSummary (groups items by shipping address/method)
              └── FulfillmentOrder
                    └── FulfillmentOrderLineItem
ReturnOrder
  └── ReturnOrderLineItem
```

An Order must reach `Status = Activated` before the OMS trigger fires to create the OrderSummary. The OrderSummary represents the commercial truth of the order throughout its lifecycle and is the anchor for all downstream financial and fulfillment records.

### MANAGED vs UNMANAGED OrderLifeCycleType

`OrderLifeCycleType` on the OrderSummary record controls whether the platform enforces Connect API usage for mutations:

- **MANAGED**: All quantity and price changes to OrderItemSummary records must be made through Connect API core actions (`submit-cancel`, `submit-return`, `adjust-item-submit`). Direct DML (insert/update/delete) on OrderItemSummary in MANAGED mode will either fail with an exception or silently produce inconsistencies in financial summaries. Change orders are created automatically to track each adjustment.
- **UNMANAGED**: Direct DML is permitted. Intended for custom or non-standard order scenarios that cannot conform to the OMS state machine.

This field is **immutable after OrderSummary creation**. Set it correctly during the Order-to-OrderSummary flow; it cannot be changed later.

### Connect API Order Management Actions

All MANAGED-mode mutations are executed through named Connect API actions. Key actions:

| Action | Purpose | Notes |
|---|---|---|
| `submit-cancel` | Cancel one or more OrderItemSummary quantities | Produces a ChangeOrder; eligible pre-fulfillment |
| `submit-return` | Initiate a return for fulfilled items | Creates ReturnOrder + ReturnOrderLineItem records |
| `adjust-item-submit` | Adjust item quantity or price | Can produce up to 3 separate ChangeOrders for pre/in/post-fulfillment splits |
| `ensure-funds-async` | Authorize or capture payment | Enqueued async job; errors surfaced via ProcessExceptionEvent |
| `ensure-refunds-async` | Issue refund to customer | Enqueued async job; errors surfaced via ProcessExceptionEvent |

### Platform Events for OMS

OMS publishes platform events at key lifecycle moments. Subscribe to these in Flow or Apex:

- **`OrderSummaryCreatedEvent`**: Fires after an OrderSummary is created from an Order. Use to trigger downstream provisioning.
- **`OrderSumStatusChangedEvent`**: Fires when an OrderSummary's status changes (e.g., to Fulfilled, Cancelled).
- **`FOStatusChangedEvent`**: Fires when a FulfillmentOrder status changes (e.g., to Fulfilled, Cancelled).
- **`ProcessExceptionEvent`**: Fires when an async job (ensure-funds-async, ensure-refunds-async) encounters an error. **You must subscribe to this event** to surface payment failures; they are not surfaced through standard exception handling.

---

## Common Patterns

### Pattern: Standard Fulfillment Flow

**When to use:** An Order has been activated and items need to be routed to a fulfillment location for picking, packing, and shipping.

**How it works:**

1. Order reaches `Status = Activated` (manually or through a Checkout flow).
2. OMS trigger fires; `OrderSummaryCreatedEvent` is published.
3. Subscribe to `OrderSummaryCreatedEvent` in a triggered Flow or Apex handler.
4. In the handler, call the OMS routing engine or a custom routing Flow to create FulfillmentOrder records grouped by location and delivery group.
5. FulfillmentOrder starts in `Draft` status; transition to `Activated` to release to the warehouse.
6. Subscribe to `FOStatusChangedEvent` to react when warehouse marks items as shipped/fulfilled.
7. Call `ensure-funds-async` to capture payment once fulfillment is confirmed.

**Why not the alternative:** Creating FulfillmentOrder records manually via DML without routing logic leads to incorrect location assignments and breaks the OMS inventory reservation model.

### Pattern: Cancellation and Return Flow

**When to use:** A customer wants to cancel an unfulfilled item (pre-fulfillment cancel) or return a fulfilled item.

**How it works:**

Pre-fulfillment cancel:
1. Call Connect API action `submit-cancel` with the OrderSummaryId and a list of `{orderItemSummaryId, quantity}` pairs.
2. OMS validates eligible cancel quantity and creates a ChangeOrder.
3. Call `ensure-refunds-async` to issue the refund. Subscribe to `ProcessExceptionEvent` for failures.

Post-fulfillment return:
1. Call Connect API action `submit-return` with the OrderSummaryId and returned line items.
2. OMS creates a ReturnOrder and ReturnOrderLineItem records.
3. When the ReturnOrderLineItem is processed (item received), call `ensure-refunds-async`.

**Why not the alternative:** Manually updating OrderItemSummary quantities in MANAGED mode will either throw a DML exception or corrupt financial aggregates on the OrderSummary. Always use the Connect API actions.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard B2C or B2B order in OMS-licensed org | Use MANAGED OrderLifeCycleType | Enforces financial consistency; Connect API actions create auditable ChangeOrders |
| Custom order scenario that cannot fit OMS state machine | Use UNMANAGED OrderLifeCycleType | Allows direct DML; but loses OMS financial-summary automation |
| Item cancellation before fulfillment starts | `submit-cancel` Connect API action | Updates TotalCancelled quantities and creates ChangeOrder automatically |
| Item return after fulfillment | `submit-return` Connect API action + ReturnOrder | Creates ReturnOrder records; eligible for `ensure-refunds-async` |
| Price or quantity adjustment spanning fulfillment status | `adjust-item-submit` | Can produce up to 3 ChangeOrders to split pre/in/post-fulfillment amounts |
| Payment authorization or capture | `ensure-funds-async` | Async job; subscribe to ProcessExceptionEvent for error handling |
| Refund issuance | `ensure-refunds-async` | Async job; subscribe to ProcessExceptionEvent for error handling |
| CPQ-generated Order needing OMS processing | Out of scope — CPQ Orders do not create OrderSummary | Separate license and data model required; evaluate integration patterns instead |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify prerequisites**: Confirm OMS license is provisioned, the Order is in Activated status, and OrderLifeCycleType has been decided (MANAGED is the default for OMS implementations).
2. **Establish the OrderSummary**: Ensure the Order activation triggers OrderSummary creation. Confirm that `OrderLifeCycleType` is set correctly before creation since it cannot be changed afterward. Subscribe to `OrderSummaryCreatedEvent` for downstream triggering.
3. **Configure fulfillment routing**: Build or configure the routing logic (OMS routing engine or custom Flow/Apex) to create FulfillmentOrder records from OrderDeliveryGroupSummary records. Validate that FulfillmentOrders reference correct locations.
4. **Implement cancellation and return paths**: Use `submit-cancel` for pre-fulfillment cancellations and `submit-return` for post-fulfillment returns. Never use direct DML on OrderItemSummary in MANAGED mode.
5. **Wire up async payment jobs**: Invoke `ensure-funds-async` after fulfillment confirmation and `ensure-refunds-async` after return/cancel. Subscribe to `ProcessExceptionEvent` to catch and handle payment job failures.
6. **Subscribe to OMS platform events**: Register event-triggered Flows or Apex for `FOStatusChangedEvent`, `OrderSumStatusChangedEvent`, and `ProcessExceptionEvent` to keep downstream systems synchronized.
7. **Test end-to-end in sandbox**: Activate a test Order, verify OrderSummary creation, run a cancellation and a return through the Connect API, confirm ChangeOrder records are created, and verify ProcessExceptionEvent handling fires correctly.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] OMS license is confirmed on the org
- [ ] OrderLifeCycleType is set to the correct value before OrderSummary creation and has been documented — it cannot be changed after creation
- [ ] All MANAGED-mode mutations use Connect API actions (submit-cancel, submit-return, adjust-item-submit) — no direct DML on OrderItemSummary
- [ ] ProcessExceptionEvent subscription is in place for ensure-funds-async and ensure-refunds-async failures
- [ ] FulfillmentOrder creation and routing logic handles all OrderDeliveryGroupSummary records
- [ ] Platform event subscriptions (OrderSummaryCreatedEvent, FOStatusChangedEvent, OrderSumStatusChangedEvent) are deployed and tested
- [ ] CPQ orders have been confirmed as out of scope; a separate integration path is documented if CPQ feeds into OMS

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **OrderLifeCycleType is immutable after OrderSummary creation** — If MANAGED is set and later the implementation requires direct DML, there is no API to change it. The OrderSummary must be deleted and recreated, which can orphan related financial records. Plan the lifecycle type carefully before go-live.
2. **Direct DML on OrderItemSummary in MANAGED mode silently corrupts totals** — Updating `QuantityCanceled` or `TotalPrice` directly via Apex DML does not raise a reliable exception in all API versions; in some cases it succeeds but leaves the OrderSummary aggregate fields (TotalAdjustedProductAmount, etc.) in an inconsistent state that cannot be repaired without support.
3. **ProcessExceptionEvent is the only error signal from async payment jobs** — `ensure-funds-async` and `ensure-refunds-async` are enqueued Queueable jobs. They do not throw exceptions to the calling context, and they do not log to standard Apex debug logs by default. If no `ProcessExceptionEvent` subscriber exists, payment failures are invisible at runtime.
4. **adjust-item-submit produces up to 3 ChangeOrders** — If an adjustment spans items that are partially pre-fulfillment, in-fulfillment, and post-fulfillment, the platform creates a separate ChangeOrder for each segment. Code that assumes a single ChangeOrder per adjustment call will miss records.
5. **CPQ Orders do not create OrderSummary records** — CPQ uses its own Order object but the OMS trigger that creates OrderSummary only fires for Orders provisioned through the Commerce/OMS activation path. A CPQ Order activated in the standard Salesforce UI will not produce an OrderSummary. Do not mix these paths.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| OrderSummary record | Immutable-lifecycle-type record representing the commercial truth of the order; anchor for all OMS financial and fulfillment records |
| FulfillmentOrder + FulfillmentOrderLineItem | Routing unit sent to a specific fulfillment location; transitions through Draft → Activated → Fulfilled |
| ChangeOrder | Audit record created by submit-cancel, submit-return, or adjust-item-submit; up to 3 per adjust-item-submit call |
| ReturnOrder + ReturnOrderLineItem | Return authorization and line-level return records created by submit-return |
| Platform event subscriptions | Flow or Apex triggers on FOStatusChangedEvent, OrderSumStatusChangedEvent, OrderSummaryCreatedEvent, ProcessExceptionEvent |

---

## Related Skills

- `commerce-checkout-configuration` — Covers checkout flow setup that activates Orders feeding into OMS
- `commerce-product-catalog` — Product and pricing setup upstream of OMS order creation
- `flow-for-admins` — Building event-triggered Flows to subscribe to OMS platform events
- `quote-to-cash-process` — End-to-end Q2C; references OMS as the fulfillment leg post-order activation

---

## Official Sources Used

- Salesforce Order Management Developer Guide v66.0 Spring '26 — https://developer.salesforce.com/docs/atlas.en-us.order_management_developer_guide.meta/order_management_developer_guide/
- Connect REST API Developer Guide — Order Management Actions — https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_order_management.htm
- Platform Events Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm
- Object Reference — OrderSummary — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_ordersummary.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
