---
name: webhook-inbound-patterns
description: "Use when implementing an inbound webhook receiver in Salesforce: routing via Apex REST and Salesforce Sites, authenticating webhook payloads via HMAC, ensuring idempotent processing, and handling the 5-second response window. NOT for outbound callouts from Salesforce to external systems (use callouts-and-http-integrations), NOT for general Apex REST service design (use apex-rest-services), NOT for platform events as inbound triggers."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "how do I receive a webhook in Salesforce from an external system"
  - "how do I verify HMAC signature on an incoming webhook in Apex"
  - "my Salesforce Site webhook endpoint is getting 401 errors from the external sender"
  - "how do I make my Apex REST webhook endpoint idempotent to handle retries"
  - "my webhook receiver is timing out because processing takes too long"
  - "inbound integration isn't working"
tags:
  - webhook
  - inbound-integration
  - apex-rest
  - salesforce-sites
  - hmac-verification
  - idempotency
inputs:
  - "External system's webhook payload format and HTTP method (POST/GET)"
  - "Authentication mechanism used by the sender (HMAC signature, OAuth, API key)"
  - "Whether authentication is required (authenticated vs. unauthenticated webhooks)"
  - "Expected processing latency and whether async processing is needed"
outputs:
  - "Apex @RestResource class with @HttpPost handler and HMAC verification"
  - "Salesforce Site configuration steps for unauthenticated webhook routing"
  - "Idempotency pattern using External ID field for duplicate prevention"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Webhook Inbound Patterns

Use this skill when implementing an inbound webhook receiver in Salesforce — accepting HTTP POST callbacks from external systems (GitHub, Stripe, Twilio, etc.), verifying payload authenticity, and processing events idempotently. This skill covers the two authentication models (unauthenticated via Salesforce Sites, authenticated via OAuth Client Credentials), HMAC signature verification, idempotency via External ID upsert, and the 5-second response window pattern using Queueable.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify whether the webhook sender is a trusted partner system (use OAuth Client Credentials) or a public SaaS that only supports shared secret HMAC (use Salesforce Sites + HMAC verification).
- Confirm the HTTP method the sender uses (typically POST). @HttpPost is the standard handler.
- Determine if processing the event can complete within 5 seconds (synchronous) or requires longer (use Queueable for async ACK pattern).
- Identify the idempotency key in the payload — the field that uniquely identifies the event so retries can be detected and ignored.

---

## Core Concepts

### Salesforce Sites for Unauthenticated Webhooks

Many SaaS webhook senders cannot perform OAuth flows — they only support shared-secret HMAC or no authentication. To receive webhooks from these senders, expose the Apex REST endpoint via a **Salesforce Site** (Force.com Site) which provides an unauthenticated public URL.

Configuration steps:
1. Create a Salesforce Site in Setup > Sites. Set an active site domain.
2. Add the Apex class containing the `@RestResource` endpoint to the Site's Guest User Profile > Apex Class Access.
3. The webhook URL becomes: `https://<site-domain>.my.salesforce-sites.com/services/apexrest/<your-endpoint-path>`
4. Add HMAC signature verification in the handler — the endpoint is public, so signature verification is the only authentication.

### Authenticated Webhooks via OAuth Client Credentials

For trusted system-to-system integrations where the sender can perform OAuth:
1. Create a Connected App with Client Credentials flow enabled.
2. Configure an integration user with only the permissions needed to process webhook events.
3. The sender authenticates via `POST /services/oauth2/token` with `grant_type=client_credentials` before calling the endpoint.
4. The endpoint URL is the standard org endpoint: `https://<org-domain>/services/apexrest/<path>`

This approach does not require a Salesforce Site.

### HMAC Signature Verification

HMAC (Hash-based Message Authentication Code) verifies that the payload was sent by the trusted sender and was not tampered with in transit.

