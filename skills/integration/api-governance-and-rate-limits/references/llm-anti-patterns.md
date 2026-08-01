# LLM Anti-Patterns — API Governance and Rate Limits

Scope: governing how much API allocation your consumers burn, and reacting when they
burn it. Connected App scopes, IP restriction and session policy are a different
control plane and belong to `security/api-security-and-rate-limiting` — cross-link, do
not restate.

## Anti-Pattern 1: Treating every limit error as the same event

`REQUEST_LIMIT_EXCEEDED` is returned for more than one condition, and the right response
differs by condition. Assistants generate a single catch-all handler, which means the
one case that recovers on its own gets treated like the one that cannot.

- **24-hour rolling allocation exhausted.** The org has spent its daily API request
  entitlement. Nothing recovers this within the transaction; it clears as the rolling
  window advances. Retrying makes it worse.
- **Concurrent long-running requests exceeded.** The documented allocation is 25
  concurrent requests running longer than 20 seconds in production orgs and sandboxes,
  and 5 in Developer Edition and Trial orgs. This *does* clear in seconds, as soon as
  in-flight requests finish. It is the one case where a bounded retry is correct.

❌ `catch (e) { sleep(60); retry(); }` for anything containing `REQUEST_LIMIT_EXCEEDED`.
✅ Branch on which condition it is — read remaining daily allocation from `/limits`
before deciding. Concurrency: back off with jitter and retry. Daily allocation: stop,
alert, and shed load; the window will not move because you retried.

Source: Salesforce Platform API limits (daily allocations, concurrent long-running
request allocation, `REQUEST_LIMIT_EXCEEDED`) —
https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm

## Anti-Pattern 2: Confusing per-transaction governor limits with the org's API allocation

These are unrelated budgets and assistants routinely blend them. `Too many SOQL queries:
101` is an Apex governor limit inside one transaction and has nothing to do with API
consumption; `REQUEST_LIMIT_EXCEEDED` is an org-wide allocation across 24 hours and is
not affected by how efficient any single transaction is.

❌ "We're hitting API limits, so bulkify the trigger."
✅ Identify the budget from the error first. Governor limits are fixed by transaction
design; the API allocation is fixed by consumer behaviour and edition entitlement. A
perfectly bulkified org still exhausts its daily allocation if a middleware polls every
thirty seconds.

## Anti-Pattern 3: Estimating consumption instead of reading it

Assistants compute expected call volume from the integration design. The org publishes
the actual number, so the estimate is never worth having.

**Wrong** — a derived figure, wrong the moment a consumer changes behaviour:

```apex
Integer estimatedDailyCalls = accountsSynced * 3 + contactsSynced * 2;
if (estimatedDailyCalls > 80000) {
    AlertService.warn('approaching limit');
}
```

**Right** — read the org's own meter, and treat every consumer's usage as attributable:

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:MyOrg/services/data/v64.0/limits');
req.setMethod('GET');
HttpResponse res = new Http().send(req);

Map<String, Object> limits =
    (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
Map<String, Object> daily = (Map<String, Object>) limits.get('DailyApiRequests');
Integer maxCalls  = (Integer) daily.get('Max');
Integer remaining = (Integer) daily.get('Remaining');
Decimal usedPct   = maxCalls == 0 ? 0 : (1 - (Decimal) remaining / maxCalls) * 100;

if (usedPct >= 85)      { AlertService.page('API_ALLOCATION_85', usedPct + '%'); }
else if (usedPct >= 70) { AlertService.ticket('API_ALLOCATION_70', usedPct + '%'); }
```

Two things to know about this resource. `Max` is the limit for the org and `Remaining` is
what is left, so consumed is the difference — there is no "used" key. And the values are
documented as accurate only within five minutes of consumption, so a threshold tuned to
trip at 99% will trip after the wall has already been hit. Alert at 70 and 85.

Source: /limits REST resource —
https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_limits.htm

## Anti-Pattern 4: One integration user for every consumer

The single most expensive governance decision, and the default that assistants produce.
When six systems authenticate as `integration@company.com`, the org-level consumption
number is real but unattributable. You know you are at 92% and you cannot say who by, so
the only available remediation is to throttle everyone.

❌ One integration user, one Connected App, six consumers.
✅ One Connected App and one dedicated user per consumer. Consumption then attributes by
consumer key in the `ApiTotalUsage` event type in Event Monitoring, and remediation can
be targeted at the one system that changed. Do this before the incident; you cannot
attribute retroactively.

## Anti-Pattern 5: Retrying into a 24-hour wall

An immediate retry on a limit error is the reflex, and against a daily allocation it
converts a partial outage into a total one — each retry consumes another call from the
allocation it is waiting on. Assistants reach for it because retry is the standard answer
to a transient failure, and this failure is not transient.

❌ Fixed-interval retry loops on any error response.
✅ Exponential backoff with jitter, a bounded attempt count, and a circuit breaker that
opens on the daily-allocation condition and stays open until the window advances. Without
jitter, every queued job retries in lockstep and the recovery itself becomes the spike.

## Anti-Pattern 6: Row-by-row REST for bulk work

An assistant asked to "sync 200,000 records" produces a loop of single-record REST calls
because that is the shape of the example it learned. This is the largest single source of
avoidable allocation burn, and the fix is a different API rather than a faster loop.

❌ 200,000 individual `PATCH /sobjects/Account/{id}` calls.
✅ Bulk API 2.0 for the volume path, and Composite or `composite/sobjects` to collapse
multiple related operations into one request on the transactional path. Consult
`standards/decision-trees/integration-pattern-selection.md` before choosing; the branch
that matters is record volume against latency requirement.

## Anti-Pattern 7: Instrumenting the org but not the consumer

The dashboard shows org-level consumption, so the team sees the cliff arriving but has no
lever. Attribution has to exist in the consumer's own telemetry too, because that is
where throttling is implemented — Salesforce will refuse the call, but it will not slow a
consumer down for you.

❌ A Salesforce dashboard as the only instrument.
✅ Enforce the token bucket in the middleware, where a request can be delayed rather than
rejected, and reconcile it against `ApiTotalUsage` weekly. The Salesforce-side number is
the audit; the middleware-side number is the control.
