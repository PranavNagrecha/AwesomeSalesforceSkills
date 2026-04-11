# Commerce Order Management — Work Template

Use this template when working on any OMS task: order lifecycle, fulfillment routing, cancellations, returns, payment jobs, or platform event wiring.

## Scope

**Skill:** `commerce-order-management`

**Request summary:** (fill in what the user asked for)

## Prerequisites Confirmed

Before starting, verify all of the following:

- [ ] Org has Salesforce Order Management or Commerce license provisioned
- [ ] Order is in `Activated` status (or we are configuring the activation trigger)
- [ ] `OrderLifeCycleType` decision documented: MANAGED / UNMANAGED (circle one — this is immutable after creation)
- [ ] Payment gateway configured (if ensure-funds or ensure-refunds is in scope)
- [ ] Confirmed this is NOT a CPQ order (CPQ orders do not create OrderSummary records)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md:

- OMS license status:
- OrderLifeCycleType chosen and reason:
- Upstream Order activation mechanism (Flow / Process / API / Checkout):
- Fulfillment location(s) involved:
- Payment gateway or method in use:
- Known constraints or limits:

## Task Type

Which category does this work fall into? (check one)

- [ ] OrderSummary creation / lifecycle setup
- [ ] FulfillmentOrder routing and status handling
- [ ] Cancellation (pre-fulfillment) via submit-cancel
- [ ] Return (post-fulfillment) via submit-return + ReturnOrder
- [ ] Price / quantity adjustment via adjust-item-submit
- [ ] Payment job wiring (ensure-funds-async / ensure-refunds-async)
- [ ] Platform event subscription (OrderSummaryCreatedEvent / FOStatusChangedEvent / OrderSumStatusChangedEvent / ProcessExceptionEvent)
- [ ] Debugging / investigation

## Approach

Which pattern from SKILL.md applies?

- [ ] Standard Fulfillment Flow (OrderSummaryCreatedEvent → routing → FulfillmentOrder)
- [ ] Cancellation and Return Flow (submit-cancel / submit-return)
- [ ] Custom approach — describe below:

Reason for pattern choice:

## Connect API Actions Used

List every Connect API action this implementation calls:

| Action | Purpose | Sync or Async |
|---|---|---|
| submit-cancel | Pre-fulfillment item cancellation | Synchronous |
| submit-return | Post-fulfillment return initiation | Synchronous |
| adjust-item-submit | Quantity or price adjustment | Synchronous (up to 3 ChangeOrders) |
| ensure-funds-async | Payment authorization / capture | Async — subscribe to ProcessExceptionEvent |
| ensure-refunds-async | Refund issuance | Async — subscribe to ProcessExceptionEvent |

(Delete rows not applicable to this task)

## Platform Events Subscribed

| Event | Handler (Flow / Apex) | Purpose |
|---|---|---|
| OrderSummaryCreatedEvent | | |
| FOStatusChangedEvent | | |
| OrderSumStatusChangedEvent | | |
| ProcessExceptionEvent | | Error handling for async payment jobs |

## Checklist

- [ ] OrderLifeCycleType confirmed and documented before OrderSummary creation
- [ ] No direct DML on OrderItemSummary, OrderItemAdjustmentLineSummary, or OrderItemTaxLineItemSummary in MANAGED mode
- [ ] All mutations use the correct Connect API action for the fulfillment status of the item
- [ ] ProcessExceptionEvent subscriber deployed before enabling ensure-funds-async or ensure-refunds-async
- [ ] FulfillmentOrder routing handles all OrderDeliveryGroupSummary records
- [ ] adjust-item-submit result processed as a list of ChangeOrders (up to 3), not a single record
- [ ] CPQ order scope boundary documented if CPQ is in the ecosystem
- [ ] Tested in sandbox end-to-end: Order activation → OrderSummary → FulfillmentOrder → status events

## Notes

Record any deviations from the standard pattern and why:
