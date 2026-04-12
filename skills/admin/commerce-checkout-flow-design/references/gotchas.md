# Gotchas — Commerce Checkout Flow Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: LWR and Aura Checkout Are Mutually Exclusive — There Is No Hybrid or Migration Path

**What happens:** A practitioner designs checkout customizations assuming they can use Flow Builder for some steps and Extension Points for others, or plans to migrate from Aura to LWR after launch by copying their Flow configuration. Neither is possible. LWR stores use Managed Checkout exclusively — no Flow in Experience Builder affects the checkout on an LWR store. Aura stores use Flow Builder exclusively — Extension Point classes registered in Commerce Setup are not called. A team that builds checkout customizations on the wrong surface will find their work has zero effect when tested.

**When it occurs:** Any time the store template type is not confirmed before design work begins, or when a project assumes a future migration is an upgrade path rather than a complete rebuild.

**How to avoid:** Lock the runtime model selection as the first step in any checkout design session. Confirm the template type by checking the Experience Cloud Site template in the Commerce App in Setup. Document the chosen model explicitly and note that migration requires a full storefront rebuild with no automated migration tool. Treat the runtime model as an irreversible architectural decision.

---

## Gotcha 2: Guest Checkout Requires Explicit Email and Phone Collection — Platform Does Not Derive Them

**What happens:** For unauthenticated (guest) buyers, Salesforce has no user session from which to derive contact data. If the checkout UX does not include explicit form fields for `Email` and `Phone` — and the values are not written to `CartDeliveryGroup` before the order creation step — the resulting Order has a null Contact record. No error or warning is thrown at order creation. The failure is silent and discovered only when order confirmation emails fail to send or when the fulfillment integration finds null contact fields.

**When it occurs:** Any guest checkout implementation that assumes the platform will auto-populate contact fields the way it does for authenticated buyers. This is the most common silent data quality issue in guest checkout implementations.

**How to avoid:** In the checkout design, explicitly identify email and phone as required fields in the address entry step for guest buyers. Map them to `CartDeliveryGroup.Email` and `CartDeliveryGroup.Phone`. Mark these fields as mandatory in the UX specification — not just as nice-to-have. Include order confirmation email delivery in the end-to-end test criteria so that null contact issues are caught before go-live.

---

## Gotcha 3: Billing Address Is Not Auto-Derived from Shipping Address — Must Be Explicitly Mapped

**What happens:** The "same as shipping address" checkbox pattern common in consumer checkout UX does not have a platform-native implementation. Salesforce Commerce does not automatically copy shipping address fields from `CartDeliveryGroup` to the `WebCart` billing address fields. If the design assumes this is automatic and the implementation team does not build explicit field mapping logic, the `OrderSummary` is created with null billing contact fields. This is another silent failure — no error is thrown.

**When it occurs:** Any checkout design that includes a "same as billing" toggle without specifying the explicit field mapping logic that must back it. Common in D2C stores modeled after consumer checkout patterns from other platforms where this behavior is provided out-of-the-box.

**How to avoid:** In the checkout design, specify that the "same as shipping" toggle must trigger explicit population of `WebCart.BillingStreet`, `WebCart.BillingCity`, `WebCart.BillingPostalCode`, `WebCart.BillingState`, and `WebCart.BillingCountry` from the corresponding `CartDeliveryGroup` address fields. This must happen before the order creation step executes. Add a verification step in the test plan: after address entry, query the `WebCart` record directly and confirm billing fields are non-null before proceeding to payment.

---

## Gotcha 4: Shipping and Tax Are a Single Combined Async Step — Not Two Separate Design Steps

**What happens:** From the platform's perspective, shipping rate calculation and tax calculation are triggered together in a single async job when the buyer selects or changes their delivery address. Designs that model "calculate shipping" and "calculate tax" as two distinct user-triggered steps — each with its own button, confirmation, and retry flow — do not correspond to how the platform actually works. Implementing these as separate triggered actions requires significant workarounds and creates state inconsistencies.

**When it occurs:** When checkout UX is designed by practitioners familiar with other commerce platforms that separate shipping and tax as discrete steps, or when the business requirement is to show tax as a separate confirmation before order submission.

**How to avoid:** Design shipping method selection and tax display as a single UX step triggered by delivery address entry. The UX shows a loading state while the async job runs, then displays both shipping method options and tax totals together when the job completes. If the business requires separate tax review, design it as a display-only review step after shipping selection — not as a separate calculation trigger.

---

## Gotcha 5: Payment Adapter Exceptions Are Unrecoverable Without a Session Reset

**What happens:** If the Apex Payment Adapter throws an unhandled exception instead of returning `setAuthorized(false)` on a decline, the `CartCheckoutSession` enters an error state that cannot be resolved by the buyer simply re-entering payment details. The session must be explicitly reset via the Commerce Checkout API (`DELETE /checkouts/{id}`) and a new session started before checkout can proceed. Buyers who hit this state in a production storefront experience a checkout that appears permanently broken until the session is cleared.

**When it occurs:** This is a design constraint that must be communicated to the implementation team as part of the payment options design spec. It is not triggered by design choices per se, but the checkout decline UX design must account for it: the decline retry flow must include a session reset, not just a re-presentation of the payment form.

**How to avoid:** In the payment options design, specify the decline UX as: (1) surface error message to buyer, (2) reset CartCheckoutSession via Commerce Checkout API, (3) allow buyer to re-enter payment details in a fresh session. Flag this explicitly in the design handoff to the implementation team as a requirement for the Apex adapter: declines must return `setAuthorized(false)`, never throw. Include a forced-decline test scenario in the end-to-end test plan.
