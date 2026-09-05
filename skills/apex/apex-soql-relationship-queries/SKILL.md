---
name: apex-soql-relationship-queries
description: "Use this skill when writing or debugging SOQL relationship queries in Apex — child-to-parent dot notation traversal, parent-to-child subqueries, polymorphic TYPEOF projection and `.Type` type filtering, and FROM-clause alias notation for implicit-join filtering. Trigger keywords: relationship query, subquery, dot notation, getSObjects, TYPEOF, What.Type filter, WhatId, WhoId, alias notation, child relationship name, __r, aggregate query has too many rows, nested SELECT, selector relationship shape. NOT for aggregate queries — use apex/apex-aggregate-queries. NOT for SOSL text search — use data/sosl-search-patterns."
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
  - "fix aggregate query has too many rows for direct assignment use for loop"
  - "iterate child records from a parent sobject without a second soql query"
  - "write a selector method that returns a parent with its children in one query"
  - "batch apex start method with a subquery runs slowly"
  - "choose between a subquery and two queries plus a map"
  - "resolve the child relationship name for a custom lookup in a subquery"
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
  - "API version in the class meta.xml (67.0+ changes the default access mode and bans WITH SECURITY_ENFORCED)"
  - "Execution context the query will run in (synchronous Apex, Batch start(), Bulk API job)"
  - "Expected child-record count per parent (the 200-child SOQL-for-loop boundary)"
outputs:
  - "Syntactically correct SOQL with relationship traversal or subquery"
  - "A selector method returning the relationship shape, and Apex that reads children safely"
  - "TYPEOF clause for polymorphic fields with WHEN branches (ELSE optional)"
  - "A test class asserting each relationship shape including the zero-children case"
dependencies: []
version: 1.3.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# SOQL Relationship Queries in Apex

This skill activates when a practitioner needs to query related records across Salesforce objects — traversing parent fields with dot notation, pulling child records in a subquery, or handling polymorphic lookup fields like `Task.WhatId`. It covers correct SOQL syntax, Apex accessor patterns, and the hard platform limits that cause silent data loss when ignored.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the relationship direction: are you reading parent field values from a child record (child-to-parent) or loading related child records from a parent (parent-to-child)?
- Check whether any lookup field is polymorphic. Standard polymorphic fields are `Task.WhatId`, `Task.WhoId`, `Event.WhatId`, `Event.WhoId`, and `FeedItem.ParentId`. These require `TYPEOF` — a plain dot-notation `WhatId.Name` is not valid.
- Verify the execution context. Bulk API 2.0 "doesn't support SOQL queries that include ... Parent-to-child relationship queries. (Child-to-parent relationship queries are supported.)" (`api_asynch L2892–2896`). External objects *do* support subqueries in Apex — the guide's Salesforce Connect sample queries `(SELECT Id FROM IssueComments__r) FROM GithubIssues__x` (`apexdev L29882, L29906`). UNVERIFIED (2026-09-05): the previous edition of this skill said subqueries "require standard REST/SOAP API v58.0 or later"; no such version floor appears anywhere in apexdev.txt, apexrefguide.txt, api_rest.txt or api_asynch.txt, and every subquery sample in the Apex guide is written without a version caveat. Treat the v58.0 floor as unsupported until the SOQL and SOSL Reference is in the corpus.
- Know the relationship name, which is not the object API name. For a custom relationship field named `MyRel`: "the name of the ID becomes MyRelId__r, the parent object pointer becomes MyRel__c, and the relationship name is MyRel__r" (`object_reference L3030–3032`). Standard child relationships use the registered plural name — the Apex guide's own samples use `FROM Contacts` and `FROM Account.Contacts` (`apexdev L11704, L12160`).
- Check the class `apiVersion`. "In API version 67.0 and later, you can't use the WITH SECURITY_ENFORCED clause in SOQL SELECT queries in Apex code. Instead, use the WITH USER_MODE clause." and "In API version 67.0 and later, Apex runs in user context by default" (`apexdev L11742–11744`, restated `L44493–44502`).

