---
name: fhir-integration-architecture
description: "Use this skill when architecting how Health Cloud connects to external EHR/EMR systems via FHIR R4 — covering integration pattern selection, transformation layer design, MuleSoft Accelerator usage, and EMR bidirectional sync topology. NOT for individual FHIR REST API call implementation, NOT for FHIR object-level data mapping or Apex code that reads/writes specific Health Cloud objects, and NOT for HL7 v2 message parsing internals."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Scalability
  - Operational Excellence
triggers:
  - "how should we connect our Epic EHR to Health Cloud using FHIR"
  - "what integration pattern should we use to sync patient data from Cerner into Salesforce"
  - "we need real-time clinical data from an external FHIR server in Health Cloud — what is the right architecture"
  - "how does MuleSoft Accelerator for Healthcare help us ingest FHIR bundles"
  - "should we use bulk FHIR export or event-driven ingestion for our EMR integration"
tags:
  - fhir
  - health-cloud
  - ehr-integration
  - mulesoft
  - interoperability
  - emr-sync
inputs:
  - "Source EMR/EHR system (Epic, Cerner, other HL7 or FHIR-capable system)"
  - "Data freshness requirements (real-time, near-real-time, batch)"
  - "Volume profile (number of patients, frequency of updates)"
  - "Directionality requirement (inbound only, bidirectional)"
  - "Whether HL7 v2 legacy feeds exist alongside FHIR R4 endpoints"
  - "Existing middleware inventory (MuleSoft, Boomi, custom API gateway)"
outputs:
  - "Integration pattern recommendation with rationale (one of four canonical patterns)"
  - "Transformation layer design specifying where FHIR-to-Health-Cloud mapping occurs"
  - "Decision table documenting pattern selection criteria"
  - "Risk and gotcha inventory for the chosen approach"
  - "Architecture review checklist"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# FHIR Integration Architecture

This skill activates when an architect must decide how Health Cloud will connect to an external EHR or EMR system using FHIR R4. It covers the four canonical sync patterns, the mandatory transformation layer, and how MuleSoft Accelerator for Healthcare fits into the topology. It does not cover low-level Apex coding, individual object mappings, or HL7 v2 parsing internals.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm Health Cloud is enabled** and that the FHIR R4 feature is licensed. The Generic FHIR Client and FHIR ingestion features require Health Cloud, not just core Salesforce.
- **Clarify data freshness requirements.** Real-time clinician-facing use cases require a different pattern than overnight batch reconciliation. Mismatched pattern selection is the most common architectural error.
- **Identify whether HL7 v2 legacy feeds exist** alongside FHIR R4 endpoints. Many EMRs (Epic, Cerner) emit both. HL7 v2 ADT/ORU messages cannot be ingested directly into Health Cloud and require MuleSoft conversion to FHIR R4 first.
- **Confirm whether integration is inbound only or bidirectional.** Bidirectional sync introduces write-back conflict resolution complexity that must be designed explicitly.
- **Check the 26-resource limit.** Salesforce's FHIR R4 implementation maps approximately 26 FHIR R4 resource types. Resources outside this set cannot be stored in Health Cloud's clinical data model without custom extension objects.

---

## Core Concepts

### Health Cloud is NOT a Conformant FHIR Server

Salesforce Health Cloud is a FHIR-aware CRM platform, not a fully conformant FHIR server. It supports approximately 26 FHIR R4 resource types mapped to its clinical data model. Data is stored in a denormalized relational structure across child objects — not in the one-to-many FHIR resource graph model. Raw FHIR bundles cannot be persisted directly. Every inbound FHIR payload must pass through a transformation layer that maps FHIR elements to Health Cloud object fields before storage. Architects who treat Health Cloud as a FHIR endpoint will design the wrong data flow.

### The Four Canonical Sync Patterns

Health Cloud FHIR R4 supports four documented integration patterns. Pattern selection drives every downstream architectural decision.

**Pattern 1 — Real-Time REST Query (Generic FHIR Client):** Health Cloud queries an external FHIR server on demand, typically triggered by a user opening a patient record. Data is fetched at query time and displayed or stored transiently. No persistent copy is written to Health Cloud objects unless a separate write step is implemented. Best for supplemental reference data that does not need to live in Salesforce long-term.

**Pattern 2 — Event-Driven Inbound Ingestion:** An external system pushes FHIR resources into Salesforce via Platform Events or a REST inbound endpoint. MuleSoft or another middleware layer receives the EMR event, transforms the payload, and writes to Health Cloud. Appropriate for real-time notifications such as ADT events (admissions, discharges, transfers) that need to create or update records immediately.

