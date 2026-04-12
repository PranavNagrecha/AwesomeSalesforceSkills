# Examples — Commerce Order API (SCAPI / OCAPI Headless Storefront)

## Example 1: Guest Shopper Order Submission via SCAPI with SLAS Authentication

**Context:** A React-based headless storefront needs to allow guest shoppers to check out and place an order without requiring account creation. The storefront uses SCAPI exclusively (no OCAPI). The shopper has already added products to a basket.

**Problem:** The developer attempts to call `POST /checkout/shopper-orders/v1/.../orders` but receives a 401 Unauthorized. They check the bearer token and it appears valid. The underlying cause is that the SLAS public client was configured without the `sfcc.shopper-baskets-orders` scope — SLAS grants the token regardless of scope configuration, but the Commerce API enforces scope at request time. The error body contains `{"type":"https://api.commercecloud.salesforce.com/documentation/error/v1/errors/invalid-scope"}` but this is easy to miss in JSON response logging.

**Solution:**

Step 1 — Obtain a SLAS guest token (JavaScript fetch, run server-side or via a BFF):
```javascript
const slasResponse = await fetch(
  `https://${shortCode}.api.commercecloud.salesforce.com/shopper/auth/v1/organizations/${organizationId}/oauth2/guest/token`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'client_credentials',
      client_id: PUBLIC_SLAS_CLIENT_ID,
    }),
  }
);
const { access_token: guestToken } = await slasResponse.json();
```

Step 2 — Verify basket is complete, then submit:
```javascript
const orderResponse = await fetch(
  `https://${shortCode}.api.commercecloud.salesforce.com/checkout/shopper-orders/v1/organizations/${organizationId}/orders`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${guestToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ basketId: currentBasketId }),
  }
);

if (!orderResponse.ok) {
  // Do NOT retry immediately — check if order was created first
  const errorBody = await orderResponse.json();
  throw new Error(`Order submission failed: ${errorBody.type}`);
}

const order = await orderResponse.json();
// order.orderNo is the only future reference for this guest shopper
storeOrderNo(order.orderNo, shopperEmail);
```

**Why it works:** SLAS guest tokens carry the `sfcc.shopper-baskets-orders` scope (after correct client configuration), which is the exact scope the ShopAPI Orders endpoint validates. The `basketId` in the request body points to the shopper's active basket; the platform reads all line item, shipping, and payment data from the basket and atomically deletes it upon successful order creation. Storing `orderNo` paired with email is critical because guest shoppers have no session-based order history.

---

## Example 2: Registered Shopper Order History with SLAS PKCE Flow

**Context:** A headless My Account page needs to display the last 10 orders for a logged-in registered shopper. The storefront runs PKCE for registered authentication.

**Problem:** The developer has a working guest token flow for checkout but re-uses the guest token for the `GET /orders` call on the My Account page. The API returns 403 Forbidden. The error type is `https://api.commercecloud.salesforce.com/documentation/error/v1/errors/insufficient-scope`. The developer incorrectly concludes the SLAS client is misconfigured and files a support case, but the real issue is that order history retrieval requires a registered (non-guest) token with `sfcc.shopper-myaccount.order` scope.

**Solution:**

Step 1 — Complete PKCE flow to get a registered shopper token:
```javascript
// After user logs in via SLAS PKCE redirect, exchange the auth code:
const tokenResponse = await fetch(
  `https://${shortCode}.api.commercecloud.salesforce.com/shopper/auth/v1/organizations/${organizationId}/oauth2/token`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      code: authorizationCode,
      code_verifier: pkceVerifier,
      client_id: PUBLIC_SLAS_CLIENT_ID,
      redirect_uri: REDIRECT_URI,
    }),
  }
);
const { access_token: registeredToken, refresh_token } = await tokenResponse.json();
// Store refresh_token securely (httpOnly cookie recommended)
```

Step 2 — Retrieve order history with pagination:
```javascript
const ordersResponse = await fetch(
  `https://${shortCode}.api.commercecloud.salesforce.com/checkout/shopper-orders/v1/organizations/${organizationId}/orders?offset=0&limit=10`,
  {
    headers: { 'Authorization': `Bearer ${registeredToken}` },
  }
);
const { data: orders, total, offset, limit } = await ordersResponse.json();
// Render orders; use total/limit/offset for pagination controls
```

Step 3 — Implement token refresh before expiry:
```javascript
// Check token expiry before each API call; default TTL is 1800s (30 min)
if (isTokenExpiredOrNearExpiry(registeredToken)) {
  const refreshed = await refreshSLASToken(refresh_token, organizationId, shortCode);
  registeredToken = refreshed.access_token;
}
```

**Why it works:** Registered SLAS tokens embed the shopper's `customer_id` in the JWT payload. The SCAPI Orders `GET /orders` endpoint validates the token's `sub` claim and only returns orders belonging to that shopper. The `sfcc.shopper-myaccount.order` scope enables this cross-resource access. Guest tokens intentionally lack a persistent identity anchor and therefore cannot access account-scoped resources.

---

## Example 3: Apex Callout to Read B2C Commerce Order into Salesforce Core (Trusted Agent Flow)

**Context:** A Salesforce Service Cloud org with an integrated B2C Commerce storefront needs to display recent B2C orders in a Service Console component. OMS is not implemented. The team wants an Apex callout to SCAPI using server-side credentials.

**Problem:** The developer initially uses an OCAPI client ID and hardcodes it as a String constant in an Apex utility class. When the OCAPI client is rotated in Business Manager (standard security practice), all callouts break. The credential is also visible to any developer with access to the org's Apex code.

**Solution:**

Configure a Named Credential in Salesforce for the SLAS Trusted Agent endpoint:
- Auth Protocol: No Authentication (token is managed manually) or JWT Bearer Token flow
- URL: `https://{shortCode}.api.commercecloud.salesforce.com`

