# Gotchas — SOQL Relationship Queries

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Two Different Child Accessors, and Only One of Them Is the Dynamic One

**What happens:** Code written against the wrong accessor either does not compile or adds casts for
no reason. `getSObjects('Contacts')` returns `SObject[]` and is documented as "primarily used with
dynamic DML to access values for associated objects, such as child relationships"
(`apexrefguide L233176–233178`). When the query already returns a concrete sObject type, the child
collection is reachable directly: the Apex Developer Guide's own bulkification example writes
`for (Line_Item__c li : inv.Line_Items__r)` (`apexdev L20254`), assigns a relationship straight to a
typed list — `List<IssueComments__x> comments = issue.IssueComments__r;` (`apexdev L29894`) — and
calls `.size()` on one (`apexdev L29908`).

**When it occurs:** A developer reads that `getSObjects()` is "the" way to read children and applies
it to a typed inline query, producing `(Contact) row` casts on every iteration. Or the reverse: a
`Database.query()` result is a generic `SObject`, typed access is unavailable, and the code will not
compile until `getSObjects()` is used.

**How to avoid:** Match the accessor to the query. Typed inline SOQL → read `parent.Children__r`
directly. Dynamic SOQL returning `SObject[]` → `getSObjects(relationshipName)`. Either way, guard the
collection before iterating: the guide's dynamic sample does exactly that, under the comment
"Prevent a null relationship from being accessed" (`apexdev L11719–11721`).

UNVERIFIED (2026-09-05): earlier editions of this skill stated that `getSObjects()` returns `null`
rather than an empty list and that a direct cast of the relationship throws `TypeException`. Neither
statement appears in apexdev.txt or apexrefguide.txt, and the second is contradicted by the typed
samples cited above. The corpus shows the guard, not the rule behind it. Write
`if (children == null || children.isEmpty()) { continue; }` — correct under either behaviour — and do
not assert the null-vs-empty rule as documented.

---

## Gotcha 2: Custom __r vs Standard Relationship Name Confusion

**What happens:** Using the object API name (`My_Custom_Child__c`) instead of the child relationship name (`My_Custom_Children__r`) inside a subquery causes a compile-time parse error: `No such column 'My_Custom_Child__c' on entity 'Account'`. Using the wrong name in `getSObjects()` at runtime throws a `System.SObjectException`.

**When it occurs:** Most common when developers copy a flat SOQL query and try to embed it as a subquery, or when a custom object's plural label differs from its singular API name.

**How to avoid:** Look up the child relationship name on the parent object in Setup > Object Manager > [Parent Object] > Fields & Relationships > [Lookup Field] > Child Relationship Name. That exact value (with `__r` appended for custom) is what goes in both the SOQL subquery parentheses and the `getSObjects()` string argument. Standard objects use the registered child relationship name visible in the Schema Explorer — e.g., `Contacts`, `Opportunities`, `Cases`.

---

## Gotcha 3: Subqueries Are Charged to a Separate Query Pool, Not the Top-Level One

**What happens:** A query that reads like "one SOQL statement" is charged more than once. The Apex
Developer Guide is explicit: "In a SOQL query with parent-child relationship subqueries, each
parent-child relationship counts as an extra query. These types of queries have a limit of three
times the number for top-level queries. The limit for subqueries corresponds to the value that
`Limits.getLimitAggregateQueries()` returns. The row counts from these relationship queries
contribute to the row counts of the overall code execution." (`apexdev L19613–19616`). Top-level
queries are capped at 100 synchronous / 200 asynchronous (`apexdev L19544`) and total rows retrieved
by SOQL at 50,000 in both modes (`apexdev L19546`) — so a wide result set exhausts rows long before
it exhausts statements.

**When it occurs:** A handler that loops parents and calls a five-subquery selector method per chunk.
The developer counts five statements against the 100-query budget and concludes there is headroom;
the real constraint is the aggregate-query pool, which is being charged 25.

**How to avoid:** Assert on `Limits.getAggregateQueries()` against `Limits.getLimitAggregateQueries()`
in tests, not on a hardcoded number, and cap child rows per parent with a subquery `LIMIT` so the
50,000-row budget survives a handful of unusually wide parents. If the requirement is a count or a sum
per parent rather than the rows themselves, an aggregate query is the cheaper shape — see
`apex/apex-aggregate-queries`.

