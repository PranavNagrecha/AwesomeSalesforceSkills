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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
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
- **Product Offering**: a market-facing bundle or individual service offer derived from a Product Specification, with pricing, eligibility rules, and effective dates.
- **Catalog Assignment**: links a Product Offering to one or more catalogs (Consumer, Business, Wholesale). Controls visibility per segment.
- **Child Items** (vlocity_cmt__ProductChildItem__c): parent-child relationships that model bundle decomposition — a "Triple Play Bundle" parent contains child offering references for broadband, TV, and voice.

EPC must be configured before any order decomposition flows, pricing rules, or subscriber provisioning flows can function. Skipping EPC and creating products directly in Product2 breaks order fulfillment because the decomposition engine reads EPC child item structure, not raw Product2 records.

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

3. **Build the EPC service catalog** — In the EPC app, create Catalogs (one per market segment), Product Specifications for each service component, Product Offerings with pricing, bundle Product Offerings with Child Items, and Catalog Assignments linking offerings to catalogs. Do not bypass EPC and create offerings in raw Product2.

4. **Configure order decomposition rules** — In Industries Order Management, define the decomposition rules that map commercial order line items to technical fulfillment actions. Reference the EPC Child Item relationships defined in Step 3. Test decomposition by submitting a sample order and verifying that technical order records are generated.

5. **Activate contract lifecycle** — Configure Industries Contract Management for the subscriber contract types in scope (e.g., service agreements, device financing). Activate contracts through the Industries contract activation sequence, not the standard Contract object workflow, to ensure entitlement and provisioning flows fire.

6. **Validate the end-to-end subscriber flow** — Create a test Billing Account, add a Service Account child, place a test order against an EPC-cataloged offering, verify order decomposition generates technical order records, and confirm the contract is activated. Review any OmniStudio flows used for order capture and confirm they reference EPC catalog data.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Communications Cloud managed package confirmed installed in Setup > Installed Packages
- [ ] Communications Cloud Admin permission set assigned before EPC configuration
- [ ] EPC service catalog contains at least one Catalog, Product Specification, Product Offering, and Catalog Assignment
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
- `admin/industries-energy-utilities-setup` — Use when configuring Energy & Utilities Cloud; shares similar account hierarchy and Industries Order Management patterns
