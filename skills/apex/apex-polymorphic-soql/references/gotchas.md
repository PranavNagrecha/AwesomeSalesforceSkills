# Gotchas — Apex Polymorphic SOQL

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `TYPEOF` is legal only in the outer SELECT clause — and the restriction list is long

**What happens:** A query that runs fine in the Developer Console Query Editor fails to compile, or fails at run time, when moved into a subquery, an aggregate, a PushTopic, or Bulk API. The SOQL and SOSL Reference lists the constraints explicitly, and every one of them catches somebody:

- "TYPEOF is only allowed in the SELECT clause of a query."
- "TYPEOF isn't allowed in queries that don't return objects, such as COUNT() and aggregate queries."
- "GROUP BY, GROUP BY ROLLUP, GROUP BY CUBE, and HAVING aren't allowed in queries that use TYPEOF."
- "TYPEOF expressions can't be nested."
- "TYPEOF isn't allowed in the SELECT clause of a semi-join query."
- "TYPEOF can't be used in SOQL queries that are the basis of Streaming API PushTopics."
- "TYPEOF can't be used in SOQL used in Bulk API."

**When it occurs:** Most often when working code is refactored — moved into a `SELECT (SELECT ... FROM Tasks)` subquery on Account, or reused as a PushTopic query, or handed to a Bulk API extract job.

**How to avoid:** Reach for `TYPEOF` in the outer SELECT of ordinary Apex/REST queries only. For subqueries, aggregates, PushTopics, and Bulk API, use the flat `What.Type` / `What.Name` form and dispatch in Apex. `TYPEOF` is also gated on API version — it "is available in API version 26.0 and later" — so a class pinned to an ancient `apiVersion` in its `.cls-meta.xml` will not accept it.

---

## Gotcha 2: Fields outside the matched `WHEN` branch are not on the returned sObject

**What happens:** A query projects `WHEN Account THEN Industry WHEN Opportunity THEN Amount`, and Apex then reads `((Opportunity) t.What).Amount` on a row whose `What` is an Account. The field was never selected for that row, so the read throws `System.SObjectException: SObject row was retrieved via SOQL without querying the requested field` — the same error you get from any unselected field, which sends people hunting for a missing field in the SELECT list that is already there.

**When it occurs:** Any dispatch loop that casts without first checking the concrete type, and any code that assumes the `ELSE` branch covered a field it did not name.

**How to avoid:** Check the type before you cast. The Apex Developer Guide notes you "can use the `instanceof` keyword to determine the object type", and that "you must assign the referenced sObject that the query returns to a variable of the appropriate type before you can pass it to another method."

```apex
for (Task t : tasks) {
    if (t.What == null) { continue; }
    if (t.What instanceof Account) {
        Account a = (Account) t.What;
        handleAccount(a.Industry);
    } else if (t.What instanceof Opportunity) {
        Opportunity o = (Opportunity) t.What;
        handleOpportunity(o.Amount);
    } else {
        handleOther(t.What.Id);          // only fields in the ELSE branch are safe here
    }
}
```

---

## Gotcha 3: `.Type` is a filter, not an index — it does not make a query selective

**What happens:** `SELECT Id FROM Task WHERE What.Type = 'Account'` runs acceptably in a sandbox with 5,000 Tasks and then, against a production Activity table with tens of millions of rows, fails with `System.QueryException: Non-selective query against large object type`. Nothing about the query changed; the row count did.

**When it occurs:** Any Activity-, Feed-, or ContentDocumentLink-sourced query in an org with real history. Activity tables are among the largest in most orgs and are the ones most often queried by type.

**How to avoid:** Pair the type filter with something the platform can index — an Id set, a bounded `ActivityDate`/`CreatedDate` range, or a selective lookup. Treat `.Type` as a post-filter that narrows results, never as the thing that makes the query runnable.

```apex
// Selective: Id set drives the query, Type narrows the result.
List<Task> tasks = [
    SELECT Id, Subject, What.Name, What.Type
    FROM Task
    WHERE WhatId IN :accountIds
      AND ActivityDate >= :Date.today().addDays(-90)
];
```

---

## Gotcha 4: The describe map lets you discover targets, but the target list is not stable

**What happens:** A "handles every WhatId type" dispatcher is written against the five objects present when it was authored. Someone enables Activities on a new custom object, and rows start arriving whose type has no branch. Without an `ELSE`, those rows return no projected fields at all and the handler silently skips them.

**When it occurs:** Long-lived utilities in orgs where object configuration keeps changing — which is every org.

**How to avoid:** Always write the `ELSE` branch and make it meaningful (at minimum `Id`, and `Name` where the targets share it). Discover the real target list at run time rather than hard-coding it:

```apex
List<Schema.SObjectType> targets =
    Task.SObjectType.getDescribe().fields.getMap()
        .get('WhatId').getDescribe().getReferenceTo();
```

Log anything that lands in `ELSE` so a new target type surfaces as an observation rather than as missing data.

---

## Gotcha 5: `Who` and `What` have fixed, different target sets, and `Owner` is polymorphic too

**What happens:** Code filters `WHERE Who.Type = 'Account'` and gets zero rows forever, with no error. The SOQL reference defines the three documented polymorphic relationships by their semantics: `Who` "represents the person associated with the record" and is limited to Contacts or Leads; `What` "represents nonhuman objects that are associated with the record... where What can be an Account or a Solution, or any of another number of object types"; and `Owner` "represents the parent of the record" — for Tasks, owners "are either Calendars or Users."

**When it occurs:** Whenever someone reasons about `WhoId` and `WhatId` as interchangeable "related record" fields, and whenever a query assumes `OwnerId` is always a User — an assumption that breaks on Task and Event, where a Calendar owner is legal.

**How to avoid:** Treat the three as distinct fields with distinct target sets. Never filter `Who` by a non-person object, and null-guard `Owner.Name` dereferences on activity objects instead of assuming `Owner` resolves to a User.
