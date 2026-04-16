# Gotchas — Commerce Order History Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: OrderSummary Cannot Be Created via Direct DML or Bulk API

OrderSummary requires `ConnectAPI.OrderSummary.createOrderSummary()` in Apex or the "Create Order Summary" Flow core action. Direct DML inserts via Bulk API or Data Loader either fail with an error or silently create malformed records that do not initialize Order Management state. The result is an OrderSummary record queryable via SOQL but broken in all Order Management reports and action menus.

**Fix:** Always use ConnectAPI or the Flow core action for OrderSummary creation. Never use insert DML statements or Bulk API for this object.

---

## Gotcha 2: LifeCycleType Is Immutable After OrderSummary Creation

The `LifeCycleType` field (Managed vs. Unmanaged) is set at creation time and cannot be updated. To correct a wrong LifeCycleType, the OrderSummary record must be deleted (along with all its OM child records) and recreated with the correct value via ConnectAPI. This is a costly correction in production.

**Fix:** Determine the correct LifeCycleType before running ConnectAPI. Historical orders = Unmanaged. Active orders = Managed. Validate the selection in a sandbox before production migration.

---

## Gotcha 3: Order Must Be Activated Before OrderSummary Creation

Calling ConnectAPI for an Order in Draft status raises `FIELD_INTEGRITY_EXCEPTION`. The load sequence must include an explicit Order activation step (update Status Draft → Activated) before running the ConnectAPI batch.

**Fix:** After inserting all Order, OrderDeliveryGroup, and OrderItem records, run a Bulk API status update. Confirm activation via SOQL before proceeding to OrderSummary creation.

---

## Gotcha 4: Conflating Salesforce Order Management with B2C Commerce Cloud Legacy Orders

Salesforce Order Management uses the standard Order object on the CRM platform. B2C Commerce Cloud has its own separate SaaS order model. These are different platforms. Documentation, objects, and APIs for one do not apply to the other.

**Fix:** Confirm the target system is Salesforce Order Management (standard Order object, CRM platform) before applying this skill.

---

## Gotcha 5: OrderDeliveryGroup Is a Mandatory Intermediate Object Between Order and OrderItem

OrderItem in Order Management does not have a direct Order lookup. It references OrderDeliveryGroup, which references Order. Skipping OrderDeliveryGroup and inserting OrderItem with a direct Order lookup fails with a missing required field error.

**Fix:** Include at least one OrderDeliveryGroup per Order in the load plan, even for single-location historical orders.
