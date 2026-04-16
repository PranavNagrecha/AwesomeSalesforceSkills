# Eval: integration/callouts-and-http-integrations

- **Skill under test:** `skills/integration/callouts-and-http-integrations/SKILL.md`
- **Priority:** P0
- **Cases:** 3
- **Last verified:** 2026-04-16
- **Related templates:** `templates/apex/HttpClient.cls`, `templates/apex/tests/MockHttpResponseGenerator.cls`, `templates/apex/ApplicationLogger.cls`
- **Related decision trees:** `standards/decision-trees/integration-pattern-selection.md`, `standards/decision-trees/async-selection.md`

## Pass criteria

Every generated callout must: use a Named Credential (never a raw URL),
set an explicit timeout, handle transient errors with bounded retries,
log via `ApplicationLogger`, and be tested with `MockHttpResponseGenerator`.

## Case 1 — Build a typed Apex client for a REST API

**Priority:** P0

**User prompt:**

> "Build me a typed Apex wrapper for the vendor's `GET /v2/accounts/:id`
> and `POST /v2/accounts` endpoints. Include tests."

**Expected output MUST include:**

- Single service class (e.g. `VendorAccountApi`) with two methods —
  `getAccount(String extId)` returning a typed DTO, and
  `createAccount(AccountDto dto)` returning the remote Id.
- DTOs as inner classes annotated appropriately for `JSON.deserialize`.
- Use of `HttpClient` template with explicit timeout (20s) and retry on transient.
- Apex exceptions mapped to named types — `NotFoundException` for 404,
  `RateLimitException` for 429, etc.
- Test class uses `MockHttpResponseGenerator` with 3 cases: success,
  404, 500-retry-then-success.
- Test coverage ≥ 90% on the new class.

**Expected output MUST NOT include:**

- Raw HTTP request building with `http.setEndpoint(...)` and a hardcoded URL.
- `JSON.deserializeUntyped` as the primary deserialization (prefer typed).
- Swallowing all exceptions with a generic `catch(Exception e)` and returning null.
- Hitting the real endpoint in tests.

**Rubric (0–5):**

- **Correctness:** Both endpoints implemented correctly.
- **Completeness:** DTOs + exceptions + tests.
- **Bulk safety:** Methods can be called in a loop of up to 100 without fanout issues; ideally there's a batch variant.
- **Security:** Named Credential, no secrets in source.
- **Citation of official docs:** Links to HttpRequest / HttpResponse / JSON deserialize.

**Reference answer (gold):**

```apex
public with sharing class VendorAccountApi {

    public class AccountDto {
        public String externalId;
        public String name;
        public String status;
    }

    public class NotFoundException extends Exception {}
    public class RateLimitException extends Exception {}
    public class VendorException extends Exception {}

    public AccountDto getAccount(String externalId) {
        if (String.isBlank(externalId)) {
            throw new VendorException('externalId is required');
        }
        HttpClient.Response res = new HttpClient()
            .namedCredential('My_Vendor')
            .path('/v2/accounts/' + EncodingUtil.urlEncode(externalId, 'UTF-8'))
            .method('GET')
            .header('Accept', 'application/json')
            .timeoutMs(20000)
            .retryOnTransient(true)
            .send();
        if (res.statusCode == 404) { throw new NotFoundException('Account ' + externalId + ' not found'); }
        if (res.statusCode == 429) { throw new RateLimitException('Rate limited'); }
        if (!res.isSuccess()) {
            ApplicationLogger.error('VendorAccountApi.getAccount',
                'HTTP ' + res.statusCode + ': ' + res.body.left(1000));
            throw new VendorException('Upstream ' + res.statusCode);
        }
        return (AccountDto) JSON.deserialize(res.body, AccountDto.class);
    }

    public String createAccount(AccountDto dto) {
        if (dto == null) { throw new VendorException('dto is required'); }
        HttpClient.Response res = new HttpClient()
            .namedCredential('My_Vendor')
            .path('/v2/accounts')
            .method('POST')
            .header('Content-Type', 'application/json')
            .body(JSON.serialize(dto))
            .timeoutMs(20000)
            .retryOnTransient(true)
            .send();
        if (res.statusCode == 429) { throw new RateLimitException('Rate limited'); }
        if (!res.isSuccess()) {
            ApplicationLogger.error('VendorAccountApi.createAccount',
                'HTTP ' + res.statusCode + ': ' + res.body.left(1000));
            throw new VendorException('Upstream ' + res.statusCode);
        }
        Map<String, Object> parsed = (Map<String, Object>) JSON.deserializeUntyped(res.body);
        return (String) parsed.get('id');
    }
}
```

