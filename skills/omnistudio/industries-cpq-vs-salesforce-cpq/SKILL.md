---
name: industries-cpq-vs-salesforce-cpq
description: "Use this skill when comparing Industries CPQ (formerly Vlocity CPQ) with Salesforce CPQ (Revenue Cloud managed package) — covering feature parity, decision criteria, migration paths, and coexistence patterns. Trigger keywords: Vlocity CPQ, Industries CPQ, Salesforce CPQ comparison, Revenue Cloud migration, CPQ selection, which CPQ to use. NOT for implementing, configuring, or debugging either CPQ product."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Operational Excellence
triggers:
  - "Should we use Industries CPQ or Salesforce CPQ for our telco/insurance/utilities project?"
  - "We are migrating from Vlocity CPQ to native OmniStudio — what do we need to know?"
  - "What is the difference between Industries CPQ and Revenue Cloud, and which fits our enterprise sales process?"
tags:
  - industries-cpq
  - vlocity-cpq
  - salesforce-cpq
  - revenue-cloud
  - cpq-comparison
  - omnistudio
  - migration
inputs:
  - "Industry vertical and business segment (telco, utilities, insurance, high-tech, manufacturing)"
  - "Current CPQ investment: Vlocity/Industries CPQ version, Salesforce CPQ managed package version"
  - "Complexity profile: product catalog size, pricing tiers, bundling depth, guided selling requirements"
  - "Roadmap alignment: Revenue Cloud adoption plans, OmniStudio licensing status"
outputs:
  - "Decision framework recommending Industries CPQ vs Salesforce CPQ (or coexistence) with rationale"
  - "Migration path summary from current CPQ state to target state"
  - "Risk register of top switching costs and platform constraints"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Industries CPQ vs Salesforce CPQ

Use this skill when a practitioner or org must choose between Industries CPQ (formerly Vlocity CPQ, now the OmniStudio-native CPQ) and Salesforce CPQ (the managed-package product, now entering end-of-sale as of March 2025 and being superseded by Revenue Cloud). This skill provides comparison facts, decision criteria, and migration path guidance. It does not implement either product.

---

## Before Starting

Gather this context before advising on CPQ selection or migration:

- Confirm which Salesforce CPQ product is actually in scope. "Revenue Cloud" is now Salesforce's preferred successor to Salesforce CPQ (the managed package). Industries CPQ is a separate product for communications, media, energy, and insurance verticals. These are not the same thing.
- Identify the org's industry vertical — telco, utilities, insurance, high-tech, or manufacturing. This is the single strongest selection driver.
- Confirm whether OmniStudio is already licensed and deployed. Industries CPQ requires OmniStudio and cannot operate without it.
- Identify the managed-package version of Salesforce CPQ currently deployed (if any). The managed package introduces namespace pollution and version lock-in that affects migration complexity.

---

## Core Concepts

### Industries CPQ (Formerly Vlocity CPQ)

Industries CPQ is Salesforce's industry-specific configuration, pricing, and quoting product, built natively on OmniStudio primitives. Its core components are:

- **Calculation Procedures**: declarative pricing-engine rules that replace custom Apex pricing logic. They execute server-side and support complex, attribute-driven pricing trees.
- **DataRaptors**: data transformation components that read and write Salesforce data. DataRaptors handle catalog lookups, product attribute hydration, and cart data preparation.
- **OmniScripts**: guided-selling UI flows that walk the sales representative step by step through product selection, configuration, and quoting. OmniScripts replace the Salesforce CPQ Quote Line Editor for industry catalog scenarios.
- **Vlocity Cards / FlexCards**: responsive product and cart display components embedded inside OmniScripts or standalone pages.
- **Product Catalog**: products modeled as catalog items with attributes (not standard Pricebook Entries). Bundles can be multi-level with cardinality rules, exclusion rules, and compatibility constraints.

Industries CPQ is the required CPQ engine for Communications Cloud, Energy and Utilities Cloud, Media Cloud, and Insurance/Financial Services product-selling use cases. It is deployed via DataPacks and managed through OmniStudio's own deployment tooling.

### Salesforce CPQ (Managed Package / Revenue Cloud Predecessor)

Salesforce CPQ is a managed package (`SBQQ__`) that installs on top of Sales Cloud. Its core components are:

