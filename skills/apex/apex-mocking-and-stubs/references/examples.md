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

`Notifier` and the provider are separate top-level classes — an inner class cannot be
stubbed (Apex Developer Guide L42214), and a provider nested inside the test class is an
inner class.

```apex
// Notifier.cls — the seam. Top-level, so it is stubbable.
public interface Notifier {
    Boolean send(String message);
}
```

```apex
// NotifierStubProvider.cls — top-level and public so the test can instantiate it.
// @IsTest keeps it out of the org's 6 MB Apex code size limit (L35417-35418).
@IsTest
public class NotifierStubProvider implements System.StubProvider {

    public String lastMessage;
    public Boolean nextResult = true;

    public Object handleMethodCall(
        Object stubbedObject,
        String stubbedMethodName,
        Type returnType,
        List<Type> paramTypes,
        List<String> paramNames,
        List<Object> args
    ) {
        if (stubbedMethodName == 'send') {
            lastMessage = (String) args[0];
            return nextResult;
        }
        return null;
    }
}
```

```apex
// RenewalServiceTest.cls — the assertion is on what the service SENT, not just on
// what it returned. That is the whole reason to stub rather than to fake.
@IsTest
private class NotifierSeamTest {
    @IsTest
    static void orchestratesWithStubbedNotifier() {
        NotifierStubProvider provider = new NotifierStubProvider();
        Notifier notifier = (Notifier) Test.createStub(Notifier.class, provider);

        Test.startTest();
        Boolean processed = new RenewalService(notifier).processRenewal('R-001');
        Test.stopTest();

        Assert.isTrue(processed, 'Renewal should succeed when the notifier succeeds');
        Assert.isTrue(provider.lastMessage.contains('R-001'),
            'The service must pass the renewal id through to the notifier, got: '
            + provider.lastMessage);
    }

    @IsTest
    static void reportsFailureWhenTheNotifierRefuses() {
        NotifierStubProvider provider = new NotifierStubProvider();
        provider.nextResult = false;
        Notifier notifier = (Notifier) Test.createStub(Notifier.class, provider);

        Test.startTest();
        Boolean processed = new RenewalService(notifier).processRenewal('R-002');
        Test.stopTest();

        Assert.isFalse(processed, 'A refused notification must not report success');
    }
}
```

**Why it works:** The test replaces an internal collaborator cleanly without transport mocks or test-only branching, and the provider's captured state turns "did it call the collaborator correctly?" into an assertion. A fuller, reusable version of this provider — recording every invocation with its parameter names — is in `references/code-examples.md` § 3.

---

## Example 3: Choosing the double — the routing table an agent should apply first

**Context:** A reviewer is handed a test class and asked whether the mocking approach is right.

**Problem:** "Use a mock" is not a decision. The dependency's shape decides, and getting it
wrong produces tests that compile, pass, and prove nothing.

**Solution — walk the table top to bottom and stop at the first match:**

| What is being replaced | Correct double | Registration | Fails if you pick the other one |
|---|---|---|---|
| Outbound HTTP through `Http.send()` | `HttpCalloutMock` (see `templates/apex/tests/MockHttpResponseGenerator.cls`) | `Test.setMock(HttpCalloutMock.class, mock)` | `createStub` cannot touch the `System.Http` type at all |
| Outbound HTTP with large, stable payloads | `StaticResourceCalloutMock` | `Test.setMock(HttpCalloutMock.class, mock)` | Inline JSON drowns the test |
| Several endpoints in one transaction | `MultiStaticResourceCalloutMock` | `Test.setMock(HttpCalloutMock.class, mock)` | A single mock returns the wrong body for the second endpoint |
| WSDL-generated SOAP stub | `WebServiceMock` | `Test.setMock(WebServiceMock.class, mock)` (L35060-35063) | `HttpCalloutMock` never fires; the callout goes to `WebServiceCallout.invoke` |
| Apex collaborator behind an interface | `StubProvider` + `Test.createStub` | `Test.createStub(IThing.class, provider)` | `Test.setMock` does nothing; the real method runs |
| Apex collaborator that is a static utility | **Refactor first** — no double exists | n/a | Statics, including `@future`, are on the cannot-mock list (L42210) |
| A `Database.Batchable` class | **Refactor first** — extract an injectable service | n/a | `Batchable` implementors are on the cannot-mock list (L42216) |

**Why it works:** The first three rows are transport concerns and the runtime intercepts them;
the `StubProvider` row is a language-level substitution; the last two rows are design work
wearing a testing costume. An agent that answers "which row?" before writing code cannot
produce the `Test.setMock`-to-fake-a-service mistake in `references/llm-anti-patterns.md`
anti-pattern 1.

---

## Anti-Pattern: `Test.isRunningTest()` To Skip Real Dependencies

**What practitioners do:** Production code checks `Test.isRunningTest()` and bypasses its dependency.

**What goes wrong:** Tests stop resembling production behavior and the seam problem remains unsolved.

**Correct approach:** Introduce an interface or transport-level mock boundary and use the appropriate test double.
