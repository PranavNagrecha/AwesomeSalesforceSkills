# Gotchas — Commerce Checkout Configuration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Billing Address Missing on OrderSummary — No Error Thrown

**What happens:** When the order creation state of CartCheckoutSession executes, it reads `BillingStreet`, `BillingCity`, `BillingPostalCode`, `BillingState`, and `BillingCountry` from the `WebCart` record to construct the billing contact on the resulting Order and OrderSummary. If any of these fields are null, the Order is created with a null billing contact. No validation error is raised, no `CartValidationOutput` record is written, and the checkout appears to complete successfully. The missing data is only discovered downstream when finance systems, invoice generators, or reporting queries against OrderSummary return null billing information.

**When it occurs:** Stores where the checkout UI collects a shipping address but does not explicitly copy it to the WebCart billing fields before submission. This is the default behavior of the standard LWC checkout components unless the developer adds explicit billing-address mapping logic. It also occurs when merchants assume "same as shipping" is handled automatically by the platform.

**How to avoid:** Add an explicit step in the storefront's checkout address component that writes `BillingStreet`, `BillingCity`, `BillingPostalCode`, `BillingState`, and `BillingCountry` to the `WebCart` record whenever the buyer confirms their address. For stores with a separate billing address form, map that form to the same WebCart fields. Validate by querying `OrderSummary.BillingAddress` after a test checkout and asserting it is non-null.

---

## Gotcha 2: Guest Checkout Requires Email and Phone on CartDeliveryGroup — Not Derived from Session

**What happens:** For authenticated buyers, Salesforce can derive contact details from the buyer's user profile. For guest (unauthenticated) buyers, no profile exists. If the storefront does not explicitly set `Email` and `Phone` on the `CartDeliveryGroup` record at address-entry time, the Order Contact record is created with null values. Order confirmation emails (which typically trigger on Contact email) never fire. Fulfillment system integrations that depend on order contact phone fail silently.

**When it occurs:** Any guest checkout implementation where the storefront collects the buyer's email (e.g., in a separate "guest email" form field) but does not write it to `CartDeliveryGroup.Email` via the Commerce Checkout API or Flow. Teams often assume that because Salesforce prompted the buyer for an email, it is stored somewhere accessible to the order creation process — it is not unless explicitly mapped.

**How to avoid:** When processing the guest's address submission, include `email` and `phone` in the delivery address payload sent to the Commerce Checkout API's `PATCH /checkouts/{id}` endpoint. For Aura Flow stores, the Update Delivery Address Flow element exposes these as explicit input fields. Validate by querying `Order.BillToContact.Email` on a completed guest order in a test environment.

---

## Gotcha 3: Payment Adapter Exception Makes CartCheckoutSession Unrecoverable

**What happens:** If the Apex class implementing `sfdc_checkout.CartPaymentAuthorize` throws an unhandled exception during `authorizePayment`, the `CartCheckoutSession` enters an error state that cannot be resolved by retrying. The platform does not provide a mechanism to resume the same session. The session must be explicitly deleted via `DELETE /commerce/webstores/{id}/checkouts/{sessionId}` and a new checkout session started from scratch.

**When it occurs:** Any uncaught exception in the adapter body — including `System.CalloutException` on gateway timeout, `JSONException` on malformed gateway response, or `NullPointerException` on missing fields. Standard Apex exception handling often re-throws or does not catch these at the outermost level.

**How to avoid:** Wrap the entire `authorizePayment` body in a try/catch that catches `Exception`. In the catch block, construct and return a `CartPaymentAuthorizationResponse` with `setAuthorized(false)` and an error message. Reserve exception propagation for cases where returning a structured response is itself impossible (i.e., the response object cannot be constructed).

---

## Gotcha 4: Managed Checkout Extension Points and Flow Builder Checkout Do Not Coexist

**What happens:** LWR stores use the Managed Checkout model where custom behavior is injected through Apex Extension Point classes registered in Commerce Setup. Aura stores use a declarative Flow in Experience Builder. If a developer registers an Apex extension point on an Aura store, or configures a checkout Flow on an LWR store, the configuration is silently ignored. No error or warning indicates the mismatch. Debugging is extremely difficult because the affected extension appears correctly configured in Setup but never executes.

**When it occurs:** Teams migrating from Aura to LWR who retain Aura checkout Flow customizations, or developers who follow LWR documentation on an Aura store because the store's template is ambiguous. It also occurs when a merchant's org has both template types across multiple storefronts and developers apply configuration from one store's documentation to another.

**How to avoid:** Before registering any checkout extension or Flow, confirm the store template by navigating to the Commerce App in Setup and checking the Experience Cloud Site template associated with the store. LWR stores will show an LWR template; Aura stores will show an Aura template. Apply only the configuration surface appropriate to that template.

---

## Gotcha 5: Shipping/Tax Callout Failure Pauses Session Without Visible User Error

**What happens:** When the buyer enters or changes their delivery address, CartCheckoutSession triggers an asynchronous job to fetch shipping rates and tax amounts from the registered provider. If that callout fails — due to endpoint unavailability, timeout, or malformed response — the session pauses at the Shipping state. A `CartValidationOutput` record is written with the error detail, but the standard storefront components do not display this error to the buyer. The buyer sees the shipping method selector remain empty or unchanged, with no error message. Merchants often log support tickets describing this as a "UI bug" or "checkout freezing" rather than a backend callout failure.

**When it occurs:** External shipping or tax service is down or unreachable during checkout. The named credential endpoint URL is misconfigured after a deployment. The external service returns a response format that differs from what the Apex provider class expects, causing a parse error inside the async job.

**How to avoid:** Instrument the storefront's checkout component to query `CartValidationOutput` records associated with the active `CartCheckoutSession` and surface the `Message` field to the buyer when shipping methods are absent. Set up monitoring on the external shipping/tax endpoint with alerting on error rates. In the Apex shipping/tax provider class, wrap the callout in try/catch and write a descriptive `CartValidationOutput` record rather than letting the platform write a generic one.
