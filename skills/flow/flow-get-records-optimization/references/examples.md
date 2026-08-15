# Examples — Get Records Optimization

Worked examples for the four things that actually make a Get Records expensive:
how many times it runs, how many rows it touches, how many fields it stores, and
whether the filter is selective.

The budget every one of these is measured against, per **transaction** (not per
element, not per interview):

| Governor | Synchronous | Asynchronous |
|---|---|---|
| SOQL queries | 100 | 200 |
| SOQL query rows | 50,000 | 50,000 |
| CPU time | 10,000 ms | 60,000 ms |
| Heap | 6 MB | 12 MB |

A record-triggered or schedule-triggered flow runs one interview per record and
the platform batches those interviews — up to 200 — into a single transaction.
So the number to compute is always `per-interview cost × batch size`, and a
single Get Records in the per-record path is 200 queries at a full batch.

Which column those 200 are measured against follows from the flow type. A
record-triggered flow runs in the triggering transaction and gets the synchronous
100 — so 200 queries fails. A schedule-triggered flow gets the asynchronous 200
from runtime version 61.0 onward (*Improve Scheduled Flow Performance with Updated
Limits*), so the same 200 queries fit exactly, leaving nothing for the other
automation on the object. Everything below that reduces a query count is worth
doing in either column; what changes is whether "200 queries" is a failure or a
design with no margin. DML statements are 150 in both columns.

---

## Example 1: Wrong vs Right — Lifting the Query Out of the Loop

**Wrong:**

```xml
<loops>
    <name>Loop_Cases</name>
    <label>Loop Cases</label>
    <locationX>176</locationX>
    <locationY>278</locationY>
    <collectionReference>caseCollection</collectionReference>
    <iterationOrder>Asc</iterationOrder>
    <nextValueConnector>
        <targetReference>Get_Account_For_Case</targetReference>
    </nextValueConnector>
</loops>

<recordLookups>
    <name>Get_Account_For_Case</name>
    <label>Get Account For Case</label>
    <locationX>352</locationX>
    <locationY>278</locationY>
    <connector>
        <targetReference>Assign_Account_Name</targetReference>
    </connector>
    <assignNullValuesIfNoRecordsFound>true</assignNullValuesIfNoRecordsFound>
    <filterLogic>and</filterLogic>
    <filters>
        <field>Id</field>
        <operator>EqualTo</operator>
        <value>
            <elementReference>Loop_Cases.AccountId</elementReference>
        </value>
    </filters>
    <getFirstRecordOnly>true</getFirstRecordOnly>
    <object>Account</object>
    <storeOutputAutomatically>true</storeOutputAutomatically>
</recordLookups>
```

200 iterations, 200 queries. And because the flow itself is batched at 200
interviews, that ceiling arrives long before the loop does.

**Right:**

```xml
<!-- 1. Collect the parent Ids in an Assignment inside the loop. -->
<assignments>
    <name>Collect_Account_Ids</name>
    <label>Collect Account Ids</label>
    <locationX>352</locationX>
    <locationY>278</locationY>
    <assignmentItems>
        <assignToReference>accountIds</assignToReference>
        <operator>Add</operator>
        <value>
            <elementReference>Loop_Cases.AccountId</elementReference>
        </value>
    </assignmentItems>
    <connector>
        <targetReference>Loop_Cases</targetReference>
    </connector>
</assignments>

<!-- 2. ONE query, after the loop, with an In filter. -->
<recordLookups>
    <name>Get_Accounts</name>
    <label>Get Accounts</label>
    <locationX>528</locationX>
    <locationY>278</locationY>
    <assignNullValuesIfNoRecordsFound>true</assignNullValuesIfNoRecordsFound>
    <filterLogic>and</filterLogic>
    <filters>
        <field>Id</field>
        <operator>In</operator>
        <value>
            <elementReference>accountIds</elementReference>
        </value>
    </filters>
    <getFirstRecordOnly>false</getFirstRecordOnly>
    <object>Account</object>
    <queriedFields>Id</queriedFields>
    <queriedFields>Name</queriedFields>
    <storeOutputAutomatically>true</storeOutputAutomatically>
</recordLookups>
```

**Why it works:** one query, filtered on `Id` — a standard-indexed field — with
an `In` list. `Id` is the cheapest filter the platform has.

