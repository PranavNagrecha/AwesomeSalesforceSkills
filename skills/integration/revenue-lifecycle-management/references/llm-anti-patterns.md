# LLM Anti-Patterns — Revenue Lifecycle Management

## Anti-Pattern 1: Conflating RLM with CPQ + Salesforce Billing

**What the LLM generates:** SOQL against `blng__BillingSchedule__c` or `SBQQ__Quote__c` in a context described as "Revenue Cloud" or "RLM."

**Why it happens:** "Revenue Cloud" is used informally to describe both native RLM and the legacy CPQ + Salesforce Billing managed package. LLMs apply the most common training data pattern (CPQ + Billing) to all "Revenue Cloud" queries.

**Correct pattern:** Native RLM uses standard API objects: `BillingSchedule`, `Invoice`, `Payment`, `FinanceTransaction`. CPQ uses SBQQ__* and blng__* managed package objects. Confirm the product before writing any code. Never mix object namespaces.

**Detection hint:** Any code mixing `blng__*` or `SBQQ__*` objects with native `BillingSchedule` or `Invoice` objects is operating on incorrect assumptions.

---

## Anti-Pattern 2: Assuming Billing Schedules Auto-Create on Order Activation

**What the LLM generates:** "When you activate an Order in Revenue Cloud, the platform automatically creates billing schedules based on the OrderItem terms."

**Why it happens:** Legacy Salesforce Billing does auto-create billing schedules on activation. LLMs apply this behavior to native RLM, which does not.

**Correct pattern:** In native RLM, billing schedules must be explicitly created via Connect API POST after order activation. Design a DRO Auto-Task or post-activation callout for this step. There is no auto-creation.

**Detection hint:** Any architecture that does not include an explicit billing schedule creation step after order activation is missing a required step for RLM.

---

## Anti-Pattern 3: Attempting DML on FinanceTransaction

**What the LLM generates:**

```apex
FinanceTransaction ft = new FinanceTransaction();
ft.Amount = 1200.00;
ft.InvoiceId = invoiceId;
insert ft;
```

**Why it happens:** LLMs treat FinanceTransaction as a standard insertable Salesforce object, not recognizing it as a system-generated read-only ledger entry.

**Correct pattern:** FinanceTransaction records cannot be created, updated, or deleted via API or DML. They are system-generated automatically when Invoices are posted or Payments are received. Accounting adjustments must be made at the Invoice or Payment level.

**Detection hint:** Any Apex or Flow that performs DML on `FinanceTransaction` is incorrect.

---

## Anti-Pattern 4: Treating Amendment Order as BillingSchedule Update

**What the LLM generates:** "When an asset amendment order is activated, the existing BillingSchedule record is updated to reflect the new terms."

**Why it happens:** Updating an existing record to reflect a change is a natural model. RLM creates a net-new BillingSchedule for each amendment instead.

**Correct pattern:** Each amendment activation creates a new BillingSchedule record. The original remains. Revenue reporting must aggregate all BillingSchedule records for an asset across its full lifecycle, not query only the latest.

**Detection hint:** Any reporting query that fetches `ORDER BY CreatedDate DESC LIMIT 1` on BillingSchedule to get the "current" billing terms is likely missing amendment history.

---

## Anti-Pattern 5: Designing DRO Steps Without Idempotency

**What the LLM generates:** DRO auto-task designs that perform non-idempotent operations (e.g., create a record without checking for duplicates, charge a payment without checking if already charged).

**Why it happens:** LLMs design the happy path without accounting for DRO step re-execution after failure. Failed DRO steps are manually resumed — which re-executes the step.

**Correct pattern:** All DRO auto-tasks must be designed to be safely re-executed. Check for existing records before creating, verify payment status before charging, use external IDs or idempotency keys on callouts. A non-idempotent auto-task executed twice causes data corruption or double-charging.

**Detection hint:** DRO auto-task designs that insert records, process payments, or trigger external calls without idempotency checks are fragile.
