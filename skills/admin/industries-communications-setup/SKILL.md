---
name: industries-communications-setup
description: "Use when configuring Communications Cloud for the first time: org setup sequence, permission sets, Enterprise Product Catalog (EPC) service catalog configuration, TM Forum-aligned order decomposition, Account record-type segmentation, and contract lifecycle activation. NOT for generic OmniStudio configuration, Salesforce CPQ (SBQQ), standard B2C/B2B Commerce order management, or non-Communications Industries clouds."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
tags:
  - communications-cloud
  - enterprise-product-catalog
  - epc
  - order-management
  - industries
  - subscriber-management
  - contract-lifecycle
  - tm-forum
triggers:
  - "How do I set up Communications Cloud for the first time"
  - "configuring Enterprise Product Catalog for telecom services"
  - "Communications Cloud account hierarchy setup — Billing Account, Service Account, Consumer Account"
  - "Industries Order Management setup and order decomposition configuration"
  - "TM Forum commercial to technical order decomposition in Salesforce"
  - "we're having issues with communications cloud"
  - "model product specifications and attributes in Enterprise Product Catalog"
  - "set up attribute-based pricing for the Communications Cloud cart"
inputs:
  - "Communications Cloud license type and edition confirmed in org (check Setup > Installed Packages)"
  - "Target account model — consumer B2C or business B2B"
  - "Whether Enterprise Product Catalog EPC is already partially configured"
  - "Existing product hierarchy or legacy catalog structure if migrating"
  - "List of subscriber segment types the org must support"
outputs:
  - Org setup checklist for Communications Cloud activation
  - EPC service catalog structure recommendation
  - Account record-type segmentation design
  - Order decomposition flow (commercial to technical) guidance
  - Permission set assignment plan
  - Contract lifecycle activation sequence
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-07-06
---

# Industries Communications Setup

This skill activates when a practitioner needs to configure a Salesforce Communications Cloud org from scratch or diagnose a broken setup. It covers the mandatory sequencing of org setup steps, Enterprise Product Catalog (EPC) configuration for service catalog modeling, TM Forum-aligned order decomposition, Account record-type segmentation (Billing Account, Service Account, Consumer Account), Industries Order Management, and contract lifecycle activation.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the Communications Cloud managed package is installed: Setup > Installed Packages should show "Communications Cloud" or "Vlocity Communications". The EPC objects (Product2, vlocity_cmt__ProductChildItem__c relationship tables, and catalog assignment objects) only appear after package install.
- Confirm which account model applies: Consumer (Person Accounts may be enabled) or Business (standard Account with record types). This determines how Billing, Service, and Consumer account record types are configured.
- Determine whether the org is a greenfield setup or a migration from a legacy catalog (e.g., Amdocs, Siebel, or manual Product2 entries). Migration orgs require EPC import tooling; greenfield orgs start with EPC catalog definition.
- Most common wrong assumption: practitioners treat Communications Cloud Account records like standard CRM Accounts and query them without RecordType filters. The Account object in a Communications Cloud org is segmented into Billing Account, Service Account, and Consumer Account via RecordTypes — querying without a RecordType filter produces data integrity problems at every layer.
- Key limit to know: EPC enforces a strict parent-child catalog hierarchy. Products, bundles, and child items must be modeled in EPC, not assembled ad hoc in Product2. Attempting to configure pricing or order decomposition before the EPC catalog is structured will block downstream flows.

---

## Core Concepts

### Enterprise Product Catalog (EPC) — Service Catalog Modeling

The Enterprise Product Catalog is the canonical source of truth for all communications service offerings in a Communications Cloud org. It is not a replacement for Salesforce CPQ or the standard Product2 object in isolation — rather, EPC uses Product2 as a base record and extends it with Communications Cloud-specific child relationships, attributes, and catalog assignments.

Key EPC constructs:
- **Product Specification**: the master template for a product or service type (e.g., "Broadband Internet 100Mbps"). Defined once, reused across catalog versions.
- **Product Offering**: a market-facing bundle or individual service offer that applies a Product Specification and inherits its data shape from it, with pricing, eligibility rules, and effective dates layered on top.
- **Catalog Assignment**: links a Product Offering to one or more catalogs (Consumer, Business, Wholesale). Controls visibility per segment.
- **Child Items** (vlocity_cmt__ProductChildItem__c): parent-child relationships that model bundle decomposition — a "Triple Play Bundle" parent contains child offering references for broadband, TV, and voice.

EPC must be configured before any order decomposition flows, pricing rules, or subscriber provisioning flows can function. Skipping EPC and creating products directly in Product2 breaks order fulfillment because the decomposition engine reads EPC child item structure, not raw Product2 records.

#### The Four Specification Types

EPC defines four specification types, and choosing the right one is the first modeling decision for any new catalog entity:

| Spec Type | Purpose | Customer-Facing? |
|---|---|---|
| Offer | Sellable, market-facing entity with pricing and activation settings | Yes |
| Product | Reusable template of product data that offers inherit from | Yes |
| Service | Fulfillment-side capability that supports delivery of a product | No — not sold directly |
| Resource | Fulfillment-side asset (e.g., network element) consumed during delivery | No — not sold directly |

Service and resource specs exist to support fulfillment; only offer and product specs face the customer. Modeling a fulfillment-only component as a sellable offer (or vice versa) breaks the commercial/technical separation the decomposition engine depends on.

#### Spec Inheritance: Offers Apply Product Specs

A product spec is a reusable design-time template that carries the product's data shape. When you create a sellable offer, you apply the product spec to the offer so the offer inherits all the product data — Salesforce compares this to how a record inherits structure from an object type. Because specs are reusable, one product spec can back many differently priced offers: launch a promotional offer, a retention offer, and a standard offer off the same spec without reconfiguring the same product information from scratch each time.

#### Simple vs. Bundled Product Specs

Bundling is a spec-level modeling decision, not just a Child Item relationship. Simple product specs create standalone products with no child products; bundled product specs are specifically for parent products that have associated child products. Pick the spec subtype first, then express the concrete parent-child links (with quantities and cardinalities) as Child Item records. Assembling a parent-child bundle under a simple spec contradicts these definitions — simple specs are for standalone products without child products — and building it through custom lookups on Product2 bypasses EPC entirely (see Pattern 1).

#### Commercial vs. Technical Products

EPC formally separates the two halves of the catalog:

- **Commercial products** are the customer-facing assets available for purchase, managed by sales and marketing teams.
- **Technical products** represent the underlying back-end components that order management engineers and delivery teams use to fulfill orders.

The catalog maps commercial products to their technical products so that Order Management can decompose the order into the associated technical products during orchestration. This mapping is the catalog-side foundation of the TM Forum decomposition described in the next section — if the commercial-to-technical mapping is missing in EPC, decomposition has nothing to read.

#### Shared Catalog: The Cross-Cloud Foundation

EPC sits on **Shared Catalog**, a common foundation for all products, services, and resources used by Industries Communications, Media, and Energy & Utilities Cloud applications. Shared Catalog is included with Industries CPQ; EPC is a separately licensed layer that adds catalog entity versioning and lifecycle management on top of Shared Catalog's capabilities. Two practical consequences:

1. Catalog modeling skills (spec types, inheritance, bundling, attributes) transfer directly between Communications and Energy & Utilities implementations — see `admin/industries-energy-utilities-setup` in Related Skills.
2. When scoping a project, confirm whether the org has Shared Catalog only (via Industries CPQ) or the full EPC license — versioning and lifecycle-management features belong to EPC.

#### Attributes, Attribute Categories, and Picklists

Attributes are configurable key-value pairs on catalog items that capture product characteristics — tangible ones like size or color, and intangible ones like subscription type or SKU. The framework has three moving parts:

- **Attributes**: key-value pairs whose value, depending on configuration, is set at design time, at runtime in the CPQ Cart, or during order decomposition. Runtime attributes are what make a product configurable by the customer or sales rep in the Cart.
- **Attribute Categories**: every attribute must correspond to an attribute category, which holds a group of related attributes and organizes them into sections. Create the category before the attributes.
- **Picklists**: drive dynamic attribute value selection in the Cart. Picklists must be created before they can be linked to attributes.

Attributes also feed **attribute-based pricing rules** — price can vary based on the attribute values selected in the CPQ Cart, so configuration choices (speed tier, contract length) reprice the line without separate offerings per combination.

Know the fields-vs-attributes boundary: fields store universal product information (name, ID, description) and require administrator privileges to manage; attributes capture product-specific or class-specific details and need only Product Designer access. Modeling a per-configuration characteristic as a Product2 custom field instead of an attribute strands it outside the Cart configuration and pricing-rule machinery.

### TM Forum-Aligned Order Decomposition (Commercial to Technical Order)

Communications Cloud implements TM Forum SID (Shared Information/Data Model) TR139-aligned order decomposition. When a subscriber places an order, Communications Cloud decomposes it in two stages:

1. **Commercial Order**: the customer-facing representation of what was sold (e.g., "Add Broadband 100Mbps to account"). Stored as an Order record with associated OrderItem records referencing EPC Product Offerings.
2. **Technical Order** (Decomposed Order): the network-fulfillment representation that breaks the commercial order into atomic fulfillment actions per service component. Generated by the Industries Order Management decomposition engine reading EPC child item definitions.

Industries Order Management in Communications Cloud is **not** the same as Salesforce Order Management (part of B2C/B2B Commerce). They use different object models, different APIs, and different fulfillment engines. Conflating them leads to incorrect API calls, missing object references, and broken decomposition rules.

### Account Record-Type Segmentation

In Communications Cloud, the standard Account object is segmented by RecordType into three subtypes:

| RecordType DeveloperName | Purpose |
|---|---|
| `Billing_Account` | Holds billing address, payment method, and invoice relationships. Parent of Service Accounts. |
| `Service_Account` | Represents a service location or service grouping. Child of Billing Account, parent of subscriptions. |
| `Consumer_Account` | Represents an individual subscriber (B2C). May be linked to Person Accounts if enabled. |

These are RecordTypes on Account, not separate objects. Any SOQL query, Apex trigger, or Flow that processes Accounts in a Communications Cloud org **must** filter by `RecordType.DeveloperName` or it will mix billing, service, and consumer records, causing reporting errors, workflow misfires, and data corruption.

### Permission Sets and Setup Sequence

Communications Cloud requires specific permission sets to be assigned before any EPC configuration can proceed. Attempting to access EPC screens or run catalog APIs before permission set assignment produces silent failures or "Insufficient Privileges" errors that can be mistaken for missing metadata.

Required permission sets (names vary slightly by package version):
- `Vlocity_Communications_Admin` (or equivalent Communications Cloud Admin PS)
- `Vlocity_Communications_User` for non-admin users
- OmniStudio permission sets if OmniStudio runtime is used for order capture UIs

Permission sets must be assigned before configuring EPC catalogs, because EPC record visibility is controlled at the permission set level, not just profile level.

---

## Common Patterns

### Pattern 1: EPC Service Catalog Initialization for a New Org

**When to use:** Greenfield Communications Cloud setup where no products exist yet and EPC must be seeded before any order management work.

**How it works:**
1. Navigate to the EPC app (App Launcher > Enterprise Product Catalog).
2. Create one or more Catalogs (e.g., "Consumer Catalog", "Business Catalog") and set effective dates.
3. Create Product Specifications for each atomic service component (Broadband, Voice, TV).
4. Create Product Offerings that reference the Product Specifications, with pricing tiers attached.
5. Create bundle Product Offerings with Child Items linking to the atomic offerings.
6. Assign Product Offerings to the appropriate Catalog via Catalog Assignment records.
7. Validate the catalog by running a test quote or order capture flow against it.

**Why not the alternative:** Creating products directly in Product2 with custom fields does not populate the EPC relationship tables (ProductChildItem, CatalogAssignment). The decomposition engine reads EPC relationships, not raw Product2. Orders placed against non-EPC products will fail decomposition silently.

