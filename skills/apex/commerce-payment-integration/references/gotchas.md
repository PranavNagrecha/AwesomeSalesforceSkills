# Gotchas — Commerce Payment Integration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: CommercePayments.PaymentGatewayAdapter and sfdc_checkout.CartPaymentAuthorize Are Unrelated Interfaces

**What happens:** A developer implementing a payment adapter for a modern LWR-based B2B or D2C Commerce store implements `sfdc_checkout.CartPaymentAuthorize` instead of `CommercePayments.PaymentGatewayAdapter`. The class compiles and deploys without error. At checkout time, the platform never invokes it, because LWR-based stores use the `CommercePayments` namespace exclusively — `sfdc_checkout.CartPaymentAuthorize` is only invoked in legacy Aura-based B2B checkout flows. The store silently fails payment authorization with no obvious stack trace pointing to the wrong interface.

**When it occurs:** Any time a developer searches for "Salesforce Commerce payment adapter Apex" and finds legacy B2B documentation or community posts that predate the `CommercePayments` namespace introduction (~API v55.0, Spring '22). The older interface still compiles and its documentation still exists, so it is easy to conflate the two.

**How to avoid:** Confirm the store type before writing any adapter code. LWR-based B2B Commerce and all D2C Commerce stores require `CommercePayments.PaymentGatewayAdapter`. Only use `sfdc_checkout.CartPaymentAuthorize` for legacy Aura B2B stores (see `admin/commerce-checkout-configuration`). Check the class declaration: `implements CommercePayments.PaymentGatewayAdapter` is the correct signature for modern stores.

---

## Gotcha 2: An Unhandled RequestType Returns Null and Stalls Checkout Silently

**What happens:** An adapter that handles only `Authorization` and `Capture` in its `processRequest` dispatch logic returns `null` (or falls through to no return statement) when the platform sends a `Tokenize`, `ReferencedRefund`, or `AuthorizationReversal` request. The platform does not throw a descriptive error — instead, checkout freezes at the payment step, the order is not placed, and the error logged is a generic system error with no indication of the missing branch.

**When it occurs:** This most commonly surfaces when a team builds and tests only the happy-path authorization and capture flow, then deploys. The first time a buyer attempts a refund or the store triggers tokenization, the missing branch manifests in production.

**How to avoid:** Always implement all six `RequestType` branches in `processRequest`. For branches not yet fully implemented, return a typed `GatewayErrorResponse` with a descriptive `setGatewayMessage` value rather than leaving them unimplemented. Cover every branch in the test class, including Tokenize, PostAuthorization, ReferencedRefund, and AuthorizationReversal, even if some currently return stub error responses.

---

## Gotcha 3: Apple Pay Cannot Be Supported by a Custom CommercePayments Adapter Without Significant Out-of-Platform Work

**What happens:** A merchant requests Apple Pay support on their custom-gateway Commerce store. A developer assumes that adding Apple Pay handling to the `Tokenize` branch of a custom adapter is sufficient. In practice, Apple Pay requires domain verification (an Apple Pay merchant identity certificate served from the store's domain), a merchant session validation API call, and integration with the Apple Pay JS API — none of which are handled by the `CommercePayments` adapter interface. Attempting to build this within a custom adapter requires a separate Apex endpoint, a Named Credential to Apple's session validation URL, and custom LWC code — a multi-sprint effort.

**When it occurs:** Any time a merchant migrates from Stripe/Salesforce Payments (where Apple Pay is native) to a custom gateway and assumes feature parity.

**How to avoid:** Communicate at project kickoff that Apple Pay requires Salesforce Payments (the native Stripe path). If the merchant requires a custom gateway AND Apple Pay, escalate to a full custom Apple Pay merchant session integration that lives outside the `CommercePayments` adapter. Budget significant additional engineering effort and document the architecture decision.

---

## Gotcha 4: Gateway Callout Limits Apply Inside processRequest

**What happens:** The `processRequest` method runs synchronously during checkout. It is subject to the standard Apex governor limits: 100 HTTP callouts per transaction, 10 seconds callout timeout per individual request (configurable up to 120 seconds), and the overall 10-second CPU time limit for synchronous Apex. A payment gateway that requires multiple sequential API calls (e.g., create token, then create customer, then authorize) can blow through these limits during high-traffic checkout windows.

**When it occurs:** During load testing or peak traffic events. A single-callout adapter rarely hits this, but retry logic or multi-step gateway flows can.

**How to avoid:** Design the adapter to make the minimum number of callouts per `RequestType`. If multi-step gateway flows are unavoidable, investigate whether any steps can be pre-executed asynchronously (e.g., customer profile creation). Set explicit callout timeouts on `HttpRequest` to avoid waiting the full 120 seconds on a hung gateway response.

---

## Gotcha 5: SalesforceResultCodes Mapping Is Required for Commerce Order Processing

**What happens:** A developer populates the gateway-specific fields on a response object (`setGatewayReferenceNumber`, `setGatewayResultCode`) but omits `setSalesforceResultCodeInfo`. The Commerce order management system cannot interpret gateway-specific result codes — it relies on the `SalesforceResultCodes` enum mapping to determine whether to proceed, decline, or retry. Without this mapping, order transitions may stall or the order may be left in an indeterminate state.

**When it occurs:** When adapters are authored by developers familiar with the raw gateway API but not with the `CommercePayments` response contract. The field is not syntactically required by the compiler.

**How to avoid:** Every response handler must call `setSalesforceResultCodeInfo(CommercePayments.SalesforceResultCodes.Success)` on success and the appropriate decline/error code on failure. Add a validation check in the test class that asserts `getSalesforceResultCodeInfo()` is non-null on all response objects.
