# LLM Anti-Patterns — Apex Callout Retry and Resilience

Mistakes AI assistants commonly make when generating Apex callout-retry code.

## 1. Retrying on 4xx responses

LLMs love symmetric loops: "if not success, retry." They generate code like:

```apex
// WRONG
for (Integer i = 0; i < 3; i++) {
    HttpResponse r = http.send(req);
    if (r.getStatusCode() == 200) break;
}
```

This retries 401, 404, 422 — wasting callouts on errors that will NEVER succeed. Always classify the status code: only retry on 408, 429, and 5xx. 4xx (except 408/429) means the caller is wrong; retrying changes nothing.

**Detection hint:** `getStatusCode()` comparison to 200 only, with no branch for 4xx.

---

## 2. Sleep loops via `System.now()` polling

When the LLM realizes Apex has no `Thread.sleep`, it sometimes generates:

```apex
// CATASTROPHICALLY WRONG
DateTime end = System.now().addSeconds(5);
while (System.now() < end) { /* spin */ }
```

This burns the 10-second CPU governor in milliseconds and throws `LimitException: Apex CPU time limit exceeded`. There is no legal sync sleep in Apex. For real backoff, schedule a Queueable with a delayed `nextAttemptAt` field and a Scheduled Apex picker, OR rely on Platform Event re-publish with a delay queue.

**Detection hint:** `while (System.now()` or `while (Datetime.now()` anywhere in callout code paths.

---

## 3. Unbounded retry counts

Generated code often forgets the attempt counter or mis-bounds it:

```apex
// WRONG — no upper bound, depends on circuit-breaker which may be cache-evicted
while (!CalloutCircuitBreaker.isOpen('api')) {
    HttpResponse r = http.send(req);
    if (r.getStatusCode() == 200) return;
}
```

Always have a HARD attempt cap independent of the circuit breaker. Cache-based state can be evicted; the attempt counter must live in the Queueable's instance state or the source record.

**Detection hint:** `while (` containing `http.send` or `Http().send` with no integer comparison in the loop header.

---

## 4. Missing Idempotency-Key on retry of a write operation

LLMs frequently generate retry logic for POST/PUT operations without sending an Idempotency-Key:

```apex
// WRONG — duplicate charges possible
HttpRequest req = new HttpRequest();
req.setMethod('POST');
req.setEndpoint('callout:Payment/charge');
req.setBody(payload);
// retry without Idempotency-Key header → double charge
```

For ANY write retry where the downstream supports it, send `Idempotency-Key`. If the downstream doesn't support it, implement a Salesforce-side dedup table — do NOT silently retry writes.

**Detection hint:** `setMethod('POST'` or `setMethod('PUT'` inside a retry-loop block with no `setHeader('Idempotency-Key'`.

---

## 5. Not separating circuit-breaker state per endpoint

LLMs often generate a single global breaker:

```apex
// WRONG — one bad endpoint blackholes everything
public static Boolean isCircuitOpen() {
    return (Boolean) Cache.Org.get('circuit_open');
}
```

The cache key MUST encode the endpoint: `'ckt:' + endpointName`. Otherwise a flaky `partner-webhook` shuts down `payment-api` too. Reviewers should reject any breaker without an endpoint-scoped key.

**Detection hint:** `Cache.Org.get(` with a hard-coded string that does not include a parameter.

---

## 6. Treating `Test.setMock` as if it accepts a list

Generated tests often write:

```apex
// WRONG — Test.setMock takes ONE mock, not a list
Test.setMock(HttpCalloutMock.class, new List<HttpResponse>{r1, r2, r3});
```

`Test.setMock` accepts a single `HttpCalloutMock` implementation. Sequencing requires a stateful mock class that returns the next response based on its own call counter (see `gotchas.md` #3).

**Detection hint:** `Test.setMock(...)` second argument is a `List<HttpResponse>` literal.

---

## 7. Catching and swallowing `CalloutException` silently

```apex
// WRONG — failure vanishes
try {
    http.send(req);
} catch (Exception e) {
    // ignore
}
```

Empty catch blocks hide both transient AND permanent failures. The dead-letter pattern requires that exhausted retries be RECORDED, not eaten. Any catch block in a callout path must either: rethrow, log to `Failed_Callout__c`, or hand off to a Queueable retry.

**Detection hint:** `catch (...) { }` with empty body within 40 chars of a `try` containing `http.send`.

---

## 8. Recommending `@future` for retry chains

`@future` methods cannot chain (no `System.enqueueJob` equivalent that returns a JobId for follow-on scheduling) and have weaker observability. For retries, use Queueable + `Database.AllowsCallouts`. Reserve `@future` for single fire-and-forget callouts with no retry expectation.

**Detection hint:** `@future(callout=true)` in any code path described as "retry."
