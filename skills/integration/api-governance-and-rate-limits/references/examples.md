# Examples — API Governance and Rate Limits

## Example 1: An overnight ETL reaching 95% of the daily allocation

**Context:** a nightly ETL upserts roughly 200,000 Account and Contact rows through
single-record REST calls. By 03:00 the org is at 95% of its 24-hour allocation, and every
other integration that starts after it fails.

**Problem:** two defects, and only the second is usually noticed. The visible one is
volume: 200,000 rows through a per-record endpoint is 200,000 calls against an allocation
sized in the low hundreds of thousands. The structural one is attribution — the ETL
authenticates as the same integration user as four other systems, so the 95% figure could
not be pinned on it without reading application logs.

**Solution, in the order the work should be done:**

1. **Attribute first.** Give the ETL its own Connected App and its own integration user,
   so `ApiTotalUsage` in Event Monitoring can name the consumer. Until this exists, no
   remediation can be targeted.
2. **Move the volume path to Bulk API 2.0.** A single job ingests the whole file, so
   allocation consumption stops scaling with row count.
3. **Gate the job on measured headroom, not on the clock.**

```apex
public with sharing class EtlGuard {

    public class LimitBreach extends Exception {}

    /** Refuse to start a large job that cannot finish inside remaining headroom. */
    public static void assertHeadroom(Integer estimatedCalls) {
        Map<String, Object> limits = readLimits();
        Map<String, Object> daily  = (Map<String, Object>) limits.get('DailyApiRequests');
        Integer maxCalls  = (Integer) daily.get('Max');
        Integer remaining = (Integer) daily.get('Remaining');

        // /limits is documented as accurate within five minutes of consumption, so
        // leave a margin rather than spending down to the last reported call.
        Integer usable = remaining - Math.max(1000, (Integer) (maxCalls * 0.05));

        if (estimatedCalls > usable) {
            throw new LimitBreach(
                'ETL needs ~' + estimatedCalls + ' calls; usable headroom is ' + usable
                + ' of ' + maxCalls + '. Deferring rather than starving other consumers.');
        }
    }

    private static Map<String, Object> readLimits() {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:MyOrg/services/data/v64.0/limits');
        req.setMethod('GET');
        req.setTimeout(30000);
        return (Map<String, Object>) JSON.deserializeUntyped(new Http().send(req).getBody());
    }
}
```

**Why it works:** the guard converts a shared, invisible resource into an explicit
precondition. A job that would exhaust the allocation now refuses to start and says so,
which is a far better failure than a job that half-completes and takes four unrelated
integrations down with it. The 5% floor exists because the resource is documented as
accurate only within five minutes — spending down to the last reported call means
spending past it.

---

## Example 2: Reacting to the platform's own back-pressure signal

**Context:** an outbound middleware calls Salesforce continuously through the day. It has
no view of allocation until a call fails.

**Problem:** the generated client retries immediately on failure. Against the daily
allocation each retry spends another call from the budget it is waiting for, so the
recovery attempt is itself the thing preventing recovery. Against the concurrency
allocation — documented as 25 concurrent requests over 20 seconds in production orgs and
sandboxes, 5 in Developer Edition and Trial orgs — an immediate retry adds another
concurrent request to the exact resource that is saturated.

**Solution:** read the usage header the REST API returns on every call, and branch the
handler on which limit was hit rather than on the fact that something failed.

In a Node middleware client, every Salesforce REST response carries a usage header —
treat it as continuous back-pressure rather than waiting for an exception:

```javascript
async function callSalesforce(path, options, attempt = 0) {
  const res = await fetch(`${instanceUrl}${path}`, options);

  const limitInfo = res.headers.get('sforce-limit-info');   // api-usage=<used>/<total>
  if (limitInfo) {
    const m = /api-usage=(\d+)\/(\d+)/.exec(limitInfo);
    if (m) {
      const [used, total] = [Number(m[1]), Number(m[2])];
      metrics.gauge('sfdc.api.used_pct', (used / total) * 100);
      // Shed low-priority traffic before the platform starts refusing it.
      if (used / total > 0.85 && options.priority === 'low') {
        throw new DeferError('shedding low-priority traffic above 85% allocation');
      }
    }
  }

  if (res.ok) return res.json();

  const body = await res.json().catch(() => []);
  const errorCode = Array.isArray(body) ? body[0]?.errorCode : body?.errorCode;

  if (errorCode === 'REQUEST_LIMIT_EXCEEDED') {
    // Distinguish the two conditions behind this one code. Only concurrency recovers.
    const remaining = await dailyRemaining();          // GET /services/data/vXX.0/limits
    if (remaining > 0) {
      if (attempt >= 4) throw new Error('concurrency limit: retries exhausted');
      const backoffMs = 2 ** attempt * 1000 + Math.random() * 1000;   // jitter is required
      await sleep(backoffMs);
      return callSalesforce(path, options, attempt + 1);
    }
    circuitBreaker.open('daily allocation exhausted');   // no retry can help
    throw new Error('daily API allocation exhausted; window advances on its own');
  }

  throw new Error(`Salesforce ${res.status} ${errorCode}`);
}
```

**Why it works:** the usage header turns allocation into a continuous signal instead of a
cliff, so low-priority traffic sheds while there is still headroom for the traffic that
matters. Branching `REQUEST_LIMIT_EXCEEDED` on remaining daily allocation is what
separates the recoverable case from the unrecoverable one: with allocation left, the
refusal was concurrency and a jittered backoff clears it in seconds; with none left, no
number of retries moves the 24-hour window, so the circuit breaker is the only correct
response. The jitter is not decoration — without it every queued worker retries in
lockstep and the recovery becomes the next spike.
