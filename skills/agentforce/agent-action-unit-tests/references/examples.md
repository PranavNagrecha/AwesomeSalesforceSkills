# Examples — Agent Action Unit Tests

## Example 1: Per-reason-code test matrix

**Context:** `CloseCaseAction` returns `CLOSED` | `VALIDATION_BLOCKED` | `UNKNOWN`.

**Problem:** the generated test covered only the happy path, so the DML-failure branch
first ran in production, where an ordinary validation rule came back as `UNKNOWN` and
the agent told the customer to phone support.

**Solution:** one test per literal the class can assign to `reasonCode`.

```apex
@IsTest
private class CloseCaseActionTest {

    private static CloseCaseAction.Request reqFor(Id caseId) {
        CloseCaseAction.Request r = new CloseCaseAction.Request();
        r.caseId = caseId;                 // set every @InvocableVariable explicitly:
        r.resolutionNote = 'resolved';     // omitted variables arrive as null, not a default
        return r;
    }

    @IsTest
    static void closedOnHappyPath() {
        Case c = new Case(Status = 'New', Subject = 'ok');
        insert c;
        Test.startTest();
        List<CloseCaseAction.Response> out =
            CloseCaseAction.run(new List<CloseCaseAction.Request>{ reqFor(c.Id) });
        Test.stopTest();
        Assert.areEqual('CLOSED', out[0].reasonCode);
        Assert.areEqual('Closed', [SELECT Status FROM Case WHERE Id = :c.Id].Status);
    }

    @IsTest
    static void validationBlockedKeepsItsOwnCode() {
        Case c = new Case(Status = 'New');
        insert c;
        CloseCaseAction.Request r = reqFor(c.Id);
        r.resolutionNote = null;           // trips Case_Requires_Reason__c
        Test.startTest();
        List<CloseCaseAction.Response> out =
            CloseCaseAction.run(new List<CloseCaseAction.Request>{ r });
        Test.stopTest();
        Assert.areEqual('VALIDATION_BLOCKED', out[0].reasonCode,
            'a DML validation failure must not collapse into UNKNOWN');
    }

    @IsTest
    static void unknownIsReservedForUnanticipatedFailures() {
        Test.startTest();
        List<CloseCaseAction.Response> out =
            CloseCaseAction.run(new List<CloseCaseAction.Request>{ reqFor(null) });
        Test.stopTest();
        Assert.areEqual('UNKNOWN', out[0].reasonCode);
    }
}
```

**Why it works:** the agent branches on `reasonCode`, not on prose. One test per code
makes the error taxonomy an executable specification and keeps `UNKNOWN` meaning "we did
not anticipate this" rather than "something went wrong".

---

## Example 2: Bulk-safety harness

**Context:** Agentforce and Flow Builder both batch invocable calls, so `run()` can
receive many Requests in a single transaction.

**Problem:** a SOQL query inside the per-Request loop walks into the synchronous limit of
100 SOQL queries per transaction, and the size/order contract was never asserted.

**Solution:**

```apex
@IsTest
static void twoHundredRequestsStayWithinLimitsAndKeepOrder() {
    List<Case> cases = new List<Case>();
    for (Integer i = 0; i < 200; i++) {
        cases.add(new Case(Status = 'New', Subject = 'bulk-' + i));
    }
    insert cases;

    List<CloseCaseAction.Request> reqs = new List<CloseCaseAction.Request>();
    for (Case c : cases) {
        CloseCaseAction.Request r = new CloseCaseAction.Request();
        r.caseId = c.Id;
        r.resolutionNote = 'bulk';
        reqs.add(r);
    }

    Test.startTest();                       // fresh limit budget; setup DML excluded
    List<CloseCaseAction.Response> out = CloseCaseAction.run(reqs);
    Integer queriesUsed = Limits.getQueries();
    Test.stopTest();

    Assert.areEqual(reqs.size(), out.size(), 'one Response per Request');
    for (Integer i = 0; i < reqs.size(); i++) {
        Assert.areEqual(reqs[i].caseId, out[i].caseId,
            'the i-th Output must correspond to the i-th Input');
    }
    Assert.isTrue(queriesUsed < 10,
        'query count must not scale with request count; saw ' + queriesUsed);
}
```

**Why it works:** asserting `Limits.getQueries()` inside the `startTest`/`stopTest`
window turns "is it bulkified?" into a number. A per-Request query drives `queriesUsed`
to 200 and fails this assertion well before the platform limit trips, so the failure
message names the real defect instead of surfacing as
`System.LimitException: Too many SOQL queries: 101` from an unrelated line.