---

## Questions to Ask Before Configuring

Ask these before writing the query. Relationship queries fail late — the wrong answer here produces code that passes a single-parent unit test and throws on the first parent with 200 children or zero children.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "How many children does a busy parent actually have — 5, 50, or 5,000?" | Past ~200 children, reading `acct.Contacts` by direct assignment or `.size()` **inside a SOQL for loop** raises `Aggregate query has too many rows for direct assignment, use FOR loop` (`apexdev L10078–10088`) | Either a `LIMIT` on the subquery, a nested `for` instead of an assignment, or a decision to split into two queries |
| "Is this query going into a Batch `start()` method?" | "Batch Apex jobs run faster when the start method returns a QueryLocator object that doesn't include related records via a subquery… If the start method returns … a QueryLocator object with a relationship subquery, the batch job uses a slower, non-chunking, implementation" (`apexdev L17796–17800`) | A flat QueryLocator plus a child query in `execute()` — the guide's own recommended alternative (`apexdev L17803–17805`) |
| "Which lookup fields on this object are polymorphic?" | `Task`/`Event` `WhoId` points to Contact or Lead, `WhatId` to Account, Opportunity, Campaign or Case, "and if the WhoId field refers to a Lead, then the WhatId field must be empty" (`object_reference L2399–2401`) | The `TYPEOF` `WHEN` branch list, and confirmation that `WhatId.Name` dot notation is not on the table |
| "Do we need the parent's fields, or only to filter on them?" | Filtering does not require projecting: dot notation in `WHERE` works without the parent field in `SELECT`, and so does FROM-clause alias notation | A narrower SELECT list, fewer FLS surfaces, less heap |
| "What API version is the class saved at?" | 67.0+ flips the default access mode to user mode and rejects `WITH SECURITY_ENFORCED` (`apexdev L11742–11744`) | The correct security clause, and whether an existing `WITH SECURITY_ENFORCED` is a blocking upgrade finding |
| "Will the same SOQL string ever be handed to a Bulk API job or an ETL tool?" | Bulk API 2.0 rejects parent-to-child subqueries, `TYPEOF`, `GROUP BY`, `OFFSET` and aggregate functions (`api_asynch L2892–2896`); PK chunking "works only with queries that don't include subqueries" (`api_asynch L7147`) | A second, flat query path for the bulk consumer instead of one shared string |
| "Can a parent legitimately have zero children here?" | The guide's own dynamic-Apex sample guards the child collection with `if (childRecordsFromParent != null)` under the comment "Prevent a null relationship from being accessed" (`apexdev L11719–11721`) | A test case with a childless parent, and a guard that is exercised rather than assumed |

What a proper relationship query adds over just writing a nested SELECT: the query count stays O(1) as the batch grows, the child-access path survives both the zero-child and the 200-child parent, the security clause matches the class's API version, and the shape is pinned by a test instead of by the first production record that breaks it.

---

## Core Concepts

### Child-to-Parent Dot Notation

A child record can access fields on its parent and grand-parent objects using dot notation in the SELECT clause or WHERE clause. Each dot step traverses one lookup or master-detail relationship upward.

```soql
SELECT Id, Name, Account.Name, Account.Owner.Name
FROM Contact
WHERE Account.Industry = 'Technology'
```

The token you dot into is the **relationship name**, not the field name. `Contact.AccountId` carries "Relationship Name: `Account`" (`object_reference L71327–71342`), which is why `Account.Name` and not `AccountId.Name` is the legal path. `Schema.DescribeFieldResult.getRelationshipName()` "Returns the name of the child-to-parent relationship" (`apexrefguide L190914–190917`) when you need to resolve it at runtime.

