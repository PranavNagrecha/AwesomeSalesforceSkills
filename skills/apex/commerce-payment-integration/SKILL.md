---
name: commerce-payment-integration
description: "Use this skill when building or debugging a custom Salesforce Commerce payment gateway adapter using the CommercePayments Apex namespace — covering adapter implementation, RequestType handling, PCI tokenization patterns, and integration path selection. NOT for billing (Salesforce Billing / blng namespace), NOT for configuring the legacy sfdc_checkout.CartPaymentAuthorize interface (see admin/commerce-checkout-configuration), and NOT for storefront UI payment form design."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "How do I build a custom payment gateway adapter for Salesforce B2B or D2C Commerce?"
  - "My CommercePayments processRequest method is not being called during checkout"
  - "I need to handle tokenization, authorization, and capture separately in a Commerce payment flow"
  - "Which RequestType values must my payment gateway adapter implement?"
  - "How do I keep raw card data out of Apex when integrating a payment gateway with Salesforce Commerce?"
tags:
  - commerce-payment-integration
  - CommercePayments
  - payment-gateway-adapter
  - PCI-compliance
  - tokenization
  - B2B-commerce
  - D2C-commerce
  - apex
inputs:
  - "Target store type (B2B or D2C Commerce)"
  - "Payment gateway vendor name and available API documentation"
  - "Which integration path is in scope: Salesforce Payments (Stripe), AppExchange package, or custom CommercePayments adapter"
  - "Whether Apple Pay or other digital wallets are required"
  - "Org API version (must be v55.0+ for CommercePayments namespace)"
outputs:
  - "Apex class implementing CommercePayments.PaymentGatewayAdapter with all required RequestType branches"
  - "Named Credential configuration for secure gateway API callout"
  - "Payment Gateway Provider custom metadata record wiring the adapter to the store"
  - "Test class exercising each RequestType with mock callout responses"
  - "Recommended Workflow checklist covering PCI isolation and governor limit risk points"
dependencies:
  - admin/commerce-checkout-configuration
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Commerce Payment Integration

This skill activates when a practitioner needs to write or debug Apex code that connects a Salesforce B2B or D2C Commerce store to a payment gateway using the `CommercePayments` Apex namespace. It covers the full adapter lifecycle from tokenization through capture and refund, PCI isolation patterns, and the decision between the three supported integration paths.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org API version is v55.0 or higher — the `CommercePayments` namespace was introduced in that release.
- Identify which integration path applies: Salesforce Payments (native Stripe, no custom Apex required), a vetted AppExchange payment package, or a fully custom `CommercePayments` Apex adapter. Custom Apex is only necessary when neither of the first two paths supports the target gateway.
- Verify the store is a B2B Commerce or D2C Commerce store — not a legacy B2B store (Aura-based) which uses a different checkout model.
- Confirm whether digital wallets (Apple Pay, Google Pay) are required. Only Salesforce Payments (Stripe path) natively supports Apple Pay; custom adapters must handle wallet tokenization explicitly.
- Check whether the existing checkout configuration uses `sfdc_checkout.CartPaymentAuthorize` — if so, that is the legacy admin-configured path covered by `admin/commerce-checkout-configuration`, not this skill.

---

## Core Concepts

### The CommercePayments Namespace and Gateway Adapter Contract

The `CommercePayments` Apex namespace provides the interfaces, request/response types, and enums that form the contract between Salesforce Commerce checkout and a payment gateway. Every custom gateway adapter must implement `CommercePayments.PaymentGatewayAdapter` and its single entry point: `processRequest(CommercePayments.PaymentGatewayContext context)`. The platform calls this method at every payment lifecycle stage; the adapter inspects `context.getPaymentRequestType()` to determine which operation to perform and returns a concrete subtype of `CommercePayments.GatewayResponse`.

The six `RequestType` values the platform can pass are:

| RequestType | When called | Expected response type |
|---|---|---|
| `Tokenize` | Client-side payment capture complete; platform requests a gateway token | `GatewayTokenizeResponse` |
| `Authorization` | Reserve funds at time of order placement | `AuthorizationResponse` |
| `PostAuthorization` | Called after a successful authorization (optional lifecycle hook) | `PostAuthorizationResponse` |
| `Capture` | Settle previously authorized funds | `CaptureResponse` |
| `ReferencedRefund` | Issue a refund against a prior transaction | `ReferencedRefundResponse` |
| `AuthorizationReversal` | Release a prior authorization without capturing | `AuthorizationReversalResponse` |

An adapter that does not handle all six will throw an unhandled branch at runtime for any request type the store triggers. At minimum, `Tokenize`, `Authorization`, and `Capture` must be implemented for a functional checkout.

### PCI Compliance Through Cross-Domain Tokenization

The most critical architectural constraint is that raw card data — card numbers (PAN), CVV, and expiry — must never pass through Salesforce servers. The Commerce payment framework enforces this by delegating card capture entirely to a cross-domain client-side component (an iframe or redirect) owned and hosted by the payment provider. The provider's JavaScript captures the card details directly and returns a gateway-specific payment method token or nonce. The Apex adapter receives only this opaque token reference — it never sees card data. This is the platform-enforced PCI DSS scope reduction mechanism.

