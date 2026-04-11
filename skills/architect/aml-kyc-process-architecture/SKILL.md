---
name: aml-kyc-process-architecture
description: "Use when designing the architecture for AML/KYC compliance workflows on Salesforce — covering verification orchestration, third-party screening integration patterns, risk scoring design, and regulatory data flow. Triggers: AML architecture, KYC verification workflow design, sanctions screening integration, customer risk rating design, onboarding compliance workflow, watchlist screening Salesforce, FinCEN / FATF obligation data flow, BSA compliance architecture. NOT for implementing KYC data collection forms or FSC Action Plans (use admin/fsc-action-plans). NOT for configuring FSC Identity Verification for contact-center caller authentication. NOT for production screening vendor ISV configuration."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
tags:
  - aml
  - kyc
  - fsc
  - compliance
  - sanctions-screening
  - risk-scoring
  - integration-patterns
  - financial-services
inputs:
  - Salesforce edition and FSC license type (FSC standard, FSC Plus, CRM Analytics license status)
  - Third-party screening vendor(s) in scope (Refinitiv World-Check, Accuity/Fircosoft, LexisNexis, etc.)
  - Regulatory jurisdiction and AML program requirements (BSA/FinCEN, FATF, EU AMLD, etc.)
  - Customer risk tiers and the attributes used to define them
  - Expected onboarding volume and screening throughput requirements
  - Existing integration middleware (MuleSoft, Heroku, external ESB) if any
outputs:
  - AML/KYC process architecture document with component responsibilities and data flow
  - Screening integration pattern recommendation with synchronous vs. asynchronous decision rationale
  - Risk scoring design (scoring model, PartyProfileRisk usage, tier definitions)
  - Orchestration layer design (Flow, OmniStudio Integration Procedures, or Apex callout)
  - Compliance data retention and audit trail design
triggers:
  - "designing AML sanctions screening integration on Salesforce FSC"
  - "KYC verification workflow architecture with third-party screening vendor"
  - "customer risk scoring design for regulatory compliance in FSC"
  - "onboarding compliance workflow with FinCEN or FATF obligations"
  - "PartyProfileRisk object usage for AML risk tier storage"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# AML/KYC Process Architecture

Use this skill when designing the Salesforce-side architecture for Anti-Money Laundering (AML) and Know Your Customer (KYC) compliance workflows. It covers the orchestration layer that drives screening calls, the integration patterns for connecting to mandatory third-party sanctions and watchlist screening vendors, and the risk scoring design that produces regulatory customer risk ratings. This skill is architectural — it produces design artifacts, not implementation code.

Salesforce Financial Services Cloud (FSC) does not contain a native AML engine or sanctions screening service. The platform provides orchestration primitives (Flows, OmniStudio Integration Procedures, Apex callouts) and standard data model objects (notably `PartyProfileRisk`) that store and route results from mandatory third-party ISV screening calls. Every compliant AML/KYC architecture on Salesforce depends on an external screening vendor; this skill helps you design how Salesforce orchestrates those external calls and what it does with the results.

---

## Before Starting

- **Confirm FSC license type.** The `PartyProfileRisk` object and risk-category fields are part of the FSC data model and require an FSC license. The Industries Scoring Framework (propensity scoring via CRM Analytics apps) requires CRM Analytics Plus license on top of an FSC product license — it is not the same as a regulatory AML risk engine.
- **Identify the screening vendor(s) early.** Salesforce has no native watchlist, PEP (Politically Exposed Person), or adverse media data. The architecture cannot be designed without knowing whether the vendor exposes a REST API, a batch file interface, or an AppExchange managed package with its own data model.
- **Do not assume FSC Identity Verification is AML-relevant.** FSC Identity Verification is a contact-center feature that authenticates callers against stored identity records using Salesforce Connect APIs. It performs no biometric check, no sanctions match, and no PEP screening. Conflating it with KYC identity proofing is a common and dangerous misunderstanding.
- **Know the throughput envelope.** Synchronous callouts from Salesforce Flows and Apex are capped at 10 seconds timeout and 100 callouts per transaction. High-volume onboarding (thousands of records per day) almost certainly requires an asynchronous batch screening architecture, not a synchronous record-save trigger.
- **Determine data residency requirements.** Some AML regulations require that screening results and risk decisions remain within a specific geographic region. If the org uses Hyperforce, confirm the data residency pod aligns with regulatory jurisdiction before designing the data flow.

---

## Core Concepts

### FSC Has No Native AML Engine — Salesforce Is the Orchestrator

