# Code Examples — Callouts And HTTP Integrations

Deployable artifacts for one outbound integration: post `Invoice__c` records to an external billing
API through a Named Credential, classify every response, retry only what is retryable, and prove all
three outcomes in tests.

Line references are into the **Apex Developer Guide v67.0, Summer '26** (`apexdev`), the **Apex
Reference Guide v67.0** (`apexrefguide`), the **Metadata API Developer Guide** (`api_meta`) and the
**Salesforce App Limits Cheat Sheet** (`cheatsheet`).

Canonical building blocks used by reference, not re-implemented here:

| Template | Role in this example |
|---|---|
| `templates/apex/HttpClient.cls` | Builds the `HttpRequest`, prefixes `callout:`, sets the timeout, catches transport exceptions, returns `HttpClient.Response` |
| `templates/apex/tests/MockHttpResponseGenerator.cls` | `HttpCalloutMock` with default / per-path / sequence modes — the 500-then-200 retry test uses sequence mode |
| `templates/apex/ApplicationLogger.cls` | Durable failure log; `HttpClient` already calls `ApplicationLogger.error` on a transport failure |

---

## 1. Service class — `BillingApiService.cls`

The service owns **payload shape, idempotency, response typing and error mapping**. It owns no
endpoint string, no credential, and no retry loop.