**Pattern 3 — Bulk FHIR Batch Retrieval:** Uses the FHIR `$export` operation to retrieve large volumes of FHIR resources from an EMR in bulk, typically on a schedule. Payloads are NDJSON files that must be transformed before loading into Health Cloud. Appropriate for initial data migration or nightly reconciliation of large patient populations.

**Pattern 4 — Scheduled EMR Bidirectional Sync:** A scheduled integration job reads changes from both the EMR and Health Cloud, reconciles differences, and writes updates in both directions. This is the most complex pattern and requires explicit conflict resolution rules. Appropriate when Health Cloud is a system of record for certain data (e.g., care plans) that must flow back to the EMR.

### Transformation Layer is Mandatory

Every FHIR integration pattern requires a transformation layer between the FHIR resource representation and Health Cloud's object model. MuleSoft Accelerator for Healthcare provides pre-built DataWeave transformations for Epic and Cerner that map common FHIR R4 resources (Patient, Encounter, Observation, Condition, MedicationRequest) to Health Cloud objects. For custom EMRs or resources not covered by the Accelerator, custom DataWeave or Apex-based transformation must be built. The transformation layer must handle FHIR Bundle unwrapping, resource type routing, and identifier cross-referencing.

### HL7 v2 Requires Conversion Before Ingestion

Many production EMR environments emit both FHIR R4 and HL7 v2 messages (lab results as ORU^R01, ADT events as ADT^A01/A08). HL7 v2 is a pipe-delimited message format that Health Cloud has no native parser for. MuleSoft Accelerator for Healthcare includes HL7 v2 to FHIR R4 conversion assets. Any architecture that receives HL7 v2 feeds must route them through MuleSoft (or an equivalent middleware) for conversion before the FHIR ingestion pipeline begins.

---

## Common Patterns

### Real-Time Clinical Data Supplementation (Generic FHIR Client)

**When to use:** A clinician or care coordinator opens a patient record in Health Cloud and needs to see the latest vitals, lab results, or medications from an external EHR in real time. Data does not need to persist in Salesforce between sessions.

**How it works:**
1. Configure a Named Credential pointing to the external FHIR server endpoint.
2. Enable the Generic FHIR Client in Health Cloud setup and associate it with the Named Credential.
3. A Lightning Web Component or Flow on the patient record page triggers a FHIR query (e.g., `GET /Patient/{id}/Observation`) when the record loads.
4. Results are displayed inline. Optionally, a subset of critical values can be written back to Health Cloud object fields for audit or alerting purposes.

**Why not the alternative:** Storing every real-time query result as persistent Health Cloud records creates record bloat and stale data problems. The Generic FHIR Client pattern avoids this by keeping Health Cloud as the system of engagement without duplicating the EHR's source-of-truth data.

### Event-Driven ADT Ingestion via MuleSoft

**When to use:** The EMR fires admission, discharge, and transfer events that must immediately create or update Health Cloud episode records, trigger care gap alerts, or enroll patients in care programs.

**How it works:**
1. EMR publishes ADT events (HL7 v2 ADT^A01 or FHIR Encounter resource) to a message bus or webhook.
2. MuleSoft Accelerator for Healthcare receives the event, converts HL7 v2 to FHIR R4 if necessary, and executes the DataWeave transformation to Health Cloud object format.
3. MuleSoft calls the Health Cloud REST API or Composite API to create/update the Patient, EpisodeOfCare, or related objects.
4. A Platform Event is optionally published to trigger downstream Flows or Apex for care plan enrollment or task creation.

**Why not the alternative:** Polling the EMR on a schedule for new encounters introduces minutes-to-hours of latency for time-sensitive workflows like care gap closure at point of admission.

---

## Decision Guidance

| Situation | Recommended Pattern | Reason |
|---|---|---|
| Clinician needs latest EHR data on record open; data need not persist in Salesforce | Real-Time REST Query (Generic FHIR Client) | Avoids data duplication and stale record issues; data is always fetched live from source of truth |
| ADT events (admit/discharge/transfer) must trigger immediate Salesforce record updates or workflows | Event-Driven Inbound Ingestion | Lowest latency; EMR push model avoids polling overhead |
| Initial load or nightly reconciliation of large patient populations (10k+ records) | Bulk FHIR Batch ($export) | Purpose-built for high-volume extraction; NDJSON format is efficient for batch transform pipelines |
| Health Cloud care plans or clinical notes must flow back to the EMR | Scheduled EMR Bidirectional Sync | Only pattern that handles write-back; requires explicit conflict resolution design |
| EMR exposes only HL7 v2 (no FHIR R4 endpoint) | Event-Driven Inbound via MuleSoft with HL7 v2 conversion | MuleSoft Accelerator provides HL7 v2 to FHIR R4 conversion; output feeds the standard ingestion pipeline |
| Multiple patterns are needed simultaneously (e.g., real-time view + nightly sync) | Hybrid: Generic FHIR Client for on-demand reads + Bulk for baseline population | Common production topology; ensure named credentials and transformation configs are shared |

