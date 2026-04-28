## Example 1: HMAC signing key for outbound webhook

**Context:** A managed package (namespace `acme`) signs outbound HTTP requests to a customer's webhook endpoint with HMAC-SHA256. The signing secret must be readable by Apex inside the namespace, invisible to subscriber admins, and rotatable without a code deploy.

**Problem:** Engineer instinct is `private static final String SIGNING_KEY = 'sk_live_...'`. That value lives in version control, in package distributions, and in any compiled artifact — a single leak compromises every customer.

**Solution:**

Create Protected CMDT `Webhook_Signing_Key__mdt` with `Value__c` (Long Text Area, External ID), `Key_Version__c`, `Active__c`. Mark the type Protected. Ship inside the managed package.

```apex
public with sharing class WebhookSigner {

    @NamespaceAccessible
    public static Blob activeSigningKey() {
        for (Webhook_Signing_Key__mdt k : Webhook_Signing_Key__mdt.getAll().values()) {
            if (k.Active__c) {
                return EncodingUtil.base64Decode(k.Value__c);
            }
        }
        throw new SecretsException('No active signing key configured');
    }

    @NamespaceAccessible
    public static String sign(String payload) {
        Blob mac = Crypto.generateMac('HmacSHA256', Blob.valueOf(payload), activeSigningKey());
        return EncodingUtil.base64Encode(mac);
    }

    public class SecretsException extends Exception {}
}
```

**Why it works:** Subscribers cannot read `Webhook_Signing_Key__mdt.Value__c` via SOQL, Tooling API, or anonymous Apex — Protected CMDT in a packaged namespace blocks all four. `@NamespaceAccessible` lets sibling classes inside `acme` invoke `activeSigningKey()` while keeping subscriber Apex out. Rotation is a single CMDT row insert + flip of `Active__c`, no code deploy.

---

## Example 2: Inbound webhook signature verification (third-party shared secret)

**Context:** A SaaS provider POSTs events to a public-facing Apex REST endpoint. They sign each request with a shared HMAC secret defined in their dashboard. Apex must verify the signature on every inbound call.

**Problem:** Engineer adds the shared secret to a regular Custom Setting "for now" so the customer-success team can paste it during onboarding. The setting is unprotected — every internal user with View Setup can read the secret, and `Trust__c.getInstance().Webhook_Secret__c` shows up in debug logs whenever anyone enables Apex profiling.

**Solution:**

Define Protected Hierarchy Custom Setting `Inbound_Webhook_Trust__c` with `Provider__c`, `Shared_Secret__c` (Encrypted Text where possible, Text otherwise), and ship inside the managed package.

```apex
@RestResource(urlMapping='/events/v1/*')
global with sharing class InboundEventsResource {

    @HttpPost
    global static void receive() {
        RestRequest req = RestContext.request;
        String provider = req.headers.get('X-Provider');
        String signature = req.headers.get('X-Signature-256');

        Inbound_Webhook_Trust__c trust = Inbound_Webhook_Trust__c.getInstance(provider);
        if (trust == null) {
            RestContext.response.statusCode = 401;
            return;
        }
        Blob expected = Crypto.generateMac(
            'HmacSHA256',
            req.requestBody,
            Blob.valueOf(trust.Shared_Secret__c)
        );
        if (EncodingUtil.base64Encode(expected) != signature) {
            // Never log the expected MAC or the secret in this branch.
            RestContext.response.statusCode = 401;
            return;
        }
        EventDispatcher.handle(req.requestBody);
    }
}
```

**Why it works:** The Protected Hierarchy Custom Setting is per-org configurable (admins paste the dashboard secret into a setup page exposed by the package), but the value can only be read by namespace Apex. Constant-time comparison should replace `==` in production; this snippet keeps the storage pattern in focus.

---

## Example 3: Customer-supplied per-tenant API key (subscriber-side configuration)

**Context:** A managed package integrates with Stripe. Each subscriber org has its own Stripe account and its own restricted-access API key. The subscriber admin must be able to set the key but should not be able to read it back, screenshot it, or export it via Data Loader.

**Problem:** "Just put it in a Custom Setting" leaves the value visible to any user with View Setup and to any extracted-metadata audit. Worse, if the package is unmanaged, even Protected CMDT doesn't hide the value from the subscriber admin.

**Solution:**

Use Protected Hierarchy Custom Setting `Stripe_Config__c` with `Api_Key__c` (Encrypted Text, 175 chars). Provide a Lightning Web Component setup screen with a write-only input — the LWC sends the value via `@AuraEnabled` Apex into the setting, but never reads it back. Package the type and the setup LWC together as a managed package with namespace `acme`.

```apex
public with sharing class StripeConfigSetup {

    @AuraEnabled
    public static void saveApiKey(String key) {
        if (String.isBlank(key) || !key.startsWith('rk_')) {
            throw new AuraHandledException('Invalid Stripe restricted key format.');
        }
        Stripe_Config__c cfg = Stripe_Config__c.getInstance(UserInfo.getOrganizationId());
        if (cfg == null) cfg = new Stripe_Config__c(SetupOwnerId = UserInfo.getOrganizationId());
        cfg.Api_Key__c = key;
        upsert cfg;
    }

    // No corresponding @AuraEnabled getter. Reading happens only inside namespace Apex.

    @NamespaceAccessible
    public static String getApiKey() {
        return Stripe_Config__c.getInstance().Api_Key__c;
    }
}
```

**Why it works:** The subscriber admin can SET the value via the LWC (write path is `@AuraEnabled`) but cannot GET it (no exposed getter, and the setting is Protected so direct SOQL from subscriber code returns null/error). Internal namespace Apex reads via `@NamespaceAccessible getApiKey()` only at the moment of callout. Combine with a Named Credential (`Stripe_NC`) that delegates the Authorization header injection — `getApiKey` is a fallback for SDK-style code that demands a raw bearer.

---

## Anti-Pattern: "Temporary" hardcoded key

**What practitioners do:** During development, paste the live API key into the class — `private static final String STRIPE_KEY = 'rk_live_a1b2...';` — with a `// TODO: move to settings before prod` comment.

**What goes wrong:** The TODO survives the demo, survives the deploy, survives the package upload. The key is now in version control, in every developer's local clone, in CI logs, and in the managed-package distribution. Rotation requires a code change and a deploy to every subscriber org.

**Correct approach:** Even on day one, store in Named Credential (for callouts) or Protected CMDT (for signing). The "five extra minutes" pays back the first time you rotate.
