# Examples — Apex Named Credentials Patterns

## Example 1: Callout Using Named Credential With Custom OAuth Header Formula Token

**Context:** An external REST API requires the OAuth access token in the `X-Auth-Token` request header rather than the standard `Authorization: Bearer` header. The Named Credential is configured in the enhanced model with a custom header field `X-Auth-Token` set to `{!$Credential.OAuthToken}`. The Apex developer's job is to write the callout; the platform handles token injection.

**Problem:** Developers unfamiliar with the custom header formula approach manually read the OAuth token from a Custom Setting or Custom Label and call `req.setHeader('X-Auth-Token', token)`. This exposes the token in the Salesforce database outside the Protected credential vault, does not handle token refresh automatically, and violates the Well-Architected Security pillar.

**Solution:**

```apex
/**
 * Callout to a REST API that uses a Named Credential with a custom OAuth
 * header formula token.
 *
 * Prerequisites (setup — NOT in this Apex):
 *   - Named Credential API name: ExternalCatalogNC
 *   - External Credential: ExternalCatalogEC (OAuth 2.0 Client Credentials flow)
 *   - Named Credential custom header:
 *       Name:  X-Auth-Token
 *       Value: {!$Credential.OAuthToken}
 *
 * At callout time the platform evaluates {!$Credential.OAuthToken} and
 * injects the active access token into the X-Auth-Token header automatically.
 * The Apex developer does NOT set this header in code.
 */
public class ProductCatalogService {

    private static final String NC_NAME = 'ExternalCatalogNC';

    /**
     * Fetch a product by ID from the external catalog API.
     * @param productId  External system product identifier (not a Salesforce ID)
     * @return  Parsed product name, or null if not found
     */
    public static String fetchProductName(String productId) {
        if (String.isBlank(productId)) {
            throw new IllegalArgumentException('productId is required');
        }

        HttpRequest req = new HttpRequest();
        // callout: prefix — platform resolves endpoint, injects auth headers
        req.setEndpoint('callout:' + NC_NAME + '/products/' + EncodingUtil.urlEncode(productId, 'UTF-8'));
        req.setMethod('GET');
        req.setTimeout(30000); // 30 s; platform max is 120 000 ms

        HttpResponse res = new Http().send(req);

        if (res.getStatusCode() == 200) {
            Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            return (String) body.get('name');
        } else if (res.getStatusCode() == 404) {
            return null;
        } else {
            throw new CalloutException(
                'Unexpected response from ExternalCatalogNC: HTTP ' + res.getStatusCode()
                + ' — ' + res.getStatus()
            );
        }
    }
}
```

**Why it works:** The `callout:ExternalCatalogNC/products/{id}` endpoint is processed by the platform before the HTTP request is sent. The platform resolves the Named Credential's endpoint URL, evaluates any custom header formulas (including `{!$Credential.OAuthToken}`), and appends the resulting headers to the outgoing request. The Apex code never touches authentication data directly. If the token has expired, the platform's OAuth refresh flow kicks in transparently (for refresh-token flows) or the callout fails with a 401 that the caller can detect and handle.

---

## Example 2: Querying UserExternalCredential for Per-User Token Status

**Context:** A Lightning component allows users to browse data from an external SaaS system using per-user OAuth. Before making any callout, the component needs to know whether the current user has authenticated so it can show a "Connect your account" prompt instead of a broken data table.

**Problem:** Developers either skip the pre-auth check and let the callout fail with a confusing HTTP 401, or they make a test callout on page load just to see if auth works — wasting one of the 100 allowed callouts per transaction.

**Solution:**

