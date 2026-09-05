# Code Examples — Apex REST Services

A complete, deployable inbound endpoint: a versioned `@RestResource` at `/services/apexrest/v1/cases/*`, a service class that carries the business work, DTOs, a stable error envelope, and the test class that drives it through `RestContext`. Every platform claim in the comments carries an Apex Developer Guide v67.0 (`apexdev.txt`, Summer '26, L1–2) or Apex Reference Guide v67.0 (`apexrefguide.txt`) line reference.

Canonical building blocks reused rather than re-invented:

| Path | Used for |
|---|---|
| `templates/apex/SecurityUtils.cls` | `requireReadable` / `requireCreatable` / `stripInaccessibleForInsert` — throws `SecurityUtils.SecurityException`, which this resource maps to HTTP 403 |
| `templates/apex/ApplicationLogger.cls` | `warn` / `error(source, Exception)` / `flush()` — durable log rows keyed by `Request_Id__c`, so a 500 in the client's hand can be found in the org |
| `templates/apex/BaseService.cls` | `beginTransaction` / `rollbackTransaction` / `logAndRethrow` — the savepoint and logging contract the service extends |
| `templates/apex/tests/TestDataFactory.cls` | `createCases(count, accountId, overrides)` for the seed data and the 200-record volume test |
| `templates/apex/tests/TestUserFactory.cls` | `createUser(profileName, permissionSetNames)` for the least-privilege 403 case |

Not used here: `templates/apex/HttpClient.cls` and `templates/apex/tests/MockHttpResponseGenerator.cls` are for **outbound** callouts — see `apex/callouts-and-http-integrations`.

---

## 1. Contract

| Verb | Path | Body in | Success | Failure |
|---|---|---|---|---|
| `GET` | `/services/apexrest/v1/cases/{caseId}` | — | `200` + `CaseView` | `400` bad path, `403` no access, `404` invisible/absent, `500` unhandled |
| `POST` | `/services/apexrest/v1/cases` | `CaseCreateRequest` | `201` + `CaseView` + `Location` header | `400` malformed JSON or failed validation, `403` no create access, `500` unhandled |

Error envelope, returned on every non-2xx path this code controls:

```json
{
  "code": "VALIDATION_FAILED",
  "message": "subject is required.",
  "requestId": "4t3GkFTQ_dQ7jGKYCJ2Fu-"
}
```

`requestId` is `System.Request.getCurrent().getRequestId()` — "Same as REQUEST_ID in event monitoring" (apexrefguide L228162–228163), so a client support ticket resolves to one `Apex Execution` event-log row and one `Application_Log__c` row.

Why **not** `422 Unprocessable Entity` for validation: `422` is absent from the documented `RestResponse.statusCode` table (apexrefguide L228772–228820), and "If you set the `RestResponse.statusCode` property to a value that's not listed in the table, then an HTTP status of 500 is returned with the error message 'Invalid status code for HTTP response: nnn'" (apexrefguide L228768–228770). A validation failure returned as `422` therefore reaches the client as a `500`.

---

## 2. Resource class — `CaseApiV1.cls`

```apex
/**
 * CaseApiV1 — inbound REST adapter for Case, version 1.
 *
 * Transport only: parse, validate shape, delegate, shape the response.
 * No SOQL and no DML live in this file.
 *
 * Grounding:
 *  - "To use this annotation, your Apex class must be defined as global."  (apexdev L6352)
 *  - "To use this annotation, your Apex method must be defined as global static." (apexdev L6388)
 *  - "The URL mapping is relative to https://instance.salesforce.com/services/apexrest/."
 *    and "The path must begin with a forward slash (/)."  (apexdev L6348, L6356)
 *  - "A single Apex class annotated with @RestResource can't have multiple methods
 *     annotated with the same HTTP request method."  (apexdev L18446-18448)
 *  - Both methods take NO parameters, so "Apex REST copies the HTTP request body into
 *    the RestRequest.requestBody property" (apexdev L18459-18461). Declaring parameters
 *    would leave requestBody empty.
 *  - Both methods return void, so "If the method returns void, then Apex REST returns
 *    the response in the responseBody property" (apexrefguide L228730-228731) — which is
 *    what lets this class own its status codes instead of letting the platform serialize
 *    a return value.
 */
@RestResource(urlMapping='/v1/cases/*')
global with sharing class CaseApiV1 {

    private static final String SOURCE = 'CaseApiV1';

    // ---------------------------------------------------------------- GET

    @HttpGet
    global static void doGet() {
        RestRequest req = RestContext.request;
        RestResponse res = RestContext.response;
        try {
            Id caseId = pathId(req.requestURI);
            if (caseId == null) {
                fail(res, 400, 'INVALID_PATH', 'Expected /v1/cases/{caseId} with a valid 15- or 18-character Case Id.');
                return;
            }
            CaseView view = new CaseApiService().findById(caseId);
            if (view == null) {
                // Absent and invisible are deliberately the same answer: a 404 that
                // differed from a 403 would let a caller enumerate record existence
                // past their sharing rules.
                fail(res, 404, 'NOT_FOUND', 'No Case with that Id is visible to this user.');
                return;
            }
            ok(res, 200, view);
        } catch (SecurityUtils.SecurityException e) {
            ApplicationLogger.warn(SOURCE + '.doGet', e.getMessage());
            fail(res, 403, 'FORBIDDEN', 'The calling user lacks read access to Case.');
        } catch (Exception e) {
            ApplicationLogger.error(SOURCE + '.doGet', e);
            fail(res, 500, 'INTERNAL_ERROR', 'Unhandled failure. Quote requestId when reporting this.');
        } finally {
            ApplicationLogger.flush();
        }
    }

    // --------------------------------------------------------------- POST

    @HttpPost
    global static void doPost() {
        RestRequest req = RestContext.request;
        RestResponse res = RestContext.response;
        try {
            if (req.requestBody == null || req.requestBody.size() == 0) {
                fail(res, 400, 'EMPTY_BODY', 'A JSON body matching CaseCreateRequest is required.');
                return;
            }

            CaseCreateRequest payload;
            try {
                // deserializeStrict "throws an exception in all API versions" when the JSON
                // carries attributes the Apex type does not declare (apexrefguide L218287-218290).
                // That is the point: an unknown key is a client that thinks it is talking to v2.
                payload = (CaseCreateRequest) JSON.deserializeStrict(
                    req.requestBody.toString(), CaseCreateRequest.class
                );
            } catch (Exception parseError) {
                ApplicationLogger.warn(SOURCE + '.doPost', 'Rejected body: ' + parseError.getMessage());
                fail(res, 400, 'MALFORMED_JSON', 'Body is not a valid CaseCreateRequest: ' + parseError.getMessage());
                return;
            }

            List<String> problems = payload.problems();
            if (!problems.isEmpty()) {
                fail(res, 400, 'VALIDATION_FAILED', String.join(problems, ' '));
                return;
            }

            CaseView created = new CaseApiService().create(payload);
            res.addHeader('Location', '/services/apexrest/v1/cases/' + created.id);
            ok(res, 201, created);

        } catch (CaseApiService.ApiValidationException e) {
            fail(res, 400, 'REJECTED_BY_ORG', e.getMessage());
        } catch (SecurityUtils.SecurityException e) {
            ApplicationLogger.warn(SOURCE + '.doPost', e.getMessage());
            fail(res, 403, 'FORBIDDEN', 'The calling user lacks create access to Case.');
        } catch (Exception e) {
            ApplicationLogger.error(SOURCE + '.doPost', e);
            fail(res, 500, 'INTERNAL_ERROR', 'Unhandled failure. Quote requestId when reporting this.');
        } finally {
            ApplicationLogger.flush();
        }
    }

    // ------------------------------------------------------------ helpers

    /**
     * requestURI is "everything after the host in the HTTP request string"; the guide's own
     * example shows https://instance.salesforce.com/services/apexrest/Account/ yielding
     * /Account/ (apexrefguide L228552-228555) — the /services/apexrest prefix is not part of it.
     * So the segments here are ['', 'v1', 'cases', '<id>'].
     *
     * Validating the segment COUNT and the literal segments is what makes this safe:
     * substringAfterLast('/') alone accepts /v1/cases/anything/500... and silently reads
     * the wrong segment when the mapping changes.
     */
    private static Id pathId(String requestUri) {
        String path = (requestUri == null ? '' : requestUri).substringBefore('?');
        List<String> parts = path.split('/');
        if (parts.size() != 4 || parts[1] != 'v1' || parts[2] != 'cases' || String.isBlank(parts[3])) {
            return null;
        }
        try {
            Id candidate = Id.valueOf(parts[3]);
            return candidate.getSObjectType() == Case.SObjectType ? candidate : null;
        } catch (Exception badId) {
            return null;
        }
    }

    private static void ok(RestResponse res, Integer status, Object body) {
        res.statusCode = status;
        res.addHeader('Content-Type', 'application/json');
        // suppressApexObjectNulls = true: "If true, remove null values before serializing"
        // (apexrefguide L218454). Keeps the contract stable when a field is simply unset.
        res.responseBody = Blob.valueOf(JSON.serialize(body, true));
    }

    private static void fail(RestResponse res, Integer status, String code, String message) {
        res.statusCode = status;
        res.addHeader('Content-Type', 'application/json');
        res.responseBody = Blob.valueOf(JSON.serialize(new ErrorEnvelope(code, message)));
    }

    // --------------------------------------------------------------- DTOs
    // These are NOT method parameters, so they do not have to be global — the
    // "public, private, or global class member variables" rule (apexdev L18488-18490)
    // governs types used as @HttpPost parameters, which this class deliberately avoids.

    public class CaseCreateRequest {
        public String subject;
        public String description;
        public String origin;
        public String priority;
        public String accountId;

        public List<String> problems() {
            List<String> out = new List<String>();
            if (String.isBlank(subject))              { out.add('subject is required.'); }
            if (subject != null && subject.length() > 255) { out.add('subject exceeds 255 characters.'); }
            if (String.isNotBlank(accountId)) {
                try {
                    if (Id.valueOf(accountId).getSObjectType() != Account.SObjectType) {
                        out.add('accountId is not an Account Id.');
                    }
                } catch (Exception e) {
                    out.add('accountId is not a valid Id.');
                }
            }
            return out;
        }
    }

    public class CaseView {
        public String id;
        public String caseNumber;
        public String subject;
        public String status;
        public String priority;
        public String origin;
        public Datetime createdDate;
    }

    public class ErrorEnvelope {
        public String code;
        public String message;
        public String requestId;
        public ErrorEnvelope(String code, String message) {
            this.code = code;
            this.message = message;
            this.requestId = System.Request.getCurrent().getRequestId();
        }
    }
}
```

---

## 3. Service class — `CaseApiService.cls`

```apex
/**
 * CaseApiService — the business half of /v1/cases. Owns SOQL, DML, and the
 * savepoint; owns nothing about HTTP.
 *
 * Extends templates/apex/BaseService.cls for beginTransaction / rollbackTransaction /
 * logAndRethrow, so the failure-logging contract is the same as every other service.
 *
 * `with sharing` is declared even though "In API version 67.0 and later, classes
 * without an explicit sharing declaration run in with sharing mode" (apexdev L18738-18739),
 * because the posture of an undeclared class is decided by the apiVersion in its
 * .cls-meta.xml — invisible to anyone reading this file.
 */
public with sharing class CaseApiService extends BaseService {

    public class ApiValidationException extends Exception {}

    public CaseApiV1.CaseView findById(Id caseId) {
        SecurityUtils.requireReadable(Case.SObjectType);
        // WITH USER_MODE, not WITH SECURITY_ENFORCED: "With API version 67.0 and later,
        // you cannot use the WITH SECURITY_ENFORCED clause in SOQL SELECT queries in Apex
        // code. Instead, to run a SOQL or SOSL query in user mode, use the WITH USER_MODE
        // clause." (apexdev L44500-44502)
        List<Case> found = [
            SELECT Id, CaseNumber, Subject, Status, Priority, Origin, CreatedDate
            FROM Case
            WHERE Id = :caseId
            WITH USER_MODE
            LIMIT 1
        ];
        return found.isEmpty() ? null : toView(found[0]);
    }

    public CaseApiV1.CaseView create(CaseApiV1.CaseCreateRequest payload) {
        SecurityUtils.requireCreatable(Case.SObjectType);

        Case draft = new Case(
            Subject     = payload.subject,
            Description = payload.description,
            Origin      = String.isBlank(payload.origin) ? 'Web' : payload.origin,
            Priority    = String.isBlank(payload.priority) ? 'Medium' : payload.priority,
            AccountId   = String.isBlank(payload.accountId) ? null : (Id) payload.accountId
        );

        List<SObject> safe = SecurityUtils.stripInaccessibleForInsert(new List<Case>{ draft });

        Savepoint sp = beginTransaction();
        try {
            insert as user safe;
            commitTransaction();
        } catch (DmlException e) {
            rollbackTransaction(sp);
            // A validation rule, required field, or trigger addError is the CALLER's problem
            // (400), not the server's (500). getDmlMessage(0) is the message the org produced.
            throw new ApiValidationException(e.getDmlMessage(0), e);
        } catch (Exception e) {
            rollbackTransaction(sp);
            logAndRethrow('CaseApiService.create', e);
        }

        // Re-read so the response carries CaseNumber and the org's own defaulting,
        // which the insert does not populate on the in-memory record.
        return findById(safe[0].Id);
    }

    private CaseApiV1.CaseView toView(Case record) {
        CaseApiV1.CaseView view = new CaseApiV1.CaseView();
        view.id          = record.Id;
        view.caseNumber  = record.CaseNumber;
        view.subject     = record.Subject;
        view.status      = record.Status;
        view.priority    = record.Priority;
        view.origin      = record.Origin;
        view.createdDate = record.CreatedDate;
        return view;
    }
}
```

**Why a DTO instead of returning the `Case` sObject.** Serializing an sObject emits the platform's own envelope — the guide's `doGet` cURL walkthrough shows the body coming back as `{"attributes":{"type":"Account","url":"/services/data/v22.0/sobjects/Account/accountId"}, "Id":..., "Name":"Acme"}` (apexdev L18818–18828). Clients then bind to `attributes.url`, which pins them to whatever `/services/data/vNN.0/` string the platform emits. A DTO also caps the response size, which matters because "if the heap limit is exceeded in the process of serialization, an HTTP 200 code is returned and the error `{"status":"some error occurred"}` is appended to the partial JSON response" (apexdev L18474–18475).

---

## 4. Class metadata — `*.cls-meta.xml`

One per class, alongside the `.cls`. `apiVersion` matches the guide this package is grounded in (Apex Developer Guide **Version 67.0, Summer '26**, `apexdev.txt` L1–2) and `templates/apex/SecurityUtils.cls-meta.xml`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

`apiVersion` and `status` are the `ApexClass` metadata fields; "The file suffix is `.cls` for the class file. The accompanying metadata file is named `ClassName.cls-meta.xml`" (api_meta L22231–22232). Pinning **67.0** is not cosmetic here: it is what makes the undeclared-sharing default `with sharing` and database operations user-mode (apexdev L18735–18739). A resource copied into a project whose `.cls-meta.xml` still says `58.0` runs the same source without sharing.

---

## 5. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>CaseApiV1</members>
        <members>CaseApiService</members>
        <members>CaseApiV1Test</members>
        <members>SecurityUtils</members>
        <members>ApplicationLogger</members>
        <members>BaseService</members>
        <members>TestDataFactory</members>
        <members>TestUserFactory</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Integration_Case_API</members>
        <name>PermissionSet</name>
    </types>
    <version>67.0</version>
</Package>
```

The `PermissionSet` member is not optional decoration. Class security "applies to methods that are in Apex transaction entry points, such as: … Apex REST services" (apexdev L12325–12329), and a caller without it gets `403 — You don't have access to the specified Apex class` (apexdev L18686) before a line of `CaseApiV1` runs. Grant `CaseApiV1` (and nothing else — `CaseApiService` is reached *through* the entry point, which class security permits: "user X can execute the code in class B, but only through class A", apexdev L12323–12324).

---

## 6. Test class — `CaseApiV1Test.cls`

```apex
/**
 * CaseApiV1Test — drives the resource through RestContext, the way the platform does.
 *
 * RestRequest and RestResponse both have public no-arg constructors
 * (apexrefguide L228426-228432, L228676-228682) and RestContext.request / .response
 * are public read-write properties (apexrefguide L228336-228356), which is the entire
 * mechanism for testing an Apex REST class without an HTTP client.
 *
 * addHeader / addParameter on RestRequest exist for exactly this: "This method is
 * intended for unit testing of Apex REST classes." (apexrefguide L228617)
 */
@IsTest
private class CaseApiV1Test {

    private static final String BASE = '/v1/cases';

    private static RestResponse callGet(String uri) {
        RestRequest req = new RestRequest();
        req.requestURI = uri;
        req.httpMethod = 'GET';
        req.addHeader('Accept', 'application/json');
        RestContext.request  = req;
        RestContext.response = new RestResponse();
        CaseApiV1.doGet();
        return RestContext.response;
    }

    private static RestResponse callPost(String body) {
        RestRequest req = new RestRequest();
        req.requestURI = BASE;
        req.httpMethod = 'POST';
        req.addHeader('Content-Type', 'application/json');
        req.requestBody = body == null ? null : Blob.valueOf(body);
        RestContext.request  = req;
        RestContext.response = new RestResponse();
        CaseApiV1.doPost();
        return RestContext.response;
    }

    private static Map<String, Object> bodyOf(RestResponse res) {
        Assert.isNotNull(res.responseBody, 'Every path must write a response body');
        return (Map<String, Object>) JSON.deserializeUntyped(res.responseBody.toString());
    }

    @TestSetup
    static void seed() {
        List<Account> accounts = TestDataFactory.createAccounts(1, null);
        insert accounts;
        insert TestDataFactory.createCases(1, accounts[0].Id, new Map<String, Object>{
            'Subject' => 'Seeded case', 'Priority' => 'High'
        });
    }

    @IsTest
    static void getReturns200AndTheView() {
        Case seeded = [SELECT Id, CaseNumber FROM Case LIMIT 1];

        Test.startTest();
        RestResponse res = callGet(BASE + '/' + seeded.Id);
        Test.stopTest();

        Assert.areEqual(200, res.statusCode, 'Happy path must be 200');
        Map<String, Object> body = bodyOf(res);
        Assert.areEqual(String.valueOf(seeded.Id), (String) body.get('id'), 'id must round-trip');
        Assert.areEqual(seeded.CaseNumber, (String) body.get('caseNumber'), 'CaseNumber must be present');
        Assert.isFalse(body.containsKey('attributes'), 'A DTO must not leak the sObject attributes envelope');
    }

    @IsTest
    static void getWithATrailingGarbageSegmentReturns400() {
        // substringAfterLast('/') would happily read 'extra' here and 404. The
        // segment-count check is what turns this into an honest 400.
        RestResponse res = callGet(BASE + '/' + [SELECT Id FROM Case LIMIT 1].Id + '/extra');
        Assert.areEqual(400, res.statusCode, 'A path that does not match the contract is a 400');
        Assert.areEqual('INVALID_PATH', (String) bodyOf(res).get('code'));
    }

    @IsTest
    static void getWithANonIdSegmentReturns400() {
        RestResponse res = callGet(BASE + '/not-an-id');
        Assert.areEqual(400, res.statusCode, 'A malformed Id is a client error, not a 404');
        Assert.areEqual('INVALID_PATH', (String) bodyOf(res).get('code'));
    }

    @IsTest
    static void getWithAWrongObjectIdReturns400() {
        Account a = [SELECT Id FROM Account LIMIT 1];
        RestResponse res = callGet(BASE + '/' + a.Id);
        Assert.areEqual(400, res.statusCode, 'An Account Id on a Case route is a 400, not a 404');
    }

    @IsTest
    static void getAnAbsentCaseReturns404WithAnEnvelope() {
        Case ghost = new Case(Subject = 'Deleted before the call');
        insert ghost;
        Id ghostId = ghost.Id;
        delete ghost;

        RestResponse res = callGet(BASE + '/' + ghostId);
        Assert.areEqual(404, res.statusCode);
        Map<String, Object> body = bodyOf(res);
        Assert.areEqual('NOT_FOUND', (String) body.get('code'));
        Assert.isNotNull(body.get('requestId'), 'Every error carries the request id for support');
    }

    @IsTest
    static void postCreatesAndReturns201WithLocation() {
        Account a = [SELECT Id FROM Account LIMIT 1];
        String payload = JSON.serialize(new Map<String, Object>{
            'subject'   => 'Printer is on fire',
            'origin'    => 'Web',
            'priority'  => 'High',
            'accountId' => a.Id
        });

        Test.startTest();
        RestResponse res = callPost(payload);
        Test.stopTest();

        Assert.areEqual(201, res.statusCode, 'A create is 201, not 200');
        Map<String, Object> body = bodyOf(res);
        Assert.areEqual('Printer is on fire', (String) body.get('subject'));
        Assert.isNotNull(body.get('caseNumber'), 'The response must carry org-assigned values');
        Assert.areEqual(
            '/services/apexrest/v1/cases/' + (String) body.get('id'),
            res.headers.get('Location'),
            'Location must address the created resource through the public path'
        );
        Assert.areEqual(1, [SELECT COUNT() FROM Case WHERE Subject = 'Printer is on fire']);
    }

    @IsTest
    static void postWithAnUnknownFieldReturns400() {
        // deserializeStrict rejects attributes the type does not declare
        // (apexrefguide L218287-218290) — a v2 client hitting v1 gets told so.
        RestResponse res = callPost('{"subject":"ok","escalate":true}');
        Assert.areEqual(400, res.statusCode);
        Assert.areEqual('MALFORMED_JSON', (String) bodyOf(res).get('code'));
    }

    @IsTest
    static void postWithBrokenJsonReturns400NotAn500() {
        RestResponse res = callPost('{"subject":');
        Assert.areEqual(400, res.statusCode, 'A parse failure is the caller\'s fault');
        Assert.areEqual('MALFORMED_JSON', (String) bodyOf(res).get('code'));
    }

    @IsTest
    static void postWithAnEmptyBodyReturns400() {
        RestResponse res = callPost(null);
        Assert.areEqual(400, res.statusCode);
        Assert.areEqual('EMPTY_BODY', (String) bodyOf(res).get('code'));
    }

    @IsTest
    static void postWithoutASubjectReturns400Validation() {
        RestResponse res = callPost('{"description":"no subject"}');
        Assert.areEqual(400, res.statusCode);
        Map<String, Object> body = bodyOf(res);
        Assert.areEqual('VALIDATION_FAILED', (String) body.get('code'));
        Assert.isTrue(((String) body.get('message')).contains('subject'), 'The message must name the field');
    }

    @IsTest
    static void everyStatusCodeUsedIsOneThePlatformAccepts() {
        // Guard against the 422 trap: a code outside the documented table is turned
        // into a 500 with "Invalid status code for HTTP response" (apexrefguide L228768-228770).
        Set<Integer> allowed = new Set<Integer>{
            200, 201, 202, 204, 206, 300, 301, 302, 304,
            400, 401, 403, 404, 405, 406, 409, 410, 412, 413, 414, 415, 417,
            500, 503
        };
        for (String uri : new List<String>{ BASE + '/not-an-id', BASE + '/x/y/z' }) {
            Assert.isTrue(allowed.contains(callGet(uri).statusCode), 'Status must be in the documented table');
        }
        Assert.isTrue(allowed.contains(callPost('{"subject":').statusCode), 'POST error status must be in the table');
    }

    @IsTest
    static void getIsOneQueryRegardlessOfCaseVolume() {
        Account a = [SELECT Id FROM Account LIMIT 1];
        insert TestDataFactory.createCases(200, a.Id, null);
        Case target = [SELECT Id FROM Case LIMIT 1];

        Test.startTest();
        Integer before = Limits.getQueries();
        RestResponse res = callGet(BASE + '/' + target.Id);
        Integer used = Limits.getQueries() - before;
        Test.stopTest();

        Assert.areEqual(200, res.statusCode);
        Assert.areEqual(1, used, 'A single-record GET must stay at one query no matter the table size');
    }

    @IsTest
    static void aUserWithoutCaseAccessGets403NotAStackTrace() {
        // UNVERIFIED (2026-09-05): the profile name 'Minimum Access - Salesforce' is not
        // stated in apexdev.txt / apexrefguide.txt / api_meta.txt. If the org does not
        // have it, substitute any profile with no Case object permission.
        User leastPrivilege = TestUserFactory.createUser('Minimum Access - Salesforce', new List<String>());
        Case seeded = [SELECT Id FROM Case LIMIT 1];

        System.runAs(leastPrivilege) {
            RestResponse res = callGet(BASE + '/' + seeded.Id);
            Assert.areEqual(403, res.statusCode, 'No Case read access is a 403');
            Map<String, Object> body = bodyOf(res);
            Assert.areEqual('FORBIDDEN', (String) body.get('code'));
            Assert.isFalse(
                ((String) body.get('message')).contains('SELECT'),
                'The envelope must not leak the query or the stack trace'
            );
        }
    }
}
```

---

## 7. Deploy and verify

```bash
# 1. Static check before deploying — flags the REST-specific defects the compiler cannot see
python3 skills/apex/apex-rest-services/scripts/check_apex_rest_services.py \
    --manifest-dir force-app

# 2. Deploy the manifest
sf project deploy start -x manifest/package.xml -o myOrg -w 30

# 3. Run only this suite, with coverage, and fail the shell on a failed assertion
sf apex run test -o myOrg \
    -n CaseApiV1Test \
    -r human -w 20 -c -y

# 4. Retrieve back to confirm what actually landed (including the apiVersion pin)
sf project retrieve start -x manifest/package.xml -o myOrg
```

**Live verification with cURL.** The guide's own walkthrough authenticates with `-H "Authorization: Bearer sessionId"` against `https://instance.salesforce.com/services/apexrest/...` (apexdev L18811–18813, L18836–18838); Apex REST "supports these authentication mechanisms: OAuth 2.0, Session ID" (apexdev L18402–18404). Replace `MyDomainName` with the org's My Domain and `ACCESS_TOKEN` with a token from an OAuth flow — see `integration/oauth-flows-and-connected-apps`.

```bash
TOKEN='ACCESS_TOKEN'          # placeholder — never commit a real token
HOST='https://MyDomainName.my.salesforce.com'

# GET one case — expect 200 and the CaseView DTO
curl -i -H "Authorization: Bearer $TOKEN" \
     "$HOST/services/apexrest/v1/cases/5003000000D8cuIAAR"

# POST a new case — expect 201, a Location header, and the created view
curl -i -X POST \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"subject":"Printer is on fire","origin":"Web","priority":"High"}' \
     "$HOST/services/apexrest/v1/cases"

# Contract probes that must NOT return 200
curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" \
     "$HOST/services/apexrest/v1/cases/not-an-id"                 # expect 400
curl -s -o /dev/null -w '%{http_code}\n' -X DELETE -H "Authorization: Bearer $TOKEN" \
     "$HOST/services/apexrest/v1/cases/5003000000D8cuIAAR"        # expect 405 — no @HttpDelete
curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" \
     "$HOST/services/apexrest/v2/cases/5003000000D8cuIAAR"        # expect 404 — unmapped URL
```

The last two are the documented platform responses, not this class's: `405 — The request method doesn't have a corresponding Apex method` and `404 — The URL is unmapped in an existing @RestResource annotation` (apexdev L18684–18693). Confirming them is how you prove the mapping is what you think it is.

**Setup check.** Setup → Apex Classes shows `CaseApiV1` with its API version — that number, not the org's release, decides the sharing and user-mode defaults (apexdev L18735–18739). Setup → Permission Sets → *Integration Case API* → Apex Class Access must list `CaseApiV1`; remove it and every call returns `403` (apexdev L18686).

**Log check.** After a 500 in production, the client's `requestId` finds the row:

```soql
SELECT Id, Source__c, Severity__c, Message__c, Exception_Type__c,
       Request_Id__c, Running_User__c, CreatedDate
FROM Application_Log__c
WHERE Request_Id__c = '4t3GkFTQ_dQ7jGKYCJ2Fu-'
ORDER BY CreatedDate DESC
```

That join works because the envelope's `requestId` and the log row's `Request_Id__c` are both `System.Request.getCurrent().getRequestId()`, which is "the same as in the event log files of the Apex Execution event type used in Event Monitoring" (apexrefguide L228153).