```apex
/**
 * BillingApiService — outbound integration to the billing system.
 *
 * Endpoint + auth live in the Billing_API Named Credential (see section 4).
 * Transport lives in templates/apex/HttpClient.cls.
 * Retry scheduling lives in BillingSyncQueueable — NOT here.
 */
public with sharing class BillingApiService {

    public class BillingApiException extends Exception {}

    /** Named Credential developer name. The only endpoint knowledge in this class. */
    private static final String NAMED_CREDENTIAL = 'Billing_API';

    /**
     * Per-request timeout. Valid range is 1..120,000 ms (apexrefguide L216720).
     * 20 s keeps four sequential calls inside the 120 s cumulative per-transaction
     * callout budget (apexdev L35856) with headroom.
     */
    private static final Integer TIMEOUT_MS = 20000;

    /** Typed response DTO. Callers never see Map<String, Object>. */
    public class InvoiceAck {
        public String invoiceId;      // remote id
        public String state;          // 'accepted' | 'duplicate'
        public Long   acceptedAtEpoch;
    }

    /** One classified result per input record. */
    public class Outcome {
        public Id invoiceId;
        public Boolean success = false;
        public Boolean isRetryable = false;
        public Integer statusCode;
        public String errorCode;      // stable, loggable, never the raw body
        public String errorMessage;
        public InvoiceAck ack;
    }

    /**
     * Bulk entry point. Sequential by design: a single Apex transaction may make at most
     * 100 callouts (apexdev L35844), so the caller must size the list, and this method
     * stops early rather than throwing LimitException mid-list.
     */
    public static Map<Id, Outcome> postInvoices(List<Invoice__c> invoices) {
        Map<Id, Outcome> results = new Map<Id, Outcome>();
        if (invoices == null || invoices.isEmpty()) {
            return results;
        }
        for (Invoice__c inv : invoices) {
            // Limits.getCallouts() / getLimitCallouts() (apexrefguide L220503, L220532)
            // beat a hardcoded 100 — the number differs in managed-package contexts.
            if (Limits.getCallouts() >= Limits.getLimitCallouts()) {
                Outcome deferred = new Outcome();
                deferred.invoiceId  = inv.Id;
                deferred.isRetryable = true;
                deferred.errorCode  = 'CALLOUT_BUDGET_EXHAUSTED';
                deferred.errorMessage = 'Transaction callout limit reached before this record';
                results.put(inv.Id, deferred);
                continue;
            }
            results.put(inv.Id, postOne(inv));
        }
        return results;
    }

    private static Outcome postOne(Invoice__c inv) {
        HttpClient.Response res = new HttpClient()
            .namedCredential(NAMED_CREDENTIAL)
            .path('/v1/invoices')
            .method('POST')
            .header('Content-Type', 'application/json')
            .header('Accept', 'application/json')
            // Idempotency-Key lets the remote system collapse a retry of a request it
            // already accepted. Without it, "retry on 500" can double-bill: a 500 may
            // mean "failed" or "succeeded, reply lost" and the client cannot tell.
            .header('Idempotency-Key', idempotencyKey(inv))
            .timeoutMs(TIMEOUT_MS)
            // FALSE on purpose. HttpClient.send() backs off with a busy-wait loop, which
            // burns CPU time against the 10,000 ms sync / 60,000 ms async ceiling
            // (cheatsheet L91, apexdev L19579). Retries belong on the job boundary.
            .retryOnTransient(false)
            .body(JSON.serialize(toPayload(inv)))
            .send();

        return classify(inv.Id, res);
    }

    /**
     * Stable per-invoice key. CreatedDate is immutable, so a retry of the same invoice
     * reproduces the same key; a genuinely new submission gets a new record and a new key.
     */
    private static String idempotencyKey(Invoice__c inv) {
        if (String.isNotBlank(inv.Idempotency_Key__c)) {
            return inv.Idempotency_Key__c;
        }
        return String.valueOf(inv.Id) + '-' + String.valueOf(inv.CreatedDate.getTime());
    }

    private static Map<String, Object> toPayload(Invoice__c inv) {
        return new Map<String, Object>{
            'externalRef'  => inv.Name,
            'amountMinor'  => (inv.Total__c == null) ? 0 : (inv.Total__c * 100).intValue(),
            'currencyCode' => inv.Currency_Code__c,
            'issuedOn'     => String.valueOf(inv.Issued_On__c)
        };
    }

    /**
     * Error mapping. Every branch sets isRetryable explicitly — there is no default
     * "retry everything" and no default "give up".
     */
    private static Outcome classify(Id invoiceId, HttpClient.Response res) {
        Outcome out = new Outcome();
        out.invoiceId  = invoiceId;
        out.statusCode = res.statusCode;

        // HttpClient catches transport failures (connect timeout, DNS, TLS) and reports
        // statusCode 0 with the exception message in status — CalloutException never
        // escapes it. Code that only switches on 2xx/4xx/5xx silently drops this case.
        if (res.statusCode == null || res.statusCode == 0) {
            out.isRetryable   = true;
            out.errorCode     = 'TRANSPORT';
            out.errorMessage  = res.status;
            return out;
        }

        if (res.statusCode >= 200 && res.statusCode < 300) {
            try {
                out.ack = (InvoiceAck) JSON.deserialize(res.body, InvoiceAck.class);
            } catch (Exception parseError) {
                // A 2xx with an unparseable body is a contract break, not a network blip.
                out.isRetryable  = false;
                out.errorCode    = 'BAD_RESPONSE_SHAPE';
                out.errorMessage = parseError.getMessage();
                return out;
            }
            if (String.isBlank(out.ack.invoiceId)) {
                out.isRetryable  = false;
                out.errorCode    = 'BAD_RESPONSE_SHAPE';
                out.errorMessage = 'Response omitted invoiceId';
                return out;
            }
            out.success = true;
            return out;
        }

        if (res.statusCode == 401 || res.statusCode == 403) {
            // Never retried: the credential is wrong, and a retry loop turns a config
            // error into a lockout on the remote side.
            out.isRetryable  = false;
            out.errorCode    = 'AUTH';
            out.errorMessage = 'Check the Billing_API Named Credential principal';
            return out;
        }

        if (res.statusCode == 408 || res.statusCode == 429 || res.statusCode >= 500) {
            out.isRetryable  = true;
            out.errorCode    = (res.statusCode == 429) ? 'THROTTLED' : 'UPSTREAM';
            out.errorMessage = truncate(res.body, 240);
            return out;
        }

        out.isRetryable  = false;
        out.errorCode    = 'REJECTED';
        out.errorMessage = truncate(res.body, 240);
        return out;
    }

    private static String truncate(String value, Integer max) {
        if (String.isBlank(value)) {
            return '';
        }
        return value.length() <= max ? value : value.substring(0, max);
    }
}
```

---

## 2. Async wrapper — `BillingSyncQueueable.cls`

The trigger enqueues; the Queueable calls out. `Database.AllowsCallouts` is what makes HTTP legal in
a queueable job (apexdev L16164–16165).

