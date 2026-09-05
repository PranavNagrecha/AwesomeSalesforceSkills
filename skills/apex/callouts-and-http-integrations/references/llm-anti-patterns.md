# LLM Anti-Patterns — Callouts and HTTP Integrations

Common mistakes AI coding assistants make when generating or advising on outbound Apex HTTP callouts.
These patterns help the consuming agent self-check its own output.

Line references are into the **Apex Developer Guide v67.0, Summer '26** (`apexdev`) and the **Apex
Reference Guide v67.0** (`apexrefguide`).

## Anti-Pattern 1: Hardcoding endpoint URLs and credentials instead of using Named Credentials

**What the LLM generates:**

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('https://api.example.com/v1/data');
req.setHeader('Authorization', 'Bearer ' + apiKey); // Hardcoded or from Custom Setting
req.setMethod('GET');
```

**Why it happens:** LLMs generate the simplest working callout. A literal URL also drags in a Remote Site Setting the generated code never mentions: "Before any Apex callout can call an external site, that site must be registered in the Remote Site Settings page, or the callout fails" — and "if the callout specifies a named credential as the endpoint, you don't need to configure remote site settings" (apexdev L34293–34299). The Named Credential form is also the packaging-safe one: create the same-named credential with a different URL per org and "the Apex class that defines the callout can be packaged and deployed on all those orgs without programmatically checking the environment" (apexdev L34327–34331). UNVERIFIED (2026-09-05): the frequently repeated claim that hardcoded endpoints fail AppExchange security review is not stated in any of the v67.0 developer guides — treat it as folklore, not a citable rule.

**Correct pattern:**

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:MyExternalApi/v1/data'); // Named Credential handles auth
req.setMethod('GET');
HttpResponse res = new Http().send(req);
```

**Detection hint:** `setEndpoint\('https?://` — hardcoded URLs instead of `callout:` prefix.

---

## Anti-Pattern 2: Making a callout after DML in the same transaction

**What the LLM generates:**

```apex
insert new Account(Name = 'New Account');
// DML committed — now callout throws
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:ExternalApi/notify');
new Http().send(req); // System.CalloutException: uncommitted work pending
```

**Why it happens:** LLMs generate code linearly — insert the record, then notify the external system. But Salesforce prohibits callouts after uncommitted DML in the same transaction. The exact message is `You have uncommitted work pending. Please commit or rollback before calling out.` (apexdev L8769–8770), and the blocking set is wider than DML: "queueable jobs (that are queued with System.enqueueJob), Database.executeBatch, or future methods" all count (apexdev L35379–35380). Option 1 below is legal because "you can make callouts before performing these types of operations" (apexdev L35862–35863).

**Correct pattern:**

```apex
// Option 1: Callout first, then DML
HttpResponse res = new Http().send(req);
insert new Account(Name = 'New Account');

// Option 2: Defer the callout to a Queueable
insert new Account(Name = 'New Account');
System.enqueueJob(new NotifyExternalApiJob(accountId));
```

**Detection hint:** `insert ` or `update ` DML statements appearing before `Http\(\)\.send` in the same method without an intervening async boundary.

---

## Anti-Pattern 3: Not setting a timeout on HttpRequest

**What the LLM generates:**

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:SlowApi/data');
req.setMethod('GET');
// No setTimeout — defaults to 10 seconds, may be too long or too short
HttpResponse res = new Http().send(req);
```

**Why it happens:** LLMs omit `setTimeout` because the default works in examples — "the default timeout is 10 seconds. A custom timeout can be defined for each callout. The minimum is 1 millisecond and the maximum is 120,000 milliseconds" (apexdev L35854–35855). In production, a slow external service consumes the shared budget: "the maximum cumulative timeout for callouts by a single Apex transaction is 120 seconds … additive across all callouts" (apexdev L35856–35857). Note what the value actually bounds — it is "the maximum time to wait for establishing the HTTP connection", and once the request is executing "the connection is kept alive until the request finishes" (apexrefguide L216720–216723). A short `setTimeout` is not a wall-clock cap.

**Correct pattern:**

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:SlowApi/data');
req.setMethod('GET');
req.setTimeout(5000); // Explicit 5-second timeout
HttpResponse res = new Http().send(req);
```

**Detection hint:** `HttpRequest` usage without a `setTimeout` call before `send`.

---

## Anti-Pattern 4: Not checking the response status code before parsing the body

**What the LLM generates:**

```apex
HttpResponse res = new Http().send(req);
Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
String value = (String) body.get('data'); // NPE if response was 500 with different body
```

**Why it happens:** LLMs assume every response is a 200 with valid JSON. A 500, 401, or 503 response may have a completely different body structure (HTML error page, empty body, or XML), causing `JSONException` or `NullPointerException`.

**Correct pattern:**

```apex
HttpResponse res = new Http().send(req);
if (res.getStatusCode() == 200) {
    Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
    return (String) body.get('data');
} else if (res.getStatusCode() == 401) {
    throw new IntegrationException('Authentication failed — check Named Credential');
} else {
    throw new IntegrationException('API error ' + res.getStatusCode() + ': ' + res.getBody());
}
```

**Detection hint:** `JSON.deserialize` immediately after `Http\(\)\.send` without checking `getStatusCode()`.

---

## Anti-Pattern 5: Making callouts inside a trigger synchronously

