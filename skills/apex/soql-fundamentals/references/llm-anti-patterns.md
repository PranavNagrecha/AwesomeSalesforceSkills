# LLM Anti-Patterns — SOQL Fundamentals

Common mistakes AI coding assistants make when generating or advising on SOQL query syntax and semantics.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using the wrong relationship name in parent-to-child subqueries

**What the LLM generates:**

```apex
// Wrong: using the object name instead of the relationship name
List<Account> accounts = [
    SELECT Id, Name, (SELECT Id FROM Contact) FROM Account
];
// Should be "Contacts" (the relationship name), not "Contact"
```

**Why it happens:** LLMs use the object API name in subqueries instead of the child relationship name. For standard objects, the relationship name is the plural (e.g., `Contacts`, `Opportunities`, `Cases`). For custom objects, it ends in `__r` (e.g., `Invoices__r`). Using the object name causes `Didn't understand relationship 'Contact'`.

**Correct pattern:**

```apex
// Standard: use the plural relationship name
List<Account> accounts = [
    SELECT Id, Name, (SELECT Id, Email FROM Contacts) FROM Account
];

// Custom: use the relationship name ending in __r
List<Account> accounts = [
    SELECT Id, (SELECT Id FROM Invoices__r) FROM Account
];
```

**Detection hint:** Subquery `(SELECT.*FROM [A-Z]\w+(?:__c)?)` where the FROM target does not end in `s` (standard) or `__r` (custom) — likely using the object name instead of the relationship name.

---

## Anti-Pattern 2: Using OFFSET for deep pagination beyond 2000 rows

**What the LLM generates:**

```apex
// Page 50 of results
List<Account> page = [SELECT Id, Name FROM Account ORDER BY Name LIMIT 50 OFFSET 5000];
// OFFSET max is 2000 — throws QueryException
```

**Why it happens:** LLMs generate `LIMIT/OFFSET` pagination patterns from SQL training data. SOQL `OFFSET` has a hard maximum of 2,000 rows. For deep pagination, you must use a cursor-based approach with `WHERE` filters.

**Correct pattern:**

```apex
// Cursor-based pagination using the last ID from previous page
Id lastId = previousPageLastId;
List<Account> nextPage = [
    SELECT Id, Name FROM Account
    WHERE Id > :lastId
    ORDER BY Id
    LIMIT 50
];
// Store nextPage[nextPage.size()-1].Id as the cursor for the next page
```

**Detection hint:** `OFFSET\s+\d{4,}` — OFFSET values at or above 2000.

---

## Anti-Pattern 3: Using COUNT() with other fields in the SELECT clause

**What the LLM generates:**

```apex
List<AggregateResult> results = [
    SELECT Name, COUNT(Id) total FROM Account GROUP BY Name
];
// LLM then accesses results like:
String name = (String) results[0].get('Name'); // correct
// But sometimes:
String name = results[0].Name; // Wrong — AggregateResult, not Account
```

**Why it happens:** LLMs confuse `AggregateResult` with SObject field access. Aggregate queries return `AggregateResult` objects, and fields must be accessed via `.get('alias')` or `.get('fieldName')`. Direct dot notation (`.Name`) does not work on `AggregateResult`.

**Correct pattern:**

```apex
List<AggregateResult> results = [
    SELECT Industry, COUNT(Id) total FROM Account GROUP BY Industry
];
for (AggregateResult ar : results) {
    String industry = (String) ar.get('Industry');
    Integer count = (Integer) ar.get('total');
}
```

**Detection hint:** Accessing fields on `AggregateResult` with dot notation (e.g., `result.Name`) instead of `result.get('Name')`.

---

## Anti-Pattern 4: Writing child-to-parent queries with the wrong dot notation for custom objects

**What the LLM generates:**

```apex
// Wrong: using __c in the dot path
List<Contact> contacts = [
    SELECT Id, Account__c.Name FROM Contact
];
// Should use __r for relationship traversal
```

**Why it happens:** LLMs use the field API name (`Account__c`) in dot notation for relationship traversal. For custom lookup fields, the dot path must use the relationship suffix `__r`, not `__c`. The `__c` suffix is only for the ID field itself.

**Correct pattern:**

```apex
// Standard relationship: use the relationship name directly
List<Contact> contacts = [SELECT Id, Account.Name FROM Contact];

// Custom relationship: replace __c with __r for traversal
List<Invoice__c> invoices = [SELECT Id, Customer__r.Name FROM Invoice__c];

// The field itself (ID value) uses __c
List<Invoice__c> invoices = [SELECT Id, Customer__c FROM Invoice__c]; // Returns the Id
```

**Detection hint:** `__c\.` in SOQL — custom field with `__c` used in dot notation traversal (should be `__r.`).

---

## Anti-Pattern 5: Missing date literal format in WHERE clauses

**What the LLM generates:**

```apex
// Wrong: using a string date format
List<Account> accounts = [
    SELECT Id FROM Account WHERE CreatedDate > '2024-01-01'
];
// Should use date literal or bound variable
```

**Why it happens:** LLMs generate SQL-style date strings. SOQL requires date literals (`LAST_N_DAYS:30`, `TODAY`, `THIS_YEAR`) or bound Apex variables for date comparisons. String dates work in some cases but are fragile and locale-dependent.

**Correct pattern:**

```apex
// Use SOQL date literals
List<Account> accounts = [
    SELECT Id FROM Account WHERE CreatedDate > LAST_N_DAYS:90
];

// Or use bound Apex variables
Date cutoff = Date.today().addDays(-90);
List<Account> accounts = [
    SELECT Id FROM Account WHERE CreatedDate > :cutoff
];
```

**Detection hint:** Date/datetime string literals in SOQL WHERE clauses — `WHERE.*>\s*'20\d{2}-` — should use date literals or bind variables.

---

## Anti-Pattern 6: Querying without a WHERE clause or LIMIT on large objects

**What the LLM generates:**

```apex
List<Account> allAccounts = [SELECT Id, Name FROM Account];
// Returns ALL accounts — hits 50K row limit in production orgs
```

**Why it happens:** LLMs generate unbounded queries when the intent is "get some accounts." In production orgs with millions of records, this immediately hits the 50,000 SOQL row limit and throws a `QueryException`.

**Correct pattern:**

```apex
// Always filter or limit queries
List<Account> accounts = [
    SELECT Id, Name FROM Account
    WHERE OwnerId = :UserInfo.getUserId()
    LIMIT 200
];

// For large datasets, use Batch Apex with Database.getQueryLocator
```

**Detection hint:** `\[SELECT.*FROM\s+\w+\s*\]` — SOQL with no WHERE clause and no LIMIT.
