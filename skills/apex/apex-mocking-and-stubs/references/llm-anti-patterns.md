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

## Anti-Pattern 3: Guessing at what the Stub API can mock instead of using the documented list

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

**Why it happens:** LLMs assume `StubProvider` can stub any method, then over-correct into the opposite myth — that the target must be `virtual` or an interface. Both are wrong, and the second one is wrong in a way that produces useless `virtual` keywords all over the codebase.

The Apex Developer Guide states the boundary exactly (L42209–42219). You **cannot** mock:

| Cannot be mocked | Why it bites |
|---|---|
| Static methods (including `@future` methods) | The most common "dependency" shape in legacy Apex |
| Private methods | `@TestVisible` widens access; it does not make the method stubbable |
| Properties (getters and setters) | A `public Integer count { get; set; }` is not a method to the Stub API |
| Triggers | Trigger logic must live in a handler class to be testable at all |
| Inner classes | A helper nested inside its consumer can never be a seam |
| System types | You cannot stub `Http`, `Database`, `Messaging` — use `Test.setMock` |
| Classes implementing `Batchable` | Extract the work into an injectable service the batch calls |
| Classes with only private constructors | The singleton-with-private-constructor idiom blocks stubbing |

Plus: iterators can't be used as return types or parameter types.

What you **can** mock includes ordinary non-`virtual` public instance methods on ordinary non-`virtual` top-level classes — stubs are generated as anonymous subclasses at runtime, and the guide's own worked example stubs `getTodaysDate()` on a plain `public class DateHelper` (L42060–42073, L42180–42192). Prefer interfaces because they document the contract, not because the API requires them.

The failure is also a **runtime** failure, not a compile error: `Test.createStub()` on a rejected type saves fine and blows up when the test runs.

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

**Detection hint:** `Test\.createStub\(` whose first argument names a type on the cannot-mock list — an inner class (`Outer.Inner.class`), a class declaring `implements Database.Batchable`, or a class whose only constructor is `private`. Do **not** flag a plain non-`virtual` class; that is a false positive.

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

---

## Anti-Pattern 7: Setting the mock before `Test.startTest()` in a test that inserts its own data

**What the LLM generates:**

```apex
@IsTest
static void testCallout() {
    Account a = new Account(Name = 'Acme');
    insert a;                                      // pending uncommitted work
    Test.setMock(HttpCalloutMock.class, new SuccessMock());
    Test.startTest();
    SyncService.push(a.Id);                        // "You have uncommitted work pending"
    Test.stopTest();
}
```

**Why it happens:** LLMs group the two `Test.` calls together because they look like setup, and the pattern works by accident in tests that use `@TestSetup` (where the DML happened in a prior transaction). It fails the moment the test does its own DML inline.

**Correct pattern:**

```apex
@IsTest
static void testCallout() {
    Account a = new Account(Name = 'Acme');
    insert a;                                      // DML OUTSIDE the block
    Test.startTest();                              // startTest FIRST
    Test.setMock(HttpCalloutMock.class, new SuccessMock());   // then setMock
    SyncService.push(a.Id);
    Test.stopTest();
}
```

The Apex Developer Guide states the ordering rule directly: enclose the callout in `Test.startTest`/`Test.stopTest`, "the `Test.startTest` statement must appear before the `Test.setMock` statement", and the DML calls must not be part of the block (L35675–35681).

**Detection hint:** a `Test\.setMock\(` line that appears before the `Test\.startTest\(\)` line in a method that also contains a bare `insert`/`update`/`upsert` statement outside `@TestSetup`.
