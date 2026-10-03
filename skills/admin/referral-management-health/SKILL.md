---
name: referral-management-health
description: "Use this skill when configuring Health Cloud referral management: setting up ClinicalServiceRequest-based referrals, provider search, referral status workflows, and network management. NOT for referrals in Financial Services Cloud — use admin/fsc-referral-management. NOT for care team workflow and transition-of-care design — use admin/care-coordination-requirements."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "How do I set up referral management in Health Cloud for tracking inbound and outbound clinical referrals?"
  - "Provider search is not returning results in Health Cloud referral workflow"
  - "How does ClinicalServiceRequest work for managing patient referrals in Salesforce?"
  - "Data Pipelines Base User permission missing blocks provider search index population"
  - "How to configure referral types and status flow in Health Cloud for care coordination"
  - "create a patient referral in Health Cloud from an external system through the API"
  - "add a custom field to Health Cloud provider search results"
tags:
  - health-cloud
  - referral-management
  - clinical-service-request
  - provider-search
  - care-coordination
inputs:
  - Health Cloud org with Referral Management enabled
  - ClinicalServiceRequest object access (API v51.0+)
  - Provider network records (Account/Contact with healthcare-specific record types)
  - Data Pipelines Base User permission set license (required for provider search)
outputs:
  - Configured referral type taxonomy and status workflow
  - Provider search index populated via Data Processing Engine job
  - ClinicalServiceRequest-based referral tracking with inbound/outbound distinction
  - Network management configuration for in-network vs. out-of-network routing
dependencies:
  - admin/health-cloud-patient-setup
  - admin/care-program-management
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Referral Management — Health Cloud

Use this skill when configuring Health Cloud referral management: defining referral types, setting up the ClinicalServiceRequest-based workflow, enabling provider search, and managing provider network relationships. This skill covers the clinical referral lifecycle from initiation through completion. It does NOT cover FSC Einstein Referral Scoring (a Financial Services Cloud feature for advisor-client referrals), the Public Sector Solutions Referral sObject, or generic Sales Cloud lead referral tracking.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has Health Cloud enabled and the HealthCloudGA managed package installed. Referral management requires specific Health Cloud permission set licenses beyond base Salesforce access.
- Identify whether the org uses Health Cloud's native referral workflow (ClinicalServiceRequest) or a custom object-based approach. The native approach is the only one with long-term Salesforce investment.
- Confirm the Data Pipelines Base User permission set license is provisioned for all users who need to run provider search. Without this license, the Data Processing Engine (DPE) job that populates CareProviderSearchableField will fail silently or throw a license error, making provider search return zero results. UNVERIFIED (2026-10-03): the license and DPE job are described in Help, not in the developer guide read for this revision; the guide only says provider search APIs query `CareProviderSearchableField`, which supports query and delete but not create or update.
- Confirm the FHIR-Aligned Clinical Data Model org preference is enabled (FHIR R4 Support Settings). `ClinicalServiceRequest`, `ClinicalServiceRequestDetail`, and `ClinicalEncounterSvcRequest` are on the developer guide's list of objects that need it.
- Distinguish inbound referrals (from external providers to your organization) from outbound referrals (from your clinicians to external specialists). They share the ClinicalServiceRequest object. There is no direction field on the object; direction is expressed through who `RequesterId` and `PerformerId` point to, plus record types or a custom field.
- Check whether the org also uses the older referral fields that Health Cloud adds to Lead, Contact, and Opportunity (for example `ReferralStatus__c`, `ReferredToOrganization__c`, `ReasonForReferral__c`). New designs should not mix the two models without a decision.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| Will referrals live on `ClinicalServiceRequest`, on the older Lead-based referral fields, or both? | Health Cloud documents both: FHIR-aligned `ClinicalServiceRequest` and referral fields on Lead, Contact, and Opportunity. | One model per persona, with a migration rule if both exist. | Reports and automation read one source of truth for referral status. |
| Which status values does the referral lifecycle need, and how do they map to the standard ones? | `ClinicalServiceRequest.Status` ships with Active, Completed, Draft, Entered-in-Error, On-Hold, Revoked, Unknown; acceptance is a separate `IsAccepted` checkbox and reasons go in `StatusReason`. | A mapping from business statuses ("Submitted", "Declined") to Status, IsAccepted, and StatusReason. | Automation keys off documented values, and FHIR exchange keeps working. |
| Who requests and who performs: Account, HealthcareProvider, Asset, or device? | `RequesterId` and `PerformerId` are polymorphic and only accept Account, Asset, HealthcareProvider, or CareRegisteredDevice. | The record type that represents referring and receiving providers. | Provider search results drop straight into the referral without remapping. |
| Do referrals arrive from outside Salesforce? | The Referral Management Connect API (`/connect/health/referral-management/referrals`, API 59.0+) creates Account, ClinicalServiceRequest, and ClinicalServiceRequestDetail records, with at most five performers per request. | Source systems, payload owners, and duplicate-matching rules. | Intake is one API call with duplicate matching instead of a custom integration per sender. |
| Which provider attributes must be searchable? | Provider search queries `CareProviderSearchableField`; extra fields are added with `CareProviderSearchConfig` mappings from HealthcareProvider or HealthcarePractitionerFacility. | A list of source fields and target fields per mapped object. | Care coordinators can filter on the attributes they actually use. |
| Should referrals be worked from queues? | `OwnerId` exists from API 56.0, but queues need the object's sharing changed from Controlled By Parent to Private. | The queue design and the sharing change. | Referral intake can be distributed without giving everyone patient-level access. |

