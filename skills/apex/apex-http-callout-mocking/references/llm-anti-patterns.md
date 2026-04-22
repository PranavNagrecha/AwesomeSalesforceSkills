# LLM Anti-Patterns — Apex HTTP Callout Mocking

Common mistakes AI coding assistants make when mocking HTTP callouts in Apex tests.

## Anti-Pattern 1: Single mock response for a paginated test

**What the LLM generates:** A `StaticResourceCalloutMock` with one body reused for every page.

**Why it happens:** Model forgets each call needs a distinct response.

**Correct pattern:**

```
public class PageMock implements HttpCalloutMock {
    private Integer call = 0;
    public HttpResponse respond(HttpRequest req) {
        call++;
        HttpResponse r = new HttpResponse();
        r.setStatusCode(200);
        r.setBody(call == 1 ? PAGE1 : call == 2 ? PAGE2 : EMPTY);
        return r;
    }
}

A single-response mock masks pagination bugs — the loop either
exits immediately (done=true) or loops infinitely (done=false),
neither of which exercises the real traversal.
```

**Detection hint:** Paginating code-under-test + single `StaticResourceCalloutMock` in its test.

---

## Anti-Pattern 2: Inline giant JSON bodies in mocks

**What the LLM generates:** 300 lines of JSON concatenated in a `String` literal inside the mock class.

**Why it happens:** Model avoids asking about StaticResource.

**Correct pattern:**

```
Use StaticResourceCalloutMock:
- Save the JSON as a file named OrderResponse.json
- Upload as a StaticResource named OrderResponse
- In test:
    StaticResourceCalloutMock m = new StaticResourceCalloutMock();
    m.setStaticResource('OrderResponse');
    m.setStatusCode(200);
    Test.setMock(HttpCalloutMock.class, m);

Benefits: diffable fixtures, reusable across tests, reviewable
by QA without reading Apex.
```

**Detection hint:** `r.setBody('{\"...\":' + ...)` with hundreds of characters inline.

---

## Anti-Pattern 3: No error-path test

**What the LLM generates:** One test with a 200 mock and assertions for success. No 4xx/5xx variant.

**Why it happens:** Model optimizes happy path.

**Correct pattern:**

```
Every callout touched by a test class should have paired happy +
error tests:

@IsTest static void testServerDown() {
    Test.setMock(HttpCalloutMock.class, new ErrorMock(500));
    // invoke code, assert graceful failure
}

Real APIs return 429, 500, 502, 503 regularly. Code that never
sees those paths in tests ships half-baked retry logic.
```

**Detection hint:** Test class with exactly one mock returning 200, no 4xx/5xx variants.

---

## Anti-Pattern 4: DML before callout in test

**What the LLM generates:**

```
@IsTest static void t() {
    insert new Account(Name = 'X');
    Test.setMock(HttpCalloutMock.class, new Mock());
    OrderService.fetch();  // CalloutException: uncommitted work pending
}
```

**Why it happens:** Model writes tests in narrative order (set up data, call service).

**Correct pattern:**

```
Callouts forbid prior uncommitted DML in the same transaction.
Options:
1. Move DML to @TestSetup (commits before the test method runs)
2. Call the callout path via Queueable / @future (async context
   gets a fresh transaction)
3. Flush DML explicitly: not possible in sync Apex

If using @TestSetup, the data is visible to the test method
without incurring uncommitted-work-pending.
```

**Detection hint:** Test method with `insert`/`update` before `Test.setMock` or callout invocation.

---

## Anti-Pattern 5: `Test.setMock` inside `Test.startTest()` block

**What the LLM generates:**

```
Test.startTest();
Test.setMock(HttpCalloutMock.class, new Mock());
OrderService.fetch();
Test.stopTest();
```

**Why it happens:** Model groups test boilerplate together.

**Correct pattern:**

```
Works — but convention is to call Test.setMock BEFORE startTest,
so the mock is in place before the governor reset:

Test.setMock(HttpCalloutMock.class, new Mock());
Test.startTest();
OrderService.fetch();
Test.stopTest();

More importantly: if a class-setup method also does callouts (rare),
setMock inside a specific test won't apply to setup. Setting once
per method is always safe.
```

**Detection hint:** `Test.setMock` ordered after `Test.startTest()` with no specific reason.
