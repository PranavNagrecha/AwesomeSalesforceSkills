# Examples — Apex REST Services

## Example 1: Versioned `@RestResource` With Explicit Status Codes

**Context:** An integration client needs a custom endpoint to retrieve Account summary data by external key.

**Problem:** A quick REST class returns raw records or thrown exceptions directly, leaving the contract unstable.

**Solution:**

```apex
@RestResource(urlMapping='/accounts/v1/*')
global with sharing class AccountApiResource {

    @HttpGet
    global static void getAccount() {
        RestRequest req = RestContext.request;
        RestResponse res = RestContext.response;

        String externalKey = req.requestURI.substringAfterLast('/');
        if (String.isBlank(externalKey)) {
            res.statusCode = 400;
            res.responseBody = Blob.valueOf('{"code":"BAD_REQUEST","message":"External key is required."}');
            return;
        }

        Account acct = AccountApiService.findByExternalKey(externalKey);
        if (acct == null) {
            res.statusCode = 404;
            res.responseBody = Blob.valueOf('{"code":"NOT_FOUND","message":"Account not found."}');
            return;
        }

        res.statusCode = 200;
        res.responseBody = Blob.valueOf(JSON.serialize(acct));
    }
}
```

**Why it works:** The URL is versioned, status codes are explicit, and the resource delegates retrieval logic elsewhere.

---

## Example 2: `@HttpPost` Upsert With Typed Deserialization

**Context:** An external system posts a customer record into Salesforce.

**Problem:** The endpoint uses untyped parsing everywhere and does not return a clear response.

**Solution:**

```apex
public class CustomerUpsertRequest {
    public String externalKey;
    public String name;
}

@RestResource(urlMapping='/customers/v1/upsert')
global with sharing class CustomerApiResource {

    @HttpPost
    global static void upsertCustomer() {
        RestResponse res = RestContext.response;
        CustomerUpsertRequest payload = (CustomerUpsertRequest) JSON.deserialize(
            RestContext.request.requestBody.toString(),
            CustomerUpsertRequest.class
        );

        Id accountId = CustomerApiService.upsertCustomer(payload);
        res.statusCode = 202;
        res.responseBody = Blob.valueOf(JSON.serialize(new Map<String, Object>{
            'id' => accountId,
            'status' => 'accepted'
        }));
    }
}
```

**Why it works:** The request contract is explicit, the response is shaped deliberately, and the endpoint stays focused on transport concerns.

---

## Anti-Pattern: Resource Class As Business Layer

**What practitioners do:** The `@RestResource` class queries, validates, transforms, updates, and handles every error path directly.

**What goes wrong:** Security review becomes difficult, versioning gets risky, and tests cannot isolate the transport layer from business logic.

**Correct approach:** Keep the resource thin and move business behavior into a service layer.