**Hard limits (enforced at parse time):**
- Maximum **5 levels** of dot traversal in a single chain (e.g. `A.B.C.D.E.F` is 5 hops — one more throws a parse error). UNVERIFIED (2026-09-05): the five-level depth limit is stated in the SOQL and SOSL Reference ("Understanding Relationship Query Limitations"), which is not in the offline corpus; `grep -n -i "five levels\|5 levels\|levels of relationship" apexdev.txt object_reference.txt` returns nothing relevant. The App Limits cheat sheet points at that same reference page for query limits without restating the number (`salesforce_app_limits_cheatsheet L1051–1055`).
- Maximum **55 relationship traversals** per query across all chains combined. UNVERIFIED (2026-09-05): same source gap — no occurrence of a 55-traversal cap in apexdev.txt, object_reference.txt or the App Limits cheat sheet.
- Cross-object formula fields **cannot** be used in the `WHERE` clause. Use the underlying field or traverse the relationship directly. UNVERIFIED (2026-09-05): the non-filterable behaviour of cross-object formula fields is documented on help.salesforce.com and in the SOQL Reference; neither is fetchable, and the Object Reference's field-property tables mark filterability per field rather than stating the general rule.
- What *is* grounded is the failure mode when a relationship query gets too wide: long, complex SOQL "can result in a `QUERY_TOO_COMPLICATED` error … because the statement is expanded internally when processed by Salesforce, even though the original SOQL statement is under the 100,000 character limit" (`salesforce_app_limits_cheatsheet L1057–1062`). Deep traversal chains and many-branch `TYPEOF` clauses are exactly what expands.

### Alias Notation for Implicit-Join Filtering

SOQL supports alias notation in SELECT queries. You assign a short name to an object in the `FROM` clause and then reference that object — or a related object reached through it — by the alias everywhere else in the query. To establish an alias, name the object first and put the alias token immediately after it. To bring in a related parent object, add a comma and reference it through the base object's relationship path, then give it its own alias.

```soql
SELECT count()
FROM Contact c, c.Account a
WHERE a.Name = 'MyriadPubs'
```

Here `Contact c` aliases the base object and `c.Account a` aliases its related Account. This is an implicit join: it lets you filter on a parent record in `WHERE` without listing any parent field in the `SELECT` clause. Plain dot notation (`WHERE Account.Name = 'MyriadPubs'`) resolves the same filter — alias notation is the documented alternative and reads more compactly when the same related object is referenced several times in one query.

UNVERIFIED (2026-09-05): alias notation and the reserved-word list are SOQL Reference claims, not in the offline corpus — see [gotchas.md](references/gotchas.md) Gotcha 7 for the full marker and what was searched.

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

**Governor accounting — each subquery is charged as a query:**

> "In a SOQL query with parent-child relationship subqueries, each parent-child relationship counts as an extra query. These types of queries have a limit of three times the number for top-level queries. The limit for subqueries corresponds to the value that `Limits.getLimitAggregateQueries()` returns. The row counts from these relationship queries contribute to the row counts of the overall code execution." — `apexdev L19613–19616`

So the subquery budget is a *separate* pool sized at 3× the top-level query limit (100 synchronous / 200 asynchronous — `apexdev L19544`), read at runtime via `Limits.getLimitAggregateQueries()`; assert against that method rather than hardcoding a number. Total rows retrieved by SOQL queries is 50,000 per transaction synchronous and asynchronous (`apexdev L19546`), and subquery rows count toward it.

