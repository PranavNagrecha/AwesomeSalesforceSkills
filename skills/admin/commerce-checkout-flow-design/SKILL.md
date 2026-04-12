---
name: commerce-checkout-flow-design
description: "Use this skill when designing the checkout experience for a Salesforce B2B or D2C Commerce storefront — covering runtime model selection (LWR Managed Checkout vs Aura Flow Builder), cart and line-item requirements, payment option scoping, shipping rule definition, and guest vs. registered buyer experience design. Trigger keywords: checkout flow design, checkout UX requirements, LWR vs Aura checkout, guest checkout design, payment options design, shipping rules, checkout experience planning. NOT for implementation: does not cover Apex adapter code, CartCheckoutSession debugging, Extension Point registration, or Flow Builder configuration steps."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - User Experience
triggers:
  - "we are starting a new Commerce storefront and need to decide what the checkout experience should look like"
  - "I need to figure out whether to use LWR Managed Checkout or Aura Flow Builder checkout before we begin building"
  - "the business wants guest checkout and multiple payment options but we have not decided on the design yet"
  - "we need to define the shipping rules and payment methods for our B2B Commerce checkout before any development starts"
  - "how do I design a checkout flow that supports both registered buyers and guest buyers in Salesforce Commerce"
  - "what are the UX requirements and constraints I need to lock down before building checkout in a D2C storefront"
tags:
  - commerce
  - checkout
  - checkout-design
  - lwr
  - aura
  - managed-checkout
  - guest-checkout
  - payment-options
  - shipping-rules
  - b2b-commerce
  - d2c-commerce
  - ux-design
  - requirements
inputs:
  - "Store template type already chosen or under evaluation: LWR (Managed Checkout) or Aura (Flow Builder)"
  - "Whether the storefront needs to support guest (unauthenticated) buyers, registered buyers, or both"
  - "Payment methods the business intends to support (credit card, PO, ACH, invoice, etc.)"
  - "Shipping carrier strategy: external carrier rates, flat rate, or free shipping with conditions"
  - "B2B vs D2C context: account-based purchasing, contract pricing, and approval workflows are B2B concerns"
  - "Any regulatory or compliance requirements affecting payment (PCI-DSS scope) or data collection"
outputs:
  - "Runtime model selection recommendation (LWR Managed Checkout or Aura Flow Builder) with rationale"
  - "Checkout flow step map: ordered list of steps, decision points, and required data per step"
  - "Guest vs. registered experience matrix: what differs, what required fields must be collected, what permissions are needed"
  - "Payment options design: supported methods, tokenization approach, fallback behavior on decline"
  - "Shipping rules design: rate source, free shipping thresholds, multiple delivery group handling"
  - "Design constraints document: what the chosen runtime model cannot do, where custom Apex will be required"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Commerce Checkout Flow Design

This skill activates when a practitioner or project team needs to define, scope, or document the checkout experience for a Salesforce B2B or D2C Commerce storefront before any implementation begins. It covers runtime model selection, UX step design, payment option scoping, shipping rule definition, and guest versus registered buyer experience planning. It does not cover implementation: Apex adapter code, CartCheckoutSession debugging, Extension Point class registration, or Flow Builder element configuration are handled by `commerce-checkout-configuration`.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Store template type.** The single most consequential design decision is whether the store uses the LWR template (Managed Checkout) or the Aura template (Flow Builder checkout). These are mutually exclusive runtime models with entirely different customization surfaces. If the store template has not yet been chosen, this skill must help make that selection first — everything else flows from it.
- **Buyer personas.** Confirm whether the storefront will serve registered authenticated buyers, guest (unauthenticated) buyers, or both. Guest checkout requires different data collection requirements at every step and imposes additional platform permissions that must be planned for.
- **Payment landscape.** Identify all payment methods the business needs to support at launch and near-term. Each non-native payment method requires a custom Apex Payment Adapter. Knowing the full list upfront prevents surprise scope additions mid-build.
- **Shipping model.** Determine whether shipping rates come from an external carrier API, a flat rate table, free shipping with conditions, or a mix. External carrier rate calls introduce async latency constraints that must be accounted for in the UX design.
- **B2B-specific concerns.** B2B Commerce introduces purchase order (PO) payment, account-level pricing, and optional buyer approval workflows before order submission. These are design concerns that must be scoped before configuration begins.

---

## Core Concepts

### LWR Managed Checkout vs. Aura Flow Builder Checkout

Salesforce Commerce supports exactly two checkout runtime models. They are mutually exclusive — a store can only use one, and migrating between them requires a full storefront rebuild with no automated migration path.

**LWR Managed Checkout** (current strategic path for new stores):
- The platform manages the CartCheckoutSession state machine automatically.
- Custom behavior is injected at defined Extension Points via registered Apex classes.
- No Flow Builder is involved. Checkout configuration surfaces are in the Commerce App in Setup.
- The checkout UX is rendered by platform-managed LWC components. Custom UI steps require building custom LWC extensions against the Extension Point contracts.
- Best suited to net-new stores where the team can invest in the LWC-based extension model.

**Aura Flow Builder Checkout** (supported, not recommended for new stores):
- The checkout experience is driven by a declarative Salesforce Flow in Experience Builder.
- The standard managed package ships a Flow template. Merchants clone it and add or rearrange steps.
- Custom UI elements are added as screens or actions within the Flow.
- No Extension Point classes are involved. Configuration lives entirely inside Experience Builder.
- Best suited to existing Aura stores where the team has invested in Flow-based customization.

The design implication: every UX requirement that involves a custom step or custom data collection must be mapped to the available customization surface of the chosen runtime model before any work begins.

### Checkout Step Sequence and Required Data

Regardless of runtime model, the underlying CartCheckoutSession moves through the same canonical steps: cart validation → inventory check → pricing recalculation → shipping method selection → tax calculation → payment authorization → order creation. Each step has required data that must be collected from the buyer and present in the cart record before that step can execute.

Design must account for:
- What data is collected at each UX step and which Salesforce field it maps to
- Whether data from a previous step must persist into the current step (e.g., delivery address collected at shipping step must remain set when tax and payment steps execute)
- What happens when a step fails (e.g., insufficient inventory, declined payment) — the UX must surface the error and allow retry without losing previously entered data

### Guest vs. Registered Buyer Experience

Guest checkout allows unauthenticated buyers to complete a purchase without creating an account. The platform does not have a user session to draw contact data from, which has significant design implications:

- The checkout UX must explicitly collect `Email` and `Phone` at the address step. These must be written to the `CartDeliveryGroup` record before order creation executes. If they are not collected, the resulting Order Contact record is created with null values — silently.
- Billing address fields (`BillingStreet`, `BillingCity`, `BillingPostalCode`, `BillingState`, `BillingCountry`) must be explicitly set on the `WebCart` record. There is no automatic derivation from the guest session.
- Guest buyers require a specific set of object-level permissions assigned to the Guest User profile. These permissions must be identified in the design phase so that security review can happen before go-live.
- The "same as shipping" billing address option common in consumer checkout requires explicit field mapping logic — it does not happen automatically on the platform.

Registered buyer checkout can pre-populate address fields from the buyer's saved addresses if the storefront is wired to do so, but this is an opt-in design decision with its own UX implications (address book management, default address selection).

### Payment Option Design Constraints

Salesforce Commerce does not have a native payment gateway connector. Every payment method requires an Apex Payment Adapter class implementing `sfdc_checkout.CartPaymentAuthorize`. Design must account for:

- **Supported methods at launch.** Each distinct payment method (credit card, ACH, PO, invoice net terms) is a separate integration decision. Credit card requires client-side tokenization (e.g., Stripe Elements, Adyen Drop-in) before any Salesforce data is touched — storing raw card data in Salesforce violates PCI-DSS and is architecturally impossible on the platform.
- **Payment method fallback UX.** What happens when a card is declined? The design must specify whether the buyer is offered a retry, an alternative payment method, or a saved-method selection.
- **B2B-specific payment options.** Purchase order payment is common in B2B scenarios. PO payment does not require real-time authorization but may trigger a buyer approval workflow before the order is confirmed. This must be designed as a distinct flow branch, not retrofitted onto a card payment flow.

---

## Common Patterns

### Pattern: LWR Store with Single Payment Method (Credit Card)

**When to use:** Net-new D2C or B2B store on LWR template with a single payment gateway and no buyer approval workflow.