---

## Gotcha 4: Bulk API Does Not Support Parent-to-Child Subqueries

**What happens:** SOQL with subqueries works in synchronous Apex, anonymous execution, and the standard REST API. When the same query string is used in a Bulk API job (e.g., via `Database.BatchQueryLocator` configured for Bulk API mode, or an external ETL tool using the Bulk API), Salesforce rejects the query at runtime with an error.

**When it occurs:** Batch Apex that calls `Database.getQueryLocator()` with a subquery and is executed by the platform's Bulk API executor path, or external tools (Data Loader, MuleSoft Bulk connector) using Bulk API mode.

**How to avoid:** For Bulk API code paths, issue a flat query for the parent records and a separate query for the child records using a parent ID filter. Join them in memory in Apex. Grounding: "Bulk API 2.0 doesn't support SOQL queries that include any of these items: ... Parent-to-child relationship queries. (Child-to-parent relationship queries are supported.)" (`api_asynch L2890–2896`), and PK chunking "works only with queries that don't include subqueries or conditions other than WHERE" (`api_asynch L7147`), so a subquery silently costs you chunking as well as the query itself. `ORDER BY` or `LIMIT` on a bulk query also disables PK chunking (`api_asynch L2888–2890`).

---

## Gotcha 5: Cross-Object Formula Fields Are Not Filterable in WHERE

**What happens:** A formula field on Contact that references `Account.Industry` (e.g., `Account_Industry_Formula__c`) cannot be used in a WHERE clause. Salesforce throws a `SOQL exception: field 'Account_Industry_Formula__c' can not be filtered in a WHERE clause` error at runtime.

**When it occurs:** When a developer tries to filter on a cross-object formula to avoid typing the dot-notation path, especially when the formula was created for display purposes.

**How to avoid:** Use the direct dot-notation traversal in the WHERE clause: `WHERE Account.Industry = 'Technology'`. Reserve formula fields for display and formula-based calculations, not query filtering.

UNVERIFIED (2026-09-05): the non-filterability of cross-object formula fields is documented on help.salesforce.com and in the SOQL and SOSL Reference; neither is fetchable, and the Object Reference records filterability per field rather than stating the general rule. The exact error text above is likewise unverified — read the runtime message rather than matching on it.

---

## Gotcha 6: TYPEOF Is SELECT-Only — Use `.Type` to Filter

