# Gotchas — B2B vs B2C Commerce Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Commerce Extensions Apply Only to B2B/D2C Commerce on Core — Not SFCC

**What happens:** An architect specifies a custom pricing or tax implementation using Commerce Extensions (the `sfdc_checkout.CartExtension` Apex interface, Winter '24+) for a project that is on Salesforce B2C Commerce (SFCC). The build team cannot find the referenced Apex interface in the SFCC environment and spends days investigating before escalating. The entire pricing customization design must be re-architected using SFCC's cartridge hook pattern.

**When it occurs:** When an architect or AI assistant reads the Commerce Extensions documentation without first confirming whether the implementation is on B2B/D2C Commerce on Core or SFCC. The documentation is clearly scoped to Core-platform commerce, but the distinction is easy to miss when researching "Salesforce Commerce checkout customization" generically.

**How to avoid:** Confirm the platform infrastructure before specifying any extensibility mechanism. The tell is simple: if there is a Salesforce org, a Flow checkout, and Apex classes, you are on B2B/D2C Commerce on Core. If there is a Business Manager, SFRA cartridges, and Node.js controllers, you are on SFCC. Commerce Extensions (Apex) apply only to the former.

---

## Gotcha 2: B2B Commerce and SFCC Share No Objects, APIs, or Org Data

**What happens:** An architect designs a data flow in which the SFCC storefront reads `BuyerGroup` membership and `CommerceEntitlementPolicy` records from the Salesforce org at checkout to determine which products to display. The SFCC development team reports that these objects do not exist in the SFCC environment and cannot be queried via any available API.

**When it occurs:** When B2B Commerce and SFCC are mentally conflated because both are sold under the "Salesforce Commerce" umbrella. The `BuyerGroup`, `CommerceEntitlementPolicy`, `WebStore`, `OrderSummary`, and other B2B Commerce objects are Salesforce platform objects. They exist in the Salesforce org's database. SFCC has a completely separate database and does not expose or consume these objects in any native way.

**How to avoid:** Treat SFCC as an external system relative to the Salesforce org at all times. Any data from the Salesforce org (account entitlements, CRM pricing, order history) must be surfaced to SFCC through an explicit integration (REST API call, middleware, batch import). Design the integration surface explicitly before committing to SFCC as the platform.

---

## Gotcha 3: B2B Commerce Checkout Is Flow Builder; SFCC Checkout Is SFRA Cartridges — These Are Not the Same Skill Set

**What happens:** A delivery team that has successfully customized B2B Commerce checkout steps in Flow Builder is assigned to a follow-on SFCC project and attempts to find the equivalent "checkout flow" configuration in Business Manager. There is no Flow Builder in SFCC. Checkout behavior is controlled by SFRA cartridge controllers, ISML templates, and server-side rendering pipelines. The team's Salesforce Flow expertise provides no transferable capability for this work, leading to a severely under-estimated project.

**When it occurs:** When project staffing or scoping assumes that "Salesforce Commerce checkout customization" experience is interchangeable across B2B Commerce on Core and SFCC. The two platforms use completely different runtime models, languages, and tooling for checkout.

**How to avoid:** Assess team capability against the specific platform's customization model before scoping. B2B Commerce checkout customization requires Flow Builder and optionally Apex. SFCC checkout customization requires Node.js, SFRA cartridge architecture, and Business Manager proficiency. Treat these as separate skill domains and staff accordingly.

---

## Gotcha 4: SFCC Order Data Does Not Automatically Appear in Salesforce Order Management

**What happens:** A project assumes that orders placed in SFCC will automatically create `OrderSummary` records in Salesforce Order Management for fulfillment processing. Orders are placed successfully in SFCC but never appear in Salesforce Order Management. The fulfillment team has no visibility into new orders.

**When it occurs:** When the project team assumes that because both SFCC and Order Management are "Salesforce" products, they are automatically integrated. They are not. SFCC stores orders in its own database. Syncing them to Salesforce Order Management requires either the Salesforce Connector for B2C Commerce (a managed integration) or a custom integration built on SFCC's OCAPI/SCAPI order export and the Salesforce Order Management intake API.

**How to avoid:** Explicitly design and scope the SFCC-to-Order Management integration as a distinct integration workstream. Confirm whether the Salesforce Connector for B2C Commerce is the right fit, or whether a custom integration is needed. Never assume SFCC and Order Management share data natively.

---

## Gotcha 5: Salesforce Platform Governor Limits Apply to B2B Commerce on Core at Traffic Scale

**What happens:** A B2B Commerce on Core storefront performs well in UAT with 20–50 concurrent authenticated users but degrades under load testing at 500+ concurrent sessions. The root cause is that every storefront page load triggers SOQL queries, Apex callouts, and Experience Cloud rendering within the Salesforce platform's governor-limited runtime. Concurrent API request limits and per-transaction CPU time limits that are invisible in low-traffic testing become binding constraints at scale.

**When it occurs:** When B2B Commerce on Core is selected for a consumer-scale or high-concurrency use case without validating peak load requirements against Salesforce platform limits. B2B Commerce on Core is optimized for authenticated, account-gated buyer workflows — not anonymous consumer traffic at e-commerce peak scale.

**How to avoid:** Run a capacity planning exercise against Salesforce platform concurrent request limits before committing B2B Commerce on Core for any storefront with expected anonymous or semi-anonymous traffic above a few hundred concurrent sessions. If the analysis reveals a capacity risk, SFCC or D2C Commerce with CDN caching is the correct architectural path.
