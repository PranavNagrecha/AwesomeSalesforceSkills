# Gotchas — Apex Callout Retry and Resilience

## 1. The 120-second sync callout cap is cumulative AND hard

Salesforce documents a 120-second cumulative HTTP-callout time limit per synchronous transaction. Three retries each with a 30-second `setTimeout(30000)` plus interspersed CPU work CAN exceed it. Once exceeded, every subsequent callout in the transaction throws `CalloutException: Read timed out` with no escape. Always size attempts as `attempts * (timeoutMs + backoffMs) < 120_000` with a safety margin (target < 90s).

## 2. Platform Cache keys are case-sensitive

`Cache.Org.put('ckt:Payment-API', ...)` and `Cache.Org.get('ckt:payment-api')` are different keys. A typo silently creates a NEW circuit that's always CLOSED, and your real circuit never gets read. Pick a convention (lowercase, hyphen-separated) and enforce it via a constant or a small helper that normalizes:

```apex
private static String key(String endpoint) {
    return 'ckt:' + endpoint.toLowerCase();
}
```

## 3. `Test.setMock` returns ONE mock instance — use stateful sequencing

`Test.setMock(HttpCalloutMock.class, mockInstance)` registers a single instance. To return a sequence (e.g. 503, 503, 200), the mock class must hold state:

```apex
public class SequencedMock implements HttpCalloutMock {
    private List<HttpResponse> responses;
    private Integer index = 0;
    public SequencedMock(List<HttpResponse> responses) {
        this.responses = responses;
    }
    public HttpResponse respond(HttpRequest req) {
        HttpResponse r = responses[Math.min(index, responses.size() - 1)];
        index++;
        return r;
    }
}
```

The instance side-effect on `index` works because the mock is the same instance for every call within the test transaction.

## 4. `Limits.getCallouts()` is per-transaction, not per-class

A single trigger can fire multiple handler classes, each issuing callouts. The 100 limit is shared across all of them. Before issuing a retry, check:

```apex
if (Limits.getCallouts() >= Limits.getLimitCallouts() - 1) {
    // No headroom for retry — dead-letter immediately.
    DeadLetter.write(...);
    return;
}
```

This also matters in long Queueable transactions that combine batched work with per-record callouts.

## 5. Async retries do NOT reset the daily callout limit

Each Queueable runs in a fresh transaction (so the 100/120s caps reset), but every callout still counts against the org's 24-hour callout total (per license). A misconfigured circuit breaker that flaps OPEN/CLOSED can issue thousands of probe callouts per day.

## 6. `Database.AllowsCallouts` is required on Queueables that call out

Forgetting the marker interface throws `System.CalloutException: Callout from triggers are currently not supported.` even though the Queueable is itself async. The error message is misleading; the fix is the marker interface.

## 7. Circuit-breaker state in Platform Cache is best-effort

`Cache.Org` entries can be evicted under memory pressure. A circuit "reset" can happen unexpectedly, leading to a burst of probe traffic. Treat the circuit as a **soft** safety net — combine it with a hard per-Queueable attempt cap.

## 8. Idempotency keys must be persisted BEFORE the first attempt

If you generate the key in the same line as the first callout, a retry that re-runs the calling code will generate a new key — defeating dedup. Persist the key on the source record FIRST, commit, then issue the callout. On retry, read the persisted key.

## 9. `Retry-After` header is in seconds OR an HTTP-date

The 429 / 503 `Retry-After` header per RFC 7231 can be either a delta-seconds integer ("120") or an HTTP-date ("Fri, 31 Dec 2027 23:59:59 GMT"). Handle both. In sync context with a 120s cap, if `Retry-After > remaining_budget`, dead-letter immediately rather than burn the rest of the transaction sleeping.
