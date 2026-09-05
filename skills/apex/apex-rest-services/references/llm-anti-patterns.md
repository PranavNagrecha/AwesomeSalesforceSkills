# LLM Anti-Patterns — Apex REST Services

Common mistakes AI coding assistants make when generating or advising on inbound Apex REST resources.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Not setting explicit HTTP status codes on error responses

**What the LLM generates:**

```apex
@HttpPost
global static String createAccount(String name) {
    try {
        insert new Account(Name = name);
        return 'Success';
    } catch (Exception e) {
        return 'Error: ' + e.getMessage(); // Returns 200 with error text
    }
}
```

**Why it happens:** LLMs return error information as a string body but leave the HTTP status code at the default 200. Clients cannot distinguish success from failure by status code, breaking standard REST conventions.

**Correct pattern:**

```apex
@HttpPost
global static void createAccount() {
    RestRequest req = RestContext.request;
    RestResponse res = RestContext.response;
    try {
        Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(req.requestBody.toString());
        insert new Account(Name = (String) body.get('name'));
        res.statusCode = 201;
        res.responseBody = Blob.valueOf(JSON.serialize(new Map<String, String>{'status' => 'created'}));
    } catch (DmlException e) {
        res.statusCode = 400;
        res.responseBody = Blob.valueOf(JSON.serialize(new Map<String, String>{'error' => e.getDmlMessage(0)}));
    } catch (Exception e) {
        res.statusCode = 500;
        res.responseBody = Blob.valueOf(JSON.serialize(new Map<String, String>{'error' => e.getMessage()}));
    }
}
```

**Detection hint:** `@HttpPost` or `@HttpPatch` methods that `return` error strings without setting `RestContext.response.statusCode`.

---

## Anti-Pattern 2: Omitting 'with sharing' on REST resource classes

**What the LLM generates:**

```apex
@RestResource(urlMapping='/api/accounts/*')
global class AccountApi {
    // No sharing keyword — runs without sharing in a class pinned to apiVersion 66.0 or below
    @HttpGet
    global static Account getAccount() {
        Id accountId = RestContext.request.requestURI.substringAfterLast('/');
        return [SELECT Id, Name FROM Account WHERE Id = :accountId];
    }
}
```

**Why it happens:** LLMs omit the sharing keyword. What that costs depends on the `apiVersion` in the class's `.cls-meta.xml`, not on the org's release — a Summer '26 org runs a class pinned to 58.0 with the older behavior. At **66.0 and below** a class with no keyword runs without sharing enforcement, so any authenticated API caller can reach any record regardless of their sharing rules, and the bare SOQL above runs in system mode past FLS as well. At **67.0+** (Summer '26) the bare class runs `with sharing` and database operations default to user mode, so the omission is no longer that hole — but declare the keyword anyway, because otherwise the endpoint's access posture is decided by a version pin the reviewer cannot see in the source. Canonical table: [`agents/_shared/AGENT_CONTRACT.md`](../../../../agents/_shared/AGENT_CONTRACT.md) § *Apex security idiom by API version*.

**Correct pattern:**

```apex
@RestResource(urlMapping='/api/accounts/*')
global with sharing class AccountApi {
    @HttpGet
    global static Account getAccount() {
        Id accountId = RestContext.request.requestURI.substringAfterLast('/');
        return [SELECT Id, Name FROM Account WHERE Id = :accountId WITH USER_MODE];
    }
}
```

**Detection hint:** `@RestResource` class declaration without `with sharing` keyword. Grade the hit against the sibling `.cls-meta.xml`: an exposed-records defect at 66.0 and below, a hardening note at 67.0+.

---

## Anti-Pattern 3: Parsing URL parameters with fragile string splitting instead of RestContext

**What the LLM generates:**

```apex
@HttpGet
global static Account getAccount() {
    String uri = RestContext.request.requestURI;
    String[] parts = uri.split('/');
    String accountId = parts[parts.size() - 1]; // Fragile index assumption
    return [SELECT Id, Name FROM Account WHERE Id = :accountId];
}
```

**Why it happens:** LLMs split the URI string and assume a fixed path structure. If the URL mapping or API version prefix changes, the index breaks silently, returning wrong data or throwing an exception.

**Correct pattern:**

```apex
@HttpGet
global static Account getAccount() {
    RestRequest req = RestContext.request;
    // Use requestURI relative to the urlMapping
    String accountId = req.requestURI.substringAfterLast('/');
    // Or better — use request parameters for named params
    // String accountId = req.params.get('id');

    if (accountId == null || !(accountId instanceOf Id)) {
        RestContext.response.statusCode = 400;
        return null;
    }
    return [SELECT Id, Name FROM Account WHERE Id = :accountId WITH USER_MODE];
}
```

