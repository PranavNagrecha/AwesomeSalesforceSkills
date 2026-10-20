# Well-Architected Notes — SOSL Search Result Limits

## Relevant Pillars

- **Security** — the result set is not access-neutral. Users with **View All Data** see the
  full computed set; everyone else has per-user permission filters applied to search output,
  so the same SOSL returns different records depending on sharing, CRUD, and FLS. Treat a
  "missing record" that only affects non-admins as an access-control finding, not a query bug,
  and never grant View All Data to "make search work" — that widens exposure to fix a display
  gap.
- **Reliability** — nearly every limit in this domain fails *silently*: a matching record
  beyond the 2,000-record scan window, past the 250 single-object cap, or filtered by the
  min(2000/n, 250) split simply does not appear, with no error. A `FIND {…}` search term
  over 4,000 characters drops logical operators and over 10,000 returns zero rows, again with no
  exception. Reliable systems make these boundaries explicit — bound input length, set custom
  per-object limits, and assert result counts in tests — rather than trusting an unbounded
  search to surface everything.
- **Performance** — the caps exist to protect search throughput. Working *with* them (scoping
  to fewer objects, adding a `WHERE` to a single-object search) is both more correct and
  cheaper than fetching a large result set and post-filtering in Apex.
- **Operational Excellence** — because behavior differs by user permission and by API version
  (the 2,000-record limits start at API 28.0), reproduce issues in the affected user's context
  and pin the API version when reporting, so a fix verified for an admin is not assumed to hold
  for a standard user.

## Architectural Tradeoffs

- **Breadth vs. completeness.** Searching many objects in one statement gives a broad "global
  search" feel but shrinks each object's slice to min(2000/n, 250). If completeness for a
  specific object matters more than breadth, scope narrower or run per-object searches.
- **Raising the cap vs. redesigning.** A `WHERE`/`ORDER BY` inside `RETURNING` lifts a
  single-object search to 2,000, but 2,000 is the hard statement ceiling. A requirement for
  more than 2,000 ordered results is a signal to leave SOSL for SOQL/reporting, not to fight
  the limit.
- **Silent tolerance vs. explicit guards.** The platform tolerates over-length `SearchQuery`
  strings by mutating results; a well-architected service instead validates length up front and
  fails loudly, trading a little code for predictable behavior.

## Anti-Patterns

1. **Assuming 2,000 is the default** — building on the belief that any SOSL returns up to 2,000
   records, when a single object caps at 250 and a 10-object search caps each at 200. Add a
   `WHERE`/`ORDER BY`, or scope to fewer objects, deliberately.
2. **Debugging missing records only as an admin** — View All Data masks the per-user permission
   filter, so the bug is invisible to the investigator. Reproduce as the affected user.
3. **Trusting length overruns to error** — letting the `FIND {…}` term grow past 4,000 or
   10,000 characters and expecting an exception. Bound the term's length before the search runs.

## Official Sources Used

Read for this revision (2026-10-19):

- SOQL and SOSL Reference, "SOSL Limits on Search Results" (API 67.0, fetched from https://developer.salesforce.com/docs/get_document_content/soql_sosl/sforce_api_calls_sosl_limits.htm/en-us/262.0): the 2,000-record term scan from API 28.0, the 250 single-object default and WHERE/ORDER BY raise to 2,000, min(2,000/n, 250) with the 2- and 10-object examples, View All Data versus permission filters, results changing as the index changes, and the Joe example.
- SOQL and SOSL Reference, "SOSL Syntax" and "FIND {SearchQuery}" (fetched, same endpoint, pages sforce_api_calls_sosl_syntax and sforce_api_calls_sosl_find): `{SearchQuery}` is the text to search for; over 10,000 characters returns no rows; over 4,000 removes logical operators and AND defaults to OR; asterisks match at the middle or end of a term.
- SOQL and SOSL Reference, "RETURNING FieldSpec" and "LIMIT n" (fetched, pages sforce_api_calls_sosl_returning and sforce_api_calls_sosl_limit): WHERE, ORDER BY, LIMIT, and OFFSET need a field list; OFFSET only for a single object; USING ListView searches the first 2,000 list-view records; RETURNING affects what is returned, not what is searched; LIMIT up to 2,000, cannot increase the maximum, statement LIMIT spread evenly across objects, LIMIT 0 returns none.
- Apex Developer Guide 264, Execution Governors and Limits (`salesforce_apex_developer_guide.txt`): 20 SOSL queries and 2,000 records per SOSL query per transaction (264 L19753, L19755). The Winter '27 limits cheatsheet dropped its Apex tables and points to that section (`salesforce_app_limits_cheatsheet.txt` 264 L21-29); the earlier cite was cheatsheet 262 L60-62.
- Salesforce Developer Limits and Allocations Quick Reference (`salesforce_app_limits_cheatsheet.txt`): SOSL statement length 100,000 characters by default (264 L671-672); SearchQuery 10,000/4,000 thresholds and AND-to-OR example (264 L674-680); 2,000 results total including child objects from API 28.0 (264 L682-685). Values unchanged from the 262 edition (L1106-1129).
- Metadata API Developer Guide (`api_meta.txt`): CustomObject `enableSearch`, disabled by default for new custom objects, disabled after 120 days without searches (L42062-42071).
- Best Practices for Deployments with Large Data Volumes (`salesforce_large_data_volumes_bp.txt`): indexing before search and "about 15 minutes or more" latency (L160-162); index searched first, then narrowed by permissions and limits, remainder discarded (L171-174); large data changes must be indexed (L748); specific terms, search crowding over 2,000 matches, not indexing unwanted custom objects, targeted search groups (L921, L994-1005).
- Apex Developer Guide (`salesforce_apex_developer_guide.txt`): SOSL in tests returns empty results unless `Test.setFixedSearchResults` is called; WHERE and LIMIT are applied to the fixed list (L41467-41475).