**How it works:**
1. Confirm LWR template is selected or recommended. Document that Flow Builder checkout configuration has no effect on this store.
2. Map the standard checkout steps: cart review → address entry (with explicit email/phone collection for guest users) → shipping method selection → order review → payment entry → confirmation.
3. Identify the payment gateway and confirm client-side tokenization is available (Stripe Elements, Adyen Drop-in, Braintree Hosted Fields). Card data never enters Salesforce — only the token does.
4. Define the decline UX: buyer is shown an error message and can re-enter payment details. The CartCheckoutSession is reset via the Checkout API; a new session starts from the payment step.
5. Document that the shipping step triggers an async callout to the registered shipping/tax service. UX must show a loading indicator while rates are fetched.

**Why not the alternative:** Designing for Aura Flow Builder checkout on an LWR store produces configuration that has zero effect. Confirming the template type before any UX work begins prevents wasted design cycles.

### Pattern: Aura Store with Guest and Registered Buyer Experience

**When to use:** Existing Aura store that needs to support both unauthenticated guest purchasers and registered account buyers with saved addresses.

**How it works:**
1. Design two distinct checkout paths that share the same underlying Flow template but branch on buyer authentication state.
2. For guest path: address step must include email and phone fields mapped explicitly to `CartDeliveryGroup.Email` and `CartDeliveryGroup.Phone`. Design a "same as shipping" toggle that copies address fields to `WebCart` billing fields.
3. For registered path: pre-populate address from buyer's saved address book. Provide an "add new address" option that also writes to billing fields.
4. Payment step is identical for both paths assuming the same payment method is supported for both. If PO is only available to registered buyers, add a conditional Flow branch that checks authentication state.
5. Define the order confirmation experience for each path: guest buyers receive a confirmation email (requires email collection above); registered buyers see the order in their account order history.

**Why not the alternative:** Treating guest and registered paths as identical produces silent data gaps — null Contact fields on guest orders, missed email confirmations, and broken fulfillment integrations.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New store, greenfield project | Use LWR template with Managed Checkout | LWR is the strategic direction; new Extension Point model is more maintainable than custom Flow |
| Existing Aura store with heavy Flow investment | Stay on Aura Flow Builder checkout | Migration requires full storefront rebuild; no automated migration path exists |
| Need guest checkout | Design explicit email/phone collection in address step | Platform does not derive these from guest session; null Contact fields result if omitted |
| Multiple payment methods required | Design each as a separate adapter; scope Apex development per method | Each method is a distinct Apex integration; payment method count directly drives development scope |
| B2B store with PO payment and approval | Design PO as a distinct flow branch with approval step | PO payment has no real-time authorization; mixing it with card flow path creates state machine ambiguity |
| Shipping rates from external carrier | Design async loading UX with error fallback | Shipping rate call is async; UX must handle latency and callout failure gracefully |
| Compliance or PCI-DSS concerns | Confirm client-side tokenization for all card methods | No raw card data may enter Salesforce; tokenization must happen at the client before any API call |
| D2C with free shipping threshold | Design conditional free shipping as a cart-level rule | Free shipping thresholds are evaluated against cart total; design must specify the threshold and currency behavior |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner designing a Commerce checkout experience:

1. **Confirm or select the store template type.** Establish definitively whether the store uses LWR (Managed Checkout) or Aura (Flow Builder checkout). If the store does not yet exist, make a runtime model recommendation using the decision table above. Document the chosen model as a locked constraint — all subsequent design steps depend on it.

2. **Map the buyer personas and authentication states.** Define whether the checkout must serve guest buyers, registered buyers, or both. For each persona, document what identity and address data is available from the session and what must be explicitly collected in the UX. Flag guest checkout as requiring platform permission configuration that must happen before testing.

3. **Design the checkout step sequence.** List every step in order. For each step, specify: what the buyer sees, what data they enter, what Salesforce object field that data maps to, and what platform action triggers at the end of the step. Explicitly mark steps that trigger async platform calls (shipping/tax) so the UX design accounts for loading states.

4. **Scope all payment methods.** List every payment method the business requires at launch. For each: confirm client-side tokenization availability for card methods, identify whether a custom Apex adapter is required, and document the decline or failure UX. For B2B stores, determine whether PO payment needs a buyer approval branch.

