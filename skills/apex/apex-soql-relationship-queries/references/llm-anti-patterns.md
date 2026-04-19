# LLM Anti-Patterns — SOQL Relationship Queries

Common mistakes AI coding assistants make when generating or advising on SOQL relationship queries.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Direct Cast of Child Relationship Result Without getSObjects()

**What the LLM generates:**

```apex
List<Contact> contacts = (List<Contact>) acc.Contacts;
// or
for (Contact c : acc.Contacts) { ... }
```

**Why it happens:** LLMs trained on general Java/OOP patterns expect a typed collection property access. The SOQL relationship result looks syntactically like a list field, reinforcing this pattern. Some older Salesforce blog posts also show this incorrectly.

**Correct pattern:**

```apex
List<SObject> rows = acc.getSObjects('Contacts');
if (rows == null) continue;
for (SObject row : rows) {
    Contact c = (Contact) row;
}
```

**Detection hint:** Look for `(List<Contact>)` cast applied directly to a relationship field expression, or a `for (Contact c : acc.Contacts)` loop without a `getSObjects()` call.

---

## Anti-Pattern 2: Using the Object API Name Instead of Child Relationship Name in Subquery

**What the LLM generates:**

```soql
SELECT Id, (SELECT Id FROM My_Custom_Child__c) FROM Account
```

**Why it happens:** LLMs default to inserting the object API name because it is the most frequently referenced identifier in Apex code. The child relationship name (the `__r` form or the plural standard name) is a distinct metadata attribute that LLMs conflate with the object name.

**Correct pattern:**

```soql
-- Use the child relationship name, not the object API name
SELECT Id, (SELECT Id FROM My_Custom_Children__r) FROM Account
```

**Detection hint:** A subquery FROM clause that ends in `__c` (object API name) is always wrong — subquery FROM must use the relationship name, which ends in `__r` for custom or is a plural noun for standard (e.g., `Contacts`, not `Contact`).

---

## Anti-Pattern 3: Using a Cross-Object Formula Field in the WHERE Clause

**What the LLM generates:**

```soql
SELECT Id FROM Contact WHERE Account_Industry__c = 'Technology'
```

where `Account_Industry__c` is a formula field on Contact that references `Account.Industry`.

**Why it happens:** LLMs correctly recognize that formula fields can be referenced in SELECT and treat them as queryable columns without knowing the platform restriction on cross-object formula fields in WHERE clauses.

**Correct pattern:**

```soql
SELECT Id FROM Contact WHERE Account.Industry = 'Technology'
```

**Detection hint:** A formula field in the WHERE clause. Check whether the field is defined as a cross-object formula (formula text contains a dot-traversal like `Account.Industry`). If so, replace with the direct dot-notation path in the WHERE clause.

---

## Anti-Pattern 4: Assuming Subqueries Work in Bulk API Contexts

**What the LLM generates:** Code that places a SOQL query containing a subquery into a `Database.BatchQueryLocator` or instructs the user to use the same query string in an ETL tool using Bulk API mode.

```apex
// LLM suggests this for batch Apex start() method
return Database.getQueryLocator([
    SELECT Id, (SELECT Id FROM Contacts) FROM Account
]);
```

**Why it happens:** LLMs learn that subqueries work in SOQL and do not distinguish execution contexts (interactive Apex, REST API, Bulk API). The Bulk API limitation is not prominently surfaced in most training data.

**Correct pattern:**

```apex
// Batch start: flat query only
return Database.getQueryLocator([SELECT Id FROM Account WHERE ...]);

// Batch execute: separate child query per chunk
List<Contact> contacts = [SELECT Id, AccountId FROM Contact WHERE AccountId IN :accountIds];
```

**Detection hint:** A `Database.getQueryLocator()` call or Bulk API context that contains a subquery (a nested SELECT inside parentheses in the FROM'd object's SELECT list).

---

## Anti-Pattern 5: Missing null Guard on getSObjects() Result

**What the LLM generates:**

```apex
for (SObject row : acc.getSObjects('Contacts')) {
    // process row
}
```

**Why it happens:** Most programming environments return an empty collection for "no results." LLMs trained on these conventions do not anticipate that Salesforce returns `null` from `getSObjects()` when no children exist, because null-for-empty is a non-standard behavior.

**Correct pattern:**

```apex
List<SObject> rows = acc.getSObjects('Contacts');
if (rows == null) continue; // null, not empty, when no children
for (SObject row : rows) {
    Contact c = (Contact) row;
}
```

**Detection hint:** An inline `acc.getSObjects('...')` call used directly as the expression in a `for` loop, without an intermediate variable and null check. This is reliably wrong whenever the parent records may have zero children.

---

## Anti-Pattern 6: Dot Notation on Polymorphic Lookup Field

**What the LLM generates:**

```soql
SELECT Id, Subject, WhatId.Name FROM Task
```

**Why it happens:** Dot notation works for non-polymorphic lookups, so LLMs generalize it to all lookup fields. The distinction that polymorphic fields require `TYPEOF` is a SOQL-specific rule not present in relational SQL or most ORM patterns.

**Correct pattern:**

```soql
SELECT Id, Subject,
       TYPEOF WhatId
           WHEN Account     THEN Name
           WHEN Opportunity THEN Name, StageName
           ELSE Id
       END
FROM Task
```

**Detection hint:** Dot notation applied to `WhatId`, `WhoId`, or `ParentId` on Task, Event, or FeedItem objects — these are always polymorphic and require `TYPEOF`.
