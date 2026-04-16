# Gotchas — Revenue Cloud Data Model

## Gotcha 1: Managed Package Object Names vs. Standard API Object Names

**What happens:** SOQL against `blng__BillingSchedule__c` in a native RLM org returns "INVALID_TYPE: sObject type 'blng__BillingSchedule__c' is not supported."

**When it occurs:** When developers write Revenue Cloud queries using CPQ/Salesforce Billing managed package object names (blng__*) in an org running native RLM.

**How to avoid:** Always confirm the product type first. In native RLM orgs, use standard API names: `BillingSchedule`, `Invoice`, `Payment`, `FinanceTransaction`. The managed package names only exist in orgs where the Salesforce Billing managed package is installed.

---

## Gotcha 2: BillingSchedule Requires API Version 55.0+

**What happens:** SOQL against `BillingSchedule` returns "INVALID_TYPE" or the object is not visible in the describe response — even in an RLM-enabled org.

**When it occurs:** When code targets API version 54.0 or earlier. `BillingSchedule` was introduced at API v55.0 (Winter '22).

**How to avoid:** Verify the API version used by the integration or tool (Apex, REST calls, or SFDX settings). Set API version to v55.0+ for any code that queries BillingSchedule, Invoice, or related RLM objects.

---

## Gotcha 3: FinanceTransaction Cannot Be Created or Updated

**What happens:** Apex DML or REST API calls to insert or update FinanceTransaction records throw "ENTITY_IS_LOCKED" or "Entity is not editable" exceptions.

**When it occurs:** When developers attempt to create accounting entries directly by DMLing FinanceTransaction, or try to correct posted transactions by updating them.

**How to avoid:** FinanceTransaction is a system-generated read-only ledger. It is auto-created when Invoices are posted or Payments are received. Read it for reconciliation. Never attempt DML. Accounting corrections must be applied at the Invoice or Payment level.

---

## Gotcha 4: Amendment Creates New BillingSchedule — Original Is Not Updated

**What happens:** A billing dashboard displays only the original BillingSchedule for an asset that has been amended twice. The amendment billing terms (different amounts or dates) are invisible to the reporting query.

**When it occurs:** When reporting queries use `SELECT ... FROM BillingSchedule ORDER BY CreatedDate DESC LIMIT 1` to get the "current" billing schedule, missing amendment records.

**How to avoid:** For amended assets, aggregate all BillingSchedule records to get the full billing picture across the asset lifecycle. Do not rely on LIMIT 1 queries to represent the complete billing state.

---

## Gotcha 5: BillingScheduleGroup Controls Invoice Grouping — Not BillingSchedule Directly

**What happens:** Multiple BillingSchedule records that should appear on a single invoice are generating separate invoices — one per billing schedule.

**When it occurs:** When BillingSchedule records for the same order are not assigned to the same BillingScheduleGroup.

**How to avoid:** Invoice generation is controlled by BillingScheduleGroup, which aggregates BillingSchedule records. Configure BillingScheduleGroup assignment to match the desired invoice grouping logic — all billing lines that should appear on one invoice must belong to the same BillingScheduleGroup.
