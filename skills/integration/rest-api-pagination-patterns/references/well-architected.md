# Well-Architected Notes — REST API Pagination Patterns

## Relevant Pillars

Pagination is rarely thought of as "architecture" — it's seen as
plumbing. That framing is the source of most pagination outages.
Three pillars dominate the decision space; the binding one is
usually Performance, with Scalability the close second on any
data-egress job whose row count grows organically.

- **Performance** — The two knobs that move the needle are
  `Sforce-Query-Options: batchSize` (round trips vs payload size)
  and choice of pagination primitive (cursor walk vs keyset vs
  Bulk job). A 10× difference in API-call consumption between a
  default-batchSize export and a tuned one is routine; a 100×
  difference between a REST cursor walk and a Bulk API 2.0 job on
  a 10M-row extract is also routine. Neither difference shows up
  in functional tests — it only surfaces in production at full
  volume.
- **Scalability** — REST query pagination scales linearly in API
  calls with row count. Linear is fine until row count exceeds
  ~100K, at which point the daily API budget becomes the binding
  constraint instead of throughput. The right architectural move
  at that threshold is to swap pagination primitives entirely
  (REST cursor → Bulk API 2.0 query job), not to keep tuning
  batchSize. Designing for "what happens at 10× current row
  count" is the test that separates pagination code that survives
  a year from code that needs to be rewritten on the next
  data-volume jump.
- **Operational Excellence** — A pagination loop is a stateful
  walk that can fail mid-stream — at page 42 of 1,000, the network
  blinks and the cursor is now 15-minute-stale. Whether the
  integration recovers gracefully (resume from `lastId`) or
  re-fetches all 42 pages (waste of API budget and time) is a
  function of which pagination primitive was chosen at design
  time. Observability — emitting page-number, cursor-age, and
  API-calls-remaining as structured logs — is the difference
  between "we know we're at page 800 of 1,000 with 90 minutes of
  budget left" and "the export hung and we don't know where."

## Architectural Tradeoffs

The defining choice is **which pagination primitive** fits the
job. Five options, each with a sweet spot:

| Primitive | Best for | Row-count sweet spot | API-call cost | Resumability | Notes |
|-----------|----------|----------------------|---------------|--------------|-------|
| REST `nextRecordsUrl` cursor walk | One-shot exports under a single session | 2K - 500K | 1 call per page (= rows / batchSize) | None — 15-min TTL | Default choice for outbound integrations; tune batchSize toward 2000 |
| Composite API batch (`/composite/batch`) | Pagination across multiple disparate queries in one round trip | 0 - 25 sub-queries per call | 1 call per composite batch (up to 25 subrequests) | N/A — atomic batch | Use when you need a few pages worth of results across many queries, not when you need many pages of one query |
| SOQL keyset (`WHERE Id > :lastId`) | Resumable, restart-tolerant pagination across transactions or days | 0 - any volume | 1 SOQL per page (within governor) or 1 API call per page (REST) | Full — persist `lastId` anywhere | The only correct REST-based pattern when the loop must survive process restarts |
| Bulk API 2.0 query job | Million-row+ one-shot extracts | 100K - 1B | ~5-10 calls total (create + poll + paginated results via `Sforce-Locator`) | Job-level (job id persists 7 days) | Wins on API-budget and throughput for large extracts; loses on per-row latency for small ones |
| Change Data Capture (CDC) subscription | Continuous incremental sync, not bulk egress | N/A (event stream) | Counts against PE/CDC delivery limits, not REST API | Replay via replay id (3-day window) | Different architectural shape entirely — push, not pull; the right answer when "always up to date" matters more than "snapshot at time T" |

The 100K-row mark is the practical inflection point. Below it,
REST cursor pagination is simpler to build, simpler to debug, and
the API-call cost is acceptable. Above it, Bulk API 2.0 becomes
the better fit on every dimension except per-row latency — and
once you're in the millions, CDC subscriptions deserve a serious
look as a permanent replacement for the periodic-egress pattern.

A secondary tradeoff: **`batchSize` choice within REST cursor
pagination**. Smaller batches (200-500) mean more round trips,
more API calls, and faster recovery from a single-page failure.
Larger batches (1000-2000) mean fewer round trips, lower API-call
consumption, and longer single-request latency with higher
per-request memory pressure on both endpoints. The sweet spot for
most warehouse-egress jobs is 500-1000; reserve 2000 for low-
field, flat-projection queries on stable schemas.

A third tradeoff: **safety-cap iteration count vs trust in
termination signal**. The platform-contract termination signal
(`done == true`) is reliable in normal operation but can be
malformed under degraded conditions (server returns 200 with
truncated body, cursor expires mid-loop, API gateway returns a
non-JSON error page). A safety cap on iteration count (e.g., 1000
pages) costs nothing in the happy path and prevents an infinite
loop in the unhappy path. There is no good reason to omit it.

## Anti-Patterns

1. **SOQL `OFFSET` for pagination past page 10.** Caps at 2000
   rows total with `NUMBER_OUTSIDE_VALID_RANGE`. Use keyset
   pagination on `Id` instead. See `examples.md` anti-pattern.
2. **Looping on `nextRecordsUrl` presence instead of `done`
   absence.** Forward-incompatible across API versions and can
   over-fetch an empty tail page. Always loop on `done`. See
   `gotchas.md` gotcha 5.
3. **Defaulting to `batchSize=200` on a million-row extract.**
   5,000-call extracts when 5,000-call budgets exist is fragile.
   Either tune to `batchSize=2000` (5× reduction) or migrate to
   Bulk API 2.0 (100× reduction). See `gotchas.md` gotcha 4.
4. **Treating `nextRecordsUrl` as durable state.** The cursor
   expires after ~15 minutes and is bound to the originating
   session. Pagination loops that need to survive process
   restarts must use keyset pagination, not cursor walking. See
   `gotchas.md` gotcha 1.
5. **Mixing REST `Sforce-Query-Options` semantics with Bulk API
   2.0 results pagination.** Two different APIs, two different
   pagination contracts. `batchSize` on a Bulk query results call
   is silently ignored; the right knob is `maxRecords` plus the
   `Sforce-Locator` response header. See `gotchas.md` gotcha 3.

## Official Sources Used

- REST API Developer Guide — Execute a SOQL Query:
  https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_query.htm
- REST API Developer Guide — Introduction:
  https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_rest.htm
- REST API Developer Guide — Query More Results:
  https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/headers_querymore.htm
- REST API Developer Guide — Query Options Header:
  https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/headers_queryoptions.htm
- Bulk API 2.0 and Bulk API Developer Guide — Introduction:
  https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Bulk API 2.0 — Get Results for a Query Job:
  https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/query_get_job_results.htm
- SOQL and SOSL Reference — Change the Batch Size in Queries:
  https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_changing_batch_size.htm
- Salesforce Well-Architected — Performant:
  https://architect.salesforce.com/well-architected/trusted/performant
