# LLM Anti-Patterns — Apex Aggregate Queries

Common mistakes AI coding assistants make when generating or advising on Apex aggregate queries.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Accessing AggregateResult with a Typed Getter Instead of get('alias')

**What the LLM generates:**

```apex
List<AggregateResult> results = [SELECT SUM(Amount) FROM Opportunity GROUP BY AccountId];
for (AggregateResult ar : results) {
    Decimal total = ar.Amount; // or (Decimal) ((Opportunity) ar).Amount
}
```

**Why it happens:** LLMs trained on large Apex corpora conflate `AggregateResult` with typed SObject subclasses. The pattern of accessing `sobject.fieldName` is overwhelmingly common in training data, so the model generalizes it incorrectly to `AggregateResult`.

**Correct pattern:**

```apex
List<AggregateResult> results = [SELECT SUM(Amount) total FROM Opportunity GROUP BY AccountId];
for (AggregateResult ar : results) {
    Decimal total = (Decimal) ar.get('total');
}
```

**Detection hint:** Any line of the form `ar.<fieldName>` or a cast like `((Opportunity) ar)` when `ar` is typed `AggregateResult`.

---

## Anti-Pattern 2: Assuming the 50,000-Row Governor Limit Applies to Aggregate Queries

**What the LLM generates:**

```apex
// "This GROUP BY query can safely return up to 50,000 rows"
List<AggregateResult> results = [
    SELECT AccountId, SUM(Amount) total
    FROM Opportunity
    GROUP BY AccountId
]; // May have 10,000+ groups — LLM says this is fine
```

**Why it happens:** The 50,000-row flat SOQL limit is well-represented in Salesforce training data. The 2,000-row aggregate-specific cap is a lesser-known separate limit and is often absent or underrepresented. LLMs generalize the more commonly cited limit.

**Correct pattern:**

```apex
// Aggregate queries are capped at 2,000 rows total (including ROLLUP/CUBE subtotals).
// If AccountId cardinality exceeds ~1,800, partition the query by date range or use Batch Apex.
List<AggregateResult> results = [
    SELECT AccountId, SUM(Amount) total
    FROM Opportunity
    WHERE CreatedDate = THIS_QUARTER  // partition to reduce cardinality
    GROUP BY AccountId
    LIMIT 2000
];
```

**Detection hint:** Comments or explanations claiming "up to 50,000 rows" for a GROUP BY query, or absence of any cardinality check when the grouped field has high cardinality.

---

## Anti-Pattern 3: Using GROUP BY Inside an Inner/Subquery

**What the LLM generates:**

```apex
List<Account> accs = [
    SELECT Id, Name,
           (SELECT AccountId, SUM(Amount) total
            FROM Opportunities
            GROUP BY AccountId)  // compile error
    FROM Account
];
```

**Why it happens:** LLMs see GROUP BY and subqueries both used with SELECT in SOQL and assume they are composable. SQL databases allow subqueries with aggregation; SOQL's inner query syntax is more restricted and explicitly bans GROUP BY in subqueries.

**Correct pattern:**

```apex
// Run the aggregate query separately, then map to accounts
Map<Id, Decimal> revenueByAccount = new Map<Id, Decimal>();
for (AggregateResult ar : [
    SELECT AccountId, SUM(Amount) total
    FROM Opportunity
    GROUP BY AccountId
]) {
    revenueByAccount.put((Id) ar.get('AccountId'), (Decimal) ar.get('total'));
}
List<Account> accs = [SELECT Id, Name FROM Account WHERE Id IN :revenueByAccount.keySet()];
```

**Detection hint:** `GROUP BY` appearing inside parentheses in a FROM subquery clause of a larger SOQL query.

---

## Anti-Pattern 4: Forgetting to Alias When the Same Function Is Used Twice

**What the LLM generates:**

```apex
List<AggregateResult> results = [
    SELECT COUNT(Id), COUNT(OpportunityId)  // both get auto-alias, one may shadow the other
    FROM OpportunityContactRole
    GROUP BY ContactId
];
Integer total1 = (Integer) results[0].get('expr0'); // fragile — breaks if column order changes
Integer total2 = (Integer) results[0].get('expr1');
```

**Why it happens:** LLMs often omit aliases when generating SOQL because aliases are not required by SQL syntax broadly — the model applies SQL habits to SOQL. Auto-assigned aliases like `expr0` look plausible in generated examples but are fragile.

**Correct pattern:**

```apex
List<AggregateResult> results = [
    SELECT COUNT(Id)              totalRoles,
           COUNT(OpportunityId)   oppRoleCount
    FROM   OpportunityContactRole
    GROUP BY ContactId
];
Integer totalRoles   = (Integer) results[0].get('totalRoles');
Integer oppRoleCount = (Integer) results[0].get('oppRoleCount');
```

**Detection hint:** Multiple aggregate functions in a single SELECT with no alias keywords, or `get('expr0')` / `get('expr1')` in Apex code.

---

## Anti-Pattern 5: Using WHERE Instead of HAVING to Filter on Aggregate Values

**What the LLM generates:**

```apex
List<AggregateResult> results = [
    SELECT AccountId, SUM(Amount) total
    FROM Opportunity
    WHERE SUM(Amount) > 100000  // parse error — WHERE cannot reference aggregate output
    GROUP BY AccountId
];
```

**Why it happens:** `WHERE` is the universal SQL filter clause in most training examples. `HAVING` is less common in training data, and the distinction between pre-aggregation (WHERE) and post-aggregation (HAVING) filtering is a nuance that LLMs frequently miss or collapse.

**Correct pattern:**

```apex
List<AggregateResult> results = [
    SELECT AccountId, SUM(Amount) total
    FROM Opportunity
    GROUP BY AccountId
    HAVING SUM(Amount) > 100000  // HAVING filters on aggregate output after grouping
];
```

**Detection hint:** `WHERE` clause containing a function call like `SUM(...)`, `COUNT(...)`, `AVG(...)`, `MIN(...)`, or `MAX(...)`.

---

## Anti-Pattern 6: Calling QueryMore / Database.getQueryLocator on an Aggregate Query

**What the LLM generates:**

```apex
// Batch Apex start method
public Database.QueryLocator start(Database.BatchableContext bc) {
    return Database.getQueryLocator([
        SELECT AccountId, SUM(Amount) total
        FROM Opportunity
        GROUP BY AccountId  // QueryLocator does not support aggregate queries
    ]);
}
```

**Why it happens:** `Database.getQueryLocator` is the standard pattern for large dataset processing in Batch Apex, and LLMs apply it broadly. The restriction that aggregate queries do not support cursor-based pagination is a platform-specific constraint absent from general Apex examples.

**Correct pattern:**

```apex
// Use Database.Batchable<AggregateResult> with a query-less start, or partition with WHERE ranges
public List<AggregateResult> start(Database.BatchableContext bc) {
    return [
        SELECT AccountId, SUM(Amount) total
        FROM Opportunity
        WHERE CreatedDate >= :startDate AND CreatedDate < :endDate  // range partition
        GROUP BY AccountId
    ];
}
```

**Detection hint:** `Database.getQueryLocator(...)` where the SOQL string contains `GROUP BY`.
