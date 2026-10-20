---
name: compliance-documentation-requirements
description: "Use when setting up or auditing how compliance documentation is structured, collected, and preserved for regulatory audit in Salesforce FSC — covering KYC data collection workflows, AML screening integration setup, audit trail configuration, and regulatory reporting readiness. Triggers: KYC form setup, AML integration configuration, compliance data collection, audit trail setup, regulatory documentation workflow, Field Audit Trail configuration, Setup Audit Trail, Event Monitoring, Discovery Framework, FSC KYC objects, Identity Document setup, Party Identity Verification. NOT for security implementation, NOT for designing AML/KYC architecture (use architect/aml-kyc-process-architecture), NOT for configuring who can access deal or client data (use admin/compliant-data-sharing-setup)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "setting up KYC data collection workflow for new client onboarding in FSC"
  - "configuring audit trail for compliance reporting — what combination of Setup Audit Trail, Field Audit Trail, and Event Monitoring do I need?"
  - "how do I configure the Discovery Framework to collect identity verification data with versioned audit-ready responses?"
  - "connecting FSC to a third-party AML screening vendor like Onfido for watchlist checks"
  - "what FSC objects store KYC identity data and how do I configure them for regulatory audit?"
tags:
  - compliance
  - kyc
  - aml
  - fsc
  - audit-trail
  - field-audit-trail
  - discovery-framework
  - identity-verification
  - financial-services
  - regulatory-documentation
inputs:
  - FSC org details — edition, FSC license type, whether OmniStudio is licensed
  - Regulatory obligations in scope (e.g., BSA/FinCEN, FATF, EU AMLD, MiFID II)
  - Third-party AML screening vendor if already selected (e.g., Onfido, Refinitiv, LexisNexis)
  - Whether Salesforce Shield is in scope or licensed (required for Field Audit Trail)
  - Current KYC data collection process — manual forms, existing system of record
  - Retention period required for compliance documentation
outputs:
  - Configured FSC KYC objects (PartyIdentityVerification, IdentityDocument, PartyProfileRisk, PartyScreeningSummary)
  - Discovery Framework OmniScript with versioned, audit-ready response capture
  - Audit trail configuration plan covering Setup Audit Trail, Field Audit Trail (Shield), and Event Monitoring
  - AML screening integration setup guidance with Named Credential and integration pattern
  - Regulatory documentation checklist for readiness review
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Compliance Documentation Requirements

Use this skill when configuring how compliance documentation is structured, collected, and preserved in Salesforce FSC for regulatory purposes. This skill covers the admin-layer setup of KYC data collection workflows using FSC's native data model and Discovery Framework, the integration setup for AML screening via third-party vendors, and the layered audit trail configuration required for regulatory audit readiness. It produces configured org metadata and documented compliance data flows — not architecture design artifacts.

This skill is distinct from `admin/compliant-data-sharing-setup`, which governs WHO can see deal and client data (Compliant Data Sharing). This skill governs HOW compliance documentation is structured, collected, and preserved for regulatory audit obligations.

---

## Before Starting