---

## Core Concepts

### ClinicalServiceRequest as the Referral Record

Health Cloud referral management uses the `ClinicalServiceRequest` object (API v51.0+) as the core referral record. This is a standard Salesforce object — not a managed-package custom object — which means it is available via standard SOQL, reports, and list views once the FHIR-Aligned Clinical Data Model org preference is enabled. Key fields from the Agentforce Health Developer Guide object reference:

- `PatientId` — master-detail to the patient Account record
- `RequesterId`: polymorphic reference to the Account, Asset, HealthcareProvider, or CareRegisteredDevice raising the request
- `PerformerId`: polymorphic, same allowed targets; who performs the service
- `Status` — Active, Completed, Draft, Entered-in-Error, On-Hold, Revoked, Unknown
- `IsAccepted`: checkbox, default false; `StatusReason`: multi-select reason for the current status
- `Type`: Directive, Filler-Order, Instance-Order, Option, Order, Original-Order, Plan, Proposal, Reflex-Order
- `Priority`: ASAP, Routine, Stat, Urgent; plus `StartDate`, `EndDate`, `DateSigned`, `PatientInstruction`, `ReferralScore`, `CaseId`, `EncounterId`

Earlier versions of this skill listed `ReferralDate`, `ReferralType`, `ReferredToId`, and `AuthorizationNumber`. None of these fields exists on `ClinicalServiceRequest` in the object reference. Supporting details such as insurance or a reason reference go into `ClinicalServiceRequestDetail` records linked by `ClinicalServiceRequestId`.

The `ClinicalServiceRequest` object requires the HealthCloudICM permission set to be assigned to users who create or update referral records. UNVERIFIED (2026-10-03): the HealthCloudICM permission set name does not appear in the developer guide read for this revision.

### Provider Search and CareProviderSearchableField

Provider search is powered by a denormalized index object: `CareProviderSearchableField`. This object is NOT populated automatically. It requires a Data Processing Engine (DPE) job to run, which reads the Provider Relationship Management data model and writes denormalized, search-optimized records to `CareProviderSearchableField`.

The most common implementation blocker: the user running the DPE job (or the automated process credential) must have the **Data Pipelines Base User** permission set license assigned. Without this license, the DPE job either fails to run or silently produces no output. Provider search then returns zero results even when provider records exist.