---

## Recommended Workflow

Step-by-step instructions for an architect working on FHIR integration design:

1. **Gather requirements against the four pattern dimensions.** Confirm data freshness SLA, volume profile, directionality, and whether HL7 v2 feeds exist. Document findings before any design work begins.

2. **Map each data domain to a pattern.** Not all clinical data domains require the same pattern. Vitals and labs may be real-time reads; ADT events may be event-driven; medication history may be bulk. Create a data domain-to-pattern matrix.

3. **Confirm the transformation layer scope.** For each pattern, identify which FHIR R4 resources are involved and whether they fall within Health Cloud's supported 26-resource set. For unsupported resources, design custom extension objects or determine whether they can be stored as external data references.

4. **Design the middleware topology.** If MuleSoft is in scope, confirm whether MuleSoft Accelerator for Healthcare assets cover the EMR (Epic, Cerner have pre-built assets; custom EMRs require custom DataWeave). Document where HL7 v2 conversion occurs in the pipeline.

5. **Design error handling and retry logic for each pattern.** Real-time queries need circuit breaker patterns. Event-driven ingestion needs dead-letter queues. Bulk jobs need idempotent upsert logic (use the EMR patient identifier as the external ID in Health Cloud).

6. **Validate the architecture against the review checklist** (see below) before presenting to stakeholders or handing off to implementation teams.

7. **Document integration pattern decisions in the ADR template** (`templates/fhir-integration-architecture-template.md`) so the rationale is traceable during implementation and future reviews.

---

## Review Checklist

Run through these before marking FHIR integration architecture work complete:

- [ ] Each data domain has been explicitly assigned to one of the four canonical sync patterns with written rationale
- [ ] The transformation layer is designed for every pattern — no pattern assumes raw FHIR bundles are persisted directly into Health Cloud
- [ ] HL7 v2 feeds have been identified and routed through a conversion step before the FHIR ingestion pipeline
- [ ] The 26-resource limit has been verified — FHIR resources outside Health Cloud's supported set have a design decision documented
- [ ] Error handling strategy is defined for each pattern (circuit breaker, dead-letter queue, idempotent upsert)
- [ ] Bidirectional sync conflict resolution rules are documented if write-back to the EMR is required
- [ ] Named Credentials and Connected App configuration for external FHIR endpoints are included in the design
- [ ] MuleSoft Accelerator asset coverage confirmed — custom DataWeave identified for any gaps

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Health Cloud is not a conformant FHIR server** — Salesforce's FHIR R4 support covers only ~26 resource types mapped to its internal data model. Architects who assume Health Cloud can receive and store any arbitrary FHIR resource will discover at implementation time that resources like CareTeam, ServiceRequest, or custom profiles with extensions not in the supported set have no target object. This forces late-stage redesign. Verify the supported resource list against the Health Cloud Developer Guide before finalizing scope.

2. **Raw FHIR bundles cannot be persisted directly** — There is no "save this Bundle to Health Cloud" API operation. Every FHIR bundle must be unwrapped, each contained resource identified by type, and each mapped individually to Health Cloud object fields before a DML/API write occurs. Architects who do not design an explicit transformation layer end up with ad hoc Apex parsing logic scattered across the codebase that is fragile and untestable.

3. **Generic FHIR Client does not cache results** — Data retrieved via the Generic FHIR Client on a patient record open is not automatically stored in Health Cloud. If a downstream process (Flow, Apex trigger, report) needs the retrieved data, the design must include an explicit write step. Architects who assume the client persists data will create phantom data dependencies.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Integration Pattern Decision Matrix | Table mapping each clinical data domain to a selected sync pattern with rationale |
| Transformation Layer Design | Document specifying which FHIR resources are transformed, by which middleware component, and to which Health Cloud objects |
| FHIR Resource Coverage Audit | List of FHIR resources in scope vs. Health Cloud's supported 26-resource set, with gap disposition |
| Architecture Decision Record (ADR) | Completed `fhir-integration-architecture-template.md` capturing decisions, tradeoffs, and risks |

---

## Related Skills

- `health-cloud-data-model` — use alongside this skill when designing the Health Cloud object model that will receive the transformed FHIR data
- `health-cloud-apex-extensions` — use when custom Apex is needed to supplement the transformation layer or implement post-ingestion business logic
- `hipaa-compliance-architecture` — use to ensure the chosen integration pattern meets HIPAA PHI data handling requirements
- `compliant-data-sharing-setup` — use when FHIR data sharing across org boundaries or external portals is in scope