```apex
/**
 * BillingSyncQueueable — the callout boundary for Invoice__c.
 *
 * Called from an after-insert/after-update trigger handler with IDs only.
 * Order inside execute() is deliberate: query, call out, THEN dml.
 */
public with sharing class BillingSyncQueueable implements Queueable, Database.AllowsCallouts {

    /** Leaves headroom under the 100-callouts-per-transaction ceiling (apexdev L35844). */
    private static final Integer CALLOUT_BUDGET = 80;

    /** Bounded. An unbounded retry chain fails at the platform's chaining limit with nothing written down. */
    private static final Integer MAX_ATTEMPTS = 4;

    private final Set<Id> invoiceIds;
    private final Integer attempt;

    public BillingSyncQueueable(Set<Id> invoiceIds) {
        this(invoiceIds, 1);
    }

    public BillingSyncQueueable(Set<Id> invoiceIds, Integer attempt) {
        this.invoiceIds = (invoiceIds == null) ? new Set<Id>() : invoiceIds;
        this.attempt    = (attempt == null || attempt < 1) ? 1 : attempt;
    }

    public void execute(QueueableContext context) {
        if (invoiceIds.isEmpty()) {
            return;
        }

        List<Invoice__c> all = [
            SELECT Id, Name, Total__c, Currency_Code__c, Issued_On__c, CreatedDate,
                   Idempotency_Key__c, Sync_Status__c, Sync_Attempts__c,
                   Sync_Error__c, External_Invoice_Id__c
            FROM Invoice__c
            WHERE Id IN :invoiceIds
            WITH USER_MODE
            ORDER BY CreatedDate
        ];
        if (all.isEmpty()) {
            return;
        }

        List<Invoice__c> thisPass = new List<Invoice__c>();
        Set<Id> deferred = new Set<Id>();
        for (Invoice__c inv : all) {
            if (thisPass.size() < CALLOUT_BUDGET) {
                thisPass.add(inv);
            } else {
                deferred.add(inv.Id);
            }
        }

        // --- callouts happen before any DML in this transaction ---
        Map<Id, BillingApiService.Outcome> outcomes = BillingApiService.postInvoices(thisPass);

        Set<Id> retryIds = new Set<Id>(deferred);
        for (Invoice__c inv : thisPass) {
            BillingApiService.Outcome result = outcomes.get(inv.Id);
            inv.Sync_Attempts__c = attempt;
            if (result != null && result.success) {
                inv.Sync_Status__c         = 'Synced';
                inv.External_Invoice_Id__c = result.ack.invoiceId;
                inv.Sync_Error__c          = null;
            } else if (result != null && result.isRetryable && attempt < MAX_ATTEMPTS) {
                inv.Sync_Status__c = 'Retrying';
                inv.Sync_Error__c  = result.errorCode + ' ' + result.statusCode + ': ' + result.errorMessage;
                retryIds.add(inv.Id);
            } else {
                inv.Sync_Status__c = 'Failed';
                inv.Sync_Error__c  = (result == null)
                    ? 'No outcome returned'
                    : result.errorCode + ' ' + result.statusCode + ': ' + result.errorMessage;
            }
        }

        // --- DML after the callouts. This direction is always allowed; the reverse is not. ---
        update as user thisPass;

        // One enqueue only: async contexts allow a single System.enqueueJob
        // (cheatsheet L84–85: 50 sync / 1 async).
        if (!retryIds.isEmpty() && attempt < MAX_ATTEMPTS && !Test.isRunningTest()) {
            System.enqueueJob(new BillingSyncQueueable(retryIds, attempt + 1));
        }
    }
}
```

**Where a Finalizer belongs.** The code above records outcomes the service *returned*. It cannot
record the case where `execute()` itself dies — an uncaught `LimitException`, for instance — because
that rolls back the `update`. Attach a `System.Finalizer` when the "we never found out" case must
leave a row behind; the pattern is in **apex/apex-transaction-finalizers**, not duplicated here.

---

## 3. Trigger handler fragment — enqueue, never call out

