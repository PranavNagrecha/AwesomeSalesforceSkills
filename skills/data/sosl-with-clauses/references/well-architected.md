# Well-Architected Notes — SOSL WITH Clauses

## Relevant Pillars

- **Performance** — the scoping clauses (`DATA CATEGORY`, `NETWORK`, `PricebookId`,
  `DivisionFilter`) push filtering into the search engine so fewer rows cross the boundary into
  Apex, and the shaping clauses (`SNIPPET`, `HIGHLIGHT`) let the platform compute excerpts and
  match markup instead of re-tokenizing text in Apex. Respect the documented cut-offs — snippets
  render only at ≤20 results per page and highlighting caps at 25 records per entity per query —
  so the UI degrades predictably rather than silently.
- **Security** — `WITH DATA CATEGORY` returns only results "visible to users," and `WITH NETWORK`
  keeps one Experience Cloud site's users and feeds from bleeding into another. Treat these as
  scoping, not authorization: `NETWORK` filtering applies only to users and feeds, so don't
  assume it isolates every object, and keep the surrounding Apex `with sharing` and CRUD/FLS-aware
  (see `templates/apex/SecurityUtils.cls`).
- **Reliability** — because clause behavior is gated by object type and API version, a query that
  works in one context silently loses a clause in another (a lower `apiVersion`, an unsupported
  object). Pin and verify the API version so the search behaves the same across environments.

## Architectural Tradeoffs

- **Wildcard breadth vs. result shaping.** Wildcards widen recall but suppress `SNIPPET` and
  `HIGHLIGHT`. Choose per use case: broad discovery searches can skip shaping; precise
  help-center searches should use complete terms so excerpts and highlights render.
- **Spell correction on vs. off.** The default `SPELL_CORRECTION = true` improves forgiving,
  natural-language search but can mis-hit exact identifiers (part numbers, codes). Disable it for
  exact-match lookups; keep it on for human-language content search.
- **Engine-side scoping vs. post-filtering in Apex.** Scoping clauses are cheaper and safer than
  pulling a wide result set and filtering in memory — but only where the clause supports the
  object. Where it doesn't (e.g. `NETWORK` on non-feed objects), you still need an explicit
  `WHERE`/`WITH` on the record, not a false sense of isolation.

## Anti-Patterns

1. **Freely reordered WITH clauses** — SOSL enforces a single fixed order; a "logical" reorder
   fails to parse. Assemble in canonical sequence every time.
2. **Trusting a silently-gated clause** — using `SNIPPET`/`HIGHLIGHT`/`DATA CATEGORY` on an
   unsupported object or below its API floor yields no error and no effect. Verify support first.
3. **Treating WITH NETWORK as full multi-site isolation** — it scopes only users and feeds;
   assuming it filters every object risks cross-site data exposure.

## Official Sources Used

- SOSL Syntax (FIND, RETURNING, WITH clause order) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl_syntax.htm
- WITH SNIPPET — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl_with_snippet.htm
- WITH HIGHLIGHT — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl_with_highlight.htm
- WITH SPELL_CORRECTION — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl_with_spell_correction.htm
- WITH DATA CATEGORY — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl_with_data_category.htm
- WITH NETWORK NetworkIdSpec — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl_with_network_id.htm
