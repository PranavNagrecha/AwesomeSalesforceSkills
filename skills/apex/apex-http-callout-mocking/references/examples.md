# Examples — Apex HTTP Callout Mocking

## Example 1: Paginated fetch, tested with a sequenced mock

**Context:** `OrderSyncService.pullAll()` pages through a partner REST API until the response's `next` token is null, upserting each page. The team needs coverage that proves the loop terminates on the token, not on an arbitrary iteration cap.

**Problem:** A single-response mock returns the same body for every call. The loop either never terminates or terminates for the wrong reason, and either way the test tells you nothing about the pagination logic. Meanwhile the test needs to insert an Account first, which puts DML before the callout.

**Solution:**

```apex
@IsTest
private class OrderSyncServiceTest {

    private static final String PAGE_1 =
        '{"records":[{"externalId":"O-1"},{"externalId":"O-2"}],"next":"cursor-2"}';
    private static final String PAGE_2 =
        '{"records":[{"externalId":"O-3"}],"next":null}';

    @IsTest
    static void pullsEveryPageAndStopsOnNullCursor() {
        Account partner = new Account(Name = 'Acme Distribution');
        insert partner;                      // DML stays OUTSIDE start/stop

        Test.startTest();                    // startTest BEFORE setMock
        Test.setMock(HttpCalloutMock.class,
            new MockHttpResponseGenerator()  // templates/apex/tests/
                .pushSequence(200, PAGE_1)
                .pushSequence(200, PAGE_2));
        OrderSyncService.pullAll(partner.Id);
        Test.stopTest();

        List<Order__c> loaded = [
            SELECT External_Id__c FROM Order__c WHERE Partner__c = :partner.Id
            ORDER BY External_Id__c
        ];
        Assert.areEqual(3, loaded.size(), 'Expected both pages to be consumed');
        Assert.areEqual('O-1', loaded[0].External_Id__c);
        Assert.areEqual('O-3', loaded[2].External_Id__c);
    }
}
```

**Why it works:** `pushSequence` queues responses that are popped one per `respond()` call, so page 2 genuinely differs from page 1 and the `next == null` branch is the only thing that can stop the loop. The `startTest` / `setMock` / DML ordering satisfies all three documented conditions for performing DML before a mock callout — "The Test.startTest statement must appear before the Test.setMock statement" and "The calls to DML operations must not be part of the Test.startTest/Test.stopTest block."

If a third page were requested, the sequence would be exhausted and the mock would fall through to its default `{}` body — which fails the assertion loudly rather than passing silently.

---

## Example 2: Routing by endpoint, and asserting on the request

**Context:** An auth-then-resource flow: the service posts to `/oauth/token`, then GETs `/v2/accounts` with the returned bearer. The security review requires proof that the token actually reaches the second request's `Authorization` header.

**Problem:** A single-response mock cannot serve two different endpoints, and no mock validates the request unless you write the assertion yourself. Coverage on the auth path is meaningless if the header is never inspected.

**Solution:**

```apex
@IsTest
public class AuthFlowMock implements HttpCalloutMock {

    public static String capturedAuthHeader;
    public static Integer callCount = 0;

    public HttpResponse respond(HttpRequest req) {
        callCount++;
        HttpResponse res = new HttpResponse();
        res.setHeader('Content-Type', 'application/json');

        if (req.getEndpoint().contains('/oauth/token')) {
            Assert.areEqual('POST', req.getMethod(), 'Token request must be POST');
            res.setStatusCode(200);
            res.setBody('{"access_token":"tok-abc123","expires_in":3600}');
            return res;
        }

        if (req.getEndpoint().contains('/v2/accounts')) {
            capturedAuthHeader = req.getHeader('Authorization');
            res.setStatusCode(200);
            res.setBody('{"records":[{"id":"A-1","name":"Acme"}]}');
            return res;
        }

        res.setStatusCode(404);
        res.setBody('{"error":"unexpected endpoint ' + req.getEndpoint() + '"}');
        return res;
    }
}
```

```apex
@IsTest
static void forwardsBearerTokenToResourceCall() {
    Test.startTest();
    Test.setMock(HttpCalloutMock.class, new AuthFlowMock());
    AccountFetchService.fetchAll();
    Test.stopTest();

    Assert.areEqual(2, AuthFlowMock.callCount, 'Expected token call then resource call');
    Assert.areEqual('Bearer tok-abc123', AuthFlowMock.capturedAuthHeader,
        'Resource call did not carry the token returned by the auth call');
}
```

**Why it works:** One mock instance serves every callout in the transaction, so branching on `req.getEndpoint()` is how you serve two endpoints from one registration. The static capture fields turn the mock into an assertion surface — without them the test proves only that the code did not throw. The explicit 404 fallback converts a typo in the production endpoint into a failing test rather than a silently reused response.

The mock is annotated `@IsTest`, which the Apex Developer Guide notes excludes it from organization code size limits; it is `public` because the implementation class "can be either global or public" — `private` will not compile at the `Test.setMock` call.

---

## Anti-Pattern: Reusing one `StaticResourceCalloutMock` for a retry test

**What practitioners do:** Test the retry path by registering `StaticResourceCalloutMock` with a 500 status and asserting the method returns false.

**What goes wrong:** Every attempt gets 500, so the test proves only that the code gives up. It never proves the interesting behaviour — that attempt 2 succeeds after attempt 1 fails, and that the caller sees the successful result. The recovery path stays uncovered while showing green coverage. Worse, a retry loop tuned against an all-failing mock hides the real ceiling: "the maximum cumulative timeout for callouts by a single Apex transaction is 120 seconds", additive across every callout in the transaction, and a transaction may make at most 100 callouts.

**Correct approach:** Sequence the responses so the failure is transient.

```apex
Test.setMock(HttpCalloutMock.class,
    new MockHttpResponseGenerator()
        .pushSequence(503, '')
        .pushSequence(200, '{"ok":true}'));
```

Then assert both that the final result is success *and* that exactly two callouts were made — because a retry policy that quietly makes six attempts is a production incident waiting on a slow day.
