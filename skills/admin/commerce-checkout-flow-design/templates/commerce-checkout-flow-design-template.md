# Commerce Checkout Flow Design — Work Template

Use this template when designing or documenting the checkout experience for a Salesforce B2B or D2C Commerce storefront. Complete all sections before handing off to implementation.

---

## Scope

**Skill:** `commerce-checkout-flow-design`

**Store name / project:** (fill in)

**Request summary:** (describe what the business is asking for — e.g., "Design checkout for a new D2C fashion store with guest checkout and Stripe payment")

---

## 1. Runtime Model Selection

**Store template type confirmed:** [ ] LWR (Managed Checkout)   [ ] Aura (Flow Builder)   [ ] Not yet determined

**How confirmed:** (e.g., checked in Commerce App in Setup → Experience Cloud Site template shows "B2C Lite Store / LWR")

**Selection rationale:**
- New store or existing?: 
- Team has Apex development capacity?: 
- Existing Flow investment to preserve?: 
- Strategic direction per roadmap: LWR is the strategic path for new stores

**Locked constraint:** The chosen runtime model determines every customization surface. Changing it requires a full storefront rebuild.

> **LWR stores:** customization via Extension Points in Commerce App in Setup. Flow Builder checkout has no effect.
> **Aura stores:** customization via checkout Flow in Experience Builder. Extension Point classes have no effect.

---

## 2. Buyer Persona and Authentication Matrix

| Persona | Authentication | Notes |
|---|---|---|
| Guest buyer | Unauthenticated | Must explicitly collect Email + Phone at address step |
| Registered buyer | Authenticated | Can pre-populate address from account; has order history |
| (Add rows as needed) | | |

**Guest checkout enabled?** [ ] Yes   [ ] No

**If yes — required fields for guest path (must be in UX spec):**
- [ ] `CartDeliveryGroup.Email` — collected at address step (no session default)
- [ ] `CartDeliveryGroup.Phone` — collected at address step (no session default)
- [ ] Guest User profile permissions reviewed and assigned

---

## 3. Checkout Step Map

For each step: describe what the buyer sees, what data they enter, where it maps in Salesforce, and what platform action triggers at the end.

| Step | Buyer Action | Salesforce Object/Fields | Platform Trigger |
|---|---|---|---|
| 1. Cart Review | Review items, quantities, prices | WebCart, CartItem | None |
| 2. Address Entry | Enter shipping address (+ email/phone for guest) | CartDeliveryGroup.Street/City/PostalCode/State/Country/Email/Phone | None |
| 3. Billing Address | Enter billing address or select "same as shipping" | WebCart.BillingStreet/BillingCity/BillingPostalCode/BillingState/BillingCountry | None (explicit mapping required — not automatic) |
| 4. Shipping Selection | Select shipping method from available rates | CartDeliveryGroupMethod | Async shipping + tax callout triggered by address entry |
| 5. Order Review | Confirm all details before payment | (display only) | None |
| 6. Payment Entry | Enter payment details | CartCheckoutSession.paymentMethod (token only, never raw card data) | Payment authorization via Apex adapter |
| 7. Confirmation | View order confirmation | Order, OrderSummary | Order creation |

**Add or remove rows as needed. Do not combine async-triggered steps (shipping/tax) into a single user action without specifying the loading state UX.**

---

## 4. Payment Options Design

For each payment method the business requires:

### Payment Method: _______________

- **Type:** [ ] Credit/Debit Card   [ ] Purchase Order   [ ] ACH   [ ] Invoice   [ ] Other: ___
- **Tokenization required?** [ ] Yes (client-side via: _______________)   [ ] No (non-card method)
- **PCI-DSS note:** Raw card data must never enter Salesforce. Tokenization must occur at the client before any Salesforce API call.
- **Custom Apex adapter required?** [ ] Yes   [ ] No
- **Decline / failure UX:**
  - Error message shown to buyer: (describe)
  - Session reset required: [ ] Yes (via DELETE /checkouts/{id})   [ ] N/A
  - Retry allowed: [ ] Yes   [ ] No
- **B2B approval workflow needed?** [ ] Yes (threshold: _______________)   [ ] No

*(Duplicate this section for each additional payment method)*

---

## 5. Shipping Rules Design

- **Rate source:** [ ] External carrier API   [ ] Flat rate   [ ] Free shipping   [ ] Combination
- **External service endpoint (if applicable):** _______________
- **Free shipping threshold (if applicable):** Cart total >= _______________   Currency: _______________
- **Multiple delivery groups / split shipments supported?** [ ] Yes   [ ] No
- **Async loading UX:** The shipping/tax callout is async. UX must show a loading indicator while rates are fetched.
- **Callout failure UX:** If the shipping/tax service times out or errors, the CartCheckoutSession pauses at the Shipping state. Buyer must see a user-friendly error with a retry option (not a blank or hung step).
- **Tax calculation method:** [ ] Avalara (native integration)   [ ] Vertex (native integration)   [ ] Custom Apex provider   [ ] None

---

## 6. B2B-Specific Requirements (Complete if B2B store)

- **Account-based pricing in use?** [ ] Yes   [ ] No
- **Purchase Order (PO) payment required?** [ ] Yes   [ ] No
- **Buyer approval workflow for PO orders?** [ ] Yes (threshold: _______________)   [ ] No
- **Contract pricing / entitlement enforcement at checkout?** [ ] Yes   [ ] No
- **Multi-account / buyer account selection at checkout?** [ ] Yes   [ ] No

---

## 7. Design Constraints and Custom Development Scope

Document what the chosen runtime model cannot do declaratively and what requires custom development. This is the handoff to the implementation team.

| Requirement | Declarative? | Custom Development Needed | Notes |
|---|---|---|---|
| (e.g., Custom address validation step) | No | Apex Extension Point (LWR) or Flow Screen (Aura) | (notes) |
| (e.g., Stripe credit card payment) | No | Apex Payment Adapter class | sfdc_checkout.CartPaymentAuthorize |
| (e.g., Free shipping conditional logic) | Partially | Cart calculation Apex or Flow decision | (notes) |
| (Add rows as needed) | | | |

---

## 8. Review Checklist

- [ ] Runtime model confirmed and documented as a locked constraint
- [ ] Guest vs. registered path documented; email/phone collection required fields identified
- [ ] Checkout step sequence mapped with Salesforce field mappings for every data input
- [ ] "Same as shipping" billing address: explicit WebCart field mapping specified (not assumed automatic)
- [ ] All payment methods listed; tokenization confirmed for card methods; Apex adapter scope identified
- [ ] Shipping rule source defined; async loading UX and callout failure handling specified
- [ ] B2B requirements (PO payment, approval, account pricing) addressed if applicable
- [ ] Design constraints documented; custom development scope quantified
- [ ] PCI-DSS scope confirmed: no raw card data enters any Salesforce field or API payload

---

## 9. Notes and Deviations

(Record any requirements that do not fit the standard patterns documented in SKILL.md, and explain why.)
