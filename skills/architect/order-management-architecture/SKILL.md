---
name: order-management-architecture
description: "Use when designing or reviewing a Salesforce Order Management (OMS) solution architecture: fulfillment workflow strategy, split-order routing design, Omnichannel Inventory (OCI) integration, returns process architecture, and multi-location inventory management decisions. Trigger keywords: OMS architecture, split orders, fulfillment routing, OCI, order routing strategy, returns architecture, fulfillment location design. NOT for individual order setup or day-to-day OMS administration (use admin/commerce-order-management), NOT for storefront or checkout flow design, NOT for CPQ quote-to-order workflows."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Operational Excellence
triggers:
  - "How should I architect split-order routing across multiple fulfillment locations using OMS?"
  - "We need to integrate Omnichannel Inventory with Order Management — what does the architecture look like?"
  - "Design an OMS returns architecture that decouples return processing from refund issuance"
  - "What is the difference between Connected Commerce Order Routing and Growth Order Routing?"
  - "How do I architect OMS to minimize shipment splits while handling inventory consistency issues?"
tags:
  - OMS
  - order-management
  - fulfillment
  - OCI
  - split-orders
  - returns
  - omnichannel-inventory
  - order-routing
inputs:
  - "Commerce variant: B2B only, B2C only, or both"
  - "Number of fulfillment locations and warehouse configuration"
  - "Whether Omnichannel Inventory (OCI) is provisioned or planned"
  - "Expected order volume and split-order frequency"
  - "Returns and refund policy requirements"
  - "Inventory consistency requirements (real-time vs. eventually consistent acceptable)"
outputs:
  - "OMS architecture decision record with routing variant selection rationale"
  - "Split-order routing design including OCI wiring requirements"
  - "Returns and refund decoupling architecture"
  - "Fulfillment location topology with inventory signal strategy"
  - "Review checklist for OMS go-live readiness"
dependencies:
  - admin/commerce-order-management
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Order Management Architecture

Use this skill when you are designing or reviewing the architecture of a Salesforce Order Management (OMS) implementation: how fulfillment workflows are structured, how split-order routing is configured, how Omnichannel Inventory (OCI) connects as the inventory truth layer, and how returns and refund flows are decoupled. The focus is holistic architecture — how routing variants, inventory signals, and the returns lifecycle interact as a system rather than how individual records are created.

---

## Before Starting

Gather this context before working on anything in this domain:

- **OMS license and routing variant** — Confirm which routing variant is provisioned: Connected Commerce Order Routing (B2B only) or Growth Order Routing (B2B + B2C). These are not interchangeable and the choice must be made before designing routing flows.
- **OCI provisioning status** — Omnichannel Inventory is the real-time inventory signal for OMS routing. If OCI is not provisioned, OMS has no live inventory data and all orders route to a single default location regardless of how routing flows are configured. This is the most common architecture gap.
- **Number of fulfillment locations** — Get the concrete count of warehouses, stores, and 3PL locations. Split-order architecture complexity scales with location count. Routing flows that work for 3 locations fail operationally at 30 if not designed for it.

---

## Core Concepts

### OMS Object Chain and Routing Unit

The canonical OMS object chain determines where routing decisions are made:

```
Order (Activated)
  └── OrderSummary
        ├── OrderItemSummary (one per OrderItem)
        └── OrderDeliveryGroupSummary (groups items by shipping address/method)
              └── FulfillmentOrder  ← routing assigns each ODGS to a location
                    └── FulfillmentOrderLineItem
ReturnOrder
  └── ReturnOrderLineItem
```

Each `OrderDeliveryGroupSummary` (ODGS) is the unit of fulfillment routing. The routing engine assigns each ODGS to one `FulfillmentOrder` per fulfillment location. A single customer order with one delivery group fulfilled from one location produces one FulfillmentOrder. A split order with one delivery group fulfilled from two locations produces two FulfillmentOrders for that group. Architects must design routing logic at the ODGS level, not at the order level.

### Split-Order Routing and the "Fewest Splits" Algorithm

OMS includes the `Find Routes with Fewest Splits` Flow action, which implements an iterative minimization algorithm:

1. First pass: test every single fulfillment location to find locations that can fulfill the entire ODGS without splitting.
2. Second pass: if no single location can fulfill everything, test pairs of locations to find the combination that minimizes the number of shipments.
3. The algorithm continues expanding the search until a valid routing set is found or no routing is possible.

This algorithm is a Flow action — it does not execute automatically. Architects must wire it into an orchestrating Flow or Apex process that is triggered by OrderSummary creation or by a manual routing request. If the wiring is absent, OMS does not route; it simply creates unassigned FulfillmentOrders.

### Omnichannel Inventory as the Inventory Truth Layer

Omnichannel Inventory (OCI) is a separate provisioned capability that exposes real-time inventory availability across locations via API. OMS routing consults OCI availability data when selecting which fulfillment location(s) can satisfy an ODGS. Key architectural properties:

- **OCI availability is eventually consistent.** Inventory reservation happens at order placement, but the counts returned by OCI availability queries may reflect slightly stale data (seconds to low minutes in typical conditions). Routing decisions can therefore act on a count that another concurrent order has already reduced. Architects must design routing to treat OCI availability as a signal, not a guarantee, and implement retry or fallback logic for reservation failures.
- **OCI reservation decouples availability query from fulfillment commitment.** OCI reserves the quantity when the order is placed, before routing completes. The routing algorithm then assigns those reserved units to a location. If routing fails (e.g., no location can fulfill), the reservation must be explicitly released.
- **Without OCI, routing has no inventory signal.** OMS cannot query a warehouse management system or ERP inventory on its own. If OCI is not provisioned, the routing flow has no data on which to base location selection and defaults to a single configured location.

### Returns Architecture and Refund Decoupling

The OMS returns lifecycle is deliberately decoupled into two independent stages:

1. **Return initiation**: The `submit-return` Connect API action creates `ReturnOrder` and `ReturnOrderLineItem` records. This marks items as pending return and updates OrderItemSummary quantities but does not issue a refund.
2. **Refund issuance**: The `ensure-refunds` job is a separate asynchronous payment job that runs only after the ReturnOrder has been explicitly progressed (e.g., to a `Received` or `Closed` status). The refund job does not fire automatically at return creation.

This decoupling is intentional — it allows warehouse teams to confirm physical receipt of returned goods before money moves. Architects who wire refund logic to fire immediately on return creation break the intended control flow and risk issuing refunds for goods that were never returned. The architecture must include a clear state machine for ReturnOrder status transitions and the trigger conditions for ensure-refunds invocation.

---

## Common Patterns

### OCI-Wired Fewest-Splits Routing

**When to use:** Any B2C or B2B org with two or more fulfillment locations and a requirement to minimize shipment splits (cost control, customer experience, or carrier SLA reasons).

**How it works:**
1. An OrderSummary Creation Flow or Platform Event subscriber triggers routing when a new OrderSummary reaches `Created` status.
2. The Flow calls `Find Routes with Fewest Splits`, passing the ODGS ID and an OCI availability query result for the relevant SKUs at each candidate location.
3. The action returns a ranked set of location assignments. The Flow creates FulfillmentOrders from the winning assignment.
4. If OCI reservation succeeds for all items, the FulfillmentOrders advance to `Allocated`. If reservation fails for any item, the Flow rolls back FulfillmentOrder creation and re-queues for retry.

**Why not the alternative:** Routing without the fewest-splits action defaults to first-available logic, which creates unnecessary split orders — increasing shipping cost and customer confusion. Routing without OCI wiring means the "fewest splits" calculation has no real inventory data and will assign locations that cannot actually fulfill.

### Returns State Machine with Deferred Refund

**When to use:** Any OMS implementation with customer returns, regardless of whether returns are self-service (storefront) or agent-initiated (Service Cloud).

**How it works:**
1. `submit-return` Connect API action creates ReturnOrder with status `Draft` or `Submitted`.
2. A warehouse process (manual or via Flows on ReturnOrder status) transitions the ReturnOrder through `In Transit` → `Received` when goods arrive.
3. A quality check step (optional) transitions to `Closed`.
4. The `ensure-refunds` job is invoked only after the ReturnOrder reaches `Closed` (or whatever status the org defines as "refund eligible").
5. The refund job calls the payment gateway asynchronously. Results post back via Payment Gateway Log records.

**Why not the alternative:** Triggering ensure-refunds at return creation (step 1) issues refunds before goods are received. If the customer never returns the item, the merchant has already refunded. The deferred pattern also separates the customer-facing return confirmation email from the financial settlement, allowing different teams to own each step.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| B2B-only org with Order Management | Connected Commerce Order Routing | B2B-specific routing features; Growth routing adds B2C overhead not needed |
| B2C or mixed B2B+B2C org | Growth Order Routing | Only variant that supports B2C order routing natively |
| 2+ fulfillment locations with split-order requirement | OCI + Fewest Splits Flow action | OCI provides inventory signal; without it, fewest-splits has no data |
| OCI not provisioned, routing required | Single-location routing with manual override | Do not attempt multi-location routing without OCI; design for OCI as a future phase |
| Returns where refund timing is critical | Deferred ensure-refunds tied to ReturnOrder status transition | Prevents premature refund issuance; keeps financial and warehouse workflows separate |
| High-volume returns (1000+/day) | Batch invocation of ensure-refunds | Synchronous refund invocation at this volume will hit callout and CPU governor limits |
| Inventory reservation failures | Retry queue via Platform Event | OCI is eventually consistent; reservation failures are expected under load |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm routing variant and OCI provisioning** — Before designing anything, establish which routing variant is licensed (Connected Commerce or Growth) and whether OCI is provisioned. Document these as fixed constraints. Do not design a multi-location routing architecture without confirmed OCI provisioning.

