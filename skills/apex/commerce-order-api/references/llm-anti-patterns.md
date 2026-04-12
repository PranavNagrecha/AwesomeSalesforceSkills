# LLM Anti-Patterns — Commerce Order API (SCAPI / OCAPI Headless Storefront)

Common mistakes AI coding assistants make when generating or advising on B2C Commerce SCAPI/OCAPI order submission from headless storefronts. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating OMS Connect API Actions with SCAPI ShopAPI Orders

**What the LLM generates:** Code or advice that tells the practitioner to call `ensure-funds-async`, `submit-cancel`, or `submit-return` as part of the storefront order submission flow — framed as "completing the order through the Commerce API."

**Why it happens:** Training data conflates Salesforce B2C Commerce SCAPI with Salesforce Order Management (OMS) Connect API because both are described as "Commerce" APIs and both deal with orders. The LLM merges the two layers into a single conceptual model.

**Correct pattern:**
```
SCAPI ShopAPI Orders layer (storefront-facing):
  POST /checkout/shopper-orders/v1/.../orders  → Creates the order from basket
  GET  /checkout/shopper-orders/v1/.../orders  → Retrieves order history
  GET  /checkout/shopper-orders/v1/.../orders/{orderNo} → Retrieves single order

OMS Connect API layer (post-submission, fulfillment-facing — NOT SCAPI):
  POST /services/data/v{ver}/commerce/order-management/orders/{id}/actions/submit-cancel
  POST /services/data/v{ver}/commerce/order-management/orders/{id}/actions/submit-return
  POST /services/data/v{ver}/commerce/order-management/orders/{id}/actions/ensure-funds-async
```

SCAPI order submission does not call ensure-funds or submit-cancel. Those are OMS Connect API actions that operate on the OMS OrderSummary after the order is ingested. Do not mix these layers in the same integration code.

**Detection hint:** If the generated code includes `ensure-funds-async` or `submit-cancel` alongside a `POST /orders` SCAPI call, flag it as a layer conflation error.

---

## Anti-Pattern 2: Missing SLAS Authentication — Using OCAPI Client ID for SCAPI Calls

**What the LLM generates:** Advice to "use the OCAPI client ID and HMAC authentication" for SCAPI order API calls, or code that sets an `x-dw-client-id` header on a SCAPI endpoint URL.

**Why it happens:** OCAPI and SCAPI share a similar URL space (`{shortCode}.api.commercecloud.salesforce.com` vs older OCAPI paths) and both involve a "client ID." LLMs trained on older B2C Commerce documentation default to OCAPI authentication patterns and apply them to SCAPI.

**Correct pattern:**
```javascript
// WRONG — OCAPI auth on a SCAPI endpoint:
headers: { 'x-dw-client-id': 'your-ocapi-client-id' }  // Not valid for SCAPI

// CORRECT — SLAS Bearer token for SCAPI:
const { access_token } = await getSLASToken(); // SLAS guest or registered token
headers: { 'Authorization': `Bearer ${access_token}` }  // Required for SCAPI
```

SCAPI requires a SLAS-issued Bearer token in the `Authorization` header. The `x-dw-client-id` header is an OCAPI-specific mechanism. Do not use OCAPI client IDs directly with SCAPI endpoints.

**Detection hint:** If generated SCAPI code includes `x-dw-client-id` header or references HMAC authentication, flag it as an incorrect auth pattern for SCAPI.

---

## Anti-Pattern 3: Direct DML on OrderItemSummary After SCAPI Order Ingestion into OMS (MANAGED Mode)

**What the LLM generates:** Apex code that runs `update orderItemSummaryRecord` or sets `QuantityCanceled` directly on an `OrderItemSummary` record to handle a post-submission change request, framed as "updating the order quantity in Salesforce."

**Why it happens:** LLMs know that Salesforce data can generally be modified via DML and generate the simplest possible Apex mutation. They do not distinguish between MANAGED and UNMANAGED OrderLifeCycleType, and they do not know that MANAGED mode enforces Connect API exclusivity for mutations.

**Correct pattern:**
```apex
// WRONG — direct DML on OrderItemSummary in MANAGED mode:
OrderItemSummary ois = [SELECT Id FROM OrderItemSummary WHERE Id = :itemId];
ois.QuantityCanceled = 1.0;
update ois; // Silently corrupts TotalAdjustedProductAmount in MANAGED mode

// CORRECT — use OMS Connect API action submit-cancel:
ConnectApi.OrderSummaryInputRepresentation input = new ConnectApi.OrderSummaryInputRepresentation();
ConnectApi.CancelOrderItemSummaryInputRepresentation cancelItem =
    new ConnectApi.CancelOrderItemSummaryInputRepresentation();
cancelItem.orderItemSummaryId = itemId;
cancelItem.quantity = 1.0;
input.orderItemSummaryInputs = new List<ConnectApi.CancelOrderItemSummaryInputRepresentation>{ cancelItem };
ConnectApi.OrderSummary.submitCancel(orderSummaryId, input);
```

