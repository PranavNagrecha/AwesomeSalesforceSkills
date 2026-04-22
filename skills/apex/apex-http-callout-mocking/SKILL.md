---
name: apex-http-callout-mocking
description: "HttpCalloutMock for Apex tests: HttpCalloutMock interface, StaticResourceCalloutMock, MultiStaticResourceCalloutMock, Test.setMock, multi-call mocks for pagination, error-path mocks. NOT for the callout code itself (use callouts-and-http-integrations). NOT for WSDL callouts (use apex-wsdl2apex-patterns)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
tags:
  - apex
  - testing
  - http-callout
  - mocks
  - test-setmock
triggers:
  - "httpcalloutmock apex test mock http callout"
  - "test.setmock multiple callouts pagination"
  - "staticresourcecalloutmock vs httpcalloutmock which"
  - "multistaticresourcecalloutmock endpoint routing test"
  - "mock http response error 500 apex retry test"
  - "you have uncommitted work pending callout test"
inputs:
  - Callout shape (endpoints, verbs, headers)
  - Number of calls per test
  - Error scenarios to exercise
outputs:
  - HttpCalloutMock implementation
  - Test method with Test.setMock
  - Multi-call routing logic
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-22
---

# Apex HTTP Callout Mocking

Activate when testing Apex code that makes HTTP callouts. Apex disallows real HTTP during tests; you MUST supply a mock via `Test.setMock`. The default single-response mock covers simple cases, but pagination, retry, and multi-endpoint flows require stateful mocks.

## Before Starting

- **Enumerate callouts.** How many requests, which endpoints, which status-code paths?
- **Pick the mock shape.** Single response → `StaticResourceCalloutMock`. Multiple responses → custom `HttpCalloutMock`. Per-endpoint routing → `MultiStaticResourceCalloutMock`.
- **Load-bearing response body content.** Store JSON in a `StaticResource` instead of inline strings to keep tests reviewable.

## Core Concepts

### HttpCalloutMock interface

```
public class MyMock implements HttpCalloutMock {
    public HttpResponse respond(HttpRequest req) {
        HttpResponse r = new HttpResponse();
        r.setStatusCode(200);
        r.setBody('{"ok":true}');
        return r;
    }
}
```

Register via `Test.setMock(HttpCalloutMock.class, new MyMock());` before the code-under-test runs.

### StaticResourceCalloutMock

```
StaticResourceCalloutMock m = new StaticResourceCalloutMock();
m.setStaticResource('OrderResponse');  // StaticResource with JSON body
m.setStatusCode(200);
m.setHeader('Content-Type', 'application/json');
Test.setMock(HttpCalloutMock.class, m);
```

Stores the response body in metadata; best for large fixtures.

### MultiStaticResourceCalloutMock

```
MultiStaticResourceCalloutMock m = new MultiStaticResourceCalloutMock();
m.setStaticResource('https://api/x/orders', 'OrdersResponse');
m.setStaticResource('https://api/x/accounts', 'AccountsResponse');
m.setStatusCode(200);
m.setHeader('Content-Type', 'application/json');
Test.setMock(HttpCalloutMock.class, m);
```

Routes by request endpoint; single mock handles multiple distinct endpoints.

### Multi-call stateful mock (pagination)

```
public class PageMock implements HttpCalloutMock {
    private Integer call = 0;
    private List<String> bodies;
    public PageMock(List<String> bodies) { this.bodies = bodies; }
    public HttpResponse respond(HttpRequest req) {
        HttpResponse r = new HttpResponse();
        r.setStatusCode(200);
        r.setBody(call < bodies.size() ? bodies[call++] : '{}');
        return r;
    }
}
```

Required when a single endpoint is called multiple times and each response differs (pagination, retry).

### Uncommitted-work-pending error

If DML precedes a callout in the same transaction, Salesforce throws `CalloutException: You have uncommitted work pending`. Cannot be "fixed" in a mock — refactor to Queueable or call DML AFTER all callouts complete.

## Common Patterns

### Pattern: Error-path test

```
public class ErrorMock implements HttpCalloutMock {
    public HttpResponse respond(HttpRequest req) {
        HttpResponse r = new HttpResponse();
        r.setStatusCode(500);
        r.setBody('{"error":"down"}');
        return r;
    }
}

@IsTest static void testHandlesServerError() {
    Test.setMock(HttpCalloutMock.class, new ErrorMock());
    Test.startTest();
    Boolean result = OrderService.fetch();
    Test.stopTest();
    System.assertEquals(false, result);
}
```

### Pattern: Endpoint-dispatched mock

```
public class Router implements HttpCalloutMock {
    public HttpResponse respond(HttpRequest req) {
        HttpResponse r = new HttpResponse();
        r.setStatusCode(200);
        if (req.getEndpoint().contains('/orders')) r.setBody(ORDERS_JSON);
        else if (req.getEndpoint().contains('/auth')) r.setBody(AUTH_JSON);
        else r.setStatusCode(404);
        return r;
    }
}
```

### Pattern: Header assertion

```
public class HeaderMock implements HttpCalloutMock {
    public static String capturedAuth;
    public HttpResponse respond(HttpRequest req) {
        capturedAuth = req.getHeader('Authorization');
        // ... return response
    }
}
// In test: assert HeaderMock.capturedAuth == 'Bearer expected_token'
```

## Decision Guidance

| Situation | Mock |
|---|---|
| One endpoint, one response | `StaticResourceCalloutMock` |
| Many endpoints, one each | `MultiStaticResourceCalloutMock` |
| One endpoint, multiple calls returning different bodies | Custom `HttpCalloutMock` with call counter |
| Error-path testing | Custom mock returning non-2xx |
| Assert on request headers/body | Custom mock capturing into static fields |

## Recommended Workflow

1. Identify every callout the test exercises (endpoint, verb, count).
2. Store large JSON fixtures as `StaticResource` files.
3. Choose mock type per the decision table.
4. For multi-call: implement counter-based `HttpCalloutMock`.
5. Register via `Test.setMock` BEFORE the code-under-test is invoked.
6. For error paths, add a parallel test with an error-returning mock.
7. Assert on side-effects AND, where relevant, on captured request fields.

## Review Checklist

- [ ] `Test.setMock` called before the code-under-test runs
- [ ] Multi-call scenarios use a stateful custom mock (not a single-response mock reused)
- [ ] Error-path test present (non-2xx status)
- [ ] Large fixtures in `StaticResource`, not inline
- [ ] Test does no DML between callouts that triggers "uncommitted work pending"
- [ ] Request-level assertions (headers/body) where security/auth matters

## Salesforce-Specific Gotchas

1. **`Test.setMock` must be called before any callout in the transaction.** Calling it after the first callout is ignored.
2. **You cannot perform a real callout in a test even with no `setMock` — it throws.** Forgetting to set a mock yields a test failure, not a skip.
3. **`HttpCalloutMock` respond method runs within the test's governor context** — don't do heavy DML inside it.
4. **`MultiStaticResourceCalloutMock` matches the endpoint string literally** — query parameters in the request but not the mock registration cause misses.

## Output Artifacts

| Artifact | Description |
|---|---|
| Custom `HttpCalloutMock` | Stateful mock for multi-call tests |
| `StaticResource` JSON fixtures | Reviewable response bodies |
| Error-path mocks | 4xx/5xx responses |
| Header-capture mock | Assertion helper for request validation |

## Related Skills

- `apex/apex-test-setup-patterns` — test structure + startTest/stopTest
- `apex/callouts-and-http-integrations` — the callout code itself
- `integration/rest-api-pagination-patterns` — pagination tests need multi-call mocks
