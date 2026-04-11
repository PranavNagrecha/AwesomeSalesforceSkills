# LLM Anti-Patterns — FHIR Integration Architecture

Common mistakes AI coding assistants make when generating or advising on FHIR Integration Architecture.
These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Recommending Health Cloud as a Fully Conformant FHIR Server

**What the LLM generates:** Architecture diagrams or prose that describe external systems "sending FHIR resources to Salesforce Health Cloud's FHIR endpoint" as if Health Cloud implements the full FHIR R4 specification — accepting any resource type, supporting FHIR search parameters, and returning conformant CapabilityStatements.

**Why it happens:** LLMs trained on general FHIR documentation conflate FHIR R4 specification conformance with Salesforce's partial FHIR implementation. Salesforce marketing language ("FHIR R4 support") reinforces the assumption.

**Correct pattern:**

```
Health Cloud supports approximately 26 FHIR R4 resource types mapped to its
clinical data model. It is not a fully conformant FHIR server. External systems
cannot push arbitrary FHIR resources to Health Cloud. Inbound FHIR data must be
transformed to Health Cloud object field values before storage. Unsupported
resource types require custom extension objects or out-of-scope handling.
```

**Detection hint:** Look for phrases like "push FHIR bundles directly to Health Cloud," "Health Cloud FHIR endpoint accepts any resource," or "FHIR-compliant storage in Salesforce." These indicate the anti-pattern.

---

## Anti-Pattern 2: Proposing to Parse Raw HL7 v2 in Apex

**What the LLM generates:** Apex code that accepts an HL7 v2 pipe-delimited message body (e.g., `MSH|^~\&|EPIC|...`) as a REST endpoint input parameter and parses it using `String.split('|')` or custom segment-parsing logic within Salesforce.

**Why it happens:** LLMs know HL7 v2 is text-based and that Apex can manipulate strings, so they extrapolate that "you can parse HL7 in Apex." They are not aware that Salesforce has no native HL7 v2 library and that this creates a fragile, unmaintainable, and performance-limited pattern.

**Correct pattern:**

```
HL7 v2 feeds must be converted to FHIR R4 before entering Salesforce.
Use MuleSoft Accelerator for Healthcare (which provides HL7 v2 listener
and DataWeave conversion assets) or equivalent middleware. The FHIR R4
output of the conversion then follows the standard Health Cloud ingestion
pipeline. Never parse raw HL7 v2 segments inside Salesforce Apex.
```

**Detection hint:** Look for Apex code containing `split('|')`, `split('^')`, segment names like `MSH`, `PID`, `OBR`, or `OBX`, or Apex classes named `HL7Parser`, `HL7Handler`, or similar.

---

## Anti-Pattern 3: Storing Raw FHIR JSON in Long Text Area Fields

**What the LLM generates:** A design where FHIR Bundle responses from an EMR are serialized to a JSON string and stored in a `FHIR_Payload__c` Long Text Area field on a Health Cloud record for "later processing."

**Why it happens:** LLMs recognize that building a full transformation layer is complex and may suggest deferring it. They correctly identify that Long Text Area fields can hold JSON strings. They do not account for the downstream consequences of this design for reporting, automation, and maintainability.

**Correct pattern:**

```
Never store raw FHIR payloads as the primary data store in Salesforce.
Design the transformation layer before implementation. Transform FHIR
resources to Health Cloud object fields at ingestion time. If the raw
payload must be retained for audit, store it in a separate archival
object (not the primary clinical record) with a relationship to the
structured data. Long Text Area blobs break SOQL, Flows, reports,
list views, and all Health Cloud clinical data model functionality.
```

**Detection hint:** Look for field definitions like `FHIR_Payload__c` of type Long Text Area, JSON.serialize() calls storing FHIR data to object fields, or comments like "parse this later when needed."

---

## Anti-Pattern 4: Recommending Scheduled Apex to Poll EMR FHIR Endpoints for Real-Time Events

