# Well-Architected Notes — SOQL Relationship Queries

## Relevant Pillars

- **Performance Efficiency** — Relationship queries are the primary mechanism for eliminating N+1 SOQL patterns. A parent-to-child subquery replaces a per-row child query inside a loop, reducing query count from O(n) to O(1). Child-to-parent dot notation similarly avoids a separate parent lookup. However, relationship queries that return large row totals (outer rows + inner rows > 50,000) will hit governor limits just as flat queries do; careful limit and chunk planning is required at scale.
- **Reliability** — Failing to null-guard `getSObjects()` results causes `NullPointerException` errors in production triggers and batch jobs. The reliability pillar demands defensive coding for all platform APIs that return null rather than empty collections. Handling the TYPEOF ELSE branch and checking `getSObjectType()` before casting prevents `ClassCastException` errors that surface as unhandled exceptions.
- **Security** — Relationship queries inherit the field-level security and sharing enforcement of the running user context. Use `WITH USER_MODE` to enforce FLS and CRUD on both the outer object and the inner subquery fields when queries run in system context; it also handles polymorphic fields and processes the WHERE clause, which the older `WITH SECURITY_ENFORCED` did not. `WITH SECURITY_ENFORCED` was removed in API 67.0 (Summer '26) and does not compile on a class pinned at 67.0 or above — do not write it into new relationship queries, and treat it as a migration finding on classes at 57.0–66.0. Cross-object field access via dot notation is subject to the same FLS rules as direct field access. Per-version detail: [`agents/_shared/AGENT_CONTRACT.md`](../../../../agents/_shared/AGENT_CONTRACT.md) § *Apex security idiom by API version*.
- **Operational Excellence** — Relationship query structure (subquery count, traversal depth) should be reviewed during code review and tested against governor limits in dedicated bulk test scenarios. Documenting the child relationship name used in both SOQL and `getSObjects()` calls is important for maintainability, especially for custom object relationships where the name can be changed in Setup.

## Architectural Tradeoffs

**Single relationship query vs multiple flat queries:** A single query with subqueries minimizes SOQL count (critical for triggers processing large batches) but risks hitting the 50,000 total row limit faster than multiple targeted flat queries with specific WHERE filters. Choose based on expected data volume per parent record.

**TYPEOF vs `.Type` filter vs post-query split:** `TYPEOF` in SOQL is expressive and type-safe, projecting per-type fields in a single pass, and is GA (API 46.0+) with no preview deployment risk. Its real constraint is that it is SELECT-clause only: it cannot appear in `WHERE`, `GROUP BY`/aggregate queries, Bulk API SOQL, or semi-join subqueries. When the requirement is to *filter* rows by polymorphic type in any of those contexts, the `.Type` qualifier (`What.Type IN ('Account','Opportunity')`) is the only legal option and carries no API-version floor. Reserve the post-query split — query the polymorphic Id, partition in Apex, re-query per type — for cases where per-type downstream logic is genuinely complex, since it spends extra SOQL to buy that flexibility.

**One subquery vs two queries plus a `Map<Id, List<Child>>`:** The subquery costs one top-level query
plus one entry in the aggregate-query pool (`apexdev L19613–19616`) and hands you the children already
attached to their parent. Two queries cost two top-level queries and force you to build the map
yourself, but the child query can be filtered, ordered and `LIMIT`-ed on its own terms, stays clear of
the 200-child SOQL-for-loop boundary (`apexdev L10078–10081`), and is the only shape that works in a
Batch `start()` without dropping to the non-chunking implementation (`apexdev L17796–17805`) or in a
Bulk API path (`api_asynch L2892–2896`). Rule of thumb: subquery when the child set per parent is
small and bounded and the code is synchronous; two queries plus a map when the child set is unbounded,
the context is asynchronous or bulk, or the children need their own ordering. Grouping the second
result into a map belongs to `apex/apex-collections-patterns`.

**Typed relationship access vs `getSObjects()`:** Typed access (`acct.Contacts`) is compile-time
checked, needs no per-row cast, and is what the guide's own bulkification example uses
(`apexdev L20254`). `getSObjects(name)` takes the relationship as a string, so a rename or a typo
becomes a runtime failure — but it is the only option when the query returns generic `SObject` rows,
which is the documented dynamic-DML case (`apexrefguide L233176–233178`). The trade is compile-time
safety against runtime flexibility; take the flexibility only when the relationship genuinely is not
known until runtime, and see `apex/apex-dynamic-soql-binding-safety` for the injection surface that
comes with it.

**Subquery with LIMIT vs full child set:** Adding `LIMIT 200` to a subquery guards against large child sets but silently truncates data. If all child records must be processed, use a separate child query with a parent ID filter and process in batch.

## Anti-Patterns

1. **N+1 SOQL in Triggers** — Issuing a child SOQL query inside a `for` loop over trigger records is the most commonly cited Apex performance anti-pattern. For every 200-record batch in a trigger, this can exhaust the 100-query limit before processing completes. Use parent-to-child subqueries to bundle child fetches into the initial query.

2. **Unguarded Child Iteration** — Iterating a child collection inline with no guard passes unit tests that always seed child data and fails on the first childless parent. The Apex guide's dynamic sample guards it with the comment "Prevent a null relationship from being accessed" (`apexdev L11719-L11721`); its typed samples (`apexdev L20254`, `L29894`) do not, and no corpus source states which behaviour applies where. Write `== null || isEmpty()` at every call site and cover the childless parent with a test.

2b. **Reading a Child Set by Assignment Inside a SOQL For Loop** — `List<Contact> cs = acct.Contacts;` or `acct.Contacts.size()` inside a SOQL for loop raises `Aggregate query has too many rows for direct assignment, use FOR loop` once a parent has 200 or more children (`apexdev L10078-L10088`). It is invisible below that threshold, so it ships.

2c. **A Relationship Subquery in a Batch `start()`** — Accepted without error, and silently drops the job onto "a slower, non-chunking, implementation" (`apexdev L17798-L17800`). Since nothing fails, only code review catches it.

3. **Mixing Subqueries into Bulk API Paths** — Including parent-to-child subqueries in SOQL that may be executed through the Bulk API (e.g., external ETL tools, some batch configurations) causes runtime failures that are difficult to diagnose because the same query works in interactive Apex. Separate Bulk API query paths must use flat queries only.

## Official Sources Used

Primary grounding for this revision is the offline Summer '26 extraction of the Apex Developer Guide,
Apex Reference Guide, Object Reference, Bulk API guide and App Limits cheat sheet. Line numbers are
`grep -n` positions in those extracts.

- **Apex Developer Guide — SOQL For Loops** (`apexdev L10077–10110`) — supports the
  `Aggregate query has too many rows for direct assignment, use FOR loop` exception at 200+ child
  records, the guide's failing and corrected code, and the incomplete-`JSON.serialize()` caveat.
  PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- **Apex Developer Guide — Working with Polymorphic Relationships in SOQL Queries** (`apexdev L9772–9836`) —
  supports `What.Type IN (...)` filtering, `TYPEOF What WHEN … END` projection with no `ELSE`,
  `instanceof` as the runtime discriminator, and the rule that a polymorphic reference must be assigned
  to a typed variable before being passed to a method.
- **Apex Developer Guide — Dynamic DML / foreign keys** (`apexdev L11690–11730`) — supports the
  `getSObjects('Contacts')` dynamic-access pattern and the guard commented "Prevent a null
  relationship from being accessed".
- **Apex Developer Guide — Batch Apex best practices** (`apexdev L17796–17805`) — supports the claim
  that a QueryLocator containing a relationship subquery forces the slower, non-chunking batch
  implementation, and the recommended alternative of subquerying inside `execute()`.
- **Apex Developer Guide — Execution Governors and Limits** (`apexdev L19544–19616`) — supports the
  100/200 top-level SOQL query limits, the 50,000-row transaction limit, and the rule that each
  parent-child subquery is charged against a separate pool sized at 3× the top-level limit and read
  from `Limits.getLimitAggregateQueries()`.
- **Apex Developer Guide — Enforcing Object and Field Permissions / Versioned Behavior Changes**
  (`apexdev L11742–11744`, `L11940–11974`, `L12160–12178`, `L44493–44502`) — supports the API 67.0
  changes (user mode by default, `WITH SECURITY_ENFORCED` unusable), user mode's support for
  polymorphic fields and full-statement processing, and `stripInaccessible` stripping fields from
  subquery results.
- **Apex Developer Guide — bulkification examples and exception types** (`apexdev L20228–20255`,
  `L29882–29910`, `L39938–39943`) — supports typed child access (`inv.Line_Items__r`,
  `issue.IssueComments__r`) as the guide's own pattern, subqueries against external objects, and the
  `SObject row was retrieved via SOQL without querying the requested field` `SObjectException`.
- **Apex Reference Guide — SObject Class, `getSObject`/`getSObjects`** (`apexrefguide L233130–233230`) —
  supports the `SObject[]` return type, the `String` and `Schema.SObjectType` overloads, and the
  "primarily used with dynamic DML" framing.
- **Apex Reference Guide — DescribeFieldResult and ChildRelationship** (`apexrefguide L189843–189876`,
  `L190905–190917`, `L191317–191321`) — supports `ChildRelationship.getRelationshipName()`,
  `DescribeFieldResult.getRelationshipName()`, `isNamePointing()` for polymorphic detection, and the
  API 51.0 change to `getReferenceTo()`.
- **Object Reference — Reference Field Type, custom object relationship naming, Task/Event fields**
  (`object_reference L2390–2405`, `L3022–3032`, `L23950–23969`, `L71327–71342`) — supports
  `WhoId` → Contact/Lead and `WhatId` → Account/Opportunity/Campaign/Case with the Lead exclusion, the
  `MyRel__c` / `MyRel__r` naming rule, `Task.WhatId` relationship name `What`, and `Contact.AccountId`
  relationship name `Account`.
  PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- **Bulk API 2.0 and Bulk API Developer Guide — SOQL Considerations and PK Chunking**
  (`api_asynch L2888–2896`, `L6862–6866`, `L7147`) — supports the rejection of parent-to-child
  subqueries, `TYPEOF`, `GROUP BY`, `OFFSET`, aggregate functions and compound address/geolocation
  fields in bulk queries (child-to-parent is supported), and PK chunking's incompatibility with
  subqueries and with `ORDER BY`/`LIMIT`.
- **Salesforce Developer Limits and Allocations Quick Reference — SOQL and SOSL Limits**
  (`salesforce_app_limits_cheatsheet L1049–1080`) — supports the 100,000-character SOQL statement
  limit, the `QUERY_TOO_COMPLICATED` expansion behaviour, and the 500-junction-ID cap. Note that this
  page defers to "Understanding Relationship Query Limitations" for relationship limits rather than
  restating them.

### Sources consulted but not verifiable offline

These pages carry the traversal-depth, traversal-count and subquery-count limits and the alias-notation
rules that this skill states. `help.salesforce.com` cannot be fetched and the SOQL and SOSL Reference is
not in the offline corpus, so claims resting on them carry an UNVERIFIED marker beside them in SKILL.md.

- SOQL and SOSL Reference — Using Relationship Queries: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_relationships_query_using.htm
- SOQL and SOSL Reference — Understanding Relationship Query Limitations: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_relationships.htm (five-level depth, 55 traversals, 20 subqueries)
- SOQL and SOSL Reference — Alias Notation: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_alias.htm (reserved words rejected as aliases)
- SOQL and SOSL Reference — Using Aliases with GROUP BY: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_groupby_alias.htm
- SOQL and SOSL Reference — Filtering on Polymorphic Relationship Fields: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_filtering_polymorphic_relationships.htm
- SOQL and SOSL Reference — Understanding Relationship Fields and Polymorphic Keys: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_relationships_and_polymorph_keys.htm
- SOQL and SOSL Reference — TYPEOF: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_typeof.htm
- SOQL and SOSL Reference — semi-joins and anti-joins (`IN (SELECT ...)` limits) and `FIELDS(ALL|STANDARD|CUSTOM)` restrictions — neither topic appears anywhere in apexdev.txt
- Apex Developer Guide (HTML index): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- SOAP API Developer Guide — StatusCode enumeration: https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_calls_concepts_core_data_objects.htm — used to confirm no `QUERY_WITH_SELECTIVITY_HINT_ONLY_ALLOWED_IN_SUBQUERY` code exists
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