Any design that routes raw card data through Apex — even transiently — violates PCI DSS and breaks the tokenization contract. Named Credentials must be used for gateway API credentials; they must never be stored in Custom Settings or hardcoded.

### Three Integration Paths

**Path 1 — Salesforce Payments (Stripe)**: Enabled through Store Setup with no custom Apex. Supports Stripe payment methods including cards and Apple Pay. Requires a Salesforce Payments account. Lowest engineering effort; least flexibility.

**Path 2 — AppExchange Payment Package**: A vetted third-party package that ships a pre-built `CommercePayments` adapter for a specific gateway (e.g., Adyen, Braintree, CyberSource). The adapter code is managed and upgraded by the ISV. Appropriate when the target gateway has a published package.

**Path 3 — Custom CommercePayments Apex Adapter**: Required only when no AppExchange package covers the target gateway, or when bespoke authorization logic is needed. The developer authors and maintains the full adapter class. This is the path this skill covers in detail.

---

## Common Patterns

### Pattern: Full Lifecycle Adapter with Named Credential Callout

**When to use:** A custom gateway requires supporting Tokenize, Authorization, Capture, ReferencedRefund, and AuthorizationReversal.

**How it works:**

```apex
global class AcmeGatewayAdapter implements CommercePayments.PaymentGatewayAdapter {

    global CommercePayments.GatewayResponse processRequest(
            CommercePayments.PaymentGatewayContext context) {

        CommercePayments.RequestType reqType = context.getPaymentRequestType();

        if (reqType == CommercePayments.RequestType.Tokenize) {
            return handleTokenize(
                (CommercePayments.PaymentMethodTokenizationRequest) context.getPaymentRequest());
        } else if (reqType == CommercePayments.RequestType.Authorization) {
            return handleAuthorization(
                (CommercePayments.AuthorizationRequest) context.getPaymentRequest());
        } else if (reqType == CommercePayments.RequestType.Capture) {
            return handleCapture(
                (CommercePayments.CaptureRequest) context.getPaymentRequest());
        } else if (reqType == CommercePayments.RequestType.ReferencedRefund) {
            return handleRefund(
                (CommercePayments.ReferencedRefundRequest) context.getPaymentRequest());
        } else if (reqType == CommercePayments.RequestType.AuthorizationReversal) {
            return handleReversal(
                (CommercePayments.AuthorizationReversalRequest) context.getPaymentRequest());
        } else if (reqType == CommercePayments.RequestType.PostAuthorization) {
            return handlePostAuth(
                (CommercePayments.PostAuthorizationRequest) context.getPaymentRequest());
        }
        // Explicit fallback — should never be reached if all types are handled
        CommercePayments.GatewayErrorResponse errResp =
            new CommercePayments.GatewayErrorResponse();
        errResp.setGatewayMessage('Unsupported request type: ' + reqType);
        return errResp;
    }

    private CommercePayments.GatewayResponse handleAuthorization(
            CommercePayments.AuthorizationRequest req) {
        // Callout uses Named Credential — no hardcoded secrets
        HttpRequest httpReq = new HttpRequest();
        httpReq.setEndpoint('callout:Acme_Gateway/authorize');
        httpReq.setMethod('POST');
        // ... build request body, call gateway, parse response ...
        CommercePayments.AuthorizationResponse resp =
            new CommercePayments.AuthorizationResponse();
        resp.setGatewayReferenceNumber('acme-txn-12345');
        resp.setAmount(req.getAmount());
        resp.setGatewayResultCode('00');
        resp.setSalesforceResultCodeInfo(
            CommercePayments.SalesforceResultCodes.Success);
        return resp;
    }
    // ... remaining handler methods
}
```

**Why not the alternative:** Using a single method without dispatching on `RequestType` means the adapter returns an incorrect response type for lifecycle steps other than the one it was built for, causing silent checkout failures.

### Pattern: Payment Gateway Provider Registration via Custom Metadata

**When to use:** Wiring a custom adapter class to a specific Commerce store so the platform knows which Apex class to invoke.

