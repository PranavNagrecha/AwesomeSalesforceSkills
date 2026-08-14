# Examples — Apex Polymorphic SOQL

## Example 1: `TYPEOF` projection with a safe Apex dispatcher

**Context:** A daily digest summarises each rep's open Tasks. The summary line differs by what the Task is attached to: Accounts show industry, Opportunities show amount and stage, Cases show priority, and anything else shows just a name.

**Problem:** Four separate queries burn four of the 100 SOQL queries per transaction and force four passes over the same result set. Doing it in one flat query and reading `((Opportunity) t.What).Amount` throws `System.SObjectException: SObject row was retrieved via SOQL without querying the requested field` the moment a row's `What` is an Account, because `Amount` was never selected for that row.

**Solution:**

```apex
public with sharing class ActivityDigestSelector {

    public List<Task> openTasksFor(Set<Id> ownerIds) {
        return [
            SELECT Id, Subject, ActivityDate, WhatId,
                   TYPEOF What
                       WHEN Account     THEN Name, Industry
                       WHEN Opportunity THEN Name, Amount, StageName
                       WHEN Case        THEN CaseNumber, Priority
                       ELSE Id, Name
                   END
            FROM Task
            WHERE OwnerId IN :ownerIds
              AND IsClosed = false
              AND ActivityDate <= :Date.today().addDays(7)
            ORDER BY ActivityDate
            LIMIT 2000
        ];
    }
}
```

```apex
public with sharing class ActivityDigestFormatter {

    public String describe(Task t) {
        if (t.What == null) {
            return t.Subject + ' (no related record)';
        }
        if (t.What instanceof Account) {
            Account a = (Account) t.What;
            return t.Subject + ' — ' + a.Name + ' [' + a.Industry + ']';
        }
        if (t.What instanceof Opportunity) {
            Opportunity o = (Opportunity) t.What;
            return t.Subject + ' — ' + o.Name + ' ' +
                   o.StageName + ' ' + String.valueOf(o.Amount);
        }
        if (t.What instanceof Case) {
            Case c = (Case) t.What;
            return t.Subject + ' — Case ' + c.CaseNumber + ' (' + c.Priority + ')';
        }
        // ELSE branch: only Id and Name were projected. Nothing else is readable.
        return t.Subject + ' — ' + String.valueOf(t.What.get('Name'));
    }
}
```

**Why it works:** One query, per-type field projection, and an `instanceof` guard before every cast — which is what the Apex Developer Guide requires when it says "you must assign the referenced sObject that the query returns to a variable of the appropriate type before you can pass it to another method." The `ELSE Id, Name` branch means a newly Activity-enabled custom object degrades to a readable line instead of producing a row whose fields are all unreadable. The `OwnerId IN :ownerIds` and dated `ActivityDate` bound keep the query selective — `What.Type` alone would not.

---

## Example 2: Flat query plus partition, for the cases `TYPEOF` cannot serve

**Context:** The same digest data is needed inside a subquery on Account (`SELECT Name, (SELECT ... FROM Tasks) FROM Account`) and as a Bulk API extract for the analytics warehouse.

**Problem:** Neither is legal with `TYPEOF`. "TYPEOF is only allowed in the SELECT clause of a query", "TYPEOF isn't allowed in the SELECT clause of a semi-join query", and "TYPEOF can't be used in SOQL used in Bulk API." A query that works in the Apex service cannot simply be pasted into either context.

**Solution:** Project the common parent fields flat, then partition by concrete type in Apex and re-query only the types you need detail for.

```apex
public with sharing class PolymorphicPartitioner {

    /** Group WhatIds by their concrete SObjectType, without a second query. */
    public static Map<Schema.SObjectType, Set<Id>> partition(List<Task> tasks) {
        Map<Schema.SObjectType, Set<Id>> byType =
            new Map<Schema.SObjectType, Set<Id>>();
        for (Task t : tasks) {
            if (t.WhatId == null) { continue; }
            Schema.SObjectType token = t.WhatId.getSObjectType();
            if (!byType.containsKey(token)) {
                byType.put(token, new Set<Id>());
            }
            byType.get(token).add(t.WhatId);
        }
        return byType;
    }
}
```

```apex
// Flat form — legal in subqueries and Bulk API. Name and Type are readable
// for every target because they are common to the parent.
List<Task> tasks = [
    SELECT Id, Subject, WhatId, What.Name, What.Type
    FROM Task
    WHERE WhatId IN :seedIds
      AND CreatedDate = LAST_N_DAYS:30
];

Map<Schema.SObjectType, Set<Id>> byType = PolymorphicPartitioner.partition(tasks);

Map<Id, Opportunity> opps = new Map<Id, Opportunity>([
    SELECT Id, Amount, StageName
    FROM Opportunity
    WHERE Id IN :byType.get(Opportunity.SObjectType)
]);
```

**Why it works:** `Id.getSObjectType()` resolves the concrete type from the key prefix with no query and no describe call, so partitioning is free. Each per-type re-query is one SOQL statement against an indexed Id set, which stays selective at Activity-table volume. Discovering the legal target list ahead of time is a describe call, not a guess:

```apex
List<Schema.SObjectType> possibleTargets =
    Task.SObjectType.getDescribe().fields.getMap()
        .get('WhatId').getDescribe().getReferenceTo();
```

---

## Anti-Pattern: `WHERE What.Type = 'Account'` as the only filter

**What practitioners do:** Reach for the type filter as the primary predicate — `SELECT Id, What.Name FROM Task WHERE What.Type = 'Account'` — reasoning that it narrows the result set enough.

**What goes wrong:** `.Type` is a filter, not an index. Against a production Activity table the optimizer has nothing selective to drive from, and the query fails with `System.QueryException: Non-selective query against large object type`. In Batch Apex the same query is accepted as the start scope and then times out mid-run, which is worse: it fails after partially processing.

**Correct approach:** Lead with an indexed predicate and let the type filter narrow what comes back.

```apex
SELECT Id, What.Name, What.Type
FROM Task
WHERE WhatId IN :accountIds            // indexed, selective
  AND CreatedDate = LAST_N_DAYS:90     // bounded
  AND What.Type = 'Account'            // narrows, does not drive
```

If you genuinely need every Task of one target type across the whole org, that is an extract job — Bulk API with a date-chunked query — not a synchronous SOQL statement. And note that Bulk API cannot use `TYPEOF` at all, so the extract must use the flat form above.
