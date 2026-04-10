# Examples — CPQ Integration with ERP

## Example 1: Order Activation Platform Event Trigger to SAP

**Context:** A manufacturing company uses Salesforce CPQ for quoting and SAP S/4HANA for order fulfillment. The integration team initially built the trigger on Opportunity stage `Closed Won` but found that the SAP Sales Order API call fails intermittently because the `OrderItem` records are not yet written when the trigger fires.

**Problem:** Triggering on quote close or Opportunity `Closed Won` results in the middleware calling Salesforce to fetch `OrderItem` data before CPQ has finished generating the Order. The query returns zero items. SAP receives an empty order shell and the integration produces a fulfillment error that requires manual remediation.

**Solution:**

```apex
// Flow-based platform event publish on Order.Status change
// Record-Triggered Flow on Order object
// Entry conditions: Status EQUALS Activated (the agreed ERP-ready value)
// Action: Create Record — Order_Activated__e platform event

// Platform event fields:
// Order_Id__c = {!$Record.Id}
// Account_Id__c = {!$Record.AccountId}
// Order_Number__c = {!$Record.OrderNumber}
// Is_Amendment__c = {!$Record.SBQQ__Contracted__c}

// MuleSoft then subscribes to /event/Order_Activated__e
// and queries OrderItem with the Order Id from the event payload:
// SELECT Id, Product2Id, Product2.ProductCode, Quantity, UnitPrice, TotalPrice
// FROM OrderItem
// WHERE OrderId = :orderId
```

**Why it works:** The `Status = Activated` transition happens only after the Order record and all its `OrderItem` children have been committed. The platform event carries the Order Id so the middleware can query the complete, stable dataset before calling the SAP BAPI or OData API. The `Is_Amendment__c` flag in the event payload tells the middleware whether to create a new SAP Sales Order or route to a delta-quantity update.

---

## Example 2: Amendment Order Delta Detection and ERP Routing

**Context:** A SaaS company uses CPQ subscriptions. Sales reps frequently amend contracts mid-term to add or remove seats. The ERP integration was built to create a new Sales Order for every activated Salesforce Order. After the first renewal cycle, the ERP shows duplicate subscription records because each amendment was treated as a net-new order.

**Problem:** CPQ amendment Orders carry only the delta quantity — e.g., `Quantity = 10` for an add-on of 10 seats to an existing 50-seat contract. The ERP integration, not knowing this is an amendment, creates a new Sales Order for 10 seats. The ERP now has two records: the original 50-seat order and a separate 10-seat order, rather than one 60-seat subscription.

**Solution:**

```apex
// Apex helper in the middleware outbound call handler
// Detects amendment and routes to correct ERP transaction

public class ErpOrderRouter {

    public static String resolveErpTransactionType(Id orderId) {
        Order ord = [
            SELECT Id, SBQQ__Contracted__c, SBQQ__Quote__c,
                   SBQQ__Quote__r.SBQQ__AmendedContract__c
            FROM Order
            WHERE Id = :orderId
            LIMIT 1
        ];

        // If the originating quote has an amended contract,
        // this is a delta order — route to ERP contract update
        if (ord.SBQQ__Quote__r.SBQQ__AmendedContract__c != null) {
            return 'AMENDMENT';
        }

        // Otherwise treat as a new order
        return 'NEW_ORDER';
    }
}

// MuleSoft uses the resolved type to choose:
// NEW_ORDER   → POST /sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder
// AMENDMENT   → PATCH /sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder('{existingDocNo}')
```

**Why it works:** The `SBQQ__AmendedContract__c` field on the CPQ quote is the reliable indicator that the order originated from an amendment flow. Routing on this field ensures the ERP receives either a new Sales Order document or a patch/change-order against the existing contract, matching the CPQ delta quantity semantics.

---

## Anti-Pattern: Embedding Inventory Checks Inside QCP

**What practitioners do:** To show inventory availability during quoting, a developer adds an HTTP callout inside the `QuoteCalculator` plugin's `calculate()` method, calling the ERP inventory REST endpoint for each quote line.

**What goes wrong:** The Quote Calculator Plugin executes in a restricted Apex context. HTTP callouts are not permitted from this context. The first time a rep calculates a quote in production, Salesforce throws `System.CalloutException: Callout not allowed from this context`, and the entire quote calculation fails. No pricing is applied, and no error message is shown to the rep — the quote simply returns with no prices populated, which appears as a CPQ pricing bug rather than an integration error.

**Correct approach:** Move the inventory check out of QCP entirely. Create a custom LWC component on the CPQ quote record page with an explicit "Check Availability" button. The button calls an Apex `@InvocableMethod` (or a public Apex method annotated for LWC wire) that performs the ERP callout. Store results in custom fields on `SBQQ__QuoteLine__c` so the quote page can display them without recalculating. The QCP never touches inventory data.