```apex
/**
 * AuraEnabled controller that checks per-user auth status before callouts.
 *
 * Prerequisites (setup — NOT in this Apex):
 *   - External Credential API name: SaasSystemEC
 *   - External Credential principal type: PerUserPrincipal
 *   - Named Credential API name: SaasSystemNC (references SaasSystemEC)
 */
public with sharing class SaasAuthController {

    /**
     * Returns true if the running user has authenticated with the SaaS system
     * via the PerUserPrincipal OAuth flow.
     *
     * @param externalCredentialDevName  Developer name of the External Credential,
     *                                   e.g. 'SaasSystemEC'
     */
    @AuraEnabled(cacheable=true)
    public static Boolean isUserAuthenticated(String externalCredentialDevName) {
        // Step 1: Resolve External Credential ID from developer name.
        // ExternalCredential is a Setup object accessible via SOQL with WITH SECURITY_ENFORCED.
        List<ExternalCredential> ecs = [
            SELECT Id
            FROM ExternalCredential
            WHERE DeveloperName = :externalCredentialDevName
            WITH SECURITY_ENFORCED
            LIMIT 1
        ];
        if (ecs.isEmpty()) {
            // Named Credential setup is missing or mis-configured.
            return false;
        }

        // Step 2: Check if the current user has a PerUserPrincipal record.
        // UserExternalCredential exists only in enhanced-model orgs.
        List<UserExternalCredential> uecs = [
            SELECT Id, PrincipalType
            FROM UserExternalCredential
            WHERE UserId       = :UserInfo.getUserId()
              AND ExternalCredentialId = :ecs[0].Id
              AND PrincipalType = 'PerUserPrincipal'
            LIMIT 1
        ];
        return !uecs.isEmpty();
    }

    /**
     * Fetches data from the SaaS system for the current user.
     * Throws a user-friendly AuraHandledException if the user is not authenticated.
     */
    @AuraEnabled
    public static List<Map<String, Object>> fetchData(String externalCredentialDevName) {
        if (!isUserAuthenticated(externalCredentialDevName)) {
            throw new AuraHandledException(
                'You have not connected your SaaS System account. '
                + 'Please authenticate from the component settings.'
            );
        }

        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:SaasSystemNC/api/v1/items');
        req.setMethod('GET');
        req.setTimeout(30000);

        HttpResponse res = new Http().send(req);
        if (res.getStatusCode() == 200) {
            return (List<Map<String, Object>>) JSON.deserializeUntyped(res.getBody());
        }
        throw new AuraHandledException('API error: HTTP ' + res.getStatusCode());
    }
}
```

**Why it works:** The `UserExternalCredential` query is a cheap SOQL read (no callout consumed) that answers "has this user ever authenticated?" with high confidence. The two-step flow — resolve External Credential ID, then check `UserExternalCredential` — is necessary because `UserExternalCredential` records are keyed by the Internal Salesforce ID of the External Credential record, not by its developer name. Note the `WITH SECURITY_ENFORCED` clause on the `ExternalCredential` query to respect FLS and object permissions, and the use of `with sharing` on the class to enforce record-level visibility.

---

## Anti-Pattern: Using a Hardcoded Endpoint Instead of the `callout:` Prefix

**What practitioners do:**

```apex
// WRONG: hardcoded base URL + token from Custom Label
HttpRequest req = new HttpRequest();
req.setEndpoint('https://api.acme-corp.com/v2/orders/' + orderId);
req.setMethod('GET');
req.setHeader('Authorization', 'Bearer ' + System.Label.Acme_OAuth_Token);
Http http = new Http();
HttpResponse res = http.send(req);
```

**What goes wrong:**
- The OAuth token is stored in a Custom Label — plaintext, visible to anyone with access to the org's Setup UI and deployable to any sandbox without rotation.
- Token expiry is never handled: when the token rotates, every callout fails until a developer manually updates the Custom Label.
- The base URL must be in Remote Site Settings manually; Named Credentials handle this automatically.
- Hard-coding endpoint base URLs in Apex makes them environment-specific; Named Credentials can have different values per sandbox vs. production.

**Correct approach:**

```apex
// CORRECT: Named Credential handles endpoint, auth, and Remote Site Settings
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:AcmeCorpNC/v2/orders/' + orderId);
req.setMethod('GET');
req.setTimeout(30000);
// No setHeader for auth — the Named Credential custom header formula injects it
HttpResponse res = new Http().send(req);
```
