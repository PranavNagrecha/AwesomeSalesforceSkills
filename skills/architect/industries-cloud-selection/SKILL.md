---
name: industries-cloud-selection
description: "Use this skill when selecting which Salesforce Industries (vertical) cloud fits a customer's industry and requirements — evaluating data model compatibility, licensing implications, and customization vs configuration tradeoffs before committing to a vertical cloud. Trigger keywords: which industry cloud should I use, Communications Cloud vs Health Cloud, Industries licensing, vertical cloud selection, Salesforce Industries portfolio, industry cloud comparison. NOT for implementation of any individual vertical cloud — this skill covers pre-purchase and pre-implementation selection only, not configuration, data migration, or OmniStudio component development."
category: architect
salesforce-version: "Spring '26+"
well-architected-pillars:
  - Reliability
  - Scalability
  - Operational Excellence
triggers:
  - "Which Salesforce industry cloud should I use for insurance or financial services?"
  - "Does Communications Cloud include the objects I need for telecom order management?"
  - "What licenses do I need for Salesforce Insurance Cloud and what is included?"
  - "How do I decide between Health Cloud and Financial Services Cloud for my use case?"
  - "Is OmniStudio platform-native or managed package in my org and does it matter?"
tags:
  - industries-cloud
  - vertical-cloud
  - platform-selection
  - licensing
  - architect
  - communications-cloud
  - health-cloud
  - insurance-cloud
  - energy-utilities-cloud
  - financial-services-cloud
  - industries-portfolio
inputs:
  - "Industry vertical the customer operates in (e.g., Telecommunications, Insurance, Utilities, Healthcare, Financial Services)"
  - "Core business processes that must be supported (order management, policy administration, service point management, etc.)"
  - "Standard objects the solution requires (e.g., InsurancePolicy, ServicePoint, BillingAccount, EnterpriseProduct)"
  - "Whether the customer is a new Salesforce customer or migrating an existing org to an industry cloud"
  - "OmniStudio deployment model preference: platform-native (Spring '26+) vs managed package"
  - "Budget and license tier information if available (Growth vs Enterprise edition)"
  - "Hyperforce org or legacy infrastructure"
outputs:
  - "Vertical cloud recommendation with documented rationale per requirement"
  - "Data model compatibility assessment listing required standard objects and which license provides them"
  - "Customization vs configuration tradeoff analysis for the chosen vertical"
  - "OmniStudio packaging decision guidance (platform-native vs managed package)"
  - "Open questions log for items that could change the recommendation"
  - "License and module dependency map (e.g., Insurance requires FSC base)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# Industries Cloud Selection

This skill activates when a practitioner or architect must determine which Salesforce Industries vertical cloud fits a customer's industry, data model requirements, and licensing constraints. It produces a structured vertical cloud recommendation grounded in data model compatibility, standard object availability, and license gating. It does not cover implementation, configuration, OmniStudio component development, or data migration after the cloud has been selected.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Identify the required standard objects first.** Salesforce Industries clouds are license-gated, and the key selection driver is which vertical cloud's license provides the standard objects the solution actually needs. Ask: "What standard objects — InsurancePolicy, ServicePoint, BillingAccount, EnterpriseProduct — does this solution require?" before evaluating any other factor.
- **Most common wrong assumption:** Practitioners frequently assume that standard objects like `InsurancePolicy`, `ServicePoint`, or `BillingAccount` are available in a base Salesforce org or that they can be created as custom objects as a substitute. They cannot. These objects only exist in orgs licensed for the corresponding vertical cloud. No license means no object, no data, no solution.
- **OmniStudio packaging is now a one-way door.** As of Spring '26, new orgs provisioned with a Salesforce Industries license receive OmniStudio platform-native (included in the core Salesforce platform). Opening a managed-package OmniStudio component in the Standard Designer to convert it to platform-native is a one-way migration — the component can no longer be edited in the managed-package designer afterward.
- **License modules are additive, not interchangeable.** Several vertical clouds are built on a base cloud and require both licenses. For example, Insurance Cloud requires Financial Services Cloud (FSC) as its base layer. Purchasing Insurance Cloud modules without FSC is not a valid configuration.

---

## Core Concepts

### Salesforce Industries Is a License-Gated Portfolio — Not a Configuration Option