- **Verify FSC license type.** The KYC data model objects — `PartyIdentityVerification`, `IdentityDocument`, `PartyProfileRisk`, and `PartyScreeningSummary` — appear in the Metadata API guide as onboarding target objects and standard picklists (api_meta 264 L96630-96645, L146588, L146637, L146690). UNVERIFIED (2026-10-20): that they require an FSC license and are absent from standard CRM — the corpus names no license.
- **Confirm OmniStudio licensing for Discovery Framework.** The Discovery Framework — the recommended FSC mechanism for structured, versioned data collection — is backed by OmniStudio (OmniScript + DataRaptor). It requires OmniStudio or Industries Cloud licenses. Without OmniStudio, custom Screen Flows must substitute but lose native versioning. UNVERIFIED (2026-10-20): the Discovery Framework's OmniStudio basis, licensing and response versioning. The corpus does hold three Discovery Framework facts: IndustriesSettings `enableIndustriesAssessment` turns on its Industries Assessment feature (api_meta 264 L122648-122650); a "Discovery Framework Data Capture" flow type (Beta) presents its assessment questions (object_reference 264 L143426-143429), and assessment questions deploy before those flows (api_meta 264 L26110-26111); a `<versionNumber>` on an assessment question creates a version on deploy (L26106-26107).
- **Determine whether Shield is in scope.** Field Audit Trail — required to retain historical values of sensitive KYC fields beyond the standard 18 months (24 via the API) of field history (secguide 262 L4632-4633) — is part of Salesforce Shield with Shield Platform Encryption and Event Monitoring (secguide 262 L297-298). If the regulatory retention obligation exceeds 18 months for field-level data (common under BSA/FinCEN: 5 years), Shield must be licensed. Setup Audit Trail and Event Monitoring have different scopes and different add-on requirements.
- **Do not assume FSC has a native AML engine.** FSC provides objects to store screening results but has no internal watchlist, PEP database, or sanctions list matching capability. Every AML screening decision comes from a third-party vendor integration. UNVERIFIED (2026-10-20): FSC's lack of a screening engine and the "Set Up Integrations" pattern name — no corpus line.
- **Identify which audit trail components address which regulatory obligation.** Setup Audit Trail covers configuration changes; Field Audit Trail covers field value history at scale; Event Monitoring covers user activity and login behavior. All three serve distinct compliance documentation purposes and are often required in combination.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| What field-level retention does each obligation require, in months? | Without Field Audit Trail history is kept 18 months (24 via the API); with it, until deleted (Gotcha 1) | Whether Shield is a go-live dependency |
| Is Salesforce Shield licensed, and is a `HistoryRetentionPolicy` planned per object? | Field Audit Trail policies are deployed through Metadata API, not toggled (Gotcha 1) | A policy per KYC object before the first record changes |
| How far back must configuration-change evidence go? | Setup Audit Trail keeps 180 days, then deletes (Gotcha 3) | The export interval and the archive location |
| Which screening vendor writes `PartyScreeningSummary`, and what happens when it is down? | The object stores results it receives (Gotcha 2; UNVERIFIED (2026-10-20): no screening engine) | An error path that surfaces a Case instead of an empty record |
| Will screening run from batch, scheduled or event-driven Apex? | Per-user credentials in headless runs are a suspected risk (Gotcha 4; UNVERIFIED (2026-10-20)) | Named Principal on the External Credential, granted through a permission set |
| Is Data Protection and Privacy enabled, and does every client Contact carry an `IndividualId`? | `Contact.IndividualId` exists only with it (object_reference 264 L71890-71891), and the KYC design assumes an Individual (Gotcha 5; UNVERIFIED (2026-10-20): the Individual lookup) | A pre-load count of Contacts with a null `IndividualId` |
| Which fields need history, and are any of them formula or long text? | Formula, roll-up, auto-number and long text fields cannot be tracked (secguide 262 L4885-4890) | A trackable field list per object |

A proper configuration fixes retention, archive cadence and credential type before data arrives; "just doing it" turns on the objects and finds the history gap at the first audit.

---

## Core Concepts

### FSC KYC Data Model — Four Core Objects

FSC provides four standard objects that form the KYC documentation layer for financial institutions. The corpus confirms the objects and these standard picklists: `PartyIdentityVerification.Status`, `.Result`, `.VerifiedBy`; `PartyProfileRisk.RiskCategory`; `PartyScreeningSummary.Status`, `.ScreeningDecision` (api_meta 264 L146588-146761). UNVERIFIED (2026-10-20): every other field name and every picklist value in the bullets below — the per-object field tables are not in the corpus.