- **Products and Price Books**: standard Salesforce products with price book entries. Bundles are configured through parent-child product relationships and product options.
- **Quote Line Editor (QLE)**: the native CPQ UI for adding products, applying discounts, and configuring bundles. It operates inside a standard Salesforce page.
- **Pricing Rules**: Apex-based or declarative rules that fire on the QLE to apply discounts, fees, and price adjustments.
- **Approval Rules and Approval Chains**: multi-level discount approval workflows with automated routing.
- **Contracts and Amendments**: structured contract lifecycle with amendment quoting, renewal quoting, and subscription management.
- **Salesforce Billing (add-on)**: invoicing, payment, and revenue recognition built on top of CPQ contracts.

As of March 2025, Salesforce CPQ is in end-of-sale. Existing customers can renew and continue using the product. Salesforce is no longer selling Salesforce CPQ to new customers. The strategic successor is **Revenue Cloud** (formerly Revenue Lifecycle Management / RLM), which is built natively on the Salesforce platform (no managed package) and includes CPQ, Billing, and Contract Lifecycle Management as first-party objects.

### Revenue Cloud (The New Native CPQ)

Revenue Cloud is Salesforce's on-core replacement for the Salesforce CPQ managed package. Key differences from the managed package:

- No `SBQQ__` namespace. Objects are native Salesforce objects.
- Uses a product catalog built on standard objects (`ProductCatalog`, `ProductCategory`, `PriceBook`).
- Includes a Product Configurator for guided selling built on LWC (not OmniStudio).
- Scale Cache optimizes pricing SOQL to reduce governor-limit pressure.
- Includes native CLM (Contract Lifecycle Management) without a third-party add-on.

Revenue Cloud is distinct from Industries CPQ. They share some OmniStudio underpinnings in certain clouds but are separate products with separate licensing.

### Feature Comparison Matrix

| Capability | Industries CPQ | Salesforce CPQ (managed package) | Revenue Cloud (native) |
|---|---|---|---|
| Product modeling | Attribute-based catalog items, multi-level bundles | Pricebook entries, product options, product rules | Native product catalog objects, LWC configurator |
| Pricing engine | Calculation Procedures (declarative, server-side) | Pricing rules + Apex plugins | Price waterfall, scale cache |
| Guided selling UI | OmniScripts + FlexCards | Quote Line Editor (managed package UI) | LWC Product Configurator |
| Bundle complexity | Deep multi-level, cardinality and exclusion rules | Two-level bundles, option constraints | Multi-level via product categories |
| Subscription billing | Industry-specific contract assets | Salesforce Billing add-on | Native billing included |
| Approval workflows | Managed via OmniStudio flows | Native CPQ approval chains | Native approval flows |
| Contract amendments | Asset-based amendment via cart | CPQ amendment quotes | Native amendment transactions |
| Industry-specific content | Telco, energy, insurance workflows built-in | Generic enterprise, partner ecosystem | Generic + industry overlay with add-ons |
| Deployment tooling | DataPacks + OmniStudio CLI | Managed package installer + Metadata API | Metadata API, SFDX |
| Integration with OmniStudio | Native — required | Not required, limited integration | Partial — LWC-first, optional OmniStudio |
| End-of-sale status | Active / strategic | End-of-sale March 2025 | Active / strategic |

---

## Common Patterns

### Pattern 1: Industry-Vertical Selection (Communications / Energy / Insurance)

**When to use:** The org operates in telecommunications, media, energy, utilities, or insurance and needs product bundling with complex attribute-based pricing (e.g., a telco quoting mobile plans with add-on features, SIM quantities, and installation fees).

**How it works:**
1. Industries CPQ is the required product — its Calculation Procedures and OmniScript guided-selling flows are built for this shape of problem.
2. The product catalog is modeled as catalog items with attributes rather than Pricebook Entries. Bundles use cardinality rules and compatibility constraints.
3. DataRaptors read existing account and asset data to pre-populate the cart with the customer's current service configuration.
4. The OmniScript walks the sales rep through the guided-selling flow, and the Calculation Procedure fires on the cart to apply tiered pricing.
5. Output is a CPQ order, which integrates downstream to order management or BSS/OSS systems via Integration Procedures.

**Why not Salesforce CPQ:** Salesforce CPQ's product-option model does not support attribute-based pricing natively. Modeling a telco catalog in Salesforce CPQ requires heavy Apex plugin development and typically results in a brittle system that cannot scale to thousands of catalog items.

