---
name: fsc-document-generation
description: "Use this skill when designing or implementing FSC compliance document generation workflows — FINRA disclosure packets, account statements, consent records, and regulatory delivery confirmations using OmniStudio DocGen with FSC data models. Trigger keywords: OmniStudio DocGen FSC, disclosure document generation, account statement PDF, AuthorizationForm document, FINRA disclosure workflow, compliance document batch, DataRaptor document template, DocGen permission set license. NOT for general OmniStudio DocGen mechanics unrelated to FSC compliance, standard Salesforce document templates, or Document Builder (excluded from PCI scope)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "How do I generate FINRA disclosure documents automatically in Financial Services Cloud?"
  - "My account statement PDF job is hitting a document generation limit in FSC — what do I do?"
  - "How should I use AuthorizationForm and DataUseLegalBasis objects to drive compliant disclosure delivery?"
  - "What permission set licenses do FSC users need to run OmniStudio DocGen document jobs?"
  - "How do I set up a batch disclosure document run in FSC that produces PDFs for thousands of accounts?"
tags:
  - fsc
  - document-generation
  - omnistudio-docgen
  - disclosure-compliance
  - authorization-form
  - finra
  - gdpr
  - pdf-generation
  - dataraptor
inputs:
  - "FSC org with Industries (Financial Services Cloud) licensing confirmed"
  - "OmniStudio DocGen enabled and DocGen permission set licenses assigned"
  - "Target document type: FINRA disclosure, account statement, consent record, or contract"
  - "Regulatory requirement details (FINRA, GDPR, CCPA) driving the document workflow"
  - "AuthorizationForm and DataUseLegalBasis object population plan if using Disclosure and Compliance Hub"
outputs:
  - "OmniStudio DocGen template configuration with DataRaptor data source binding"
  - "Batch document generation job setup with server-side 1000 documents/hour throughput plan"
  - "AuthorizationForm record design for regulatory disclosure capture and delivery confirmation"
  - "Permission set license assignment checklist for DocGen roles"
  - "PDF output delivery architecture (ContentDocument / EmailMessage / portal)"
dependencies:
  - omnistudio/document-generation-omnistudio
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# FSC Document Generation