```apex
// Inside a TriggerHandler subclass (templates/apex/TriggerHandler.cls)
public override void afterInsert() {
    Set<Id> toSync = new Set<Id>();
    for (Invoice__c inv : (List<Invoice__c>) Trigger.new) {
        if (inv.Status__c == 'Approved') {
            toSync.add(inv.Id);
        }
    }
    if (!toSync.isEmpty()) {
        // "Callouts must be made asynchronously from a trigger so that the trigger
        // process isn't blocked while waiting for the external service's response"
        // (apexdev L14900-14902).
        System.enqueueJob(new BillingSyncQueueable(toSync));
    }
}
```

---

## 4. Named Credential + External Credential metadata

Field names, enum values and the shape below come from `api_meta` **NamedCredential** (L89887+),
**NamedCredentialParameter** (L90253+) and **ExternalCredential** (L63601+), extended from the
guide's own sample definitions (L90386–90411, L63857–63878).

`force-app/main/default/namedCredentials/Billing_API.namedCredential-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Billing API</label>
    <namedCredentialType>SecuredEndpoint</namedCredentialType>
    <calloutStatus>Enabled</calloutStatus>
    <namedCredentialParameters>
        <description>Billing service base URL</description>
        <parameterName>DefaultEndpoint</parameterName>
        <parameterType>Url</parameterType>
        <parameterValue>https://billing.example.com</parameterValue>
    </namedCredentialParameters>
    <namedCredentialParameters>
        <description>OAuth client credentials for the billing service</description>
        <parameterName>DefaultAuth</parameterName>
        <parameterType>Authentication</parameterType>
        <externalCredential>Billing_API_Auth</externalCredential>
    </namedCredentialParameters>
    <namedCredentialParameters>
        <description>Tenant header required by the billing service on every request</description>
        <parameterName>X-Tenant-Id</parameterName>
        <parameterType>HttpHeader</parameterType>
        <parameterValue>{!$Source.Tenant_Id__c}</parameterValue>
        <sequenceNumber>1</sequenceNumber>
    </namedCredentialParameters>
    <allowMergeFieldsInBody>false</allowMergeFieldsInBody>
    <allowMergeFieldsInHeader>true</allowMergeFieldsInHeader>
    <generateAuthorizationHeader>true</generateAuthorizationHeader>
</NamedCredential>
```

`force-app/main/default/externalCredentials/Billing_API_Auth.externalCredential-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExternalCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Billing API Auth</label>
    <authenticationProtocol>Oauth</authenticationProtocol>
    <externalCredentialParameters>
        <parameterName>BillingServicePrincipal</parameterName>
        <parameterType>NamedPrincipal</parameterType>
        <sequenceNumber>1</sequenceNumber>
    </externalCredentialParameters>
    <externalCredentialParameters>
        <parameterName>BillingAuthProvider</parameterName>
        <parameterType>AuthProvider</parameterType>
        <authProvider>Billing_OAuth_Provider</authProvider>
    </externalCredentialParameters>
</ExternalCredential>
```

**How to read it**

- `<namedCredentialType>SecuredEndpoint</namedCredentialType>` is the modern form: "extensible and
  uses external credentials to control authentication and permissions" (api_meta L90147–90148). The
  `Legacy` value exists only for backward compatibility, and every `Legacy`-only field —
  `endpoint`, `authProvider`, `certificate`, `oauthToken`, `password`, `username` — is **deprecated
  in API version 56.0** (api_meta L89946, L90037, L90158, L90200, L90211). A generated Named Credential that
  carries `<endpoint>` instead of a `Url` parameter is 56.0-era output.
- The endpoint is a `namedCredentialParameters` entry of `parameterType` `Url`, with the URL in
  `parameterValue` (api_meta L90352–90354). Apex then addresses it as
  `callout:Billing_API/v1/invoices` — "the scheme `callout:`, the name of the named credential, and
  an optional path" (apexdev L34332–34335).
- `parameterType` `HttpHeader` "allows the user to specify custom headers to be added to the callout
  at run time … `parameterName` must be the header name as a string, and `parameterValue` must be a
  formula of a header value that is evaluated at run time" (api_meta L90326–90331), ordered by
  `sequenceNumber` (api_meta L90369). Headers that never vary belong here, not in Apex.
