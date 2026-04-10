---
name: commerce-checkout-configuration
description: "Use this skill when configuring Salesforce B2B or D2C Commerce checkout: payment methods, shipping/tax integration, guest checkout, order summary setup, and CartCheckoutSession state orchestration. Trigger keywords: checkout flow, payment adapter, shipping tax integration, guest checkout, order summary, CartCheckoutSession, Managed Checkout, Commerce checkout flow. NOT for CPQ quoting, Checkout.com account management, or Service Cloud Order Management post-fulfillment logic."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Performance
triggers:
  - "checkout is not moving past the shipping step in my B2B Commerce store"
  - "how do I configure payment methods in Salesforce Commerce checkout"
  - "guest checkout is not collecting email in my LWR storefront"
  - "shipping and tax are not calculating when I change the delivery address"
  - "order summary is missing billing address after order creation"
  - "how do I set up a custom payment gateway with an Apex adapter"
  - "CartCheckoutSession is stuck in a particular state and will not progress"
tags:
  - commerce
  - checkout
  - payment-adapter
  - shipping
  - tax
  - cart-checkout-session
  - guest-checkout
  - order-summary
  - b2b-commerce
  - d2c-commerce
  - lwr
  - managed-checkout
inputs:
  - "Store template type: LWR (Managed Checkout) or Aura (Flow Builder checkout)"
  - "Payment gateway name and whether a custom Apex Payment Adapter is required"
  - "Whether guest checkout is needed (headless or storefront)"
  - "Shipping carrier integration method: external service call or custom Apex"
  - "Tax calculation method: Avalara, Vertex, or custom Apex provider"
  - "Order management requirements: does the merchant use Salesforce Order Management?"
outputs:
  - "Configured CartCheckoutSession state machine (inventory → shipping → tax → payment authorization → order creation)"
  - "Apex Payment Adapter class implementing the sfdc_checkout.CartPaymentAuthorize interface"
  - "Shipping and tax integration configuration in Commerce Setup"
  - "Guest checkout configuration with required email/phone fields"
  - "Order Summary record with correct billing address linkage"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Commerce Checkout Configuration

This skill activates when a practitioner needs to configure or debug the end-to-end checkout experience for a Salesforce B2B or D2C Commerce store — covering CartCheckoutSession state orchestration, payment gateway integration via Apex adapters, shipping and tax API wiring, guest checkout requirements, and order summary creation. It does not cover CPQ quoting, post-fulfillment Order Management flows, or third-party checkout-as-a-service integrations outside Salesforce.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Store template type.** LWR stores use Managed Checkout (a platform-orchestrated checkout experience). Aura stores use a Flow Builder-driven checkout flow. These are mutually exclusive runtime models with different configuration surfaces.
- **Payment gateway contract.** Determine which payment gateway the merchant uses (e.g., Stripe, Adyen, Braintree). A custom Apex class implementing `sfdc_checkout.CartPaymentAuthorize` is the only supported integration path.
- **Guest vs. authenticated.** Guest checkout requires specific shipping address fields (email, phone) and additional site guest user permission set assignments. Without these, order creation fails silently.
- **Shipping and tax service availability.** Shipping rates and tax amounts are fetched in a single async API call when the buyer enters a delivery address. The external endpoint must respond within the platform's async callout timeout window. A failed callout leaves CartCheckoutSession in an error state.
- **Billing address on cart.** The `BillingStreet`, `BillingCity`, `BillingPostalCode`, `BillingCountry`, and `BillingState` fields on the WebCart record must be set before the final order creation step executes. Missing fields cause OrderSummary to be created with a null billing contact — there is no error thrown.

---

## Core Concepts

### CartCheckoutSession State Machine

Checkout in Salesforce Commerce is modeled as a `CartCheckoutSession` record that advances through a defined set of sequential states. The canonical state sequence is:

1. **Start** — session created, cart validated
2. **Inventory** — inventory availability checked for all line items
3. **Pricing** — prices recalculated against active price books
4. **Shipping** — available shipping methods fetched from an external service or custom Apex
5. **Tax** — tax amounts calculated, applied to cart totals
6. **Payment Authorization** — payment gateway called to authorize the selected payment instrument
7. **Order Creation** — WebCart converted to an Order and OrderSummary

Each state transition is atomic. If a state fails (e.g., an inventory check returns insufficient stock), the session pauses in that state and exposes an error on the `CartValidationOutput` record linked to the session. The practitioner must resolve the underlying issue and re-trigger the state before checkout can continue.

LWR stores use the Commerce Checkout REST API (`/commerce/webstores/{id}/checkouts`) to move the session forward programmatically. Aura stores drive the same state machine through a declarative checkout Flow that calls the Cart Calculate API internally.

### LWR Managed Checkout vs. Aura Flow Builder Checkout

These are two distinct runtime models that share the same underlying CartCheckoutSession object but expose different configuration surfaces:

- **LWR (Managed Checkout):** Configured through the Commerce App in Setup. Platform manages session state progression automatically. Custom behavior is injected via Extension Points (Apex classes) registered against named extension point contracts. No Flow Builder involvement. This is the current strategic path for new stores.
- **Aura (Flow Builder Checkout):** Configured using the Checkout Flow in the storefront Experience Builder. A standard Flow template ships with the managed package; merchants clone and modify it. State transitions are modeled as Flow elements. This path is still supported but not recommended for new implementations.

Both models converge on the same Order and OrderSummary objects at completion.

### Apex Payment Adapter

Salesforce Commerce does not connect to a payment gateway directly. All payment authorization is routed through a developer-authored Apex class that implements the `sfdc_checkout.CartPaymentAuthorize` interface. The platform calls `authorizePayment(CartExtension.CartPaymentAuthorizationRequest request)` and expects a `CartExtension.CartPaymentAuthorizationResponse` in return.

The adapter class is responsible for:
- Extracting the payment token from the request (tokenized by the client-side payment component before checkout submission)
- Calling the gateway's authorization API via `Http` callout
- Mapping the gateway response (approved, declined, error) back to the Commerce response type
- Writing any gateway-specific reference data (authorization code, transaction ID) to a custom field on the order before returning

A declined authorization must return a response with `setAuthorized(false)` — not throw an exception. Throwing an exception from the adapter leaves the CartCheckoutSession in an unrecoverable error state that requires manual session reset.

### Shipping and Tax Integration

Shipping and tax are evaluated together in a single async callout triggered when the buyer selects or changes their delivery address. Salesforce calls the registered external shipping/tax service and expects a structured response containing available shipping methods (with prices) and tax line items.

Two integration paths exist:
- **Salesforce-managed integration:** For supported carriers and tax engines (Avalara, Vertex), configuration is point-and-click in Commerce Setup. Salesforce handles the callout, response parsing, and cart field updates.
- **Custom Apex shipping/tax provider:** For unsupported carriers or custom tax logic, a developer implements a class that extends `sfdc_checkout.CartShippingCharges` and another that extends `sfdc_checkout.CartTaxes`. These classes are registered as extension points and called synchronously within the async job.

---

## Common Patterns

### Pattern: Apex Payment Adapter with Tokenized Card

**When to use:** Any store that requires credit/debit card payment where the gateway is not natively supported by Salesforce Commerce.

**How it works:**
1. The storefront renders the gateway's client-side payment component (e.g., Stripe Elements). The component tokenizes the card and stores the token in a hidden field or a custom payment method record.
2. When the buyer submits payment, the token is passed to the checkout session via the `paymentMethod` payload in the Commerce Checkout API or the Flow element.
3. The platform calls the registered Apex adapter's `authorizePayment` method with a `CartPaymentAuthorizationRequest` that includes the token.
4. The adapter retrieves the token, calls the gateway's charge or authorize endpoint via `Http`, and maps the response to `CartPaymentAuthorizationResponse`.
5. On success, the adapter sets `setAuthorized(true)` and optionally sets a reference field on the cart before returning.

