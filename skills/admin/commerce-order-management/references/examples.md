# Examples — Commerce Order Management

## Example 1: Standard Fulfillment — Order Activation to FulfillmentOrder Creation

**Context:** An e-commerce storefront completes a checkout. The resulting Salesforce Order is activated. The OMS implementation must create an OrderSummary and route items to the correct fulfillment location.

**Problem:** Without explicit platform event handling, the team tried to create FulfillmentOrder records via a Flow that polled the Order object. The polling introduced race conditions and the FulfillmentOrder sometimes referenced the wrong delivery group, causing incorrect address labels.

**Solution:**

Subscribe to `OrderSummaryCreatedEvent` in a record-triggered or event-triggered Flow. When the event fires, retrieve the OrderSummary and its OrderDeliveryGroupSummary children, then invoke the OMS routing engine via a Connect API action or a custom Apex class:

```apex
// Apex trigger handler — subscribes to OrderSummaryCreatedEvent
// Registered via Platform Event Trigger in Setup or deployed as Apex trigger on the event

trigger OrderSummaryCreatedHandler on OrderSummaryCreatedEvent (after insert) {
    List<Id> summaryIds = new List<Id>();
    for (OrderSummaryCreatedEvent evt : Trigger.new) {
        summaryIds.add(evt.OrderSummaryId);
    }
    // Enqueue routing logic to avoid governor limit issues in trigger context
    System.enqueueJob(new FulfillmentOrderRoutingQueueable(summaryIds));
}

public class FulfillmentOrderRoutingQueueable implements Queueable {
    private List<Id> summaryIds;

    public FulfillmentOrderRoutingQueueable(List<Id> ids) {
        this.summaryIds = ids;
    }

    public void execute(QueueableContext ctx) {
        for (Id summaryId : summaryIds) {
            // Retrieve delivery groups for this OrderSummary
            List<OrderDeliveryGroupSummary> groups = [
                SELECT Id, DeliverToName, DeliverToStreet, DeliverToCity
                FROM OrderDeliveryGroupSummary
                WHERE OrderSummaryId = :summaryId
            ];

            // Create one FulfillmentOrder per delivery group
            // (real routing selects location based on inventory and proximity)
            for (OrderDeliveryGroupSummary grp : groups) {
                FulfillmentOrder fo = new FulfillmentOrder();
                fo.OrderSummaryId = summaryId;
                fo.OrderDeliveryGroupSummaryId = grp.Id;
                fo.FulfilledFromLocationId = WarehouseLocationSelector.selectFor(grp);
                fo.Status = 'Draft';
                fo.Type = 'Warehouse';
                insert fo;
            }
        }
    }
}
```

**Why it works:** Using `OrderSummaryCreatedEvent` removes polling, eliminates the race condition, and ensures the FulfillmentOrder is created only after the OrderSummary is fully persisted. Enqueueing the routing work keeps the trigger context clean.

---

## Example 2: Customer Cancellation Before Fulfillment (Pre-Fulfillment Cancel)

**Context:** A customer contacts support within 10 minutes of placing an order and wants to cancel one of two line items. The OrderSummary OrderLifeCycleType is MANAGED.

**Problem:** A developer attempted to set `QuantityCanceled` on the OrderItemSummary directly via DML. The DML succeeded in a sandbox but the OrderSummary `TotalCancelled` and `GrandTotalAmount` fields were not updated, causing the invoice total to remain incorrect. In production a later API version began throwing `FIELD_INTEGRITY_EXCEPTION` for the same DML.

**Solution:**

Use the `submit-cancel` Connect API action. In Apex, call `ConnectApi.OrderSummaryInputRepresentation` or invoke the REST endpoint:

```apex
// Apex — using ConnectApi to cancel one OrderItemSummary quantity in MANAGED mode
public static ConnectApi.OrderSummaryActionOutput cancelOrderItem(
    Id orderSummaryId,
    Id orderItemSummaryId,
    Decimal quantityToCancel
) {
    ConnectApi.CancelOrderItemSummaryInputRepresentation input =
        new ConnectApi.CancelOrderItemSummaryInputRepresentation();
    input.orderItemSummaryId = orderItemSummaryId;
    input.quantity = quantityToCancel;

    ConnectApi.CancelOrderInputRepresentation cancelInput =
        new ConnectApi.CancelOrderInputRepresentation();
    cancelInput.orderSummaryId = orderSummaryId;
    cancelInput.orderItemSummaryInputs = new List<ConnectApi.CancelOrderItemSummaryInputRepresentation>{ input };

    // submit-cancel creates a ChangeOrder and updates OrderItemSummary aggregates
    ConnectApi.OrderSummaryActionOutput result =
        ConnectApi.OrderSummaryAction.submitCancel(cancelInput);

    return result;
}
```

