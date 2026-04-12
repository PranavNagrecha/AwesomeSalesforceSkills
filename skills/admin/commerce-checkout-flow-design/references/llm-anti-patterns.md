# LLM Anti-Patterns — Commerce Checkout Flow Design

Common mistakes AI coding assistants make when generating or advising on Commerce Checkout Flow Design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Describing a Unified Checkout Flow That Applies to Both LWR and Aura Stores

**What the LLM generates:** Checkout design advice that presents Experience Builder Flow configuration and Commerce Setup Extension Point registration as parallel options the practitioner can choose from, without noting that each only applies to one store template type. For example: "You can customize the checkout by either modifying the checkout Flow in Experience Builder or by registering an Extension Point class in Commerce Setup."

**Why it happens:** Training data includes documentation and forum posts for both LWR and Aura stores. Without a store template type discriminator in the prompt, the model conflates the two configuration surfaces and presents them as equivalent alternatives rather than as mutually exclusive runtime models.

**Correct pattern:**

```
Before generating any checkout design guidance, confirm the store template type:
  - LWR store → customization surface is Commerce App in Setup (Extension Points only)
  - Aura store → customization surface is Experience Builder (Flow Builder only)
  - NEVER describe both as available options for the same store
  - NEVER generate Flow Builder steps for an LWR store
  - NEVER generate Extension Point registration steps for an Aura store
```

**Detection hint:** If the output mentions both "Experience Builder Checkout Flow" and "Commerce Checkout Extension Points" as steps for the same store, one is wrong. Ask the user to confirm their store template type before continuing.

---

## Anti-Pattern 2: Omitting Guest Checkout Email and Phone Collection Requirements

**What the LLM generates:** A guest checkout flow design that collects shipping address fields (street, city, postal code, state, country) but does not include `Email` and `Phone` as required fields. The design may note "collect contact information" without specifying the exact fields and where they map to in the data model.

**Why it happens:** Authenticated buyer checkout does not require explicit email/phone collection because the platform derives these from the user session. LLMs trained on general checkout patterns apply authenticated buyer defaults to guest buyer design, missing the platform-specific requirement that guest buyers have no session to draw from.

**Correct pattern:**

```
Guest checkout address step must include:
  - CartDeliveryGroup.Email (required — no session default exists for guest buyers)
  - CartDeliveryGroup.Phone (required — same reason)
  - CartDeliveryGroup.Street, City, PostalCode, State, Country (standard address)

Failure to collect Email results in:
  - Null Contact on resulting Order record (silent — no error thrown)
  - Order confirmation emails fail to send
  - Fulfillment integrations find null contact fields
```

**Detection hint:** If a guest checkout design does not explicitly call out email and phone as required fields mapped to `CartDeliveryGroup`, the design is incomplete. Search the output for "CartDeliveryGroup.Email" — if absent from guest path requirements, flag it.

---

## Anti-Pattern 3: Treating "Same as Shipping" Billing Address as a Platform Feature

**What the LLM generates:** A checkout UX design that includes a "same as shipping address" checkbox with a note like "Salesforce Commerce will automatically populate billing fields from the shipping address when this is selected."

**Why it happens:** Many e-commerce platforms (Shopify, WooCommerce, Magento) natively support automatic billing address derivation from the shipping address. LLMs trained on cross-platform checkout documentation apply this cross-platform assumption to Salesforce Commerce, where no such native behavior exists.

**Correct pattern:**

```
"Same as shipping" must be implemented as explicit field mapping logic:
  WebCart.BillingStreet    ← CartDeliveryGroup.Street
  WebCart.BillingCity      ← CartDeliveryGroup.City
  WebCart.BillingPostalCode ← CartDeliveryGroup.PostalCode
  WebCart.BillingState     ← CartDeliveryGroup.State
  WebCart.BillingCountry   ← CartDeliveryGroup.Country

This mapping must execute before the order creation step.
Platform does NOT do this automatically.
Missing BillingStreet/City/etc. on WebCart → null billing contact on OrderSummary (silent).
```

**Detection hint:** If output describes "same as shipping" behavior without specifying explicit `WebCart` billing field population, the implementation will produce null billing fields on orders. Flag any design that says "billing address will be copied automatically" or "the platform handles billing address derivation."

