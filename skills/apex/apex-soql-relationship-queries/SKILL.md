---
name: apex-soql-relationship-queries
description: "Use this skill when writing or debugging SOQL relationship queries in Apex — child-to-parent dot notation traversal, parent-to-child subqueries, polymorphic TYPEOF projection and `.Type` type filtering, and FROM-clause alias notation for implicit-join filtering. Trigger keywords: relationship query, subquery, dot notation, getSObjects, TYPEOF, What.Type filter, WhatId, WhoId, alias notation. NOT for aggregate queries — use apex/apex-aggregate-queries. NOT for SOSL text search — use data/sosl-search-patterns."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
triggers:
  - "soql parent to child subquery apex getSObjects iterate related records"
  - "relationship query dot notation child to parent five levels deep"
  - "polymorphic TYPEOF WhatId WhoId Task Event SOQL query"
  - "TYPEOF WhatId WhoId polymorphic lookup Task Event SOQL"
  - "aliasing a soql object in the from clause to filter its parent without selecting parent fields"
  - "filter task or event by whatid whoid type in account opportunity soql"
tags:
  - soql
  - relationship-queries
  - child-to-parent
  - parent-to-child
  - polymorphic
  - typeof
  - getSObjects
  - subquery
  - alias-notation
inputs:
  - "Object names and the relationship direction needed (child-to-parent or parent-to-child)"
  - "Whether any lookup field is polymorphic (Task.WhatId, Task.WhoId, Event.WhatId, Event.WhoId, FeedItem.ParentId)"
  - "API version in use (subqueries require API v58.0+; Bulk API excludes subqueries)"
outputs:
  - "Syntactically correct SOQL with relationship traversal or subquery"
  - "Apex code that safely accesses child records via getSObjects()"
  - "TYPEOF clause for polymorphic fields with WHEN/ELSE branches"
dependencies: []
version: 1.2.1
author: Pranav Nagrecha
updated: 2026-07-08
---

# SOQL Relationship Queries in Apex

This skill activates when a practitioner needs to query related records across Salesforce objects — traversing parent fields with dot notation, pulling child records in a subquery, or handling polymorphic lookup fields like `Task.WhatId`. It covers correct SOQL syntax, Apex accessor patterns, and the hard platform limits that cause silent data loss when ignored.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the relationship direction: are you reading parent field values from a child record (child-to-parent) or loading related child records from a parent (parent-to-child)?
- Check whether any lookup field is polymorphic. Standard polymorphic fields are `Task.WhatId`, `Task.WhoId`, `Event.WhatId`, `Event.WhoId`, and `FeedItem.ParentId`. These require `TYPEOF` — a plain dot-notation `WhatId.Name` is not valid.
- Verify the API version. Parent-to-child subqueries are not supported in the Bulk API or for external objects. They require standard REST/SOAP API v58.0 or later.
- Know the relationship name: custom relationships use the `__r` suffix (e.g. `Custom_Object__r`), standard relationships use the plural child name (e.g. `Contacts`, `Opportunities`).

---

## Core Concepts

### Child-to-Parent Dot Notation

A child record can access fields on its parent and grand-parent objects using dot notation in the SELECT clause or WHERE clause. Each dot step traverses one lookup or master-detail relationship upward.

```soql
SELECT Id, Name, Account.Name, Account.Owner.Name
FROM Contact
WHERE Account.Industry = 'Technology'
```

**Hard limits (enforced at parse time):**
- Maximum **5 levels** of dot traversal in a single chain (e.g. `A.B.C.D.E.F` is 5 hops — one more throws a parse error).
- Maximum **55 relationship traversals** per query across all chains combined.
- Cross-object formula fields **cannot** be used in the `WHERE` clause. Use the underlying field or traverse the relationship directly.

### Alias Notation for Implicit-Join Filtering

SOQL supports alias notation in SELECT queries. You assign a short name to an object in the `FROM` clause and then reference that object — or a related object reached through it — by the alias everywhere else in the query. To establish an alias, name the object first and put the alias token immediately after it. To bring in a related parent object, add a comma and reference it through the base object's relationship path, then give it its own alias.

```soql
SELECT count()
FROM Contact c, c.Account a
WHERE a.Name = 'MyriadPubs'
```

Here `Contact c` aliases the base object and `c.Account a` aliases its related Account. This is an implicit join: it lets you filter on a parent record in `WHERE` without listing any parent field in the `SELECT` clause. Plain dot notation (`WHERE Account.Name = 'MyriadPubs'`) resolves the same filter — alias notation is the documented alternative and reads more compactly when the same related object is referenced several times in one query.