```apex
@RestResource(urlMapping='/webhook/github')
global class GitHubWebhookEndpoint {
    private static final String SHARED_SECRET = 'your-shared-secret'; // Use Custom Metadata in production

    @HttpPost
    global static void handleWebhook() {
        RestRequest req = RestContext.request;
        RestResponse res = RestContext.response;

        String signature = req.headers.get('X-Hub-Signature-256');
        String body = req.requestBody.toString();

        if (!verifyHmac(body, signature, SHARED_SECRET)) {
            res.statusCode = 401;
            return;
        }

        // Process payload asynchronously
        System.enqueueJob(new WebhookProcessor(body));
        res.statusCode = 200;
    }

    private static Boolean verifyHmac(String body, String signature, String secret) {
        if (signature == null || !signature.startsWith('sha256=')) return false;
        String hex = signature.substring(7);
        if (hex.length() != 64) return false; // hmacSHA256 = 32 bytes = 64 hex chars
        Blob macToVerify;
        try {
            macToVerify = EncodingUtil.convertFromHex(hex);
        } catch (Exception e) {
            return false; // non-hex payload in the header
        }
        // Crypto.verifyHMac does the comparison inside the platform — do NOT
        // recompute the MAC and compare it with String.equals (see below).
        return Crypto.verifyHMac(
            'hmacSHA256', Blob.valueOf(body), Blob.valueOf(secret), macToVerify
        );
    }
}
```

**Key rule:** Use the raw request body (not parsed JSON) for HMAC computation. The signature is computed over the exact bytes sent, before any parsing.

**Key rule — never compare signatures with `==` or `String.equals()`.** Apex `String.equals()` short-circuits at the first differing character, so the call returns measurably faster the fewer leading characters match. That is exactly the timing side-channel HMAC verification is supposed to close: an attacker who can retry a forged delivery can recover the signature one character at a time. Use `Crypto.verifyHMac(algorithmName, data, privateKey, macToVerify)` — the documented Apex method for "Verifies the HMAC signature for the data blob using the specified algorithm, input data, private key, and the mac." It accepts `hmacMD5`, `hmacSHA1`, `hmacSHA256`, and `hmacSHA512`.

If the sender's scheme is not a plain HMAC-over-body (so `verifyHMac` does not apply) and you genuinely must compare two strings, compare them without an early exit:

```apex
// Fixed-iteration compare: every call touches every character of the
// expected value, so elapsed time does not leak how many chars matched.
@TestVisible
private static Boolean equalsConstantTime(String expected, String actual) {
    if (expected == null || actual == null) return false;
    Integer diff = expected.length() ^ actual.length(); // length mismatch -> non-zero
    Integer n = Math.min(expected.length(), actual.length());
    for (Integer i = 0; i < n; i++) {
        diff |= expected.charAt(i) ^ actual.charAt(i);  // charAt returns Integer
    }
    return diff == 0;                                    // one comparison, at the end
}
```

Accumulate the XOR of every character pair and test the accumulator once, at the end. Compare lengths by folding the length difference into the same accumulator rather than returning early on a length mismatch. Hex-encoded HMAC-SHA256 signatures are always 64 characters, so the residual length leak is not exploitable here.

### Idempotency via External ID Upsert

Webhook senders retry on timeout or failure. Without idempotency, the same event is processed multiple times, creating duplicate records.

Pattern:
1. The payload contains a unique event ID (e.g., `event_id`, `delivery_id`)
2. Store processed events in a custom object `Webhook_Event__c` with `Event_Id__c` as an External ID
3. Use Database.upsert with the External ID — if the event was already processed, the upsert updates the existing record (no duplicate DML)
4. Check whether the upsert was an insert or update: `UpsertResult.isCreated()` returns true for new events, false for retries

---

## Common Patterns

### Async ACK Pattern (Queueable)

**When to use:** Processing the webhook event takes longer than 5 seconds, or involves callouts that would conflict with the same-transaction callout restriction.

**How it works:**
```apex
@HttpPost
global static void handleWebhook() {
    String body = RestContext.request.requestBody.toString();
    // Verify HMAC first (synchronous)
    if (!verifyHmac(body)) {
        RestContext.response.statusCode = 401;
        return;
    }
    // Enqueue async processing — respond immediately with 200
    System.enqueueJob(new WebhookProcessor(body));
    RestContext.response.statusCode = 200;
}
```

The `WebhookProcessor` Queueable class does the actual DML and callout work. The HTTP response is returned immediately, satisfying the sender's 5-second timeout.

