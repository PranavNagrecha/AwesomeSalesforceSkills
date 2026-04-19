# Examples — Apex Aggregate Queries

## Example 1: Revenue by Account Using SUM + GROUP BY + HAVING

**Context:** A sales ops team wants to identify high-value accounts for a QBR. They need total closed-won Opportunity revenue per Account, restricted to accounts with more than $100,000 in total revenue.

**Problem:** Without aggregate SOQL, the developer fetches all Opportunities, loops in Apex to sum by AccountId, and filters in memory — burning heap and SOQL rows against the 50,000-row flat limit.

**Solution:**

```apex
// Step 1: Run the aggregate query with explicit aliases
List<AggregateResult> results = [
    SELECT AccountId,
           Account.Name            accountName,
           SUM(Amount)             totalRevenue,
           COUNT(Id)               oppCount,
           MAX(CloseDate)          lastClose
    FROM   Opportunity
    WHERE  StageName = 'Closed Won'
    GROUP BY AccountId, Account.Name
    HAVING SUM(Amount) > 100000
    ORDER BY SUM(Amount) DESC
    LIMIT  200
];

// Step 2: Iterate — always use get('alias'), never a typed getter
for (AggregateResult ar : results) {
    Id      accId       = (Id)      ar.get('AccountId');
    String  accName     = (String)  ar.get('accountName');
    Decimal revenue     = (Decimal) ar.get('totalRevenue');
    Integer count       = (Integer) ar.get('oppCount');
    Date    lastClose   = (Date)    ar.get('lastClose');

    System.debug(accName + ' | ' + revenue + ' | ' + count + ' opps | last close: ' + lastClose);
}
```

**Why it works:** All aggregation and filtering runs at the database tier. HAVING filters on `SUM(Amount)` after grouping — this is not possible with WHERE. Every alias is explicit and stable; the Apex cast targets the correct type.

---

## Example 2: Monthly Opportunity Trend Using CALENDAR_YEAR / CALENDAR_MONTH

**Context:** A RevOps analyst wants a monthly pipeline trend for the current fiscal year. They need a count of opportunities created per calendar month and the total amount per month.

**Problem:** Fetching all Opportunity records and bucketing by month in Apex is expensive (heap, CPU) and breaks at scale. Date string formatting in Apex also introduces timezone edge cases.

**Solution:**

```apex
// Step 1: Use date functions in both SELECT and GROUP BY
List<AggregateResult> monthly = [
    SELECT CALENDAR_YEAR(CreatedDate)  yr,
           CALENDAR_MONTH(CreatedDate) mo,
           COUNT(Id)                   oppCount,
           SUM(Amount)                 pipeline
    FROM   Opportunity
    WHERE  CreatedDate = THIS_YEAR
    GROUP BY CALENDAR_YEAR(CreatedDate), CALENDAR_MONTH(CreatedDate)
    ORDER BY CALENDAR_YEAR(CreatedDate), CALENDAR_MONTH(CreatedDate)
];

// Step 2: Iterate — date function aliases return Integer
for (AggregateResult ar : monthly) {
    Integer yr       = (Integer) ar.get('yr');
    Integer mo       = (Integer) ar.get('mo');
    Integer cnt      = (Integer) ar.get('oppCount');
    Decimal pipeline = (Decimal) ar.get('pipeline');

    // pipeline can be null if all Amount values are null for a bucket
    Decimal safePipeline = (pipeline != null) ? pipeline : 0;

    System.debug(yr + '-' + mo + ' | ' + cnt + ' opps | $' + safePipeline);
}
```

**Why it works:** `CALENDAR_YEAR` and `CALENDAR_MONTH` are DB-native date grouping functions. They appear in both SELECT (with alias) and GROUP BY (without alias — the GROUP BY clause uses the function expression, not the alias). The ORDER BY clause keeps months in chronological order with no Apex sorting needed.

---

## Example 3: Hierarchical Subtotals Using GROUP BY ROLLUP

**Context:** A sales manager wants revenue grouped by Region and Sub-Region, with subtotals per Region and a grand total for a full territory report.

**Problem:** Computing subtotals in Apex after a flat GROUP BY query requires multiple passes and custom logic. GROUP BY ROLLUP handles this at the DB tier.

**Solution:**

```apex
List<AggregateResult> rollupResults = [
    SELECT Region__c           region,
           Sub_Region__c       subRegion,
           SUM(Amount)         totalAmount,
           COUNT(Id)           oppCount
    FROM   Opportunity
    WHERE  StageName = 'Closed Won'
    GROUP BY ROLLUP(Region__c, Sub_Region__c)
];

for (AggregateResult ar : rollupResults) {
    String  region    = (String)  ar.get('region');
    String  subRegion = (String)  ar.get('subRegion');
    Decimal total     = (Decimal) ar.get('totalAmount');
    Integer cnt       = (Integer) ar.get('oppCount');

    if (region == null) {
        // Grand total row — both dimensions are null in ROLLUP
        System.debug('GRAND TOTAL | ' + total);
    } else if (subRegion == null) {
        // Region subtotal row — sub-region dimension is null
        System.debug('Region subtotal: ' + region + ' | ' + total);
    } else {
        // Leaf row
        System.debug(region + ' > ' + subRegion + ' | ' + total + ' (' + cnt + ')');
    }
}
```

**Why it works:** ROLLUP generates subtotal rows with `null` for the rolled-up dimension. Null-checking in Apex distinguishes leaf rows, region subtotals, and the grand total. Note: the total row count is (distinct combinations) + (distinct regions) + 1 — account for this against the 2,000-row cap.

---

## Anti-Pattern: Accessing AggregateResult with a Typed Getter

**What practitioners do:** They try `(Decimal) ((Opportunity) ar).Amount` or call `ar.Amount` as if `AggregateResult` is a typed SObject.

**What goes wrong:** `AggregateResult` does not extend any SObject type. Typed field access causes a compile-time error (`Variable does not exist`) or a runtime `SObjectException`. Even if the developer casts to Object first, the cast will fail because AggregateResult stores values as generic Object keyed by alias.

**Correct approach:**

```apex
// Wrong — does not compile
Decimal rev = ((Opportunity) ar).Amount;

// Wrong — AggregateResult has no typed field accessors
Decimal rev = ar.Amount;

// Correct — always use get('alias') and cast
Decimal rev = (Decimal) ar.get('totalRevenue');
```