**What the LLM generates:** A Scheduled Apex class that runs every 5 minutes, queries the EMR's FHIR Encounter or Observation endpoint for records updated in the last 5 minutes, and writes results to Health Cloud. Presented as the "real-time integration" solution.

**Why it happens:** LLMs are familiar with Scheduled Apex as Salesforce's built-in scheduling mechanism. They may not be aware of event-driven alternatives in the MuleSoft Accelerator or the Salesforce Platform Events pattern. Polling is the default pattern in many training examples.

**Correct pattern:**

```
Scheduled Apex polling is not real-time and does not meet sub-minute
latency requirements. Scheduled Apex queues under load can delay execution
by 15+ minutes. For event-driven clinical use cases (ADT events, lab results),
use MuleSoft to receive EMR-pushed events (HL7 v2 via MLLP or FHIR Subscription
webhooks) and write to Salesforce via REST API in near-real-time. Reserve
Scheduled Apex or batch jobs for true bulk reconciliation scenarios (Pattern 3)
where 15-60 minute latency is acceptable.
```

**Detection hint:** Look for Scheduled Apex classes that make HTTP callouts to FHIR endpoints, use `System.schedule()` with intervals under 60 minutes for clinical event use cases, or contain query parameters like `_lastUpdated=gt{timestamp}` inside a scheduled context.

---

## Anti-Pattern 5: Omitting Conflict Resolution Design for Bidirectional Sync

**What the LLM generates:** A bidirectional sync architecture diagram or implementation plan that shows data flowing in both directions between the EMR and Health Cloud without any mention of conflict resolution, field ownership rules, or what happens when the same logical record is updated in both systems between sync runs.

**Why it happens:** LLMs generate architectures based on the happy path. Conflict scenarios are edge cases that require domain-specific knowledge about healthcare data governance. LLMs default to "last write wins" implicitly, without calling it out as a design choice or documenting its risks.

**Correct pattern:**

```
Every bidirectional sync architecture must include an explicit conflict
resolution strategy documented before implementation:
- Field-level ownership: define which system owns each field. Only the
  owning system's value is written to the non-owning system.
- Timestamp-based last-write-wins with mandatory audit logging of
  overwritten values.
- Conflict flagging: surface concurrent updates as Tasks for human
  review rather than auto-resolving silently.

The chosen strategy must be implemented in the middleware transformation
layer (MuleSoft DataWeave), not as an afterthought in Apex. Document it
in the ADR before any code is written.
```

**Detection hint:** Look for bidirectional sync descriptions or diagrams that do not contain the words "conflict," "ownership," "field ownership," "last write wins," or "concurrent update." If a bidirectional architecture is described without any of these terms, the conflict resolution design is missing.

---

## Anti-Pattern 6: Assuming the Generic FHIR Client Persists Data Automatically

**What the LLM generates:** A design that uses the Generic FHIR Client to fetch patient data from an external FHIR server and then immediately references that data in a Flow, Apex trigger, or report — as if the fetch operation created Salesforce records that can be queried via SOQL.

**Why it happens:** LLMs may conflate the Generic FHIR Client with an ingestion mechanism. The name "client" implies a read/write capability, and LLMs infer that successful data retrieval means data persistence.

**Correct pattern:**

```
The Generic FHIR Client is a display/fetch mechanism only. It returns
data to the calling component (LWC or Apex) at runtime but does not
write to any Salesforce object automatically. If retrieved FHIR data
must be accessible via SOQL, displayed in list views, used in reports,
or trigger Flows/Apex, an explicit write step must be designed and
implemented. This write step transforms the returned FHIR payload and
upserts to Health Cloud objects — it is separate from the fetch operation
and must be architecturally accounted for.
```

**Detection hint:** Look for designs where the Generic FHIR Client is used but downstream logic assumes SOQL-queryable records exist, or where Flows reference object fields that would only be populated if data was persisted (but no explicit write step is shown).
