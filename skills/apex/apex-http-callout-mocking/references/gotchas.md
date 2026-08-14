# Gotchas — Apex HTTP Callout Mocking

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `Test.startTest()` must come BEFORE `Test.setMock()` when the test does DML first

**What happens:** A test inserts fixture records, calls `Test.setMock`, then invokes a service that makes a callout — and fails with an uncommitted-work exception even though a mock is registered. The order requirement is documented and exact. "By default, callouts aren't allowed after DML operations in the same transaction because DML operations result in pending uncommitted work that prevents callouts from executing." To get around it in a test you must satisfy three conditions together:

- "Enclose the portion of your code that performs the callout within Test.startTest and Test.stopTest statements."
- "The Test.startTest statement must appear before the Test.setMock statement."
- "The calls to DML operations must not be part of the Test.startTest/Test.stopTest block."

**When it occurs:** Almost every realistic callout test, because almost every one needs fixture data. It is also the most common reason a test that passes in isolation fails when someone moves an `insert` two lines down.

**How to avoid:** Fix the shape of the test, not the mock:

```apex
@IsTest
static void syncsOrderAfterInsert() {
    Account a = new Account(Name = 'Acme');
    insert a;                                    // DML: OUTSIDE start/stop

    Test.startTest();                            // 1. startTest first
    Test.setMock(HttpCalloutMock.class,          // 2. then setMock
        new MockHttpResponseGenerator().withResponse(200, '{"id":"A-1"}'));
    OrderSyncService.sync(a.Id);                 // 3. then the callout
    Test.stopTest();

    Assert.areEqual('A-1',
        [SELECT External_Id__c FROM Account WHERE Id = :a.Id].External_Id__c);
}
```

Note this is a *test-context* affordance. It does not make the production code legal — production still needs the callout before the DML, or an async boundary.

---

## Gotcha 2: A registered mock silences the callout entirely, including the endpoint

**What happens:** A test passes for months against a mock while the production endpoint in the Named Credential is wrong, or the code builds a malformed URL. "If an HTTP callout is invoked in test context, the callout is not made and you receive the mock response you specified in the respond method implementation." The mock does not validate the request in any way — endpoint, method, headers, and body all go unchecked unless you check them yourself.

**When it occurs:** Every single-response mock (`StaticResourceCalloutMock`, or a `respond` that ignores its argument). It is why "100% coverage on the integration class" tells you nothing about whether the integration works.

**How to avoid:** Assert on the request inside `respond`. The `HttpRequest` argument is the only place the request is ever observable in a test.

```apex
@IsTest
public class AssertingMock implements HttpCalloutMock {
    public HttpResponse respond(HttpRequest req) {
        Assert.areEqual('POST', req.getMethod());
        Assert.isTrue(req.getEndpoint().startsWith('callout:Acme_API/v2/orders'),
            'Unexpected endpoint: ' + req.getEndpoint());
        Assert.areEqual('application/json', req.getHeader('Content-Type'));
        HttpResponse res = new HttpResponse();
        res.setStatusCode(201);
        res.setBody('{"id":"A-1"}');
        return res;
    }
}
```

---

## Gotcha 3: One mock instance serves every callout in the transaction, so a stateless mock hides pagination bugs

**What happens:** Code that pages through a REST API is tested with a single-response mock. Every page returns the same body, including the same `nextPageToken`, so the loop either terminates for the wrong reason or the test would loop forever if the code were correct. The bug ships. In production the second page arrives with different content and the parser breaks.

**When it occurs:** Pagination, retry-with-backoff, OAuth token-then-resource sequences, and any bulk pattern that calls the same endpoint N times.

**How to avoid:** Use a stateful mock that pops one queued response per call. `templates/apex/tests/MockHttpResponseGenerator.cls` implements this as `pushSequence(status, body)`:

```apex
Test.setMock(HttpCalloutMock.class,
    new MockHttpResponseGenerator()
        .pushSequence(200, '{"records":[{"id":1}],"next":"p2"}')
        .pushSequence(200, '{"records":[{"id":2}],"next":null}'));
```

Sequence entries are consumed in order and removed, so the third call falls through to the default response — which is itself a useful assertion: if your code makes a third call, the body it gets will not parse.

---

## Gotcha 4: The mock class's visibility and `@IsTest` annotation are not interchangeable choices

**What happens:** A team writes the mock as a plain `public class` in the main source directory. It counts against the org's Apex character limit, and in a managed package it becomes part of the package's public surface. Alternatively someone marks it `private` and gets a compile error at the `Test.setMock` call.

**When it occurs:** Any shared mock promoted out of a single test class for reuse.

**How to avoid:** The Apex Developer Guide states the implementation class "can be either global or public" — `private` is not an option — and that it "may be annotated with `@IsTest`" to exclude it from organization code size limits. Use `@IsTest` on any mock that exists only for tests; reserve `global` for mocks a managed package deliberately exposes to subscribers for their own test classes.

---

## Gotcha 5: Mocks never exercise the timeout path, and the real limits are tight

**What happens:** Retry-and-timeout code has full line coverage and has never actually run. Mock responses return instantly, so `setTimeout` is never hit and the `CalloutException` handler is dead code that fails the first time a slow endpoint appears in production.

**When it occurs:** Any integration with a retry policy — which is to say, any integration worth writing tests for.

**How to avoid:** Know the real numbers and design tests against them. "A single Apex transaction can make a maximum of 100 callouts to an HTTP request or an API call." For `HttpRequest.setTimeout`, "the default timeout is 10 seconds", and "the minimum is 1 millisecond and the maximum is 120,000 milliseconds". Critically, "the maximum cumulative timeout for callouts by a single Apex transaction is 120 seconds. This time is additive across all callouts invoked by the Apex transaction" — so a retry loop of three attempts at a 60-second timeout each cannot complete, regardless of how the mock behaves.

To cover the failure handler, make the mock throw rather than return:

```apex
@IsTest
public class TimeoutMock implements HttpCalloutMock {
    public HttpResponse respond(HttpRequest req) {
        throw new CalloutException('Read timed out');
    }
}
```

Then assert that your retry budget respects the 120-second cumulative ceiling — that is arithmetic you check by reading the code, not something any mock can prove.
