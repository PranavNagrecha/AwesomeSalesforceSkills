# Well-Architected Notes — B2B vs D2C Commerce Requirements

## Relevant Pillars

- **Security** — The B2B buyer-entitlement layer (BuyerGroup, CommerceEntitlementPolicy) enforces catalog-level access control at the platform level. Choosing the wrong Commerce type risks either over-exposing products to unauthorized buyers (if D2C is used where B2B entitlement is required) or unnecessarily blocking consumer access (if B2B authentication requirements are applied to a consumer use case). The platform decision directly determines the security model for buyer data and purchasing access.

- **Scalability** — B2B Commerce entitlement objects carry hard platform limits (200 BuyerGroups per CommerceEntitlementPolicy; 2,000 BuyerGroups per product per WebStore for search indexing). Choosing B2B Commerce for a high-volume consumer use case that does not need account gating creates scalability overhead with no benefit. Conversely, choosing D2C Commerce for a large enterprise dealer portal means building custom entitlement logic that must scale without platform-native enforcement.

- **Reliability** — The WebStore store type (B2B vs. D2C) is immutable post-creation. A wrong platform decision made during requirements results in a rebuild, not a reconfiguration. Reliability risk is highest when the platform decision is deferred or made informally without documentation — incorrect store type selection can only be resolved by deleting and recreating the WebStore.

- **Operational Excellence** — Clear platform selection documentation, licensing verification, and a structured decision process (as this skill provides) reduce operational risk for the entire project. Teams that skip the formal platform decision step frequently encounter license gaps, object availability issues, and data model mismatches that surface late in implementation and are expensive to fix.

---

## Architectural Tradeoffs

**B2B Commerce: power of account-gated entitlement vs. configuration overhead**

B2B Commerce provides native, platform-enforced catalog segmentation and contract pricing via BuyerGroup and CommerceEntitlementPolicy. This eliminates the need for custom entitlement logic. The tradeoff is configuration complexity: every buyer account must be explicitly modeled as a BuyerAccount, assigned to a BuyerGroup, and each contact must receive an explicit role. This overhead is justified when the use case genuinely requires account-gated access. It is pure cost when applied to consumer storefronts where all buyers see the same catalog.

**D2C Commerce: simplicity for consumer use cases vs. inability to scale account-gated segmentation**

D2C Commerce is optimized for individual consumers. The data model is simpler, guest checkout is a first-class scenario, and there is no BuyerGroup overhead. The tradeoff is that native account-based catalog segmentation and contract pricing are unavailable. Implementing these features on D2C requires custom development that operates outside the platform's security and scalability guarantees for Commerce entitlement.

**Hybrid B2B2C: maximum flexibility, maximum complexity**

Maintaining two separate WebStores (one B2B, one D2C) with shared product catalog, shared order management, and consistent buyer data across both platforms is architecturally correct but operationally expensive. It requires both license types, two separate Experience Cloud sites, and a routing strategy. This pattern is appropriate for large enterprises with genuine dual-channel requirements; it is over-engineered for most mid-market implementations.

---

## Anti-Patterns

1. **Starting a WebStore without confirming the store type** — Creating a WebStore of the wrong type (B2B vs. D2C) and expecting to reconfigure it later. The store type is immutable. The only fix is deletion and recreation. This anti-pattern is avoided entirely by completing the platform selection decision (this skill) before touching WebStore setup (admin/b2b-commerce-store-setup or admin/b2c-commerce-store-setup).

2. **Applying B2B entitlement configuration to a D2C use case** — Attempting to implement per-consumer catalog segmentation using BuyerGroups on a D2C store. D2C Commerce does not provision BuyerGroup objects. All code and automation referencing these objects will fail. The correct approach for consumer-level personalization on D2C Commerce is price book segmentation, promotion rules, or custom entitlement logic — not the B2B entitlement model.

3. **Conflating Salesforce B2C Commerce (SFCC) with D2C Commerce (Lightning WebStore)** — Planning an SFCC-based infrastructure (Business Manager, SFRA cartridges, Site Cartridge Path configuration) for a project that is actually using D2C Commerce on the core Salesforce platform. These are entirely separate products with different admin surfaces, deployment models, and developer APIs. This anti-pattern leads to incorrect architecture diagrams, wrong licensing procurement, and implementation plans that cannot be executed.

---

## Official Sources Used

- B2B Commerce and D2C Commerce Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2c_comm_dev_intro.htm
- B2B and D2C Commerce Licenses (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.comm_licenses.htm&type=5
- B2B Commerce Developer Guide — Entitlement Data Limits — https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2c_comm_dev_entitlement_limits.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