This skill activates when a practitioner needs to generate compliance-grade documents in Financial Services Cloud — disclosure packets, account statements, consent records, or regulatory delivery confirmations — using OmniStudio DocGen integrated with FSC's Disclosure and Compliance Hub data model.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm FSC Industries licensing is active and OmniStudio DocGen is provisioned; DocGen is bundled with the Industries license but individual user access requires separate DocGen permission set licenses per role (DocGen Designer, DocGen User, DocGen Runtime).
- Identify the regulatory driver: FINRA disclosure, GDPR consent record, CCPA data-use notice, or client-facing account statement. Each has distinct template structure, delivery confirmation, and retention requirements.
- Know the server-side batch throughput cap: OmniStudio DocGen processes a maximum of 1000 documents per hour via the DocGen API. For large account statement runs (tens of thousands of accounts), plan a queued Apex batch job that issues DocGen calls in controlled bursts.
- Determine whether Disclosure and Compliance Hub is the delivery orchestrator; if regulatory compliance is required, the AuthorizationForm and DataUseLegalBasis objects must be populated to record delivery status — raw DocGen alone does not satisfy audit trail requirements for FINRA or GDPR.
- Do not use Document Builder (GA in Winter '25) for sensitive financial documents — Salesforce explicitly excludes Document Builder from PCI DSS compliance scope, making it unsuitable for most FSC compliance workflows.

---

## Core Concepts

### OmniStudio DocGen in the FSC Context

OmniStudio DocGen is the FSC-native document generation engine. It merges Word or PowerPoint templates with Salesforce record data retrieved via DataRaptor transforms, then renders the output to PDF (or DOCX). The result can be stored as a ContentDocument, delivered by email, or pushed to Experience Cloud portals. In FSC, DocGen is the preferred engine for compliance documents because it supports server-side rendering without client browser dependency, has an audit-friendly output chain, and integrates directly with OmniStudio OmniScripts for guided disclosure delivery workflows.

### Disclosure and Compliance Hub Data Model

FSC ships the Disclosure and Compliance Hub, built on top of the `AuthorizationForm`, `AuthorizationFormDataUse`, `AuthorizationFormConsent`, and `DataUseLegalBasis` standard objects. A well-designed compliance document workflow does not treat DocGen as a standalone feature: it uses DocGen to render the document, then writes an `AuthorizationFormConsent` record linking the rendered document to the contact and the legal basis (FINRA, GDPR Article 6, CCPA) to record that the disclosure was delivered, viewed, or acknowledged. Skipping this step means document generation happened but regulatory proof of delivery is absent.

### Permission Set Licenses for DocGen

OmniStudio DocGen requires three separate permission set licenses beyond FSC base:
1. **DocGen Designer** — authors who build and edit document templates.
2. **DocGen User** — end users who trigger document generation manually from the UI.
3. **DocGen Runtime** — required for automated server-side generation (API, batch Apex, Flow).

A common production failure is assigning only DocGen User when the org runs automated nightly statement jobs. Those jobs run under an integration user; that user needs DocGen Runtime. Forgetting this causes silent job failures or permission errors that surface only at batch time.

### Server-Side Batch Cap and Statement Run Design

The DocGen API enforces a hard limit of 1000 documents per hour on the server side. FSC implementations that generate monthly account statements for large books of business (10,000+ accounts) must plan batch processing windows carefully. The standard pattern is an Apex `Batchable` class that chunks account IDs into groups of 200–300 per batch interval, calls the DocGen REST API per chunk, and uses `System.scheduleBatch` or a nightly scheduled job to spread the load over 10–12 hours before the delivery deadline.

---

## Common Patterns

### Pattern 1 — FINRA Disclosure Delivery Workflow

**When to use:** A financial advisor's client onboarding or annual review requires delivering a Form ADV or investment advisory agreement that must be recorded as delivered and acknowledged.

**How it works:**
1. OmniScript captures advisor context and client record ID.
2. A DataRaptor Extract fetches client name, address, account type, and advisor CRD number from `FinancialAccount`, `Contact`, and `Account` objects.
3. DocGen merges the data into a pre-approved Word template and renders a PDF stored as a `ContentDocument` linked to the Contact.
4. The OmniScript writes an `AuthorizationFormConsent` record with `Status = Agreed`, `ConsentGivenAt = now()`, and a reference to the `AuthorizationForm` representing the Form ADV version.
5. An email action sends the PDF to the client; the `EmailMessage` record is linked to the `AuthorizationFormConsent`.

**Why not raw email attachment:** Emailing a PDF directly has no FSC audit trail. Without the `AuthorizationFormConsent` record, there is no machine-readable proof of delivery that satisfies FINRA record-keeping rules (Rule 4511).

### Pattern 2 — Batch Account Statement Generation

**When to use:** Monthly or quarterly statement production for hundreds or thousands of financial accounts.

**How it works:**
1. A nightly `Schedulable` Apex job queries all active `FinancialAccount` records with a statement preference of `Mail` or `Portal`.
2. The `Batchable` class processes accounts in chunks of 200. Each chunk calls the DocGen REST API using a named credential and a prepared `DocGenDocument` JSON payload containing the template ID and record IDs.
3. DocGen renders each statement PDF server-side and attaches the output as a `ContentDocument` linked to the `FinancialAccount`.
4. Statements flagged for portal delivery are shared to the Experience Cloud site through `ContentDistribution`; paper statements are handed off to a print vendor via an outbound `Platform Event`.
5. A post-batch summary record logs run completion time, document count, and any failures for operations review.

**Why not OmniScript for batch:** OmniScript is an interactive UI engine — it requires a user session. Server-side batch generation must use the DocGen API directly or via a headless Apex callout.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Interactive disclosure delivery during onboarding | OmniScript + DocGen + AuthorizationFormConsent | Combines guided UX, document merge, and compliance record in one workflow |
| Automated monthly account statements for 10,000+ accounts | Batch Apex → DocGen API, chunked at 200/batch | Respects 1000 docs/hour server cap; runs overnight without UI dependency |
| Sensitive financial document requiring PCI-in-scope handling | OmniStudio DocGen only (not Document Builder) | Document Builder is explicitly excluded from Salesforce's PCI DSS compliance scope |
| Simple branded letter with no regulatory obligation | Document Builder or Salesforce Files | Lighter weight; OmniStudio DocGen overhead is not justified without compliance needs |
| Proof-of-delivery audit trail required (FINRA, GDPR) | AuthorizationFormConsent + ContentDocument link | DocGen alone does not record delivery; the consent record is the legal artifact |
| Multi-language regulatory disclosure | DocGen template with locale-conditional sections | DataRaptor can pass `Contact.Language__c`; Word template conditional blocks handle language variants |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify licensing and permissions** — Confirm FSC Industries license is active, OmniStudio DocGen is enabled in the org, and the correct DocGen permission set licenses (Designer / User / Runtime) are assigned to the relevant user profiles. Automated jobs need the Runtime license assigned to the integration user.

2. **Model the compliance data requirement** — Identify whether the workflow requires an `AuthorizationForm` record (representing the regulatory document version), a `DataUseLegalBasis` record (the legal basis for data use), and an `AuthorizationFormConsent` record (the per-contact delivery acknowledgment). Create these records and their relationships before building the DocGen template.

3. **Build the DataRaptor Extract** — Design a DataRaptor Extract transform that fetches all data the template needs: contact demographics, financial account fields, advisor information, and any calculated values. Test the DataRaptor independently against real records before wiring it to DocGen.

4. **Design and validate the DocGen template** — Create the Word template using OmniStudio DocGen Designer. Use `{{}}`-style merge fields mapped to DataRaptor output keys. Validate the template against a sample record set and confirm the PDF output matches compliance team requirements (font size, required disclosures, page ordering).

5. **Build the delivery orchestration** — For interactive workflows, build the OmniScript that calls DocGen, stores the PDF, writes the `AuthorizationFormConsent`, and sends the email confirmation. For batch workflows, build the Apex `Batchable` class that chunks accounts and calls the DocGen API, staying within the 1000 documents/hour limit.

6. **Test delivery and audit trail** — Run end-to-end tests covering: PDF renders correctly, `ContentDocument` is linked to the right parent object, `AuthorizationFormConsent` is written with correct `Status`, and the email or portal delivery confirmation is recorded.

7. **Review with compliance stakeholders** — Before production deploy, have compliance and legal sign off on the rendered PDF against the approved disclosure language. Confirm the audit trail records satisfy the regulatory record-keeping period requirements (FINRA: 6 years for records, 3 years easily accessible).

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] DocGen Runtime permission set license is assigned to the integration user running automated jobs
- [ ] AuthorizationFormConsent record is written for every compliance document generated, not just stored
- [ ] Batch job chunk size does not exceed the DocGen API 1000 documents/hour server-side limit
- [ ] Document Builder is NOT used for PCI-in-scope or highly sensitive financial documents
- [ ] DataRaptor Extract tested independently against representative records before DocGen template wiring
- [ ] PDF output reviewed and signed off by compliance/legal team before production deploy
- [ ] Retention and deletion policy for generated ContentDocuments aligns with regulatory requirements (FINRA 6-year rule)
- [ ] Experience Cloud portal delivery tested if statements are delivered via portal channel

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **DocGen Runtime License Missing for Automated Jobs** — Server-side DocGen API calls fail silently or return permission errors when the integration user running a batch Apex job lacks the DocGen Runtime permission set license. This license is separate from DocGen User and is frequently missed because interactive testing (which uses a human user with DocGen User) succeeds but the nightly batch fails. Always assign DocGen Runtime to the integration user profile and verify with a dedicated sandbox batch run before go-live.

