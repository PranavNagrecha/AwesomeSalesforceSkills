# Gotchas — Commerce Order Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: OrderLifeCycleType Is Immutable After OrderSummary Creation

**What happens:** Setting `OrderLifeCycleType` to MANAGED on an OrderSummary record is permanent. No standard API or admin tool allows changing it after the record is created. If a team sets MANAGED and later discovers their implementation requires direct DML (e.g., a legacy batch job that updates quantities), the OrderSummary must be deleted and recreated, which orphans all downstream financial and fulfillment records.

**When it occurs:** During initial OMS implementation when the lifecycle type is set without fully understanding the Connect API requirement. Also surfaces during post-go-live integrations where an external system tries to push data directly to OrderItemSummary via bulk upsert.

**How to avoid:** Treat OrderLifeCycleType as an architectural decision, not a field value. Document the choice in the solution design before any Order activation. If there is genuine uncertainty, test in a full-copy sandbox with realistic data volumes before deploying. For mixed scenarios (some orders MANAGED, some not), use a custom field on the Order to drive a Flow that sets the correct type during OrderSummary creation.

---

## Gotcha 2: Direct DML on OrderItemSummary in MANAGED Mode Corrupts Aggregates Silently

**What happens:** Apex DML that updates OrderItemSummary fields such as `QuantityCanceled`, `TotalLineAmount`, or `TotalAdjustedLineAmount` in a MANAGED-lifecycle OrderSummary can succeed at the DML layer in some API versions but leaves the parent OrderSummary aggregate fields (TotalCancelled, GrandTotalAmount, TotalAdjustedProductAmount) inconsistent. There is no immediate visible error; the corruption is only discovered when invoices or reports show wrong totals. In API v55+ the platform throws `FIELD_INTEGRITY_EXCEPTION` before the DML completes, which is a breaking change for integrations built on earlier versions.

**When it occurs:** Batch migration jobs, external system integrations, or hand-rolled cancellation Apex that bypasses the Connect API. Often introduced when a team migrates from a non-OMS order management setup and carries over the old DML patterns.

**How to avoid:** Use only the Connect API actions for all mutations on MANAGED OrderSummaries: `submit-cancel`, `submit-return`, and `adjust-item-submit`. Never write DML targeting OrderItemSummary, OrderItemAdjustmentLineSummary, or OrderItemTaxLineItemSummary in MANAGED mode. Add a pre-deploy check that flags any Apex class or trigger containing DML on these objects.

---

## Gotcha 3: ProcessExceptionEvent Is the Only Error Surface for Async Payment Jobs

**What happens:** `ensure-funds-async` and `ensure-refunds-async` are enqueued as Queueable Apex jobs. They do not throw exceptions back to the calling context, do not write to standard Apex debug logs, and do not set a visible error state on the OrderSummary. If the payment gateway returns an authorization failure and no `ProcessExceptionEvent` subscriber exists, the failure is invisible. The order appears to be in a valid state but payment was never captured or the refund was never issued.

**When it occurs:** During initial OMS setup when the team focuses on the "happy path" and defers error handling. Also surfaces after a gateway credential rotation where gateway calls start failing silently.

**How to avoid:** Deploy a `ProcessExceptionEvent` subscriber (triggered Flow or Apex trigger) before enabling any `ensure-funds-async` or `ensure-refunds-async` calls in production. The subscriber should log the exception, create a case or task for operations review, and update the OrderSummary or FulfillmentOrder status to reflect the payment failure. Test the subscriber by intentionally triggering a gateway failure in sandbox.

---

## Gotcha 4: adjust-item-submit Produces Up to Three Separate ChangeOrders

**What happens:** When `adjust-item-submit` is called on an OrderItemSummary where some quantity is pre-fulfillment, some is in-fulfillment, and some is post-fulfillment, the OMS platform creates a separate ChangeOrder for each fulfillment-status segment. Code that queries for ChangeOrders after calling `adjust-item-submit` and expects exactly one record will miss the additional records. Reporting or invoice generation logic that sums ChangeOrder amounts can double-count if it does not account for multiple records per adjustment call.

**When it occurs:** Adjustments on partially fulfilled orders — common in split shipment scenarios where an order has multiple FulfillmentOrders in different statuses.

**How to avoid:** After calling `adjust-item-submit`, query ChangeOrders by `OriginalOrderId` and `OrderSummaryId` and aggregate all records created within the same transaction or within a short time window. Do not assume a 1:1 relationship between an `adjust-item-submit` call and a ChangeOrder record. The Connect API response body includes the IDs of all ChangeOrders created.

---

## Gotcha 5: CPQ Orders Do Not Trigger OrderSummary Creation

**What happens:** Orders generated from Salesforce CPQ quotes are standard Salesforce Order records but the OMS platform trigger that creates the OrderSummary does not fire for them. Activating a CPQ-generated Order will NOT create an OrderSummary, even in an org with a valid OMS license. Teams that activate a CPQ Order and then look for an OrderSummary will find nothing.

**When it occurs:** Any project that attempts to connect a CPQ quoting process directly to an OMS fulfillment process without a custom integration layer.

**How to avoid:** Treat CPQ → OMS as an integration problem, not a native flow. The standard path is to create a separate Order (or convert the CPQ Order through a custom mapping) in the OMS-compatible format and activate that record. Document the scope boundary explicitly: CPQ order management ends at Order activation; OMS order management begins with OrderSummary creation from a non-CPQ Order.