Salesforce Industries is a portfolio of vertical-specific cloud products, each delivered as a separately licensed addition to the Salesforce Platform. Each vertical cloud adds a distinct set of standard Salesforce objects, industry-specific data models, pre-built OmniStudio components, and business rules that are not available in a standard Salesforce org.

This means vertical cloud selection is primarily a **data model compatibility decision**:
- If a solution requires `InsurancePolicy`, the org must be licensed for Insurance Cloud.
- If a solution requires `ServicePoint` or `UtilityAccount`, the org must be licensed for Energy & Utilities Cloud.
- If a solution requires `BillingAccount` or `ProductCatalog` with TM Forum–aligned order decomposition, the org must be licensed for Communications Cloud.

No configuration workaround, custom object substitution, or AppExchange alternative replaces the license-gated standard objects. These objects carry pre-built relationships, validation rules, platform behavior, and integration hooks designed for the vertical — reimplementing them in custom objects loses all of that.

### Vertical Cloud Standard Object Landscape

Each vertical cloud introduces a characteristic set of standard objects that anchor the data model:

| Vertical Cloud | Anchor Standard Objects | Key Capability Signature |
|---|---|---|
| Communications Cloud | `BillingAccount`, `EnterpriseProduct`, `ProductCatalog`, `Order` (decomposed) | TM Forum–aligned order decomposition, Enterprise Product Catalog (EPC), multi-level billing hierarchy |
| Insurance Cloud | `InsurancePolicy`, `InsurancePolicyCoverage`, `InsurancePolicyParticipant` | Policy lifecycle management; **requires FSC base license** |
| Energy & Utilities Cloud | `ServicePoint`, `UtilityAccount`, `RatePlan`, `ServicePointReading` | CIS-authoritative service point management, RatePlan sync from billing system |
| Financial Services Cloud (FSC) | `FinancialAccount`, `FinancialHolding`, `AssetsAndLiabilities`, `FinancialGoal` | Household data model, relationship groups, wealth and banking objects |
| Health Cloud | `ClinicalEncounter`, `CarePlan`, `CarePlanTemplate`, `MemberPlan` | Clinical data model, care plan management, member/patient 360 |
| Public Sector Solutions | `BusinessLicense`, `BusinessRegulatoryAuthorization`, `VisitInventory` | Permitting, licensing, inspections, case management for government |
| Automotive Cloud | `Vehicle`, `Fleet`, `DriverQualification`, `MaintenanceAsset` | Vehicle and fleet lifecycle, dealer management |
| Nonprofit Cloud (Agentforce Nonprofit) | `Donation`, `FundraisingCampaign`, `ProgramEngagement`, `Benefit` | Fundraising, program management, case management for nonprofits |
| Manufacturing Cloud | `SalesAgreement`, `AccountProductForecast`, `RunRate` | Sales agreements, account-based forecasting, run-rate management |
| Consumer Goods Cloud | `RetailStore`, `AssortmentProduct`, `VisitObjective` | Route accounting, retail execution, trade promotion |
| Education Cloud | `CourseOffering`, `CourseConnection`, `AcademicTerm`, `ProgramEnrollment` | Student lifecycle, academic planning, advising |

### OmniStudio Packaging: Platform-Native vs Managed Package

OmniStudio is the low-code tooling layer shared across all Salesforce Industries clouds. As of Spring '26, new Industries-licensed orgs receive OmniStudio as a platform-native feature included in the Salesforce Platform (no separate managed package required). Existing orgs provisioned before this change may still run the OmniStudio managed package.

This packaging decision has permanent architectural consequences:
- **Platform-native OmniStudio** stores components as Salesforce metadata (deployable via Metadata API, versioned in source control, available in scratch orgs).
- **Managed-package OmniStudio** stores components in managed package namespaces not visible to standard metadata retrieval.
- **The migration from managed package to platform-native is one-way.** Once a component is opened in the Standard Designer and converted, it cannot be returned to the managed-package designer.
- Selection must confirm which model the org uses before recommending component design patterns.

### Customization vs Configuration in Vertical Clouds

Each vertical cloud offers a spectrum of extension options:

- **Configuration:** Using the industry-standard objects, page layouts, record types, and pre-built OmniStudio flows without modification. This is the fastest path to value and carries the lowest upgrade risk.
- **OmniStudio customization:** Building or extending OmniScripts, FlexCards, DataRaptors, and Integration Procedures to adapt standard components to customer-specific processes. These components are versioned and can be upgraded independently.
- **Apex and Flow customization:** Extending the vertical cloud's data model with custom fields, custom objects, Apex triggers, and Flow automation layered on top of industry standard objects.
- **Anti-pattern:** Replacing industry standard objects with custom objects when the standard object's behavior is undesirable — this destroys upgrade compatibility and eliminates the data model advantages that justified the license purchase.

---

## Common Patterns

### Pattern 1: Object-First Vertical Selection

**When to use:** A new customer or internal team is evaluating which Salesforce Industries license to purchase, and the primary driver is functional requirements, not industry affiliation.

**How it works:**
1. List every business entity the solution must model (e.g., "policy," "covered vehicle," "premium payment").
2. Map each entity to the nearest Salesforce standard object across vertical clouds using the object landscape table above.
3. Identify which vertical cloud license provides the maximum coverage of required standard objects.
4. Flag any entities not covered by any vertical and plan for custom object extensions layered on top.
5. Confirm license dependencies (e.g., if Insurance objects are required, FSC base is also required).

**Why not the alternative:** Selecting a vertical cloud based on industry name alone (e.g., "we are a financial services firm so we need FSC") without checking which specific standard objects are required can result in a mismatch — a fintech firm processing insurance policies needs Insurance Cloud (which builds on FSC), not FSC alone.

### Pattern 2: Greenfield vs Retrofit Assessment

**When to use:** An existing Salesforce customer is considering adding an Industries license to their current org.

**How it works:**
1. Audit existing custom objects that duplicate standard vertical cloud objects (e.g., a custom `Policy__c` object when `InsurancePolicy` is about to become available).
2. Assess migration cost: migrating from custom objects to industry standard objects requires data migration, field remapping, and process rebuild.
3. Compare retrofit cost against greenfield org cost.
4. Confirm the existing org's OmniStudio packaging model (managed package or platform-native) before planning any OmniStudio component work.
5. Evaluate whether a new sandbox provisioned with the Industries license can serve as a proof-of-concept before full commitment.

**Why not the alternative:** Adding an Industries license to a mature org without auditing the existing data model leads to object conflicts, naming collisions, and expensive migration work that was not scoped in the project estimate.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Customer requires policy lifecycle, coverage, and participant tracking | Insurance Cloud (+ FSC base) | `InsurancePolicy` and `InsurancePolicyCoverage` are only available with Insurance Cloud license |
| Customer requires TM Forum-aligned order decomposition and multi-product catalog | Communications Cloud | Enterprise Product Catalog and order decomposition are Communications Cloud-specific |
| Customer requires service point management with CIS billing system sync | Energy & Utilities Cloud | `ServicePoint` and `RatePlan` sync to CIS authoritative billing systems are E&U Cloud-specific |
| Customer requires household relationship model and financial accounts | Financial Services Cloud | `FinancialAccount`, `FinancialHolding`, and household data model are FSC-specific |
| Customer requires clinical encounters, care plans, and member management | Health Cloud | `ClinicalEncounter`, `CarePlan`, and `MemberPlan` are Health Cloud-specific |
| Customer is a government agency requiring permitting and licensing | Public Sector Solutions | `BusinessLicense` and `BusinessRegulatoryAuthorization` are PSS-specific |
| Customer requires vehicle and fleet lifecycle management | Automotive Cloud | `Vehicle` and `Fleet` standard objects are Automotive Cloud-specific |
| Customer requires sales agreements and run-rate forecasting | Manufacturing Cloud | `SalesAgreement` and `AccountProductForecast` are Manufacturing Cloud-specific |
| New org on Spring '26+ | Platform-native OmniStudio | All new orgs provision OmniStudio as platform-native; no managed package needed |
| Existing org with managed-package OmniStudio components to migrate | Plan migration carefully; migration is one-way | Opening in Standard Designer is irreversible; scope migration separately |
| Customer's industry spans multiple verticals (e.g., bank with insurance subsidiary) | Evaluate each line of business separately; consider multi-cloud licensing | Objects from multiple vertical clouds can coexist in one org with the appropriate licenses |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner guiding vertical cloud selection:

1. **Identify the required standard objects.** Before evaluating any vertical cloud by name, list every business entity the solution must model. Map each to the nearest industry standard object using the vertical cloud object landscape. This is the primary selection signal — not the customer's industry name.
2. **Determine license dependencies.** Check whether any required vertical cloud has a base license dependency (e.g., Insurance Cloud requires FSC). Confirm all required licenses are in scope for the purchase.
3. **Assess the OmniStudio deployment model.** Confirm whether the org will be new (platform-native OmniStudio, Spring '26+) or existing (potentially managed package). If existing, identify which OmniStudio model is in use before planning any component work. Flag the one-way migration risk if managed-package components are involved.
4. **Evaluate customization vs configuration tradeoffs.** For each business process, determine whether pre-built vertical cloud components (OmniStudio flows, page layouts, guided setup) cover the requirement or whether custom development is needed. Document the delta explicitly.
5. **Document the data model compatibility assessment.** Produce a table mapping each required business entity to the standard object it will use, the vertical cloud license required, and any gaps requiring custom extension.
6. **Identify open questions that could change the recommendation.** List any unclear requirements — edition tier (Growth vs Enterprise), Hyperforce vs legacy, existing custom object conflicts — that must be resolved before finalizing the recommendation.
7. **Produce the formal recommendation.** Write a documented vertical cloud recommendation citing each driving factor: required standard objects, license dependencies, OmniStudio model, and known customization requirements. Include a risk log for any assumptions made.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Required standard objects are identified and mapped to the vertical cloud that provides them
- [ ] License dependencies are confirmed (e.g., Insurance Cloud requires FSC base)
- [ ] OmniStudio deployment model (platform-native vs managed package) is documented
- [ ] One-way Standard Designer migration risk is flagged if managed-package components are involved
- [ ] Customization vs configuration tradeoffs are assessed for key business processes
- [ ] Existing org custom object conflicts are identified for retrofit scenarios
- [ ] Open questions that could change the recommendation are logged
- [ ] Edition tier (Growth vs Enterprise) is confirmed or flagged as outstanding

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Industry standard objects are license-gated — no license, no object.** Standard objects like `InsurancePolicy`, `ServicePoint`, and `BillingAccount` do not appear in a Salesforce org unless the corresponding vertical cloud license is active. They cannot be created as custom objects and used as substitutes without losing all platform behaviors (relationships, validation, API behaviors) those objects carry. Attempting to use SOQL against `InsurancePolicy` in an unlicensed org returns an error, not an empty result.
2. **Insurance Cloud requires FSC as a base — they are not alternatives.** A common mistake is treating Financial Services Cloud and Insurance Cloud as competing options for a financial services firm. Insurance Cloud modules are built on top of FSC. An org licensed for Insurance Cloud must also hold an FSC license. Proposing Insurance Cloud without FSC in the license scope results in an invalid configuration that cannot be provisioned.
3. **OmniStudio Standard Designer migration is permanent and irreversible.** Once a managed-package OmniStudio component (OmniScript, FlexCard, DataRaptor) is opened in the Standard Designer as part of a platform-native migration, it can no longer be edited in the managed-package designer. This applies even if the migration is aborted midway. Any existing managed-package OmniStudio customizations must be fully scoped before beginning migration, and rollback is not available.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Vertical Cloud Recommendation | Written recommendation stating which Industries cloud(s) are required, with each driving factor documented |
| Data Model Compatibility Assessment | Table mapping required business entities to industry standard objects and the license that provides them |
| License Dependency Map | List of all licenses required, including base license dependencies (e.g., Insurance + FSC) |
| OmniStudio Deployment Model Decision | Documented choice of platform-native vs managed package with migration risk assessment if applicable |
| Customization vs Configuration Analysis | Per-process assessment of what is available pre-built vs what requires custom development |
| Open Questions Log | List of unresolved requirements that could change the recommendation |

---

## Related Skills

- `architect/industries-data-model` — Use after selecting a vertical cloud to understand the detailed data model, object relationships, and extension patterns for the chosen cloud
- `admin/industries-process-design` — Use after selection to design OmniStudio-based process flows for the chosen vertical cloud
- `data/industries-data-migration` — Use when migrating existing data from custom objects or legacy systems to industry standard objects
- `data/omnistudio-metadata-management` — Use when managing OmniStudio component lifecycle, versioning, and deployment across environments
- `architect/platform-selection-guidance` — Use upstream when the question is broader than vertical cloud selection (e.g., whether to use Salesforce Industries at all vs standard platform)