After the ChangeOrder is created, invoke `ensure-refunds-async` to issue the refund:

```apex
// Trigger ensure-refunds-async after cancel
ConnectApi.EnsureRefundsAsyncInputRepresentation refundInput =
    new ConnectApi.EnsureRefundsAsyncInputRepresentation();
refundInput.orderSummaryId = orderSummaryId;
ConnectApi.OrderSummaryAction.ensureRefundsAsync(refundInput);
// Subscribe to ProcessExceptionEvent to catch refund job failures
```

**Why it works:** `submit-cancel` is the only supported mutation path in MANAGED mode. It atomically updates the OrderItemSummary aggregate fields and creates an auditable ChangeOrder record. The Connect API enforces eligibility checks (e.g., prevents cancelling already-fulfilled quantities).

---

## Example 3: Post-Fulfillment Return Flow

**Context:** A customer received a shipped item and wants to return it. The FulfillmentOrder is in Fulfilled status.

**Problem:** The team used `submit-cancel` to handle the return, thinking it was the general-purpose reversal action. This failed with an API error because `submit-cancel` only operates on unfulfilled quantities. ReturnOrder records were never created, breaking the warehouse receiving workflow.

**Solution:**

Use `submit-return` for post-fulfillment returns. This creates a ReturnOrder and associated ReturnOrderLineItem records:

```apex
public static void initiateReturn(Id orderSummaryId, Id orderItemSummaryId, Decimal qty) {
    ConnectApi.ReturnOrderItemSummaryInputRepresentation itemInput =
        new ConnectApi.ReturnOrderItemSummaryInputRepresentation();
    itemInput.orderItemSummaryId = orderItemSummaryId;
    itemInput.quantity = qty;
    itemInput.returnReason = 'DefectiveProduct';

    ConnectApi.ReturnOrderInputRepresentation returnInput =
        new ConnectApi.ReturnOrderInputRepresentation();
    returnInput.orderSummaryId = orderSummaryId;
    returnInput.orderItemSummaryInputs =
        new List<ConnectApi.ReturnOrderItemSummaryInputRepresentation>{ itemInput };

    // Creates ReturnOrder + ReturnOrderLineItem
    ConnectApi.ReturnOrderActionOutput result =
        ConnectApi.OrderSummaryAction.submitReturn(returnInput);

    // After warehouse receives the item and ReturnOrderLineItem is processed:
    // call ensure-refunds-async with the ReturnOrder ID
}
```

**Why it works:** `submit-return` is distinct from `submit-cancel`. It targets fulfilled quantities and creates the ReturnOrder records needed for warehouse receiving, inventory crediting, and refund processing. `submit-cancel` would fail because the items are already fulfilled.

---

## Anti-Pattern: Direct DML on OrderItemSummary in MANAGED Mode

**What practitioners do:** Write an Apex batch or trigger that updates `OrderItemSummary.QuantityCanceled` or `OrderItemSummary.TotalLineAmount` directly to reflect a cancellation or price correction.

**What goes wrong:** In MANAGED mode, direct DML on OrderItemSummary bypasses the OMS state machine. In some API versions it succeeds at the DML level but leaves OrderSummary aggregate fields (TotalCancelled, GrandTotalAmount, TotalAdjustedProductAmount) in an inconsistent state. In later API versions (v55+) it throws `FIELD_INTEGRITY_EXCEPTION`. Inconsistent aggregates cannot be corrected without Salesforce Support intervention and can cause invoicing errors, incorrect refund amounts, and inaccurate reporting.

**Correct approach:** Always use the appropriate Connect API action for MANAGED mode OrderSummaries:
- Pre-fulfillment quantity reduction → `submit-cancel`
- Post-fulfillment return → `submit-return`
- Price or quantity adjustment → `adjust-item-submit`