**Why not synchronous:** Webhook senders typically have a short timeout (5–30 seconds). Synchronous processing that hits SOQL/DML limits or external callouts can exceed this timeout, causing the sender to mark the delivery as failed and retry.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| SaaS sender with HMAC only | Salesforce Site + HMAC verification | Unauthenticated endpoint required for non-OAuth senders |
| Trusted system with OAuth capability | OAuth Client Credentials | More secure — no unauthenticated endpoint |
| Processing takes >5 seconds | Async ACK with Queueable | Respond 200 immediately, process in background |
| Preventing duplicate processing on retry | External ID upsert on event ID | Database-level idempotency |
| Sender uses raw body HMAC | Compute HMAC over requestBody.toString() | Parse before HMAC = wrong hash |

---

## Recommended Workflow

1. **Identify the authentication model.** HMAC-only sender → Salesforce Site. OAuth-capable sender → Client Credentials Connected App.
2. **Create the Apex @RestResource class** with @HttpPost handler. Store shared secrets in Custom Metadata (not hardcoded).
3. **Implement HMAC verification** before any processing. Return 401 immediately if the signature does not match.
4. **Identify the idempotency key** in the payload. Create a `Webhook_Event__c` custom object with the event ID as External ID. Upsert on arrival to detect duplicates.
5. **Add async processing via Queueable** if the event processing exceeds 5 seconds or involves callouts.
6. **If using Salesforce Sites**: configure the Site, add the Apex class to the Guest User Profile's Apex access, and test the public URL with a curl command from outside Salesforce.
7. **Test with retry simulation**: send the same event twice and verify the second delivery does not create duplicate records.

---

## Review Checklist

- [ ] Signature compared with `Crypto.verifyHMac` (or a fixed-iteration accumulator) — never `==`, `String.equals()`, or `equalsIgnoreCase()`
- [ ] HMAC signature verified before any processing — 401 returned immediately on failure
- [ ] Shared secret stored in Custom Metadata, not hardcoded in Apex class
- [ ] Idempotency key identified in payload and upsert used to prevent duplicate processing
- [ ] Async Queueable used for processing that exceeds 5 seconds
- [ ] Salesforce Site configured and Guest User Profile has Apex class access (if unauthenticated)
- [ ] Endpoint tested with curl or Postman with a valid HMAC signature
- [ ] Endpoint tested with a repeated delivery — confirmed no duplicate records created

---

## Salesforce-Specific Gotchas

1. **HMAC must be computed over the raw body bytes, not parsed JSON** — Parsing the body before HMAC computation changes the byte representation. Always use `req.requestBody.toString()` (the raw string) for signature verification, before any `JSON.deserialize()` calls.
2. **Salesforce Site guest user must have explicit Apex class access** — Adding the class to the site is not enough. The guest user profile must explicitly have the class in its Apex Class Access list, or calls return 403.
3. **`String.equals()` is not a constant-time comparison** — Apex `String.equals()` (and `==`) returns as soon as it finds a differing character, so signature checks written as `expected.equals(signature)` leak, through response latency, how many leading characters of the forged signature were correct. Use `Crypto.verifyHMac('hmacSHA256', Blob.valueOf(body), Blob.valueOf(secret), EncodingUtil.convertFromHex(hex))`. There is no `areEqualConstantTime` on the platform `Crypto` class — helpers by that name are hand-written sample code, not an Apex API.
4. **Queueable for the async pattern does NOT inherit the HTTP response** — The HTTP response (status 200) is returned synchronously before the Queueable runs. The Queueable cannot modify the HTTP response. Design the response to be unconditional (always 200 on valid signature) and let the Queueable handle failures via Platform Events or logging.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Apex webhook handler class | @RestResource class with HMAC verification, idempotency check, and Queueable enqueue |
| Salesforce Site setup checklist | Steps to configure an unauthenticated endpoint via Salesforce Sites |
| Custom Metadata structure | Fields for storing webhook shared secrets per sender |

---

## Related Skills

- callouts-and-http-integrations — outbound callouts from Salesforce to external systems
- oauth-flows-and-connected-apps — OAuth Client Credentials flow for authenticated webhooks
- apex-rest-services — general Apex REST endpoint design patterns
