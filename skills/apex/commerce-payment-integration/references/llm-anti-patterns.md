# LLM Anti-Patterns — Commerce Payment Integration

Common mistakes AI coding assistants make when generating or advising on Commerce Payment Integration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Routing Raw Card Data Through Apex

**What the LLM generates:** An LWC component that collects card number, expiry, and CVV in input fields and posts them to an `@AuraEnabled` Apex method or Apex REST endpoint, which then passes the values to the gateway adapter or a direct HTTP callout.

**Why it happens:** LLMs trained on generic web payment integration examples (Node.js, Ruby on Rails, etc.) learn the pattern of server-side card collection followed by gateway tokenization. They apply this pattern to Apex without accounting for Salesforce's PCI isolation requirement.

**Correct pattern:**

```
1. Embed the payment provider's hosted iframe or payment.js library in the LWC.
2. The provider library captures card data entirely client-side in the cross-domain component.
3. The provider returns an opaque nonce or token to the parent LWC — no card data in JS variables.
4. The Commerce checkout passes this nonce to the platform, which calls processRequest with RequestType.Tokenize.
5. The Apex adapter exchanges the nonce for a durable gateway token via callout — never sees PAN/CVV.
```

**Detection hint:** Any Apex method with parameters named `cardNumber`, `cvv`, `expiryDate`, or `pan` is a definitive flag. Also watch for `httpReq.setBody('{"card_number":"' + ...)`.

---

## Anti-Pattern 2: Implementing sfdc_checkout.CartPaymentAuthorize for a Modern LWR Store

**What the LLM generates:** An Apex class `implements sfdc_checkout.CartPaymentAuthorize` with an `authorize` method, deployed as the payment adapter for a B2B Commerce or D2C Commerce store.

**Why it happens:** Many community posts, Trailhead modules, and older official docs describe `sfdc_checkout.CartPaymentAuthorize` as the payment adapter interface. LLMs trained on this content apply the older interface to modern LWR stores where it is never invoked.

**Correct pattern:**

```apex
// CORRECT for LWR-based B2B Commerce and all D2C Commerce stores
global class MyGatewayAdapter implements CommercePayments.PaymentGatewayAdapter {
    global CommercePayments.GatewayResponse processRequest(
            CommercePayments.PaymentGatewayContext context) {
        // dispatch on context.getPaymentRequestType()
    }
}

// LEGACY ONLY — only use for Aura-based B2B checkout
// global class MyAdapter implements sfdc_checkout.CartPaymentAuthorize { ... }
```

**Detection hint:** Presence of `implements sfdc_checkout.CartPaymentAuthorize` in a skill task scoped to a modern LWR store. Check the store type before generating adapter code.

---

## Anti-Pattern 3: Omitting the SalesforceResultCodes Mapping on Response Objects

**What the LLM generates:** An adapter that populates gateway-specific fields (`setGatewayReferenceNumber`, `setGatewayResultCode`) but does not call `setSalesforceResultCodeInfo` on the response object.

**Why it happens:** LLMs focus on the fields that map directly to gateway API response parameters. The `setSalesforceResultCodeInfo` call is a Salesforce-specific contract not present in any external gateway API, so it is frequently omitted when generating from gateway API docs alone.

**Correct pattern:**

```apex
CommercePayments.AuthorizationResponse resp =
    new CommercePayments.AuthorizationResponse();
resp.setGatewayReferenceNumber(txnId);
resp.setAmount(req.getAmount());
resp.setGatewayResultCode('00');
// REQUIRED — Commerce order management reads this to determine next state
resp.setSalesforceResultCodeInfo(
    CommercePayments.SalesforceResultCodes.Success);
return resp;
```

**Detection hint:** Any generated response object that lacks a call to `setSalesforceResultCodeInfo(...)` is missing required mapping.

---

## Anti-Pattern 4: Handling Only Authorization and Capture, Ignoring Other RequestTypes