The DPE job reads **objects**, not record types. `HealthcareProvider` is a standard Health Cloud object — "Represents business-level details about the healthcare organization or the practitioner" — alongside `HealthcarePractitionerFacility` and the rest of the Provider Relationship Management model; `Account` represents a healthcare facility or location and `Contact` represents physicians and other licensed practitioners. There is **no `HealthcareProvider` record type on Account and no `HealthcarePractitioner` record type on Contact**. If provider data has been loaded onto Accounts and Contacts alone without the corresponding PRM object records, the DPE job has nothing to denormalize and provider search returns zero results — which looks identical to the permission-set-license failure above, so check both.

### Referral Status Workflow

Health Cloud referral management uses a status-driven workflow on `ClinicalServiceRequest`. The standard status picklist values are Active, Completed, Draft, Entered-in-Error, On-Hold, Revoked, and Unknown (aligned with FHIR ServiceRequest). Acceptance is tracked with the `IsAccepted` checkbox, and reasons such as a decline go in `StatusReason`. Admins can add custom picklist values but must also update any validation rules or Flow automation that checks for specific status values.

A common pattern is to use Flow to automate status transitions — for example, setting `IsAccepted` when the receiving provider logs a response, or setting Status to Completed when a clinical encounter is linked to the referral through `ClinicalEncounterSvcRequest`.

---

## Common Patterns

### Outbound Referral to Specialist

**When to use:** A clinician needs to refer a patient to an external specialist and track the referral through acceptance and completion.

