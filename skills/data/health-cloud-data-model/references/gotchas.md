# Gotchas — Health Cloud Data Model

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: HC24__ Objects Are Frozen for New Writes Post-Spring '23 — With No Deprecation Warning

**What happens:** Insert and update DML operations targeting HC24__ EHR objects (such as `HC24__EhrEncounter__c`, `HC24__EhrCondition__c`, `HC24__EhrCarePlan__c`, `HC24__EhrMedication__c`) fail with a generic DML error in orgs provisioned after Spring '23. The error does not reference the freeze policy by name. Salesforce froze these objects where standard FHIR R4-aligned counterparts exist, but the error message is not self-explanatory.

**When it occurs:** Any Apex, Flow, Data Loader, or integration that attempts to insert or update a HC24__ object whose function is covered by a standard clinical object (ClinicalEncounter, HealthCondition, CarePlan, etc.) in an org provisioned on Spring '23 release or later. Read operations against HC24__ still succeed — the freeze affects writes only.

**How to avoid:** Before writing any code that references HC24__ objects, confirm the org provisioning date. For any org on Spring '23 or later, redirect all writes to the corresponding FHIR R4-aligned standard object. Use the object mapping table in SKILL.md. When in doubt, test a single insert in a sandbox and inspect the debug log for the DML exception type.

---

## Gotcha 2: Standard Clinical Objects Do Not Exist Until the Org Preference Is Enabled

**What happens:** `ClinicalEncounter`, `HealthCondition`, `AllergyIntolerance`, `PatientImmunization`, `CarePlan`, and related FHIR R4-aligned objects are completely absent from the org schema until the "FHIR-Aligned Clinical Data Model" org preference is activated. SOQL queries return "sObject type not supported" errors. Apex classes referencing these objects fail to compile. Object Manager does not show them. This is frequently misdiagnosed as a license or permissions issue and teams spend hours troubleshooting the wrong layer.

**When it occurs:** Any new Health Cloud org where the preference has not been explicitly enabled, or any sandbox refreshed from a production org where the preference was disabled. The preference is not enabled by default.

**How to avoid:** Make enabling the org preference the first step in any Health Cloud clinical-data implementation checklist. Add a setup validation step that runs a test SOQL query against `ClinicalEncounter LIMIT 1` — a successful response (even with zero rows) confirms the schema is active. Include this check in deployment runbooks for all environments (dev sandbox, UAT, staging, production).

---

## Gotcha 3: Experience Cloud Users Need a Separate FHIR R4 Permission Set

**What happens:** Experience Cloud (community) users — such as patients accessing a health portal — cannot read or write standard clinical objects even when the org preference is enabled and they hold a Health Cloud community license. The "FHIR R4 for Experience Cloud" permission set is a distinct gate from the base Health Cloud permissions. Without it, patients receive access-denied errors or see empty data in portal components that render CarePlan or HealthCondition records.

**When it occurs:** Patient portal implementations where Experience Cloud users are expected to view their own care plans, conditions, or allergy records. Also affects any community-based care coordination scenario where a care team external user needs to access clinical data through a community org.

**How to avoid:** When building any Experience Cloud patient portal on Health Cloud, explicitly add "FHIR R4 for Experience Cloud" to the permission set configuration checklist. Assign it to the relevant community user profiles or directly to users during setup. Validate by logging in as a test community user and confirming that clinical record components render data correctly before going live.

---

## Gotcha 4: The Two Data Layers Are Not Synchronized — Data Written to HC24__ Is Not Visible in Standard Objects

**What happens:** Some orgs have historical clinical data in HC24__ objects from before the Spring '23 freeze. When teams enable the FHIR-Aligned Clinical Data Model org preference and begin using standard objects, they discover that existing HC24__ records do not automatically appear in ClinicalEncounter, HealthCondition, or other standard objects. The two layers are entirely separate storage tables. There is no automatic migration or live synchronization between them.

**When it occurs:** Any org that has existing HC24__ data and transitions to the standard-object layer without performing an explicit data migration. Care coordinators and clinicians using new UI components built on standard objects will not see historical records stored in HC24__ objects.

**How to avoid:** Perform an explicit data migration from HC24__ objects to their standard-object counterparts before retiring the HC24__ layer in any user-facing workflow. Use Bulk API 2.0 for high-volume extracts. Document which historical records have been migrated and which remain only in HC24__ during the transition period. Consider a read-through pattern in Apex that queries both layers during the migration window.

---

## Gotcha 5: External ID Fields Must Be Explicitly Created — They Are Not Included by Default

**What happens:** The standard clinical objects (ClinicalEncounter, HealthCondition, etc.) do not include a built-in External ID field for storing the originating EHR system's native identifier. If integrations use the Salesforce record ID as the cross-system key, re-ingesting the same records from the EHR creates duplicates rather than updating existing records.

**When it occurs:** FHIR R4 integrations that replay encounter or condition data from the EHR (e.g., after a data correction or resync). Bulk imports that do not have a stable upsert key. Any integration that cannot guarantee that each EHR record will be submitted exactly once.

**How to avoid:** Add a custom External ID field to each standard clinical object that the integration writes to (e.g., `EhrEncounterId__c` on ClinicalEncounter). Mark it as an External ID and unique in the field definition. Use `Database.upsert()` with this field as the upsert key, or use the REST Composite API's upsert endpoint. Include External ID field creation in the initial org setup checklist for every Health Cloud clinical integration.