**Other limits:**
- Maximum **20 subqueries** per outer query. UNVERIFIED (2026-09-05): the 20-subquery cap comes from the SOQL and SOSL Reference, which is not in the corpus; `grep -n -i "20 subqueries\|maximum of 20" apexdev.txt object_reference.txt salesforce_app_limits_cheatsheet.txt` finds nothing on this topic. The grounded constraint is the `getLimitAggregateQueries()` budget above — prefer asserting on that.
- `ORDER BY` inside subqueries: UNVERIFIED (2026-09-05). No statement about subquery `ORDER BY` support exists in apexdev.txt. What *is* grounded is that `ORDER BY` or `LIMIT` on a Bulk API 2.0 query disables PK chunking and can cause timeouts (`api_asynch L2888–2890`). Sorting in Apex after the query remains a safe default, but do not present cross-version instability as a documented fact.
- **Bulk API 2.0 rejects parent-to-child subqueries** (`api_asynch L2892–2896`) and PK chunking "works only with queries that don't include subqueries or conditions other than WHERE" (`api_asynch L7147`).

### Reading Child Records in Apex — Typed Access vs `getSObjects()`

There are two accessors, and which one is correct depends on whether the query returned a **concrete sObject type** or a generic `SObject`.

**Concrete type (inline SOQL, typed list) — read the relationship field directly.** This is what the Apex Developer Guide's own bulkification example does:

```apex
// apexdev L20245-L20255 — the guide's recommended alternative to a query in a loop
List<Invoice_Statement__c> invoicesWithLineItems =
   [SELECT Id, Description__c, (SELECT Id, Units_Sold__c, Merchandise__c FROM Line_Items__r)
    FROM Invoice_Statement__c WHERE Id IN :Trigger.newMap.KeySet()];

for (Invoice_Statement__c inv : invoicesWithLineItems) {
    for (Line_Item__c li : inv.Line_Items__r) {
        // Do something
    }
}
```

The guide also assigns the relationship to a typed list outright — `List<IssueComments__x> comments = issue.IssueComments__r;` (`apexdev L29894`) — and calls `.size()` on it (`apexdev L29908`). Direct typed access is documented, supported, and the normal path.

**Generic `SObject` (dynamic SOQL) — use `getSObjects(relationshipName)`.** The Apex Reference Guide describes it as "primarily used with dynamic DML to access values for associated objects, such as child relationships" (`apexrefguide L233176–233181`). It has a `String` overload and a `Schema.SObjectType` overload (`apexrefguide L233181, L233223`) and returns `SObject[]`. The guide's dynamic sample guards the result:

```apex
// apexdev L11703-L11730 (abridged) — dynamic query, generic SObject, explicit guard
String queryString = 'SELECT Id, Name, ' +
           '(SELECT FirstName, LastName FROM Contacts LIMIT 1) FROM Account';
SObject[] queryParentObject = Database.query(queryString);

for (SObject parentRecord : queryParentObject) {
    // Prevent a null relationship from being accessed
    SObject[] childRecordsFromParent = parentRecord.getSObjects('Contacts');
    if (childRecordsFromParent != null) {
        for (SObject childRecord : childRecordsFromParent) {
            System.debug(childRecord.get('FirstName'));
        }
    }
}
```

The guide's comment on that guard is verbatim "Prevent a null relationship from being accessed" (`apexdev L11719`). UNVERIFIED (2026-09-05): the corpus shows the guard, but nowhere states in prose that the accessor returns `null` rather than an empty list, nor whether typed access (`acc.Contacts`) behaves the same way — the typed samples at `apexdev L20254` and `L29894` carry no guard. Write the guard; do not assert the null-vs-empty rule as documented.

Either way the token is the **child relationship name** — the same string used in the subquery `FROM`, carrying `__r` for custom relationships. `Schema.ChildRelationship.getRelationshipName()` resolves it at runtime from `DescribeSObjectResult.getChildRelationships()` (`apexrefguide L189843–189876`).

### The 200-Child Boundary Inside a SOQL For Loop

This is the trap that unit tests with three child records never reach:

> "You can get a `QueryException` in a SOQL for loop with the message `Aggregate query has too many rows for direct assignment, use FOR loop`. This exception is sometimes thrown when accessing a large set of child records (200 or more) of a retrieved sObject inside the loop, or when getting the size of such a record set." — `apexdev L10078–10081`