**Detection hint:** `requestURI\.split\('/'` with hard-coded array indices.

---

## Anti-Pattern 4: Accepting user input directly into SOQL without sanitization

**What the LLM generates:**

```apex
@HttpGet
global static List<Account> searchAccounts() {
    String name = RestContext.request.params.get('name');
    String query = 'SELECT Id, Name FROM Account WHERE Name LIKE \'%' + name + '%\'';
    return Database.query(query); // SOQL injection vulnerability
}
```

**Why it happens:** LLMs build dynamic SOQL with string concatenation from request parameters. This is a textbook SOQL injection vulnerability — a caller can inject arbitrary SOQL clauses.

**Correct pattern:**

```apex
@HttpGet
global static List<Account> searchAccounts() {
    String name = RestContext.request.params.get('name');
    if (String.isBlank(name)) {
        RestContext.response.statusCode = 400;
        return new List<Account>();
    }
    String safeName = '%' + String.escapeSingleQuotes(name) + '%';
    return [SELECT Id, Name FROM Account WHERE Name LIKE :safeName WITH USER_MODE];
}
```

**Detection hint:** Dynamic SOQL string concatenation with `RestContext.request.params.get` values — look for `'\s*\+\s*.*params\.get`.

---

## Anti-Pattern 5: Using method parameters instead of RestContext for complex POST bodies

**What the LLM generates:**

```apex
@HttpPost
global static String createRecord(String name, String email, String phone) {
    // Method parameters auto-deserialize, but only for simple flat JSON
    // Nested objects, arrays, and optional fields break silently
}
```

**Why it happens:** LLMs use method-parameter auto-deserialization for `@HttpPost` because it looks cleaner. Nesting is not what breaks — the guide explicitly allows "user-defined types that contain member variables of the types listed above" (apexdev L18437) and demonstrates a nested one (apexdev L18491–18516). Four real behaviours break instead:

- **The raw body becomes unavailable.** "If the method has parameters, then Apex REST attempts to deserialize the data into those parameters and the data won't be deserialized into the `RestRequest.requestBody` property" (apexdev L18459–18461). Signature verification, replay, and idempotency keys all need that body.
- **Parameter names are the contract.** "The names of the Apex parameters matter, although the order doesn't" (apexdev L18570) — so renaming a parameter is a breaking API change that no compiler flags.
- **Duplicate keys are a hard 400.** `{"x":"value1","x":"value2"}` "results in an HTTP 400 status code error response" (apexdev L18607–18609), and the same applies to a repeated member of a user-defined type — a `400` your code never sees and cannot wrap in your envelope.
- **Cyclic types are a runtime 400.** Two user-defined types referencing each other compile, and then "at run time when a request is made, Apex REST detects a cycle between instances of `def1` and `def2`, and generates an HTTP 400 status code error response" (apexdev L18564–18565).

**Correct pattern:**

```apex
@HttpPost
global static void createRecord() {
    RestRequest req = RestContext.request;
    RestResponse res = RestContext.response;
    CreateRecordRequest payload;
    try {
        payload = (CreateRecordRequest) JSON.deserialize(
            req.requestBody.toString(), CreateRecordRequest.class
        );
    } catch (JSONException e) {
        res.statusCode = 400;
        res.responseBody = Blob.valueOf('{"error":"Invalid JSON payload"}');
        return;
    }
    // Process payload.name, payload.contacts, etc.
}

public class CreateRecordRequest {
    public String name;
    public String email;
    public List<ContactWrapper> contacts; // Supports nested structures
}
```

**Detection hint:** `@HttpPost` method with more than 2 primitive parameters in the method signature.

---

## Anti-Pattern 6: Not writing tests that set RestContext.request and RestContext.response

**What the LLM generates:**

```apex
@IsTest
static void testGetAccount() {
    Account a = new Account(Name = 'Test');
    insert a;
    // Calling the method directly without setting RestContext
    Account result = AccountApi.getAccount();
    // NullPointerException on RestContext.request
}
```

**Why it happens:** LLMs forget that `RestContext` is null in tests unless explicitly set. The test either throws an NPE or tests a different code path than production.

**Correct pattern:**

```apex
@IsTest
static void testGetAccount() {
    Account a = new Account(Name = 'Test');
    insert a;

    RestRequest req = new RestRequest();
    req.requestURI = '/services/apexrest/api/accounts/' + a.Id;
    req.httpMethod = 'GET';
    RestContext.request = req;
    RestContext.response = new RestResponse();

    Test.startTest();
    Account result = AccountApi.getAccount();
    Test.stopTest();

    System.assertNotEquals(null, result);
    System.assertEquals('Test', result.Name);
}
```