The most important architectural principle for AML/KYC on Salesforce is that FSC provides the workflow shell and data model, not the screening intelligence. Compliance decisions come from external vendors; Salesforce stores, routes, and surfaces them. The architecture must be designed around this separation of concerns:

- **External vendor:** performs sanctions list matching (OFAC, UN, EU), PEP screening, adverse media screening, and returns a match result (clear, potential match, confirmed match) with a case reference number.
- **Salesforce:** triggers the vendor call at the correct point in the onboarding or periodic review workflow, receives the result, maps it to the `PartyProfileRisk` record (or a custom object if the vendor has its own managed package schema), and routes the result to the right queue or decision workflow.

A well-architected design treats the vendor API as a remote system with its own SLA and failure modes — not as a Salesforce extension.

### PartyProfileRisk and the FSC Data Model

`PartyProfileRisk` is a standard FSC object that stores risk assessment records for individuals and accounts. Key fields:

- `RiskCategory` — a picklist (typically Low / Medium / High / Prohibited) that represents the customer's regulatory risk tier. This is the field most downstream compliance workflows key off.
- `RiskScore` — a numeric score. This field can be populated by custom Apex scoring logic, a CRM Analytics model output, or a vendor-returned score.
- `RiskReason` — a text field for documenting the reason for the current risk rating, essential for audit trail.
- `RiskReviewDate` — the date by which the risk rating must be reviewed. Driving periodic review triggers from this field is the standard FSC pattern.

`PartyProfileRisk` records are associated with an `Individual` record (the FSC person model), not directly with a Contact. This means the onboarding flow must ensure an `Individual` record exists before creating or updating a `PartyProfileRisk`.

### Orchestration Layer Options

Three orchestration mechanisms are available, each with different tradeoffs for AML/KYC workflows:

1. **OmniStudio Integration Procedures** — best for real-time, guided onboarding flows where a human is present and the screening result must be surfaced immediately in the UI. Integration Procedures are callable from OmniScript steps, can chain multiple API calls, and have built-in response mapping. Requires OmniStudio license.

2. **Apex callouts with Platform Events** — best for fully automated, non-interactive screening (periodic review, batch re-screening). The Apex layer calls the vendor REST API, receives the response, and publishes a Platform Event. A separate subscriber flow or trigger processes the event and updates `PartyProfileRisk`. Decouples the screening call from the DML transaction.

3. **Screen Flow / Record-Triggered Flow** — acceptable for simple low-volume cases where the vendor provides a reliable, fast synchronous API and onboarding volume is below a few hundred records per day. Synchronous callouts from Flows share the same 10-second callout timeout as Apex synchronous callouts. Do not use a record-triggered Flow with a synchronous callout for bulk-imported accounts.

### Risk Scoring Design

Risk scoring in an AML context produces a customer risk rating (typically Low / Medium / High / Prohibited) based on a combination of factors: screening result, geography, product type, customer type (individual, corporate, PEP), and transaction behavior. Salesforce's Industries Scoring Framework uses CRM Analytics propensity models — it is designed for marketing and sales scoring, not for regulatory risk rating. Custom scoring logic is the standard pattern:

- **Rule-based Apex scoring** — the most common approach. An Apex class evaluates the screening result plus contextual attributes and writes a `RiskCategory` value and a `RiskScore` to `PartyProfileRisk`. This approach is deterministic, auditable, and does not require CRM Analytics licensing.
- **DataWeave transformations** — useful when the scoring inputs arrive as a complex JSON payload from the screening vendor and need transformation before writing to Salesforce objects.
- **CRM Analytics app** — viable if the institution already has CRM Analytics Plus and wants a data-science-driven model for risk tiering, but requires additional governance to ensure the model output meets regulatory explainability requirements.

---

## Common Patterns

### Pattern A: Real-Time Screening via OmniStudio Integration Procedure

**When to use:** Guided onboarding flow with a human agent present; screening result must be visible in the OmniScript UI before the agent can advance; vendor exposes a REST API that responds within 3–5 seconds; onboarding volume is below ~500 records per day.

**How it works:**

1. OmniScript collects customer identity data (name, date of birth, nationality, ID document).
2. On a dedicated screening step, the OmniScript invokes an Integration Procedure.
3. The Integration Procedure calls the vendor REST API via an HTTP Action element. The Named Credential stores the endpoint and credentials; no hardcoded secrets in the procedure.
4. The Integration Procedure maps the vendor response to Salesforce fields using a DataRaptor Transform or inline DataWeave expression.
5. The Integration Procedure performs a DML operation to create or update the `PartyProfileRisk` record with the screening result, risk category, and vendor case reference number.
6. The OmniScript displays the result and, if a potential match is returned, routes to a compliance review queue via a Screen Flow or Case assignment rule.