The guide's own failing example and its fix:

```apex
// apexdev L10082-L10098
for (Account acct : [SELECT Id, Name, (SELECT Id, Name FROM Contacts)
                     FROM Account WHERE Id IN ('<ID value>')]) {
    List<Contact> contactList = acct.Contacts;   // Causes an error
    Integer count = acct.Contacts.size();        // Causes an error
}

// Correct: iterate the child records instead of assigning or sizing the set
for (Account acct : [SELECT Id, Name, (SELECT Id, Name FROM Contacts)
                     FROM Account WHERE Id IN ('<ID value>')]) {
    Integer count = 0;
    for (Contact c : acct.Contacts) {
        count++;
    }
}
```

The same section warns that `JSON.serialize()` on a parent inside a SOQL for loop will not carry the complete child set, because the for-loop mechanism "keep[s] only a subset of the record data in memory, [so] the complete sObject and any subquery sObjects will not be available to obtain complete serialization" (`apexdev L10108–10110`).

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
- `TYPEOF` is required to project *type-specific* fields on a polymorphic lookup; plain dot notation like `WhatId.Name` is invalid. UNVERIFIED (2026-09-05): the Apex guide demonstrates `TYPEOF` on polymorphic fields (`apexdev L9784–9786`) and `SObject.getSObject()` says "If the method references polymorphic fields, a Name object is returned. Use the TYPEOF clause … to directly get results that depend on the runtime object type" (`apexrefguide L233152–233156`), but no corpus source states that `WhatId.Name` is a parse error.
- The `ELSE` branch handles any object types not listed in `WHEN` clauses, and is **optional**: the Apex guide's own examples omit it — `[SELECT TYPEOF What WHEN Account THEN Phone WHEN Opportunity THEN Amount END FROM Event]` (`apexdev L9785–9786`) and the `Merchandise__c` owner query (`apexdev L9823–9824`).
- The relationship name, not the Id field, is what `TYPEOF` takes: `Task.WhatId` and `Event.WhatId` carry "Relationship Name: `What`" (`object_reference L23967–23969`), which is why the guide writes `TYPEOF What`, not `TYPEOF WhatId`. Both spellings appear in the wild; prefer the documented relationship name.
- After the query, the referenced record must be **assigned to a correctly typed variable before it is passed to a method** — "Note that you must assign the referenced sObject that the query returns to a variable of the appropriate type before you can pass it to another method" (`apexdev L9797–9798`; worked example `L9827–9834`).
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

To detect a polymorphic field from Apex, call `Schema.DescribeFieldResult.isNamePointing()` — it "Returns true if the field can have multiple types of objects as parents. For example, a task can have both the Contact/Lead ID (WhoId) field and the Opportunity/Account ID (WhatId) field return true for this method" (`apexrefguide L191317–191321`). Pair it with `getReferenceTo()`, which returns the parent sObject tokens; note that since API 51.0 it "returns referenced objects that aren't accessible to the context user", where API 50.0 and earlier returned an empty list in that case (`apexrefguide L190905–190910`). UNVERIFIED (2026-09-05): the earlier edition of this skill named a `polymorphicForeignKey` describe attribute; that name appears nowhere in apexrefguide.txt, apexdev.txt or object_reference.txt. It is a SOAP-API describe field, not an Apex `DescribeFieldResult` method — do not call it from Apex.

---

## Common Patterns

### Pattern: Bulk-Safe Parent-to-Child, Typed Access

**When to use:** Trigger or service that needs related child records for every parent in a collection, where the query returns a concrete sObject type.

**How it works:**