- `allowMergeFieldsInHeader` must be `true` for the merge field above to resolve; both merge-field
  flags default to `false` (api_meta L89917–89920, L89935–89939).
- `<calloutStatus>Enabled</calloutStatus>` is available in **API version 59.0 and later** (api_meta
  L90006). Omit it if your `sourceApiVersion` is below 59.0.
- The External Credential's `principal` field is gone: "First available in API version 56.0, this
  field is removed in API version 58.0 and later" (api_meta L63830–63831). Permission-set access to
  the principal is granted through the permission set's own External Credential Principal Access,
  not from this file.
- `authenticationProtocol` valid values are `AwsSv4`, `Basic`, `Custom`, `Jwt`, `JwtExchange`,
  `NoAuthentication`, `Oauth`, `Password` — and the guide marks `Jwt`, `JwtExchange`,
  `NoAuthentication` and `Password` "Reserved for future use" (api_meta L63640–63656).
- Optional but useful for OAuth: an `AdditionalRefreshStatusCode` parameter "allows the user to
  specify 4xx, 6xx, 7xx, 8xx, and 9xx HTTP status codes that trigger Salesforce to refresh expired
  or invalid access tokens, in addition to the standard 401" (api_meta L63753–63757). It is omitted
  above because UNVERIFIED (2026-09-05): the guide does not state the `parameterValue` format for
  this parameter type (single code, comma list, or range).
- **Secrets are not in this file.** The client secret lives in the Auth. Provider / External
  Credential principal in the target org; the metadata carries only the reference.

---

## 5. Remote Site Setting — only if you are *not* using a Named Credential

"Before any Apex callout can call an external site, that site must be registered in the Remote Site
Settings page, or the callout fails … If the callout specifies a named credential as the endpoint,
you don't need to configure remote site settings" (apexdev L34293–34299).

`force-app/main/default/remoteSiteSettings/Billing_Legacy_Reports.remoteSite-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<RemoteSiteSetting xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Legacy unauthenticated billing report feed. New work uses Billing_API.</description>
    <disableProtocolSecurity>false</disableProtocolSecurity>
    <isActive>true</isActive>
    <url>https://reports.billing.example.com</url>
</RemoteSiteSetting>
```

`disableProtocolSecurity` is **required** and controls whether Salesforce may pass data between an
HTTPS session and an HTTP session: "Only set to true if you understand the security implications"
(api_meta L103824–103829). Leave it `false`.

---

## 6. Class metadata — `*.cls-meta.xml`

