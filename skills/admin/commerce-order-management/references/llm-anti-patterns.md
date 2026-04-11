# LLM Anti-Patterns — Commerce Order Management

Common mistakes AI coding assistants make when generating or advising on Commerce Order Management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Direct DML on OrderItemSummary in MANAGED Mode

**What the LLM generates:**

```apex
// LLM-generated cancellation — WRONG for MANAGED lifecycle
OrderItemSummary ois = [SELECT Id, QuantityCanceled FROM OrderItemSummary WHERE Id = :itemId];
ois.QuantityCanceled += cancelQty;
update ois;
```

**Why it happens:** LLMs trained on general Salesforce Apex patterns default to the standard DML-update pattern for any SObject field. The MANAGED lifecycle constraint is a domain-specific OMS rule that is underrepresented in general Apex training corpora, so the model treats OrderItemSummary like any other standard object.

**Correct pattern:**

```apex
// Correct — use submit-cancel Connect API action in MANAGED mode
ConnectApi.CancelOrderItemSummaryInputRepresentation itemInput =
    new ConnectApi.CancelOrderItemSummaryInputRepresentation();
itemInput.orderItemSummaryId = itemId;
itemInput.quantity = cancelQty;

ConnectApi.CancelOrderInputRepresentation cancelInput =
    new ConnectApi.CancelOrderInputRepresentation();
cancelInput.orderSummaryId = orderSummaryId;
cancelInput.orderItemSummaryInputs =
    new List<ConnectApi.CancelOrderItemSummaryInputRepresentation>{ itemInput };

ConnectApi.OrderSummaryAction.submitCancel(cancelInput);
```

**Detection hint:** Flag any Apex containing `update ois` or `insert ois` where `ois` is typed as `OrderItemSummary`, or any DML statement targeting `OrderItemSummary`, `OrderItemAdjustmentLineSummary`, or `OrderItemTaxLineItemSummary` in a MANAGED-mode context.

---

## Anti-Pattern 2: Conflating submit-return With the Full ReturnOrder Path

**What the LLM generates:**

```
// LLM advice: "To process a return, call submit-return and the refund will be issued automatically."
```

Or code that calls `submit-return` and then immediately assumes the refund has been issued without calling `ensure-refunds-async`.

**Why it happens:** LLMs conflate the concept of "initiate return" with "complete refund" because in simpler systems these are one step. The OMS pattern separates return authorization (submit-return → ReturnOrder creation) from physical receipt (ReturnOrderLineItem processing) and financial settlement (ensure-refunds-async). The multi-step nature is not obvious from the action name alone.

**Correct pattern:**

```
Step 1: submit-return → Creates ReturnOrder and ReturnOrderLineItem records (authorization only)
Step 2: Warehouse receives item → ReturnOrderLineItem status updated to indicate receipt
Step 3: ensure-refunds-async → Enqueues the actual refund job to the payment gateway
Step 4: Subscribe to ProcessExceptionEvent → Handle refund job failures
```

**Detection hint:** Look for code that calls `submitReturn` without a subsequent call to `ensureRefundsAsync`, or advice that states "submit-return issues the refund."

---

## Anti-Pattern 3: Using submit-cancel for Post-Fulfillment Returns

**What the LLM generates:**

```apex
// LLM-generated: tries to cancel a fulfilled item — WRONG
ConnectApi.OrderSummaryAction.submitCancel(cancelInput); // item already fulfilled
```

**Why it happens:** LLMs associate "cancel" with any order reversal, including returns, because in many order systems cancellation and return are handled by the same endpoint. In OMS, `submit-cancel` only operates on quantities that have not yet entered fulfillment; calling it on fulfilled quantities returns an API error or silently skips the quantity.

**Correct pattern:**

```apex
// For post-fulfillment returns, use submit-return — NOT submit-cancel
ConnectApi.OrderSummaryAction.submitReturn(returnInput);
// submit-cancel is only valid for pre-fulfillment quantities
```

**Detection hint:** Flag any use of `submitCancel` where the FulfillmentOrder or OrderItemSummary is already in a fulfilled/shipped status. The correct action for fulfilled items is `submitReturn`.

