# Worked Example — Tracing One Missing Record Through Every Stage

**Report:** "Searching for `Northwind` in our service console never shows the Northwind Logistics project record, but the Account and its Contacts show up."

The console runs this Apex as the logged-in agent:

```apex
List<List<SObject>> hits = [
    FIND :term IN ALL FIELDS
    RETURNING Account(Id, Name), Contact(Id, Name), Lead(Id, Name), Case(Id, Subject),
              Opportunity(Id, Name), Contract(Id, ContractNumber), Asset(Id, Name),
              Order(Id, OrderNumber), Campaign(Id, Name), Solution(Id, SolutionName),
              Product2(Id, Name), Project__c(Id, Name)
];
```

## Stage-by-stage check

| # | Stage | Check | Finding |
|---|---|---|---|
| 1 | Searchability | Retrieve `Project__c` metadata; read `<enableSearch>` | `false`: the object was created by a deployment that never set it, and new custom objects default to search off |
| 2 | Indexing | When were the records loaded? | Loaded last week, so the 15-minute-plus indexing delay is not the cause |
| 3 | Term scan | Is `Northwind` a broad term in this org? | 3,400 records contain it; the engine considers a maximum of 2,000 for the term |
| 4 | Per-object split | n = 12 objects | min(2,000/12, 250) = 166 per object |
| 5 | Permission filter | Does the agent have View All Data? Can they read the project? | No View All Data; the agent's role can read the project via a sharing rule |
| 6 | Term length | Length of the bound `term` | 9 characters; thresholds (4,000 / 10,000) not involved |

Stage 1 alone explains the report: no SOSL query can return `Project__c` rows until search is enabled. Stages 3 and 4 explain why the fix should not stop there: even with search on, a 12-object search with a broad term gives each object at most 166 slots out of a 2,000-record scan.

## Fix

1. Deploy the object with search enabled (merge into the retrieved file):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- excerpt: objects/Project__c/Project__c.object-meta.xml, search element only -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableSearch>true</enableSearch>
</CustomObject>
```

2. Split the console search: a primary search over the four objects agents use most, each with `ORDER BY` so per-object order is predictable, and a second, single-object search on `Project__c` when the agent picks the Projects tab:

```apex
List<List<SObject>> projects = [
    FIND :term IN NAME FIELDS
    RETURNING Project__c(Id, Name, Status__c WHERE Status__c != 'Archived' ORDER BY Name)
];
```

A single-object search with WHERE or ORDER BY can return up to 2,000 project rows, instead of 166.

3. Re-test as the agent, not as an admin, after the next indexing cycle.

## What the arithmetic looks like at other object counts

| Objects (n) | 2,000 / n | Per-object cap = min(2,000/n, 250) |
|---|---|---|
| 1 | 2,000 | 250 (2,000 with WHERE or ORDER BY) |
| 2 | 1,000 | 250 |
| 8 | 250 | 250 |
| 9 | 222 | 222 |
| 12 | 166 | 166 |
| 16 | 125 | 125 |
