# Well-Architected Notes — SOQL Outer-Join & Null Semantics

## Relevant Pillars

- **Reliability** — the dominant concern. The outer-join behavior of relationship queries and the
  Boolean null-coercion rule mean a filter that *looks* correct can return a superset (or the
  wrong set) of rows, and Apex that walks a parent relationship can throw a
  `NullPointerException` on null-foreign-key rows. Writing filters against the foreign-key field
  and null-guarding parent traversals makes query results deterministic and code crash-free.
- **Security** — result-set correctness is a data-exposure concern. A `WHERE Parent.Field = null`
  filter used as a "no parent" guard, or a Boolean `= null` misread as "unset," can silently
  widen what a query returns — including records the author intended to exclude from a list view,
  export, or downstream sharing decision. Getting the filter semantics right is part of exposing
  only the intended rows. (Enforce CRUD/FLS and injection safety separately via `apex/soql-security`.)
- **Performance** — a filter that returns far more rows than intended (e.g. every `false` Boolean
  row, or all parent-less rows) inflates the result set, heap, and downstream processing. A
  correct foreign-key filter keeps the query selective.

## Architectural Tradeoffs

- **Foreign-key filter vs parent-field filter.** Filtering the FK Id (`AccountId = null`) is the
  reliable way to express presence/absence of a lookup, but it only answers "is the lookup set."
  When you genuinely need "the parent exists *and* its field has value X," a parent-field
  predicate is appropriate — just know it does not double as a "parent exists" test on its own.
- **Explicit Boolean literals vs terse null checks.** `= true` / `= false` is unambiguous and
  survives review; `= null` / `!= null` on a Boolean is legal and equivalent but forces every
  reader to recall the coercion rule. Prefer the explicit literal even though both compile.
- **Filter in SOQL vs guard in Apex.** You can exclude null-FK rows in the query (`WHERE
  AccountId != null`) or tolerate them and null-guard the traversal in Apex. Filtering is cleaner
  when parent-less rows are never wanted; guarding is right when you must process all rows and
  simply handle the missing parent.

## Anti-Patterns

1. **Treating a relationship query as an inner join** — assuming null-foreign-key rows are dropped
   and skipping the explicit FK filter or null guard. They are returned as documented; filter or
   guard deliberately.
2. **Using `WHERE Parent.Field = null` as a "no parent" test** — it also returns rows whose parent
   doesn't exist, so it over-selects. Filter the foreign-key Id instead.
3. **Comparing a Boolean field to null** — reads as "unset" but evaluates as `= false`, returning
   every unchecked row. Compare Booleans to explicit `true` / `false`.

## Official Sources Used

- SOQL and SOSL Reference — null Values in Lookup Relationships and Outer Joins — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_relationships_lookup.htm
- SOQL and SOSL Reference — Using null in a WHERE clause — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_null.htm