---

## Anti-Pattern 4: Assuming ensure-funds-async Failures Are Surfaced as Exceptions

**What the LLM generates:**

```apex
try {
    ConnectApi.OrderSummaryAction.ensureFundsAsync(input);
} catch (Exception e) {
    // LLM assumes payment failure throws here — WRONG
    LogService.log('Payment failed: ' + e.getMessage());
}
```

**Why it happens:** LLMs default to try/catch for error handling in Apex because it is the universal pattern for synchronous operations. `ensure-funds-async` returns immediately after enqueueing the job; the try/catch block only catches errors in the enqueue step, not in the actual payment transaction. Gateway failures surface later via `ProcessExceptionEvent`.

**Correct pattern:**

```apex
// Calling ensure-funds-async — only catches enqueue errors, not payment failures
ConnectApi.OrderSummaryAction.ensureFundsAsync(input);
// Payment outcome is delivered asynchronously via ProcessExceptionEvent
// A separate platform event trigger or Flow must handle ProcessExceptionEvent
```

**Detection hint:** Any pattern that wraps `ensureFundsAsync` or `ensureRefundsAsync` in a try/catch and treats the catch block as the payment failure handler is incorrect. Look for missing `ProcessExceptionEvent` trigger or Flow in the deployment.

---

## Anti-Pattern 5: Assuming CPQ Orders Automatically Create OrderSummary Records

**What the LLM generates:**

```
// LLM advice: "Activate the CPQ order and the OrderSummary will be created automatically by OMS."
```

Or code that queries OrderSummary by a CPQ-generated Order ID and treats a null result as a timing issue rather than a structural one.

**Why it happens:** LLMs that know both CPQ and OMS extrapolate that "activating an order triggers OMS" applies universally. The distinction that CPQ Orders use a separate activation path that does not trigger the OMS OrderSummary creation flow is a platform-specific constraint that is frequently missed.

**Correct pattern:**

```
CPQ Orders: Quote → Order (CPQ activation path) → NO OrderSummary created
OMS Orders: Order (activated through OMS/Commerce path) → OrderSummary created

If CPQ orders must feed OMS:
- Build a custom integration that maps CPQ Order data to a new OMS-compatible Order
- Activate the OMS Order to trigger OrderSummary creation
- Document this as an explicit integration boundary
```

**Detection hint:** Any advice or code that implies CPQ-generated Orders will produce OrderSummary records without a custom integration layer is incorrect. Check whether the Order source is CPQ before applying OMS lifecycle guidance.

---

## Anti-Pattern 6: Expecting a Single ChangeOrder Per adjust-item-submit Call

**What the LLM generates:**

```apex
ConnectApi.OrderSummaryAction.adjustItemSubmit(adjustInput);
// LLM then queries for exactly one ChangeOrder
ChangeOrder co = [SELECT Id FROM ChangeOrder WHERE OrderSummaryId = :summaryId LIMIT 1];
processChangeOrder(co);
```

**Why it happens:** LLMs model a 1:1 action-to-result relationship by default. The OMS behavior of creating up to 3 ChangeOrders per `adjust-item-submit` call (one each for pre/in/post-fulfillment splits) is a non-obvious platform behavior that requires domain-specific knowledge to anticipate.

**Correct pattern:**

```apex
ConnectApi.AdjustOrderItemSummaryOutputRepresentation result =
    ConnectApi.OrderSummaryAction.adjustItemSubmit(adjustInput);

// The response includes IDs of all ChangeOrders created (up to 3)
List<Id> changeOrderIds = new List<Id>();
if (result.changeOrders != null) {
    for (ConnectApi.ChangeOrderOutputRepresentation co : result.changeOrders) {
        changeOrderIds.add(co.changeOrderId);
    }
}
// Process all ChangeOrders, not just the first
```

**Detection hint:** Look for `LIMIT 1` queries on ChangeOrder after an `adjustItemSubmit` call, or code that processes only `result.changeOrders[0]` without iterating the full list.
