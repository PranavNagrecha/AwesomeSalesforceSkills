# Examples — SOQL Fundamentals

## Example 1: Querying Related Contact Data from an Account

**Context:** A developer needs to build a Lightning component that shows an Account's related Contacts including their parent Account's billing city — all in one query to avoid extra API calls.

**Problem:** The developer writes two separate SOQL queries: one for the Account and one for Contacts. Inside a trigger, this costs two of the 100 SOQL queries allowed per transaction and makes the code harder to maintain.

**Solution:**

```apex
// Child-to-parent: get Contact fields + parent Account fields in one query
List<Contact> contacts = [
    SELECT Id, FirstName, LastName, Email,
           Account.Name, Account.BillingCity, Account.Industry
    FROM Contact
    WHERE Account.Industry = 'Technology'
    AND Account.BillingState = 'California'
    ORDER BY LastName ASC
    LIMIT 200
];
```

Or with a parent-to-child subquery when starting from Account:

```apex
// Parent-to-child: Account + nested Contacts list in one query
List<Account> accounts = [
    SELECT Id, Name, BillingCity,
           (SELECT Id, FirstName, LastName, Email FROM Contacts
            WHERE IsEmailBounced = false
            ORDER BY LastName
            LIMIT 50)
    FROM Account
    WHERE Industry = 'Technology'
    AND BillingState = 'California'
    LIMIT 50
];

// Iterate nested results
for (Account acc : accounts) {
    for (Contact c : acc.Contacts) {
        // process each contact
    }
}
```

**Why it works:** Child-to-parent traversal uses dot notation on the relationship name (standard: `Account.Name`; custom: `Parent__r.Field__c`). Parent-to-child uses a subquery with the child's relationship name (standard: `Contacts`; custom: `Line_Items__r`). Both reduce SOQL count to a single query.

---

## Example 2: Paginated Query for Large Result Sets

**Context:** A Visualforce controller or REST API integration needs to display a paginated list of Opportunity records sorted by close date. The full result set may exceed 2,000 records, which is the OFFSET limit.

**Problem:** The developer tries to use a large OFFSET value (e.g., OFFSET 5000) and gets a `NUMBER_OUTSIDE_VALID_RANGE` error. Alternatively, they load all 50,000 records into memory and filter in Apex, burning heap limit.

**Solution — OFFSET for small result sets (< 2,000 rows):**

```apex
Integer pageSize = 50;
Integer pageNumber = 3; // zero-based page
Integer offset = pageSize * pageNumber; // 150

List<Opportunity> opps = [
    SELECT Id, Name, CloseDate, Amount, StageName
    FROM Opportunity
    WHERE IsClosed = false
    ORDER BY CloseDate ASC, Id ASC  // tiebreaker Id for stable order
    LIMIT :pageSize
    OFFSET :offset
];
```

**Solution — queryLocator for large result sets (> 2,000 rows):**

```apex
// Use Database.getQueryLocator() for batch/cursor-based pagination
Database.QueryLocator locator = Database.getQueryLocator(
    'SELECT Id, Name FROM Opportunity WHERE IsClosed = false ORDER BY CloseDate ASC'
);
Database.QueryLocatorIterator it = locator.iterator();
while (it.hasNext()) {
    Opportunity opp = (Opportunity) it.next();
    // process record
}
```

**Why it works:** OFFSET works server-side and is efficient for small pages. The maximum OFFSET is 2,000; beyond that, use `queryMore()` (SOAP), `nextRecordsUrl` (REST), or `Database.QueryLocator` (Apex Batch). Always include `ORDER BY Id` as a tiebreaker so the page boundaries are stable even if records are added between requests.

---

## Example 3: Aggregate Query for Pipeline Reporting

**Context:** A developer needs to produce a pipeline summary showing total opportunity amount grouped by Stage, but only for stages with more than $50,000 in pipeline.

**Problem:** The developer loads all Opportunity records and aggregates in Apex code, consuming heap and CPU. For large orgs with tens of thousands of open opportunities, this risks hitting governor limits.

**Solution:**

```apex
// GROUP BY with HAVING to filter aggregated results server-side
List<AggregateResult> results = [
    SELECT StageName, SUM(Amount) totalAmount, COUNT(Id) oppCount
    FROM Opportunity
    WHERE IsClosed = false
    AND CloseDate = THIS_FISCAL_YEAR
    GROUP BY StageName
    HAVING SUM(Amount) > 50000
    ORDER BY SUM(Amount) DESC
];

for (AggregateResult ar : results) {
    String stage = (String) ar.get('StageName');
    Decimal total = (Decimal) ar.get('totalAmount');
    Integer count = (Integer) ar.get('oppCount');
    System.debug(stage + ': $' + total + ' (' + count + ' opps)');
}
```

**Why it works:** GROUP BY runs aggregation on the database server — no Apex heap consumption for individual records. HAVING filters after grouping, equivalent to SQL HAVING. Date literals like `THIS_FISCAL_YEAR` automatically respect the org's fiscal year configuration, making the query portable across deployments.

---

## Anti-Pattern: SELECT * Workaround That Breaks on Schema Changes

**What practitioners do:** To avoid enumerating fields, developers write queries that list every field name they can find in Schema.getGlobalDescribe(), building a comma-separated string and passing it to `Database.query()`.

**What goes wrong:** When new fields are added or fields are removed, the dynamically constructed field list breaks. Encrypted fields, formula fields with complex logic, or long text area fields can trigger `QUERY_TOO_COMPLICATED` even when the query length is under 100,000 characters. The dynamic approach also introduces SOQL injection risk if any user input is concatenated.

**Correct approach:** Use `FIELDS(STANDARD)` for standard fields and `FIELDS(CUSTOM)` for custom fields (API v51.0+), always with `LIMIT`. These respect FLS automatically. For specific use cases, enumerate only the fields actually needed — this is explicit, safe, and performant.

```apex
// Safe schema exploration with FIELDS keyword
List<Contact> contacts = [SELECT FIELDS(STANDARD) FROM Contact LIMIT 200];

// Production queries: enumerate only needed fields
List<Account> accs = [SELECT Id, Name, BillingCity, Industry FROM Account LIMIT 200];
```
