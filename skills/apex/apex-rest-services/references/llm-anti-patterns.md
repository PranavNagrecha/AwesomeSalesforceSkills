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
    // No sharing keyword — defaults to without sharing for global REST classes
    @HttpGet
    global static Account getAccount() {
        Id accountId = RestContext.request.requestURI.substringAfterLast('/');
        return [SELECT Id, Name FROM Account WHERE Id = :accountId];
    }
}
```

**Why it happens:** LLMs omit the sharing keyword, and `@RestResource` classes are typically `global`, which runs without sharing enforcement by default. This means any authenticated API caller can access any record regardless of their sharing rules.

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

**Detection hint:** `@RestResource` class declaration without `with sharing` keyword.

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

**Why it happens:** LLMs use method-parameter auto-deserialization for `@HttpPost` because it looks cleaner. But this only works for flat JSON with exact key name matching. Nested objects, arrays, missing keys, and extra keys cause silent failures or exceptions.

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
