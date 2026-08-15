# Examples — Webhook Signature Verification

An inbound webhook is an unauthenticated-by-default HTTP POST from a third party.
The signature header is the *only* thing distinguishing a genuine Stripe or GitHub
callback from anyone on the internet who knows your endpoint URL. Verifying it
correctly is a short amount of code that is easy to get subtly wrong.

Every Apex construct below is from the Apex Reference Guide and Apex Developer
Guide (Summer '26, API 67.0).

---

## The one platform method that matters

Salesforce ships a dedicated HMAC verifier. Use it:

```apex
public static Boolean Crypto.verifyHMac(
    String algorithmName,   // hmacMD5 | hmacSHA1 | hmacSHA256 | hmacSHA512
    Blob   data,
    Blob   privateKey,      // max 4 KB
    Blob   macToVerify
)
```

The Apex Reference Guide documents the signature, the four valid algorithm names,
the 4 KB key cap, the Base64 symmetry rule, and the Boolean return. It makes **no
claim about the timing characteristics of the comparison**, so neither does this
skill — see [`references/gotchas.md`](gotchas.md) Gotcha 4.

`verifyHMac` is still the right call, for a reason that does not depend on an
undocumented property: the alternative — `Crypto.generateMac(...)` followed by
`String.equals(...)` — makes you write the digest comparison yourself, and
`String.equals` short-circuits on the first differing character. Both Stripe and
GitHub tell integrators to compare signatures in constant time. Calling the
platform's own verifier keeps that comparison out of your code and out of the
review, which is the benefit you can actually rely on.

Note the encoding rule from the reference guide, which is the single most common
source of "the signature never matches":

> "You may supply a private key that has been encoded using Base64 encoding.
> However if you do, then you must also supply the Base64-encoded private key when
> verifying the MAC using the `verifyHMac` method."

---

## Example 1: GitHub webhook (`X-Hub-Signature-256`)

**Context:** A GitHub App posts `push` events to Salesforce so a DevOps custom
object can record commits against a release record.

**Problem:** The endpoint must reject any request whose body was not signed with
the shared secret, and must do so before parsing the payload or touching the
database.

**GitHub's format:** header `X-Hub-Signature-256`, value
`sha256=<lowercase hex HMAC-SHA256 of the raw request body>`.

```apex
@RestResource(urlMapping='/github/v1/*')
global with sharing class GitHubWebhookResource {

    private static final String SIG_HEADER = 'X-Hub-Signature-256';
    private static final String PREFIX     = 'sha256=';

    @HttpPost
    global static void handle() {
        RestRequest  req = RestContext.request;
        RestResponse res = RestContext.response;

        // 1. Read the RAW body. Never re-serialise a parsed object and sign that:
        //    key order and whitespace will differ and the MAC will never match.
        Blob rawBody = req.requestBody;
        if (rawBody == null) {
            reject(res, 400, 'Empty body');
            return;
        }

        // 2. RestRequest.headers is a Map<String, String>. Map keys in Apex are
        //    case-sensitive, but HTTP header names are not. Look the header up
        //    case-insensitively rather than trusting the sender's casing.
        String provided = headerIgnoreCase(req.headers, SIG_HEADER);
        if (String.isBlank(provided) || !provided.startsWith(PREFIX)) {
            reject(res, 401, 'Missing or malformed signature');
            return;
        }

        // 3. GitHub sends lowercase hex. Convert to Blob for verifyHMac.
        Blob expectedMac;
        try {
            expectedMac = EncodingUtil.convertFromHex(provided.substring(PREFIX.length()));
        } catch (Exception e) {
            reject(res, 401, 'Malformed signature encoding');
            return;
        }

        // 4. Secret comes from a protected custom metadata record, never a
        //    hardcoded string and never a custom setting readable by users.
        Blob secret = Blob.valueOf(WebhookSecrets.get('GitHub'));

        // 5. Verify with the platform method rather than a hand-written
        //    digest comparison.
        if (!Crypto.verifyHMac('hmacSHA256', rawBody, secret, expectedMac)) {
            reject(res, 401, 'Signature verification failed');
            return;
        }

        // 6. Only now is it safe to parse and act.
        GitHubPushEvent evt =
            (GitHubPushEvent) JSON.deserialize(rawBody.toString(), GitHubPushEvent.class);
        GitHubEventService.record(evt);

        res.statusCode = 202;
    }

    private static String headerIgnoreCase(Map<String, String> headers, String name) {
        if (headers == null) {
            return null;
        }
        String target = name.toLowerCase();
        for (String key : headers.keySet()) {
            if (key.toLowerCase() == target) {
                return headers.get(key);
            }
        }
        return null;
    }

    private static void reject(RestResponse res, Integer code, String message) {
        // Do not echo the computed signature, the secret, or the body back.
        // A verbose failure response is an oracle for a forging attacker.
        res.statusCode = code;
        res.responseBody = Blob.valueOf('{"error":"' + message + '"}');
        res.addHeader('Content-Type', 'application/json');
        ApplicationLogger.warn('GitHubWebhookResource', message);
    }
}
```

**Why it works:**

- `req.requestBody` is a `Blob` — the untouched bytes GitHub sent. That is exactly
  what GitHub hashed. Any round trip through `JSON.deserializeUntyped` and back
  changes byte order and breaks the MAC.
- `Crypto.verifyHMac` does the comparison itself, so there is no hand-written
  equality check to get wrong or to argue about in review.
- The reject path is uniform: same status, same body shape, no detail about *why*
  verification failed.

---

## Example 2: Stripe webhook (`Stripe-Signature`) with replay protection

**Context:** Stripe posts `invoice.payment_succeeded` events to update a Billing
custom object.

**Problem:** Stripe's header is a compound value, and the signed payload is *not*
just the body — it is `timestamp + "." + body`. A verifier that hashes the body
alone will never match. Stripe also expects the receiver to reject stale
timestamps, which is what stops a captured request being replayed.

**Stripe's format:**
`Stripe-Signature: t=1700000000,v1=<hex HMAC-SHA256>,v1=<another>,v0=<legacy>`
where the signed payload is `"{t}.{raw body}"`.

```apex
@RestResource(urlMapping='/stripe/v1/*')
global with sharing class StripeWebhookResource {

    // Stripe's own recommended default tolerance is 5 minutes.
    private static final Long TOLERANCE_SECONDS = 300;

    @HttpPost
    global static void handle() {
        RestRequest  req = RestContext.request;
        RestResponse res = RestContext.response;

        Blob   rawBody = req.requestBody;
        String header  = headerIgnoreCase(req.headers, 'Stripe-Signature');

        if (rawBody == null || String.isBlank(header)) {
            res.statusCode = 400;
            return;
        }

        // Parse t=... and every v1=... Stripe sends more than one v1 during a
        // secret roll (the previous secret stays active for up to 24 hours), and
        // ANY of them matching is a valid request. Collect ONLY v1: Stripe also
        // emits a fake v0 scheme for test events and instructs receivers to
        // "ignore all schemes that aren't v1" to prevent downgrade attacks.
        String timestamp;
        List<String> v1Signatures = new List<String>();
        for (String part : header.split(',')) {
            List<String> kv = part.trim().split('=', 2);
            if (kv.size() != 2) {
                continue;
            }
            if (kv[0] == 't') {
                timestamp = kv[1];
            } else if (kv[0] == 'v1') {
                v1Signatures.add(kv[1]);
            }
        }
        if (String.isBlank(timestamp) || v1Signatures.isEmpty()) {
            res.statusCode = 401;
            return;
        }

        // Replay window. Check this BEFORE the HMAC so a flood of stale replays
        // costs a Long comparison rather than a crypto operation.
        Long sentAt = Long.valueOf(timestamp);
        Long nowSec = DateTime.now().getTime() / 1000;
        if (Math.abs(nowSec - sentAt) > TOLERANCE_SECONDS) {
            res.statusCode = 401;
            ApplicationLogger.warn('StripeWebhookResource', 'Timestamp outside tolerance');
            return;
        }

        // The signed payload is timestamp + "." + raw body.
        Blob signedPayload = Blob.valueOf(timestamp + '.' + rawBody.toString());
        Blob secret        = Blob.valueOf(WebhookSecrets.get('Stripe'));

        Boolean verified = false;
        for (String hex : v1Signatures) {
            if (Crypto.verifyHMac('hmacSHA256', signedPayload,
                                  secret, EncodingUtil.convertFromHex(hex))) {
                verified = true;
                break;
            }
        }
        if (!verified) {
            res.statusCode = 401;
            return;
        }

        // Idempotency: Stripe retries on any non-2xx and can deliver the same
        // event more than once even on success. The event id is the natural key.
        StripeEvent evt =
            (StripeEvent) JSON.deserialize(rawBody.toString(), StripeEvent.class);

        Webhook_Event__c record = new Webhook_Event__c(
            Provider__c    = 'Stripe',
            External_Id__c = evt.id,          // External Id, Unique
            Event_Type__c  = evt.type,
            Payload__c     = rawBody.toString()
        );

        Database.UpsertResult ur = Database.upsert(
            record, Webhook_Event__c.External_Id__c, false);

        // isSuccess() alone is NOT the idempotency check: a redelivered event
        // upserts onto the existing row and still reports success, so gating on
        // it re-enqueues processing for every retry. isCreated() is true only
        // for the first sighting of this event id.
        if (ur.isSuccess() && ur.isCreated()) {
            StripeEventProcessor.enqueue(evt);
        }

        // 200 fast. Stripe times out and retries if you do the work inline.
        res.statusCode = 200;
    }

    private static String headerIgnoreCase(Map<String, String> headers, String name) {
        String target = name.toLowerCase();
        for (String key : headers.keySet()) {
            if (key.toLowerCase() == target) {
                return headers.get(key);
            }
        }
        return null;
    }
}
```

**Why it works:**

- The signed payload is reconstructed exactly as Stripe built it.
- Multiple `v1` values are all tried, so a secret rotation does not cause an
  outage window.
- The timestamp check bounds replay to five minutes; without it, a signature
  captured once is valid forever.
- The upsert on an External Id makes redelivery idempotent, which matters because
  the provider retries and there is no transactional handshake.

---

## Example 3: Where the secret lives, and how the endpoint is reachable

### The secret

Never a string literal, never a Custom Setting a user can read in a report.

```apex
// force-app/main/default/objects/Webhook_Secret__mdt/
//   fields/Secret__c.field-meta.xml  -> type Text, "Field Manageability: Protected"
public with sharing class WebhookSecrets {
    private static Map<String, Webhook_Secret__mdt> cache;

    /**
     * TEST SEAM — the reason this class has one.
     *
     * Custom Metadata records cannot be inserted by DML, and `getAll()` returns
     * the ORG'S REAL RECORDS inside a test. A verifier test therefore has no
     * secret it can control: it either depends on whichever Webhook_Secret__mdt
     * rows happen to exist in the org it runs in, or — in a clean scratch org —
     * gets the CalloutException below and fails for the wrong reason.
     *
     * Tests populate this map; production never reads it, because the lookup is
     * gated on Test.isRunningTest() as well as on @TestVisible.
     */
    @TestVisible
    private static Map<String, String> testSecrets = new Map<String, String>();

    public static String get(String provider) {
        if (Test.isRunningTest() && testSecrets.containsKey(provider)) {
            return testSecrets.get(provider);
        }
        if (cache == null) {
            cache = new Map<String, Webhook_Secret__mdt>();
            for (Webhook_Secret__mdt s : Webhook_Secret__mdt.getAll().values()) {
                cache.put(s.Provider__c, s);
            }
        }
        Webhook_Secret__mdt row = cache.get(provider);
        if (row == null) {
            throw new CalloutException('No webhook secret configured for ' + provider);
        }
        return row.Secret__c;
    }
}
```

Custom Metadata is the right home because it deploys with the release, is
queryable without a SOQL statement (`getAll()` costs no query), and protected
fields in a managed package are not readable by subscribers. In an unmanaged org
the protection is weaker, so pair it with restrictive permission-set access to the
custom metadata type.

**The seam is not optional, and it is not a testing convenience.** Without it the
negative tests — the ones that are the entire point of this skill — cannot be
written at all. `@TestVisible private` keeps the map unreachable from production
code outside this class, and the `Test.isRunningTest()` guard means that even a
future refactor that widens the visibility cannot change a production lookup.

### Exposing the endpoint

Apex REST requires an authenticated session. A third-party webhook has none. There
are exactly two supported shapes:

**Option A — the provider authenticates (preferred).** Register a Connected App /
External Client App for the provider and have it obtain a token via the OAuth 2.0
client credentials flow, binding to a dedicated integration user. The webhook then
posts to
`https://<mydomain>.my.salesforce.com/services/apexrest/stripe/v1/` with a bearer
token. Signature verification still applies — the token proves *who is calling*,
the signature proves *what they sent was not tampered with*.

**Option B — a public Site.** Expose the class through a Salesforce Site and grant
the site's guest user Apex class access. This makes the endpoint reachable by
anyone, so the signature check becomes the only authentication:

```text
Setup → Sites → [your site] → Public Access Settings
    → Enabled Apex Class Access → add StripeWebhookResource
```

Under Option B the guest user must have the absolute minimum object access — and
because guest users cannot own records and are heavily restricted by design, the
handler should do nothing but write the raw event and enqueue asynchronous
processing that runs under a proper integration context.

**Sizing:** the request body is bounded by the Apex heap. The Apex Developer Guide
gives "the maximum request or response size is 6 MB for synchronous Apex or 12 MB
for asynchronous Apex." A provider that posts large payloads needs a pull-based
design, not a webhook.

---

## Example 4: Testing the verifier, including the negative cases

The thing that makes this test class runnable is the seam from Example 3. A test
that declares `SECRET = 'whsec_test_key'` and then exercises a handler which reads
`WebhookSecrets.get('Stripe')` is asserting against **whatever
`Webhook_Secret__mdt` rows exist in the org running the test** — Custom Metadata
cannot be inserted by DML, and `getAll()` is not isolated in test context. In a
clean scratch org there is no row at all, so the handler throws
`CalloutException` and every case fails for a reason that has nothing to do with
the verifier. Inject the secret; do not hope for it.

```apex
@IsTest
private class StripeWebhookResourceTest {

    private static final String SECRET = 'whsec_test_key';

    /**
     * Bind the test secret through the seam, so the class under test verifies
     * against THIS value rather than against whatever Webhook_Secret__mdt rows
     * the running org happens to hold. Called first in every test method —
     * statics do not survive across transactions, so this cannot live in
     * @TestSetup.
     */
    private static void useTestSecret() {
        WebhookSecrets.testSecrets.put('Stripe', SECRET);
    }

    private static RestRequest buildRequest(String body, Long ts, String sig) {
        RestRequest req = new RestRequest();
        req.requestURI  = '/services/apexrest/stripe/v1/';
        req.httpMethod  = 'POST';
        req.requestBody = Blob.valueOf(body);
        req.addHeader('Stripe-Signature', 't=' + ts + ',v1=' + sig);
        return req;
    }

    private static String sign(String body, Long ts) {
        Blob mac = Crypto.generateMac(
            'hmacSHA256',
            Blob.valueOf(ts + '.' + body),
            Blob.valueOf(SECRET));
        return EncodingUtil.convertToHex(mac);
    }

    @IsTest
    static void validSignatureIsAccepted() {
        useTestSecret();
        String body = '{"id":"evt_1","type":"invoice.payment_succeeded"}';
        Long   ts   = DateTime.now().getTime() / 1000;

        RestContext.request  = buildRequest(body, ts, sign(body, ts));
        RestContext.response = new RestResponse();

        Test.startTest();
        StripeWebhookResource.handle();
        Test.stopTest();

        Assert.areEqual(200, RestContext.response.statusCode);
        Assert.areEqual(1, [SELECT COUNT() FROM Webhook_Event__c WHERE External_Id__c = 'evt_1']);
    }

    @IsTest
    static void tamperedBodyIsRejected() {
        useTestSecret();
        String body = '{"id":"evt_2","amount":100}';
        Long   ts   = DateTime.now().getTime() / 1000;
        String sig  = sign(body, ts);

        // Attacker changes the amount but reuses the captured signature.
        RestContext.request  = buildRequest('{"id":"evt_2","amount":100000}', ts, sig);
        RestContext.response = new RestResponse();

        StripeWebhookResource.handle();

        Assert.areEqual(401, RestContext.response.statusCode);
        Assert.areEqual(0, [SELECT COUNT() FROM Webhook_Event__c]);
    }

    @IsTest
    static void staleTimestampIsRejected() {
        useTestSecret();
        String body = '{"id":"evt_3"}';
        Long   ts   = (DateTime.now().getTime() / 1000) - 3600;   // one hour old

        RestContext.request  = buildRequest(body, ts, sign(body, ts));
        RestContext.response = new RestResponse();

        StripeWebhookResource.handle();

        Assert.areEqual(401, RestContext.response.statusCode,
            'A correctly signed but stale request must still be rejected');
    }

    @IsTest
    static void missingSignatureHeaderIsRejected() {
        useTestSecret();
        RestRequest req = new RestRequest();
        req.requestURI  = '/services/apexrest/stripe/v1/';
        req.httpMethod  = 'POST';
        req.requestBody = Blob.valueOf('{"id":"evt_4"}');

        RestContext.request  = req;
        RestContext.response = new RestResponse();

        StripeWebhookResource.handle();

        Assert.areEqual(400, RestContext.response.statusCode);
    }
}
```

**Why it works:** `RestContext.request` and `RestContext.response` are settable in
test context, so the resource can be exercised without a callout. The injected
secret makes every assertion deterministic — the same result in a scratch org, a
sandbox, and production, with no dependence on the org's metadata rows. And the
three negative tests are the ones that matter: a verifier that accepts everything
passes the positive test perfectly.

---

## Anti-Pattern: Verifying a re-serialised body

**What practitioners do:**

```apex
Map<String, Object> payload =
    (Map<String, Object>) JSON.deserializeUntyped(req.requestBody.toString());
String canonical = JSON.serialize(payload);            // <-- fatal
Blob mac = Crypto.generateMac('hmacSHA256', Blob.valueOf(canonical), secret);
```

**What goes wrong:** HMAC is over bytes. `JSON.serialize` reorders keys, drops
insignificant whitespace, and normalises number formatting. The regenerated MAC
never equals the sender's, so *every* request fails verification — including
genuine ones. Teams then "fix" it by removing the check.

**Correct approach:** hash `req.requestBody` directly, exactly as received, and
parse only after verification succeeds. If the provider signs a derived payload —
as Stripe does with `"{timestamp}.{body}"` — construct that derivation from the
raw body string, never from a re-serialised object.
