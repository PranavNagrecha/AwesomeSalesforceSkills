# Commerce Order History Migration — Work Template

Use this template when planning or executing a Salesforce Order Management historical order migration.

## Scope

- Total historical orders to migrate: ___________
- Date range of orders: ___________
- Are any orders still active (fulfillment/refund pending)? [ ] Yes  [ ] No
- LifeCycleType for migrated OrderSummary records: [ ] Unmanaged (historical)  [ ] Managed (active)

---

## Pre-Migration Checklist

- [ ] Order Management enabled in target org (Setup > Order Settings)
- [ ] OrderSummary object visible in Object Manager
- [ ] ConnectAPI access confirmed in Apex sandbox test
- [ ] LifeCycleType decision documented (Unmanaged for historical orders)
- [ ] Load sequence documented (Order > OrderDeliveryGroup > OrderItem > Activate > OrderSummary)

---

## Load Sequence Plan

| Step | Object | Status Required | Method | Batch Size |
|---|---|---|---|---|
| 1 | Order | N/A (set Status=Draft) | Bulk API Insert | ≤10,000/batch |
| 2 | OrderDeliveryGroup | Order must exist | Bulk API Insert | ≤10,000/batch |
| 3 | OrderItem | Order + ODG must exist | Bulk API Insert | ≤10,000/batch |
| 4 | Order Activation | All child records loaded | Bulk API Update (Status=Activated) | ≤10,000/batch |
| 5 | OrderSummary | Order must be Activated | ConnectAPI / Batch Apex | ≤200/execute() |

---

## ConnectAPI OrderSummary Creation (Apex Template)

```apex
ConnectAPI.OrderSummaryInputRepresentation input = 
    new ConnectAPI.OrderSummaryInputRepresentation();
input.orderId = order.Id;
input.orderLifeCycleType = 'UNMANAGED'; // Use 'MANAGED' only for active orders
ConnectAPI.OrderSummary.createOrderSummary(input);
```

---

## Validation SOQL

```sql
-- Orders without OrderSummary (should be 0 after migration)
SELECT Id FROM Order WHERE Status = 'Activated' 
  AND Id NOT IN (SELECT OrderId FROM OrderSummary)

-- Confirm LifeCycleType
SELECT Id, LifeCycleType, OrderId FROM OrderSummary 
  WHERE LifeCycleType = 'UNMANAGED' LIMIT 10

-- OrderItem and OrderDeliveryGroup counts
SELECT COUNT() FROM OrderItem
SELECT COUNT() FROM OrderDeliveryGroup
```

---

## Notes

_Capture org-specific configuration, error patterns, and open questions._