### Pattern 2: Account Hierarchy Setup (Billing → Service → Consumer)

**When to use:** Setting up a new subscriber, migrating an existing customer, or debugging account-related order failures.

**How it works:**
1. Create or identify the Billing Account (`RecordType.DeveloperName = 'Billing_Account'`): this holds payment and invoice information.
2. Create a Service Account (`RecordType.DeveloperName = 'Service_Account'`) as a child of the Billing Account: this represents the service address.
3. For B2C, create or link a Consumer Account (`RecordType.DeveloperName = 'Consumer_Account'`) representing the individual subscriber.
4. Validate the hierarchy by querying: `SELECT Id, Name, RecordType.DeveloperName, ParentId FROM Account WHERE RecordType.DeveloperName IN ('Billing_Account', 'Service_Account')`.
5. Ensure any order, subscription, or asset records are created on the correct account subtype.

**Why not the alternative:** Creating a single Account without RecordType assignment results in all Communications Cloud platform automations (order decomposition, billing event triggers, service provisioning) failing to associate the record with the correct processing pipeline.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Setting up products for order capture | Configure in EPC (Product Specification → Product Offering → Catalog Assignment) | Order decomposition engine reads EPC; direct Product2 creation bypasses decomposition |
| Modeling a new catalog entity | Pick the spec type first: offer/product for customer-facing, service/resource for fulfillment-only | Spec type determines visibility and purpose; service and resource specs are never sold directly |
| Several price points for the same product | One product spec, multiple offers that apply it | Each offer inherits the spec's product data — no reconfiguring the same product information per offer |
| Bundle vs. standalone product | Choose bundled vs. simple product spec at the spec level, then add Child Items | Bundling is a spec-level decision; Child Items express the concrete parent-child links |
| Per-configuration characteristic (speed tier, contract length) | Model as an attribute in an attribute category, with a picklist if Cart-selectable | Attribute values can be set in the Cart or at decomposition and can drive attribute-based pricing; Product2 custom fields cannot |
| Customer account creation | Create Billing Account first, then Service Account as child | Account hierarchy is required for billing and provisioning linkage |
| Querying accounts in Apex or Flow | Always filter by `RecordType.DeveloperName` | Without filter, all account subtypes mix, causing data integrity failures |
| Order management APIs | Use Industries Order Management (vlocity_cmt namespace) APIs | Salesforce Order Management (commerce) uses different object model and APIs |
| Permission errors in EPC config screens | Assign Communications Cloud Admin permission set before configuring EPC | EPC visibility is permission-set gated, not just profile-based |
| Contract lifecycle activation | Activate contract through Industries Contract Management sequence, not standard Contract object workflow | Standard Contract activation does not trigger Industries entitlement and provisioning flows |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner setting up or validating a Communications Cloud org:

1. **Verify package install and permission sets** — Check Setup > Installed Packages for Communications Cloud or Vlocity Communications. Assign the Communications Cloud Admin permission set to the implementing user before any configuration begins. Confirm EPC app appears in App Launcher.

2. **Design and confirm the account model** — Determine if the org is B2C (Consumer Accounts, possibly Person Accounts) or B2B (Billing + Service Account hierarchy). Document the RecordType DeveloperNames that will be used. Validate that RecordTypes for `Billing_Account`, `Service_Account`, and `Consumer_Account` exist on the Account object in Setup > Object Manager.

3. **Build the EPC service catalog** — In the EPC app, create Catalogs (one per market segment), then specs with the correct type for each entity: product specs for customer-facing templates (simple or bundled, decided at the spec level), service and resource specs for fulfillment-only components. Create Product Offerings that apply the product specs (inheriting their data shape) with pricing attached, bundle offerings with Child Items, and Catalog Assignments linking offerings to catalogs. Define attribute categories, picklists, and attributes for any characteristic the Cart or decomposition must configure. Do not bypass EPC and create offerings in raw Product2.

4. **Configure order decomposition rules** — In Industries Order Management, define the decomposition rules that map commercial order line items to technical fulfillment actions. Reference the EPC Child Item relationships defined in Step 3. Test decomposition by submitting a sample order and verifying that technical order records are generated.

