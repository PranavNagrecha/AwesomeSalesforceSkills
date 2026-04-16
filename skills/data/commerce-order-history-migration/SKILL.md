---
name: commerce-order-history-migration
description: "Use when migrating historical order records into Salesforce Order Management — covers the required object creation sequence (Order > OrderDeliveryGroup > OrderItem > OrderSummary), LifeCycleType=Unmanaged for historical orders, and OrderSummary creation via ConnectAPI. NOT for standard Opportunity migration, CPQ legacy order migration using SBQQ objects, or active order processing."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "How do I migrate historical order records into Salesforce Order Management?"
  - "OrderSummary not being created after bulk importing orders via Data Loader"
  - "What is LifeCycleType Unmanaged for historical orders in Salesforce Order Management?"
  - "Required load sequence for Order OrderDeliveryGroup OrderItem OrderSummary migration"
  - "Historical order import failing because ConnectAPI create order summary not called"
tags:
  - order-management
  - order-migration
  - OrderSummary
  - commerce
  - LifeCycleType
inputs:
  - "Historical order data: order header, line items, delivery groups, payment records"
  - "Whether orders are historical (no longer being serviced) or active (still subject to fulfillment/refunds)"
  - "Target Salesforce Order Management org with Order object and OrderSummary enabled"
outputs:
  - "Object load sequence plan with dependency documentation"
  - "ConnectAPI or Flow core action specification for OrderSummary creation"
  - "LifeCycleType selection guidance per order type"
  - "Validation queries to confirm OrderSummary creation"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Commerce Order History Migration

This skill activates when a practitioner needs to migrate historical order records into Salesforce Order Management. It provides the mandatory object creation sequence, explains why OrderSummary cannot be created via direct DML insert, and covers the LifeCycleType=Unmanaged setting for historical orders that disables refund and fulfillment core actions.

---

## Before Starting

Gather this context before working on anything in this domain:

- Salesforce Order Management uses a strict object creation sequence: Order (Status=Draft) → OrderDeliveryGroup → OrderItem → Order activation → OrderSummary via ConnectAPI or Flow core action.
- OrderSummary **cannot** be created via direct DML insert, Bulk API, or Data Loader. Attempting to do so either fails silently or raises an error depending on the API version.
- Historical orders that are no longer being serviced should use `LifeCycleType = Unmanaged`. Unmanaged OrderSummaries disable the refund, cancel, and fulfillment core actions, which is correct for historical data.
- This skill covers Salesforce Order Management (the Order object on the CRM platform), not B2C Commerce Cloud legacy order objects in a separate SaaS system.

---

## Core Concepts

### Mandatory Object Creation Sequence

Salesforce Order Management enforces referential integrity through a strict creation order:

1. **Order** (Status = Draft) — The parent order record. Must be in Draft status before child records are added.
2. **OrderDeliveryGroup** — Delivery grouping: shipping address, delivery method. Must reference a valid Order in Draft status.
3. **OrderItem** — Line items referencing the Order and OrderDeliveryGroup. Product and pricing data.
4. **Order activation** — Change Order Status from Draft to Activated. This commits the order and enables OrderSummary creation.
5. **OrderSummary** — Created via `ConnectAPI.OrderSummaryInputRepresentation` in Apex, or via the "Create Order Summary" Flow core action. This is NOT a direct DML insert.

Attempting to create OrderSummary before Order activation, or via direct DML, will fail.

### LifeCycleType for Historical Orders

The `LifeCycleType` field on OrderSummary controls which Order Management core actions are available:

- **`Managed`** — Standard active order lifecycle: supports fulfillment, cancel, refund, and change order core actions. Use for orders that are still being processed.
- **`Unmanaged`** — Historical order marker: disables fulfillment, cancel, refund, and change order core actions. Use for historical orders that are no longer being serviced. This is the correct value for order history migration.

Setting `LifeCycleType = Unmanaged` during OrderSummary creation prevents accidental refund or fulfillment actions from being triggered on historical data in Order Management.

### Why OrderSummary Requires ConnectAPI or Flow

OrderSummary is not a standard DML-insertable object in the same way as Order or OrderItem. It requires platform-managed creation through:
- **ConnectAPI (Apex):** `ConnectAPI.OrderSummary.createOrderSummary(orderSummaryInput)` where `orderSummaryInput` is a `ConnectAPI.OrderSummaryInputRepresentation`
- **Flow Core Action:** "Create Order Summary" standard core action in Flow Builder

This design ensures Order Management's internal state machine is correctly initialized for the new summary record. Bypassing ConnectAPI by inserting directly to the OrderSummary object either fails or creates a malformed record that breaks Order Management reports and actions.

---

## Common Patterns

### Pattern 1: Full Historical Order Migration with Unmanaged OrderSummary

**When to use:** Migrating closed or completed historical orders from a legacy system where no further fulfillment, refund, or cancellation actions are needed.

