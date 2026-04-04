# Examples — Webhook Inbound Patterns

## Example 1: GitHub Webhook with HMAC Verification and Async Processing

**Context:** A DevOps team needs to receive GitHub push events in Salesforce to create Deployment records automatically when code is pushed to main. GitHub uses HMAC-SHA256 signatures with a shared secret.

**Problem:** Processing the webhook synchronously takes 8+ seconds due to looking up related records and creating multiple objects. GitHub has a 10-second timeout and marks deliveries as failed if no response is received in time.

**Solution:**

```apex
@RestResource(urlMapping='/webhook/github')
global class GitHubWebhookHandler {

    @HttpPost
    global static void handlePush() {
        RestRequest req = RestContext.request;
        RestResponse res = RestContext.response;

        String rawBody = req.requestBody.toString();
        String signature = req.headers.get('X-Hub-Signature-256');

        if (!isValidSignature(rawBody, signature)) {
            res.statusCode = 401;
            return;
        }

        // Parse event type
        Map<String, Object> payload = (Map<String, Object>) JSON.deserializeUntyped(rawBody);
        String deliveryId = req.headers.get('X-GitHub-Delivery');

        // Enqueue async processing immediately
        System.enqueueJob(new GitHubEventProcessor(deliveryId, rawBody));

        // Return 200 within 5 seconds
        res.statusCode = 200;
    }

    private static Boolean isValidSignature(String body, String signature) {
        if (signature == null || !signature.startsWith('sha256=')) return false;
        String secret = [SELECT Value__c FROM Webhook_Secret__mdt
                         WHERE DeveloperName = 'GitHub' LIMIT 1].Value__c;
        String expected = 'sha256=' + EncodingUtil.convertToHex(
            Crypto.generateMac('HmacSHA256', Blob.valueOf(body), Blob.valueOf(secret))
        );
        return expected.equals(signature);
    }
}
```

The `GitHubEventProcessor` Queueable upserts a `Deployment__c` record using `X-GitHub-Delivery` as the External ID.

**Why it works:** The HMAC check rejects unauthorized callers. Enqueueing to a Queueable lets Salesforce respond within the timeout window. The External ID upsert on `X-GitHub-Delivery` ensures retried deliveries do not create duplicates.

---

## Example 2: Stripe Payment Webhook via Salesforce Site

**Context:** A payment team needs to receive Stripe payment success/failure events to update Opportunity payment status. Stripe uses HMAC-SHA256 and sends POST requests — no OAuth support.

**Problem:** Stripe cannot authenticate with OAuth. The endpoint must be publicly accessible without Salesforce session auth.

**Solution:**

1. Create a Salesforce Site at Setup > Sites with domain `payments`.
2. Add `StripeWebhookEndpoint` to the Guest User Profile's Apex Class Access.
3. Configure the webhook URL in Stripe dashboard: `https://payments.my.salesforce-sites.com/services/apexrest/webhook/stripe`
4. The endpoint verifies Stripe's `Stripe-Signature` header using the endpoint's signing secret.

```apex
@RestResource(urlMapping='/webhook/stripe')
global class StripeWebhookEndpoint {

    @HttpPost
    global static void handleEvent() {
        String rawBody = RestContext.request.requestBody.toString();
        String stripeSignature = RestContext.request.headers.get('Stripe-Signature');

        if (!verifyStripeSignature(rawBody, stripeSignature)) {
            RestContext.response.statusCode = 400;
            return;
        }

        Map<String, Object> event = (Map<String, Object>) JSON.deserializeUntyped(rawBody);
        String eventId = (String) event.get('id');

        System.enqueueJob(new StripeEventProcessor(eventId, rawBody));
        RestContext.response.statusCode = 200;
    }
    // verifyStripeSignature() implementation computes HMAC over timestamp.rawBody
}
```

**Why it works:** The Salesforce Site provides a publicly accessible URL. HMAC verification on the Stripe-Signature header authenticates requests. Queueable async processing prevents timeouts.

---

## Anti-Pattern: Parsing the Body Before HMAC Verification

**What practitioners do:** Deserialize the JSON payload first to extract fields, then compute the HMAC over the deserialized string representation.

**What goes wrong:** Serializing the deserialized object produces a different byte sequence than the original body (different whitespace, key ordering). The computed HMAC never matches the sender's signature, causing all webhooks to fail with 401.

**Correct approach:** Compute the HMAC over `req.requestBody.toString()` — the raw string — BEFORE any JSON parsing. Only parse the JSON after the signature is verified.
