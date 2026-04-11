# FHIR Integration Architecture — Decision Record Template

Use this template to document integration pattern decisions for a Health Cloud FHIR integration project. Complete one record per distinct integration stream (e.g., one for ADT events, one for medication reconciliation).

---

## Project Context

**Project / Initiative name:** (fill in)

**Date:** (fill in)

**Architect / Author:** (fill in)

**Health Cloud org:** (Production / Sandbox / Scratch org URL or name)

**EMR / EHR system(s):** (Epic, Cerner, Meditech, custom, etc.)

**Salesforce Health Cloud version:** (e.g., Spring '25)

---

## Scope of This Integration Stream

**Data domain:** (e.g., Patient Demographics, ADT Events, Medication Reconciliation, Lab Results, Care Plans)

**FHIR R4 resources involved:**

| FHIR Resource | In Health Cloud's Supported Set (~26)? | Target Health Cloud Object | Notes |
|---|---|---|---|
| (e.g., Patient) | Yes | Account (PersonAccount) | — |
| (e.g., Encounter) | Yes | EpisodeOfCare | Map status codes to picklist values |
| (e.g., ServiceRequest) | No | Custom: ServiceRequest__c | Requires custom object and transform |

**Directionality:** Inbound only / Outbound only / Bidirectional (circle one)

**Data freshness SLA:** (e.g., real-time < 1 min, near-real-time < 5 min, batch daily)

**Peak volume estimate:** (e.g., 500 ADT events/day, 50k patient records initial load)

---

## Integration Pattern Selection

**Selected pattern:**

- [ ] Pattern 1 — Real-Time REST Query (Generic FHIR Client)
- [ ] Pattern 2 — Event-Driven Inbound Ingestion (MuleSoft + Platform Events)
- [ ] Pattern 3 — Bulk FHIR Batch Retrieval ($export)
- [ ] Pattern 4 — Scheduled EMR Bidirectional Sync
- [ ] Hybrid (describe below)

**Rationale for pattern selection:**

(Explain why this pattern was chosen over alternatives. Reference data freshness SLA, volume profile, and directionality requirements.)

**Patterns considered and rejected:**

| Pattern | Rejected Because |
|---|---|
| (e.g., Pattern 1) | (e.g., Data must persist in Salesforce for reporting — Generic FHIR Client does not persist) |
| (e.g., Pattern 3) | (e.g., 5-minute SLA cannot be met by batch) |

---

## Transformation Layer Design

**Where does FHIR-to-Health-Cloud transformation occur?**

- [ ] MuleSoft Accelerator for Healthcare (pre-built DataWeave assets — Epic/Cerner)
- [ ] Custom MuleSoft DataWeave (custom EMR or unsupported resource types)
- [ ] Apex-based transformation inside Salesforce (requires justification — see gotchas)
- [ ] Other middleware: (specify)

**DataWeave / transformation coverage:**

| FHIR Resource | Transformation Script | Handles Bundle Unwrapping? | Handles Identifier Cross-Reference? |
|---|---|---|---|
| Patient | (e.g., MuleSoft Accelerator patient-to-account.dwl) | Yes | Yes — maps MRN to External ID |
| Encounter | (custom DataWeave) | Yes | Partial — encounter ID only |

**External ID strategy:**

Describe the field used as the idempotent upsert key on each Health Cloud object:

| Health Cloud Object | External ID Field | Source in FHIR Resource |
|---|---|---|
| Account (Patient) | MRN__c | Patient.identifier where system = MRN |
| EpisodeOfCare | EMR_Encounter_ID__c | Encounter.identifier where system = encounter |

---

## HL7 v2 Handling (if applicable)

**Does the EMR emit HL7 v2 feeds (ADT, lab results)?**

- [ ] Yes — HL7 v2 feeds are in scope
- [ ] No — FHIR R4 only

**If yes, conversion approach:**

| HL7 v2 Message Type | Conversion Tool | Output FHIR Resource | Notes |
|---|---|---|---|
| ADT^A01 (Admission) | MuleSoft Accelerator HL7 v2 Listener | FHIR Encounter + Patient | Pre-built asset available |
| ORU^R01 (Lab Result) | Custom MuleSoft DataWeave | FHIR Observation | OBX segment mapping required |

---

## Authentication and Connectivity

**External FHIR endpoint(s):**

| EMR System | FHIR Base URL | Auth Method | Named Credential Name |
|---|---|---|---|
| (e.g., Epic) | https://epicfhir.example.org/api/FHIR/R4 | OAuth 2.0 SMART on FHIR | Epic_FHIR_NC |

**Connected App configuration required?** Yes / No / N/A

**OAuth scopes requested:** (e.g., patient/*.read, user/Encounter.read)

---

## Error Handling Strategy

| Pattern | Error Scenario | Handling Approach |
|---|---|---|
| Pattern 1 (Real-Time Query) | External FHIR server unavailable | Circuit breaker in MuleSoft; display "data unavailable" in LWC rather than error |
| Pattern 2 (Event-Driven) | Transform failure on incoming event | Dead-letter queue in MuleSoft; alert on-call via Salesforce Case or PagerDuty |
| Pattern 3 (Bulk Export) | Partial file failure mid-load | Checkpoint file tracks last processed line; reprocess from checkpoint on retry |
| Pattern 4 (Bidirectional) | Concurrent update conflict | Field-level ownership enforced in DataWeave; conflicts flagged as Tasks for human review |

---

## Conflict Resolution (Bidirectional Only)

Complete this section only if Pattern 4 (Bidirectional Sync) is selected.

**Conflict resolution strategy:**

- [ ] Field-level ownership (each field owned by one system)
- [ ] Timestamp-based last-write-wins with audit log
- [ ] Conflict flagging for human review
- [ ] Other: (describe)

**Field ownership table:**

| Field | Owner System | Rationale |
|---|---|---|
| (e.g., Medication List) | EMR | EMR is clinical system of record for prescribed medications |
| (e.g., Care Plan Goals) | Health Cloud | Care coordinators own goal-setting in Salesforce |

**Conflict audit log location:** (e.g., ConflictAuditLog__c object, Splunk, MuleSoft CloudHub logs)

---

## Risks and Open Issues

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| EMR exposes FHIR resources outside Health Cloud's ~26-resource set | Medium | High | Audit resource list before implementation sprint; design custom objects for gaps |
| HL7 v2 ADT message variants not covered by MuleSoft Accelerator | Low | Medium | Test against EMR's full ADT message catalog in pre-prod |
| Bulk $export file size exceeds MuleSoft worker memory | Medium | Medium | Implement NDJSON streaming line-by-line; size MuleSoft workers for peak file size |

---

## Architecture Review Sign-Off

| Reviewer | Role | Date | Decision |
|---|---|---|---|
| | Health Cloud Architect | | Approved / Changes Required |
| | Security Architect | | Approved / Changes Required |
| | EMR Integration Lead | | Approved / Changes Required |

---

## Review Checklist

Before presenting this ADR to stakeholders:

- [ ] Every FHIR resource in scope is verified against Health Cloud's supported resource list
- [ ] Transformation layer design covers every resource type — no "raw bundle storage" approach
- [ ] HL7 v2 feeds identified and conversion approach documented
- [ ] External ID fields defined for all Health Cloud objects receiving FHIR data
- [ ] Error handling strategy documented for each pattern in use
- [ ] Conflict resolution design completed if bidirectional sync is selected
- [ ] Authentication and Named Credential configuration documented
- [ ] Risk register reviewed with stakeholders

---

## Notes and Deviations

(Record any deviations from the standard patterns documented in SKILL.md and the reasons for them.)