**Why not a record-triggered Flow:** Record-triggered Flows that make synchronous callouts run inside the saving transaction. If the vendor API is slow or unavailable, the entire record save fails. This creates a poor user experience and risks data loss. OmniScript separates the screening step from record creation.

### Pattern B: Asynchronous Batch Re-Screening via Apex + Platform Events

**When to use:** Periodic AML review of an existing customer portfolio; bulk import of new accounts; screening vendor operates a batch file interface rather than a real-time REST API; onboarding volume exceeds synchronous callout limits.

**How it works:**

1. A scheduled Apex batch job (`Database.Batchable`) queries `Individual` or `Account` records due for re-screening based on `PartyProfileRisk.RiskReviewDate`.
2. The batch job groups records and makes callouts to the vendor REST API in `execute()` scope (callouts from batch Apex execute methods are supported; the interface must implement `Database.AllowsCallouts`).
3. For each vendor response, the batch job publishes a Platform Event (`ScreeningResult__e`) containing the vendor case reference, match status, and risk score.
4. A separate Platform Event trigger or record-triggered Flow subscribes to `ScreeningResult__e` and updates the `PartyProfileRisk` record. Decoupling DML from the batch callout prevents governor limit collisions.
5. Cases are opened automatically for potential matches via a Flow or Process Builder replacement; cases are assigned to a compliance review queue.

**Why not a single synchronous Apex transaction:** Each synchronous Apex transaction is limited to 100 callouts. For a portfolio of 50,000 customers requiring annual re-screening, the batch architecture with Platform Events is the only governor-limit-safe pattern.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Guided human-assisted onboarding, vendor has fast REST API | OmniStudio Integration Procedure + OmniScript | Response surfaced inline; agent sees result before advancing |
| Automated onboarding, no human in loop | Apex callout (future or queueable) + Platform Event | Decouples screening from record save; handles async response |
| Periodic portfolio re-screening at scale | Scheduled Batch Apex + Platform Events | Only pattern that handles callout limits for large data volumes |
| Vendor provides managed package, not raw REST API | Follow vendor's documented Salesforce integration pattern | Vendor package may use its own objects; map results to PartyProfileRisk in a separate step |
| Risk scoring: rule-based, must be auditable | Custom Apex scoring class writing to PartyProfileRisk | Deterministic, explainable, no additional licensing required |
| Risk scoring: data-science model, CRM Analytics licensed | CRM Analytics app + Apex writer class | Model produces score; Apex writes result to RiskScore / RiskCategory |
| Vendor response may be delayed (async callback) | Inbound REST endpoint on Salesforce (Remote Call-In pattern) | Vendor POSTs result back; Salesforce updates PartyProfileRisk on receipt |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on AML/KYC process architecture:

1. **Confirm the platform baseline** — verify FSC is enabled, identify the FSC license type, confirm whether OmniStudio is licensed, and establish which Salesforce edition (Enterprise or Unlimited) is in use. Record whether `PartyProfileRisk` is already in use or must be configured from scratch.

2. **Define the screening integration contract** — identify the third-party screening vendor, obtain the vendor's API specification (REST endpoint, authentication method, request/response schema, SLA/timeout), and determine whether the vendor supports synchronous response or asynchronous callback (Remote Call-In pattern). Create a Named Credential for the endpoint.

3. **Select the orchestration pattern** — using the Decision Guidance table above, choose OmniStudio Integration Procedure (guided/real-time), Apex callout + Platform Event (automated/async), or Batch Apex (periodic/bulk). Document the rationale in the architecture decision record.

4. **Design the risk scoring model** — define the risk tier definitions (Low / Medium / High / Prohibited), list the inputs to the scoring decision (screening result, geography, customer type, product type), and choose the scoring implementation (rule-based Apex vs. CRM Analytics). Map outputs to `PartyProfileRisk.RiskCategory`, `RiskScore`, and `RiskReason`.

5. **Design the compliance review workflow** — define what happens for each screening outcome: clear (auto-advance), potential match (route to compliance queue, open Case), confirmed match (block onboarding, escalate). Specify SLAs per outcome tier and design the Case assignment rules or Omni-Channel routing.

6. **Design the audit trail and data retention** — identify which fields and events must be logged for regulatory audit (screening request timestamp, vendor response, risk decision, decision override with reason, reviewer identity). Determine whether Shield Field Audit Trail is required to meet retention obligations beyond the platform's 18-month field history.

