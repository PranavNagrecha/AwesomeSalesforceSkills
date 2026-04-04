# Examples — Industries CPQ vs Salesforce CPQ

## Example 1: Telco Selects Industries CPQ Over Salesforce CPQ

**Context:** A regional telecommunications company is implementing Salesforce for its B2C and SMB selling motions. The product catalog contains 800+ mobile, broadband, and TV bundle items, each with multiple attribute combinations (data caps, contract lengths, hardware options). The sales team runs guided-selling flows through a customer service portal.

**Problem:** The initial project team defaulted to Salesforce CPQ because "we already have Sales Cloud." They began modeling telco bundles as Salesforce CPQ product families with product options. After three months, the model had grown to 1,200+ `SBQQ__ProductOption__c` records and required custom Apex pricing plugins for every tier. The Quote Line Editor could not render the bundle depth without hitting SOQL limits. Guided-selling had to be built from scratch in Flow.

**Solution:**

The correct architecture is Industries CPQ with OmniStudio:

```
Architecture:
1. Product Catalog → Catalog Items with Attributes (not Pricebook Entries)
2. Bundles → Multi-level catalog items with cardinality rules
   (e.g., 1 base plan, 0–5 add-ons, 0–2 hardware items)
3. Pricing → Calculation Procedures that fire on the cart
   - Procedure: ApplyTieredPricing
   - Input: CartItem.Quantity, CartItem.AttributeSet
   - Output: CartItem.UnitPrice
4. Guided Selling → OmniScript "ShopAndBuy" flow
   - Step 1: DataRaptor lookup of customer account/assets
   - Step 2: FlexCard product grid
   - Step 3: Attribute selection per bundle item
   - Step 4: Cart review + pricing summary
5. Output → CPQ Order → Integration Procedure → OSS/BSS system
```

**Why it works:** Industries CPQ's Calculation Procedures are designed for attribute-driven, multi-level catalog pricing. The product catalog does not balloon to thousands of Pricebook Entries because attributes are stored on the catalog item, not as separate products. OmniScript handles guided-selling natively without custom Apex.

---

## Example 2: Enterprise SaaS Company Plans Revenue Cloud Migration from Salesforce CPQ

**Context:** A B2B SaaS company has run Salesforce CPQ (managed package version 236) for four years. The use case is simple: annual software subscriptions, 10–30 line items per quote, two-tier discount approval. The company learned that Salesforce CPQ entered end-of-sale in March 2025 and wants to understand the migration path to Revenue Cloud.

**Problem:** The team assumed they needed to migrate immediately after end-of-sale was announced. They also assumed all existing CPQ configuration (pricing rules, approval chains, product bundles) would migrate automatically using a Salesforce-provided tool.

**Solution:**

```
Migration approach:
1. Assess current Salesforce CPQ footprint:
   - Count custom fields on SBQQ__Quote__c, SBQQ__QuoteLine__c
   - Identify Apex plugins (CPQ plugin interfaces implemented)
   - Document pricing rule and discount schedule count
   - Map managed-package objects used in reports, dashboards, flows

2. Map to Revenue Cloud equivalents:
   SBQQ__Quote__c           → Transaction (native)
   SBQQ__QuoteLine__c       → TransactionLineItem (native)
   SBQQ__PricingRule__c     → PriceAdjustmentSchedule (native)
   SBQQ__ApprovalChain__c   → Approval Flows (native)

3. Data migration sequence:
   - Migrate active products and price books first (no namespace change needed)
   - Migrate open quotes last (SBQQ__Quote__c → Transaction)
   - Archive or freeze closed quotes; do not attempt bulk migrate

4. Validate feature parity before setting migration date:
   - Confirm partner community quoting support if used
   - Confirm billing configuration parity if Salesforce Billing is in use
```

**Why it works:** End-of-sale does not mean end-of-life or end-of-support on a defined date. Existing customers can renew and use Salesforce CPQ. A planned, phased migration tied to a natural business cycle (e.g., annual contract renewal) reduces risk significantly compared to a forced cutover.

---

## Example 3: Post-Acquisition Coexistence — Industries CPQ and Salesforce CPQ in Same Org

**Context:** A global energy company (parent) runs Salesforce CPQ for its enterprise services quoting. It acquires a utility subsidiary that runs Industries CPQ for residential and SMB energy product selling. The integration team proposes merging both into the parent's single Salesforce org.

**Problem:** The team assumed "merge the orgs and pick one CPQ." The subsidiary's 600 active catalog items are modeled in Industries CPQ catalog item format. The parent's quote-to-order flow is entirely built on `SBQQ__` objects. There is no direct object bridge.

**Solution:**

```
Coexistence design:
1. Shared org, separate quoting paths:
   - Enterprise services: Salesforce CPQ flow (unchanged)
   - Residential/SMB energy: Industries CPQ OmniScript flow (unchanged)
   - Record Type on Opportunity determines which CPQ flow launches

2. Unified reporting via a CPQ Reporting Object:
   - Create a custom junction object CPQOrderSummary__c
   - Both flows write a summary record (unit price, ARR, product family)
   - Revenue dashboards query CPQOrderSummary__c, not native CPQ objects

3. Consolidation roadmap:
   - Year 1: coexistence as described
   - Year 2: evaluate Revenue Cloud as unified target
   - Year 3: migrate Salesforce CPQ to Revenue Cloud when EOL date is announced
   - Year 4: assess Industries CPQ roadmap for utility vertical parity in Revenue Cloud

4. Governance:
   - Separate release trains for each CPQ product
   - CPQ-specific permission sets control access
   - No shared custom objects between the two CPQ namespaces
```

**Why it works:** Coexistence is viable when the two CPQ products serve genuinely different business units with different product models. The key is isolating each CPQ's object surface and avoiding shared dependencies that create deployment coupling.

---

## Anti-Pattern: Recommending Industries CPQ for a Non-Industry-Cloud Org

**What practitioners do:** A practitioner reads that Industries CPQ has "more powerful bundling" than Salesforce CPQ and recommends it for a manufacturing company on Sales Cloud + Salesforce CPQ, without checking licensing.

**What goes wrong:** Industries CPQ is only available through Communications Cloud, Energy and Utilities Cloud, Media Cloud, or Insurance/Financial Services Cloud licensing. A Sales Cloud org cannot install or use Industries CPQ. The recommendation fails at the licensing gate, wastes discovery time, and may create contractual confusion.

**Correct approach:** Always confirm cloud licensing before recommending Industries CPQ. For a manufacturing org on Sales Cloud needing more complex bundling than current Salesforce CPQ provides, the correct path is Revenue Cloud (native CPQ), not Industries CPQ.