**Why not the alternative:** Storing raw card data in Salesforce fields violates PCI-DSS and is not possible on the platform. Tokenization at the client side before any Salesforce data layer involvement is the only compliant approach.

### Pattern: Guest Checkout with Required Address Fields

**When to use:** B2B or D2C stores that allow unauthenticated buyers to complete an order without creating an account.

**How it works:**
1. Enable Guest Browsing and Guest Checkout in the store's Experience Site settings.
2. Assign the Guest User profile the required Commerce permissions: `WebCart`, `CartItem`, `CartDeliveryGroup`, `WebOrder`, and `CartCheckoutSession` object access.
3. At address entry, the storefront component must collect and populate `Email` and `Phone` on the `CartDeliveryGroup` shipping address. These are not automatically populated from a user session because no session exists.
4. Before order creation, ensure `BillingStreet`, `BillingCity`, `BillingPostalCode`, `BillingState`, and `BillingCountry` are set on `WebCart`. Map these from the shipping address if the buyer indicates billing and shipping are the same.
5. The Order and Contact are created from these field values. Missing fields do not error — they silently produce incomplete records.

**Why not the alternative:** Relying on the platform to derive contact data from the guest session produces null Contact records on the Order. The guest user has no profile email that Salesforce can automatically populate into order fields.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New store on LWR template | Use Managed Checkout with Extension Points | Platform-managed state progression; less custom code; strategic path |
| Existing Aura store with custom Flow checkout | Keep Flow Builder checkout; do not migrate mid-project | Migration requires full storefront rebuild; parity is not automatic |
| Supported payment gateway (e.g., Stripe, Adyen) | Implement Apex Payment Adapter with client tokenization | No native gateway connector exists; adapter is the only supported path |
| Tax via Avalara or Vertex | Use native Commerce Setup integration | Salesforce manages the callout contract and cart field mapping |
| Custom carrier rate logic | Extend `sfdc_checkout.CartShippingCharges` in Apex | Provides structured integration without breaking session state |
| Guest checkout needed | Enable in Site Settings and populate email/phone on CartDeliveryGroup | Platform does not derive these from unauthenticated session |
| Order billing address missing | Set billing fields on WebCart before order creation step | OrderSummary is created from WebCart at that moment; no retry path |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner configuring or debugging Commerce checkout:

1. **Confirm the store template type.** Navigate to Commerce Setup and identify whether the store uses LWR (Managed Checkout) or Aura (Flow Builder checkout). This determines every subsequent configuration surface. Do not assume — the wrong surface produces changes that have no effect.
2. **Verify CartCheckoutSession state and errors.** Query `CartCheckoutSession` and the associated `CartValidationOutput` records in the org to identify which state the session is paused in and what error is recorded. Fix the underlying cause (inventory, shipping, tax, payment) before adjusting configuration.
3. **Configure the shipping and tax provider.** In Commerce Setup, under Shipping and Tax, register the external service endpoint or verify the Apex extension point class is deployed and assigned. Confirm the external endpoint responds within the platform callout timeout. Run a test checkout to trigger the async shipping/tax job and inspect the resulting `CartDeliveryGroupMethod` records.
4. **Deploy and register the Apex Payment Adapter.** Write or review the class implementing `sfdc_checkout.CartPaymentAuthorize`. Deploy to the org, then register it in Commerce Setup under Payment. Verify the adapter returns `setAuthorized(false)` on declines rather than throwing exceptions.
5. **Set billing address fields before order creation.** Confirm that the storefront component or Flow element populates `BillingStreet`, `BillingCity`, `BillingPostalCode`, `BillingState`, and `BillingCountry` on `WebCart` before the final order creation step. Query a test WebCart record after address entry to verify.
6. **Validate guest checkout field population.** For guest-enabled stores, confirm that `Email` and `Phone` are set on `CartDeliveryGroup` at address entry time. Complete a guest checkout end to end in a test environment and query the resulting Order Contact record to verify it is not null.
7. **Review the resulting Order and OrderSummary.** After a successful test checkout, inspect the Order, OrderSummary, and OrderDeliveryGroup records for correct billing contact, shipping method, and line item pricing. Compare against the WebCart state at order creation time.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Store template type confirmed (LWR Managed Checkout or Aura Flow Builder)
- [ ] CartCheckoutSession state machine tested end to end in a scratch or sandbox org
- [ ] Apex Payment Adapter deployed, registered in Commerce Setup, and tested with decline scenario
- [ ] Shipping and tax provider registered; `CartDeliveryGroupMethod` records verified after address entry
- [ ] Billing address fields set on WebCart before order creation; OrderSummary billing contact is non-null
- [ ] Guest checkout tested end to end; email and phone present on resulting Order Contact
- [ ] All Apex adapter callouts mocked in unit tests; no raw card data stored in any Salesforce field

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Billing address must be set on WebCart before order creation** — If `BillingStreet`, `BillingCity`, `BillingPostalCode`, `BillingState`, and `BillingCountry` are not populated on the `WebCart` record at the moment the Order is created, the resulting `OrderSummary` will have a null billing contact. No error or warning is thrown. The only fix is to prevent the issue upstream by ensuring the storefront or Flow sets these fields before the order creation state executes.
2. **Guest checkout requires email and phone on CartDeliveryGroup shipping address** — For unauthenticated buyers, Salesforce has no profile email or phone to draw from. If the storefront does not explicitly collect and write `Email` and `Phone` to `CartDeliveryGroup`, the resulting Contact record on the Order is created with null values. This breaks downstream processes such as order confirmation emails and fulfillment system integrations.
3. **Payment adapter exceptions leave CartCheckoutSession unrecoverable** — If the Apex Payment Adapter throws an unhandled exception instead of returning `setAuthorized(false)`, the `CartCheckoutSession` enters an error state that cannot be resolved by retrying checkout. The session must be reset via the Commerce Checkout API (`DELETE /checkouts/{id}`) and a new session started. Train gateway error handling to always return a structured response, never throw.
4. **Managed Checkout Extension Points and Flow Builder checkout are mutually exclusive** — LWR stores register custom behavior via Apex Extension Point classes in Commerce Setup. Configuring a checkout Flow in Experience Builder has no effect on an LWR store. Conversely, Extension Point classes have no effect on Aura stores. Mixing configuration from both surfaces in the same store produces silently ignored settings.
5. **Shipping and tax callout failure pauses the session silently** — If the external shipping/tax service returns an error or times out, the `CartCheckoutSession` pauses at the Shipping state without surfacing a user-visible error message unless the storefront is explicitly coded to read `CartValidationOutput`. Merchants often interpret this as a UI bug rather than a backend callout failure. Always inspect `CartValidationOutput` records linked to the session when debugging a stuck checkout.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CartCheckoutSession record | Platform record tracking current checkout state; inspect for errors in `CartValidationOutput` |
| Apex Payment Adapter class | Custom Apex implementing `sfdc_checkout.CartPaymentAuthorize`; deployed and registered in Commerce Setup |
| CartDeliveryGroupMethod records | Created after shipping provider responds; confirm correct rates are returned |
| Order and OrderSummary records | Final purchase records; verify billing contact, line items, and payment authorization reference |
| Commerce Setup configuration | Registered shipping/tax provider and payment adapter; the authoritative configuration source |

---

## Related Skills

- commerce-store-setup — Configure the store catalog, entitlements, and price books before checkout is reached
- apex-callout-patterns — Best practices for writing reliable HTTP callouts from Apex, relevant to payment adapter and shipping integrations
- order-management-integration — Post-checkout fulfillment flows using Salesforce Order Management
