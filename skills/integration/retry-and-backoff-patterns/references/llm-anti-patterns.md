# LLM Anti-Patterns — Retry and Backoff Patterns

Common mistakes AI coding assistants make when generating or advising on retry and backoff logic in Salesforce Apex integrations. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Thread.sleep() to Implement Retry Delay

**What the LLM generates:** Code that calls `Thread.sleep(2000)` inside an Apex retry loop to introduce a 2-second delay between attempts.

**Why it happens:** `Thread.sleep()` is the standard Java idiom for retry delay, and Apex is syntactically close to Java. LLMs trained on Java code apply this pattern directly without recognizing that Apex does not expose `Thread.sleep()` as a public method.

**Correct pattern:**

```apex
// WRONG — does not compile in Apex
try {
    res = http.send(req);
} catch (Exception e) {
    Thread.sleep(2000); // Compile error: Method does not exist
    res = http.send(req); // retry
}

// CORRECT — Queueable chaining provides async delay
public void execute(QueueableContext ctx) {
    try {
        res = http.send(req);
    } catch (Exception e) {
        if (retryCount < MAX_RETRIES) {
            System.enqueueJob(new RetryJob(payload, retryCount + 1));
        }
    }
}
```

**Detection hint:** Search generated code for `Thread.sleep` — any occurrence is a compilation error in Apex.

---

## Anti-Pattern 2: Retrying All Non-200 HTTP Status Codes

**What the LLM generates:** A retry handler that retries on any response where `res.getStatusCode() != 200` — including 400, 401, 403, and 404.

**Why it happens:** LLMs generalize "non-success means retry" without applying HTTP semantics. 4xx errors indicate client-side problems (bad request, auth failure, not found) that will never resolve by retrying the same request. This pattern creates infinite retry loops against permanent errors.

**Correct pattern:**

```apex
// WRONG — retries 401 and 404 forever
if (res.getStatusCode() != 200) {
    enqueueRetry();
}

// CORRECT — only retry transient server-side or rate-limit errors
Integer status = res.getStatusCode();
if (status == 429 || (status >= 500 && status != 501)) {
    enqueueRetry();
} else if (status >= 400) {
    // 4xx = permanent client error, write to dead letter immediately
    logDeadLetter('Client error: ' + status);
}
```

**Detection hint:** Look for `!= 200` or `>= 400` retry conditions without filtering out 4xx responses. Also check if 401 handling triggers re-auth before retrying (correct) vs. immediate retry (wrong).

---

## Anti-Pattern 3: Hardcoding Retry Parameters Instead of Using Custom Metadata

**What the LLM generates:** Retry logic with `private static final Integer MAX_RETRIES = 3` and `private static final Integer BASE_DELAY = 2` hardcoded in the Apex class.

**Why it happens:** LLMs default to the simplest implementation. Hardcoded constants are easier to generate than CMDT schema + query. The LLM does not consider operational needs (changing retry behavior without a deploy).

**Correct pattern:**

```apex
// WRONG — cannot adjust without a code change and deploy
private static final Integer MAX_RETRIES = 3;

// CORRECT — operators can adjust in Setup without deploying
Retry_Config__mdt cfg = Retry_Config__mdt.getInstance('ERP_Integration');
Integer maxRetries = (cfg != null) ? (Integer)cfg.Max_Retries__c : 3;
Integer baseDelay  = (cfg != null) ? (Integer)cfg.Base_Delay_Seconds__c : 2;
```

**Detection hint:** Any `private static final` constant for retry parameters in a callout class should be flagged for CMDT extraction.

---

## Anti-Pattern 4: Performing DML Before the Callout in the Retry Handler

**What the LLM generates:** Code that updates `Retry_Count__c` on the driving record or inserts a log entry before calling `Http.send()` in the same `execute()` method.

**Why it happens:** Logging before action is a natural instinct. LLMs do not reliably model the Apex "callout after uncommitted work" rule, which throws a `System.CalloutException` if any DML has occurred in the current transaction before a callout.

**Correct pattern:**

```apex
// WRONG — update before callout triggers "callout after uncommitted work" exception
public void execute(QueueableContext ctx) {
    record.Retry_Count__c = retryCount; // DML
    update record;
    res = http.send(req); // Throws: You have uncommitted work pending
}

// CORRECT — all DML after the callout block
public void execute(QueueableContext ctx) {
    res = http.send(req); // callout first
    // ... handle response
    record.Retry_Count__c = retryCount; // DML after callout
    update record;
}
```

**Detection hint:** In any `execute()` method with both callout and DML, verify that `Http.send()` comes before any `insert`/`update`/`upsert`/`delete` call.

---

## Anti-Pattern 5: Missing Idempotency Key on Retry

**What the LLM generates:** A retry implementation that re-sends the original payload on each attempt without any deduplication mechanism. The LLM generates correct retry mechanics but omits the idempotency key field and header.

**Why it happens:** Idempotency is an integration design concern, not a code mechanics concern. LLMs focus on the retry loop structure and omit the "what if the first request succeeded but the response was lost" scenario.

**Correct pattern:**

```apex
// WRONG — no idempotency key; creates duplicates if first request succeeded
req.setBody('{"orderId":"' + orderId + '"}');
res = http.send(req);

// CORRECT — stable idempotency key preserved across all retry attempts
String idempotencyKey = record.External_Id__c; // Set before first attempt, never regenerated
req.setHeader('X-Idempotency-Key', idempotencyKey);
req.setBody('{"orderId":"' + orderId + '"}');
res = http.send(req);
```

**Detection hint:** Any Queueable retry class that issues POST/PUT/PATCH callouts without an `X-Idempotency-Key` header or equivalent body field should be flagged. Check that the key is generated once before the first enqueue and passed through the constructor on re-enqueue — not regenerated on each attempt.