**Reserved words cannot be alias names.** These SOQL keywords are rejected as alias identifiers: `AND, ASC, DESC, EXCLUDES, FIRST, FROM, GROUP, HAVING, IN, INCLUDES, LAST, LIKE, LIMIT, NOT, NULL, NULLS, OR, SELECT, USING, WHERE, WITH`. Single letters (`c`, `a`) are safe, but avoid mnemonic short forms like `in`, `or`, and `not` — they collide with the reserved words and parse-error.

This FROM-clause **object** aliasing is a separate feature from aliasing a **field or aggregate** in the `SELECT` list (e.g. `SELECT Name n, MAX(Amount) max FROM Opportunity GROUP BY Name`), which is covered in apex-aggregate-queries.

### Parent-to-Child Subqueries

A parent query can include a nested SELECT that retrieves all related child records. The inner SELECT references the child object by its **child relationship name** on the parent's object definition.

```soql
SELECT Id, Name,
       (SELECT Id, LastName, Email FROM Contacts),
       (SELECT Id, StageName FROM Opportunities WHERE StageName = 'Closed Won')
FROM Account
WHERE Type = 'Customer'
```

**Hard limits:**
- Maximum **20 subqueries** per outer query.
- The outer query row limit is **50,000** records total (same as flat SOQL). Inner subquery rows count within that total.
- `ORDER BY` inside subqueries is not supported in all API versions; prefer sorting in Apex if targeting older integrations.
- **Bulk API does not support subqueries.** Any code path that runs these queries through the Bulk API will fail at runtime.

### Accessing Child Records in Apex — getSObjects()

When a parent-to-child subquery returns results, the child list is **not** a typed `List<SObject>` you can cast directly. You must call `getSObjects(relationshipName)` on the parent `SObject` instance.

```apex
List<Account> accounts = [
    SELECT Id, Name, (SELECT Id, LastName FROM Contacts)
    FROM Account
];
for (Account acc : accounts) {
    List<SObject> childRows = acc.getSObjects('Contacts');
    if (childRows == null) {
        continue; // No child records — getSObjects returns null, NOT an empty list
    }
    for (SObject row : childRows) {
        Contact c = (Contact) row;
        System.debug(c.LastName);
    }
}
```

The relationship name string passed to `getSObjects()` is the **child relationship name** — same token used in the SOQL subquery. For custom objects it carries the `__r` suffix.

### Polymorphic Fields and TYPEOF

Polymorphic lookups (`Task.WhatId`, `Task.WhoId`, `Event.WhatId`, `Event.WhoId`, `FeedItem.ParentId`) can reference records from multiple object types. The `TYPEOF` clause in SOQL lets you specify which fields to return depending on the concrete type of the referenced record.

```soql
SELECT Id, Subject,
       TYPEOF WhatId
           WHEN Account THEN Name, Industry
           WHEN Opportunity THEN Name, StageName
           ELSE Id
       END
FROM Task
WHERE ActivityDate = TODAY
```