**Detection hint:** If generated code includes `update` DML on `OrderItemSummary`, `QuantityCanceled`, or `QuantityReturnInitiated` fields without going through a ConnectApi method, flag it as a MANAGED-mode integrity violation.

---

## Anti-Pattern 4: Retrying POST /orders Without Order Existence Check

**What the LLM generates:** Code that wraps `POST /orders` in a retry loop with exponential backoff, treating a network timeout as equivalent to a failed request and retrying automatically.

**Why it happens:** Retry-on-failure with backoff is a standard API resilience pattern that LLMs apply broadly. LLMs do not know that `POST /orders` is non-idempotent and that the basket is destroyed on success, making a blind retry potentially create a duplicate order and definitely fail with a 404 if the basket is gone.

**Correct pattern:**
```javascript
// WRONG — blind retry:
for (let attempt = 0; attempt < 3; attempt++) {
  try {
    const order = await scapiClient.post('/orders', { basketId });
    return order;
  } catch (err) {
    await sleep(1000 * attempt); // Retry may create duplicate order
  }
}

// CORRECT — check-before-retry:
async function submitOrderSafely(basketId, registeredToken) {
  try {
    return await scapiClient.post('/orders', { basketId });
  } catch (err) {
    if (isNetworkTimeout(err)) {
      // Do NOT retry immediately — check if order was created
      const existing = await findOrderByCorrelationId(basketId, registeredToken);
      if (existing) return existing; // First call succeeded
      // Only retry if confirmed no order exists
      return await scapiClient.post('/orders', { basketId });
    }
    throw err;
  }
}
```

**Detection hint:** If generated code includes a retry loop around `POST /orders` without a `GET /orders` existence check in the retry path, flag it as a non-idempotent retry risk.

---

## Anti-Pattern 5: Storing SLAS Tokens in Browser localStorage

**What the LLM generates:** JavaScript code that persists the SLAS access token in `localStorage` (e.g., `localStorage.setItem('slas_token', token)`) for reuse across page navigations.

**Why it happens:** `localStorage` is the most commonly recommended browser persistence mechanism in JavaScript training data. LLMs do not differentiate between storing non-sensitive state (UI preferences) and authentication tokens with serious security implications.

**Correct pattern:**
```javascript
// WRONG — token in localStorage:
localStorage.setItem('slas_access_token', token.access_token);
// Any third-party script, browser extension, or XSS payload can read this

// CORRECT — httpOnly cookie set by BFF server:
// Server-side (BFF):
res.cookie('slas_token', token.access_token, {
  httpOnly: true,   // Not accessible to JavaScript
  secure: true,     // HTTPS only
  sameSite: 'Strict',
  maxAge: token.expires_in * 1000,
});

// OR — in-memory only (no persistence across page reloads):
let slasToken = null; // Module-scoped, not in any browser storage
```

**Detection hint:** If generated code contains `localStorage.setItem` with a token, `sessionStorage.setItem` with a token, or `document.cookie` assignment without `httpOnly`, flag it as insecure token storage.

---

## Anti-Pattern 6: Using OCAPI Authentication Configuration for New SCAPI Integrations

**What the LLM generates:** Advice to configure OCAPI Client settings in Business Manager (Administration > Site Development > OCAPI Settings) and use an OCAPI client ID as the primary credential for a new headless integration being built on SCAPI endpoints.

**Why it happens:** OCAPI was the dominant B2C Commerce API for many years and appears in more training data than SCAPI. LLMs default to OCAPI configuration steps when the user asks about "setting up Commerce API credentials" without specifying SCAPI.

**Correct pattern:**
```
New SCAPI integration credential setup:
1. Configure SLAS client in Account Manager (not Business Manager OCAPI settings)
   - Set client type: public (for PKCE browser flow) or private (for server-side)
   - Add scopes: sfcc.shopper-baskets-orders, sfcc.shopper-myaccount.order
   - Set allowed redirect URIs for public clients
2. Retrieve organizationId and shortCode from Business Manager:
   Administration > Salesforce Commerce API Settings
3. Test token issuance:
   POST https://{shortCode}.api.commercecloud.salesforce.com/shopper/auth/v1/...
```

OCAPI settings in Business Manager are only relevant if you are also running OCAPI-specific resources. For a pure SCAPI integration, Business Manager OCAPI settings are not involved.

**Detection hint:** If the LLM's configuration steps reference Business Manager > Administration > Site Development > OCAPI Settings for a new SCAPI-only integration, flag it as an incorrect configuration target.