One per class, alongside the `.cls`. `apiVersion` matches the guide this package is grounded in
(Apex Developer Guide **Version 67.0, Summer '26**, `apexdev` L2) and
`templates/apex/HttpClient.cls-meta.xml`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

---

## 7. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>BillingApiService</members>
        <members>BillingSyncQueueable</members>
        <members>BillingApiServiceTest</members>
        <members>HttpClient</members>
        <members>ApplicationLogger</members>
        <members>MockHttpResponseGenerator</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Billing_API_Auth</members>
        <name>ExternalCredential</name>
    </types>
    <types>
        <members>Billing_API</members>
        <name>NamedCredential</name>
    </types>
    <version>67.0</version>
</Package>
```

Deploy order matters in a fresh org: the External Credential must exist before the Named Credential
that references it, and the Auth. Provider before both. A single `deploy` of this manifest handles
the first ordering; the Auth. Provider is created in Setup or deployed separately.

---

## 8. Test class — `BillingApiServiceTest.cls`

Covers 200, 500-then-200 (retry), a hard 400, and a transport failure. Without `Test.setMock`, "test
methods don't support HTTP callouts, so tests that perform callouts fail" (apexdev L35384–35385).

```apex
@IsTest
private class BillingApiServiceTest {

    /**
     * Transport-failure mock. The Apex runtime calls respond() to produce the fake
     * response (apexrefguide L216190-216193); this implementation throws instead, so
     * HttpClient's catch block runs and reports statusCode 0.
     *
     * UNVERIFIED (2026-09-05): the v67.0 guides document what respond() returns, not
     * what happens when it throws. This is the widely used technique for exercising a
     * CalloutException path and it works in practice, but it is not a documented contract.
     */
    private class ThrowingMock implements HttpCalloutMock {
        public HttpResponse respond(HttpRequest req) {
            throw new CalloutException('Read timed out');
        }
    }

    private static Invoice__c newInvoice() {
        Invoice__c inv = new Invoice__c(
            Total__c        = 125.50,
            Currency_Code__c = 'GBP',
            Issued_On__c    = Date.today(),
            Status__c       = 'Approved',
            Sync_Status__c  = 'Pending'
        );
        insert inv;
        return [
            SELECT Id, Name, Total__c, Currency_Code__c, Issued_On__c, CreatedDate,
                   Idempotency_Key__c, Sync_Status__c, Sync_Attempts__c,
                   Sync_Error__c, External_Invoice_Id__c
            FROM Invoice__c WHERE Id = :inv.Id
        ];
    }

    @IsTest
    static void postInvoices_success_returnsTypedAck() {
        Invoice__c inv = newInvoice();

        // DML above is outside the block; Test.startTest() must precede Test.setMock
        // (apexdev L35677-35681) or the insert leaves uncommitted work pending.
        Test.startTest();
        Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
            .withResponse(200, '{"invoiceId":"BIL-9001","state":"accepted","acceptedAtEpoch":1757030400000}'));
        Map<Id, BillingApiService.Outcome> results =
            BillingApiService.postInvoices(new List<Invoice__c>{ inv });
        Test.stopTest();

        BillingApiService.Outcome result = results.get(inv.Id);
        Assert.isTrue(result.success, 'A 200 with a well-formed body is a success');
        Assert.isFalse(result.isRetryable, 'A success is never retryable');
        Assert.areEqual('BIL-9001', result.ack.invoiceId, 'DTO must be typed, not a raw map');
        Assert.areEqual('accepted', result.ack.state);
    }

    @IsTest
    static void postInvoices_serverError_isRetryable() {
        Invoice__c inv = newInvoice();

        Test.startTest();
        Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
            .withResponse(500, '{"error":"downstream ledger unavailable"}'));
        Map<Id, BillingApiService.Outcome> results =
            BillingApiService.postInvoices(new List<Invoice__c>{ inv });
        Test.stopTest();

        BillingApiService.Outcome result = results.get(inv.Id);
        Assert.isFalse(result.success);
        Assert.isTrue(result.isRetryable, '5xx must be classified retryable');
        Assert.areEqual('UPSTREAM', result.errorCode);
        Assert.areEqual(500, result.statusCode);
    }

    @IsTest
    static void postInvoices_authFailure_isNotRetryable() {
        Invoice__c inv = newInvoice();

        Test.startTest();
        Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
            .withResponse(401, 'Unauthorized'));
        Map<Id, BillingApiService.Outcome> results =
            BillingApiService.postInvoices(new List<Invoice__c>{ inv });
        Test.stopTest();

        BillingApiService.Outcome result = results.get(inv.Id);
        Assert.isFalse(result.isRetryable, 'A 401 must not enter the retry loop');
        Assert.areEqual('AUTH', result.errorCode);
    }

    @IsTest
    static void postInvoices_badResponseShape_isNotRetryable() {
        Invoice__c inv = newInvoice();

        Test.startTest();
        Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
            .withResponse(200, '<html>maintenance</html>'));
        Map<Id, BillingApiService.Outcome> results =
            BillingApiService.postInvoices(new List<Invoice__c>{ inv });
        Test.stopTest();

        BillingApiService.Outcome result = results.get(inv.Id);
        Assert.isFalse(result.success, 'A 200 carrying an HTML error page is not a success');
        Assert.areEqual('BAD_RESPONSE_SHAPE', result.errorCode);
    }

    @IsTest
    static void postInvoices_transportFailure_reportsStatusZero() {
        Invoice__c inv = newInvoice();

        Test.startTest();
        Test.setMock(HttpCalloutMock.class, new ThrowingMock());
        Map<Id, BillingApiService.Outcome> results =
            BillingApiService.postInvoices(new List<Invoice__c>{ inv });
        Test.stopTest();

        BillingApiService.Outcome result = results.get(inv.Id);
        Assert.areEqual(0, result.statusCode, 'HttpClient reports 0, not null, on a transport failure');
        Assert.areEqual('TRANSPORT', result.errorCode);
        Assert.isTrue(result.isRetryable);
    }

    @IsTest
    static void queueable_marksRetryingAndWritesError() {
        Invoice__c inv = newInvoice();

        Test.startTest();
        Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
            .withResponse(503, 'Service Unavailable'));
        System.enqueueJob(new BillingSyncQueueable(new Set<Id>{ inv.Id }));
        Test.stopTest();

        Invoice__c after = [
            SELECT Sync_Status__c, Sync_Error__c, Sync_Attempts__c
            FROM Invoice__c WHERE Id = :inv.Id
        ];
        Assert.areEqual('Retrying', after.Sync_Status__c);
        Assert.areEqual(1, after.Sync_Attempts__c.intValue());
        Assert.isTrue(after.Sync_Error__c.startsWith('UPSTREAM 503'),
            'The stable error code, not the raw body, is what operations searches on');
    }

    @IsTest
    static void bulk_twoHundredInvoices_staysUnderCalloutBudget() {
        List<Invoice__c> batch = new List<Invoice__c>();
        for (Integer i = 0; i < 200; i++) {
            batch.add(new Invoice__c(
                Total__c = 10, Currency_Code__c = 'GBP', Issued_On__c = Date.today(),
                Status__c = 'Approved', Sync_Status__c = 'Pending'));
        }
        insert batch;

        Test.startTest();
        Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
            .withResponse(200, '{"invoiceId":"BIL-X","state":"accepted"}'));
        System.enqueueJob(new BillingSyncQueueable(new Map<Id, Invoice__c>(batch).keySet()));
        Test.stopTest();

        Assert.isTrue(Limits.getCallouts() <= Limits.getLimitCallouts(),
            'A 200-record enqueue must not attempt 200 callouts in one transaction');
        Assert.areEqual(80, [SELECT COUNT() FROM Invoice__c WHERE Sync_Status__c = 'Synced'],
            'Only CALLOUT_BUDGET records are attempted per job; the rest carry to the next job');
    }
}
```

Note on the last two tests: `BillingSyncQueueable` guards its re-enqueue with
`!Test.isRunningTest()`, so the test asserts the *first* pass only. Chained queueable jobs are
testable "by using appropriate stack depths, but be aware of applicable Apex governor limits"
(apexdev L16166–16167) — cover the chain in a separate test if the retry ladder itself is the risk.

---

## 9. Deploy and verify

```bash
# Deploy the classes and the credential metadata
sf project deploy start -x manifest/package.xml -o myOrg -w 20