```apex
List<Account> accs = [
    SELECT Id, Name,
           (SELECT Id, Title FROM Contacts LIMIT 200)
    FROM Account
    WHERE Id IN :accountIds
    WITH USER_MODE
];
for (Account a : accs) {
    // Typed access, as apexdev L20254 does with inv.Line_Items__r.
    // Guard anyway: the guide's dynamic sample guards the same shape (apexdev L11719).
    if (a.Contacts == null || a.Contacts.isEmpty()) { continue; }
    for (Contact c : a.Contacts) {
        // process c
    }
}
```

**Why not an alternative:** Issuing a separate SOQL query per Account inside the loop burns one governor query per record — the guide's `LimitExample` trigger is exactly that failure, and `EnhancedLimitExample` is this fix (`apexdev L20228–20255`). Note this loops over a materialised `List<Account>`, not a SOQL for loop, so the 200-child `Aggregate query has too many rows` boundary does not apply.

### Pattern: Dynamic Query — `getSObjects()` with the Documented Guard

**When to use:** The parent object name or relationship name is only known at runtime, so `Database.query()` returns generic `SObject` rows.

**How it works:**

```apex
SObject[] parents = Database.queryWithBinds(
    'SELECT Id, Name, (SELECT Id, LastName FROM ' + String.escapeSingleQuotes(childRel) + ') ' +
    'FROM Account WHERE Id IN :ids',
    new Map<String, Object>{ 'ids' => accountIds },
    AccessLevel.USER_MODE
);
for (SObject parent : parents) {
    SObject[] children = parent.getSObjects(childRel);
    if (children == null) { continue; }   // apexdev L11719-L11721
    for (SObject child : children) {
        System.debug(child.get('LastName'));
    }
}
```

**Why not an alternative:** `getSObjects` is documented as the dynamic accessor (`apexrefguide L233176–233178`); reaching for it when the query already returns a typed list adds casts without adding safety. See `apex/apex-dynamic-soql-binding-safety` for the injection surface of the concatenated relationship name.

### Pattern: Selective Child Relationship Name for Custom Objects

**When to use:** Any time a custom object is the child side of a relationship.

**How it works:** Look up the child relationship name on the parent object's field definition in Setup > Object Manager > Fields & Relationships, or resolve it in code from `DescribeSObjectResult.getChildRelationships()` → `ChildRelationship.getRelationshipName()` (`apexrefguide L189843–189876`). For a relationship field named `MyRel` the parent pointer is `MyRel__c` and the relationship name is `MyRel__r` (`object_reference L3030–3032`), but the name is configurable and need not match the object's plural label. Use that exact string in the SOQL subquery, in typed access, and in any `getSObjects()` call.

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
| Need all related child records for a set of parents, query returns a concrete type | Parent-to-child subquery, read `parent.Children__r` directly | One query; the shape the guide's own `EnhancedLimitExample` uses (`apexdev L20245–20255`) |
| Same, but the object or relationship name is only known at runtime | Subquery via `Database.query`, read with `getSObjects(name)` | The documented dynamic accessor (`apexrefguide L233176–233178`) |
| Parents have hundreds of children and you need aggregates, not the rows | Two queries plus a `Map<Id, …>`, or an aggregate query | Avoids `Aggregate query has too many rows` at the 200-child boundary in a SOQL for loop (`apexdev L10078–10081`); see `apex/apex-aggregate-queries` |
| Query is the `start()` of a Batch | Flat QueryLocator; subquery moved into `execute()` | A QueryLocator with a subquery forces "a slower, non-chunking, implementation" (`apexdev L17798–17800`) |
| Need to *project* per-type fields off a polymorphic lookup | `TYPEOF ... WHEN ... END` in the SELECT clause | Returns different fields per referenced type (`apexdev L9784–9786`) |
| Need to *filter* rows by polymorphic type | `.Type` qualifier, e.g. `What.Type IN ('Account','Opportunity')` | The guide's first-listed approach for polymorphic filtering (`apexdev L9777–9780`) |
| Running the same SOQL through Bulk API 2.0 or an ETL tool | Separate flat queries, joined in your code | Bulk API 2.0 rejects parent-to-child subqueries and `TYPEOF` (`api_asynch L2892–2896`); PK chunking needs subquery-free SOQL (`api_asynch L7147`) |
| Result must be FLS-clean for an untrusted caller | `WITH USER_MODE`, or `Security.stripInaccessible` on the parent list | `stripInaccessible` strips inaccessible fields "from query and subquery results" (`apexdev L11940–11942`; subquery example `L12160–12178`) |

