---
name: referral-management-health
description: "Use this skill when configuring Health Cloud referral management: setting up ClinicalServiceRequest-based referrals, provider search, referral status workflows, and network management. NOT for Sales Cloud referrals, FSC Einstein Referral Scoring, or Public Sector Solutions referral objects."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Referral Management — Health Cloud

Use this skill when configuring Health Cloud referral management: defining referral types, setting up the ClinicalServiceRequest-based workflow, enabling provider search, and managing provider network relationships. This skill covers the clinical referral lifecycle from initiation through completion. It does NOT cover FSC Einstein Referral Scoring (a Financial Services Cloud feature for advisor-client referrals), the Public Sector Solutions Referral sObject, or generic Sales Cloud lead referral tracking.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has Health Cloud enabled and the HealthCloudGA managed package installed. Referral management requires specific Health Cloud permission set licenses beyond base Salesforce access.
- Identify whether the org uses Health Cloud's native referral workflow (ClinicalServiceRequest) or a custom object-based approach. The native approach is the only one with long-term Salesforce investment.
- Confirm the Data Pipelines Base User permission set license is provisioned for all users who need to run provider search. Without this license, the Data Processing Engine (DPE) job that populates CareProviderSearchableField will fail silently or throw a license error, making provider search return zero results.
- Distinguish inbound referrals (from external providers to your organization) from outbound referrals (from your clinicians to external specialists). They share the ClinicalServiceRequest object but differ in direction field values and workflow steps.

---

## Core Concepts

### ClinicalServiceRequest as the Referral Record

Health Cloud referral management uses the `ClinicalServiceRequest` object (API v51.0+) as the core referral record. This is a standard Salesforce object — not a managed-package custom object — which means it is available via standard SOQL, reports, and list views once Health Cloud is enabled. Key fields include:

- `PatientId` — lookup to the patient Account record
- `ReferralDate` — date referral was initiated
- `ReferralType` — picklist distinguishing inbound vs. outbound vs. internal
- `Status` — tracks the referral lifecycle (Draft → Submitted → Accepted → Completed/Cancelled)
- `ReferredToId` — lookup to the receiving provider (Account or Contact)
- `AuthorizationNumber` — for payer-authorized referrals requiring prior authorization

The `ClinicalServiceRequest` object requires the HealthCloudICM permission set to be assigned to users who create or update referral records.

### Provider Search and CareProviderSearchableField

Provider search is powered by a denormalized index object: `CareProviderSearchableField`. This object is NOT populated automatically. It requires a Data Processing Engine (DPE) job to run, which reads provider records (Accounts/Contacts with healthcare provider record types) and writes denormalized, search-optimized records to `CareProviderSearchableField`.

The most common implementation blocker: the user running the DPE job (or the automated process credential) must have the **Data Pipelines Base User** permission set license assigned. Without this license, the DPE job either fails to run or silently produces no output. Provider search then returns zero results even when provider records exist.

Provider records must use the correct Health Cloud record types (HealthcareProvider on Account, HealthcarePractitioner on Contact or Account) for the DPE job to pick them up.

### Referral Status Workflow

Health Cloud referral management uses a status-driven workflow on `ClinicalServiceRequest`. The standard status picklist values are: Draft, Submitted, In Review, Accepted, Declined, Completed, Cancelled. Admins can add custom picklist values but must also update any validation rules or Flow automation that checks for specific status values.

A common pattern is to use Flow to automate status transitions — for example, automatically updating a referral to "Accepted" when the receiving provider logs a response, or "Completed" when a clinical encounter (ClinicalEncounter) is created that references the referral.

---

## Common Patterns

### Outbound Referral to Specialist

**When to use:** A clinician needs to refer a patient to an external specialist and track the referral through acceptance and completion.

**How it works:**
1. Clinician creates a `ClinicalServiceRequest` record with `ReferralType = Outbound`, sets `PatientId`, `ReferredToId` (specialist), and `ReferralDate`.
2. Flow automation fires on record creation to notify the receiving provider (email or Experience Cloud notification).
3. Receiving provider updates status to Accepted via a portal or manual update.
4. When the specialist visit is completed, a `ClinicalEncounter` record is created referencing the `ClinicalServiceRequest`. An Apex trigger or Flow updates status to Completed.
5. Care coordinator reviews completed referral and closes care coordination tasks.

**Why not the alternative:** Using a custom object or Lead-based workflow loses the native provider network integration, FHIR R4 mapping, and reporting on the standard Health Cloud referral dashboard.

### Provider Network Search Before Referral

**When to use:** Care coordinator needs to find in-network specialists before creating a referral.

**How it works:**
1. Run the DPE job to populate `CareProviderSearchableField` on a schedule (daily or on-demand after provider record changes).
2. Use the Health Cloud Provider Search Lightning component (or build a custom LWC querying `CareProviderSearchableField`) to filter by specialty, location, and in-network status.
3. Selected provider's Account/Contact ID populates `ReferredToId` on the new `ClinicalServiceRequest`.
4. Network status field on provider record drives in-network filtering logic.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New Health Cloud org, setting up referrals | Use ClinicalServiceRequest native object | Platform-standard, FHIR R4-aligned, future Salesforce investment |
| Provider search returns no results | Check Data Pipelines Base User license, re-run DPE job | This is the #1 cause of blank provider search results |
| Need to track referral authorization numbers | Use AuthorizationNumber field on ClinicalServiceRequest | Native field, no custom object needed |
| Referral workflow requires external portal | Build Experience Cloud portal with ClinicalServiceRequest access | Native integration; requires separate Experience Cloud for Health Cloud license |
| Custom referral statuses needed | Add picklist values + update Flow automation | Platform-standard approach; avoid hard-coded status values in code |

---

## Recommended Workflow

Step-by-step instructions for configuring Health Cloud referral management:

1. **Verify prerequisites** — confirm Health Cloud is enabled, HealthCloudGA managed package is installed, and the HealthCloudICM permission set is available. Check that provider records use the correct record types (HealthcareProvider, HealthcarePractitioner). Confirm Data Pipelines Base User license is provisioned.
2. **Configure ClinicalServiceRequest** — review and customize the Status picklist values for your referral workflow. Add custom fields if needed. Set up validation rules for required fields (PatientId, ReferralType, ReferredToId). Configure page layouts and record types for inbound vs. outbound referrals.
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
- [ ] Referral status Flow automation tested in sandbox
- [ ] Provider record types are set to HealthcareProvider / HealthcarePractitioner (not generic Account/Contact)
- [ ] Referral reports and dashboards verified to show correct data

---

## Salesforce-Specific Gotchas

1. **Data Pipelines Base User license blocks provider search silently** — If the process credential for DPE job execution lacks the Data Pipelines Base User permission set license, the job either fails to run or completes with zero records written to CareProviderSearchableField. Provider search components return empty results with no error message visible to end users. Always verify the license assignment before debugging provider search.

2. **ClinicalServiceRequest requires HealthCloudICM permission set** — Even with Health Cloud enabled, users without the HealthCloudICM permission set cannot create or update ClinicalServiceRequest records. This affects integration users, automated process users, and any profile-based user who was not explicitly assigned this permission set.

3. **CareProviderSearchableField does not auto-refresh** — The denormalized provider search index is not updated in real time when provider records change. If a provider's specialty, network status, or location changes, the DPE job must run again before the change is visible in provider search. Design provider record update workflows to trigger a DPE job re-run or build a scheduled refresh cadence.

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
