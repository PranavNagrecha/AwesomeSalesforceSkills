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

**What the split looks like in practice.** The resource keeps only the signatures below; everything with a `SELECT`, an `insert`, or a savepoint moves behind them. Compare against the fat version above — the point is that the file on the left can be reviewed for its HTTP contract alone.

```apex
// Transport (global, one method per verb, no parameters, void return)
@RestResource(urlMapping='/v1/cases/*')
global with sharing class CaseApiV1 {
    @HttpGet  global static void doGet()  { /* parse URI -> delegate -> res.statusCode */ }
    @HttpPost global static void doPost() { /* parse body -> delegate -> res.statusCode */ }

    private static Id   pathId(String requestUri)                                   { /* ... */ return null; }
    private static void ok(RestResponse res, Integer status, Object body)           { /* ... */ }
    private static void fail(RestResponse res, Integer status, String c, String m)  { /* ... */ }
}

// Domain (not global; not in the Apex Class Access permission set — reached only
// through the entry point, which class security permits: apexdev L12323-12324)
public with sharing class CaseApiService extends BaseService {
    public CaseApiV1.CaseView findById(Id caseId)                       { /* SOQL WITH USER_MODE */ return null; }
    public CaseApiV1.CaseView create(CaseApiV1.CaseCreateRequest body)  { /* savepoint + insert as user */ return null; }
    public class ApiValidationException extends Exception {}
}
```

The transport file has one job the reviewer can check without reading the domain: **every exit path sets a status code.** Full bodies for both classes, with the test class and deployment metadata, are in `references/code-examples.md`.

---

## Example 3: Probing The Contract Before A Client Integrates

**Context:** The endpoint is deployed and the tests pass, but no external client has called it yet.

**Problem:** Unit tests drive `CaseApiV1.doGet()` directly through `RestContext`. They cannot prove the *mapping* is reachable, that the verb table is what you think it is, or that Apex Class Access was actually granted — all three are platform decisions made before your method runs.

**Solution:** Assert the platform's own documented responses, not only your own.

| Probe | Expected | Whose decision |
|---|---|---|
| `GET /services/apexrest/v1/cases/{validId}` | `200` | Yours |
| `GET /services/apexrest/v1/cases/not-an-id` | `400` | Yours |
| `DELETE /services/apexrest/v1/cases/{validId}` | `405` — "The request method doesn't have a corresponding Apex method" (apexdev L18695) | Platform |
| `GET /services/apexrest/v2/cases/{validId}` | `404` — "The URL is unmapped in an existing `@RestResource` annotation" (apexdev L18688) | Platform |
| `GET /services/apexrest/V1/cases/{validId}` | `404` — the mapping is case-sensitive (apexdev L6350–6351) | Platform |
| Same call as a user without Apex Class Access | `403` — "You don't have access to the specified Apex class" (apexdev L18686) | Platform |

```bash
#!/usr/bin/env bash
# contract-probe.sh — run after every deploy of CaseApiV1.
# TOKEN is a placeholder; obtain one through an OAuth flow (integration/oauth-flows-and-connected-apps).
set -u
TOKEN="${SF_ACCESS_TOKEN:?export SF_ACCESS_TOKEN before running}"
HOST="${SF_HOST:?export SF_HOST, e.g. https://MyDomainName.my.salesforce.com}"
CASE_ID="${1:?usage: contract-probe.sh <caseId>}"

probe () {  # probe <expected> <method> <path>
  actual=$(curl -s -o /dev/null -w '%{http_code}' -X "$2" \
           -H "Authorization: Bearer $TOKEN" "$HOST$3")
  [ "$actual" = "$1" ] && echo "ok   $2 $3 -> $1" \
                       || { echo "FAIL $2 $3 -> $actual (expected $1)"; exit 1; }
}

probe 200 GET    "/services/apexrest/v1/cases/$CASE_ID"
probe 400 GET    "/services/apexrest/v1/cases/not-an-id"
probe 405 DELETE "/services/apexrest/v1/cases/$CASE_ID"
probe 404 GET    "/services/apexrest/v2/cases/$CASE_ID"
probe 404 GET    "/services/apexrest/V1/cases/$CASE_ID"
echo "contract intact"
```

**Why it works:** the four platform-decided rows fail loudly if the mapping string, the verb set, or the permission set drifted — none of which a `RestContext`-driven Apex test can see. Wire the script into the post-deploy step of the release pipeline; see `devops/post-deployment-validation` for where.
