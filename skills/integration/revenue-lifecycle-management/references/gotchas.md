# Gotchas — Revenue Lifecycle Management

## Gotcha 1: RLM and CPQ + Salesforce Billing Are Completely Different Products

**What happens:** Code written for CPQ + Salesforce Billing (using SBQQ__*, blng__* objects) does not work in an RLM org. SOQL against `blng__BillingSchedule__c` returns "object not found" or zero results.

**When it occurs:** Any time practitioners conflate the two product lines — very common because both are informally called "Revenue Cloud" or "Salesforce Billing."

**How to avoid:** Before writing any code, confirm which product the org uses. Check Setup > Installed Packages for `Salesforce CPQ` or `Salesforce Billing` (managed package = legacy). If these are absent and `Revenue Cloud` features appear in Setup, it is native RLM. Use standard API object names in RLM.

---

## Gotcha 2: Billing Schedules Must Be Created via Connect API — They Are Not Auto-Created

**What happens:** An order is activated in RLM but no BillingSchedule records appear. Querying `SELECT Id FROM BillingSchedule WHERE OrderItemId = '...'` returns zero results.

**When it occurs:** When practitioners expect RLM to behave like legacy Salesforce Billing, which auto-creates billing schedule records on order activation.

**How to avoid:** In RLM, billing schedule creation is an explicit step requiring a Connect API POST call after order activation. Design this as a DRO Auto-Task or Apex callout that fires immediately after order activation.

---

## Gotcha 3: Amendment Creates New BillingSchedule, Not Update

**What happens:** After an asset amendment, only one BillingSchedule is found per OrderItem — the original. The amendment's billing period is missing from revenue reporting.

**When it occurs:** When practitioners assume amendment orders update existing BillingSchedule records rather than creating new ones.

**How to avoid:** After amendment order activation, create a new BillingSchedule for the amended period via Connect API. When reporting total billed amount across the asset lifecycle, aggregate all BillingSchedule records for an asset, not just the latest.

---

## Gotcha 4: DRO Stalled Steps Do Not Auto-Resume

**What happens:** An auto-task in a DRO fulfillment plan fails (e.g., a callout to a provisioning system returns 500). The DRO plan stalls at that step and no subsequent swimlane steps execute. Orders remain unfulfilled until manually resolved.

**When it occurs:** When DRO auto-task or callout steps encounter errors and no monitoring or manual resume process is in place.

**How to avoid:** Monitor the DRO Fulfillment Dashboard for stalled plans. Implement alerting on failed auto-tasks. Define a runbook for manual step resolution and DRO plan resumption. Implement idempotent auto-tasks so they can be safely re-executed after failures.

---

## Gotcha 5: FinanceTransaction Is System-Generated and Read-Only

**What happens:** An Apex class attempts to create or update a FinanceTransaction record to correct an accounting entry. It throws a system exception: "Entity is not editable."

**When it occurs:** When practitioners attempt to adjust accounting entries by writing to FinanceTransaction.

**How to avoid:** FinanceTransaction records are read-only system ledger entries. Accounting corrections must be made at the source (Invoice, Payment). Never attempt DML on FinanceTransaction.
