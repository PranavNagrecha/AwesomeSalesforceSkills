---
name: b2b-vs-b2c-requirements
description: "Use this skill to determine whether a Salesforce Commerce project should use B2B Commerce (account-gated, BuyerGroup-based, contract pricing) or D2C Commerce (consumer storefront, guest checkout, individual-based). Trigger keywords: B2B vs B2C, commerce platform selection, buyer journey, account-based purchasing, consumer storefront, licensing decision. NOT for implementation mechanics — use admin/b2b-commerce-store-setup or admin/b2c-commerce-store-setup for configuration work. NOT for Salesforce B2C Commerce (SFCC/Business Manager) setup."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Scalability
  - Reliability
triggers:
  - "should we use B2B Commerce or D2C Commerce for our Salesforce storefront project"
  - "our buyers are businesses that need account-based pricing and contract catalogs — which Commerce product fits"
  - "we need guest checkout and individual consumer purchasing — does that require B2C or D2C Commerce"
  - "what is the difference between B2B Commerce and D2C Commerce licensing on the Salesforce platform"
  - "our sales team uses account-based buyer groups but marketing wants a consumer storefront — how do we choose"
tags:
  - b2b-commerce
  - d2c-commerce
  - commerce-platform-selection
  - buyer-journey
  - buyer-group
  - licensing
  - webstore
  - account-based-commerce
inputs:
  - "Description of buyer personas (businesses placing orders on behalf of an account vs. individual consumers)"
  - "Guest checkout requirement (yes/no)"
  - "Need for contract pricing, tiered pricing, or BuyerGroup-based catalog segmentation (yes/no)"
  - "Existing Salesforce org licenses (B2B Commerce, D2C Commerce, or both)"
  - "Known scale: number of buyer accounts, SKUs, and expected concurrent sessions"
outputs:
  - "Platform recommendation: B2B Commerce or D2C Commerce (with rationale)"
  - "Decision table mapping requirements to platform capabilities"
  - "Licensing implications summary"
  - "List of follow-on implementation skills to activate after the decision is made"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# B2B vs D2C Commerce Requirements

This skill activates when a practitioner must decide whether to use Salesforce B2B Commerce or D2C Commerce before building a storefront. It covers the buyer journey differences, entitlement architecture divergence, licensing requirements, and the key platform behaviors that drive the pre-build decision. It does not cover implementation mechanics — those belong to admin/b2b-commerce-store-setup or admin/b2c-commerce-store-setup.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm which Salesforce Commerce licenses are active in the org. B2B Commerce and D2C Commerce are sold as separate add-ons to Sales/Service Cloud. An org can hold both licenses simultaneously, enabling a hybrid "B2B2C" pattern, but that requires careful data model planning.
- The most common wrong assumption: "B2C Commerce" and "D2C Commerce" are the same thing. They are not. Salesforce B2C Commerce (also called SFCC) is a separate, hosted e-commerce platform built on Business Manager and SFRA cartridges. D2C Commerce (also called Direct-to-Consumer or Lightning-based B2C Commerce) is a WebStore-based storefront running on the Lightning Web Runtime (LWR) inside the core Salesforce platform. These are entirely different infrastructure stacks with different admin, API, and deployment models.
- The second most common wrong assumption: anonymous/guest purchasing is always available on D2C Commerce by default. Guest checkout was not available on D2C WebStores until Winter '24 and must be explicitly enabled even on post-Winter '24 orgs. B2B Commerce does not support anonymous purchasing by default and requires the same explicit enablement.

---

## Core Concepts

### 1. Shared Infrastructure, Divergent Buyer-Entitlement Layer

Both B2B Commerce and D2C Commerce use the same `WebStore` object and the Lightning Web Runtime (LWR) framework for storefront rendering. The code-level difference between platforms is minimal at the UI layer — both support LWC components, Experience Cloud sites, and the Commerce APIs.

The critical divergence is at the buyer-entitlement layer:

- **B2B Commerce** gates catalog and pricing access through `BuyerGroup` and `CommerceEntitlementPolicy` records. A buyer contact must be associated with an Account that is a `BuyerGroupMember`, and the contact must have an explicit Buyer or Buyer Manager role. Anonymous purchasing is not the default — it is an opt-in capability added in Winter '24.
- **D2C Commerce** is designed for individual consumers. Buyer identity is modeled on the Individual object or Person Account, not on business Account records. Guest checkout is the default intent (though it still requires explicit enablement post-Winter '24). There are no `BuyerGroup` or `CommerceEntitlementPolicy` records in a pure D2C store.

This divergence means choosing the wrong platform creates a data model that cannot be corrected without rebuilding the entitlement layer from scratch.

### 2. Account-Based vs. Consumer Buyer Journey

B2B buyer journeys are inherently account-centric:
- Orders are placed on behalf of a business account, not by an individual acting independently.
- Pricing is negotiated per account or per account tier (contract pricing, volume discounts).
- Multiple contacts within the same account share access to the same cart, order history, and catalog.
- Approvals and spending limits are enforced at the account level.

D2C buyer journeys are consumer-centric:
- Each buyer is an individual with their own cart, order history, and account (in the e-commerce sense).
- Pricing is uniform or segment-based, not negotiated per account.
- Guest checkout is a first-class scenario.
- There is no concept of a buyer-manager or order approval workflow at the account level.

Mixing these models — for example, adding BuyerGroup-gated pricing to a D2C store, or trying to support consumer guest checkout in a B2B store — is possible in limited ways but requires custom development and is unsupported as a first-class platform feature in most configurations.

### 3. Licensing

B2B Commerce and D2C Commerce are separate license SKUs:

- **B2B Commerce** license unlocks: `BuyerGroup`, `CommerceEntitlementPolicy`, `BuyerAccount`, `BuyerGroupMember`, contract pricing objects, and account-gated catalog features.
- **D2C Commerce** license unlocks: the consumer WebStore type, guest checkout flows, and the Individual-based identity model.

An org with only a B2B Commerce license cannot configure a D2C-type WebStore without purchasing the D2C add-on, and vice versa. Hybrid B2B2C deployments require both licenses. License type is visible in the org's Installed Packages and in the Commerce App's store-type selection screen — only licensed store types appear as options when creating a new WebStore.

### 4. Guest and Anonymous Purchasing

Prior to Winter '24, neither B2B nor D2C Commerce WebStores supported anonymous browsing or guest checkout natively. Winter '24 added guest purchasing enablement for both store types, but it must be explicitly activated:
- In D2C stores: enable "Allow Guest Browsing" and configure the Guest User profile in the associated Experience Cloud site.
- In B2B stores: enable anonymous access in the WebStore settings and configure the Guest User profile — but this is an uncommon configuration, as B2B buyer identity is the foundation of account-based pricing and entitlement.

If guest checkout is a core business requirement and the buyer persona is individual consumers, D2C Commerce is the correct platform. If all buyers must be authenticated business accounts and guest access is not required, B2B Commerce is correct.

---

## Common Patterns

### Pattern A: B2B Commerce for Account-Gated Catalog and Contract Pricing

**When to use:** The buyer is a business entity. Pricing varies by account or account tier. Products are gated by buyer group membership. Order approval workflows exist. Guest purchasing is not required.

**How it works:**
1. Confirm B2B Commerce license is active in the org.
2. Model buyer segmentation as `BuyerGroup` records (one per tier or customer segment).
3. Create `CommerceEntitlementPolicy` records per tier and link products to each policy.
4. Convert customer Accounts to BuyerAccounts and assign contacts explicit Buyer or Buyer Manager roles.
5. Configure contract pricing via price books linked to each BuyerGroup.
6. Proceed to admin/b2b-commerce-store-setup for implementation.

**Why not D2C Commerce:** D2C Commerce has no BuyerGroup or CommerceEntitlementPolicy objects. Account-gated catalog segmentation and contract pricing cannot be implemented natively on a D2C WebStore.

### Pattern B: D2C Commerce for Consumer Storefront with Guest Checkout

**When to use:** The buyer is an individual consumer. Pricing is uniform or segment-based (not negotiated per account). Guest checkout is required or preferred. No account-level approval workflows are needed.

**How it works:**
1. Confirm D2C Commerce license is active in the org.
2. Design the buyer identity model around Individual or Person Account records.
3. Enable guest browsing and guest checkout in the WebStore settings and the Experience Cloud site.
4. Configure standard price books (no BuyerGroup or entitlement policy setup needed).
5. Proceed to admin/b2c-commerce-store-setup for implementation.

**Why not B2B Commerce:** B2B Commerce defaults to authenticated-only access and requires account and buyer group setup for every transacting buyer. Guest checkout is possible but is an add-on configuration, not a first-class scenario. The data model overhead of BuyerGroups, EntitlementPolicies, and BuyerAccounts adds complexity without value for consumer use cases.

---

## Decision Guidance

| Situation | Recommended Platform | Reason |
|---|---|---|
| Buyers are business accounts with negotiated pricing | B2B Commerce | BuyerGroup + EntitlementPolicy model supports account-gated catalog and contract pricing natively |
| Buyers are individual consumers with uniform pricing | D2C Commerce | Individual/Person Account model; no BuyerGroup overhead |
| Guest checkout is a primary requirement | D2C Commerce | D2C is the intended platform for consumer guest flows |
| Multiple buyer tiers need different product catalogs | B2B Commerce | CommerceEntitlementPolicy segmentation is a B2B-only native feature |
| Need both account-based and consumer storefronts | Both licenses (B2B + D2C) | Hybrid B2B2C requires both license types and separate WebStore instances |
| Org only has B2B Commerce license but needs consumer store | Purchase D2C license | D2C WebStore type is unlocked by D2C license only |
| Order approval workflows at account level are required | B2B Commerce | Buyer Manager role and account-level order management are B2B-native |
| Project is on Salesforce B2C Commerce (SFCC) / Business Manager | Separate platform entirely | SFCC is a different product — this skill does not apply; use admin/b2c-commerce-store-setup |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm the buyer persona** — Determine whether purchasers are business entities placing orders on behalf of an Account, or individual consumers acting independently. This is the primary fork in the decision. If the answer is "both," flag as a B2B2C hybrid requiring both licenses.
2. **Assess guest checkout requirements** — Ask whether anonymous browsing or guest purchasing is required. If yes and buyers are individuals, D2C Commerce is strongly indicated. If yes and buyers are businesses, confirm the B2B guest access enablement introduced in Winter '24 is acceptable, or reconsider the platform choice.
3. **Evaluate pricing and catalog segmentation needs** — Determine whether pricing is negotiated per account (contract pricing) or uniform across buyers. Determine whether different buyers should see different product catalogs. Account-gated segmentation points to B2B Commerce; uniform pricing and open catalogs point to D2C Commerce.
4. **Verify active licenses** — Check the org's Installed Packages or the Commerce app's new-store dialog to confirm which store types are available. Only licensed store types appear. Report any license gap before proceeding.
5. **Document the decision and rationale** — Produce a written summary mapping each business requirement to the platform capability that satisfies it. Capture any requirements that cannot be met natively and require custom development.
6. **Hand off to the correct implementation skill** — Once the platform decision is made, activate admin/b2b-commerce-store-setup (for B2B Commerce) or admin/b2c-commerce-store-setup (for D2C/SFCC Commerce) for the configuration work.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Buyer persona is clearly documented (business account vs. individual consumer)
- [ ] Guest checkout requirement has been explicitly confirmed or ruled out
- [ ] Pricing model (negotiated/contract vs. uniform) is documented
- [ ] Catalog segmentation needs (BuyerGroup-gated vs. open) are documented
- [ ] Active Commerce licenses in the org have been verified
- [ ] Platform decision (B2B or D2C) is recorded with rationale
- [ ] Any unmet requirements (requiring custom development) are flagged
- [ ] The correct follow-on implementation skill has been identified

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **"B2C Commerce" and "D2C Commerce" are different products** — Salesforce sells Salesforce B2C Commerce (SFCC), which runs on Business Manager with SFRA cartridges and is a hosted platform entirely separate from the core Salesforce org. D2C Commerce (sometimes called Lightning-based B2C Commerce) is a WebStore running on LWR inside the core Salesforce platform. Confusing the two leads to completely incorrect infrastructure recommendations, implementation plans, and licensing procurement.

2. **B2B Commerce does not support guest checkout by default** — Prior to Winter '24, B2B WebStores required authenticated buyer access for every transaction. Guest purchasing was added in Winter '24 but must be explicitly enabled in WebStore settings and Experience Cloud site configuration. Assuming B2B Commerce supports guest checkout out-of-the-box in any org that has not been upgraded to Winter '24 or later will produce a storefront that blocks anonymous buyers with no clear error.

3. **D2C Commerce license does not include BuyerGroup or EntitlementPolicy objects** — A common mistake is trying to implement account-gated catalog segmentation on a D2C WebStore. The `BuyerGroup`, `CommerceEntitlementPolicy`, and `CommerceEntitlementBuyerGroup` objects are provisioned by the B2B Commerce license. An org with only a D2C license will not have these objects available in the data model, and any automation or code referencing them will fail with "object not found" errors.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Platform decision document | Written rationale mapping business requirements to B2B or D2C Commerce capabilities |
| Licensing gap report | List of required licenses vs. currently active licenses in the org |
| Requirements-to-features mapping | Table showing which Commerce features satisfy each buyer journey requirement |
| Follow-on skill list | Implementation skills to activate after the platform decision is finalized |

---

## Related Skills

- admin/b2b-commerce-store-setup — use for B2B Commerce implementation: WebStore creation, BuyerGroup setup, entitlement policy configuration, and buyer contact access
- admin/b2c-commerce-store-setup — use for Salesforce B2C Commerce (SFCC) storefront setup via Business Manager
- admin/commerce-pricing-and-promotions — pricing model design for either platform after the platform decision is made
- admin/commerce-product-catalog — product catalog structure and entitlement policy configuration after platform selection