2. **Document Builder PCI Exclusion** — Document Builder, GA in Winter '25, is not covered by Salesforce's PCI DSS compliance attestation. This means any document containing card numbers, account routing data, or other PCI-in-scope data must use OmniStudio DocGen, not Document Builder. The visual similarity between the two tools causes practitioners to choose Document Builder for its lower setup cost, creating a compliance gap that is difficult to remediate post-launch.

3. **AuthorizationFormConsent Is the Audit Record, Not the PDF** — The `ContentDocument` storing the generated PDF proves a document exists but does not prove delivery or acknowledgment to a regulator. FINRA Rule 4511 and GDPR Article 7 require machine-readable proof of when consent or disclosure was given. The `AuthorizationFormConsent` record with a `ConsentGivenAt` timestamp and a `Status` of `Agreed` is that proof. Omitting this record means the DocGen workflow is incomplete from a compliance standpoint even if the PDF is perfect.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| DocGen template (Word) | Merge-field template stored in OmniStudio DocGen Designer, maps to DataRaptor output keys |
| DataRaptor Extract transform | Fetches all record data required by the template; testable independently |
| AuthorizationForm record | Represents the regulatory document version (e.g., Form ADV version 2024-Q4) |
| AuthorizationFormConsent record | Per-contact delivery record with timestamp and status — the regulatory proof artifact |
| Batch Apex job | Chunked Batchable/Schedulable class for large statement runs respecting the 1000 docs/hour cap |
| ContentDocument links | Stored rendered PDFs linked to the appropriate FSC parent object (FinancialAccount, Contact) |

---

## Related Skills

- omnistudio/document-generation-omnistudio — Covers OmniStudio DocGen mechanics (template authoring, DataRaptor wiring, output format options) independent of FSC; use alongside this skill when building or debugging the DocGen template layer
- admin/fsc-action-plans — Covers FSC Action Plan templates; use when disclosures must trigger follow-up task sequences (e.g., obtain signed disclosure before proceeding with account opening)