---

## Recommended Workflow

1. **Resolve the relationship names before writing any SOQL.** For child-to-parent, read the field's "Relationship Name" in the Object Reference (`Contact.AccountId` → `Account`) or call `DescribeFieldResult.getRelationshipName()`. For parent-to-child, take the child relationship name from `DescribeSObjectResult.getChildRelationships()` → `ChildRelationship.getRelationshipName()`, never the object API name. Record whether any field is polymorphic with `isNamePointing()`.
2. **Pick the shape using the Decision Guidance table above,** then run `references/gotchas.md` § 3 and § 8 against the choice: how many children per parent, and is this going into a Batch `start()`?
3. **Write the query inside a selector, not inline in the handler.** Extend `templates/apex/BaseSelector.cls` and add one method per relationship shape — `AccountHierarchySelector` in `references/code-examples.md` is the worked version, with child-to-parent, parent-to-child, `TYPEOF` on `Task.What`, and a semi-join. Use `userMode()` from the base class; on a class at API 67.0+ never write `WITH SECURITY_ENFORCED`.
4. **Read children with the accessor that matches the query's type** — typed `parent.Children__r` for a concretely typed query, `getSObjects(name)` for a generic `SObject` — and guard the collection before iterating, as the guide does at `apexdev L11719–11721`. Never assign or `.size()` a child set inside a SOQL for loop.
5. **Write the test class from `references/code-examples.md`,** building the parent/child/grandchild graph with `templates/apex/tests/TestDataFactory.cls`. Assert every shape the selector returns, and include one parent with zero children — that case is the one the shipped code usually has never executed.
6. **Run the checker over the source tree:** `python3 scripts/check_apex_soql_relationship_queries.py --manifest-dir force-app/main/default/classes`. It flags `__c` used where a traversal was intended, over-deep dot chains, subquery count and nesting, unguarded child iteration, SOQL in loops, and `WITH SECURITY_ENFORCED` on a class at API 67.0+.
7. **Verify governor cost, not just correctness.** Assert on `Limits.getQueries()` for the top-level count and `Limits.getAggregateQueries()` / `Limits.getLimitAggregateQueries()` for the subquery pool — subqueries are charged against that separate 3× budget (`apexdev L19613–19616`), so a query that looks like "one query" can still exhaust it.

---

## Review Checklist

- [ ] Every relationship token in the query is a relationship name (`Account`, `Contacts`, `MyRel__r`), never an object API name (`MyRel__c`)
- [ ] Child access uses typed `parent.Children__r` for typed queries, `getSObjects(name)` only for generic `SObject` rows
- [ ] The child collection is guarded before iteration, and a zero-children parent is covered by a test
- [ ] No child set is assigned to a variable or `.size()`-ed inside a SOQL for loop (200-child boundary)
- [ ] Batch `start()` returns a QueryLocator with no relationship subquery
- [ ] `TYPEOF` appears only in the SELECT clause; polymorphic filtering uses `.Type`
- [ ] A polymorphic reference is assigned to a correctly typed variable before being passed to a method
- [ ] Query count and the aggregate-query pool are both asserted, not just the result contents
- [ ] Security clause matches the class `apiVersion` — `WITH USER_MODE` at 67.0+, never `WITH SECURITY_ENFORCED`
- [ ] No Bulk API or PK-chunking code path shares a SOQL string that contains a subquery
- [ ] Any FROM-clause alias avoids SOQL reserved words (`in`, `or`, `not`, and the rest of the keyword list)

