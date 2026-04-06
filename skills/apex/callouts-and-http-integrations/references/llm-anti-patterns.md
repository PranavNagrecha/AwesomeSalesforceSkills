# LLM Anti-Patterns — Callouts and HTTP Integrations

Common mistakes AI coding assistants make when generating or advising on outbound Apex HTTP callouts.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Hardcoding endpoint URLs and credentials instead of using Named Credentials

**What the LLM generates:**

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('https://api.example.com/v1/data');
req.setHeader('Authorization', 'Bearer ' + apiKey); // Hardcoded or from Custom Setting
req.setMethod('GET');
```

**Why it happens:** LLMs generate the simplest working callout. Hardcoded endpoints fail the Salesforce security review, cannot be promoted across environments (sandbox to production), and store credentials in code or queryable settings.

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

**Why it happens:** LLMs generate code linearly — insert the record, then notify the external system. But Salesforce prohibits callouts after uncommitted DML in the same transaction. The `CalloutException: You have uncommitted work pending` is one of the most common integration errors.

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

**Why it happens:** LLMs omit `setTimeout` because the default (10,000ms) often works in examples. In production, a slow external service can hold the Apex thread for 10 seconds per callout, consuming the 120-second total timeout budget. Not setting it explicitly also makes the behavior invisible to code reviewers.

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

**Why it happens:** LLMs generate callouts inline without considering that Apex triggers do not support synchronous callouts. This throws `System.CalloutException: Callout from triggers are not supported`.

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

**Why it happens:** LLMs forget that real HTTP callouts are blocked in test context. Without `Test.setMock(HttpCalloutMock.class, ...)`, the test throws `System.CalloutException: You have uncommitted work pending` or `Callout not allowed`.

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
