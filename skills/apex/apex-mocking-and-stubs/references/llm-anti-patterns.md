# LLM Anti-Patterns — Apex Mocking and Stubs

Common mistakes AI coding assistants make when generating or advising on Apex test doubles, mocking, and stub patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Test.setMock for internal service dependencies instead of StubProvider

**What the LLM generates:**

```apex
// Trying to mock an internal Apex service class with HttpCalloutMock
Test.setMock(HttpCalloutMock.class, new MyServiceMock());
```

**Why it happens:** LLMs conflate "mocking" with `Test.setMock`. `Test.setMock` is exclusively for platform-level transport mocking (HTTP callouts, web service callouts). It cannot replace an internal Apex collaborator. For those, use `StubProvider` or a manual test double via an interface.

**Correct pattern:**

```apex
public interface IAccountSelector {
    List<Account> selectByIds(Set<Id> ids);
}

// In test:
IAccountSelector stub = (IAccountSelector) Test.createStub(
    IAccountSelector.class, new AccountSelectorStub()
);
```

**Detection hint:** `Test\.setMock\(HttpCalloutMock` where the mock class does not implement `HttpCalloutMock` or is being used for a non-callout purpose.

---

## Anti-Pattern 2: Implementing HttpCalloutMock with a single hardcoded response for all endpoints

**What the LLM generates:**

```apex
public class MockHttp implements HttpCalloutMock {
    public HTTPResponse respond(HTTPRequest req) {
        HttpResponse res = new HttpResponse();
        res.setStatusCode(200);
        res.setBody('{"status":"ok"}');
        return res;
    }
}
```

**Why it happens:** LLMs generate the minimal mock. When the code under test makes multiple callouts to different endpoints, this mock returns the same response for both, masking bugs in response-specific parsing.

**Correct pattern:**

```apex
public class MockHttp implements HttpCalloutMock {
    public HTTPResponse respond(HTTPRequest req) {
        HttpResponse res = new HttpResponse();
        String endpoint = req.getEndpoint();
        if (endpoint.contains('/oauth/token')) {
            res.setStatusCode(200);
            res.setBody('{"access_token":"fake-token"}');
        } else if (endpoint.contains('/api/data')) {
            res.setStatusCode(200);
            res.setBody('{"records":[]}');
        } else {
            res.setStatusCode(404);
            res.setBody('{"error":"unknown endpoint"}');
        }
        return res;
    }
}
```

**Detection hint:** `HttpCalloutMock` implementation whose `respond` method never inspects `req.getEndpoint()` or `req.getMethod()`.

---

## Anti-Pattern 3: Forgetting that StubProvider only works with instance methods on interfaces or virtual classes

**What the LLM generates:**

```apex
// Attempting to stub a static method — this will NOT intercept static calls
public class UtilityStub implements System.StubProvider {
    public Object handleMethodCall(Object stubbedObject, String stubbedMethodName,
        Type returnType, List<Type> listOfParamTypes,
        List<String> listOfParamNames, List<Object> listOfArgs) {
        if (stubbedMethodName == 'calculateTax') return 0.10;
        return null;
    }
}
// TaxCalculator.calculateTax() still calls the real static method
```

**Why it happens:** LLMs assume `StubProvider` can stub any method. It only intercepts instance method calls on interfaces or virtual/abstract classes. Static methods, private methods, and methods on concrete non-virtual classes cannot be stubbed.

**Correct pattern:**

```apex
// Extract an interface, implement it, then stub the interface
public interface ITaxCalculator {
    Decimal calculateTax(Decimal amount);
}

public class TaxCalculator implements ITaxCalculator {
    public Decimal calculateTax(Decimal amount) { return amount * 0.08; }
}

// In test:
ITaxCalculator stub = (ITaxCalculator) Test.createStub(
    ITaxCalculator.class, new TaxCalculatorStub()
);
OrderService svc = new OrderService(stub);
```

**Detection hint:** `Test\.createStub` called with a concrete class that is not declared `virtual` or `abstract`.

---

## Anti-Pattern 4: Not testing error and failure scenarios in callout mocks

**What the LLM generates:**

```apex
@IsTest
static void testCallout() {
    Test.setMock(HttpCalloutMock.class, new SuccessMock());
    Test.startTest();
    String result = MyService.fetchData();
    Test.stopTest();
    System.assertEquals('success', result);
}
// No test for 500 errors, timeouts, or malformed JSON
```

**Why it happens:** LLMs generate the happy-path test and stop. Production callouts fail with 401s, 500s, timeouts, and malformed bodies. Without mocks for these scenarios, error-handling code is never exercised.

**Correct pattern:**

```apex
@IsTest
static void testCallout_ServerError() {
    Test.setMock(HttpCalloutMock.class, new ErrorMock(500, '{"error":"internal"}'));
    Test.startTest();
    try {
        MyService.fetchData();
        System.assert(false, 'Should have thrown on 500');
    } catch (MyService.IntegrationException e) {
        System.assert(e.getMessage().contains('500'));
    }
    Test.stopTest();
}
```

**Detection hint:** Test class with `HttpCalloutMock` where every mock always returns status code `200`.

---

## Anti-Pattern 5: Creating a StaticResourceCalloutMock without setting Content-Type

**What the LLM generates:**

```apex
StaticResourceCalloutMock mock = new StaticResourceCalloutMock();
mock.setStaticResource('MyJsonResponse');
mock.setStatusCode(200);
// Missing: mock.setHeader('Content-Type', 'application/json');
Test.setMock(HttpCalloutMock.class, mock);
```

**Why it happens:** LLMs forget to set the Content-Type header. If production code checks `response.getHeader('Content-Type')` to decide how to parse the body, the test returns null for that header and the parsing branch goes down the wrong path.

**Correct pattern:**

```apex
StaticResourceCalloutMock mock = new StaticResourceCalloutMock();
mock.setStaticResource('MyJsonResponse');
mock.setStatusCode(200);
mock.setHeader('Content-Type', 'application/json');
Test.setMock(HttpCalloutMock.class, mock);
```

**Detection hint:** `StaticResourceCalloutMock` used without any `setHeader` call.

---

## Anti-Pattern 6: Building a StubProvider that returns null for every unhandled method

**What the LLM generates:**

```apex
public Object handleMethodCall(Object stubbedObject, String stubbedMethodName,
    Type returnType, List<Type> listOfParamTypes,
    List<String> listOfParamNames, List<Object> listOfArgs) {
    if (stubbedMethodName == 'getAccounts') {
        return new List<Account>();
    }
    return null; // Silent null for anything unexpected
}
```

**Why it happens:** LLMs generate a catch-all `return null`. If the code under test calls an unanticipated method on the stub, the silent null causes a `NullPointerException` far from the actual problem.

**Correct pattern:**

```apex
public Object handleMethodCall(Object stubbedObject, String stubbedMethodName,
    Type returnType, List<Type> listOfParamTypes,
    List<String> listOfParamNames, List<Object> listOfArgs) {
    if (stubbedMethodName == 'getAccounts') {
        return new List<Account>();
    }
    throw new StubException('Unexpected method call: ' + stubbedMethodName);
}
```

**Detection hint:** `StubProvider` implementation that ends with `return null` without a preceding exception for unexpected method names.