5. **Activate contract lifecycle** — Configure Industries Contract Management for the subscriber contract types in scope (e.g., service agreements, device financing). Activate contracts through the Industries contract activation sequence, not the standard Contract object workflow, to ensure entitlement and provisioning flows fire.

6. **Validate the end-to-end subscriber flow** — Create a test Billing Account, add a Service Account child, place a test order against an EPC-cataloged offering, verify order decomposition generates technical order records, and confirm the contract is activated. Review any OmniStudio flows used for order capture and confirm they reference EPC catalog data.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Communications Cloud managed package confirmed installed in Setup > Installed Packages
- [ ] Communications Cloud Admin permission set assigned before EPC configuration
- [ ] EPC service catalog contains at least one Catalog, Product Specification, Product Offering, and Catalog Assignment
- [ ] Every spec uses the correct type — offer/product for customer-facing entities, service/resource for fulfillment-only components
- [ ] Bundles use bundled product specs at the spec level plus Child Items, not custom lookups or simple specs with ad hoc children
- [ ] Configurable characteristics modeled as attributes (each in an attribute category), with picklists created before linking to attributes
- [ ] Account RecordTypes (`Billing_Account`, `Service_Account`, `Consumer_Account`) confirmed present on Account object
- [ ] All SOQL queries and Apex that touch Account include a `RecordType.DeveloperName` filter
- [ ] Industries Order Management decomposition rules configured and tested (distinct from Salesforce Order Management)
- [ ] Contract lifecycle activation uses Industries contract activation, not standard Contract workflow
- [ ] No products created directly in Product2 without corresponding EPC Product Offering and Catalog Assignment
- [ ] End-to-end subscriber flow tested: account creation → order capture → order decomposition → contract activation

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **EPC objects are invisible without the package** — If the Communications Cloud managed package is not installed, EPC configuration screens and objects (ProductChildItem, CatalogAssignment) do not exist. Admins attempting to configure EPC before package install will find no App Launcher entry and no objects in Object Manager. Always confirm Installed Packages before starting any EPC work.

2. **RecordType DeveloperName vs. Name on Account** — Communications Cloud RecordType filtering must use `RecordType.DeveloperName`, not `RecordType.Name`. `RecordType.Name` is locale-sensitive and changes when orgs are deployed to different language environments. Queries using `RecordType.Name = 'Billing Account'` will break in non-English orgs or after translation workbench changes.

3. **Industries Order Management ≠ Salesforce Order Management** — These are two separate platforms with separate object models, APIs, and deployment requirements. Salesforce Order Management (part of B2C/B2B Commerce) uses `OrderSummary`, `FulfillmentOrder`, and Commerce APIs. Industries Order Management uses vlocity_cmt namespace objects and decomposition rules. Attempting to use Commerce APIs for Communications Cloud order fulfillment will produce missing field errors and silent fulfillment failures.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Org setup checklist | Step-by-step verification list for Communications Cloud activation |
| EPC catalog structure | Recommended Product Specification → Product Offering → Catalog Assignment hierarchy |
| Account segmentation design | RecordType mapping for Billing, Service, and Consumer accounts with query patterns |
| Order decomposition flow diagram | Commercial-to-technical order flow with EPC child item references |
| Permission set assignment plan | List of Communications Cloud permission sets and assignment sequence |
| Contract lifecycle sequence | Industries contract activation steps with entitlement flow validation |

---

## Related Skills

- `architect/industries-data-model` — Use for understanding the full Industries data model across Communications, Insurance, Energy & Utilities, and Health Cloud, including Account subtype SOQL patterns
- `omnistudio/omnistudio-custom-components` — Use when customizing OmniStudio-based order capture UIs within a Communications Cloud org
- `admin/industries-energy-utilities-setup` — Use when configuring Energy & Utilities Cloud; both clouds' catalogs sit on the same Shared Catalog foundation (along with Media Cloud), so spec-type, inheritance, bundling, and attribute patterns carry over, as do the account hierarchy and Industries Order Management patterns