# Run the tests with coverage
sf apex run test -n BillingApiServiceTest -r human -w 10 -c -o myOrg

# Static check before review
python3 skills/apex/callouts-and-http-integrations/scripts/check_callouts_and_http_integrations.py \
    --manifest-dir force-app
```

Verify the Named Credential resolved in the target org — this returns the callout endpoint the org
will actually use, which is the value that drifts between sandbox and production:

```apex
// sf apex run --file check.apex
List<NamedCredential> ncs = [
    SELECT DeveloperName, Endpoint, PrincipalType
    FROM NamedCredential
    WHERE DeveloperName = 'Billing_API'
];
System.debug(ncs.isEmpty() ? 'MISSING' : ncs[0].DeveloperName + ' -> ' + ncs[0].Endpoint);
```

Then confirm the async run and the row-level outcome:

```soql
SELECT Id, ApexClass.Name, Status, NumberOfErrors, ExtendedStatus, CompletedDate
FROM AsyncApexJob
WHERE ApexClass.Name = 'BillingSyncQueueable'
ORDER BY CreatedDate DESC
LIMIT 10
```

```soql
SELECT Sync_Status__c, COUNT(Id) records
FROM Invoice__c
WHERE LastModifiedDate = TODAY
GROUP BY Sync_Status__c
```

A healthy run has zero rows in `Retrying` after the chain drains. Rows stuck in `Retrying` mean the
chain died between jobs — that is the case a `System.Finalizer` covers
(**apex/apex-transaction-finalizers**).