**Detection hint:** Test methods that call `@RestResource` methods without setting `RestContext.request` and `RestContext.response`.


---

## Anti-Pattern 7: Returning the sObject (or a list of them) straight out of the method

**What the LLM generates:**

```apex
@RestResource(urlMapping='/api/cases/*')
global with sharing class CaseApi {
    @HttpGet
    global static List<Case> listCases() {
        return [SELECT Id, Subject, Status FROM Case WHERE Status = 'New' WITH USER_MODE];
    }
}
```

**Why it happens:** a non-void return type is the shortest code that "works", so LLMs default to it. Three platform behaviours turn it into a contract defect:

1. The body carries the platform's own envelope. The guide's cURL walkthrough shows `doGet` returning `{"attributes":{"type":"Account","url":"/services/data/v22.0/sobjects/Account/accountId"},"Id":...,"Name":"Acme"}` (apexdev L18818–18828). Clients bind to `attributes.url` and are then pinned to a platform-emitted version string.
2. Null fields silently disappear. "If the return type includes fields with null values, those fields aren't serialized into the response body" (apexdev L18463–18465), so a required field in the client's schema is present on some responses and absent on others.
3. An unbounded list can blow heap *after* the status line is on the wire: "If the heap limit is exceeded in the process of serialization, an HTTP 200 code is returned and the error `{"status":"some error occurred"}` is appended to the partial JSON response" (apexdev L18474–18475). The client sees `200` and a truncated body, so retry logic keyed on status never fires.

**Correct pattern:**

```apex
@RestResource(urlMapping='/v1/cases/*')
global with sharing class CaseApiV1 {
    @HttpGet
    global static void listCases() {
        RestResponse res = RestContext.response;
        Integer pageSize = pageSizeFrom(RestContext.request);   // capped, e.g. 200
        List<CaseView> page = new CaseApiService().recentNew(pageSize);
        res.statusCode = 200;
        res.addHeader('Content-Type', 'application/json');
        res.responseBody = Blob.valueOf(JSON.serialize(
            new Map<String, Object>{ 'items' => page, 'pageSize' => pageSize }, true
        ));
    }
    public class CaseView { public String id; public String subject; public String status; }
}
```

The guide names this fix in the same paragraph as the defect: "To gain control of the `statusCode` and the `responseBody`, use a `RestResponse` instead of directly returning sObjects" (apexdev L18477–18478).

**Detection hint:** a method annotated `@Http*` whose return type is an sObject, `List<SObject>`, or `List<`*anything*`>`. Any `@Http*` method not declared `void` is worth a second look.

---

## Anti-Pattern 8: Using a status code the platform does not accept

**What the LLM generates** (excerpt — the catch blocks of a verb method):

```apex
} catch (ValidationException e) {
    RestContext.response.statusCode = 422;          // Unprocessable Entity
    RestContext.response.responseBody = Blob.valueOf(
        JSON.serialize(new Map<String, String>{ 'error' => e.getMessage() })
    );
} catch (RateLimitException e) {
    RestContext.response.statusCode = 429;          // Too Many Requests
}
```

**Why it happens:** `422` and `429` are the codes general REST practice teaches, and nothing in Apex rejects the assignment at compile time. The valid codes are a whitelist, not a range: 200, 201, 202, 204, 206, 300, 301, 302, 304, 400, 401, 403, 404, 405, 406, 409, 410, 412, 413, 414, 415, 417, 500, 503 (apexrefguide L228772–228820). Anything else is rewritten: "If you set the `RestResponse.statusCode` property to a value that's not listed in the table, then an HTTP status of 500 is returned with the error message 'Invalid status code for HTTP response: nnn'" (apexrefguide L228768–228770). The endpoint then reports a *server* error for what was a *client* error, and the carefully built envelope is replaced.

**Correct pattern** (excerpt — the same catch blocks):

```apex
} catch (ValidationException e) {
    // 400, not 422 — the fine-grained reason lives in the envelope's `code`,
    // which is ours to define, not in the status line, which is not.
    fail(RestContext.response, 400, 'VALIDATION_FAILED', e.getMessage());
} catch (RateLimitException e) {
    // 503 is on the accepted list; 429 is not.
    RestContext.response.addHeader('Retry-After', '30');
    fail(RestContext.response, 503, 'RATE_LIMITED', 'Retry after 30 seconds.');
}
```

**Detection hint:** grep for `statusCode\s*=\s*(\d+)` and check every literal against the accepted set. `skills/apex/apex-rest-services/scripts/check_apex_rest_services.py` does this over a source tree.