```apex
@IsTest
private class VendorAccountApiTest {
    @IsTest static void getAccount_success() {
        Test.setMock(HttpCalloutMock.class,
            new MockHttpResponseGenerator().withResponse(200, '{"externalId":"A-1","name":"ACME","status":"Active"}'));
        Test.startTest();
        VendorAccountApi.AccountDto dto = new VendorAccountApi().getAccount('A-1');
        Test.stopTest();
        System.assertEquals('ACME', dto.name);
    }
    @IsTest static void getAccount_notFound() {
        Test.setMock(HttpCalloutMock.class,
            new MockHttpResponseGenerator().withResponse(404, '{"error":"not_found"}'));
        Test.startTest();
        try { new VendorAccountApi().getAccount('X'); System.assert(false, 'expected NotFound'); }
        catch (VendorAccountApi.NotFoundException e) { /* ok */ }
        Test.stopTest();
    }
    @IsTest static void getAccount_transientRetry() {
        Test.setMock(HttpCalloutMock.class,
            new MockHttpResponseGenerator()
                .pushSequence(503, '')
                .pushSequence(200, '{"externalId":"A-1","name":"ACME"}'));
        Test.startTest();
        VendorAccountApi.AccountDto dto = new VendorAccountApi().getAccount('A-1');
        Test.stopTest();
        System.assertEquals('ACME', dto.name);
    }
}
```

## Case 2 — Timeout and retry tuning

**Priority:** P0

**User prompt:**

> "Our callout to a payment provider sometimes times out. The current code
> doesn't set a timeout. What should I do and what number should I use?"

**Expected output MUST include:**

- Always set an explicit timeout; default platform timeout is 10s but
  relying on defaults is fragile.
- Payment APIs: 20–30s is typical (payment auth can take 15s).
- Retry ONLY on idempotent methods (GET, PUT, DELETE, PATCH with
  idempotency key) — NEVER on POST without an idempotency key.
- Exponential backoff; cap retries at 2–3 to stay under the 120s total
  callout budget per transaction.
- Prefer moving the callout to Queueable if it's not user-blocking — more
  headroom + Finalizer for retry across transactions.
- Log every retry attempt to `ApplicationLogger`.

**Expected output MUST NOT include:**