**Key rules:**
- `TYPEOF` is required to project *type-specific* fields on a polymorphic lookup; plain dot notation like `WhatId.Name` is invalid.
- The `ELSE` branch handles any object types not listed in `WHEN` clauses.
- `TYPEOF` has been **generally available since API version 46.0** (Summer '19). The Developer Preview label of the SOQL Polymorphism feature applied only to API versions *before* 46.0 — on any currently supported version it is a stable, GA clause, so don't gate its use behind a "preview" caveat.
- `TYPEOF` is **SELECT-clause only.** It is rejected in `WHERE`, `GROUP BY`/`HAVING`, aggregate/`COUNT()` queries, Bulk API SOQL, Streaming API PushTopics, and the SELECT list of a semi-join subquery. To *filter* a polymorphic field by type in any of those contexts, use the `.Type` qualifier (see below).
- In Apex, check `getSObjectType()` (or use `instanceof`) on the referenced field value before casting.

#### Filtering a Polymorphic Field by Type (`.Type`)

Because `TYPEOF` is projection-only, the way to *filter* rows by the concrete type of a polymorphic field is the `.Type` qualifier. `Type` resolves to a plain string value (`'Account'`, `'User'`, `'Opportunity'`), so it compares with the ordinary string operators — `=`, `!=`, and, as the documented primary form, `IN`:

```soql
SELECT Id
FROM Event
WHERE What.Type IN ('Account', 'Opportunity')
```

Rows whose reference resolves to a type outside the list are **silently excluded** — they are dropped from the result set, not returned with null fields. Per the docs, an `Event` pointing at a `Campaign` in `What` would simply not appear above. Keep this in mind when auditing polymorphic-field data completeness: a `.Type IN (...)` filter quietly narrows the population.

Once the filter pins the field to a single type, that type's own fields become addressable with ordinary dot notation:

```soql
SELECT Id, Owner.Name
FROM Event
WHERE Owner.Type = 'User'
```

Unlike `TYPEOF`, `.Type` filtering has **no API-version floor** and is the *only* legal way to select rows by polymorphic type inside the contexts where `TYPEOF` is banned — `WHERE`, Bulk API SOQL, semi-join inner queries, and `GROUP BY`/aggregate queries. The same `.Type` filter works verbatim from inside an Apex class; project the relationship with `TYPEOF`, then disambiguate the concrete type at runtime with `instanceof` before casting.

A field is polymorphic (and therefore eligible for `.Type` filtering) precisely when its describe metadata reports `namePointing` and `polymorphicForeignKey` as `true` with more than one entry in `referenceTo`.

---

## Common Patterns

### Pattern: Bulk-Safe Parent-to-Child with Null Guard

**When to use:** Trigger or batch handler that needs related child records for every parent in a collection.

**How it works:**

```apex
List<Account> accs = [
    SELECT Id, Name,
           (SELECT Id, Title FROM Contacts LIMIT 200)
    FROM Account WHERE Id IN :accountIds
];
for (Account a : accs) {
    List<SObject> contacts = a.getSObjects('Contacts');
    if (contacts == null) continue; // explicit null guard is mandatory
    for (SObject s : contacts) {
        Contact c = (Contact) s;
        // process c
    }
}
```

**Why not an alternative:** Issuing a separate SOQL query per Account inside the loop burns one governor query per record. The subquery bundles all child data into a single round-trip.

### Pattern: Selective Child Relationship Name for Custom Objects

**When to use:** Any time a custom object is the child side of a relationship.

**How it works:** Look up the child relationship name on the parent object's field definition in Setup > Object Manager > Fields & Relationships. The default is `<ObjectPluralLabel>__r` but the relationship name is configurable. Use that exact string in both the SOQL subquery and `getSObjects()`.

```soql
-- Correct: custom child relationship name with __r
SELECT Id, (SELECT Id FROM My_Custom_Children__r) FROM Account
```

```soql
-- Wrong: using the object API name instead of the relationship name
SELECT Id, (SELECT Id FROM My_Custom_Child__c) FROM Account  -- parse error
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need parent field value on a child record | Child-to-parent dot notation in SELECT | Simple, single query, no extra round-trip |
| Filter on a parent object referenced repeatedly, no parent fields in SELECT | Alias notation (`FROM Contact c, c.Account a`) or plain dot notation | Both filter without selecting parent fields; the alias gives the object a compact handle for repeated references |
| Need all related child records for a set of parents | Parent-to-child subquery with getSObjects() | One query, avoids N+1 SOQL problem |
| Need to *project* per-type fields off a polymorphic lookup | `TYPEOF ... WHEN ... END` in the SELECT clause | Only clause that returns different fields per referenced type |
| Need to *filter* rows by polymorphic type (`WHERE`, Bulk API, aggregate, semi-join) | `.Type` qualifier, e.g. `What.Type IN ('Account','Opportunity')` | `TYPEOF` is SELECT-only; `.Type` is the only legal filter and has no API-version floor |
| Running query through Bulk API | Separate queries, no subqueries | Bulk API rejects relationship subqueries at runtime |
| More than 20 child object types needed | Break into multiple queries by object | Hard 20-subquery limit per outer query |
| Need child records sorted for UI display | Sort in Apex after getSObjects() | ORDER BY in subquery has inconsistent API-version support |

---

## Recommended Workflow

1. **Identify relationship direction and type.** Determine whether you need child-to-parent traversal, a parent-to-child subquery, or both. Note whether any field is polymorphic. Confirm the exact relationship names from Setup or `Schema.DescribeFieldResult`.
2. **Verify limits before writing the query.** Count dot-traversal depth (max 5) and total traversals (max 55) for child-to-parent. Count subqueries (max 20) for parent-to-child. If limits are tight, split into multiple queries and merge results in Apex.
3. **Write the SOQL.** Use correct relationship name tokens: plural child relationship name for standard objects (`Contacts`, `Opportunities`), `__r` suffix for custom objects. Add `TYPEOF` with `WHEN`/`ELSE` for any polymorphic field.
4. **Access child records safely in Apex.** Call `getSObjects(relationshipName)` — never cast the relationship result directly. Add an explicit `null` check before iterating because `getSObjects` returns `null` when no child records exist for a row.
5. **Bulkify.** Place SOQL outside loops. Pass a `Set<Id>` via `:bindVariable` in the WHERE clause. Limit the inner subquery row count with `LIMIT` if the child volume per parent can be very large.
6. **Test boundary conditions.** Write unit tests with zero children, one child, and many children per parent. Confirm no `NullPointerException` from the missing null guard. Use `@isTest(SeeAllData=false)` and create test data explicitly.
7. **Validate governor usage.** Use `Limits.getQueries()` before and after to confirm the query count is as expected. Assert in tests that no extra SOQL is issued inside loops.

---

## Review Checklist

- [ ] Dot-traversal depth does not exceed 5 levels in any chain
- [ ] Total relationship traversals across all chains in the query do not exceed 55
- [ ] Number of subqueries in parent-to-child query does not exceed 20
- [ ] `getSObjects()` called with the correct relationship name string (not the object API name)
- [ ] Explicit `null` check present before iterating the `getSObjects()` result
- [ ] Custom object relationships use `__r` suffix in both SOQL and `getSObjects()` call
- [ ] `TYPEOF` used for any polymorphic field; add an `ELSE` branch (optional per the SOQL reference) when unlisted object types must still return a value
- [ ] SOQL is outside all loops (bulkified)
- [ ] Query not routed through Bulk API if subqueries are present
- [ ] Any FROM-clause alias avoids SOQL reserved words (`in`, `or`, `not`, and the rest of the keyword list)

---

## Salesforce-Specific Gotchas

1. **getSObjects() returns null, not an empty list** — When a parent record has no related children, `acc.getSObjects('Contacts')` returns `null`. Iterating `null` in a `for` loop throws a `NullPointerException` at runtime. Always guard with `if (childRows == null) continue;`.
2. **Custom relationship name vs object API name** — Using `My_Custom_Child__c` (the object API name) instead of `My_Custom_Children__r` (the child relationship name) in a subquery causes a compile-time parse error. The relationship name is set on the lookup/master-detail field definition and may differ from the object name.
3. **Cross-object formula fields are not filterable** — A formula field that references a parent field (e.g. `Account_Industry__c` as a formula on Contact) cannot be used in a `WHERE` clause. Use the direct dot-notation traversal instead: `Account.Industry = 'Technology'`.
4. **Bulk API rejects parent-to-child subqueries** — A query that works perfectly in synchronous Apex is rejected when the same query string is submitted to a Bulk API 2.0 query job. The documentation lists parent-to-child relationship queries among the unsupported constructs, alongside `GROUP BY`, `OFFSET`, `TYPEOF`, aggregate functions such as `COUNT()`, and compound address/geolocation fields. Child-to-parent traversal (`Contact.Account.Name`) *is* supported. Restructure any Bulk API code path as separate queries joined in your own code. Do not code against a specific named error string here: the rejection surfaces as a malformed-query/invalid-batch class failure, and the documentation does not publish a dedicated status code for it.
5. **ORDER BY inside subqueries is unreliable across API versions** — Sorting a subquery result is not guaranteed across all Salesforce API versions. Sort in Apex after calling `getSObjects()` if ordering matters.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| SOQL query string | Relationship query ready for inline or `Database.query()` use |
| Apex loop block | Null-guarded `getSObjects()` iteration pattern |
| TYPEOF clause | Polymorphic field handler with the needed WHEN branches and an optional ELSE catch-all |
| Alias-notation query | FROM-clause object aliases for implicit-join parent filtering |

---

## Related Skills

- apex-aggregate-queries — Use for GROUP BY, COUNT, SUM, AVG, and HAVING clauses; relationship subqueries and aggregate queries are mutually exclusive in the same query
- apex-soql-fundamentals — Use for foundational SELECT syntax, WHERE filters, ORDER BY, LIMIT, and OFFSET before layering relationship traversal
- apex-dml-patterns — Use when the relationship query results drive insert/update/delete operations
- apex-batch-chaining — Use when relationship query result volume requires chunked Batch Apex processing