5. **Define shipping rules.** Specify the rate source (external carrier API, flat rate, free shipping), any free-shipping thresholds, and behavior for multiple delivery groups (split shipments). Document the external service endpoint if applicable and note that a callout failure must be handled gracefully in the UX.

6. **Identify design constraints and custom development scope.** For the chosen runtime model, document what cannot be configured declaratively and will require custom Apex or LWC development. This is the handoff document to the implementation team — it defines the boundary between this design skill and `commerce-checkout-configuration`.

7. **Review design against the Well-Architected pillars.** Confirm that security (PCI-DSS, guest user permissions, no raw card data), reliability (async callout failure handling, session reset on decline), and adaptability (runtime model lock-in implications) are explicitly addressed before handing off to implementation.

---

## Review Checklist

Run through these before marking design work complete:

- [ ] Store template type confirmed and documented as a locked constraint (LWR Managed Checkout or Aura Flow Builder)
- [ ] Guest vs. registered buyer experience branching documented; email/phone collection required fields identified for guest path
- [ ] Checkout step sequence mapped with Salesforce object field mappings for every data collection point
- [ ] All payment methods listed; client-side tokenization confirmed for any card method; custom Apex adapter scope identified
- [ ] Shipping rule source defined; async loading UX and callout failure behavior specified
- [ ] B2B-specific requirements (PO payment, approval workflows, account pricing) addressed if applicable
- [ ] Design constraints document completed: what the runtime model cannot do, what requires custom development
- [ ] PCI-DSS scope confirmed: no raw card data enters any Salesforce field or API payload

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Runtime model selection is permanent without a full rebuild** — LWR stores cannot be converted to Aura stores and vice versa. There is no migration tool or hybrid mode. A team that begins design work assuming they can switch models later will face a complete rebuild if they change direction. The design phase is the last low-cost opportunity to make this decision.

2. **Guest checkout email and phone are not automatically populated** — For unauthenticated buyers, Salesforce has no user session from which to derive contact data. If the UX design does not include explicit fields for email and phone mapped to `CartDeliveryGroup`, the resulting Order Contact is created with null values and no error is thrown. This breaks order confirmation emails and fulfillment integrations silently.

3. **Billing address must be explicitly mapped from the shipping address** — The "same as shipping" billing address pattern common in consumer UX does not happen automatically. The design must include explicit logic to copy `BillingStreet`, `BillingCity`, `BillingPostalCode`, `BillingState`, and `BillingCountry` from the delivery address to the `WebCart` record. Missing billing fields produce an `OrderSummary` with a null billing contact at order creation.

4. **Shipping and tax steps trigger a single combined async callout** — From a UX design perspective, shipping method selection and tax calculation are not two separate user-visible steps that can be independently retried. They share one async platform job. A design that shows separate "calculate shipping" and "calculate tax" buttons does not map to how the platform actually works and will require significant workarounds to implement.

5. **Extension Points and Flow Builder checkout are mutually exclusive configuration surfaces** — LWR stores using Managed Checkout cannot use Flow Builder to add custom checkout steps, and Aura stores using Flow Builder cannot use Extension Point classes for custom behavior. Designs that reference both surfaces as options for the same store are not implementable.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Runtime model selection document | Confirmed choice of LWR Managed Checkout or Aura Flow Builder with rationale and implications |
| Checkout step map | Ordered list of buyer-facing steps with Salesforce field mappings and async trigger points |
| Guest vs. registered experience matrix | Documents what differs per buyer type, required fields, and platform permissions needed |
| Payment options design spec | Lists all payment methods, tokenization approach, decline UX, and custom Apex scope per method |
| Shipping rules design spec | Rate source, free shipping rules, multi-delivery-group behavior, and callout failure UX |
| Design constraints document | What the chosen runtime model cannot do declaratively; handoff doc to implementation team |

---

## Related Skills

- commerce-checkout-configuration — Implementation counterpart: configures CartCheckoutSession, registers Extension Points, writes Apex adapters, and debugs the running checkout
- commerce-store-setup — Establishes the store catalog, price books, and entitlements that checkout depends on
- commerce-pricing-and-promotions — Defines the promotion and pricing rules that are recalculated during the pricing step of checkout