2. **Map the fulfillment location topology** — List all fulfillment locations (warehouses, stores, 3PLs), their OCI location IDs, and the SKU populations each can fulfill. This topology is the input to the fewest-splits algorithm configuration and determines the search space for routing decisions.

3. **Design the routing trigger and orchestration Flow** — Define what event triggers routing (OrderSummary creation, manual agent action, or status change). Build the orchestrating Flow that calls `Find Routes with Fewest Splits`, handles OCI reservation results, and creates FulfillmentOrders from the winning assignment. Include a retry path for OCI reservation failures.

4. **Design the returns state machine** — Document the full ReturnOrder status lifecycle: what statuses exist, what transitions are allowed, which team owns each transition (storefront, warehouse, finance), and at which status the `ensure-refunds` job is invoked. Ensure the state machine is implemented as a Flow or Apex trigger on ReturnOrder — not as ad-hoc manual updates.

5. **Validate governor limit profiles** — Estimate the governor limit consumption for the routing transaction profile (OCI query + Flow invocation + FulfillmentOrder creation) at peak order volume. Confirm the profile stays within 50% of limits. For batch returns processing, estimate the ensure-refunds callout volume and verify it stays within the 100-callout-per-transaction limit.

6. **Review against Well-Architected pillars** — Walk the architecture through Reliability (what happens when OCI is slow or down?), Performance (routing latency at peak volume), and Adaptability (can new fulfillment locations be added without re-architecting the routing Flow?).

7. **Produce deliverables** — Generate the OMS architecture decision record, routing flow diagram, returns state machine diagram, and OCI integration topology. Validate all deliverables against the review checklist before sign-off.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Routing variant (Connected Commerce or Growth) is confirmed and documented
- [ ] OCI provisioning is confirmed before any multi-location routing design is approved
- [ ] Routing trigger and orchestration Flow are designed — fewest-splits action is wired, not assumed
- [ ] OCI reservation failure path (retry or fallback) is explicitly designed in the routing Flow
- [ ] Returns state machine is documented with explicit status transitions and team ownership per step
- [ ] `ensure-refunds` is wired to a ReturnOrder status transition, not to return creation
- [ ] Governor limit analysis covers routing transaction profile at peak order volume
- [ ] New fulfillment location onboarding process is documented — adding locations must not require Flow rebuild

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **OCI not provisioned = single-location fallback with no warning** — If OCI is not provisioned, the `Find Routes with Fewest Splits` Flow action has no inventory signal. It does not error; it silently routes all orders to the single configured default location. Architects who assume the routing Flow will "just work" without OCI will not see failures during testing (single-location orgs work fine) and will discover the gap in production when multi-location routing produces wrong assignments.

2. **OCI availability is eventually consistent — reservation failures are expected** — OCI availability queries return counts that may be seconds to low minutes stale under concurrent order load. Two orders for the same SKU can both see "5 in stock" simultaneously, but only one reservation will succeed. The architecture must treat reservation failure as a normal code path requiring retry or fallback, not as an error condition.

3. **Refund job does not fire until ReturnOrder is explicitly progressed** — The `ensure-refunds` job is decoupled from return creation by design. Calling `submit-return` does NOT trigger a refund. The refund job must be explicitly invoked after the ReturnOrder reaches the correct status. Orgs that do not implement the ReturnOrder status transition workflow will have returns stuck in `Submitted` with no refund ever issued.

4. **FulfillmentOrder creation is not automatic** — OMS does not create FulfillmentOrders on its own. An orchestrating Flow or Apex process must be built and wired to the OrderSummary creation event. If this wiring is absent, OrderSummary records will be created but no FulfillmentOrders will ever be generated and orders will never fulfill.

5. **OrderDeliveryGroupSummary is the routing unit, not the Order** — Architects who design routing logic at the Order level miss that a single Order can have multiple delivery groups (e.g., ship-to-home and pick-up-in-store items in the same order). Each ODGS routes independently. Routing logic that operates on the Order as a whole will produce incorrect FulfillmentOrder assignments for multi-delivery-group orders.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| OMS Architecture Decision Record | Documents routing variant selection, OCI integration approach, returns decoupling strategy, and key tradeoffs |
| Fulfillment Location Topology | Table of fulfillment locations, OCI location IDs, SKU populations, and routing priority weights |
| Routing Flow Design | Diagram of the orchestrating Flow: trigger event, OCI query, fewest-splits action, FulfillmentOrder creation, and failure retry path |
| Returns State Machine | State diagram of ReturnOrder status lifecycle with team ownership per transition and ensure-refunds trigger point |
| Governor Limit Analysis | Transaction profiles for routing and returns batch processing with limit consumption estimates at peak volume |

---

## Related Skills

- admin/commerce-order-management — Use for day-to-day OMS task implementation: creating OrderSummary records, building FulfillmentOrder routing flows, processing returns and cancellations
- architect/digital-storefront-requirements — Use when designing the upstream storefront that feeds orders into OMS
- architect/multi-store-architecture — Use when OMS must serve multiple storefronts or business units from a single org
