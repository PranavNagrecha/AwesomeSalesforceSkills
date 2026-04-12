# Well-Architected Notes — Commerce Checkout Flow Design

## Relevant Pillars

- **Security** — Checkout design is the primary point where PCI-DSS scope is established. Decisions made at design time determine whether raw card data ever touches Salesforce infrastructure. Client-side tokenization must be specified as a design requirement, not left as an implementation detail. Guest checkout also introduces security concerns: the Guest User profile must be granted only the minimum permissions required to complete an order, and this permission set must be reviewed during design before any configuration begins.

- **Reliability** — The checkout flow includes async platform callouts for shipping/tax that can fail silently. Design must explicitly specify error states, loading indicators, and fallback behavior for every step that triggers a backend call. Payment decline UX must specify session reset behavior rather than assuming a simple retry is sufficient. Designs that do not account for async failure modes produce storefronts that appear broken to buyers when callout failures occur.

- **Adaptability** — The runtime model selection (LWR vs. Aura) is the most consequential adaptability decision in any Commerce project. LWR Managed Checkout locks the team into the Extension Point customization model; Aura Flow Builder checkout locks the team into declarative Flow customization. Neither model is extensible toward the other without a full rebuild. Checkout design must document this lock-in explicitly so that future business requirements can be evaluated against the constraints of the chosen model before they are committed to.

- **Performance** — Async shipping and tax callouts introduce buyer-visible latency. Design must include loading state UX for the shipping/tax step. External service SLAs must be evaluated against the platform's async callout timeout window at design time. Designs that ignore latency produce shipping steps that appear to hang for buyers while the platform waits for a slow carrier rate API.

- **Operational Excellence** — Checkout is a revenue-critical flow. Designs must specify testability: end-to-end test scenarios for guest buyers, registered buyers, card declines, and shipping callout failures must be identified during design. Test coverage decisions made at design time determine what can be caught before go-live versus discovered in production.

## Architectural Tradeoffs

**LWR Managed Checkout vs. Aura Flow Builder Checkout**

LWR Managed Checkout is the strategic path for new stores and provides a cleaner separation between platform orchestration and custom logic via the Extension Point model. Custom behavior is Apex-only — more maintainable and testable than declarative Flow logic, but requires Apex development capacity. Aura Flow Builder checkout provides a lower barrier to declarative customization and is the right choice for teams with heavy Flow investment or existing Aura stores, but it carries the risk of complex, hard-to-maintain Flow sprawl in the checkout experience.

The tradeoff: LWR is higher upfront investment, lower long-term maintenance cost. Aura is lower upfront investment, higher long-term maintenance cost as the Flow grows.

**Guest Checkout vs. Registered-Only**

Enabling guest checkout increases reach (no account creation barrier) but introduces data quality risk (null Contact fields if email/phone are not collected) and requires additional platform permissions configuration. Registered-only checkout simplifies the design but may reduce conversion for first-time buyers. The design must weigh these tradeoffs explicitly before committing to a guest checkout requirement.

**Single Payment Method vs. Multiple Payment Methods**

Each additional payment method is a distinct custom Apex adapter integration. Design must quantify the development scope per payment method so that the business understands the cost of adding payment methods. Designs that treat "we'll add more payment methods later" as a low-cost decision underestimate the per-method adapter development and testing burden.

## Anti-Patterns

1. **Designing Without Confirming the Runtime Model** — Any checkout UX design that does not begin by locking the LWR vs. Aura decision is incomplete. Every customization requirement — custom steps, custom UI, custom logic — has a different implementation surface depending on the runtime model. A design that uses generic language like "add a custom checkout step" without specifying whether that means an Extension Point class or a Flow element cannot be implemented without additional design work. This wastes the implementation team's time and creates alignment risk.

2. **Treating PCI-DSS Scope as an Implementation Concern** — Raw card data handling must be addressed in the design phase. If the design specifies "collect credit card details at payment step" without specifying that client-side tokenization is required and that the Stripe/Adyen/Braintree SDK handles this before any Salesforce API is called, the implementation team may build a solution where card data flows through Salesforce infrastructure, which violates PCI-DSS and requires redesign. PCI-DSS scope is a design constraint, not an implementation detail.

3. **Ignoring the Async Callout Failure State in Shipping UX** — Designs that model shipping method selection as a simple dropdown selection without specifying what happens when the async callout to the shipping service fails produce storefronts that display a blank or hung shipping step. Buyers cannot proceed and the UX provides no actionable guidance. Every async-triggered step must have an explicit error state and buyer recovery path in the design.

## Official Sources Used

- B2B Commerce and D2C Commerce Developer Guide — Checkout Flow: https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2c_comm_dev_checkout.htm
- B2B Commerce Checkout Flow (Aura) — Salesforce Developer Documentation: https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2c_comm_dev_checkout_aura.htm
- Set Up Guest Checkout for Headless Commerce Stores: https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2c_comm_dev_checkout_guest.htm
- Payment Architecture — Commerce Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2c_comm_dev_payment_architecture.htm
- Shipping and Tax Integration — Commerce Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2c_comm_dev_shipping_tax.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
