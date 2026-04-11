# Well-Architected Notes — Health Cloud Data Model

## Relevant Pillars

- **Reliability** — The dual-layer architecture introduces a reliability risk: teams that write to HC24__ objects in post-Spring '23 orgs will encounter runtime DML failures that are not visible until deployment. Reliability requires proactively confirming which data layer is writable before building integrations, and establishing External ID upsert patterns to prevent duplicate-record proliferation on resync.

- **Security** — Clinical data is subject to HIPAA and related healthcare privacy regulations. Health Cloud standard clinical objects inherit Salesforce's field-level security, record-level sharing, and org-wide defaults. The FHIR R4 for Experience Cloud permission set is a security gate that must be explicitly assigned — it is not granted automatically by community license. Restricting access to clinical objects via permission sets and sharing rules is mandatory, not optional.

- **Operational Excellence** — The org preference state, permission set assignments, and External ID field configuration are not visible in standard deployment checklists. Each of these is a silent failure point. Operational excellence requires encoding these setup steps into deployment runbooks, health check scripts, and post-deployment validation queries so that environment drift is detected early.

## Architectural Tradeoffs

**HC24__ (legacy managed-package layer) vs. FHIR R4-Aligned Standard Objects:**
- HC24__ objects require no org preference toggle and contain historical data in older orgs. However, they are frozen for new writes post-Spring '23 and do not expose FHIR-compliant API names, making bidirectional FHIR integration verbose and brittle.
- Standard objects are the supported forward path, are FHIR R4-aligned by design, and are accessible via the Health Cloud FHIR R4 API surface. The tradeoff is that they require the org preference to be enabled and do not automatically inherit historical data from HC24__.

**Incremental migration vs. big-bang cutover:**
- Incremental migration (parallel-running both layers with a migration window) reduces risk but requires code that queries both layers during the transition. It is the correct approach for orgs with large volumes of HC24__ data.
- Big-bang cutover is simpler to implement but increases the risk of losing access to historical records if the migration fails partway through. Only appropriate for orgs with small HC24__ data volumes or no production data in HC24__.

**Experience Cloud patient portal data access:**
- Serving clinical data through Experience Cloud requires an additional permission set layer. This is architecturally sound as a security gate, but operationally it is easy to miss. Baking this into a persona-based permission set deployment pattern (patient portal persona = Health Cloud community license + FHIR R4 for Experience Cloud permission set) reduces the risk of this being forgotten.

## Anti-Patterns

1. **Writing to HC24__ objects in new integrations** — HC24__ EHR objects are frozen for new writes in post-Spring '23 orgs. Writing to them produces runtime errors and stores data in a layer that is not exposed through the FHIR R4 API surface. All new clinical data writes must target the FHIR R4-aligned standard objects.

2. **Assuming clinical objects are available without checking the org preference** — Apex code and SOQL queries that reference standard clinical objects will fail in orgs where the FHIR-Aligned Clinical Data Model preference is disabled. The correct pattern is to include a schema availability check in the deployment runbook and to verify the org preference state before deploying any code that references standard clinical objects.

3. **Treating HC24__ and standard objects as synchronized or interchangeable** — Data in HC24__ is not mirrored to standard objects. Building reports, Flows, or UI components that assume data in one layer is visible in the other leads to silent data gaps that are difficult to diagnose in production.

## Official Sources Used

- Health Cloud Object Reference — Clinical Data Model: https://developer.salesforce.com/docs/atlas.en-us.health_cloud_developer.meta/health_cloud_developer/
- Health Cloud Data Model Gallery: https://developer.salesforce.com/docs/platform/data-models
- FHIR R4 Support Settings Setup: https://help.salesforce.com/s/articleView?id=ind.hc_fhir_r4_support_settings.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Health Cloud Administration Guide: https://help.salesforce.com/s/articleView?id=ind.hc_admin.htm
