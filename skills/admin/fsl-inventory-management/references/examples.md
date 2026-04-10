# Examples — FSL Inventory Management

## Example 1: Technician Van Stock Setup and Parts Consumption on a Work Order

**Scenario:** A utilities company deploys field technicians who carry a standard set of parts in their vans. After completing a meter replacement work order, technicians must log the parts used so inventory counts stay accurate.

**Problem:** After the FSL rollout, technicians log into the mobile app but see no inventory. Dispatchers are also confused because QuantityOnHand on ProductItems never changes even though technicians claim they are using parts.

**Root Cause / Solution:**

Two separate issues:

1. **Van locations were not marked as Mobile Location.** Each technician's van has a Location record, but `IsMobile` was left as `false`. The FSL mobile app only displays locations where `IsMobile = true`. Fix: navigate to each van Location record and enable the Mobile Location checkbox.

2. **Parts were being logged by editing QuantityOnHand directly** via a custom Flow the admin built, instead of creating ProductConsumed records. Direct edits to QuantityOnHand are unsupported and do not create ProductItemTransaction audit records.

Correct workflow:
- After work is done, the technician (or dispatcher) creates a ProductConsumed record on the Work Order related list.
- Fields required: `WorkOrderId`, `Product2Id`, `QuantityConsumed`, `SourceProductItemId` (the van's ProductItem for that product).
- On save, the platform decrements `QuantityOnHand` on the van ProductItem and creates a ProductItemTransaction audit record automatically.

**Why it matters:** Correct ProductConsumed records enable job-level parts cost reporting (cost per work order), allow dispatchers to see when van stock is running low, and keep the inventory ledger accurate for replenishment planning. Bypassing this with direct QuantityOnHand edits produces a ledger that cannot be audited or reconciled.

---

## Example 2: Van Replenishment — ProductRequest to ProductTransfer to Received

**Scenario:** A telecom field service org runs 50 technician vans. Each van carries cable connectors, splitters, and power supplies. When a technician's on-hand count drops below threshold, a replenishment order is needed from the central warehouse.

**Problem:** An admin built a nightly batch job that directly updates QuantityOnHand on the van ProductItems to "top them back up" without creating any ProductTransfer records. After three months, ProductItemTransaction records do not match the displayed counts and auditors are flagging the discrepancy. Attempts to reconcile manually by deleting and re-creating ProductItemTransaction records have made things worse.

**Root Cause / Solution:**

Direct QuantityOnHand updates bypassed the platform's ledger mechanism. Deleting ProductItemTransaction records then corrupted the audit trail further — these records are auto-generated and must never be manually deleted.

Correct replenishment workflow:

1. Create a **ProductRequest** with `DestinationLocationId = van Location`, `RequestedDate`, and any relevant notes.
2. Create one **ProductRequestLineItem** per product: `Product2Id`, `QuantityRequested`, `SourceLocationId = warehouse Location`.
3. Warehouse fulfills by creating a **ProductTransfer**: `SourceLocationId = warehouse`, `DestinationLocationId = van`, `QuantitySent = fulfillment qty`, linked to the ProductRequestLineItem via `ProductRequestLineItemId`.
4. When stock arrives at the van, set the ProductTransfer status to **Received**.
5. Platform decrements warehouse ProductItem `QuantityOnHand` and increments van ProductItem `QuantityOnHand`. Two new ProductItemTransaction records are auto-created.

**Why it matters:** The ProductRequest → ProductTransfer → Received chain is the only supported way to move stock between locations. It maintains a fully auditable ledger, associates movement to the originating request for tracking, and correctly fires QuantityOnHand updates at the right moment (Received, not creation).

---

## Example 3: Diagnosing a QuantityOnHand Discrepancy Using ProductItemTransaction

**Scenario:** A ProductItem for "Cable Splice Kit" at the downtown depot shows `QuantityOnHand = 3`, but a physical count shows 17 units on the shelf. Management suspects data integrity issues.

**Problem:** Unknown — could be unconsumed ProductConsumed records, transfers never marked Received, or direct QuantityOnHand edits from a legacy integration.

**Investigation Approach:**

Query ProductItemTransaction records for the ProductItem:

```soql
SELECT Id, TransactionType, Quantity, CreatedDate, CreatedById
FROM ProductItemTransaction
WHERE ProductItemId = '<ProductItemId>'
ORDER BY CreatedDate ASC
```

Walk the transaction log from the opening balance forward:
- Each `TransactionType` of `Consumed` should correspond to a ProductConsumed record on a Work Order.
- Each `TransactionType` of `Transferred Out` or `Transferred In` corresponds to a ProductTransfer marked Received.
- If the running sum of transactions equals 3 but the physical count is 17, the discrepancy is either: (a) transfers that exist but were never marked Received, or (b) a legacy system that incremented QuantityOnHand directly without creating a ProductTransfer.

**Resolution:** Create a corrective ProductTransfer from a dedicated "Inventory Adjustment" location to the depot, quantity = 14 (the discrepancy), and mark it Received immediately. This brings QuantityOnHand to 17 and creates a documented adjustment entry in the ProductItemTransaction log.

**Why it matters:** ProductItemTransaction is the tamper-evident ledger for all inventory changes. Diagnosing discrepancies by walking the transaction log is the correct approach before considering any data correction — deleting or hand-editing transaction records makes recovery impossible.

---

## Anti-Pattern: Treating ProductTransfer Creation as Stock Movement

**What practitioners do:** Create a ProductTransfer record and assume QuantityOnHand has immediately updated, then mark the work order complete and close the replenishment request.

**What goes wrong:** QuantityOnHand does not change when a ProductTransfer is created — only when it is set to Received. If the "Received" step is skipped or not operationally enforced, on-hand counts never decrement at the source or increment at the destination. The inventory ledger perpetually overstates source stock and understates destination stock, making replenishment thresholds and dispatch planning inaccurate.

**Correct approach:** Build operational discipline (and optionally a Flow reminder or validation rule) to ensure every ProductTransfer is explicitly moved to Received status when the physical stock arrives at the destination. Never rely on transfer creation alone as a proxy for stock movement.
