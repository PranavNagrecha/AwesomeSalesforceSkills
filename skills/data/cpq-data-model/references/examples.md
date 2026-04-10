# Examples — CPQ Data Model

## Example 1: SOQL Query for a CPQ Quote with Line Groups and Line Items

**Context:** An integration or reporting job needs to read all CPQ quote data for an opportunity, including grouped line items and their net prices, without triggering pricing recalculation.

**Problem:** A developer queries `Quote` and `QuoteLineItem` and finds either no rows (if standard quote sync is disabled) or stale prices (if the standard quote was last synced at an earlier state). The CPQ pricing data lives exclusively on `SBQQ__Quote__c` and `SBQQ__QuoteLine__c`.

**Solution:**

```soql
SELECT
    Id,
    Name,
    SBQQ__Status__c,
    SBQQ__NetAmount__c,
    SBQQ__StartDate__c,
    SBQQ__EndDate__c,
    SBQQ__SubscriptionTerm__c,
    SBQQ__Opportunity2__c,
    SBQQ__Primary__c,
    (
        SELECT
            Id,
            Name,
            SBQQ__Group__c,
            SBQQ__Product__c,
            SBQQ__ProductName__c,
            SBQQ__Quantity__c,
            SBQQ__ListPrice__c,
            SBQQ__CustomerPrice__c,
            SBQQ__NetPrice__c,
            SBQQ__Discount__c,
            SBQQ__SubscriptionPricing__c,
            SBQQ__SubscriptionType__c
        FROM SBQQ__LineItems__r
        ORDER BY SBQQ__SortOrder__c ASC NULLS LAST
    ),
    (
        SELECT
            Id,
            Name,
            SBQQ__NetTotal__c
        FROM SBQQ__LineItemGroups__r
    )
FROM SBQQ__Quote__c
WHERE SBQQ__Opportunity2__c = :opportunityId
  AND SBQQ__Primary__c = true
LIMIT 1
```

**Why it works:** `SBQQ__LineItems__r` is the correct child relationship name from `SBQQ__Quote__c` to `SBQQ__QuoteLine__c`. `SBQQ__LineItemGroups__r` is the relationship to `SBQQ__QuoteLineGroup__c`. Both are defined in the CPQ managed package. The query is read-only and does not trigger the pricing engine.

---

## Example 2: Query Active Subscriptions for a Contract to Build a Renewal Context

**Context:** A custom renewal automation job needs to find all active CPQ subscriptions for a given contract so it can pass them to a renewal quote creation process.

**Problem:** A developer looks for `Asset` or `OrderItem` records associated with the contract. In CPQ orgs, contracted recurring products live in `SBQQ__Subscription__c`, not in standard Asset. Standard Asset may be populated if the org uses CPQ asset tracking, but `SBQQ__Subscription__c` is the authoritative source for subscription pricing and renewal dates.

**Solution:**

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

**Why it works:** `SBQQ__Subscription__c.SBQQ__Contract__c` is the lookup to the standard `Contract` object that links the subscription to its originating contract. `SBQQ__RenewalPrice__c` and `SBQQ__RenewalQuantity__c` are the fields the CPQ renewal engine uses to populate the next renewal quote line — making them the correct source for any custom renewal logic.

---

## Example 3: Checking Whether a Product Has a Volume Discount Schedule

**Context:** A quoting assistant needs to tell a sales rep what discount they will receive at a given quantity before they save the quote.

**Problem:** A developer checks the standard `PricebookEntry` for discount information and finds none. CPQ volume discounts are stored in `SBQQ__DiscountSchedule__c` with child `SBQQ__DiscountTier__c` records, not on the pricebook entry.

**Solution:**

```soql
// Step 1: Find the discount schedule for the product
SELECT
    Id,
    Name,
    SBQQ__DiscountUnit__c,
    SBQQ__Type__c,
    (
        SELECT
            SBQQ__LowerBound__c,
            SBQQ__UpperBound__c,
            SBQQ__Discount__c
        FROM SBQQ__DiscountTiers__r
        ORDER BY SBQQ__LowerBound__c ASC
    )
FROM SBQQ__DiscountSchedule__c
WHERE Id IN (
    SELECT SBQQ__DiscountSchedule__c
    FROM Product2
    WHERE Id = :productId
)
```

**Why it works:** Product2 carries a lookup `SBQQ__DiscountSchedule__c` (added by the CPQ managed package) that points to the volume schedule. The `SBQQ__DiscountTiers__r` child relationship traverses to `SBQQ__DiscountTier__c` records, each of which defines a quantity band and the discount percentage the CPQ engine applies when a quote line falls in that band.

---

## Anti-Pattern: Direct DML on a CPQ Quote Line Price Field

**What practitioners do:** To quickly fix a price for a demo or integration test, a developer runs:

```apex
update new SBQQ__QuoteLine__c(
    Id = lineId,
    SBQQ__NetPrice__c = 850.00
);
```

**What goes wrong:** The DML saves the literal value `850.00` to `SBQQ__NetPrice__c`, but the CPQ pricing engine is not invoked. The quote-header rollup field `SBQQ__NetAmount__c` is not recalculated. Any approval processes that evaluate `SBQQ__NetAmount__c` now operate against a stale value. On the next user-triggered save of the quote in the UI, the pricing engine overwrites `SBQQ__NetPrice__c` with its own calculated value, discarding the manual override.

**Correct approach:** Use the CPQ Quote API to read the quote into a `QuoteModel`, set the input field that drives pricing (e.g., `SBQQ__Discount__c` or `SBQQ__Quantity__c`), call `calculate`, and save via `SBQQ.QuoteService.save(quoteModel)`. The engine then derives `SBQQ__NetPrice__c` correctly.