**How it works:** Create a `Payment Gateway Provider` record (via Setup > Payment Gateway Providers) that points to the Apex adapter class. Then in the store's Payment Settings, select the registered provider. The platform reads this metadata at checkout time to determine which class to instantiate. This registration is done in Setup UI or deployed as a `PaymentGatewayProvider` metadata type in a SFDX/source-format project — it is not configured in Apex code itself.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Gateway is Stripe and Apple Pay support required | Salesforce Payments (Path 1) | Only native path with Apple Pay; no custom Apex needed |
| Gateway has a published AppExchange Commerce package | AppExchange Package (Path 2) | ISV maintains adapter; faster time-to-value |
| Gateway has no AppExchange package or bespoke auth logic needed | Custom CommercePayments Apex Adapter (Path 3) | Full control; this skill's primary scope |
| Legacy B2B (Aura) store or admin-only payment setup needed | sfdc_checkout.CartPaymentAuthorize (see admin/commerce-checkout-configuration) | Different interface; out of scope for this skill |
| Salesforce Billing / subscription invoicing | blng namespace (see apex/billing-integration-apex) | Separate product; CommercePayments namespace does not apply |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm integration path** — Determine whether Salesforce Payments, an AppExchange package, or a custom adapter is required. Only proceed with Apex authoring if neither of the first two paths is viable. Document the chosen path and rationale.
2. **Scaffold the adapter class** — Create an Apex class with `global` access that implements `CommercePayments.PaymentGatewayAdapter`. Add a `processRequest` method with dispatch logic covering all six `RequestType` values. Stub each handler method to return a typed error response before adding real callout logic.
3. **Configure the Named Credential** — Create a Named Credential for the gateway API endpoint and credentials. Ensure the adapter's callout endpoint references `callout:<NamedCredentialName>/...` — never hardcode URLs or secrets.
4. **Implement each handler method** — For each `RequestType`, implement the callout, parse the gateway response, and populate the corresponding `CommercePayments` response object. Map gateway result codes to `SalesforceResultCodes` enum values (Success, Decline, SystemError, etc.).
5. **Register the adapter** — Create a Payment Gateway Provider record in Setup that references the Apex class name. In the store's Payment Settings, select the registered provider.
6. **Write test coverage** — Create a test class that uses `Test.setMock(HttpCalloutMock.class, ...)` to mock the gateway API. Test each `RequestType` branch. Minimum 75% coverage required; aim for 90%+. Verify that no test directly passes raw card data through Apex.
7. **Validate PCI posture and run a full checkout** — Confirm the cross-domain client component (provider-hosted iframe or redirect) handles card capture. Walk through a test order end-to-end: tokenize, authorize, capture, refund. Verify all lifecycle transitions succeed and that error paths return `GatewayErrorResponse` rather than throwing exceptions.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Adapter implements all six `RequestType` branches (Tokenize, Authorization, PostAuthorization, Capture, ReferencedRefund, AuthorizationReversal)
- [ ] No raw card data (PAN, CVV, expiry) appears anywhere in Apex code, debug logs, or Custom Settings
- [ ] All gateway credentials are stored in Named Credentials — no hardcoded endpoints or API keys
- [ ] Every handler returns the correct typed `CommercePayments` response subclass (not a generic object or exception throw)
- [ ] Test class achieves 90%+ coverage and mocks all HTTP callouts via `HttpCalloutMock`
- [ ] Payment Gateway Provider metadata record is created and linked to the store
- [ ] End-to-end test order completes successfully through tokenize → authorize → capture

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **CommercePayments vs sfdc_checkout.CartPaymentAuthorize are separate interfaces** — The `CommercePayments.PaymentGatewayAdapter` interface (used in LWR-based B2B/D2C stores, introduced ~v55.0) and `sfdc_checkout.CartPaymentAuthorize` (older Aura-based B2B checkout) are completely different extension points. Implementing `CartPaymentAuthorize` in a modern LWR store will not be invoked by the platform. Consult `admin/commerce-checkout-configuration` if you are on the older interface.
2. **Missing RequestType branches cause silent checkout failures** — The platform does not throw an obvious error if `processRequest` returns `null` or an incorrectly typed response for a given `RequestType`. Instead, checkout silently stalls or shows a generic error. Every branch must return a correctly typed response object even if the handler is not yet implemented.
3. **Apple Pay requires Salesforce Payments — custom adapters cannot support it natively** — Apple Pay domain verification and session handling are managed entirely by Stripe/Salesforce Payments infrastructure. A custom `CommercePayments` adapter cannot implement Apple Pay without significant complexity outside the adapter interface. Communicate this limitation early.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `AcmeGatewayAdapter.cls` | Apex class implementing `CommercePayments.PaymentGatewayAdapter` with all six RequestType branches |
| `AcmeGatewayAdapterTest.cls` | Test class with `HttpCalloutMock` implementations for each gateway response scenario |
| `Named Credential` | Secure credential store for gateway API endpoint and authentication |
| `Payment Gateway Provider record` | Setup record linking the adapter class to the Commerce platform |
| Workflow checklist | Completed checklist confirming PCI isolation, test coverage, and end-to-end validation |

---

## Related Skills

- `admin/commerce-checkout-configuration` — for legacy `sfdc_checkout.CartPaymentAuthorize` pattern and store checkout setup; also covers the admin steps for registering a gateway provider
- `apex/billing-integration-apex` — for Salesforce Billing (blng namespace) invoicing and payment scenarios, which are entirely separate from Commerce payment adapters
- `apex/callouts-and-http-integrations` — for Named Credential setup, callout patterns, and HTTP mock testing in Apex
- `apex/apex-security-patterns` — for securing callout credentials and avoiding injection vulnerabilities in payment-related Apex
