# Examples — Revenue Cloud Data Model

## Example 1: Query BillingSchedule Hierarchy for an Order

**Context:** A finance team needs to build an integration that exports all billing schedule details for active Revenue Cloud orders to their external invoicing system.

**Problem:** The team was querying `SELECT Id FROM BillingSchedule` without any relationship to order — they got all billing schedules from the org and couldn't associate them back to specific orders.

**Solution:**

```sql
-- Query billing schedules with order context
SELECT 
    Id,
    OrderItem.OrderId,
    OrderItem.Product2.Name,
    OrderItem.Order.AccountId,
    OrderItem.Order.Account.Name,
    StartDate,
    EndDate,
    BillingFrequency,
    Amount,
    Status,
    BillingScheduleGroupId,
    CreatedDate
FROM BillingSchedule
WHERE OrderItem.Order.Status = 'Activated'
  AND Status = 'Active'
ORDER BY OrderItem.OrderId, StartDate ASC
```

**Why it works:** BillingSchedule has a lookup to OrderItem, not directly to Order. Relationship traversal (`OrderItem.OrderId`, `OrderItem.Order.AccountId`) provides the order context. `Status = 'Active'` filters to current billing schedules.

---

## Example 2: Trace Invoice through FinanceTransaction for ERP Reconciliation

**Context:** An accounting team needs to reconcile Revenue Cloud invoices with their ERP's journal entries. They need the accounting entries generated when each invoice was posted.

**Problem:** The team attempted to insert `FinanceTransaction` records via the REST API to create accounting entries in Salesforce. All insert requests failed with a system error.

**Solution:**

Do NOT insert FinanceTransaction records. Read them after Invoice posting:

```python
import requests

def get_finance_transactions_for_invoice(access_token: str, instance_url: str, 
                                          invoice_id: str) -> list:
    headers = {"Authorization": f"Bearer {access_token}"}
    query = f"""
    SELECT Id, TransactionType, Amount, AccountingPeriodId, 
           CreatedDate, InvoiceId, RelatedObjectId
    FROM FinanceTransaction
    WHERE InvoiceId = '{invoice_id}'
    ORDER BY CreatedDate ASC
    """
    resp = requests.get(
        f"{instance_url}/services/data/v63.0/query",
        headers=headers,
        params={"q": query}
    )
    resp.raise_for_status()
    return resp.json()["records"]

# Read after invoice posting — do NOT attempt to create
transactions = get_finance_transactions_for_invoice(token, instance_url, "INV-001-ID")
for ft in transactions:
    # Export to ERP ledger system (read-only from Salesforce perspective)
    export_to_erp(ft)
```

**Why it works:** FinanceTransaction records are system-generated when Invoices are posted. They are read-only — the only valid operation is `SELECT`. Accounting integrations read these records and export to ERP; they never write back.

---

## Anti-Pattern: Using Legacy Salesforce Billing Object Names for RLM Queries

**What practitioners do:** Query `blng__BillingSchedule__c` or `blng__Invoice__c` in an RLM org expecting to find billing data.

**What goes wrong:** These managed package objects do not exist in a native RLM org. Salesforce returns "INVALID_TYPE: sObject type 'blng__BillingSchedule__c' is not supported" or similar errors.

**Correct approach:** In native RLM orgs, use standard API object names: `BillingSchedule` (not `blng__BillingSchedule__c`), `Invoice` (not `blng__Invoice__c`), `Payment` (not `blng__Payment__c`). Verify the product type before writing any data model queries.