**How it works:**
1. Insert Order records (Status = Draft, OrderedDate = historical date) via Bulk API
2. Insert OrderDeliveryGroup records referencing each Order ID
3. Insert OrderItem records referencing Order and OrderDeliveryGroup IDs
4. Activate each Order: update Status from Draft to Activated via Bulk API update
5. Create OrderSummary for each Order via ConnectAPI or Flow core action with `LifeCycleType = Unmanaged`
6. Validate: confirm OrderSummary exists for each Order, confirm LifeCycleType = Unmanaged

**Why not Bulk API to OrderSummary:** OrderSummary requires ConnectAPI because the platform must initialize internal state, calculate summary totals, and set up the Order Management state machine. Direct DML bypasses this initialization.

### Pattern 2: Batched OrderSummary Creation via Apex

**When to use:** Large volume historical order migration where manual Flow processing is impractical.

**How it works:**
```apex
// Called in a Batch Apex job after Orders are activated
ConnectAPI.OrderSummaryInputRepresentation input = new ConnectAPI.OrderSummaryInputRepresentation();
input.orderId = orderId;
input.orderLifeCycleType = 'UNMANAGED';
ConnectAPI.OrderSummary.createOrderSummary(input);
```

Run this in a Batch Apex class that queries activated Orders without existing OrderSummary records and processes them in chunks of 200 per execute() invocation to respect governor limits.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Historical closed orders, no future actions needed | LifeCycleType = Unmanaged | Disables refund/cancel/fulfillment core actions on historical records |
| Active orders still in fulfillment | LifeCycleType = Managed | Enables standard Order Management action menu |
| OrderSummary creation | ConnectAPI or Flow core action | Cannot be created via direct DML or Bulk API |
| Large volume (>10,000 orders) | Batch Apex calling ConnectAPI | Flow core action has lower throughput than Apex batch |
| CPQ legacy order migration | Use CPQ-specific data migration skill | SBQQ objects and contract migration require different tooling |

---

## Recommended Workflow

1. **Confirm target org has Order Management enabled** — Check Setup > Order Settings and confirm OrderSummary object is visible in Object Manager.
2. **Load Order records in Draft status** — Insert Order records via Bulk API. Set `Status = Draft` and `OrderedDate` to the historical date. Do not activate yet.
3. **Load OrderDeliveryGroup records** — Insert one or more delivery groups per Order, referencing the Order ID.
4. **Load OrderItem records** — Insert line items referencing both Order ID and OrderDeliveryGroup ID.
5. **Activate Orders** — Update Order Status from Draft to Activated via Bulk API update. Only activated Orders can have OrderSummary records.
6. **Create OrderSummary via ConnectAPI or Flow** — For each activated Order without an existing OrderSummary, call `ConnectAPI.OrderSummary.createOrderSummary()` with `LifeCycleType = UNMANAGED` (for historical orders).
7. **Validate** — Run SOQL: `SELECT Id, LifeCycleType FROM OrderSummary WHERE OrderId IN :migratedOrderIds`. Confirm all Orders have a corresponding OrderSummary with the correct LifeCycleType.

---

## Review Checklist

- [ ] Order created in Draft status before OrderDeliveryGroup and OrderItem are inserted
- [ ] Order activated before OrderSummary creation attempt
- [ ] OrderSummary created via ConnectAPI or Flow core action — not via direct DML or Bulk API
- [ ] LifeCycleType = Unmanaged set for historical orders
- [ ] SOQL validation confirms OrderSummary exists for every migrated Order
- [ ] No fulfillment or refund actions triggered on historical OrderSummary records post-migration

---

## Salesforce-Specific Gotchas

1. **OrderSummary direct DML insert fails silently in some API versions** — Depending on the API version, a direct DML insert to OrderSummary either raises an error or silently creates a malformed record. Either outcome breaks Order Management functionality. Always use ConnectAPI or Flow core action.
2. **Order must be Activated before OrderSummary can be created** — Attempting to call `ConnectAPI.OrderSummary.createOrderSummary()` for an Order that is still in Draft status raises a `FIELD_INTEGRITY_EXCEPTION`. Activate Orders first, then create summaries.
3. **LifeCycleType cannot be changed after OrderSummary creation** — The `LifeCycleType` field is set at creation time and is immutable. Setting the wrong type during migration requires deleting and recreating the OrderSummary record, which also deletes all Order Management state associated with it.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Load sequence plan | Ordered list of objects to insert with dependency documentation |
| ConnectAPI OrderSummary creation Apex class | Batch Apex for bulk OrderSummary creation with Unmanaged lifecycle |
| Validation SOQL set | Queries to confirm OrderSummary count, LifeCycleType, and order-summary linkage |

---

## Related Skills

- `data/product-catalog-migration-commerce` — For migrating B2B Commerce product catalog data
- `devops/cpq-deployment-patterns` — For CPQ-specific order and billing configuration deployment
- `apex/commerce-order-api` — For Apex-level Order Management API integration patterns
