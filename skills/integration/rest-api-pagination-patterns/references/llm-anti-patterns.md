# LLM Anti-Patterns — REST API Pagination Patterns

Common mistakes AI coding assistants make when paginating REST APIs.

## Anti-Pattern 1: No safety cap on pagination loop

**What the LLM generates:**

```
while (!done) {
    // fetch
    done = response.done;
}
```

**Why it happens:** Model trusts the API termination signal.

**Correct pattern:**

```
Always pair the termination signal with a safety cap:

Integer MAX_PAGES = 1000;
Integer i = 0;
while (!done && i++ < MAX_PAGES) { ... }
if (i >= MAX_PAGES) throw new IntegrationException('Runaway pagination');

APIs return malformed responses under load. An unbounded loop becomes
the outage.
```

**Detection hint:** `while` loop consuming a paginated API with no iteration counter.

---

## Anti-Pattern 2: Offset pagination over mutable data

**What the LLM generates:**

```
for (Integer offset = 0; offset < total; offset += 100) { ... }
```

**Why it happens:** Model treats the remote collection as stable.

**Correct pattern:**

```
Offset drift: if a record is inserted/deleted between page fetches,
rows are duplicated or missed. Prefer cursor-based pagination.

If offset is the only option:
- Snapshot total at start (don't re-query)
- Filter by created_before=<start_time> to freeze the set
- Or accept the drift and dedupe on the Id column
```

**Detection hint:** Offset-based pagination against an API where records can be inserted/deleted during the window.

---

## Anti-Pattern 3: Ignoring rate-limit headers

**What the LLM generates:** Tight loop requesting pages as fast as possible.

**Why it happens:** Model optimizes for latency.

**Correct pattern:**

```
Inspect X-RateLimit-Remaining and Retry-After headers:

if (resp.getHeader('X-RateLimit-Remaining') == '0') {
    Integer retryAfter = Integer.valueOf(resp.getHeader('Retry-After'));
    // Apex can't sleep — chain Queueable with System.enqueueJob after delay
}

Hammering an API during pagination triggers 429 cascades and bans.
```

**Detection hint:** Apex callout loop that never reads `X-RateLimit-*` or `Retry-After` headers.

---

## Anti-Pattern 4: Single mock response for multi-page test

**What the LLM generates:** `Test.setMock` returning the same JSON for every page.

**Why it happens:** Model misses the mock-per-page requirement.

**Correct pattern:**

```
Implement HttpCalloutMock with call-count state:

public class MultiPageMock implements HttpCalloutMock {
    Integer calls = 0;
    public HttpResponse respond(HttpRequest req) {
        calls++;
        HttpResponse r = new HttpResponse();
        r.setBody(calls == 1 ? page1Json : calls == 2 ? page2Json : emptyJson);
        return r;
    }
}

Single-response mock hides pagination loop bugs.
```

**Detection hint:** Apex test using `Test.setMock` with a single StaticResourceCalloutMock for a multi-page endpoint.

---

## Anti-Pattern 5: Paginating inside a trigger

**What the LLM generates:** Trigger loops HTTP pages inline.

**Why it happens:** Model places the integration where the event fires.

**Correct pattern:**

```
Triggers run in the transaction's 100-callout limit (and callouts
from triggers require @future or Queueable). Enqueue a Queueable
that does the pagination; trigger merely stages the work.

if (!System.isFuture() && !System.isBatch()) {
    System.enqueueJob(new PaginateAccountsQueueable(ids));
}
```

**Detection hint:** Apex trigger containing a `while` loop with `http.send(...)` calls.
