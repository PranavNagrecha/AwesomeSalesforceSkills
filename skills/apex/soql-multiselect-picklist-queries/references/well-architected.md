# Well-Architected Notes — SOQL Multi-Select Picklist Queries

## Relevant Pillars

- **Security** — a multi-select filter is a prime SOQL-injection surface when the values come
  from a user, Flow, or LWC, because developers tend to hand-build the semicolon/comma grouping
  as a string. Prefer static SOQL with bind variables (filter literals in a `WHERE` clause are a
  supported bind position, and binds work with `INCLUDES`); if the query must be dynamic, escape
  input with `String.escapeSingleQuotes`. Enforce the running user's access with `WITH USER_MODE`
  (or CRUD/FLS checks) so the query can't read fields the user shouldn't see.
- **Performance** — multi-select picklist fields are not selective and are not backed by a
  standard index, so `INCLUDES` / `EXCLUDES` filters can force full or broad scans on large
  objects. Treat the multi-select filter as a non-selective predicate: pair it with a selective,
  indexed filter (e.g. `RecordTypeId`, `OwnerId`, a date range) so the query planner has an
  index to lead with. See `data/soql-query-optimization`.

## Architectural Tradeoffs

- **`INCLUDES` correctness vs `=` brittleness.** `INCLUDES` is the right containment test but is
  non-selective; `=` can occasionally hit an index but only matches the exact whole-selection
  string and under-matches almost every real requirement. Choose `INCLUDES` for correctness and
  compensate with a selective companion predicate rather than reaching for `=` to chase an index.
- **Query-time filtering vs data model.** If a multi-select picklist is heavily filtered on a
  high-volume object, that is a signal the values may belong in a normalized child object or as
  separate boolean/checkbox fields, which *can* be indexed and sorted. Filtering in SOQL is
  correct for modest volumes; reshape the model when the field becomes a hot, non-selective
  filter path.
- **Bind vs dynamic.** Static SOQL with binds is safest and clearest; dynamic SOQL buys
  flexibility (variable numbers of OR groups) at the cost of an injection surface you must
  actively defend. Default to static; go dynamic only when the group shape is genuinely runtime.

## Anti-Patterns

1. **`=` / `LIKE` for containment** — using exact-string equality or substring matching instead
   of `INCLUDES` / `EXCLUDES`. Both silently return the wrong rows; use the documented operators.
2. **Concatenated dynamic INCLUDES** — building the clause by string concatenation of untrusted
   input. It is a SOQL-injection hole and breaks on quotes/semicolons; bind or escape instead.
3. **Non-selective multi-select filter as the sole predicate on a large object** — filtering only
   on the multi-select field, forcing a broad scan. Add a selective, indexed companion predicate.

## Official Sources Used

- Query Multi-Select Picklists (SOQL and SOSL Reference) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_querying_multiselect_picklists.htm
- ORDER BY (SOQL and SOSL Reference) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_orderby.htm
- Using Apex Variables in SOQL and SOSL Queries (Apex Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SOQL_variables.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