Apex callout with token retrieval:
```apex
public class B2COrderService {

    // Token stored in Platform Cache (Org partition) — not in a text field
    private static final String CACHE_KEY = 'local.SCAPI.AccessToken';

    public static Map<String, Object> getOrder(String orderNo) {
        String token = getOrRefreshToken();

        HttpRequest req = new HttpRequest();
        req.setEndpoint(
            'callout:B2CCommerce/checkout/shopper-orders/v1/organizations/'
            + getOrgId() + '/orders/' + EncodingUtil.urlEncode(orderNo, 'UTF-8')
        );
        req.setMethod('GET');
        req.setHeader('Authorization', 'Bearer ' + token);
        req.setTimeout(10000);

        HttpResponse res = new Http().send(req);

        if (res.getStatusCode() == 401) {
            // Token expired — clear cache and retry once
            Cache.Org.remove(CACHE_KEY);
            token = getOrRefreshToken();
            req.setHeader('Authorization', 'Bearer ' + token);
            res = new Http().send(req);
        }

        if (res.getStatusCode() != 200) {
            throw new CalloutException('B2C order fetch failed: ' + res.getStatus());
        }

        return (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
    }

    private static String getOrRefreshToken() {
        String cached = (String) Cache.Org.get(CACHE_KEY);
        if (cached != null) return cached;

        // Obtain token via SLAS private client credentials
        HttpRequest tokenReq = new HttpRequest();
        tokenReq.setEndpoint('callout:SLAS_TrustedAgent/oauth2/token');
        tokenReq.setMethod('POST');
        tokenReq.setHeader('Content-Type', 'application/x-www-form-urlencoded');
        tokenReq.setBody(
            'grant_type=client_credentials'
            + '&client_id=' + getSLASClientId()
            + '&client_secret=' + getSLASClientSecret()
        );
        HttpResponse tokenRes = new Http().send(tokenReq);
        Map<String, Object> tokenData = (Map<String, Object>) JSON.deserializeUntyped(tokenRes.getBody());
        String newToken = (String) tokenData.get('access_token');
        Integer expiresIn = (Integer) tokenData.get('expires_in');
        // Cache for slightly less than TTL to avoid racing expiry
        Cache.Org.put(CACHE_KEY, newToken, expiresIn - 60);
        return newToken;
    }

    private static String getOrgId() {
        return (String) Commerce_API_Settings__mdt.getInstance('Default').Organization_Id__c;
    }
    private static String getSLASClientId() {
        return (String) Commerce_API_Settings__mdt.getInstance('Default').SLAS_Client_Id__c;
    }
    private static String getSLASClientSecret() {
        // Retrieve from Named Credential or Protected Custom Metadata
        return (String) Commerce_API_Settings__mdt.getInstance('Default').SLAS_Client_Secret__c;
    }
}
```

**Why it works:** Named Credentials abstract the SCAPI base URL from Apex source code and support IP whitelisting at the org level. Platform Cache holds the SLAS token across transactions without persisting it to a visible SObject field. The single retry on 401 handles token expiry gracefully without an unbounded retry loop. SLAS private client credentials (used in Trusted Agent flow) are not browser-exposed, making this pattern safe for server-side Apex.

---

## Anti-Pattern: Retrying POST /orders After a Network Timeout Without Deduplication

**What practitioners do:** After a `POST /orders` network timeout, the storefront immediately retries the same `basketId`. If the first request succeeded, the basket is already deleted and the retry returns 404 (basket not found). The developer assumes the first request failed and shows an error to the shopper — but the order was actually created.

**What goes wrong:** The shopper is shown an error message and encouraged to re-enter payment, potentially re-attempting checkout with a new basket while an order already exists. In the worst case, the shopper is double-charged.

**Correct approach:** Before retrying, call `GET /checkout/shopper-orders/v1/.../orders` with the registered token (or implement a backend order-lookup by basket correlation ID) to confirm whether an order was created. Only retry submission if no order exists. Show a "Checking your order status..." loading state during this verification window rather than an immediate error.
