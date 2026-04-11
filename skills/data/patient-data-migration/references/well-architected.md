# Well-Architected Notes — Patient Data Migration

## Relevant Pillars

- **Security** — PHI is the highest-sensitivity data category in a Health Cloud migration. Security controls are non-negotiable and sequenced: BAA must precede any data load, Shield Platform Encryption must be configured before PHI arrives in the org, TLS must be enforced on all pipeline endpoints, and sandboxes must be masked before any PHI testing. A failure in any of these controls is a HIPAA violation with regulatory and contractual consequences.
- **Performance** — Patient panels of 100K–10M records require Bulk API 2.0. REST and SOAP APIs have per-request and per-hour governor limits that make them unusable at migration scale. Within Bulk API 2.0, object load order determines whether jobs succeed or fail; parallelism is only safe within a phase where all dependencies are already satisfied.
- **Reliability** — Migration pipelines must be re-runnable. Upsert with External IDs makes each phase idempotent: re-submitting after a partial failure updates existing records rather than creating duplicates. Gating each phase on the prior phase reaching `JobComplete` with zero failed records prevents cascading failures.
- **Operational Excellence** — The boundary between importable data records and system-generated platform records must be documented in the migration runbook before the project starts. Undocumented scope gaps discovered mid-migration delay go-lives and erode stakeholder trust.

## Architectural Tradeoffs

**External ID upsert vs. Salesforce ID mapping table:** Using an External ID field and Bulk API 2.0 relationship-by-external-ID eliminates the need for a pre-migration ID mapping table. The tradeoff is a one-time cost of deploying External ID fields before migration starts. The alternative (maintaining a mapping table of source ID → Salesforce ID) is environment-specific, brittle across sandbox refreshes, and breaks when records are deleted and re-inserted.

**Full parallel load vs. ordered phase pipeline:** A fully parallel load (all objects at once) is faster in theory but produces guaranteed failures because clinical and care objects have unsatisfied AccountId lookups until Person Accounts are loaded. An ordered phase pipeline is slower but correct. The Bulk API 2.0 job status polling overhead between phases is negligible compared to the cost of resubmitting failed batches.

**Import scope: include engagement history vs. exclude it:** Including platform-generated engagement history in scope sets expectations that cannot be met — there is no DML surface to write these records. The correct tradeoff is to explicitly exclude them from scope, document the gap in the runbook, and set go-live date as the start of the Health Cloud engagement history. This is an expected outcome, not a defect.

## Anti-Patterns

1. **Load-then-encrypt** — Enabling Shield Platform Encryption after PHI is already in the org to avoid blocking the migration timeline. This leaves PHI in unencrypted secondary stores (field history, feed, audit logs) permanently. The correct approach is to block the migration until encryption is confirmed active — the security risk of proceeding is greater than the schedule risk of delaying.

2. **Flat single-phase bulk load** — Treating all Health Cloud clinical and care objects as peers and loading them in one Bulk API 2.0 job or in parallel without dependency gates. Because all clinical and care objects carry required AccountId lookups, a flat load guarantees batch failures for every non-Account record submitted before the Account job completes. The correct approach is a sequenced phase pipeline with explicit gate conditions between phases.

3. **PHI in shared sandboxes without masking** — Using a representative sample of real patient data in development or QA sandboxes to "validate the field mappings." Sandboxes are often outside the HIPAA BAA scope and accessible to personnel not authorized to handle PHI. The correct approach is to use synthetic data (structurally correct, no real identifiers) in all pre-production environments and limit PHI to the production migration window only.

## Official Sources Used

- Salesforce Health Cloud Developer Guide — Clinical Data Model: https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/hc_dev_clinical_data_model.htm
- Salesforce Health Cloud Developer Guide — CarePlan and CarePlanTemplate Objects: https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/hc_dev_care_plan_objects.htm
- Salesforce Help — Supporting Clinical Data in Health Cloud: https://help.salesforce.com/s/articleView?id=ind.hc_clinical_data_support.htm
- Bulk API 2.0 Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Shield Platform Encryption Implementation Guide: https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm&type=5
- Salesforce Data Mask: https://help.salesforce.com/s/articleView?id=sf.data_mask_overview.htm&type=5
- Object Reference — Account (Person Account): https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_account.htm
