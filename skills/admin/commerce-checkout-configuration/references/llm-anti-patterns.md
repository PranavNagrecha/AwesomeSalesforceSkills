# LLM Anti-Patterns — Commerce Checkout Configuration

Common mistakes AI coding assistants make when generating or advising on Commerce Checkout Configuration. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Throwing Exceptions from the Payment Adapter Instead of Returning Declined Response

**What the LLM generates:** An Apex Payment Adapter where gateway failures (HTTP 4xx/5xx, callout timeouts) are handled by re-throwing `CalloutException` or letting `JSONException` propagate out of `authorizePayment`.

**Why it happens:** Standard Apex error-handling convention is to throw exceptions on failures and let callers handle them. LLMs trained on general Apex patterns apply this convention without accounting for the Commerce platform contract, which expects a structured response object in all exit paths.

**Correct pattern:**

```apex
public CartExtension.CartPaymentAuthorizationResponse authorizePayment(
    CartExtension.CartPaymentAuthorizationRequest request
) {
    CartExtension.CartPaymentAuthorizationResponse response =
        new CartExtension.CartPaymentAuthorizationResponse();
    try {
        // ... callout logic ...
        response.setAuthorized(true);
    } catch (Exception e) {
        // Always return declined — never re-throw
        response.setAuthorized(false);
        response.setErrorMessage(e.getMessage());
    }
    return response;
}
```

**Detection hint:** Grep for `throw` inside any class implementing `sfdc_checkout.CartPaymentAuthorize`. Any `throw` statement in the method body is a defect.

---

## Anti-Pattern 2: Advising Use of Flow Builder Checkout Configuration for LWR Stores

**What the LLM generates:** Instructions to navigate to Experience Builder and modify the Checkout Flow steps (e.g., "add a Flow element before the payment step") for a store that is actually on an LWR template.

**Why it happens:** Pre-Spring '23 Salesforce Commerce documentation heavily featured Flow Builder checkout. LLM training data includes this documentation and articles that do not distinguish template type. The LLM conflates Aura checkout (Flow-based) with LWR checkout (Extension Point-based).

**Correct pattern:**

```
For LWR stores: Register Apex Extension Point classes in Commerce Setup > Store > Checkout Settings.
Do NOT touch Experience Builder checkout Flows — they have no effect on LWR stores.

For Aura stores: Open Experience Builder > Checkout Flow > modify the Flow.
Do NOT look for Extension Point registration in Commerce Setup — it does not apply.
```

**Detection hint:** If advice references both "Experience Builder Checkout Flow" and "Commerce Setup Extension Points" as steps for the same store, one is wrong. Ask the user to confirm their store template type before proceeding.

---

## Anti-Pattern 3: Assuming Platform Derives Guest Buyer Contact Data Automatically

**What the LLM generates:** Checkout configuration steps for guest stores that do not include explicit mapping of email and phone to `CartDeliveryGroup`, under the assumption that because the buyer "provided their email," Salesforce will use it.

**Why it happens:** For authenticated buyers, Salesforce does derive contact data from the user session. LLMs generalize this behavior to guest checkout without recognizing the key condition: the derivation requires an authenticated session. Guest buyers have no session, so no derivation occurs.

**Correct pattern:**

```javascript
// When submitting guest address, include email and phone explicitly:
const deliveryAddressPayload = {
  deliveryAddress: {
    street: address.street,
    city: address.city,
    state: address.state,
    postalCode: address.postalCode,
    country: address.country,
    email: guestEmail,      // Must be explicit — not derived
    phone: guestPhone,      // Must be explicit — not derived
    firstName: address.firstName,
    lastName: address.lastName,
  }
};
```

**Detection hint:** Any guest checkout implementation advice that does not mention `CartDeliveryGroup.Email` or `phone` in the delivery address payload is incomplete. Flag for review.

---

## Anti-Pattern 4: Recommending Direct Billing Address Updates via DML Instead of Checkout API

**What the LLM generates:** Code that sets WebCart billing address fields via a direct `update cartRecord;` DML statement from a custom Apex trigger or process automation, rather than through the Commerce Checkout API or a storefront component.

**Why it happens:** LLMs recognize that WebCart is a standard Salesforce object and that billing fields exist on it. They apply the standard DML pattern without knowing that the Commerce platform has transactional ordering constraints — specifically that the billing address must be committed before the order creation state reads it, and that process automation timing relative to CartCheckoutSession state execution is non-deterministic.

**Correct pattern:**

```
Set billing address fields on WebCart from the storefront's address component (LWC updateRecord)
or from the Commerce Checkout API PATCH call that submits the address.

Do NOT rely on Apex triggers, Process Builder, or Flow automation to set these fields
after the buyer submits — the order creation state may execute before the automation fires.
```

**Detection hint:** If the proposed solution sets WebCart billing fields from an after-update trigger on `CartDeliveryGroup` or from a Flow triggered by cart record changes, flag it as potentially racy relative to state machine execution.

---

## Anti-Pattern 5: Omitting CartValidationOutput Error Surfacing from Storefront

**What the LLM generates:** A checkout implementation that calls the Commerce Checkout API and simply shows a generic "something went wrong" message when shipping methods do not appear or payment fails, without querying `CartValidationOutput` for the actual platform error.

**Why it happens:** LLMs model checkout error handling as a simple HTTP response pattern: if the API call returns non-2xx, show an error. They do not model the platform's secondary error channel — `CartValidationOutput` records — which is where the meaningful error detail lives for shipping, tax, inventory, and payment failures. The CartCheckoutSession API may return 2xx even when the session is paused in an error state.

**Correct pattern:**

```apex
// After triggering a checkout state transition, query CartValidationOutput
List<CartValidationOutput> errors = [
    SELECT Message, Level, Type
    FROM CartValidationOutput
    WHERE CartId = :cartId
    AND Level = 'Error'
    ORDER BY CreatedDate DESC
    LIMIT 10
];
// Surface errors[0].Message to the buyer and support team
```

**Detection hint:** Any checkout integration guide that does not include a `CartValidationOutput` query or a storefront component property bound to validation output is incomplete for production support. Flag any advice that treats the Commerce Checkout API response body alone as the complete error signal.

---

## Anti-Pattern 6: Generating a Payment Adapter that Stores Raw Card Numbers

**What the LLM generates:** A payment processing example where the card number, CVV, or expiration date is passed from the browser to an Apex method or stored in a Salesforce field before being sent to the gateway.

**Why it happens:** LLMs trained on generic payment examples (non-Salesforce) may generate code that sends card data server-side as a standard API parameter. This pattern is common in non-PCI-scoped environments but is illegal in Salesforce Commerce checkout.

**Correct pattern:**

```
NEVER pass raw card numbers or CVV values to Salesforce Apex or store them in Salesforce fields.
The payment gateway's client-side JavaScript component (e.g., Stripe.js, Braintree hosted fields)
tokenizes the card in the browser. Only the opaque token reaches Salesforce.
The Apex Payment Adapter receives only the token and calls the gateway to authorize it.
```

**Detection hint:** Any Apex method signature or LWC property that includes field names like `cardNumber`, `cvv`, `securityCode`, or `expirationDate` is a PCI violation. Reject immediately.