- **`PartyIdentityVerification`** — records the outcome of a specific identity verification event for an individual or account. Fields include verification type, `Status` (UNVERIFIED (2026-10-20): values Verified / Unverified / Expired), verification date, and the method used (e.g., government ID check, biometric). One individual can have multiple verification records as they pass through periodic review cycles.
- **`IdentityDocument`** — stores document-level detail for identity evidence collected during KYC. Fields include document type (Passport, National ID, Driver's License), issuing authority, issue date, expiry date, and document number. Linked to a `PartyIdentityVerification` record. Never store raw document images in a standard text field — use Salesforce Files with Content Version if document scans must be stored.
- **`PartyProfileRisk`** — stores the regulatory risk assessment record for an individual or account. Core fields: `RiskCategory` (Low / Medium / High / Prohibited), `RiskScore`, `RiskReason`, `RiskReviewDate`. This is the canonical store for the customer's AML risk tier.
- **`PartyScreeningSummary`** — stores the result of an AML screening event. Fields capture the screening vendor reference, match status (Clear / Potential Match / Confirmed Match), and screening type (sanctions, PEP, adverse media). Created by the AML integration process and linked to the Individual and the associated `PartyProfileRisk` update workflow.

`Individual` is the data privacy record — a customer's data privacy and protection preferences (object_reference 264 L158005-158006) — and `Contact.IndividualId` exists only when Data Protection and Privacy is enabled (L71890-71891). UNVERIFIED (2026-10-20): that the four KYC objects associate to `Individual` rather than `Contact`. Ensure every onboarded individual has a linked `Individual` record before creating these child records.

### Discovery Framework for Structured, Versioned Data Collection

The Discovery Framework is the FSC-native mechanism for collecting compliance questionnaire data — KYC questionnaires, suitability assessments, periodic review forms — in a structured, versioned, audit-ready format. UNVERIFIED (2026-10-20): that it is built on OmniStudio (OmniScript + DataRaptor + Integration Procedures) and stores responses as versioned `AssessmentQuestionResponse` records, and the three properties below. The corpus holds `AssessmentQuestion` ("the container object that stores the questions required for an assessment") and `AssessmentQuestionSet` (pkg2_dev 264 L3660, L3713), question versions and the Discovery Framework Data Capture flow type (see Before Starting).

Key compliance-relevant properties:
- **Versioned responses:** Each submission creates a new version, preserving the history of what was collected and when. Prior versions remain immutable and available for audit.
- **Structured schema:** Questions are defined in a managed schema (`AssessmentQuestion`, `AssessmentQuestionSet`), not as free text. This enables regulatory-quality data exports.
- **Audit timestamps:** Response records capture the submitting user, submission date, and channel (agent-assisted vs. self-service). These are required for audit trail completeness.

Without OmniStudio, build the collection on the Discovery Framework Data Capture flow type (Beta, object_reference 264 L143426-143429) or on Screen Flows with a custom versioning pattern (e.g., creating new custom records on each update rather than overwriting). This is significantly more effort and produces weaker audit properties.

### Layered Audit Trail — Three Components for Three Scopes

FSC compliance documentation requires three distinct audit trail tools, each covering a different scope:

1. **Setup Audit Trail** — built into every Salesforce org (no add-on). Records configuration changes made in Setup: users, roles, permission sets and profiles; profile permission changes; permission set assignments (secguide 262 L4984, L4997, L5033). UNVERIFIED (2026-10-20): "metadata deployments" as a tracked item. The full history downloads for the past 180 days; after 180 days entries are deleted (secguide 262 L4974-4975; `SetupAuditTrail`, object_reference 264 L264576). Required for demonstrating that system configuration has not been altered without authorization. Export periodically and archive externally to satisfy retention obligations beyond 180 days.

2. **Field Audit Trail (Shield add-on)** — without it, field history is kept up to 18 months (24 via the API); with it, archived field history is kept until you delete it — no fixed ceiling (secguide 262 L4632-4633, L4836-4837). By default it archives after 18 months in production (L4880-4881); `HistoryRetentionPolicy.archiveAfterMonths` is 1-18, and `archiveRetentionYears` is only a reminder for manual deletion (api_meta 264 L46329-46337). Required when regulatory obligation mandates long-term retention of field-level change history (e.g., who changed a customer's risk category, from what value, on what date, and who approved it). Configure it by defining a `HistoryRetentionPolicy` per object and deploying it with Metadata API (secguide 262 L4833-4835). Field Audit Trail tracks up to 200 fields per object; without it, 20 (L4836-4838).

3. **Event Monitoring (Shield add-on)** — captures user activity as event log files for analysing usage and user behaviour (object_reference 264 L113208-113209; UNVERIFIED (2026-10-20): the per-event list — login, API, report export, record view, field access). Delivered as hourly or daily log files queryable via the EventLogFile object (object_reference 264 L113211, L113282-113283; View Event Log Files and API Enabled required, L113237). Required for demonstrating that sensitive KYC data was accessed only by authorized users during the audit period. UNVERIFIED (2026-10-20): the Event Monitoring Analytics App as a lighter, separately available form.

---

## Common Patterns

### Pattern A: KYC Data Collection via Discovery Framework OmniScript

**When to use:** New client onboarding in FSC where an agent or self-service portal collects identity data (name, date of birth, nationality, government ID details) and the data must be versioned and audit-ready.

UNVERIFIED (2026-10-20): Pattern A's `AssessmentQuestionResponse`, DataRaptor Turbo Action, response versioning and Setup page names have no corpus line. KYC and the Discovery Framework assessment feature are two IndustriesSettings flags, `enableIndustriesKYC` and `enableIndustriesAssessment` (api_meta 264 L122648-122654).

**How it works:**

1. Turn on KYC and the Discovery Framework assessment feature — `enableIndustriesKYC` and `enableIndustriesAssessment` in `Industries.settings` (api_meta 264 L122648-122654); they are separate flags.
2. Define `AssessmentQuestionSet` records for the KYC questionnaire (identity data, document details, beneficial ownership if applicable).
3. Build an OmniScript that drives the agent through the questionnaire. Each step maps to an `AssessmentQuestion`.
4. Use a DataRaptor Turbo Action to save responses as `AssessmentQuestionResponse` records linked to the individual and the onboarding event.
5. On completion, trigger creation of `PartyIdentityVerification` and `IdentityDocument` records using a DataRaptor or Integration Procedure based on the questionnaire responses.
6. The response records carry submitting user, timestamp, and version — meeting audit trail requirements for the collection event.

**Why not a custom Flow with free-text fields:** Unstructured data in custom text fields cannot be versioned natively, produces no audit timestamp on the collection event itself, and is difficult to export in a regulatory-quality structured format for audit.

### Pattern B: AML Screening Integration Setup via Named Credential

**When to use:** Configuring the Salesforce side of an AML screening integration with a third-party vendor (e.g., Onfido, Refinitiv World-Check, LexisNexis) after the architectural pattern has been selected.

**How it works:**

1. In Setup, create an External Credential (or Named Credential for Legacy auth) for the screening vendor endpoint. Select Named Principal — one set of credentials for all users (api_meta 264 L66348-66349) — not Per-User (UNVERIFIED (2026-10-20): that per-user credentials fail to resolve in batch and scheduled contexts).
2. Create a Named Credential referencing the External Credential. Set the endpoint URL to the vendor's API root.
3. Grant access through a Permission Set assigned to the integration user — an External Credential principal points to a permission set (api_meta 264 L66367-66369).
4. Configure the Integration Procedure or Apex callout to use the Named Credential label — never hardcode the endpoint URL or API key in OmniStudio procedure JSON or Apex code.
5. Create a custom field or configure the standard `PartyScreeningSummary` fields to capture the vendor's case reference number, match result, and screening timestamp.
6. Test the integration using a single record in a sandbox before enabling for bulk onboarding.

**Why not store the API key in Custom Metadata or Custom Settings:** custom settings outside a managed package are public and readable by all profiles, including the guest user; the guide says to use named credentials or encrypted custom fields for secrets (apexdev 264 L13709-13713). Credentials stored in a Named Credential or External Credential are encrypted with org-specific keys (api_meta 264 L66152-66153, L92625-92626). UNVERIFIED (2026-10-20): that they cannot be read back through the UI or API.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Collecting KYC questionnaire data with audit-ready versioning | Discovery Framework OmniScript + AssessmentQuestionResponse | UNVERIFIED (2026-10-20): native versioning and audit timestamps |
| FSC org without OmniStudio license | Screen Flow + custom versioning records | OmniStudio unavailable; custom versioning is manual but auditable |
| Storing identity document metadata | IdentityDocument object linked to PartyIdentityVerification | Standard FSC object; avoids custom schema duplication |
| AML screening vendor integration (Named Principal auth) | External Credential (Named Principal) + Named Credential | One credential set for all users (api_meta 264 L66348-66349); stored credentials encrypted (L66152-66153); UNVERIFIED (2026-10-20): batch behaviour |
| Field-level change history beyond 18 months | Field Audit Trail (Shield add-on) | Standard history is kept 18 months (24 via API); Field Audit Trail keeps it until deleted (secguide 262 L4632-4633) |
| Demonstrating no unauthorized configuration changes | Setup Audit Trail + external archival | Built-in, no add-on; export and archive beyond 180 days |
| Demonstrating authorized data access for audit | Event Monitoring (Shield add-on) | Event log files of user behaviour (UNVERIFIED (2026-10-20): field-access and report-export event types) |
| Storing AML screening results | PartyScreeningSummary + PartyProfileRisk update | Standard FSC objects purpose-built for this purpose |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner setting up compliance documentation in FSC:

1. **Confirm prerequisites** — verify FSC is enabled, confirm whether OmniStudio is licensed (required for Discovery Framework), determine whether Salesforce Shield is in scope (required for Field Audit Trail and Event Monitoring), and identify the AML screening vendor if applicable. Record the regulatory retention obligation in months/years for each data type.

2. **Enable FSC KYC feature and verify data model** — set IndustriesSettings `enableIndustriesKYC` to true (api_meta 264 L122652-122654; UNVERIFIED (2026-10-20): the Setup page name). Verify that `PartyIdentityVerification`, `IdentityDocument`, `PartyProfileRisk`, and `PartyScreeningSummary` objects are present and accessible. Confirm that every onboarded individual will have a linked `Individual` record (`Contact.IndividualId`, available when Data Protection and Privacy is enabled, object_reference 264 L71890-71891).

3. **Configure the Discovery Framework for data collection** — define `AssessmentQuestionSet` and `AssessmentQuestion` records for the KYC questionnaire. Build an OmniScript to drive the collection flow. Ensure responses are saved as `AssessmentQuestionResponse` records with user and timestamp fields populated (UNVERIFIED (2026-10-20): object and fields have no corpus line). If OmniStudio is unavailable, build a Screen Flow with a custom versioned response object.

4. **Set up AML screening integration** — create an External Credential with Named Principal authentication for the screening vendor. Create a Named Credential referencing it. Configure the Integration Procedure or Apex callout to call the vendor API using the Named Credential label. Map vendor response fields to `PartyScreeningSummary` and trigger a `PartyProfileRisk` update workflow on receipt of results.

5. **Configure audit trail components** — enable field history tracking on `PartyIdentityVerification`, `IdentityDocument`, and `PartyProfileRisk` for key fields. If Shield is licensed, deploy a `HistoryRetentionPolicy` per object through Metadata API (secguide 262 L4833-4835) for fields requiring retention beyond 18 months. Set up Event Monitoring log file retrieval (if Shield licensed) and establish a process to archive Setup Audit Trail exports beyond the 180-day platform retention.

6. **Validate data collection completeness** — run a test onboarding end-to-end. Confirm that after completion, the following records exist: `Individual`, `PartyIdentityVerification` (`Status` = Verified — UNVERIFIED (2026-10-20): value name), at least one `IdentityDocument` with document type and expiry, `PartyProfileRisk` with RiskCategory populated, `PartyScreeningSummary` with screening result from the vendor.

7. **Review against regulatory checklist** — confirm that each regulatory obligation (identity collection, screening, risk rating, documentation retention) is covered by a concrete Salesforce record or log artifact. Document which audit trail layer covers which obligation and identify any gaps requiring external archival.

---

## Review Checklist

Run through these before marking compliance documentation setup complete:

- [ ] FSC KYC feature is enabled; all four KYC objects (PartyIdentityVerification, IdentityDocument, PartyProfileRisk, PartyScreeningSummary) are accessible and mapped to onboarding workflow
- [ ] Discovery Framework OmniScript (or equivalent) stores versioned responses with user and timestamp (UNVERIFIED (2026-10-20): `AssessmentQuestionResponse` and its fields)
- [ ] AML screening integration uses Named Credential with Named Principal auth — no hardcoded API keys in metadata or code
- [ ] PartyScreeningSummary records capture vendor case reference, match result, and screening timestamp
- [ ] Field history tracking is enabled on key KYC fields; a `HistoryRetentionPolicy` is deployed if Shield is licensed
- [ ] Setup Audit Trail export and archival process is documented and scheduled
- [ ] Event Monitoring log retrieval process is in place if Shield is licensed
- [ ] Every onboarded individual has a linked Individual record (not just Contact)
- [ ] Retention period for each data type is documented and coverage is confirmed (Shield vs. standard history vs. external archive)
- [ ] Regulatory documentation checklist reviewed; no gaps between obligations and platform artifacts

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Field Audit Trail requires Shield — it is not part of base FSC** — Admins sometimes enable standard field history tracking (up to 20 fields; 18 months, 24 via the API) and believe it satisfies regulatory retention requirements (secguide 262 L4632-4633, L4838). For obligations requiring multi-year field-level retention, Field Audit Trail — part of Shield (secguide 262 L297-298) — keeps archived history until you delete it (L4836-4837). Confirm Shield licensing before designing the audit trail architecture.

2. **PartyIdentityVerification and IdentityDocument require an Individual record parent** — UNVERIFIED (2026-10-20): that these objects relate to `Individual`, not `Contact`; `Individual` is the data privacy record (object_reference 264 L158005-158006). In orgs where contacts are created without Data Protection and Privacy (which adds `Contact.IndividualId`, L71890-71891), or where bulk data imports bypassed Individual creation, there is no valid parent to attach KYC records. Validate the Contact-to-Individual mapping at the start of any KYC setup project.

3. **Setup Audit Trail retains only 180 days natively** — after 180 days setup entity records are deleted (secguide 262 L4974-4975). Organizations with multi-year compliance audit requirements must establish a process to export Setup Audit Trail records (via SOQL on `SetupAuditTrail`) and archive them externally on a recurring schedule. This is not automated by default.

4. **AML screening has no native FSC engine — third-party integration is mandatory** — UNVERIFIED (2026-10-20): no corpus line on FSC screening. FSC does not contain any watchlist data, sanctions lists, or PEP databases. The `PartyScreeningSummary` object stores results from external screening calls but performs no screening itself. Any compliance workflow that omits the third-party integration and relies solely on the FSC object schema will produce empty screening records and fail regulatory review.

5. **Named Credentials with Per-User authentication fail in batch and scheduled contexts** — UNVERIFIED (2026-10-20): no corpus line on per-user resolution in headless contexts. If the AML screening integration uses a Named Credential configured for Per-User OAuth, callouts may fail in any context that does not have an active user session: batch jobs, scheduled Apex, future methods, and Platform Event triggers. Use Named Principal (org-level) authentication on Named Credentials that back automated compliance workflows.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configured FSC KYC objects | PartyIdentityVerification, IdentityDocument, PartyProfileRisk, PartyScreeningSummary with appropriate fields tracked and layouts configured |
| Discovery Framework questionnaire | OmniScript or Discovery Framework Data Capture flow over an AssessmentQuestionSet (UNVERIFIED (2026-10-20): versioned `AssessmentQuestionResponse` records) |
| Named Credential (AML vendor) | Named Credential with Named Principal auth backing the AML screening integration |
| Audit trail configuration plan | Documented coverage of Setup Audit Trail, Field Audit Trail (if Shield), and Event Monitoring against each regulatory retention obligation |
| Regulatory documentation checklist | Mapping of each compliance obligation to the Salesforce artifact that satisfies it |

---

## Related Skills

- `architect/aml-kyc-process-architecture` — use when designing the architecture for AML/KYC orchestration; this skill covers admin-layer setup after the architecture decision is made
- `admin/compliant-data-sharing-setup` — use to configure who can see deal and client data (Compliant Data Sharing rules); distinct from how compliance documentation is collected and preserved
- `admin/fsc-action-plans` — use to configure task-based onboarding checklists that drive KYC collection steps
- `admin/health-cloud-consent-management` — parallel pattern for consent documentation in Health Cloud; useful reference for versioned consent record design

## Official Sources Used

- Enable Know Your Customer for FSC — https://help.salesforce.com/s/articleView?id=sf.fsc_admin_kyc_enable.htm
- FSC KYC Data Model (Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.financial_services_cloud_object_reference.meta/financial_services_cloud_object_reference/fsc_kyc_data_model.htm
- Set Up AML Screening Integrations — https://help.salesforce.com/s/articleView?id=sf.fsc_admin_aml_screening_setup.htm
- Compliant Data Sharing in FSC — https://help.salesforce.com/s/articleView?id=sf.fsc_admin_compliant_data_sharing.htm
- Field Audit Trail — https://help.salesforce.com/s/articleView?id=sf.field_audit_trail.htm
- Setup Audit Trail — https://help.salesforce.com/s/articleView?id=sf.admin_monitorsetup.htm
- Event Monitoring — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/using_resources_event_log_files.htm
- Named Credentials — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
