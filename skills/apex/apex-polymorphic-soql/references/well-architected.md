# Well-Architected Notes — Apex Polymorphic SOQL

## Relevant Pillars

- **Performance** — Primary. Polymorphic fields sit on the largest tables most orgs have: Task, Event, FeedItem, ContentDocumentLink. The decision that matters is not `TYPEOF` versus flat projection, it is whether the query has an indexed predicate at all. `.Type` is a filter and never an index, so a query driven by it degrades from "fine in sandbox" to `System.QueryException: Non-selective query against large object type` as production volume grows.
- **Reliability** — Primary alongside Performance. The set of objects a `WhatId` can point at is org configuration, not a constant. A dispatcher with no `ELSE` branch and no default handler silently drops rows the day someone enables Activities on a new object — a failure with no error and no log line.
- **Operational Excellence** — Secondary. `TYPEOF`'s restriction list is the main portability tax: a query that works in Apex cannot be reused as a subquery, a PushTopic, or a Bulk API extract. Knowing which form to write for which consumer avoids discovering it during a release.
- **Scalability** — Secondary. `TYPEOF` collapses N per-type queries into one, which matters against the 100-query synchronous limit when a handler processes several polymorphic fields in the same transaction.

## Architectural Tradeoffs

| Tradeoff | Decision criteria |
|---|---|
| `TYPEOF` vs flat `What.Name` / `What.Type` | `TYPEOF` when you need fields that exist only on specific targets. Flat when the common parent fields suffice — it is simpler, and it is the only form legal in subqueries, aggregates, PushTopics, and Bulk API. |
| `TYPEOF` vs partition-and-re-query | `TYPEOF` for read-and-format work in one pass. Partition-and-re-query when per-type processing is genuinely different logic, or when you need many fields per type and the `TYPEOF` clause would become unreadable. Partitioning costs one query per type but keeps each query indexed on an Id set. |
| `Id.getSObjectType()` vs `instanceof` for dispatch | `getSObjectType()` on the Id when you only have the Id and want to group before querying — no query, no describe. `instanceof` on the resolved sObject when you already have a `TYPEOF` result and are about to cast. |
| `ELSE` branch vs enumerating every type | Always write `ELSE`, even when you believe the enumeration is complete. Org configuration changes; the `ELSE` branch is the difference between degrading and dropping. |
| Synchronous query vs extract job | Synchronous when an Id set or a bounded date range makes the query selective. An extract job (date-chunked, Bulk API, flat projection) when the scope is genuinely "all rows of this type" — that is not a request a synchronous query should ever serve. |

## Architectural Anti-Patterns

1. **Type filtering as the primary predicate** — `WHERE What.Type = 'Account'` with nothing indexed alongside it. This is the same class of mistake as any non-selective query, but it is more tempting here because the filter reads like it narrows a lot. It narrows the *result*, not the *scan*.
2. **Casting without an `instanceof` guard** — Reading a field that the row's matched `WHEN` branch never projected. The resulting `System.SObjectException: SObject row was retrieved via SOQL without querying the requested field` names a field that *is* in the query text, which sends debugging in the wrong direction for a while.
3. **Assuming `Owner` is always a User** — The reference documents `Owner` as polymorphic and notes Task owners "are either Calendars or Users." Code that dereferences `Owner.Name` on activity objects without a guard will meet a Calendar owner eventually.
4. **Baking the target list into code** — A hard-coded list of possible `WhatId` targets is stale the first time an admin enables Activities on a new object. `getDescribe().getReferenceTo()` returns the current list at run time; use it and log anything unrecognised.

## Official Sources Used

- SOQL and SOSL Reference — TYPEOF. Confirms the syntax block and every usage restriction quoted in the gotchas: outer-SELECT-only, no COUNT()/aggregate queries, no GROUP BY / ROLLUP / CUBE / HAVING, no nesting, not in the SELECT clause of a semi-join, not in Streaming API PushTopics, not in Bulk API, and "TYPEOF is available in API version 26.0 and later." — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_typeof.htm (verified 2026-08-14, via the archived 218.0 rendering of the same page)
- SOQL and SOSL Reference — Understanding Relationship Fields and Polymorphic Fields. Confirms the semantics of the three documented polymorphic relationships (`Owner` "represents the parent of the record", with Task owners being "either Calendars or Users"; `Who` "represents the person associated with the record", Contacts or Leads; `What` "represents nonhuman objects that are associated with the record"), and that "You can use the Type qualifier on a field to determine the object type that's referenced in a polymorphic relationship." — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_relationships_and_polymorph_keys.htm (verified 2026-08-14)
- Apex Developer Guide — Working with Polymorphic Relationships in SOQL Queries. Confirms the `SELECT TYPEOF What WHEN Account THEN Phone WHEN Opportunity THEN Amount END FROM Event` example form, that you "can use the `instanceof` keyword to determine the object type", and that "you must assign the referenced sObject that the query returns to a variable of the appropriate type before you can pass it to another method." — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SOQL_polymorphic_relationships.htm (verified 2026-08-14)
- Salesforce Well-Architected Overview — pillar definitions used to map the tradeoffs above. — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
