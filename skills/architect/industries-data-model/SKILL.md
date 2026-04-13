---
name: industries-data-model
description: "Reference guide for Salesforce Industries cloud data models: Insurance Cloud (InsurancePolicy hierarchy), Communications Cloud (Account record types, BillingAccount), Energy & Utilities (ServicePoint, ServiceContract), and Health Cloud (CarePlan, FHIR-aligned patient objects). NOT for standard Sales/Service Cloud data model or FSC retail banking model."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "what objects does Salesforce Insurance Cloud add to the data model"
  - "Communications Cloud Account record types and billing account data model"
  - "Health Cloud FHIR object model — CarePlan, CareObservation relationships"
  - "Energy and Utilities Cloud ServicePoint and ServiceContract data model"
  - "InsurancePolicyParticipant links to Account or Contact — which is correct"
tags:
  - industries
  - data-model
  - insurance-cloud
  - communications-cloud
  - health-cloud
  - energy-utilities
  - architecture
inputs:
  - "Industries cloud edition (Insurance, Communications, Energy, Health)"
  - "Business entities and relationships to model"
  - "Integration requirements with external systems"
outputs:
  - "Industries data model reference diagram"
  - "Object relationship map"
  - "SOQL query patterns for industry-specific objects"
  - "Integration data mapping"
dependencies:
  - insurance-cloud-architecture
  - fsc-architecture-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Industries Data Model

This skill activates when a practitioner needs to understand, query, or extend the Salesforce Industries data model for Insurance Cloud, Communications Cloud, Energy & Utilities Cloud, or Health Cloud. It maps the industry-specific standard objects onto the core Salesforce data model and highlights the relationship patterns that deviate from standard Sales/Service Cloud assumptions.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm which Industries cloud license is provisioned in the org — each cloud adds its own distinct set of standard objects and those objects are not available without the corresponding license.
- The most common wrong assumption is that InsurancePolicyParticipant links to Contact. It links to Account. This breaks integrations and SOQL written by practitioners who assume the Contact-centric model of standard Sales Cloud.
- Industries data models are additive — all standard Account, Contact, Asset, and Case objects remain in place. Industries objects extend them, they do not replace them. Governor limits on standard objects (field count, relationship depth) still apply.

---

## Core Concepts

### Industries Data Models Are Additive

Salesforce Industries clouds do not replace the standard Salesforce data model. They add industry-specific standard objects layered on top of Account, Contact, Asset, and related standard objects. Any existing Sales Cloud or Service Cloud data model knowledge applies. The key shift is understanding which new objects exist, what relationships they carry, and which existing object (usually Account, not Contact) they reference for participant roles.

### Insurance Cloud Object Hierarchy

Insurance Cloud adds a dedicated policy hierarchy. The top-level object is `InsurancePolicy`. Beneath it:

- `InsurancePolicyCoverage` — child of InsurancePolicy; represents individual coverage lines (e.g., liability, collision). Cannot exist without a parent InsurancePolicy.
- `InsurancePolicyParticipant` — junction object linking an InsurancePolicy to an **Account** (not Contact) with a role such as Policyholder, Beneficiary, or Named Insured.
- `InsurancePolicyAsset` — links the insured item (Asset record) to the policy.
- `InsurancePolicyTransaction` — child of InsurancePolicy; records premium payments, endorsements, and cancellations.

The decision to link InsurancePolicyParticipant to Account rather than Contact is intentional. Insurance policies are held by legal entities (businesses and individuals both represented as Accounts in the Insurance Cloud model). Querying policyholder data requires joining through Account, not Contact.

### Communications Cloud Account Record Types

Communications Cloud does not add a separate BillingAccount object analogous to InsurancePolicy. Instead, it uses **record types on the standard Account object** to represent four distinct account subtypes:

- `Business_Account` — commercial customer
- `Consumer_Account` — residential individual customer
- `Billing_Account` — financial account tracking invoices and payments
- `Service_Account` — location or service endpoint account

All four are standard Account records differentiated by RecordType.DeveloperName. Any SOQL query that retrieves a specific account subtype **must filter by RecordType.DeveloperName**; without this filter, queries return all Account record types and produce incorrect results.

Communications Cloud also adds `BillingAccount` (the object, distinct from the Billing_Account record type) and `ServiceAccount` objects in some configurations — verify with the specific release documentation for the org's licensed edition.

### Energy & Utilities and Health Cloud Objects

**Energy & Utilities Cloud** adds:
- `ServicePoint` — the physical metering location where energy is delivered or measured.
- `ServiceContract` — the agreement between a utility provider and a customer for service at one or more ServicePoints.
- `CustomerOrder` — orchestrates service activation and change orders.

**Health Cloud** adds a FHIR R4-aligned patient object model:
- `CarePlan` — the coordinating plan for a patient's treatment.
- `CareObservation` — discrete clinical measurements (labs, vitals).
- `ClinicalEncounter` — records of visits, admissions, or telehealth sessions.
- `HealthCondition` — diagnoses and problem list entries.
- `MedicationStatement` — reported or confirmed medication use.

Health Cloud object names are Salesforce-specific identifiers and are not identical to FHIR resource names, even though the underlying model is FHIR R4-aligned. `CareObservation` maps conceptually to the FHIR `Observation` resource, but the API name and field structure differ.

---

## Common Patterns

### Querying an InsurancePolicy with Coverage Lines and Participants

**When to use:** Any time a page, integration, or report needs to display a complete view of a policy including what is covered and who holds the policy.

**How it works:**

Use a SOQL query with subqueries on `InsurancePolicyCoverages` and `InsurancePolicyParticipants`. The participant lookup is to `AccountId`, not `ContactId`.

```soql
SELECT
    Id,
    InsurancePolicyNumber,
    PolicyType,
    EffectiveDate,
    ExpirationDate,
    (
        SELECT Id, CoverageType, CoverageAmount, Deductible
        FROM InsurancePolicyCoverages
    ),
    (
        SELECT Id, RoleInPolicy, AccountId, Account.Name
        FROM InsurancePolicyParticipants
    )
FROM InsurancePolicy
WHERE Id = :policyId
```

**Why not the alternative:** Querying InsurancePolicyParticipant with a ContactId filter returns zero results because the relationship is to Account. This is the most common integration bug in Insurance Cloud implementations.

### Querying Communications Cloud Accounts by Subtype

**When to use:** Any page or integration that needs to distinguish billing accounts from service accounts or consumer accounts in a Communications Cloud org.

**How it works:**

Filter by `RecordType.DeveloperName` in the WHERE clause. Omitting the filter returns all Account record types, which produces incorrect counts and data in reports.

```soql
SELECT Id, Name, RecordType.DeveloperName, BillingStreet
FROM Account
WHERE RecordType.DeveloperName IN (
    'Business_Account',
    'Consumer_Account',
    'Billing_Account',
    'Service_Account'
)
```

To retrieve only billing accounts:

```soql
SELECT Id, Name, RecordType.DeveloperName
FROM Account
WHERE RecordType.DeveloperName = 'Billing_Account'
```

