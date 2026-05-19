# Gotchas — REST API Pagination Patterns

Non-obvious Salesforce REST query behaviors that cause real
production issues. These layer on top of the rules in `SKILL.md` —
each one is a second-order failure that only surfaces after a naive
"works on my laptop with 200 rows" implementation hits real volume.

## Gotcha 1: `nextRecordsUrl` is a server-managed cursor with a ~15-minute TTL

**What happens:** A long-running export starts paginating an 85,000-
row Opportunity query at 9:00:00. The job processes pages 1-12 at
roughly 30 seconds each, then a downstream warehouse write blocks
for 18 minutes on a lock. At 9:24:00 the caller resumes and
GETs the `nextRecordsUrl` it stored. The response is HTTP 400 with
`INVALID_QUERY_LOCATOR` — the locator has expired and there is no
"refresh" or "extend" affordance. The job has no choice but to
restart the entire query from page 1.

**When it occurs:** Any pagination loop where the wall-clock time
between consecutive `nextRecordsUrl` fetches exceeds approximately
15 minutes. Common triggers: slow downstream sinks, manual
checkpoint pauses for review, retry-with-backoff after a 503 cascade
that takes the loop past the TTL.

**How to avoid:** Treat the cursor as session-bound, not durable.
For resumable pagination that survives process restarts, daily
reboots, or operator pauses, switch to **keyset pagination on `Id`**
(see `examples.md` anti-pattern, "Correct approach 2") — the
`WHERE Id > :lastId ORDER BY Id LIMIT 200` pattern persists state
as a single 18-character `Id` string that is valid forever and
survives restarts. The cursor is not resumable across sessions and
not transferrable across users (the locator is bound to the
authenticating session token).

---

## Gotcha 2: SOQL `OFFSET` silently caps at 2,000 with `NUMBER_OUTSIDE_VALID_RANGE`

**What happens:** A pagination loop using `LIMIT 200 OFFSET N`
succeeds for the first 11 iterations (offsets 0 through 2000) then
throws `System.QueryException: OFFSET 2200 is outside of the valid
range` on iteration 12. The exception bubbles up only if the loop
is wrapped in a try/catch that re-raises — many implementations
swallow it as "no more pages" and silently truncate the export.
A 50,000-row query reads at most 2,200 records, and downstream
analysts discover the gap days later.

**When it occurs:** Any `OFFSET` pagination over a dataset larger
than 2,000 rows. The error is `NUMBER_OUTSIDE_VALID_RANGE` with
errorCode `NUMBER_OUTSIDE_VALID_RANGE` in the REST response body;
in Apex it surfaces as `QueryException`. The 2,000 cap is hard,
platform-enforced, and not adjustable via setting or support case.

**How to avoid:** Switch to **keyset pagination** with
`WHERE Id > :lastId ORDER BY Id LIMIT 200`. `Id` is a unique,
ordered, 18-character string with no offset cap — you can walk a
billion-row table this way. Persist `lastId` between calls if the
pagination crosses transactions. For one-shot egress past a few
thousand rows, prefer the `nextRecordsUrl` cursor walk (no cap, but
honor the 15-minute TTL from gotcha 1) or Bulk API 2.0 query jobs.

---

## Gotcha 3: `Sforce-Query-Options: batchSize` is REST-query-only; Bulk API uses a different pagination surface

**What happens:** A practitioner who learned page-size tuning on the
REST query resource tries to apply the same `Sforce-Query-Options:
batchSize=2000` header to a Bulk API 2.0 query job request. The
header is silently ignored — Bulk API 2.0 jobs are asynchronous and
return results through the `/services/data/vXX.X/jobs/query/<jobId>
/results` endpoint, which paginates via the `Sforce-Locator`
response header and the `maxRecords` query parameter, not via
`Sforce-Query-Options`. The job returns its default page size and
the integration thinks the tuning "didn't take" — sometimes leading
to a doubled batchSize that has no effect, or to a memory-tuning
campaign aimed at the wrong knob.

**When it occurs:** Migrating an existing REST query pagination job
to Bulk API 2.0 to chase higher throughput, or wiring up a brand-new
Bulk job from a code template copied from a REST query example.

