# Billing Integration Apex — Work Template

Use this template when implementing billing API integrations, payment gateway lifecycle management, programmatic invoice generation, or credit note automation via the Salesforce Billing managed package Apex APIs.

## Scope

**Skill:** `billing-integration-apex`

**Request summary:** (fill in what the user asked for)

**Integration type:** (check all that apply)
- [ ] Invoice generation via Connect REST API
- [ ] Payment transaction lifecycle via blng.TransactionAPI
- [ ] Credit note issuance via blng.InvoiceAPI
- [ ] Custom payment gateway adapter (blng.PaymentGateway interface)

---

## Context Gathered

Answer these before writing any code:

- **Billing package installed?** Confirm `blng__` namespace objects exist in the org. (Yes / No)
- **API version:** Confirm API version is 63.0+ if using Connect REST API. (Version: ___)
- **Volume:** How many billing schedule IDs or payment records will be processed per execution? (Count: ___)
- **Calling context:** Where will the billing API be called from? (Trigger / Controller / Flow action / Scheduled job / Other: ___)
- **DML before callout?** Does the calling context perform any DML before the gateway or REST API call? (Yes / No / Unknown)
- **Gateway type:** Native Billing gateway or custom adapter required? (Native / Custom: ___)

---

## Approach

Based on context gathered above, select the applicable pattern from SKILL.md:

**Pattern selected:** (choose one)
- [ ] Async Payment Transaction via Queueable — for TransactionAPI calls where DML precedes the callout
- [ ] Batched Invoice Generation via Connect REST API — for targeted programmatic invoice generation
- [ ] Custom Payment Gateway Adapter — for integrating a non-native payment processor

**Justification:** (why this pattern fits the requirement)

---

## Implementation Notes

### Transaction Context Assessment

- [ ] Identified all DML operations in the calling context
- [ ] Confirmed TransactionAPI calls are isolated in an async context (Queueable / @future)
- [ ] Confirmed no DML precedes the gateway callout inside the async execution method

### API Version and Limits

- [ ] Endpoint URL includes `v63.0` or later (if using Connect REST API)
- [ ] Invoice generation calls are chunked to ≤200 billingScheduleIds per request
- [ ] Chunking logic implemented for volumes exceeding 200 schedules

### Namespace Correctness

- [ ] All sObject references use `blng__` prefix (e.g., `blng__Invoice__c`, `blng__Payment__c`)
- [ ] All field references use `blng__` prefix (e.g., `blng__Status__c`, `blng__InvoiceDate__c`)
- [ ] Apex class references use `blng.` dot notation (e.g., `blng.TransactionAPI`, `blng.InvoiceAPI`)

---

## Checklist

Copy from SKILL.md Review Checklist and tick as you complete:

- [ ] All `blng.TransactionAPI` calls are in a Queueable implementing `Database.AllowsCallouts` or in a `@future(callout=true)` method
- [ ] Connect REST API endpoint URL contains the correct API version (v63.0 or later)
- [ ] Invoice generation calls contain no more than 200 `billingScheduleIds` per request; chunking logic exists for larger sets
- [ ] All Billing sObject references use the `blng__` namespace prefix
- [ ] Test classes use `HttpCalloutMock` for all callout-dependent paths
- [ ] Custom gateway adapter class is registered on `blng__PaymentGateway__c.blng__GatewayType__c`
- [ ] Error handling captures gateway response codes and persists failure details to a log record or platform event

---

## Validation Commands

```bash
# Run the billing-specific checker on your Apex classes
python3 skills/apex/billing-integration-apex/scripts/check_billing_apex.py \
    --source-dir path/to/force-app/main/default/classes
```

---

## Notes

(Record any deviations from the standard pattern and why.)