**Why not the alternative:** A query on Account without a RecordType filter in a Communications Cloud org will return all subtypes intermingled. Reports and Lightning pages built on this will show inflated account counts and mix billing logic with service logic.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to find who holds an Insurance policy | Query InsurancePolicyParticipant.AccountId with RoleInPolicy = 'Policyholder' | Participants are linked to Account, not Contact |
| Need to list coverage lines for a policy | Subquery InsurancePolicyCoverages from InsurancePolicy | CoverageType and CoverageAmount live on InsurancePolicyCoverage, not InsurancePolicy |
| Need to find all billing accounts in Comms Cloud | Filter Account by RecordType.DeveloperName = 'Billing_Account' | Account subtypes are record types; no filter returns mixed results |
| Need to map a patient's active care plans in Health Cloud | Query CarePlan with a filter on PatientId and Status | CarePlan is the coordinating object; ClinicalEncounter and CareObservation are children |
| Need to find metering location for a utility customer | Query ServicePoint with a filter on AccountId or Address | ServicePoint is the physical delivery location, separate from the Account |
| Deciding whether to build custom insurance objects | Use InsurancePolicy hierarchy objects first | Standard objects carry relationships, OmniStudio integration, and upgrade-safe behavior |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Identify the Industries cloud edition licensed in the org (Insurance, Communications, Energy & Utilities, or Health Cloud) — confirm by checking Setup > Installed Packages or querying `EntityDefinition` for the target object API name.
2. Map the business entities to the appropriate standard Industries objects before considering custom objects — start with InsurancePolicy, CarePlan, ServicePoint, or Account record types as the anchor depending on the cloud.
3. Verify participant and relationship direction: for Insurance Cloud, confirm that participant lookups go to Account; for Health Cloud, confirm that CarePlan links to the correct patient record via the standard patient lookup field.
4. Write SOQL queries using the correct relationship names from the Industries object model — use subqueries for child objects (InsurancePolicyCoverages, InsurancePolicyParticipants) and RecordType filters for Communications Cloud Account subtypes.
5. Validate that any integration data mapping uses AccountId (not ContactId) for Insurance policy participants, and uses RecordType.DeveloperName for Communications Account classification.
6. Check that custom objects or fields being added do not duplicate functionality already present in the standard Industries object hierarchy — redundant customization creates upgrade risk and data model debt.
7. Review the checker script output (`scripts/check_industries_data_model.py`) against the org metadata to surface anti-patterns before deployment.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] InsurancePolicyParticipant relationships reference AccountId, not ContactId
- [ ] Communications Cloud Account queries include a RecordType.DeveloperName filter
- [ ] No custom objects duplicate InsurancePolicy, InsurancePolicyCoverage, CarePlan, or ServicePoint
- [ ] Health Cloud object API names are used as Salesforce-defined (not raw FHIR resource names)
- [ ] InsurancePolicyCoverage records are always created with a parent InsurancePolicy — orphan coverage records are not valid
- [ ] Integrations mapping external policy or patient data correctly target Account (not Contact) for holder/participant roles

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **InsurancePolicyParticipant links to Account, not Contact** — Practitioners familiar with standard Sales Cloud assume participant and holder roles reference Contacts. In Insurance Cloud, `InsurancePolicyParticipant` has a lookup to `Account`. Any integration or SOQL written with a ContactId filter returns zero results. Every policyholder, beneficiary, and named insured is modeled as an Account record.

2. **Communications Account subtypes are record types, not separate objects** — All four account subtypes (Business, Consumer, Billing, Service) are standard `Account` records with different RecordTypes. SOQL without a `RecordType.DeveloperName` filter in a Communications Cloud org returns all subtypes mixed together. This produces inflated counts, broken page logic, and incorrect billing report totals.

3. **InsurancePolicyCoverage cannot exist without a parent InsurancePolicy** — `InsurancePolicyCoverage` is a master-detail child of `InsurancePolicy`. Attempting to insert a coverage record without a valid parent policy ID raises a required field error. Data migration scripts that load coverage lines before policies will fail.

4. **Health Cloud object names differ from FHIR resource names** — Health Cloud is FHIR R4-aligned in its data model design, but the Salesforce object API names are not the same as FHIR resource names. `CareObservation` is not `Observation`. `HealthCondition` is not `Condition`. SOQL and Apex written using raw FHIR resource names as object API names will fail at compile or query time.

5. **Industries objects require specific license provisioning** — InsurancePolicy, CarePlan, ServicePoint, and other Industries-specific objects are not available in orgs without the corresponding Industries cloud license. Deploying metadata that references these objects to an unlicensed org will fail with object not found errors. Always confirm license provisioning before designing integrations or deployments that depend on Industries objects.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Industries data model reference diagram | Object relationship map showing InsurancePolicy hierarchy, Communications Account record types, Health Cloud patient model, and Energy & Utilities service objects |
| SOQL query patterns | Ready-to-use queries for common Insurance, Communications, and Health Cloud data retrieval scenarios |
| Integration data mapping | Field-level mapping from external system entities to Salesforce Industries standard objects, including correct participant relationship direction |

---

## Related Skills

- insurance-cloud-architecture — detailed architecture patterns for Insurance Cloud implementations beyond the data model layer
- fsc-architecture-patterns — Financial Services Cloud patterns for retail banking and wealth management (distinct from Insurance Cloud)