**What the LLM generates:** A `processRequest` method with only `if (reqType == RequestType.Authorization)` and `else if (reqType == RequestType.Capture)` branches, with no handling for Tokenize, ReferencedRefund, PostAuthorization, or AuthorizationReversal. The else branch either returns null or throws an exception.

**Why it happens:** LLMs generate the most common happy-path scenario from training data. Authorization and capture are the most frequently documented steps. The full lifecycle (tokenization, reversals, refunds) is less prominent in tutorials and Q&A threads.

**Correct pattern:**

```apex
// All six branches must be handled:
if      (reqType == CommercePayments.RequestType.Tokenize)              { ... }
else if (reqType == CommercePayments.RequestType.Authorization)          { ... }
else if (reqType == CommercePayments.RequestType.PostAuthorization)      { ... }
else if (reqType == CommercePayments.RequestType.Capture)                { ... }
else if (reqType == CommercePayments.RequestType.ReferencedRefund)       { ... }
else if (reqType == CommercePayments.RequestType.AuthorizationReversal)  { ... }
else {
    CommercePayments.GatewayErrorResponse err =
        new CommercePayments.GatewayErrorResponse();
    err.setGatewayMessage('Unhandled RequestType: ' + reqType);
    return err;
}
```

**Detection hint:** Count the number of `RequestType` enum values handled. If fewer than six are present in `processRequest`, the adapter is incomplete.

---

## Anti-Pattern 5: Hardcoding Gateway API Credentials or Endpoints in Apex

**What the LLM generates:** Apex code with hardcoded strings for the gateway API endpoint, API key, or HMAC secret, such as `httpReq.setEndpoint('https://api.acmegateway.com/v2/charge')` and `httpReq.setHeader('Authorization', 'Bearer sk_live_abc123')`.

**Why it happens:** LLMs generate working code quickly by embedding values directly, mirroring patterns from online tutorials where credentials are shown inline for brevity. The Named Credential indirection is a Salesforce-specific abstraction not present in most payment integration examples.

**Correct pattern:**

```apex
// CORRECT — credentials stored in Named Credential, never in code
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:Acme_Gateway/charges'); // Named Credential name
req.setMethod('POST');
// Salesforce automatically injects the Authorization header from the
// Named Credential — no manual header construction needed

// WRONG — never do this:
// req.setEndpoint('https://api.acmegateway.com/v2/charges');
// req.setHeader('Authorization', 'Bearer sk_live_abc123');
```

**Detection hint:** Any literal `https://` URL in `setEndpoint` or any `setHeader('Authorization', ...)` with an inline credential value in payment adapter code is a flag. Endpoints must use the `callout:<NamedCredentialName>` scheme.

---

## Anti-Pattern 6: Using CommercePayments Adapter for Salesforce Billing Scenarios

**What the LLM generates:** An adapter implementing `CommercePayments.PaymentGatewayAdapter` to handle invoice payment, subscription billing, or the `blng` namespace payment lifecycle.

**Why it happens:** Both `CommercePayments` and `blng` (Salesforce Billing) deal with payments. LLMs conflate the two namespaces when a request mentions "Salesforce payment gateway." The `CommercePayments` namespace is scoped exclusively to B2B Commerce and D2C Commerce checkout; Salesforce Billing uses the `blng.PaymentGateway` interface.

**Correct pattern:**

```
For Salesforce Commerce (B2B/D2C) checkout payments:
  → Use CommercePayments.PaymentGatewayAdapter (this skill)

For Salesforce Billing invoice payments, subscription renewals, or blng.InvoiceAPI:
  → Use blng.PaymentGateway interface (see apex/billing-integration-apex skill)

These are separate products with separate extension point interfaces.
Do not mix the namespaces.
```

**Detection hint:** If the request mentions "invoices", "subscriptions", "billing", or `blng` namespace, route to `apex/billing-integration-apex` instead of this skill.