---

## Salesforce-Specific Gotchas

Full detail, each with **What happens / When it occurs / How to avoid**, is in `references/gotchas.md`. The five that most often reach production:

1. **`Aggregate query has too many rows for direct assignment, use FOR loop`** — assigning or `.size()`-ing a 200+ child set inside a SOQL for loop (`apexdev L10078–10088`). Iterate instead.
2. **A Batch `start()` subquery silently halves throughput** — a QueryLocator carrying a relationship subquery drops the job onto the non-chunking implementation (`apexdev L17796–17803`).
3. **Subqueries are charged to a separate query pool** — each parent-child relationship counts as an extra query against a 3× budget read from `Limits.getLimitAggregateQueries()` (`apexdev L19613–19616`).
4. **Bulk API 2.0 rejects parent-to-child subqueries and TYPEOF** (`api_asynch L2892–2896`), and PK chunking refuses any query containing a subquery (`api_asynch L7147`). Child-to-parent traversal is supported. Do not code against an invented status-code string.
5. **A polymorphic reference must be typed before it crosses a method boundary** — "you must assign the referenced sObject that the query returns to a variable of the appropriate type before you can pass it to another method" (`apexdev L9797–9798`).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Selector class + `-meta.xml` | `AccountHierarchySelector extends BaseSelector` with one method per relationship shape |
| Service class | Consumes the shapes with guarded child access and typed polymorphic handling |
| Apex test class | Parent/child/grandchild graph from `TestDataFactory`, asserting each shape plus the empty-children case |
| `package.xml` + deploy order | Deployable manifest and the order templates must land in |
| Checker run | `check_apex_soql_relationship_queries.py` findings over the source tree |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are about to write the class — the `AccountHierarchySelector`, the consuming service, the test class, `-meta.xml`, `package.xml`, deploy order and verification |
| `references/gotchas.md` | A relationship query returns wrong or truncated data rather than throwing, or you are reviewing someone else's traversal |
| `references/examples.md` | You want the worked end-to-end scenarios: subquery in a trigger, `TYPEOF` on `Task.WhatId`, deep child-to-parent, and the SOQL-for-loop boundary |
| `references/llm-anti-patterns.md` | The query was AI-generated, or you are prompting an assistant to write relationship SOQL |
| `references/well-architected.md` | You need the pillar framing, the architectural trade-offs, or the source behind a specific claim |

---

## Related Skills

- `apex/soql-fundamentals` — use for the SELECT/WHERE/ORDER BY/LIMIT baseline before layering relationship traversal on it.
- `apex/apex-aggregate-queries` — use when you need counts or sums per parent instead of the child rows; owns `GROUP BY`, `COUNT()`, `HAVING` and SELECT-list field aliasing.
- `apex/apex-polymorphic-soql` — use when polymorphic handling itself is the problem rather than one `TYPEOF` inside a relationship query.
- `apex/apex-design-patterns` — owns the selector layer; use it when the question is which class the query belongs in, not how to write it.
- `apex/apex-collections-patterns` — owns grouping, keying and `Map` construction *after* the query returns.
- `apex/apex-cpu-and-heap-optimization` — use when the shape is already right and the transaction still exceeds CPU or heap.
- `apex/soql-security` — owns `WITH USER_MODE` depth, sharing enforcement and FLS on query results.
- `apex/apex-stripinaccessible-and-fls-enforcement` — use when subquery fields must be stripped rather than the query failing.
- `apex/apex-dynamic-soql-binding-safety` — use when the relationship name or object is concatenated into the query string at runtime.
- `apex/batch-apex-patterns` — use when the QueryLocator design, scope size, and chunking behaviour are the focus.
- `apex/apex-dml-patterns` — use when the relationship query results drive insert/update/delete operations.
- `admin/lookup-and-relationship-design` — owns whether the relationship should be a lookup or master-detail in the first place.
