---
name: b2b-vs-b2c-architecture
description: "Use this skill when designing or evaluating the architecture of a Salesforce Commerce implementation that involves choosing between B2B Commerce (on Core, Lightning platform) and B2C Commerce (Salesforce Commerce Cloud / SFCC). Trigger keywords: B2B vs B2C architecture, SFCC vs B2B Commerce, Commerce Cloud platform decision, B2B data model architecture, B2C storefront architecture, commerce infrastructure comparison, platform selection architecture. NOT for implementation mechanics — use admin/b2b-commerce-store-setup or admin/b2c-commerce-store-setup for configuration work. NOT for requirements gathering — use admin/b2b-vs-b2c-requirements for pre-build platform selection based on buyer journey. NOT for D2C vs B2B feature comparisons within Lightning-based Commerce."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Scalability
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "how do B2B Commerce on Core and Salesforce B2C Commerce differ architecturally and what are the integration implications"
  - "we are building a commerce solution and need to understand the infrastructure, data model, and extensibility differences between B2B Commerce and SFCC before committing to a platform"
  - "our team is debating whether to use Salesforce B2B Commerce with CRM integration or deploy Salesforce Commerce Cloud for high-volume consumer traffic"
  - "what objects and APIs does B2B Commerce expose on the Core platform compared to what SFCC exposes through its REST APIs"
  - "explain the checkout customization model for B2B Commerce (Flow Builder) versus B2C Commerce (SFRA cartridges) and how that affects our DevOps pipeline"
tags:
  - commerce-cloud
  - B2B
  - B2C
  - architecture
  - platform-selection
  - sfcc
  - webstore
  - sfra
  - integration-architecture
  - data-model
inputs:
  - "Current commerce requirements: audience type, expected order volume, concurrent session estimate"
  - "Existing Salesforce org: licenses held, CRM data model (Accounts, Contacts, Leads), existing integrations"
  - "Customization needs: checkout flow, pricing engine, inventory, tax, shipping"
  - "Team capabilities: Apex/LWC/Flow experience vs. SFRA cartridge/JavaScript/Node.js experience"
  - "Integration requirements: OMS, ERP, PIM, payment processor, loyalty platform"
outputs:
  - "Architectural comparison document: infrastructure layer, data model layer, extensibility model, integration surface"
  - "Platform selection recommendation with rationale tied to non-functional requirements"
  - "Integration architecture diagram outline (B2B Commerce API surface vs. SFCC Open Commerce API surface)"
  - "Risk register: capability gaps, migration complexity, DevOps pipeline differences"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# B2B vs B2C Commerce Architecture

This skill activates when an architect or senior practitioner must evaluate the structural, data model, extensibility, and integration differences between Salesforce B2B Commerce (running on the Core Salesforce platform) and Salesforce B2C Commerce (Salesforce Commerce Cloud, SFCC), to make or validate a platform architecture decision. It does not cover implementation mechanics — those belong to the admin-domain skills for each platform.

---

## Before Starting

Gather this context before working in this domain:

