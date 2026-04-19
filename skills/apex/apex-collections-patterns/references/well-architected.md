# Well-Architected Notes — Apex Collections Patterns

## Relevant Pillars

- **Performance Efficiency** — Collections are heap-allocated and count toward the 6 MB (sync) / 12 MB (async) heap limit. The fundamental bulkification pattern — `Map<Id, SObject>` for O(1) lookup instead of nested loops with SOQL — is the primary performance concern for collection design in triggers and batch classes.
- **Reliability** — Null-safe collection access (`containsKey` guard before `Map.get`) and mutation-safe set operations (`clone` before `retainAll`) prevent `NullPointerException` and incorrect logic. These are the most common sources of production bugs in collection-heavy Apex.
- **Operational Excellence** — Collection design in `Database.Stateful` batch classes directly impacts job reliability. Unbounded list accumulation is a leading cause of batch job failure at scale.

## Architectural Tradeoffs

**Map<Id, SObject> vs. SOQL re-query:** Building a Map from a trigger's `Trigger.new` or a batch's scope avoids additional SOQL queries but requires careful management of what fields are present on the records. Re-querying is safer when you need fields not on the trigger record, but adds to SOQL governor usage. Prefer Map-based patterns in triggers; use targeted re-queries only for fields not already available.

**Set intersection via retainAll vs. stream filter:** `retainAll()` is a single O(n) pass and idiomatic in Apex. A filter loop is more explicit and avoids mutation surprise but is more verbose. For clarity in complex logic where the original set is needed, clone before `retainAll`. For simple intersection where the original is not reused, `retainAll` directly is preferred.

**Database.Stateful accumulation:** Accumulating full SObject records in a Stateful batch class is a common premature optimization (avoiding a re-query in `finish()`). The memory cost is almost always higher than the SOQL cost of a targeted re-query. Default to accumulating only Ids or summary primitives.

## Anti-Patterns

1. **Nested loops for lookup** — using a nested `for` loop to find matching records from two lists is O(n×m) and fails at bulk scale. Replace inner iteration with a `Map<Id, SObject>` lookup, reducing to O(n).
2. **Unbounded list growth in Stateful batches** — appending all processed SObjects to a member `List` across execute() chunks consumes heap proportional to total job scope. Accumulate only what is needed for `finish()` (counts, Id sets, error strings).
3. **Missing containsKey guard before Map.get** — directly using `map.get(key).field` without a null check creates fragile code that fails silently on missing keys with a confusing `NullPointerException` at the field access site, not at the map lookup.

## Official Sources Used

- Apex Developer Guide — Collections: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_collections.htm
- Apex Reference Guide — Map Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_map.htm
- Apex Reference Guide — Set Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_set.htm
- Apex Developer Guide — Execution Governors and Limits: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