- "Just set timeout to 120000" (the Apex max is 120s for the whole
  transaction; you'd leave no room for DML before/after).
- Retry on any POST without discussing idempotency.

**Rubric (0–5):**

- **Correctness:** Timeout set, retry gated on idempotency.
- **Completeness:** Covers sync vs async (Queueable) placement.
- **Bulk safety:** If batch-invoked, retries account for the per-transaction 120s wall.
- **Security:** Named Credential mentioned as prerequisite.
- **Citation of official docs:** Links to callout governor limits + HttpRequest.setTimeout.

**Reference answer (gold):**

"Two changes:

**Set an explicit timeout**. For payment auth, 20–30s is typical — payment processors sometimes wait on bank responses. Use `.timeoutMs(25000)` on the `HttpClient`.

**Retry policy**:

- GET, PUT, DELETE, PATCH with idempotency-key header → safe to retry on 5xx/408/429/network error. Use `.retryOnTransient(true)` with `.maxAttempts(3)`.
- POST without idempotency key → DO NOT retry. A retry could create a duplicate charge. Fix by asking the vendor for an idempotency-key support (most payment processors require it now); include a `UUID.randomUUID` per call.

Total budget: Apex transactions have a 120s wall clock. 3 retries × 25s timeout + backoffs = 75-90s — leaves some but not much. If the callout is not synchronous to user input, move it to Queueable with a Finalizer so transient failures retry across transactions without hitting the 120s cap:

```apex
public class PaymentCallout implements Queueable, Database.AllowsCallouts, Finalizer {
    // execute() makes the idempotent callout
    // execute(FinalizerContext) retries via a fresh Queueable on UnexpectedException
}
```

Logging every retry is critical: `ApplicationLogger.warn('PaymentCallout.retry', 'attempt 2: 503 upstream')` so Ops can correlate a spike in retries with upstream outages."

## Case 3 — Testing a class that makes callouts without hitting the network

**Priority:** P0

**User prompt:**

> "My tests fail with `System.CalloutException: You have uncommitted work
> pending` when I try to test my HTTP integration. How should I structure
> these tests?"

**Expected output MUST include:**

- You cannot do DML and then callout in the same method — resolve by
  either (a) committing DML before the callout via `Test.startTest()` split,
  or (b) using `Test.setMock` and not doing DML at all in the test.
- Use `MockHttpResponseGenerator` with `Test.setMock(HttpCalloutMock.class, ...)`.
- Structure: `@TestSetup` creates data, test method sets the mock, calls
  the method under test, asserts.
- Separate methods for success and failure paths; each sets a fresh mock.
- Never rely on the live network in tests — test runs in CI with no
  egress.

**Expected output MUST NOT include:**

- Using `HttpCalloutMock` inline without the shared `MockHttpResponseGenerator`.
- "Just skip those tests" or `@IsTest(SeeAllData=true)`.
- Suggesting `System.runAs` as the fix (unrelated).

**Rubric (0–5):**

- **Correctness:** Identifies DML-before-callout rule.
- **Completeness:** @TestSetup + mock + multiple test methods.
- **Bulk safety:** Test exercises at least 2 records in the success path.
- **Security:** Test user has minimum permissions.
- **Citation of official docs:** Links to HttpCalloutMock docs + `@TestSetup`.

**Reference answer (gold):**

"The 'uncommitted work pending' error means you did DML in the test before the callout. The platform disallows mixing DML and HTTP callouts in the same transaction. Options:

**Option A** — split with `Test.startTest()`:

```apex
@IsTest
private class VendorIntegrationTest {
    @TestSetup static void setup() {
        insert TestDataFactory.createAccounts(2, null);
    }
    @IsTest static void syncAccount_success() {
        Test.setMock(HttpCalloutMock.class,
            new MockHttpResponseGenerator().withResponse(200, '{"id":"ext-1"}'));
        Account a = [SELECT Id FROM Account LIMIT 1];
        Test.startTest();
        VendorSyncService.syncOne(a.Id);  // this method does the callout
        Test.stopTest();
        Account refreshed = [SELECT External_Id__c FROM Account WHERE Id = :a.Id];
        System.assertEquals('ext-1', refreshed.External_Id__c);
    }
}
```

`@TestSetup` commits, the test method then has a clean slate for the
callout. `Test.startTest()/stopTest()` also lets any enqueued async work run.

**Option B** — use `Test.isRunningTest()` or a test-only hook so the code under test defers DML until after the callout. Only pick this if the production code is also async.

Always:

- `Test.setMock` before the method under test runs.
- Separate success / 404 / 5xx methods; each sets its own mock.
- Never SeeAllData=true for integration tests.
- CI has no egress — any test that hits the real endpoint is a bug, not a feature."
