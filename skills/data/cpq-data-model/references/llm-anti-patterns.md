# LLM Anti-Patterns — CPQ Data Model

Common mistakes AI coding assistants make when generating or advising on Salesforce CPQ object model usage. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Querying Standard Quote Instead of SBQQ__Quote__c

**What the LLM generates:**

```soql
SELECT Id, TotalPrice, (SELECT UnitPrice, Quantity FROM QuoteLineItems)
FROM Quote
WHERE OpportunityId = :oppId
```

**Why it happens:** LLMs are trained on large volumes of standard Salesforce documentation and generic Apex patterns where `Quote` and `QuoteLineItem` are the correct objects. The CPQ managed-package objects are less represented in training data, and the LLM defaults to standard object names.

**Correct pattern:**

```soql
SELECT Id, SBQQ__NetAmount__c,
    (SELECT SBQQ__Quantity__c, SBQQ__NetPrice__c FROM SBQQ__LineItems__r)
FROM SBQQ__Quote__c
WHERE SBQQ__Opportunity2__c = :oppId AND SBQQ__Primary__c = true
```

**Detection hint:** Any SOQL that queries `FROM Quote` or references `QuoteLineItem` in a CPQ context is suspect. Check for `SBQQ__Quote__c` as the correct object name.

---

## Anti-Pattern 2: Direct DML to Update CPQ Quote Line Prices

**What the LLM generates:**

```apex
SBQQ__QuoteLine__c line = [SELECT Id FROM SBQQ__QuoteLine__c WHERE Id = :lineId];
line.SBQQ__NetPrice__c = 1200.00;
line.SBQQ__Discount__c = 10;
update line;
```

**Why it happens:** LLMs recognize `SBQQ__QuoteLine__c` as a standard SObject and apply the universal Apex DML pattern. They do not model the constraint that CPQ-managed fields require the pricing engine to be invoked.

**Correct pattern:**

```apex
// Use CPQ Quote API — read, mutate inputs (not outputs), calculate, save
SBQQ.QuoteModel qm = SBQQ.QuoteService.read(quoteId);
// Set an INPUT field that drives pricing, not a calculated output field
qm.lineItems[0].record.SBQQ__Discount__c = 10;
SBQQ.QuoteService.calculate(JSON.serialize(qm), 'MyCalculatorCallback');
// In the callback: SBQQ.QuoteService.save(quotemodelFromCallback);
```

**Detection hint:** Any `update` DML statement that sets `SBQQ__NetPrice__c`, `SBQQ__CustomerPrice__c`, `SBQQ__RegularPrice__c`, or `SBQQ__SpecialPrice__c` directly is an anti-pattern.

---

## Anti-Pattern 3: Using QuoteLineItem Instead of SBQQ__QuoteLine__c in Apex

**What the LLM generates:**

```apex
List<QuoteLineItem> lines = [
    SELECT UnitPrice, Quantity, Product2Id
    FROM QuoteLineItem
    WHERE QuoteId = :quoteId
];
```

**Why it happens:** The LLM maps "quote line" to the standard `QuoteLineItem` object. Without CPQ context it does not know the managed-package parallel object exists.

**Correct pattern:**

```apex
List<SBQQ__QuoteLine__c> lines = [
    SELECT SBQQ__CustomerPrice__c, SBQQ__Quantity__c, SBQQ__Product__c
    FROM SBQQ__QuoteLine__c
    WHERE SBQQ__Quote__c = :cpqQuoteId
];
```

**Detection hint:** References to `QuoteLineItem` in Apex that are intended for CPQ quote lines. The correct type is `SBQQ__QuoteLine__c`.

---

## Anti-Pattern 4: Wrong Child Relationship Name in Subquery

**What the LLM generates:**

```soql
SELECT Id, (SELECT Id, UnitPrice FROM QuoteLineItems)
FROM SBQQ__Quote__c
WHERE Id = :quoteId
```

or

```soql
SELECT Id, (SELECT Id FROM SBQQ__QuoteLines__r)
FROM SBQQ__Quote__c
```

**Why it happens:** The LLM guesses the child relationship name by applying standard Salesforce naming conventions (`{ObjectName}s__r` or the standard `QuoteLineItems`). The actual CPQ relationship name `SBQQ__LineItems__r` is non-obvious.

**Correct pattern:**

```soql
SELECT Id, (SELECT Id, SBQQ__NetPrice__c FROM SBQQ__LineItems__r)
FROM SBQQ__Quote__c
WHERE Id = :quoteId
```

**Detection hint:** Subqueries on `SBQQ__Quote__c` that use `QuoteLineItems`, `SBQQ__QuoteLines__r`, or `LineItems__r` instead of `SBQQ__LineItems__r`. These compile without error but return zero rows.

---

## Anti-Pattern 5: Querying Standard Asset for CPQ Subscription Data

**What the LLM generates:**

```soql
SELECT Id, Product2Id, Quantity, Price
FROM Asset
WHERE AccountId = :accountId
```

**Why it happens:** LLMs associate "contracted products" or "purchased items" with the standard `Asset` object based on general Salesforce training data. They do not model `SBQQ__Subscription__c` as the CPQ-specific subscription object.

**Correct pattern:**

```soql
SELECT
    Id,
    SBQQ__Product__c,
    SBQQ__ProductName__c,
    SBQQ__Quantity__c,
    SBQQ__NetPrice__c,
    SBQQ__StartDate__c,
    SBQQ__EndDate__c
FROM SBQQ__Subscription__c
WHERE SBQQ__Contract__c = :contractId
  AND SBQQ__SubscriptionEndDate__c >= TODAY
```

**Detection hint:** Any query on `Asset` that is intended to retrieve CPQ-contracted recurring products. In CPQ orgs, `SBQQ__Subscription__c` is the authoritative recurring-product object.

---

## Anti-Pattern 6: Confusing SBQQ__PriceRule__c with Standard Discount/Override Mechanisms

**What the LLM generates:**

```apex
// Applying a 10% discount by modifying the pricebook entry
PricebookEntry pbe = [SELECT Id, UnitPrice FROM PricebookEntry WHERE Id = :pbeId];
pbe.UnitPrice = pbe.UnitPrice * 0.9;
update pbe;
```

or advice to use standard `ApprovalProcess` discount overrides as a substitute for CPQ price rules.

**Why it happens:** The LLM defaults to standard pricebook entry or Approval Process patterns for pricing adjustments. It does not model the CPQ declarative pricing layer (`SBQQ__PriceRule__c`, `SBQQ__DiscountSchedule__c`) as the correct mechanism.

**Correct pattern:** For conditional pricing in CPQ, configure an `SBQQ__PriceRule__c` record with appropriate `SBQQ__PriceCondition__c` and `SBQQ__PriceAction__c` child records. For volume-based discounts, configure an `SBQQ__DiscountSchedule__c` with `SBQQ__DiscountTier__c` records and link it to the product. Both approaches integrate with the CPQ pricing waterfall and are evaluated by the pricing engine during quote save.

**Detection hint:** Advice to modify `PricebookEntry.UnitPrice` directly or to use standard `ApprovalProcess` for CPQ discount enforcement. These bypass the CPQ pricing engine entirely.
