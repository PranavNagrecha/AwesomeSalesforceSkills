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
  min(2000/n, 250) split simply does not appear, with no error. Dynamic `SearchQuery` strings
  over 4,000 characters drop logical operators and over 10,000 return zero rows, again with no
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
3. **Trusting length overruns to error** — letting a dynamic `SearchQuery` grow past 4,000 or
   10,000 characters and expecting an exception. Bound the string length before the call.

## Official Sources Used

- SOSL Limits on Search Results (SOQL and SOSL Reference) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl_limits.htm
- SOQL and SOSL Limits (Salesforce Platform limits cheat sheet) — https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_soslsoql.htm