**What happens:** `TYPEOF` is generally available (since API version 46.0, Summer '19 — the Developer Preview label applied only to earlier versions), so it needs no "is it enabled?" caveat. The real trap is that it is a **SELECT-clause-only** projection. Per the SOQL reference it is rejected in `WHERE`, in aggregate/`COUNT()` and `GROUP BY`/`HAVING` queries, in Bulk API SOQL, in Streaming API PushTopics, and in the SELECT list of a semi-join subquery. A query that tries to *filter* on a polymorphic type with `TYPEOF` fails to parse.

**When it occurs:** Attempting `WHERE TYPEOF ...`, running a `TYPEOF` query through the Bulk API, or expecting `TYPEOF` to work inside an aggregate/`GROUP BY` query.

**How to avoid:** Project per-type fields with `TYPEOF` in the SELECT clause only. To **filter** rows by polymorphic type, use the `.Type` qualifier instead — it compares against a plain string, has no API-version floor, and is the only legal option in the contexts above: `SELECT Id FROM Event WHERE What.Type IN ('Account', 'Opportunity')`. Once pinned to a single type, that type's fields are reachable by dot notation (`SELECT Id, Owner.Name FROM Event WHERE Owner.Type = 'User'`). Remember that a `.Type` filter silently excludes rows of other types rather than null-padding them.

---

## Gotcha 7: SOQL Reserved Words Are Rejected as Alias Names

**What happens:** Alias notation lets you name an object in the FROM clause (`FROM Contact c, c.Account a`) and reference it by that alias in SELECT and WHERE — an implicit join that filters on a parent without selecting its fields. But SOQL rejects its own reserved keywords as alias identifiers. A tempting short alias such as `in`, `or`, or `not` produces a parse error because it matches the reserved `IN`, `OR`, and `NOT` keywords.

**When it occurs:** Choosing terse, mnemonic aliases derived from an object's name (`Inventory__c in`, `Order or`), or generating aliases programmatically without screening them against the keyword list.

UNVERIFIED (2026-09-05): FROM-clause object alias notation and the SOQL reserved-word list are documented only in the SOQL and SOSL Reference, which is not in the offline corpus. `grep -n -i "alias notation" apexdev.txt` and a search for the keyword list return nothing in apexdev.txt, apexrefguide.txt or object_reference.txt — the Apex reserved-word list at `apexdev L45756` is the Apex language's, not SOQL's, and is a different set. Every SOQL example in the Apex guide uses plain dot notation, which resolves the same filters.

**How to avoid:** Screen every alias against the reserved list before using it: AND, ASC, DESC, EXCLUDES, FIRST, FROM, GROUP, HAVING, IN, INCLUDES, LAST, LIKE, LIMIT, NOT, NULL, NULLS, OR, SELECT, USING, WHERE, WITH. Single letters (`c`, `a`, `o`) and multi-letter tokens that aren't on the list are safe — `inv` instead of `in`, `ord` instead of `or`.


---

## Gotcha 8: `Aggregate query has too many rows for direct assignment, use FOR loop`

**What happens:** A parent-to-child query inside a **SOQL for loop** throws a `QueryException` the
moment a parent has 200 or more children — not on the query, but on the line that reads the child
collection. The Apex guide states it directly: "You can get a `QueryException` in a SOQL for loop
with the message `Aggregate query has too many rows for direct assignment, use FOR loop`. This
exception is sometimes thrown when accessing a large set of child records (200 or more) of a
retrieved sObject inside the loop, or when getting the size of such a record set."
(`apexdev L10078–10081`). The guide's failing lines are `List<Contact> contactList = acct.Contacts;`
and `Integer count = acct.Contacts.size();` (`apexdev L10087–10088`).

**When it occurs:** Only inside a SOQL for loop — the construct that chunks results through
`queryMore` to save heap. The identical read over a materialised `List<Account>` is fine, which is
why this never reproduces in a unit test that queries into a list first, and why it surfaces on the
one production Account with 400 Contacts.

**How to avoid:** Inside a SOQL for loop, iterate the children with a nested `for` instead of
assigning or sizing them — the guide's own correction (`apexdev L10093–10098`). If you need the
count, increment it in that loop, or ask an aggregate query for it. Watch the related trap in the
same section: `JSON.serialize()` on a parent inside a SOQL for loop will not carry the full child set,
because the loop "keep[s] only a subset of the record data in memory, [so] the complete sObject and
any subquery sObjects will not be available to obtain complete serialization" (`apexdev L10108–10110`).

---

## Gotcha 9: A Subquery in a Batch `start()` Silently Switches the Job to a Slower Engine

**What happens:** Nothing fails. The job runs, finishes, and takes far longer than an equivalent job
without the subquery. "Batch Apex jobs run faster when the start method returns a QueryLocator object
that doesn't include related records via a subquery. Avoiding relationship subqueries in a
QueryLocator allows batch jobs to run using a faster, chunked implementation. If the start method
returns an iterable or a QueryLocator object with a relationship subquery, the batch job uses a
slower, non-chunking, implementation." (`apexdev L17796–17800`). The guide names the exact shape that
triggers it: `SELECT Id, (SELECT id FROM Contacts) FROM Account` (`apexdev L17801`).

**When it occurs:** A developer moves a working synchronous selector method into `start()` to reuse
it. The selector is correct SOQL; the execution engine underneath changes.

**How to avoid:** Keep `start()` flat and query children inside `execute()` — "A better strategy is
to perform the subquery separately, from within the execute method, which allows the batch job to run
using the faster, chunking implementation." (`apexdev L17803–17805`). The
`selectIdsForBatch()` method in `references/code-examples.md` exists for exactly this. There is no
error and no debug-log warning, so this is a code-review finding, not a runtime one.

---

## Gotcha 10: A Polymorphic Reference Will Not Cross a Method Boundary Untyped

**What happens:** `t.What` is a generic reference. Passing it straight to a method that expects a
concrete type does not work: "Note that you must assign the referenced sObject that the query returns
to a variable of the appropriate type before you can pass it to another method"
(`apexdev L9797–9798`). The guide's worked example assigns `User userOwner = merch.Owner;` inside the
`instanceof` branch before calling `processUser(userOwner)` (`apexdev L9827–9834`).

**When it occurs:** Refactoring a working `instanceof` chain into per-type handler methods and passing
`t.What` through directly, because the `instanceof` test above it looks like it should have narrowed
the type.

**How to avoid:** Assign inside each `instanceof` branch, then pass the typed local. Detect
polymorphic fields programmatically with `Schema.DescribeFieldResult.isNamePointing()`, which
"Returns true if the field can have multiple types of objects as parents. For example, a task can
have both the Contact/Lead ID (WhoId) field and the Opportunity/Account ID (WhatId) field return true
for this method." (`apexrefguide L191317–191321`). Note `getReferenceTo()` changed behaviour: since
API 51.0 it returns referenced objects the context user cannot access, where 50.0 and earlier returned
an empty list (`apexrefguide L190905–190910`) — a describe-driven `TYPEOF` builder written against the
old behaviour will now emit `WHEN` branches for objects the user cannot read.

---

## Gotcha 11: Reading a Relationship Field the Query Did Not Ask For

**What happens:** `System.SObjectException: SObject row was retrieved via SOQL without querying the
requested field` (`apexdev L39943`, again at `L40110`). Relationship traversal makes this easy to hit
in a way flat queries do not: `acct.Contacts` on an Account queried without the subquery, or
`c.Account.Owner.Email` when only `Account.Name` was projected, both read a field the row never
carried. The exception is thrown at the read, potentially far from the query.

**When it occurs:** A selector method is reused by a second caller that needs one more parent field,
or a subquery is dropped from a query during optimisation while a downstream loop still reads its
result. It reproduces reliably in tests only if the test builds the same projection the caller uses.

**How to avoid:** One selector method per projection shape, named for the shape, so a caller that
needs different fields gets a different method rather than a quietly-edited one. In review, trace
every `parent.Child__r` and every dot chain in the consuming code back to the SELECT list that fed it.
`SObjectException` is a distinct catch type (`apexdev L39966`, `L40098`) if you need to degrade
gracefully rather than fail.

---

## Gotcha 12: `stripInaccessible` Reaches Into Subquery Results — and `WITH USER_MODE` Handles Polymorphic Fields

**What happens:** Developers assume field-level security on a relationship query only covers the outer
object's fields. It does not. `Security.stripInaccessible` "enforce[s] field-level and object-level
data protection by stripping fields and relationship fields from query and subquery results that the
user can't access" (`apexdev L11940–11942`), and the guide's worked example strips `Phone` from the
`(SELECT Id, LastName, Phone FROM Account.Contacts)` rows of an Account query
(`apexdev L12160–12178`). Separately, user mode on a SOQL query "Supports polymorphic fields, such as
as Owner and Task.whatId", "Processes all clauses in the SOQL SELECT statement including the WHERE
clause", and "Finds all FLS errors in your SOQL query" (`apexdev L11970–11974`).

**When it occurs:** A relationship query built in system mode for one caller is later exposed to a
lower-privileged caller — an `@AuraEnabled` method or a Guest User path — and the subquery fields go
with it.

**How to avoid:** Prefer `WITH USER_MODE` on the query so FLS is enforced across the whole statement,
including the WHERE clause and polymorphic fields, and reach for `stripInaccessible` when the query
must succeed with fields removed rather than fail. Two caveats worth knowing: object- and field-level
permissions take precedence over sharing rules where they conflict (`apexdev L11912–11914`), and
Experience Cloud personal-information visibility settings "aren't enforced in Apex, even with security
features such as the `WITH USER_MODE` clause or the `stripInaccessible` method"
(`apexdev L11916–11919`) — so a relationship query that traverses to `User` fields is not covered by
either mechanism. Depth on this belongs to `apex/soql-security` and
`apex/apex-stripinaccessible-and-fls-enforcement`.

