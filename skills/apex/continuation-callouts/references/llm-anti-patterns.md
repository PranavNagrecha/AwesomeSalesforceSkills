# LLM Anti-Patterns — Continuation Callouts

Common mistakes AI coding assistants make when generating or advising on Apex Continuation for long-running HTTP callouts.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Adding the Continuation request but forgetting to register the callback method

**What the LLM generates:**

```apex
@AuraEnabled
public static Object startCallout() {
    Continuation con = new Continuation(60);
    HttpRequest req = new HttpRequest();
    req.setEndpoint('callout:SlowApi/data');
    req.setMethod('GET');
    con.addHttpRequest(req);
    return con; // Missing: con.continuationMethod = 'processResponse';
}
```

**Why it happens:** LLMs generate the request setup but forget to set the `continuationMethod` property. Without it, the platform does not know which method to call when the response arrives, and the continuation silently fails or throws an error.

**Correct pattern:**

```apex
@AuraEnabled
public static Object startCallout() {
    Continuation con = new Continuation(60);
    con.continuationMethod = 'processResponse';
    HttpRequest req = new HttpRequest();
    req.setEndpoint('callout:SlowApi/data');
    req.setMethod('GET');
    con.addHttpRequest(req);
    return con;
}

@AuraEnabled
public static Object processResponse(List<String> labels, Object state) {
    HttpResponse res = Continuation.getResponse(labels[0]);
    return res.getBody();
}
```

**Detection hint:** `new Continuation\(` without a subsequent `continuationMethod\s*=` assignment.

---

## Anti-Pattern 2: Using Continuation from a non-UI context (Queueable, Batch, trigger)

**What the LLM generates:**

```apex
public class MyQueueable implements Queueable {
    public void execute(QueueableContext ctx) {
        Continuation con = new Continuation(60); // Not valid here
        // ...
    }
}
```

**Why it happens:** LLMs know Continuation handles long-running callouts and suggest it for any slow HTTP call. But Continuation only works from Visualforce controllers or `@AuraEnabled` methods invoked by LWC/Aura. In Queueable or Batch context, use standard `Http().send()` with `Database.AllowsCallouts`.

**Correct pattern:**

```apex
// For non-UI async contexts, use standard callouts
public class MyQueueable implements Queueable, Database.AllowsCallouts {
    public void execute(QueueableContext ctx) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:SlowApi/data');
        req.setMethod('GET');
        req.setTimeout(120000); // Up to 120 seconds in async
        HttpResponse res = new Http().send(req);
    }
}
```

**Detection hint:** `new Continuation\(` inside a class implementing `Queueable`, `Database.Batchable`, or `Schedulable`.

---

## Anti-Pattern 3: Exceeding the 3-request limit for parallel continuation callouts

**What the LLM generates:**

```apex
@AuraEnabled
public static Object startCallout() {
    Continuation con = new Continuation(60);
    con.continuationMethod = 'processResponse';
    for (Integer i = 0; i < 5; i++) { // 5 requests — exceeds limit
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:Api/resource/' + i);
        req.setMethod('GET');
        con.addHttpRequest(req);
    }
    return con;
}
```

**Why it happens:** LLMs generate loops that add requests without knowing the platform limit. A single Continuation object supports a maximum of 3 parallel HTTP requests. Adding more throws an exception.

**Correct pattern:**

```apex
@AuraEnabled
public static Object startCallout() {
    Continuation con = new Continuation(60);
    con.continuationMethod = 'processResponse';
    // Maximum 3 parallel requests per Continuation
    for (Integer i = 0; i < 3; i++) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:Api/resource/' + i);
        req.setMethod('GET');
        con.addHttpRequest(req);
    }
    return con;
}
```

**Detection hint:** `addHttpRequest` called more than 3 times on the same `Continuation` object.

---

## Anti-Pattern 4: Storing non-serializable state between the start and callback methods

**What the LLM generates:**

```apex
private transient HttpRequest originalRequest; // Lost between calls

@AuraEnabled
public static Object startCallout() {
    // Cannot use instance variables in static @AuraEnabled context anyway
    Continuation con = new Continuation(60);
    con.continuationMethod = 'processResponse';
    con.state = originalRequest; // Wrong — state must be serializable
    // ...
}
```

**Why it happens:** LLMs try to pass complex objects between the initiating method and the callback. The `state` property on Continuation must be serializable (String, primitive, or simple wrapper). Non-serializable objects are lost.

**Correct pattern:**

```apex
@AuraEnabled
public static Object startCallout(String resourceId) {
    Continuation con = new Continuation(60);
    con.continuationMethod = 'processResponse';
    con.state = resourceId; // Simple serializable state
    HttpRequest req = new HttpRequest();
    req.setEndpoint('callout:Api/resource/' + resourceId);
    req.setMethod('GET');
    con.addHttpRequest(req);
    return con;
}

@AuraEnabled
public static Object processResponse(List<String> labels, Object state) {
    String resourceId = (String) state;
    HttpResponse res = Continuation.getResponse(labels[0]);
    return new Map<String, Object>{
        'resourceId' => resourceId,
        'data' => res.getBody()
    };
}
```

**Detection hint:** `con\.state\s*=` assigned a non-primitive or non-serializable object.

---

## Anti-Pattern 5: Not handling timeout or error responses in the callback method

**What the LLM generates:**

```apex
@AuraEnabled
public static Object processResponse(List<String> labels, Object state) {
    HttpResponse res = Continuation.getResponse(labels[0]);
    return JSON.deserializeUntyped(res.getBody()); // No status check, no timeout handling
}
```

**Why it happens:** LLMs assume the callback always receives a successful response. If the external service times out or returns an error, `getBody()` may be null or contain an error page, causing `JSONException` or `NullPointerException`.

**Correct pattern:**

```apex
@AuraEnabled
public static Object processResponse(List<String> labels, Object state) {
    HttpResponse res = Continuation.getResponse(labels[0]);
    if (res == null) {
        throw new AuraHandledException('Continuation timed out — no response received');
    }
    if (res.getStatusCode() != 200) {
        throw new AuraHandledException('External API error: ' + res.getStatusCode());
    }
    return JSON.deserializeUntyped(res.getBody());
}
```

**Detection hint:** Continuation callback method that calls `getBody()` without checking `getStatusCode()` or null response.

---

## Anti-Pattern 6: Setting the Continuation timeout higher than the Visualforce page timeout

**What the LLM generates:**

```apex
Continuation con = new Continuation(180); // 3 minutes
```

**Why it happens:** LLMs set arbitrary large timeouts. The maximum Continuation timeout is 120 seconds. Setting it higher than that, or higher than the Visualforce page timeout (default 60 seconds), means the page may time out before the Continuation completes, resulting in a confusing user experience.

**Correct pattern:**

```apex
// Keep timeout within platform limits and user experience expectations
Continuation con = new Continuation(60); // 60 seconds — matches VF default
con.continuationMethod = 'processResponse';
```

**Detection hint:** `new Continuation\(\d{3,}\)` — timeout values over 120 seconds.