**How it works:**
1. Clinician creates a `ClinicalServiceRequest` record (Outbound record type), sets `PatientId`, `RequesterId` (the referring HealthcareProvider), `PerformerId` (the specialist's HealthcareProvider or Account), `Priority`, and `StartDate`.
2. Flow automation fires on record creation to notify the receiving provider (email or Experience Cloud notification).
3. Receiving provider accepts via a portal or manual update, which sets `IsAccepted` and moves Status from Draft to Active.
4. When the specialist visit is completed, a `ClinicalEncounter` is linked to the `ClinicalServiceRequest` through a `ClinicalEncounterSvcRequest` record. An Apex trigger or Flow updates Status to Completed.
5. Care coordinator reviews completed referral and closes care coordination tasks.

**Why not the alternative:** Using a custom object or Lead-based workflow loses the native provider network integration, FHIR R4 mapping, and reporting on the standard Health Cloud referral dashboard.

### Provider Network Search Before Referral

**When to use:** Care coordinator needs to find in-network specialists before creating a referral.

**How it works:**
1. Run the DPE job to populate `CareProviderSearchableField` on a schedule (daily or on-demand after provider record changes).
2. Use the Health Cloud Provider Search Lightning component (or build a custom LWC querying `CareProviderSearchableField`) to filter by specialty, location, and in-network status.
3. Selected provider's HealthcareProvider or Account ID populates `PerformerId` on the new `ClinicalServiceRequest`.
4. Network status field on provider record drives in-network filtering logic.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New Health Cloud org, setting up referrals | Use ClinicalServiceRequest native object | Platform-standard, FHIR R4-aligned, future Salesforce investment |
| Provider search returns no results | Check Data Pipelines Base User license, re-run DPE job | This is the #1 cause of blank provider search results |
| Need to track referral authorization numbers | Add a ClinicalServiceRequestDetail or a custom field; `AuthorizationNumber` does not exist on ClinicalServiceRequest | Avoids building on a field that is not in the object reference |
| Referral workflow requires external portal | Build Experience Cloud portal with ClinicalServiceRequest access | Native integration; requires separate Experience Cloud for Health Cloud license |
| Custom referral statuses needed | Map to standard Status + IsAccepted + StatusReason first; add picklist values only for true gaps | Keeps FHIR alignment and avoids hard-coded custom values in code |
| Referrals arrive from an external system | Referral Management Connect API (`POST /connect/health/referral-management/referrals`) | Creates Account, ClinicalServiceRequest, and details in one call with duplicate matching |

---

## Recommended Workflow

Step-by-step instructions for configuring Health Cloud referral management:

1. **Verify prerequisites** — confirm Health Cloud is enabled, HealthCloudGA managed package is installed, and the HealthCloudICM permission set is available. Check that the Provider Relationship Management objects (`HealthcareProvider`, `HealthcarePractitionerFacility`, and the related Account/Contact records) are populated — these are objects, not record types. Confirm Data Pipelines Base User license is provisioned.
2. **Configure ClinicalServiceRequest** — map business statuses onto Status, IsAccepted, and StatusReason. Add custom fields only where the object reference has no equivalent. Set up validation rules for required fields (RequesterId, PerformerId, Priority). Configure page layouts and record types for inbound vs. outbound referrals. Worked metadata and an API payload are in `references/metadata-examples.md`.
3. **Set up Data Processing Engine job for provider search** — in Setup > Data Processing Engine, configure the DPE job that populates CareProviderSearchableField from provider Account/Contact records. Schedule the job to run on a regular basis. Test by running manually and verifying CareProviderSearchableField records appear.
4. **Build referral status Flow automation** — create a Record-Triggered Flow on ClinicalServiceRequest to automate status transitions, send notifications, and create follow-up tasks. Include an error path for declined referrals.
5. **Assign permission sets** — assign HealthCloudICM to all referral-creating users. Assign Data Pipelines Base User to all users who run or trigger provider search DPE jobs. Verify in a sandbox before deploying to production.
6. **Test end-to-end referral workflow** — create a test referral, use provider search to find a provider, submit the referral, and simulate acceptance. Verify all status transitions, automation, and notifications fire correctly.

---

## Review Checklist

- [ ] HealthCloudICM permission set assigned to all referral users
- [ ] Data Pipelines Base User license assigned for DPE job execution
- [ ] DPE job for CareProviderSearchableField is scheduled and successfully populating records
- [ ] ClinicalServiceRequest page layouts and record types configured for inbound and outbound
- [ ] FHIR-Aligned Clinical Data Model org preference enabled
- [ ] No automation references nonexistent fields (ReferralType, ReferredToId, ReferralDate, AuthorizationNumber)
- [ ] Referral status Flow automation tested in sandbox
- [ ] Provider Relationship Management objects are populated (`HealthcareProvider` records exist and link to the Account/Contact records the search should return) — do not look for HealthcareProvider / HealthcarePractitioner *record types*; no such record types exist
- [ ] Referral reports and dashboards verified to show correct data

---

## Salesforce-Specific Gotchas

1. **Data Pipelines Base User license blocks provider search silently** — If the process credential for DPE job execution lacks the Data Pipelines Base User permission set license, the job either fails to run or completes with zero records written to CareProviderSearchableField. Provider search components return empty results with no error message visible to end users. Always verify the license assignment before debugging provider search.

2. **ClinicalServiceRequest requires HealthCloudICM permission set** — Even with Health Cloud enabled, users without the HealthCloudICM permission set cannot create or update ClinicalServiceRequest records. This affects integration users, automated process users, and any profile-based user who was not explicitly assigned this permission set.

3. **CareProviderSearchableField does not auto-refresh** — The denormalized provider search index is not updated in real time when provider records change. If a provider's specialty, network status, or location changes, the DPE job must run again before the change is visible in provider search. Design provider record update workflows to trigger a DPE job re-run or build a scheduled refresh cadence.

4. **Fields that do not exist**: `ReferralType`, `ReferredToId`, `ReferralDate`, and `AuthorizationNumber` are not on `ClinicalServiceRequest`; `PerformerId` cannot point to a Contact. Eight more traps, each with its source, are in `references/gotchas.md`.
---

## Output Artifacts

| Artifact | Description |
|---|---|
| ClinicalServiceRequest configuration | Record types, fields, and validation rules for inbound/outbound referral tracking |
| DPE job definition | Data Processing Engine job that populates CareProviderSearchableField from provider records |
| Referral status Flow | Record-triggered Flow automating referral lifecycle transitions and notifications |
| Permission set assignment guide | Checklist of HealthCloudICM and Data Pipelines Base User assignments required |

---

## Related Skills

- admin/health-cloud-patient-setup — Patient/person account setup required before referrals can reference a valid PatientId
- admin/care-program-management — Care program enrollment and referral tracking integration patterns
- admin/care-coordination-requirements — Care team coordination workflows that include referral handoffs
