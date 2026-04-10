# CPQ Data Model — Work Template

Use this template when working on tasks that involve the Salesforce CPQ (SBQQ__) object graph.

## Scope

**Skill:** `cpq-data-model`

**Request summary:** (fill in what the user or task requires — e.g., "Query CPQ quote lines for an integration", "Update discount on a quote programmatically", "Build renewal automation from subscriptions")

---

## Context Gathered

Answer these before writing any code or configuration:

- **CPQ installed?** [ ] Confirmed SBQQ__ namespace present (check Installed Packages or `SELECT Id FROM SBQQ__Quote__c LIMIT 1`)
- **Operation type:** [ ] Read-only query  [ ] Programmatic write  [ ] Contract creation  [ ] Renewal
- **CPQ lifecycle stage in scope:** [ ] Quoting  [ ] Pricing  [ ] Contracting  [ ] Renewal/Amendment
- **Running user's CPQ permissions:** [ ] SBQQ CPQ User permission set assigned
- **CPQ package version:** _______ (check Setup > Installed Packages > Salesforce CPQ)

---

## Object Reference Quick Map

| Task | Primary Object | Key Fields |
|---|---|---|
| Read a CPQ quote | `SBQQ__Quote__c` | `SBQQ__NetAmount__c`, `SBQQ__Status__c`, `SBQQ__Primary__c`, `SBQQ__Opportunity2__c` |
| Read quote lines | `SBQQ__QuoteLine__c` (via `SBQQ__LineItems__r`) | `SBQQ__NetPrice__c`, `SBQQ__Quantity__c`, `SBQQ__Discount__c`, `SBQQ__Product__c` |
| Read quote line groups | `SBQQ__QuoteLineGroup__c` (via `SBQQ__LineItemGroups__r`) | `SBQQ__NetTotal__c`, `SBQQ__Number__c` |
| Price rule logic | `SBQQ__PriceRule__c` → `SBQQ__PriceAction__c` / `SBQQ__PriceCondition__c` | `SBQQ__Active__c`, `SBQQ__EvaluationOrder__c` |
| Volume discounts | `SBQQ__DiscountSchedule__c` → `SBQQ__DiscountTier__c` | `SBQQ__DiscountUnit__c`, `SBQQ__LowerBound__c`, `SBQQ__Discount__c` |
| Contracted subscriptions | `SBQQ__Subscription__c` | `SBQQ__Contract__c`, `SBQQ__EndDate__c`, `SBQQ__RenewalPrice__c` |

---

## Approach

**Which pattern applies?** (select one)

- [ ] **Read-only SOQL** — Direct query on `SBQQ__Quote__c` / `SBQQ__QuoteLine__c`. No pricing engine involved.
- [ ] **CPQ Quote API write** — `SBQQ.QuoteService.read` → mutate inputs → `calculate` → `save` callback pattern.
- [ ] **Contract/Subscription query** — SOQL on `SBQQ__Subscription__c` with `SBQQ__Contract__c` filter.
- [ ] **Price rule / discount schedule configuration** — Admin setup in CPQ, no Apex.

**Reasoning:** (why this pattern fits the request)

---

## SOQL Template (Read-Only)

```soql
SELECT
    Id,
    Name,
    SBQQ__Status__c,
    SBQQ__NetAmount__c,
    SBQQ__StartDate__c,
    SBQQ__EndDate__c,
    SBQQ__SubscriptionTerm__c,
    SBQQ__Primary__c,
    (
        SELECT
            Id,
            SBQQ__ProductName__c,
            SBQQ__Quantity__c,
            SBQQ__ListPrice__c,
            SBQQ__CustomerPrice__c,
            SBQQ__NetPrice__c,
            SBQQ__Discount__c,
            SBQQ__Group__c
        FROM SBQQ__LineItems__r
        ORDER BY SBQQ__SortOrder__c ASC NULLS LAST
    )
FROM SBQQ__Quote__c
WHERE SBQQ__Opportunity2__c = :opportunityId
  AND SBQQ__Primary__c = true
LIMIT 1
```

---

## CPQ Quote API Template (Programmatic Write)

```apex
// Step 1: Read the quote into a QuoteModel
SBQQ.QuoteModel quoteModel = SBQQ.QuoteService.read(quoteId);

// Step 2: Mutate INPUT fields (quantities, discounts) — NOT calculated output fields
// Example: change quantity on the first line
quoteModel.lineItems[0].record.SBQQ__Quantity__c = /* new value */;

// Step 3: Serialize and calculate (async — provide callback class name)
String quoteJSON = JSON.serialize(quoteModel);
SBQQ.QuoteService.calculate(quoteJSON, 'MyQuoteCalculatorCallback');

// Step 4: Implement the callback to save after calculation
// global class MyQuoteCalculatorCallback implements SBQQ.QuoteCalculatorPlugin {
//     global void onAfterCalculate(SBQQ.QuoteModel quote) {
//         SBQQ.QuoteService.save(quote);
//     }
// }
```

---

## Subscription Query Template

```soql
SELECT
    Id,
    SBQQ__Product__c,
    SBQQ__ProductName__c,
    SBQQ__Quantity__c,
    SBQQ__NetPrice__c,
    SBQQ__StartDate__c,
    SBQQ__EndDate__c,
    SBQQ__RenewalPrice__c,
    SBQQ__RenewalQuantity__c,
    SBQQ__SubscriptionType__c,
    SBQQ__Contract__c
FROM SBQQ__Subscription__c
WHERE SBQQ__Contract__c = :contractId
  AND SBQQ__SubscriptionEndDate__c >= TODAY
ORDER BY SBQQ__StartDate__c ASC
```

---

## Review Checklist

- [ ] All quote references use `SBQQ__Quote__c` (not standard `Quote`)
- [ ] All quote line references use `SBQQ__QuoteLine__c` (not `QuoteLineItem`)
- [ ] SOQL subqueries use correct relationship name `SBQQ__LineItems__r`
- [ ] No direct DML on `SBQQ__NetPrice__c`, `SBQQ__CustomerPrice__c`, or `SBQQ__RegularPrice__c`
- [ ] Programmatic writes use CPQ Quote API (read → calculate → save)
- [ ] Subscription queries use `SBQQ__Subscription__c`, not standard `Asset`
- [ ] Running user has SBQQ CPQ User or SBQQ CPQ Admin permission set
- [ ] Apex classes that call `SBQQ.QuoteService` have a corresponding `@isTest` mock

---

## Notes

(Record deviations from the standard pattern and the reason — e.g., why a direct SOQL read was sufficient without the Quote API, or why a non-standard CPQ configuration changes the expected object graph.)