---

## Anti-Pattern 4: Presenting LWR-to-Aura Migration as a Low-Cost Future Option

**What the LLM generates:** Checkout design advice that recommends starting with the Aura template for faster initial delivery, with a note that "you can migrate to LWR Managed Checkout later when you're ready for the more modern architecture."

**Why it happens:** LLMs default to "start simple, migrate later" advice as a general architectural heuristic. This heuristic is correct in many contexts but is specifically wrong for Salesforce Commerce store template migration, where no migration path exists and a template change requires a complete storefront rebuild from scratch.

**Correct pattern:**

```
LWR ↔ Aura migration is NOT an upgrade path.
It is a complete storefront rebuild with no automated migration tooling.
  - All templates rebuilt from scratch
  - All customizations rewritten for the new surface (Flow → Extension Points or vice versa)
  - All content (products, assets, configurations) remapped

Recommendation: Choose the runtime model that fits current AND foreseeable requirements.
Do not defer this decision. The design phase is the last low-cost opportunity.
```

**Detection hint:** If output uses phrases like "you can switch to LWR later," "migrate from Aura to LWR when ready," or "start with Aura and upgrade," flag this as incorrect. There is no upgrade path — only a rebuild.

---

## Anti-Pattern 5: Designing Separate "Calculate Shipping" and "Calculate Tax" User-Triggered Steps

**What the LLM generates:** A checkout flow design with two distinct user-visible steps: "Calculate Shipping" (buyer triggers a shipping rate lookup) and "Calculate Tax" (buyer triggers a tax calculation). Each step has its own button, confirmation, and potential error state.

**Why it happens:** Some commerce platforms and checkout implementations do separate shipping and tax as distinct API calls or user actions. LLMs apply this pattern without accounting for the Salesforce Commerce platform behavior where shipping and tax are evaluated together in a single async job triggered by delivery address entry — not as two separate user-triggered operations.

**Correct pattern:**

```
Salesforce Commerce triggers a single combined async job when the buyer
selects or changes their delivery address. This job:
  1. Calls the registered shipping/tax service once
  2. Returns available shipping methods AND tax amounts together
  3. Populates CartDeliveryGroupMethod records (shipping) and cart tax fields (tax)

UX design must reflect this:
  - One loading state after address entry covers both shipping AND tax
  - Shipping method selection and tax display appear together after the job completes
  - There is no separate "recalculate tax" user action
  - A failed callout pauses the session at the Shipping state;
    UX must handle this as a single combined error, not two separate error states
```

**Detection hint:** If output shows separate "Calculate Shipping" and "Calculate Tax" buttons or confirmation steps, it does not map to platform behavior. Look for any design that treats shipping and tax as independently user-triggered operations and flag it.

---

## Anti-Pattern 6: Not Scoping PCI-DSS Impact as a Design Requirement

**What the LLM generates:** A payment step design that describes collecting credit card details (card number, CVV, expiry) in a Salesforce-rendered form, storing them in custom fields or a custom object, and then passing them to a payment gateway via an Apex callout.

**Why it happens:** LLMs default to the most literal interpretation of "collect and process payment" without knowing that storing or transmitting raw card data through Salesforce infrastructure violates PCI-DSS and is architecturally impossible — Salesforce fields cannot store raw PANs (Primary Account Numbers) under its compliance model.

**Correct pattern:**

```
Credit card data must NEVER touch Salesforce infrastructure:
  1. Render gateway's client-side component (Stripe Elements, Adyen Drop-in,
     Braintree Hosted Fields) in the storefront
  2. Buyer enters card data into the gateway's iframe — data goes directly to
     the payment gateway, never to Salesforce
  3. Gateway returns a single-use token representing the card
  4. ONLY the token is passed to the CartCheckoutSession via Commerce Checkout API
  5. The Apex Payment Adapter receives the token, calls the gateway to authorize it,
     and returns authorized=true/false to the platform

No Salesforce field, object, log, or API payload ever contains raw card data.
```

**Detection hint:** If output describes storing card numbers, CVV codes, or expiry dates in Salesforce fields, or sending raw card data via an Apex HTTP callout, flag this as a PCI-DSS violation and architectural impossibility on the Salesforce platform.
