# Examples — Commerce Checkout Flow Design

## Example 1: Selecting LWR vs. Aura at Project Kickoff for a D2C Fashion Store

**Context:** A D2C retailer is launching a new Salesforce Commerce storefront from scratch. The project team is evaluating whether to use the LWR template with Managed Checkout or the Aura template with Flow Builder checkout. The business requires guest checkout, credit card payment via Stripe, and free shipping on orders over $75.

**Problem:** Without a deliberate runtime model decision at the design phase, the team risks starting configuration work on the wrong surface — for example, building a custom checkout Flow in Experience Builder and later discovering the store is on an LWR template, where the Flow has no effect at all.

**Solution:**

The design session produces the following runtime model selection document:

```
Runtime Model: LWR Managed Checkout
Reason: Net-new store. No existing Flow investment. Team has Apex developers
  available for Extension Point customization. LWR is the strategic path for
  new stores per Salesforce roadmap.

Implications locked as constraints:
  - No checkout Flow in Experience Builder will have any effect on this store.
  - Custom checkout steps require LWC components registered against Extension Points.
  - Checkout configuration surfaces: Commerce App in Setup → Checkout settings.
  - Migration back to Aura requires full storefront rebuild. Decision is final.
```

The checkout step map produced for the LWR store:

```
Step 1: Cart Review
  Buyer action: Review items, quantities, prices
  Salesforce record: WebCart + CartItem
  No async trigger

Step 2: Address Entry (guest and registered)
  Buyer action: Enter shipping address
  Guest path: Collect Email + Phone explicitly
  Field mappings:
    CartDeliveryGroup.Street → ShippingStreet
    CartDeliveryGroup.City → ShippingCity
    CartDeliveryGroup.PostalCode → ShippingPostalCode
    CartDeliveryGroup.State/Province → ShippingState
    CartDeliveryGroup.Country → ShippingCountry
    CartDeliveryGroup.Email → Email (guest only — no session default)
    CartDeliveryGroup.Phone → Phone (guest only — no session default)
  Note: "Same as billing" toggle must explicitly copy these to
    WebCart.BillingStreet, WebCart.BillingCity, etc.

Step 3: Shipping Method Selection
  Platform async callout to registered shipping/tax service triggers here.
  UX must show loading indicator. Callout failure must surface user-friendly error.
  Result: CartDeliveryGroupMethod records created with available rates.
  Free shipping rule: if WebCart.GrandTotalAmount >= 75, inject $0 shipping method.

Step 4: Order Review
  Buyer action: Confirm items, shipping method, address, totals

Step 5: Payment Entry
  Stripe Elements rendered client-side. Card tokenized before any Salesforce call.
  Token passed to CartCheckoutSession via Commerce Checkout API.
  Decline UX: buyer shown error, offered retry. Session reset via DELETE /checkouts/{id}.

Step 6: Order Confirmation
  Order and OrderSummary created. Guest buyer receives confirmation email
  (requires email collected in Step 2 to be non-null).
```

**Why it works:** Locking the runtime model as a design constraint before any configuration or development begins eliminates the most common and costly checkout project failure mode — building on the wrong customization surface.

---

## Example 2: Designing a B2B Checkout with PO Payment and Buyer Approval

**Context:** A B2B wholesale distributor is adding a Commerce storefront for their dealer network. Dealers are registered buyers with account-based pricing. The business requires both credit card and purchase order (PO) payment options. PO orders above $10,000 must be routed through an internal approval workflow before the order is confirmed.

**Problem:** Treating PO payment as a variant of credit card payment — using the same checkout flow branch with a different payment adapter — produces a broken UX. PO payment has no real-time authorization step, and approval workflows need to pause order creation, not run after it.

**Solution:**

The payment options design spec for this store:

```
Payment Method 1: Credit Card
  Tokenization: Braintree Hosted Fields (client-side)
  Raw card data: NEVER enters Salesforce. Token only.
  Adapter: Custom Apex class implementing sfdc_checkout.CartPaymentAuthorize
  Decline UX: Error message + retry option. Session reset on retry.
  PCI-DSS scope: Braintree handles card data; Salesforce receives token only.

Payment Method 2: Purchase Order (PO)
  Tokenization: N/A — PO payment has no real-time authorization.
  Adapter: Custom Apex class that captures PO number and returns authorized=true
    immediately (authorization is deferred to accounts receivable review).
  Approval workflow: For PO orders >= $10,000, a Platform Event fires at order
    creation. The order status is set to "Pending Approval". An Approval Process
    routes it to the buyer's account manager. Order fulfillment is blocked until
    approval is granted.
  UX branch: PO payment step collects PO number field only. No card entry form.
    Buyer sees "Your order is pending approval" confirmation page, not the
    standard confirmation.

Flow branch design:
  [Cart Review] → [Address + Shipping] → [Payment Method Selection]
      ↓                                        ↓
  [Credit Card: Tokenized entry]       [PO: PO number entry]
      ↓                                        ↓
  [Real-time authorization]           [PO capture; approval trigger if >= $10k]
      ↓                                        ↓
  [Standard confirmation]            [Pending approval confirmation]
```

**Why it works:** Designing PO and card payment as explicitly separate flow branches — each with its own UX, data collection, and confirmation state — prevents the state machine from being put in an ambiguous position (e.g., triggering a card authorization step against a PO number). The approval threshold and workflow trigger are specified in the design, ensuring the implementation team knows exactly what to build before any code is written.

---

## Anti-Pattern: Assuming LWR and Aura Checkout Are Configurable from the Same Surface

**What practitioners do:** A designer documents checkout customization requirements without confirming the store template type, using generic language like "add a custom step to the checkout flow." The implementation team receives the spec and begins building in Experience Builder's Flow editor.

**What goes wrong:** If the store is on an LWR template, every modification made in the Flow editor in Experience Builder has no effect on the running checkout. The custom step never appears. The team spends time building, testing, and debugging configuration that is silently ignored by the platform.

**Correct approach:** The first item in the checkout design session must be explicit runtime model confirmation. The spec must state the model by name, document what the customization surface is for that model (Commerce App in Setup for LWR; Experience Builder Flow for Aura), and explicitly note that configuration intended for the other model will have no effect. If the team does not know the store template type, confirm it in the Commerce App in Setup before writing any requirements.
