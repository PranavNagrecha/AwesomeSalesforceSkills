# Well-Architected Notes — FHIR Integration Architecture

## Relevant Pillars

- **Security** — FHIR integrations transmit Protected Health Information (PHI) across system boundaries. Every integration pattern requires encrypted transport (TLS 1.2+), OAuth 2.0 or SMART on FHIR authentication for external FHIR endpoints, and Named Credentials to keep secrets out of code. The Generic FHIR Client must be configured with appropriate OAuth scopes limited to the minimum data set required. Audit logging for all cross-boundary PHI access must be enabled. For bidirectional sync, write operations back to the EMR carry elevated risk and require explicit authorization controls.

- **Integration** — Pattern selection is the primary integration design decision in FHIR architecture. Mismatched patterns (e.g., using polling batch where event-driven is required) produce systems that meet technical requirements but fail operational SLAs. The transformation layer is the most critical integration component: it must be centralized, versioned, and independently testable. Scatter-gun FHIR parsing across multiple Apex classes or Flow elements is an anti-pattern that collapses under EMR API version changes.

- **Reliability** — Each of the four sync patterns has distinct failure modes. Real-time REST queries (Pattern 1) need circuit breakers to handle EMR downtime without cascading failures into the Health Cloud UI. Event-driven ingestion (Pattern 2) needs dead-letter queues for messages that fail transformation or DML operations. Bulk export jobs (Pattern 3) need checkpoint-and-resume capability for large datasets. Bidirectional sync (Pattern 4) needs conflict detection and rollback logic. Reliability design must be pattern-specific, not generic.

- **Scalability** — Volume profile drives pattern choice as much as latency requirements. Bulk FHIR $export is designed for large-volume extraction but produces NDJSON payloads that must be streamed line-by-line. Event-driven ingestion scales well for individual ADT events but degrades under burst conditions (e.g., mass admission events during an emergency) unless the MuleSoft queue is sized appropriately. Assess the peak-event rate before finalizing pattern selection.

- **Operational Excellence** — FHIR integrations between Health Cloud and external EMRs are operationally complex because failures can span system boundaries. Runbooks for each integration pattern must document: how to detect a failure, how to replay missed events, how to identify records affected by a failed batch, and how to reprocess without creating duplicates. Idempotent upsert by external ID (patient MRN or EMR encounter ID) is the primary mechanism for safe reprocessing.

---

## Architectural Tradeoffs

**Real-Time vs. Persistent Storage:** The Generic FHIR Client (Pattern 1) avoids data duplication and stale copy problems but leaves Health Cloud unable to query, report, or automate on fetched data unless an explicit write step is added. Teams must decide per-data-domain whether freshness or queryability is the primary requirement. Trying to achieve both without a write step is the most common architectural oversight.

**MuleSoft Accelerator vs. Custom Middleware:** MuleSoft Accelerator for Healthcare provides pre-built Epic and Cerner assets that dramatically reduce implementation effort for common FHIR resources. The tradeoff is that Accelerator assets are opinionated — they assume a specific Health Cloud object model and FHIR profile. Orgs with customized Health Cloud data models or non-Epic/Cerner EMRs must fork the Accelerator assets (adding maintenance burden) or build custom DataWeave from scratch. The decision should be documented explicitly; teams that adopt Accelerator assets without reviewing them against their Health Cloud customizations discover mapping mismatches late.

**Bidirectional Sync Complexity:** Pattern 4 (bidirectional sync) provides the richest integration but is an order of magnitude more complex than unidirectional patterns. Conflict resolution, write authorization, and audit trail requirements create design surface area that grows non-linearly. This pattern should only be selected when there is a documented business requirement for write-back to the EMR — not as a default "complete integration" assumption.

---

## Anti-Patterns

1. **Treating Health Cloud as a FHIR Server** — Architects who design external systems to push arbitrary FHIR resources to a Salesforce endpoint as if it were a fully conformant FHIR server will encounter the ~26-resource limit and the absence of a FHIR-native storage mechanism. The correct framing is that Health Cloud is a FHIR-aware CRM that has FHIR ingestion capabilities for a defined set of resource types, not a general-purpose FHIR repository.

2. **Building the Transformation Layer Inside Salesforce** — Some teams implement FHIR-to-object transformation entirely in Apex within Salesforce (e.g., parsing FHIR JSON in a REST inbound endpoint Apex class). This creates a fragile, hard-to-test transformation layer inside a system not designed for middleware logic. Governor limits on CPU time and heap constrain complex bundle processing. The correct approach is to transform before the Salesforce boundary — in MuleSoft, a custom API gateway, or equivalent middleware — and deliver already-mapped data to the Salesforce Composite API.

3. **Single Integration Pattern for All Clinical Data Domains** — Applying one pattern uniformly across all data (e.g., bulk nightly sync for everything including ADT events) fails to meet the SLA requirements of time-sensitive data domains while over-engineering the infrastructure for low-frequency reference data. Pattern selection must be done per data domain, not per integration.

---

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Health Cloud Developer Guide — FHIR APIs — https://developer.salesforce.com/docs/health/health-cloud/references/fhir-r4-apis/fhir-r4-apis-intro.html
- MuleSoft Accelerator for Healthcare Documentation — https://docs.mulesoft.com/healthcare-toolkit/latest/
- Salesforce Health Cloud — Configure the Generic FHIR Client — https://help.salesforce.com/s/articleView?id=sf.admin_generic_fhir_client.htm