**The part people stop before:** you now have a *collection* of Accounts and a
collection of Cases, and matching them still requires a second loop. Flow has no
map. The idiomatic shape is a nested loop, which is O(n×m) in CPU but zero
additional queries — and CPU is a far more generous budget than SOQL. For large
n×m, the alternative is an invocable Apex helper that does the join in a real
`Map`, and that trade should be made on measured CPU, not on instinct.

---

## Example 2: Selectivity, With the Numbers

**Context:** A Get Records on a 4-million-row custom object filters on
`Status__c = 'Open'`, which matches about 900,000 rows.

**Problem:** The filter *looks* narrow — one value out of eight. It is not
selective, and the query does a full table scan.

**Solution:** Understand what the optimizer means by selective.

| Index type | Threshold | Cap |
|---|---|---|
| Standard index (`Id`, `Name`, `OwnerId`, `CreatedDate`, `SystemModstamp`, lookup and master-detail foreign keys, `CreatedById`, `LastModifiedById`) | 30% of the first million targeted records, 15% beyond | 1,000,000 records |
| Custom index (including fields marked Unique or External Id) | 10% of the first million targeted records, 5% beyond | 333,333 records |

`Status__c = 'Open'` returning 900,000 rows blows past the 333,333 cap even with
a custom index. Adding an index to that field will not make the query selective.

What does work:

```xml
<filters>
    <field>OwnerId</field>
    <operator>EqualTo</operator>
    <value>
        <elementReference>$User.Id</elementReference>
    </value>
</filters>
<filters>
    <field>Status__c</field>
    <operator>EqualTo</operator>
    <value>
        <stringValue>Open</stringValue>
    </value>
</filters>
```

Leading with `OwnerId` — standard-indexed, and for one user a tiny fraction of 4
million — makes the query selective, and `Status__c` then filters the small
result set. The order in the metadata is not what drives the optimizer, but
*having* a genuinely selective filter in the set is.

**How to check rather than guess:** Developer Console → Query Plan tool. A Cost
above 1 means the filter is not selective and a full table scan will be used.
Run the equivalent SOQL there before assuming a Flow filter is fine.

**Why this matters more in Flow than in Apex:** an Apex developer who writes a
non-selective query on a large object gets a
`QueryException: Non-selective query against large object type` and finds out
immediately. In a Flow the same query is often merely slow, and slowness inside a
200-interview batch surfaces as a CPU limit somewhere unrelated.

---

## Example 3: What "Store All Fields" Actually Costs

**Context:** A Get Records on Contact with automatic field storage, returning
2,000 records.

**Problem:** Automatic storage retrieves every field on the object. On an org
with 250 Contact fields that is 500,000 field values held in the interview's
memory, most of which no element reads.

**Solution:** Name the fields.

```xml
<recordLookups>
    <name>Get_Contacts</name>
    <label>Get Contacts</label>
    <locationX>176</locationX>
    <locationY>278</locationY>
    <assignNullValuesIfNoRecordsFound>true</assignNullValuesIfNoRecordsFound>
    <filterLogic>and</filterLogic>
    <filters>
        <field>AccountId</field>
        <operator>In</operator>
        <value>
            <elementReference>accountIds</elementReference>
        </value>
    </filters>
    <getFirstRecordOnly>false</getFirstRecordOnly>
    <object>Contact</object>
    <queriedFields>Id</queriedFields>
    <queriedFields>Email</queriedFields>
    <queriedFields>AccountId</queriedFields>
    <storeOutputAutomatically>false</storeOutputAutomatically>
    <outputReference>contactCollection</outputReference>
</recordLookups>
```

**Why it works:** heap is 6 MB synchronous, 12 MB asynchronous, and a screen
flow additionally serializes its variables between screens — so a fat collection
is paid for on every screen transition, not once.

**The trade, stated honestly:** naming fields makes the flow brittle in a
specific way. Add a field to a downstream element and forget to add it to
`queriedFields` and you get a null rather than an error. `storeOutputAutomatically`
exists because it removes that failure mode. Name fields on large collections
where the heap cost is real; accept automatic storage on single-record lookups
where it is not.

---

## Example 4: Sort and Limit for "Top N"

**Context:** "Show the agent the three most recent Cases for this Account."

**Wrong:** get all Cases for the Account sorted descending, then use a loop and a
counter to take the first three.

**Right:**

