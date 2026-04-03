# Examples — Apex Mocking And Stubs

## Example 1: Scenario-Specific `HttpCalloutMock`

**Context:** A service retries transient failures from an external endpoint.

**Problem:** One generic success mock never exercises retry logic.

**Solution:**

```apex
@isTest
private class BillingApiTest {
    private class RetryThenSuccessMock implements HttpCalloutMock {
        private static Integer callCount = 0;

        public HTTPResponse respond(HTTPRequest request) {
            callCount++;
            HttpResponse response = new HttpResponse();
            if (callCount == 1) {
                response.setStatusCode(503);
                response.setBody('{"error":"temporary"}');
            } else {
                response.setStatusCode(200);
                response.setBody('{"status":"ok"}');
            }
            return response;
        }
    }

    @isTest
    static void retriesTransientFailure() {
        Test.setMock(HttpCalloutMock.class, new RetryThenSuccessMock());
        Test.startTest();
        BillingApiService.syncInvoice('INV-100');
        Test.stopTest();
        System.assertEquals(true, BillingApiService.lastAttemptSucceeded);
    }
}
```

**Why it works:** The test controls multiple response scenarios from the same dependency and proves retry behavior explicitly.

---

## Example 2: `StubProvider` For A Collaborator Seam

**Context:** A service depends on a notifier abstraction rather than directly using a static helper.

**Problem:** Tests need to verify orchestration without invoking the real notifier implementation.

**Solution:**

```apex
public interface Notifier {
    Boolean send(String message);
}

@isTest
private class NotifierStubProvider implements StubProvider {
    public Object handleMethodCall(
        Object stubbedObject,
        String stubbedMethodName,
        Type returnType,
        List<Type> paramTypes,
        List<String> paramNames,
        List<Object> args
    ) {
        if (stubbedMethodName == 'send') {
            return true;
        }
        return null;
    }
}

@isTest
static void orchestratesWithStubbedNotifier() {
    Notifier notifier = (Notifier) Test.createStub(Notifier.class, new NotifierStubProvider());
    RenewalService service = new RenewalService(notifier);
    System.assertEquals(true, service.processRenewal('R-001'));
}
```

**Why it works:** The test replaces an internal collaborator cleanly without transport mocks or test-only branching.

---

## Anti-Pattern: `Test.isRunningTest()` To Skip Real Dependencies

**What practitioners do:** Production code checks `Test.isRunningTest()` and bypasses its dependency.

**What goes wrong:** Tests stop resembling production behavior and the seam problem remains unsolved.

**Correct approach:** Introduce an interface or transport-level mock boundary and use the appropriate test double.
