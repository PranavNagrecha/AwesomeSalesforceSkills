# Gotchas — FHIR Integration Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The ~26-Resource Limit is Not Prominently Documented in Marketing Materials

**What happens:** Teams scope an integration assuming Health Cloud can store any FHIR R4 resource — after all, FHIR R4 defines 140+ resource types. In implementation, they discover that Health Cloud's clinical data model maps approximately 26 FHIR R4 resources (Patient, Practitioner, Encounter, Condition, Observation, MedicationRequest, Procedure, AllergyIntolerance, CarePlan, CareTeam, etc.). Resources outside the supported set (e.g., `ServiceRequest`, `Appointment` in certain configurations, many R4 profile extensions) have no target Health Cloud object. Data for those resources either gets dropped silently or requires custom extension objects that are not part of the FHIR ingestion pipeline.

**When it occurs:** Discovered during implementation sprint 1 when the team begins writing DataWeave mappings and finds the target Health Cloud object does not exist for a FHIR resource type that was in scope. Most damaging when the out-of-scope resource type is central to the use case (e.g., `ImagingStudy` for a radiology workflow).

**How to avoid:** Before finalizing integration scope, audit every FHIR resource type in the EMR's data exchange against the Health Cloud Developer Guide's FHIR R4 API Reference — which lists the supported resources explicitly. For any resource not in the supported set, make an explicit design decision at architecture time: (a) exclude it from scope, (b) build a custom extension object and custom transformation, or (c) store it as a reference-only external record without structural mapping.

---

## Gotcha 2: Generic FHIR Client Results Are Not Automatically Persisted

**What happens:** Architects configure the Generic FHIR Client to fetch live data from an external FHIR endpoint and assume the results are cached or stored somewhere accessible to Flows, reports, or triggers. They design downstream automations (e.g., a Flow that fires when a new Observation record is created) that depend on this data being in Salesforce objects. The automations never fire because no records are created — the Generic FHIR Client returns data to the calling component only; it does not write to Health Cloud objects.

**When it occurs:** When the Generic FHIR Client is used for real-time data display (correct use case) but the architecture also requires that data to be queryable via SOQL, visible in list views, or accessible to batch Apex. The gap is not obvious in early prototyping because the LWC works fine — the data appears on screen. The failure surfaces when the reporting team queries the objects and finds no data.

**How to avoid:** Treat the Generic FHIR Client as a display/read-only fetch mechanism. If any retrieved data must persist in Salesforce (for reporting, audit, downstream logic), design an explicit write step in the LWC controller or Apex that takes the returned FHIR payload, transforms it, and upserts the relevant fields to Health Cloud objects after the display operation. This is a separate architectural step, not automatic behavior.

---

## Gotcha 3: HL7 v2 Feeds from EMRs Cannot Be Ingested Directly — No Native Salesforce Parser Exists

**What happens:** A project team discovers the hospital's EMR sends ADT and lab result notifications via HL7 v2 MLLP feeds, not FHIR R4 REST. They attempt to receive these messages by standing up an Apex REST endpoint or a Platform Event listener and parsing the raw HL7 pipe-delimited segments (`MSH|^~\&|...`) in Apex or a Flow. Salesforce has no native HL7 v2 parser, so the team must write a custom parser that is fragile, hard to test, and must handle every segment variant the EMR can produce.

**When it occurs:** Common in community hospitals and regional health systems that have not yet modernized their EMR integration layer. Even Epic and Cerner — which support FHIR R4 — continue to emit HL7 v2 for lab (ORU^R01) and ADT (ADT^A01 through ADT^A11) events in most on-premise configurations.

**How to avoid:** Route all HL7 v2 feeds through MuleSoft Accelerator for Healthcare (or equivalent middleware with HL7 v2 support) before they reach Salesforce. MuleSoft Accelerator includes pre-built HL7 v2 listener assets and DataWeave conversion scripts that produce FHIR R4 resources. The converted FHIR payload then enters the standard Health Cloud ingestion pipeline. Never attempt to parse raw HL7 v2 within Salesforce.

---

## Gotcha 4: Bidirectional Sync Conflict Resolution Has No Platform-Provided Default

**What happens:** A bidirectional EMR sync is designed where Health Cloud care plans flow back to the EMR and EMR clinical data flows into Health Cloud. Teams assume Salesforce will handle "last write wins" or provide a built-in conflict detection mechanism. There is no such mechanism. When a care coordinator updates a care plan in Health Cloud at the same time a clinician updates the same record in the EMR, whichever MuleSoft job runs next overwrites the other's changes silently.

**When it occurs:** In any bidirectional sync architecture where both systems can modify the same logical record and the sync job runs on a schedule (common in Pattern 4). The failure is intermittent and hard to reproduce, which makes it dangerous — data loss happens quietly.

**How to avoid:** Design explicit conflict resolution rules before implementation. Common strategies include: (a) field-level ownership — designate each field as "owned by EMR" or "owned by Health Cloud" and only allow the owning system to write that field; (b) timestamp-based last-write-wins with audit logging; (c) conflict flagging — surface conflicts as tasks for human review instead of auto-resolving. Document the chosen strategy in the ADR and implement it in the MuleSoft transformation layer, not as an afterthought in Apex.

---

## Gotcha 5: Bulk FHIR $export Payloads Are NDJSON — Standard JSON Parsers Will Fail

**What happens:** The FHIR `$export` operation returns data as NDJSON (Newline Delimited JSON) files — one JSON object per line, no array wrapper. Teams that have worked with standard REST APIs expect a JSON array response or a standard JSON Bundle. When they attempt to parse the export file using standard JSON parsers (e.g., Apex's `JSON.deserialize`, standard MuleSoft JSON Reader), parsing fails because NDJSON is not valid standard JSON.

**When it occurs:** During bulk data migration or nightly reconciliation implementations that use the FHIR `$export` operation (Pattern 3). The error appears as a JSON parse exception on the first attempt to process the export file, often during an after-hours batch job.

**How to avoid:** Ensure the MuleSoft (or custom) processing pipeline uses an NDJSON-aware reader. MuleSoft supports NDJSON as a distinct format separate from JSON. Process each line independently rather than attempting to parse the file as a single JSON document. Implement line-by-line streaming for large exports to avoid memory pressure on files that can exceed hundreds of megabytes for large patient populations.
