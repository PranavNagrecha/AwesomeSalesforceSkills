# Commerce Checkout Configuration — Work Template

Use this template when configuring or debugging Salesforce B2B or D2C Commerce checkout for a specific org or storefront.

---

## Scope

**Skill:** `commerce-checkout-configuration`

**Request summary:** (fill in the specific checkout task — e.g., "configure Stripe payment adapter for LWR store," "debug stuck CartCheckoutSession at shipping state," "enable guest checkout for headless storefront")

---

## Context Gathered

Answer these questions before taking any action:

- **Store template type:** [ ] LWR (Managed Checkout)   [ ] Aura (Flow Builder checkout)
- **Store name / webstore ID:**
- **Payment gateway:** (e.g., Stripe, Adyen, Braintree, custom)
- **Guest checkout required:** [ ] Yes   [ ] No
- **Shipping/tax provider:** [ ] Avalara   [ ] Vertex   [ ] Custom Apex   [ ] External service
- **Current issue / symptom:** (e.g., "checkout stops at shipping step," "OrderSummary missing billing address")
- **Sandbox / scratch org name where this will be validated:**

---

## CartCheckoutSession Diagnostic (if debugging a stuck session)

```soql
-- Run this in Developer Console or VS Code SOQL tab to identify stuck sessions
SELECT Id, Name, State, Status, WebCartId, CreatedDate, LastModifiedDate
FROM CartCheckoutSession
WHERE WebCart.OwnerId = '<buyer user ID>'
ORDER BY CreatedDate DESC
LIMIT 5
```

```soql
-- Check CartValidationOutput for the session
SELECT Id, CartId, Message, Level, Type, CreatedDate
FROM CartValidationOutput
WHERE CartId = '<WebCart ID>'
ORDER BY CreatedDate DESC
LIMIT 20
```

Record findings here:
- Current session state:
- CartValidationOutput messages:
- Root cause identified:

---

## Configuration Steps

### Step 1 — Confirm Store Template Type

- [ ] Navigate to Commerce App in Setup > Stores > [Store Name] > Experience Site
- [ ] Confirm template type: LWR or Aura
- [ ] Record template type in Context Gathered above

### Step 2 — Shipping and Tax Provider

- [ ] Navigate to Commerce Setup > [Store] > Shipping and Tax
- [ ] Confirm provider registration: (name provider here)
- [ ] Test with a sample address in a scratch or sandbox checkout
- [ ] Verify `CartDeliveryGroupMethod` records are created after address entry:

```soql
SELECT Id, Name, Carrier, ClassOfService, ShippingFee
FROM CartDeliveryGroupMethod
WHERE CartDeliveryGroupId IN (
    SELECT Id FROM CartDeliveryGroup WHERE CartId = '<WebCart ID>'
)
```

- [ ] Results: (record shipping method names and fees returned)

### Step 3 — Payment Adapter

- [ ] Apex adapter class name:
- [ ] Implements `sfdc_checkout.CartPaymentAuthorize`: [ ] Yes   [ ] No
- [ ] All gateway failure paths return `setAuthorized(false)` (no throws): [ ] Verified
- [ ] Registered in Commerce Setup > Payment: [ ] Yes   [ ] No
- [ ] Named Credential used for gateway callout: (credential name here)
- [ ] Unit test coverage includes: happy path, declined authorization, gateway timeout mock

### Step 4 — Billing Address on WebCart

- [ ] Confirm the storefront component or Checkout API call sets billing fields before submission
- [ ] Run a test checkout and verify:

```soql
SELECT BillingStreet, BillingCity, BillingState, BillingPostalCode, BillingCountry
FROM WebCart
WHERE Id = '<WebCart ID>'
```

- [ ] All billing fields are non-null after address entry: [ ] Yes   [ ] No

### Step 5 — Guest Checkout (if applicable)

- [ ] Guest Browsing enabled on Experience Site: [ ] Yes   [ ] No
- [ ] Guest user profile has read/write on: WebCart, CartItem, CartDeliveryGroup, CartCheckoutSession, WebOrder
- [ ] Storefront collects email and phone from guest buyer at address entry
- [ ] Delivery address API call includes `email` and `phone` in the payload: [ ] Verified
- [ ] Run a guest checkout end to end and verify:

```soql
SELECT BillToContactId, BillToContact.Email, BillToContact.Phone
FROM Order
WHERE Id = '<Order ID>'
```

- [ ] BillToContact is non-null: [ ] Yes   [ ] No
- [ ] BillToContact.Email matches what buyer entered: [ ] Yes   [ ] No

### Step 6 — Post-Checkout Order Verification

- [ ] Order record created: ID:
- [ ] OrderSummary record created: ID:
- [ ] Billing address on OrderSummary is correct: [ ] Yes   [ ] No
- [ ] Shipping method and cost on OrderDeliveryGroup are correct: [ ] Yes   [ ] No
- [ ] Payment authorization reference recorded (custom field or standard field): [ ] Yes   [ ] No

---

## Deviations from Standard Pattern

(Record any decisions made that differ from the SKILL.md recommended workflow and why)

---

## Final Checklist

- [ ] Store template type confirmed before configuration began
- [ ] CartCheckoutSession tested end to end in sandbox or scratch org
- [ ] Payment adapter tested: happy path + decline + gateway error
- [ ] Billing address non-null on OrderSummary after test checkout
- [ ] Guest checkout email/phone verified on Order Contact (if applicable)
- [ ] CartValidationOutput surfaced to storefront for buyer-visible error messages
- [ ] No raw card data referenced in any Apex or LWC file
- [ ] Apex payment adapter and shipping/tax provider have unit test coverage with mocked callouts
