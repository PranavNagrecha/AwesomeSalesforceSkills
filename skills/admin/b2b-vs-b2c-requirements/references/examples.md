# Examples — B2B vs D2C Commerce Requirements

## Example 1: Manufacturing Company Selecting B2B Commerce for Dealer Portal

**Context:** A manufacturing company is building a Salesforce storefront for authorized dealers. Each dealer is a business account with a negotiated price list. Different product lines are visible only to specific dealer tiers (e.g., OEM parts vs. aftermarket accessories). All buyers must be authenticated; no anonymous browsing is required.

**Problem:** The project team initially considered D2C Commerce because the storefront needed a modern consumer-grade UX. They started a D2C WebStore and quickly found there was no native way to show different product catalogs to different dealer accounts or apply negotiated pricing per account. Attempting to work around this with custom Apex and price overrides became architecturally untenable.

**Solution:**

The correct platform is B2B Commerce. The platform selection criteria map as follows:

```
Buyer persona:        Business Account (authorized dealer)
Guest checkout:       Not required — all buyers are authenticated dealers
Pricing model:        Negotiated contract pricing per dealer tier
Catalog segmentation: Different SKUs per tier (OEM vs. aftermarket)

Platform:             B2B Commerce (with BuyerGroup + CommerceEntitlementPolicy)
```

Implementation approach:
- Create one `BuyerGroup` per dealer tier (e.g., "OEM Dealers", "Aftermarket Dealers").
- Create one `CommerceEntitlementPolicy` per tier, each with the appropriate product set.
- Link each dealer Account as a `BuyerGroupMember` in the correct group.
- Associate contract price books per BuyerGroup.
- Activate admin/b2b-commerce-store-setup for configuration.

**Why it works:** B2B Commerce's `BuyerGroup` and `CommerceEntitlementPolicy` model is purpose-built for account-gated catalog segmentation. Attempting the same segmentation on a D2C WebStore would require entirely custom entitlement logic with no platform-native enforcement.

---

## Example 2: Consumer Goods Brand Selecting D2C Commerce for Direct-to-Consumer Store

**Context:** A consumer goods brand wants to sell directly to end consumers via a Salesforce-hosted storefront. Buyers are individuals, not business accounts. Pricing is the same for all buyers (with optional seasonal promotions). Guest checkout is a firm requirement — the marketing team does not want to force account creation before purchase.

**Problem:** A Salesforce partner initially recommended B2B Commerce because the client already had B2B Commerce licenses from an existing dealer portal project. The team started building on a B2B WebStore and immediately hit friction: enabling guest checkout required a non-trivial configuration that was only added in Winter '24, and the BuyerGroup/EntitlementPolicy overhead added no value for a consumer scenario. Worse, the client's org was on Summer '23, which predated guest checkout support entirely on B2B WebStores.

**Solution:**

The correct platform is D2C Commerce. The licensing analysis:

```
Buyer persona:        Individual consumer (no business account)
Guest checkout:       Required (firm marketing requirement)
Pricing model:        Uniform pricing + promotions (no contract pricing)
Catalog segmentation: None (all buyers see all products)

Platform:             D2C Commerce
License required:     D2C Commerce add-on (separate from B2B Commerce)
```

Since the org did not have a D2C Commerce license, a license procurement step was added to the project plan before any implementation began.

**Why it works:** D2C Commerce is the Salesforce platform's native consumer storefront type. Guest checkout is a first-class scenario. The Individual/Person Account identity model maps directly to consumer purchasing without the BuyerGroup overhead that serves no purpose in a B2C use case.

---

## Anti-Pattern: Recommending SFCC Setup Steps for a D2C Commerce Project

**What practitioners do:** When a client says "B2C Commerce," practitioners with SFCC experience begin discussing Business Manager, SFRA cartridges, site cartridge paths, and quota management — all of which are correct for Salesforce B2C Commerce (SFCC) but completely wrong for D2C Commerce (Lightning WebStore).

**What goes wrong:** The team plans an SFCC-based infrastructure (separate hosted platform, SFRA customization model, Business Manager administration) for what is actually a core-org WebStore project. Licensing, infrastructure, and technical architecture are all wrong. SFCC and D2C Commerce are separate products with no shared admin UI, deployment model, or codebase.

**Correct approach:** Before any technical planning, confirm which Commerce product the client is using:
- Ask whether the storefront is managed in **Business Manager** (SFCC) or in the **Salesforce Commerce app** inside the core org (D2C/B2B Commerce on Lightning).
- Check the org's Installed Packages — SFCC is a separate SaaS platform and will not appear there. D2C or B2B Commerce on Lightning will show as licensed store types in the WebStore creation dialog inside the core org.
- Use admin/b2c-commerce-store-setup for SFCC projects. Use this skill (b2b-vs-b2c-requirements) to drive the D2C vs. B2B decision for Lightning-based Commerce.
