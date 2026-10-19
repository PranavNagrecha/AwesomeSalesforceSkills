# Gotchas — API Governance and Rate Limits

## Gotcha 1: Bulk API 2.0 is not a free bucket

**What happens:** A team moves a nightly load to Bulk API 2.0 believing it no longer touches the daily allocation, then adds polling and per-job housekeeping calls and is surprised the allocation still moves.

**When it occurs:** The limits cheat sheet lists the APIs that count toward the total allocation: REST API, SOAP API, Bulk API, Bulk API 2.0, and most Connect REST APIs. Calls from certain Salesforce connected apps, such as the Salesforce mobile app, don't count.

**How to avoid:** Model Bulk API 2.0 as "few requests per job" rather than "zero". Measure it with `ApiTotalUsageEventLog.IsApiLimitCounted` instead of assuming.

---

## Gotcha 2: Composite and Composite Batch count differently

**What happens:** A client switches from 25 single calls to one Composite Batch request and sees no change in consumption.

**When it occurs:** `/composite` executes a series of requests in a single call and the entire series counts as a single call toward API limits. Composite Batch returns up to 25 subrequests in one response, but each subrequest counts against rate limits.

**How to avoid:** Use `/composite` (or composite graphs) when the goal is fewer counted calls; use Composite Batch only to save round trips.

---

## Gotcha 3: The allocation is org-wide, so a shared user hides the culprit

**What happens:** The org hits its limit and nobody can say which integration spent it.

**When it occurs:** Limits and allocations are enforced against the aggregate of all API calls in a 24-hour period, not per user. Several systems sharing one connected app and user are indistinguishable in `ApiTotalUsageEventLog` (`ConnectedAppIdentifier`, `UserIdentifier`).

**How to avoid:** One connected app and integration user per consumer, and the daily attribution query from SKILL.md.

---

## Gotcha 4: Long-running requests have their own concurrency limit

**What happens:** Calls fail with `REQUEST_LIMIT_EXCEEDED` while the daily allocation is nowhere near spent.

**When it occurs:** Production orgs and sandboxes allow 25 concurrent inbound requests of 20 seconds or longer (Developer Edition and trials: 5). Above that, new long-running requests are refused until the count drops; there is no limit on requests shorter than 20 seconds.

**How to avoid:** Cap concurrency in the middleware, shorten requests (smaller pages, Bulk API for volume), and treat this case as retryable with backoff.

---

## Gotcha 5: The daily limit is a 403, not a 429

**What happens:** Retry logic keyed on HTTP 429 never fires, or a generic "retry on any error" loop spends the allocation it is waiting for.

**When it occurs:** REST API returns HTTP 403 with error code `REQUEST_LIMIT_EXCEEDED` when API request limits are exceeded; the concurrency limit uses the same error code.

**How to avoid:** Branch on `errorCode`, then on `DailyApiRequests.Remaining`: with allocation left, back off with jitter (concurrency); with none left, open a circuit breaker.

---

## Gotcha 6: The meter lags and can be over-polled

**What happens:** A dashboard polls `/limits` every few seconds from several workers and sees inconsistent values, while adding load of its own.

**When it occurs:** The `/limits` resource is accurate within five minutes of resource consumption and the guide says to avoid concurrent or rapid requests for consistent values.

**How to avoid:** Poll `/limits` from one place every few minutes; read `Sforce-Limit-Info` on normal responses for a continuous signal; configure API Usage Notifications for email at a set percentage.

---

## Gotcha 7: Over-limit headroom exists only in paid production orgs

**What happens:** A load test in a sandbox stops hard at the limit, or a production team plans around "we can go over a bit".

**When it occurs:** Paid orgs in active status can proceed past the daily limit by a certain amount up to a hard cap, intended for occasional spikes; it doesn't apply to trials, Developer Edition, or sandboxes, and usage over the limit is still aggregated into the 30-day entitlement.

**How to avoid:** Never plan capacity on the overage; buy add-ons or licences through the account team if the steady state needs more.