### Pattern 2: Enterprise B2B Sales with Subscriptions and Approvals

**When to use:** The org runs a standard enterprise B2B sales process: reps build quotes for software subscriptions or professional services, discounts require approval chains, quotes convert to contracts, and renewals are automated.

**How it works:**
1. Salesforce CPQ (or Revenue Cloud for new implementations) fits natively.
2. Products and price books are configured using standard CPQ administration.
3. Discount approval chains handle multi-tier approval routing.
4. Contracts are generated from closed-won quotes; amendments and renewals are managed through CPQ's built-in flow.
5. For new implementations, Revenue Cloud is the correct choice. For existing Salesforce CPQ deployments, plan a migration to Revenue Cloud when contract renewal cycles allow.

**Why not Industries CPQ:** Industries CPQ adds OmniStudio licensing cost and deployment complexity that is not warranted for a generic enterprise sales process without industry-specific catalog requirements.

### Pattern 3: Coexistence of Both CPQ Products in One Org

**When to use:** A large enterprise has acquired a telco or utility subsidiary that runs Industries CPQ, while the parent company runs Salesforce CPQ for its enterprise sales process.

**How it works:**
1. Both products can technically coexist in a single org. There is no platform-level prohibition.
2. Shared objects (Account, Contact, Opportunity) are used by both products.
3. Quote objects differ: Salesforce CPQ uses `SBQQ__Quote__c`; Industries CPQ generates CPQ orders, not Salesforce CPQ quote objects.
4. Separate page layouts, record types, and profiles are used to control which UI each user population sees.
5. Reporting must account for the two different quote/order objects.

**Why this is high-risk:** Coexistence adds licensing cost for both products, doubles the release management surface area, and creates confusion when Salesforce CPQ reaches end-of-maintenance. Prefer consolidation to one product within a defined roadmap horizon.

---

## Decision Guidance

| Situation | Recommended CPQ | Reason |
|---|---|---|
| Net-new telco, energy, media, or insurance selling use case | Industries CPQ | Industry catalog structures, attribute-based pricing, and OmniScript guided-selling are required. Salesforce CPQ cannot model these natively. |
| Net-new enterprise B2B sales, subscriptions, services | Revenue Cloud (native) | Salesforce CPQ is end-of-sale. Revenue Cloud is the strategic platform with the same feature footprint and no managed-package constraints. |
| Existing Salesforce CPQ managed package deployment, stable | Keep Salesforce CPQ, plan Revenue Cloud migration | Forced migration has high cost. Plan migration when contract renewal or business process change creates a natural window. |
| Existing Vlocity CPQ (pre-OmniStudio) deployment | Migrate to Industries CPQ (native OmniStudio) | Vlocity-branded CPQ requires migration to the native OmniStudio platform as part of Salesforce's Industries cloud evolution. |
| Org with OmniStudio licensed but no CPQ yet | Industries CPQ if industry-vertical; Revenue Cloud otherwise | OmniStudio license implies an industry cloud context. Confirm vertical before recommending. |
| Acquisition: one entity on Industries CPQ, other on Salesforce CPQ | Coexistence short-term, consolidation roadmap required | Coexistence is viable but costly. Consolidation target depends on which entity is the operational anchor. |
| Migration from Salesforce CPQ to Industries CPQ | Not recommended as a general pattern | These products solve different problems. Cross-migration is only warranted if the business model shifts to an industry vertical that Industries CPQ is built for. |

---

## Recommended Workflow

Step-by-step for an AI agent or practitioner working on CPQ selection or migration planning:

1. **Identify the business model and vertical.** Confirm whether the selling motion is industry-catalog-based (telco, energy, insurance) or enterprise-subscription-based (software, services, manufacturing). This is the primary selection driver and must be answered before any other analysis.
2. **Audit current CPQ state.** Determine whether Salesforce CPQ is already deployed (managed package version), whether Industries CPQ / Vlocity CPQ is deployed, and what the OmniStudio licensing status is. Check whether the org is running legacy Vlocity-branded components that predate native OmniStudio.
3. **Map the required CPQ capabilities.** For each key business requirement (product catalog depth, pricing engine complexity, guided selling, approval workflows, contract lifecycle, billing), identify which CPQ product satisfies it natively vs. requires customization.
4. **Apply the decision table.** Use the Decision Guidance section above. If the outcome is Industries CPQ, confirm OmniStudio licensing is in place. If the outcome is Revenue Cloud, confirm the Salesforce CPQ end-of-sale timeline and migration readiness.
5. **Define the migration path.** For Vlocity CPQ to native Industries CPQ: use the DataPacks migration tooling and follow Salesforce's official Industries CPQ DataPacks migration guide. For Salesforce CPQ to Revenue Cloud: follow Salesforce's Revenue Cloud migration documentation including data model mapping for `SBQQ__` objects to native Revenue Cloud objects.
6. **Document coexistence risks if both products will run simultaneously.** Identify the shared object surface (Account, Opportunity), separate the quote/order object paths, and set a consolidation target date.
7. **Validate with official Salesforce sources.** Feature availability changes between releases. Confirm current feature parity using the Salesforce Industries CPQ documentation and Revenue Cloud release notes before finalizing the recommendation.

---

## Review Checklist

- [ ] Industry vertical confirmed and mapped to correct CPQ product
- [ ] OmniStudio license status confirmed if recommending Industries CPQ
- [ ] Salesforce CPQ end-of-sale timeline communicated if existing managed-package deployment is in scope
- [ ] Migration path documented with reference to official DataPacks migration or Revenue Cloud migration guide
- [ ] Coexistence risks and consolidation timeline documented if both products will coexist
- [ ] Feature parity gaps identified and documented for the recommended product
- [ ] Official Salesforce sources consulted and cited for any platform behavior claims

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Industries CPQ requires OmniStudio licensing — it is not included in Sales Cloud** — Industries CPQ is part of the Industry clouds (Communications Cloud, Energy and Utilities Cloud, Media Cloud, etc.). Orgs that do not have an Industries cloud license do not have access to Industries CPQ, Calculation Procedures, or the OmniStudio primitives it depends on. A practitioner recommending Industries CPQ for a non-industry-cloud org will hit a hard licensing wall before any configuration begins.

2. **Salesforce CPQ managed package introduces namespace lock-in** — All CPQ objects, fields, and Apex are namespaced under `SBQQ__`. Custom code, reports, flows, and integrations that reference these objects become tightly coupled to the managed package. When migrating to Revenue Cloud, every `SBQQ__Quote__c` reference must be remapped to the native Revenue Cloud transaction object. This remapping effort is frequently underestimated.

3. **Vlocity CPQ DataPacks and native OmniStudio DataPacks are not identical** — Orgs running legacy Vlocity CPQ (pre-Salesforce acquisition branding) may have DataPacks that use Vlocity-branded component types (`%vlocity_namespace%`). These DataPacks do not deploy cleanly to orgs running native OmniStudio without a namespace migration step. Attempting to use the standard OmniStudio CLI against legacy Vlocity DataPacks will produce schema mismatch errors.

4. **Industries CPQ cart and Salesforce CPQ quote objects are incompatible** — Industries CPQ produces CPQ order line items on Salesforce's order and asset objects. Salesforce CPQ produces `SBQQ__QuoteLine__c` records. There is no native bridge between these object models. Orgs attempting to coexist both products must maintain two separate quoting flows and cannot share a unified quote-to-order pipeline without custom integration.

5. **Revenue Cloud is not yet feature-complete relative to Salesforce CPQ managed package** — As of Spring '25, Revenue Cloud does not have full parity with every Salesforce CPQ feature (notably some partner community quoting patterns and some legacy billing configurations). Practitioners must verify specific feature availability in current release notes before committing to a Revenue Cloud migration date.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CPQ selection recommendation | Written decision rationale documenting which CPQ product is recommended, why, and what alternatives were considered |
| Migration path summary | Step-by-step migration path from current CPQ state to target state, with tooling references |
| Feature gap register | Table of required capabilities mapped to each CPQ product, noting native support, customization required, or not supported |
| Coexistence risk register | If both products will coexist, a risk register covering shared objects, separate UI paths, reporting gaps, and consolidation timeline |

---

## Related Skills

- `omnistudio-deployment-datapacks` — Use when executing the actual DataPacks migration from Vlocity CPQ to native OmniStudio Industries CPQ
- `omnistudio-performance` — Use when tuning Calculation Procedures and DataRaptor performance in an Industries CPQ implementation
- `multi-org-strategy` — Use when the CPQ selection decision is complicated by a multi-org or post-acquisition org structure