- **Confirm which product family is actually in scope.** "Salesforce B2C Commerce" and "D2C Commerce" are not the same product. Salesforce B2C Commerce (also called SFCC or Commerce Cloud) runs on a separate, hosted infrastructure with its own servers, Business Manager admin console, and SFRA (Storefront Reference Architecture) cartridge customization model. D2C Commerce (also called Direct-to-Consumer or Lightning-based B2C Commerce) is a WebStore built on LWR inside the Core Salesforce platform. These are entirely different infrastructure stacks. The research notes for this skill concern B2B Commerce on Core versus SFCC — two platforms that share no objects, no APIs, and no org data.
- **Most common wrong assumption:** That Commerce Extensions (custom pricing, inventory, shipping, and tax services introduced in Winter '24) are available on both B2B/D2C Commerce and SFCC. Commerce Extensions are a B2B Commerce and D2C Commerce on Core feature only. SFCC has its own separate extensibility model (hooks, pipelines, SFRA cartridges, Commerce APIs). Recommending Commerce Extensions for an SFCC implementation is a category error.
- **Non-functional requirements drive the decision.** Volume (anonymous concurrent sessions, peak throughput), team skills (Apex/Flow vs. Node.js/cartridges), existing CRM investment, and OMS/ERP integration patterns are the primary architectural levers. The platforms are not interchangeable at scale.

---

## Core Concepts

### 1. Infrastructure Layer: Shared Core vs. Separate Hosted Platform

**B2B Commerce on Core** is a native Lightning platform application. It runs inside the same Salesforce org that houses CRM data (Accounts, Contacts, Opportunities, Orders). Storefront rendering uses the Lightning Web Runtime (LWR) and Experience Cloud. Customization uses Apex, LWC, and Flow. All commerce objects (`WebStore`, `BuyerGroup`, `CommerceEntitlementPolicy`, `OrderSummary`) are standard Salesforce objects in the same org database. Governance is through standard Salesforce governor limits: SOQL query limits, DML limits, CPU time limits per transaction.

**Salesforce B2C Commerce (SFCC)** is a separate, hosted platform with dedicated infrastructure. It has its own server environments (Primary Instance Group, sandbox instances), its own database, its own admin UI (Business Manager), and its own deployment model (cartridge uploads, code version activations). There is no Salesforce org, no SOQL, no Apex, no Flow. Customization uses SFRA (Storefront Reference Architecture) — a Node.js-based cartridge system — and the Business Manager extension framework. SFCC exposes data through its own Open Commerce API (OCAPI) and SCAPI (Shopper Commerce API), which are HTTP REST APIs with no relationship to Salesforce REST/SOAP APIs.

**Architectural implication:** CRM integration with SFCC is always an external integration (via connected app, OMS connector, or custom middleware). CRM integration with B2B Commerce on Core is zero-latency because both systems share the same org — there is no integration layer between the commerce objects and the CRM objects.

### 2. Data Model: CRM-Native Objects vs. SFCC-Proprietary Data Store

**B2B Commerce on Core data model (key objects):**
- `WebStore` — the storefront configuration record (one per storefront)
- `BuyerGroup` + `CommerceEntitlementPolicy` — account-gated catalog and pricing segmentation
- `BuyerAccount` / `BuyerGroupMember` — buyer identity and group membership
- `CartItem`, `CartDeliveryGroup`, `WebCart` — the active shopping cart object graph
- `OrderSummary`, `OrderItemSummary`, `FulfillmentOrder` — order lifecycle objects (Salesforce Order Management)
- Standard `PricebookEntry`, `Product2`, `ProductCatalog` objects — shared with CRM

Because these objects live in the Salesforce org, they are queryable via SOQL, accessible in Flow, triggerable with Apex, reportable in CRM Analytics, and available to any integration connected to the org.

**SFCC data model:**
- Products, catalogs, inventory, promotions, content assets, and customer data are stored in SFCC's proprietary database.
- SFCC customer records (profiles, addresses, order history) are not Salesforce Contact or Account records. They exist in SFCC's customer data store.
- Order data is stored in SFCC and can be exported or synced to an external OMS, but SFCC does not natively share `OrderSummary` objects with Salesforce Order Management.
- Product data typically originates in a PIM and is imported into both SFCC and Salesforce CRM independently (or via a shared PIM integration).

**Architectural implication:** Any scenario that requires real-time access to CRM data (account-based pricing, rep-assisted selling, quote-to-order) requires a custom integration layer in SFCC. In B2B Commerce on Core, this data is available natively.

### 3. Extensibility Model: Flow/Apex/LWC vs. SFRA Cartridges and Commerce Extensions

**B2B Commerce on Core — extensibility paths:**
- **Checkout Flow** — the entire checkout process is a Salesforce Flow (`CheckoutFlow` type). Each step (address, delivery, payment) is a flow element that can be overridden with custom screen components. No code required for standard paths.
- **Commerce Extensions (Winter '24+)** — custom Apex classes registered as commerce service implementations for pricing, inventory, shipping, and tax. These run synchronously within the checkout flow and replace the default platform behavior. Applies to B2B Commerce and D2C Commerce on Core only.
- **LWC** — all storefront UI components are LWC components, reusable from the org's component library.
- **Apex** — all business logic, trigger handlers, and service implementations are Apex, subject to governor limits.

**SFCC — extensibility paths:**
- **SFRA cartridges** — the primary customization unit. A cartridge is a Node.js module that extends or overrides storefront behavior. Cartridges are layered in a path (`cartridgePathOverride`); the first matching controller or template wins. Custom cartridges override SFRA base cartridge behavior without modifying the base.
- **Business Manager extensions** — custom UI modules for back-office admin workflows.
- **Pipelines (legacy) / Controllers (current)** — server-side rendering controllers that handle HTTP requests, call service layers, and render ISML templates.
- **Hooks** — declarative extension points within SFCC's system that allow code injection at defined pipeline steps (e.g., `app.payment.handle`, `app.order.calculate`).
- **SCAPI / OCAPI** — REST APIs that allow external systems (headless front ends, mobile apps) to interact with SFCC as a commerce engine without the SFRA rendering layer.

**Architectural implication:** B2B Commerce customization requires Salesforce platform skills (Apex, Flow, LWC). SFCC customization requires Node.js, SFRA cartridge architecture, and Business Manager knowledge. These are separate skill sets; team capability is a first-class architectural constraint.

### 4. Integration Surface and API Architecture

**B2B Commerce on Core:**
- Exposes the **Salesforce Connect API** (REST/SOAP) for all standard and custom objects.
- Exposes the **B2B Commerce Connect REST API** (also called Commerce Webstore APIs) for storefront operations: product search, cart management, checkout, order history.
- Exposes the **Salesforce Order Management APIs** for order lifecycle if OSM is provisioned.
- External integrations (payment processors, tax engines, ERP) connect to the org the same way any other integration does — via Connected App, OAuth, or Named Credential.
- Commerce Extensions let the org call out to external pricing, tax, or inventory services and return results into the checkout flow synchronously.

**SFCC:**
- Exposes the **Open Commerce API (OCAPI)** — the legacy REST API suite for shop operations, data management, and meta operations.
- Exposes the **Shopper Commerce API (SCAPI)** — the modern, performance-optimized REST API for headless commerce implementations.
- Exposes the **Management API** for Business Manager automation (catalog imports, code deployment, site preferences).
- SFCC integrates with payment processors, tax engines, and shipping providers through its own cartridge-based integration framework and the SFCC payment/service frameworks.
- Salesforce CRM integration requires either the **Salesforce Connector for B2C Commerce** (a managed solution) or a custom middleware pattern. There is no native object sharing.

---

## Common Patterns

### Pattern 1: B2B Commerce on Core for Quote-to-Order with CRM Integration

**When to use:** The buyer is a known business account with negotiated pricing. The sales team uses Salesforce CRM (Accounts, Opportunities, Quotes) and needs the commerce store to be an extension of the sales process — not a separate system. Order data must flow into Salesforce Order Management. Real-time account entitlement checking is required.

**How it works:**
1. B2B Commerce WebStore is provisioned inside the existing Salesforce org.
2. `BuyerGroup` and `CommerceEntitlementPolicy` records mirror the Account tier structure already in CRM.
3. `PricebookEntry` records provide contract pricing per buyer group; Commerce Extensions (Winter '24+) can call out to an external pricing engine if needed.
4. Checkout is a Flow-based process; approval steps can be injected as Flow elements without custom code.
5. Submitted orders create `OrderSummary` records directly in the org — accessible to service reps, fulfillment flows, and analytics without any integration.
6. CRM reports and dashboards show commerce order data alongside pipeline data because they share the same database.

**Why not SFCC:** SFCC would require a custom integration for every CRM data touchpoint (account entitlement checks, quote-to-order handoff, order history in Service Cloud). Each integration point adds latency, error surface, and maintenance cost. For known-account, CRM-integrated B2B workflows, B2B Commerce on Core is architecturally superior.

### Pattern 2: SFCC for High-Volume Anonymous Consumer Storefront

**When to use:** The storefront serves anonymous or semi-anonymous consumers at high concurrency. Peak traffic during promotions or seasonal events requires infrastructure that scales independently of the Salesforce org's API and compute limits. The team has SFRA/Node.js expertise. The primary integration concern is the payment processor and OMS, not real-time CRM data.

**How it works:**
1. SFCC is provisioned with a dedicated Primary Instance Group sized for peak load.
2. SFRA provides the base storefront; custom cartridges override checkout, promotion, and content behaviors.
3. The payment processor is integrated via SFCC's payment service framework (cartridge + hook pattern).
4. Order data is exported to an external OMS or synced to Salesforce Order Management via the Salesforce Connector or custom middleware.
5. Customer account data stays in SFCC's customer store; a sync to Salesforce Contact records is optional and asynchronous.
6. SCAPI is used for headless front-end implementations (mobile app, PWA) against the SFCC back end.

**Why not B2B Commerce on Core:** High-volume anonymous consumer traffic at peak concurrency runs against Salesforce platform governor limits (API request limits, concurrent request caps). SFCC is designed for this traffic pattern with dedicated infrastructure, CDN integration, and purpose-built caching layers that the Salesforce platform does not provide at equivalent cost or scale.

---

## Decision Guidance

| Situation | Recommended Platform | Reason |
|---|---|---|
| Buyers are known business accounts with CRM-integrated pricing | B2B Commerce on Core | BuyerGroup + EntitlementPolicy model; zero-latency CRM data access |
| Anonymous consumer traffic at high concurrency (>500 concurrent sessions) | SFCC | Dedicated infrastructure scales independently of Salesforce platform limits |
| Checkout requires account-level order approvals and spending limits | B2B Commerce on Core | Flow-based checkout supports Approval Process and account-level controls natively |
| Team has Apex/LWC/Flow skills; no SFRA/Node.js experience | B2B Commerce on Core | Customization uses existing Salesforce platform skills |
| Team has SFRA cartridge and Node.js expertise | SFCC | Customization model aligns with team capability |
| Real-time CRM data required at checkout (account balance, credit limit) | B2B Commerce on Core | Same-org data access; no integration latency |
| External PIM drives product catalog; headless front end is preferred | SFCC | SCAPI is purpose-built for headless; SFCC catalog import is a mature capability |
| Custom pricing engine (external service) must be called at checkout | B2B Commerce on Core (Commerce Extensions) | Commerce Extensions provide a synchronous callout hook in the checkout flow |
| Order data must be in Salesforce Order Management in real time | B2B Commerce on Core | `OrderSummary` is created natively in the same org |
| Project requires both B2B account-gated and B2C consumer storefronts | Evaluate hybrid: B2B Commerce on Core + SFCC or B2B + D2C on Core | Hybrid architectures require explicit data boundary design and separate integration surfaces |

---

## Recommended Workflow

Step-by-step instructions for an architect working on this platform decision:

1. **Establish infrastructure constraints first.** Determine peak concurrent anonymous session volume and annual order volume. If anonymous consumer traffic exceeds what Salesforce platform API concurrency limits can support at acceptable cost, SFCC becomes the primary candidate. Document this as a hard constraint before evaluating features.
2. **Map CRM data dependencies.** List every piece of CRM data the storefront needs at runtime: account credit limits, contract pricing, order history, account entitlements, service case history. If more than two of these require real-time access at checkout, B2B Commerce on Core's same-org data model provides a structural advantage that is difficult to replicate in SFCC without significant middleware investment.
3. **Assess team skills and DevOps maturity.** Confirm whether the delivery team has Apex/Flow/LWC capability or SFRA/Node.js/Business Manager capability. Neither platform is easier in the abstract — they favor different skill sets. A team with deep Salesforce platform knowledge will move faster on B2B Commerce on Core; a team with front-end engineering depth will move faster on SFCC.
4. **Evaluate the extensibility model against customization requirements.** List every non-standard behavior: custom pricing logic, custom inventory rules, custom tax calculation, custom checkout steps. Map each to the extensibility mechanism on each platform (Commerce Extensions vs. SFRA hooks and cartridges). Identify any requirements that cannot be met by either platform's standard extensibility model.
5. **Design the integration architecture for each option.** For B2B Commerce on Core, document what external integrations are needed and how they connect to the org. For SFCC, document the CRM integration surface: what data must flow to/from Salesforce CRM, at what frequency, and through what mechanism (Salesforce Connector, middleware, batch import). The integration complexity delta between the two options is often the deciding factor.
6. **Produce the recommendation with rationale.** Document the platform choice with each driving factor cited explicitly. Record capability gaps — what the selected platform does not provide natively — and confirm the team accepts the custom development required to fill those gaps.
7. **Identify the follow-on skills.** Once the platform decision is locked, activate the appropriate implementation skill: `admin/b2b-commerce-store-setup` for B2B Commerce on Core, or `admin/b2c-commerce-store-setup` for SFCC. If Commerce Extensions are in scope, activate `apex/commerce-extensions-development`.

---

## Review Checklist

Run through these before marking this architectural decision complete:

- [ ] Peak concurrent session volume and annual order volume are documented
- [ ] CRM data dependencies at checkout runtime are enumerated
- [ ] Team skills (Salesforce platform vs. SFRA/Node.js) are assessed and documented
- [ ] Extensibility requirements are mapped to each platform's extension model
- [ ] Integration architecture is sketched for both options (even the rejected one)
- [ ] Commerce Extensions scope is clarified — B2B/D2C on Core only, not SFCC
- [ ] The recommended platform is documented with explicit rationale per non-functional requirement
- [ ] Capability gaps for the selected platform are listed with a disposition (accept, custom-build, or third-party)
- [ ] Follow-on implementation skills are identified

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Commerce Extensions do not apply to SFCC** — Commerce Extensions (custom pricing, inventory, shipping, and tax service implementations via Apex, introduced Winter '24) are a feature of B2B Commerce and D2C Commerce on Core only. SFCC has its own extensibility model: SFRA hooks, cartridges, and the Business Manager service framework. Recommending or expecting Commerce Extensions to work in an SFCC implementation will result in the entire pricing/tax customization plan failing at build time.

2. **B2B Commerce and B2C Commerce (SFCC) share no objects, APIs, or org data** — These are architecturally separate systems. There is no `WebStore` object in SFCC. There are no `BuyerGroup` or `CommerceEntitlementPolicy` records in SFCC. SFCC has no SOQL, no Apex, and no Flow. Any architecture document that refers to Salesforce platform objects (Account, Contact, Product2) as if they are natively available in SFCC is incorrect. Product and customer data must be explicitly imported into SFCC through its catalog and customer import mechanisms.

3. **B2B Commerce checkout is Flow Builder; B2C Commerce checkout is SFRA cartridges — these are not interchangeable** — The checkout customization model is fundamentally different. B2B Commerce checkout steps are Flow elements — draggable, declaratively configurable, testable in Flow Builder. SFCC checkout is a cartridge controller chain — Node.js code overriding SFRA base controllers. A team that knows how to customize B2B checkout flows has no transferable skill for SFCC checkout cartridges, and vice versa. Scoping checkout customization without identifying which model applies leads to severely incorrect effort estimates.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Platform Architecture Comparison | Table or document comparing B2B Commerce on Core and SFCC across infrastructure, data model, extensibility, integration surface, and team skill requirements |
| Integration Architecture Outline | Diagram or narrative describing how each platform option connects to external systems (ERP, OMS, PIM, payment processor, Salesforce CRM) |
| Platform Recommendation with Rationale | Written decision document citing each driving non-functional requirement and how the selected platform addresses it |
| Capability Gap Register | List of requirements the selected platform does not cover natively, with disposition for each gap |

---

## Related Skills

- `admin/b2b-vs-b2c-requirements` — use upstream of this skill for buyer-journey and requirements-level platform selection before architectural evaluation
- `admin/b2b-commerce-store-setup` — use after selecting B2B Commerce on Core; covers WebStore creation, BuyerGroup and entitlement policy setup, and buyer contact configuration
- `admin/b2c-commerce-store-setup` — use after selecting SFCC; covers Business Manager configuration, SFRA setup, and storefront activation
- `apex/commerce-extensions-development` — use when B2B Commerce on Core is selected and custom pricing, inventory, shipping, or tax logic is required
- `integration/salesforce-b2c-commerce-connector` — use when SFCC is selected and a Salesforce CRM integration is required
