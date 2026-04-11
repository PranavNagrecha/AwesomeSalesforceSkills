# Well-Architected Notes — FHIR Data Mapping

## Relevant Pillars

- **Security** — FHIR resources contain protected health information (PHI). All data in transit must use TLS 1.2+. Field-level security on clinical SObjects (HealthCondition, CareObservation, PersonName) must be configured to restrict PHI access to authorized profiles and permission sets. Encryption at rest via Salesforce Shield should be evaluated for clinical objects. Audit trail requirements under HIPAA apply to any create/update/delete operation on patient data.
- **Reliability** — FHIR data loads must be idempotent. Middleware should use upsert with external Id fields (e.g., FHIR resource Id stored as an external Id) so that re-runs after partial failures do not create duplicate records. The staged load sequence (CodeSet before CodeSetBundle, Account before child records) must be enforced in every run, not just initial load, to maintain FK integrity.
- **Operational Excellence** — Clinical data migrations require audit trails beyond standard Salesforce logs. The CodeableConcept truncation log (codings discarded due to the 15-limit) and the Condition quarantine list (code-less resources) must be produced as structured artifacts for clinical stakeholder sign-off. Migration runbooks must include the FHIR R4 Support Settings prerequisite check as step zero. Post-load validation queries should be codified and re-run after every batch to confirm record counts and FK integrity.

## Architectural Tradeoffs

**Fidelity vs. Simplicity:** The FHIR-aligned model in Health Cloud is more structurally complex than a flat patient record (Person Account + 3 child record types vs. a single Account). This complexity exists to support multiple names, phones, and addresses per patient — a clinical requirement that the standard Salesforce person model does not accommodate. Teams tempted to "simplify" by writing to Account fields directly sacrifice clinical API compatibility for short-term development speed.

**Pre-load normalization vs. runtime handling:** Truncating CodeableConcept codings in middleware before load (the recommended approach) is more predictable and auditable than allowing Health Cloud to reject records at DML time and handling errors post-hoc. The tradeoff is that middleware must carry more transformation logic. Given the clinical governance requirement to audit discarded codings, pre-load normalization is the only defensible choice.

**careTeam as Case Teams vs. custom model:** Using Salesforce Case Teams for careTeam implementation ties clinical team membership to the Case record lifecycle. If the use case requires team membership independent of a specific case, Case Teams may not be the right model. In that scenario, the team should evaluate Health Cloud's Care Team feature (separate from Case Teams) and document the choice explicitly — the default platform implementation is Case Teams, but it is not the only option for all care coordination scenarios.

## Anti-Patterns

1. **Writing FHIR demographics to standard Account/Contact fields** — This bypasses the clinical data model and makes patient records invisible to Health Cloud clinical APIs, timeline views, and downstream analytics. The correct target objects are PersonName, ContactPointPhone, and ContactPointAddress as child records of the Person Account. Teams that take this shortcut typically discover the problem only after Health Cloud features fail to surface patient data.

2. **Omitting the FHIR R4 Support Settings activation step from migration runbooks** — When this step is omitted, the migration proceeds against a schema that lacks the required clinical objects. Errors appear as "entity not found" rather than configuration issues, leading to misdiagnosis and wasted debugging time. Every migration runbook must include an explicit prerequisite check for this org preference before any schema or data operations.

3. **Assuming FHIR cardinality rules apply unchanged in Health Cloud** — Health Cloud imposes stricter cardinality on certain fields than the FHIR R4 spec (condition.code is the primary example: optional in FHIR, required in HC). Middleware that faithfully passes through spec-compliant but code-less Condition resources will generate DML failures. All FHIR-to-HC field mappings must be audited against Health Cloud object metadata, not just the FHIR spec.

## Official Sources Used

- Life Sciences Cloud Developer Guide — Mapping FHIR Resources to Salesforce Objects: https://developer.salesforce.com/docs/atlas.en-us.health_cloud_object_reference.meta/health_cloud_object_reference/fhir_mapping_overview.htm
- FHIR R4 Support Settings Setup Guide: https://help.salesforce.com/s/articleView?id=sf.fhir_r4_support_settings.htm&type=5
- Health Cloud Object Reference — HealthCondition: https://developer.salesforce.com/docs/atlas.en-us.health_cloud_object_reference.meta/health_cloud_object_reference/sforce_api_objects_healthcondition.htm
- Health Cloud Object Reference — CareObservation: https://developer.salesforce.com/docs/atlas.en-us.health_cloud_object_reference.meta/health_cloud_object_reference/sforce_api_objects_careobservation.htm
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Data Loader Guide — https://help.salesforce.com/s/articleView?id=sf.data_loader.htm&type=5