7. **Validate the architecture against governor limits** — calculate expected screening volume per day, per transaction, and per batch. Verify the chosen pattern stays within the 100 callout / 10-second timeout limits for synchronous paths and the batch size limits for asynchronous paths. Document the throttling and retry strategy for vendor API failures.

---

## Review Checklist

Run through these before marking the architecture design complete:

- [ ] `PartyProfileRisk` object is in the data model; `RiskCategory`, `RiskScore`, `RiskReason`, and `RiskReviewDate` field usage is defined
- [ ] Named Credential exists or is designed for the screening vendor endpoint — no hardcoded credentials in code or metadata
- [ ] Orchestration pattern is documented and governor limit calculations are present
- [ ] Synchronous vs. asynchronous decision is explicitly justified against volume and SLA requirements
- [ ] Risk scoring inputs, tier definitions, and output field mappings are documented
- [ ] Compliance review routing (clear / potential match / confirmed match) is designed with queue assignments and SLAs
- [ ] Audit trail fields and retention requirements are specified; Shield need is assessed
- [ ] Vendor failure / timeout handling and retry strategy are documented
- [ ] FSC Identity Verification is not conflated with KYC identity proofing or sanctions screening in the design

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Synchronous callouts inside record-triggered Flows are blocked for bulk operations** — Record-triggered Flows that invoke a subflow or action making an HTTP callout will fail for records processed via bulk data load (Data Loader, Data Import Wizard, Apex DML on multiple records). The platform blocks synchronous callouts in bulk context. Any AML screening triggered by a record save must either be deferred to an async process or use a before-save Flow that only enqueues the work rather than executing the callout inline.

2. **PartyProfileRisk requires an Individual record, not a Contact** — FSC's person model separates `Individual` (the person) from `Contact` (the CRM record). `PartyProfileRisk` is a child of `Individual`. If the onboarding workflow creates Contacts without creating corresponding `Individual` records (which is possible in standard Salesforce without FSC), there is no parent to attach a `PartyProfileRisk` to. Validate the Individual record exists — and has the expected `IndividualId` on the Contact — before attempting to create the risk record.

3. **Platform Events do not guarantee delivery order** — In the asynchronous screening pattern (Apex publishes `ScreeningResult__e`, a Flow subscriber updates `PartyProfileRisk`), Platform Events are delivered at-least-once but not in guaranteed order. If two screening results for the same customer arrive close together (e.g., initial screen and an immediate re-screen), the older result could overwrite the newer one if the subscriber does not compare timestamps. Always include the screening timestamp in the event payload and guard the DML update with a timestamp comparison.

4. **The Industries Scoring Framework is not a regulatory risk engine** — The FSC Scoring Framework (requires CRM Analytics Plus) generates propensity scores using CRM Analytics models. It is designed for marketing segmentation and sales prioritization. It does not produce audit-ready, explainable risk ratings suitable for AML regulatory purposes without significant custom governance layering. Presenting it to a compliance team as an AML risk engine will create a compliance gap.

5. **Named Credentials with Per-User authentication do not work in batch or scheduled Apex** — Named Credentials configured with `Per-User` authentication require a user session to resolve the OAuth token. Batch jobs, scheduled jobs, and future methods run in a system context with no session — they will throw a callout exception. AML screening that runs in batch context must use `Named Principal` (org-level) authentication on the Named Credential, or use an external credential with a service account token.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| AML/KYC architecture document | Component responsibilities, data flow diagram description, integration contract summary |
| Orchestration pattern decision record | Selected pattern, volume calculations, governor limit analysis, rationale |
| Risk scoring design | Tier definitions, scoring inputs, implementation choice, field mapping to PartyProfileRisk |
| Compliance review routing design | Outcome-based routing rules, queue assignments, SLA definitions |
| Audit trail and retention specification | Fields to log, retention period, Shield assessment |

---

## Related Skills

- `admin/fsc-action-plans` — use for designing the task-based KYC data collection workflow that precedes screening; this skill covers the architecture of the screening integration itself
- `architect/security-architecture-review` — use to assess the broader org security posture including the Connected App and Named Credential configuration that backs the screening vendor integration
- `architect/integration-framework-design` — use for the broader integration layer design when AML screening is one component of a larger FSC integration architecture
- `architect/wealth-management-architecture` — FSC data model context for Individual, Account, and FinancialAccount relationships that underpin the PartyProfileRisk placement