```xml
<recordLookups>
    <name>Get_Recent_Cases</name>
    <label>Get Recent Cases</label>
    <locationX>176</locationX>
    <locationY>278</locationY>
    <assignNullValuesIfNoRecordsFound>true</assignNullValuesIfNoRecordsFound>
    <filterLogic>and</filterLogic>
    <filters>
        <field>AccountId</field>
        <operator>EqualTo</operator>
        <value>
            <elementReference>$Record.AccountId</elementReference>
        </value>
    </filters>
    <getFirstRecordOnly>false</getFirstRecordOnly>
    <limit>3</limit>
    <object>Case</object>
    <queriedFields>Id</queriedFields>
    <queriedFields>CaseNumber</queriedFields>
    <queriedFields>Subject</queriedFields>
    <queriedFields>CreatedDate</queriedFields>
    <sortField>CreatedDate</sortField>
    <sortOrder>Desc</sortOrder>
    <storeOutputAutomatically>true</storeOutputAutomatically>
</recordLookups>
```

**Why it works:** the sort and the limit are pushed into the query, so three rows
come back rather than however many the Account has. `AccountId` is a foreign key
and therefore standard-indexed; `CreatedDate` is an audit field and also standard
-indexed, which keeps the sort cheap.

**The variant that is not cheap:** sorting on a non-indexed custom text field.
The sort still happens server-side, but the optimizer has no index to walk in
order, so it works from the filtered set. That is fine when the filter is
selective and expensive when it is not — which is another way of saying the
selectivity work in Example 2 is what makes the sort affordable, not the limit.

---

## Example 5: Reuse Across Screens Instead of Re-Querying

**Context:** A four-screen intake flow. Screens 2 and 4 both display the running
user's manager.

**Wrong:** a Get Records on User before each screen. Two queries for one fact
that cannot change during the interview.

**Right:** one Get Records before the first screen, stored in a variable
referenced by both.

**Why it works:** it halves the query count for that fact, and in a screen flow
the win compounds — a paused interview serializes its variables, so a re-query
after resume also re-pays whatever the query cost, while a stored variable is
already there.

**The genuine counter-argument:** a value cached at the start of a long screen
flow can be stale by the time screen 4 renders, and for a paused-and-resumed
interview it can be days stale. Cache facts that cannot change within the
interview (the running user's manager, an org-wide setting, a Custom Metadata
row) and re-query facts that can (record ownership, status, anything another user
edits). "Query once" is not a universal rule; "know which of the two this is" is.

---

## Anti-Pattern: Leading-Wildcard `Contains` on a Large Object

**What practitioners do:** Build a search screen whose Get Records filters
`Name` with the `Contains` operator against user input.

**What goes wrong:** `Contains` produces a leading wildcard, which no index can
serve. On a large object it is a full table scan every keystroke-driven
re-render, and it is slow in exactly the situation where a user is waiting.

**Correct approach:** `StartsWith` can use an index and is usually what the user
meant anyway. Where true "contains" semantics are required, that is a search
problem rather than a query problem — SOSL, or a pre-computed normalized field
that a `StartsWith` filter can hit. And bound it: a search screen that can return
thousands of rows should set a `limit` and tell the user the result was
truncated.

---

## Anti-Pattern: Using the Fault Path for "No Records Found"

**What practitioners do:** Wire a fault connector off the Get Records to a "not
found" branch.

**What goes wrong:** It never fires. Zero rows is a *successful* query — the
element takes its normal connector with a null result. The fault connector fires
only on a genuine platform exception. The "not found" branch is dead code, and
the flow proceeds holding a null that fails several elements later with a much
less informative error.

**Correct approach:** a Decision immediately after the Get, testing the record
variable with the `IsNull` operator, with `assignNullValuesIfNoRecordsFound` set
to `true` so the variable is reliably null rather than holding a value from a
previous loop iteration. Keep the fault connector for real exceptions and point
it at a logger — see `flow/flow-interview-debugging`.

---

## Anti-Pattern: Optimizing the Flow When the Transaction Is the Problem

**What practitioners do:** A flow throws `Too many SOQL queries: 101`. The author
counts three Get Records elements in the flow, cannot reconcile that with 101,
and starts merging queries that were already fine.

**What goes wrong:** the budget is per transaction and shared. An Apex trigger, a
second record-triggered flow on the same object, and a managed package can each
have spent most of the 100 before this flow's first element ran. Three elements
in a 200-interview batch is also 600 queries on its own — the same number is
reachable two entirely different ways.

**Correct approach:** compute `per-interview cost × batch size` first. If that
number is under the limit, the problem is elsewhere in the transaction: inventory
every automation on the object and read the debug log's cumulative limits
section, which attributes the spend. Optimizing a flow that was not the consumer
wastes the effort and leaves the failure in place.
