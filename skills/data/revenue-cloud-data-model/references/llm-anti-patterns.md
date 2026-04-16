# LLM Anti-Patterns — Revenue Cloud Data Model

## Anti-Pattern 1: Using blng__* Object Names for Native RLM Queries

**What the LLM generates:**

```sql
SELECT Id, blng__BillingStartDate__c, blng__Amount__c
FROM blng__BillingSchedule__c
WHERE blng__Order__c = 'OrderId'
```

**Why it happens:** Salesforce Billing (managed package) is far more common in training data than native RLM. LLMs default to managed package object names for all "billing schedule" queries.

**Correct pattern:**

```sql
SELECT Id, StartDate, Amount
FROM BillingSchedule
WHERE OrderItemId IN (SELECT Id FROM OrderItem WHERE OrderId = 'OrderId')
```

**Detection hint:** Any SOQL using `blng__BillingSchedule__c`, `blng__Invoice__c`, or `blng__Payment__c` in an RLM context is using the wrong object model.

---

## Anti-Pattern 2: Attempting to Insert or Update FinanceTransaction

**What the LLM generates:**

```apex
FinanceTransaction ft = new FinanceTransaction(
    InvoiceId = invoiceId,
    Amount = 1200.00,
    TransactionType = 'Revenue'
);
insert ft;
```

**Why it happens:** FinanceTransaction appears to be a standard SObject. LLMs model it as insertable without knowing it is system-generated and read-only.

**Correct pattern:** FinanceTransaction records are created by the platform when Invoices are posted or Payments are received. Query them for reconciliation: `SELECT Id, TransactionType, Amount FROM FinanceTransaction WHERE InvoiceId = :invoiceId`. Never attempt DML.

**Detection hint:** Any `insert`, `update`, or `upsert` DML on `FinanceTransaction` is incorrect.

---

## Anti-Pattern 3: Querying BillingSchedule Without API v55.0+

**What the LLM generates:** Code that queries `BillingSchedule` using Salesforce API version 51.0 or 52.0 and then reports that the object does not exist.

**Why it happens:** LLMs don't track API version availability for objects. `BillingSchedule` was introduced at v55.0.

**Correct pattern:** Ensure API version is set to v55.0 or higher in all tooling configurations (SFDX `sfdx-project.json`, REST API calls, Apex class API versions). Verify with `SELECT Id FROM BillingSchedule LIMIT 1` in the Developer Console or Workbench.

**Detection hint:** "BillingSchedule object not found" errors in an RLM-enabled org are often API version mismatches, not missing features.

---

## Anti-Pattern 4: Using LIMIT 1 on BillingSchedule to Get "Current" Terms

**What the LLM generates:**

```sql
SELECT Id, Amount, StartDate
FROM BillingSchedule
WHERE OrderItemId = :orderItemId
ORDER BY CreatedDate DESC
LIMIT 1
```

**Why it happens:** Finding the "latest" record via ORDER BY + LIMIT 1 is a common pattern for current-state lookups. With amendment-created BillingSchedules, this returns only the most recent amendment's schedule, missing all earlier periods.

**Correct pattern:** To get the complete billing picture for an asset across amendments, remove LIMIT 1 and aggregate all billing schedules:

```sql
SELECT SUM(Amount) totalBilled, COUNT(Id) scheduleCount
FROM BillingSchedule
WHERE OrderItemId IN (SELECT Id FROM OrderItem WHERE OrderId = :orderId)
  AND Status = 'Active'
```

**Detection hint:** `ORDER BY CreatedDate DESC LIMIT 1` on BillingSchedule in an amended asset context produces incomplete data.

---

## Anti-Pattern 5: Treating BillingSchedule as Directly Linked to Order

**What the LLM generates:**

```sql
SELECT Id FROM BillingSchedule WHERE OrderId = 'someOrderId'
```

**Why it happens:** BillingSchedule seems like it should have a direct Order relationship. It actually has a lookup to OrderItem, not Order.

**Correct pattern:**

```sql
SELECT Id FROM BillingSchedule 
WHERE OrderItemId IN (SELECT Id FROM OrderItem WHERE OrderId = 'someOrderId')
```

Or use relationship traversal:

```sql
SELECT Id, OrderItem.OrderId FROM BillingSchedule
WHERE OrderItem.OrderId = 'someOrderId'
```

**Detection hint:** `WHERE OrderId` on BillingSchedule will fail — the field is `OrderItemId`, not `OrderId`. There is no direct Order lookup on BillingSchedule.