**What the LLM generates:**

```apex
trigger AccountTrigger on Account (after insert) {
    for (Account a : Trigger.new) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:ExternalCRM/notify');
        req.setMethod('POST');
        req.setBody(JSON.serialize(a));
        new Http().send(req); // Callout from trigger — not allowed
    }
}
```

**Why it happens:** LLMs generate callouts inline without considering the trigger rule: "Callouts must be made asynchronously from a trigger so that the trigger process isn't blocked while waiting for the external service's response. The asynchronous callout is made in a background process, and the response is received when the external service returns it" (apexdev L14900–14903). UNVERIFIED (2026-09-05): earlier versions of this file quoted a `System.CalloutException: Callout from triggers are not supported` message — that string appears nowhere in the v67.0 Apex Developer Guide or Apex Reference Guide. Do not assert it. The failure a trigger callout most reliably produces in practice is the uncommitted-work exception of Anti-Pattern 2, because an after-trigger runs inside the save transaction.

**Correct pattern:**

```apex
trigger AccountTrigger on Account (after insert) {
    List<Id> newIds = new List<Id>();
    for (Account a : Trigger.new) {
        newIds.add(a.Id);
    }
    if (!newIds.isEmpty()) {
        System.enqueueJob(new ExternalCrmNotifyJob(newIds));
    }
}
```

**Detection hint:** `Http\(\)\.send` or `new Http\(\)` appearing inside a trigger file or a class called directly from trigger context without async dispatch.

---

## Anti-Pattern 6: Not implementing HttpCalloutMock for tests

**What the LLM generates:**

```apex
@IsTest
static void testCallout() {
    // No mock registered
    Test.startTest();
    String result = MyService.callExternalApi(); // Throws CalloutException in test
    Test.stopTest();
}
```

**Why it happens:** LLMs forget that real HTTP callouts are blocked in test context: "By default, test methods don't support HTTP callouts, so tests that perform callouts fail" (apexdev L35384–35385). UNVERIFIED (2026-09-05): the guides do not print the message text for this failure, and the two strings earlier versions of this file asserted are not in them. Cite the behaviour, not a message. The related — and separately grounded — trap is a test that *does* set a mock but inserts data first: `Test.startTest()` must precede `Test.setMock(...)`, and the DML must sit outside the start/stop block (apexdev L35677–35681).

**Correct pattern:**

```apex
@IsTest
static void testCallout() {
    Test.setMock(HttpCalloutMock.class, new MockHttpResponse(200, '{"status":"ok"}'));
    Test.startTest();
    String result = MyService.callExternalApi();
    Test.stopTest();
    System.assertEquals('ok', result);
}
```

**Detection hint:** Test methods that call code containing `Http().send` without a preceding `Test.setMock` call.


---

## Anti-Pattern 7: Retrying a non-idempotent POST with no idempotency key

**What the LLM generates:**

```apex
for (Integer attempt = 0; attempt < 3; attempt++) {
    HttpResponse res = new Http().send(req);   // same POST, no dedupe token
    if (res.getStatusCode() == 200) { break; }
}
```

**Why it happens:** "retry on failure" is a reflex, and the generated loop treats every non-200 as
"nothing happened". A `500` or a transport failure genuinely means *unknown*: the remote system may
have committed the write and lost the reply. Retrying a bare POST three times can create three
orders. Read-only mode makes this concrete — "during read-only mode, Apex callouts to external
services execute and aren't blocked by the system", while the Salesforce-side update that would have
recorded the result is blocked (apexdev L35869–35874).

**Correct pattern:**

```apex
req.setHeader('Idempotency-Key', invoice.Id + '-' + invoice.CreatedDate.getTime());
```

Send a stable, request-scoped key the remote system can deduplicate on, retry only what the response
classification marked retryable, and never retry `401`/`403`/`4xx`-validation. The in-transaction
loop is also the wrong place: Apex has no `sleep`, so any backoff is a busy-wait against the CPU
ceiling (10,000 ms sync / 60,000 ms async, apexdev L19579). Retry across job boundaries — see
`references/code-examples.md` §2 and apex/apex-callout-retry-and-resilience.

**Detection hint:** a `for`/`while` loop containing `Http().send` in the same method, or a POST/PUT
request with no `Idempotency-Key`-style header.

---

## Anti-Pattern 8: Attaching a body to a GET request

**What the LLM generates:**

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:SearchApi/v1/search');
req.setMethod('GET');
req.setBody(JSON.serialize(criteria));   // silently promotes the call to POST
```

**Why it happens:** several popular HTTP clients outside Salesforce allow a GET body, so the pattern
transfers. On the platform it does not fail — it changes: "When you set a request body in the
callout, set the method to POST. If you set a request body and the request method is GET, a POST
request is performed" (apexdev L35377–35378). The remote system sees a POST the code never asked for.

**Correct pattern:**

```apex
// Query string on the Named Credential URL — "use a question mark (?) as the
// separator between the named credential URL and the query string" (apexdev L34335–34336)
req.setEndpoint('callout:SearchApi/v1/search?q=' + EncodingUtil.urlEncode(term, 'UTF-8'));
req.setMethod('GET');
```

**Detection hint:** `setMethod('GET')` and `setBody`/`setBodyAsBlob` on the same request variable.