**How to avoid:** Two different API surfaces, two different
pagination protocols:

- **REST query** (`/services/data/vXX.X/query`) — request header
  `Sforce-Query-Options: batchSize=N` on the first call;
  termination by `done == true` in the response body; follow-up via
  `nextRecordsUrl` from the response body.
- **Bulk API 2.0 query job** (`/services/data/vXX.X/jobs/query`) —
  create job, poll status until `JobComplete`, then fetch results
  paginated by `Sforce-Locator` *response header* and `maxRecords`
  *query string parameter* on the results endpoint. There is no
  `done` boolean — pagination ends when the response omits the
  `Sforce-Locator` header (or returns it as `null`).

The two pagination contracts have nothing in common beyond "you
walk pages until you run out." Treat them as distinct integrations.

---

## Gotcha 4: Every `nextRecordsUrl` follow-up consumes one daily API call

**What happens:** A finance team requests a one-time export of all
10 million Order rows from production into a tax-reporting warehouse.
The job runs at the default `batchSize=200`. The pagination loop
fetches `ceil(10_000_000 / 200) = 50,000` pages. Each page is a
separate REST GET call against `/services/data/vXX.X/query/...` and
each one counts against the org's 24-hour API request limit.

**When it occurs:** Any large extract over the REST query resource.
The damage scales linearly with row count and inversely with
batchSize. On an Enterprise Edition org the rolling 24-hour API
limit is approximately 100,000 requests for 1-100 licensed users
plus 1,000 per Salesforce license — a 500-user org sits around
600,000 calls per day. A single 50,000-call export consumes ~8% of
that budget; a 10M-row daily export at default batchSize would
consume **50%** of a 500-user org's API ceiling every day.

**How to avoid:** Two complementary moves.

1. **Tune `Sforce-Query-Options: batchSize` toward 2000.** At
   `batchSize=2000` the same 10M-row export drops from 50,000 calls
   to 5,000 — a 10× reduction. Mind the per-request memory
   tradeoff (see `examples.md` Example 2 table).
2. **For one-shot extracts above ~100K rows, switch to Bulk API 2.0
   query jobs.** A Bulk job's CSV results endpoint is paginated by
   `Sforce-Locator` and counts as a small fixed number of API calls
   per job regardless of row count — the right call when row volume
   is the binding constraint on API budget.

Monitor consumption via the `Limits` resource
(`/services/data/vXX.X/limits`) — `DailyApiRequests.Remaining` tells
you how much budget the export is about to burn before you launch it.

---

## Gotcha 5: `done: false` is the only reliable termination signal — do NOT rely on `nextRecordsUrl` presence alone

**What happens:** A pagination loop is written as:

```
while (response.nextRecordsUrl != null) {
    response = fetch(response.nextRecordsUrl);
}
```

This appears correct — and works in the happy path on current API
versions. But two failure modes have surfaced in production:

1. On the **final** page (the page that exhausts the result set), some
   API-version response shapes have historically included
   `nextRecordsUrl` pointing at an empty page (and `done: true` on
   that empty page). A loop keyed on `nextRecordsUrl` presence does
   one extra fetch — wasting an API call and pulling in a zero-row
   page.
2. On a partial-result response (e.g., a transient server issue that
   returned a 200 with `done: true` and no `nextRecordsUrl` despite
   the totalSize being larger than the row count returned), a loop
   keyed on `done` correctly stops, while a loop keyed on
   `nextRecordsUrl` may attempt to recurse into a null URL and throw.

**When it occurs:** Cross-version API consumers (a job that ran fine
on v50.0 may behave differently on v60.0), retry-storm scenarios,
and any integration that copies a pagination skeleton from a
StackOverflow answer written for an older API version.

**How to avoid:** Always loop on `done`:

```
while (response.done == false) {
    response = fetch(response.nextRecordsUrl);
}
```

The `done` boolean is the platform contract; `nextRecordsUrl` is an
implementation detail. Read both — use `done` to decide whether to
continue, use `nextRecordsUrl` only when `done == false` to fetch
the next page. This pattern is forward-compatible across API
versions and immune to the empty-tail edge case.
