# LLM Anti-Patterns — Health Cloud LWC Components

Common mistakes AI coding assistants make when generating or advising on Health Cloud LWC components.

## Anti-Pattern 1: Extending Patient Card via Lightning App Builder Slot Injection

**What the LLM generates:** Instructions to add a child LWC component inside the Patient Card area using Lightning App Builder, treating the Patient Card like a standard Lightning component that supports slot composition.

**Why it happens:** Standard Lightning web components support slot injection and child component composition via App Builder. LLMs apply this standard pattern to the Health Cloud Patient Card without knowing it does not support this extension mechanism.

**Correct pattern:**
Patient Card field additions must go through Health Cloud Setup > Patient Card Configuration. This is the only supported way to add data to the Patient Card. For completely custom displays alongside (not within) the patient card, add a separate LWC component to a different region of the patient Lightning page.

**Detection hint:** If instructions say "drag a component into the Patient Card" or "add a slot to the healthCloudUtility:patientCard," the Patient Card extension mechanism is being misapplied.

---

## Anti-Pattern 2: Storing Clinical Summary Data in Custom Account Fields

**What the LLM generates:** Apex triggers or Flow automation that populates custom Account fields (e.g., `ActiveConditionCount__c`, `LatestLabResult__c`) for display in Health Cloud clinical components.

**Why it happens:** Denormalized summary fields on Account are a common CRM pattern for performance optimization. LLMs apply this pattern to Health Cloud without knowing that clinical UI components query clinical standard objects, not Account fields.

**Correct pattern:**
Clinical data must live on clinical standard objects (HealthCondition, PatientMedication, etc.) with Account lookups. Custom LWCs that need clinical summaries should query clinical objects via Apex controllers. Account fields are invisible to PatientCard, Timeline, and other Health Cloud clinical components.

**Detection hint:** If the solution creates custom fields on Account/Contact for clinical data that should be displayed in Health Cloud clinical components, the data model is incorrect.

---

## Anti-Pattern 3: Configuring Legacy Timeline Instead of Industries Timeline

**What the LLM generates:** Timeline configuration steps that reference legacy HC managed-package timeline setup rather than TimelineObjectDefinition metadata (API v55.0+).

**Why it happens:** The legacy HC package timeline was the primary timeline configuration mechanism before the Industries Timeline was introduced. LLMs trained on pre-v55.0 documentation recommend legacy configuration steps.

**Correct pattern:**
New timeline configuration should use the Industries Timeline and TimelineObjectDefinition metadata. The legacy HC package timeline is deprecated. For new timeline entries, create TimelineObjectDefinition records in Setup. Plan migration from the legacy timeline component to the Industries Timeline.

**Detection hint:** If the timeline configuration steps reference HC managed-package custom metadata types or HC package setup pages rather than TimelineObjectDefinition, legacy configuration is being applied.

---

## Anti-Pattern 4: Using Wire Service for Filtered Clinical Object Queries

**What the LLM generates:** LWC components that use the standard `@wire(getRecord)` adapter or `@wire(getRelatedListRecords)` to query Health Cloud clinical objects with patient-specific filters.

**Why it happens:** Wire adapters are the preferred LWC data fetching mechanism for standard Salesforce records. LLMs recommend them without knowing that filtered queries on clinical objects (e.g., `WHERE PatientId = :accountId`) require Apex controllers.

**Correct pattern:**
Use Apex controllers with `@AuraEnabled(cacheable=true)` for Health Cloud clinical data queries that require filtering by patient Account ID. The standard wire adapters do not support arbitrary WHERE clauses needed for patient-scoped clinical queries.

**Detection hint:** If the component uses `@wire(getRelatedListRecords)` or `@wire(getRecord)` to query clinical objects filtered by patient ID, the data fetching pattern may not work as expected.

---

## Anti-Pattern 5: Skipping FLS Enforcement in Clinical Data Apex Controllers

**What the LLM generates:** Apex controller code that queries clinical objects (HealthCondition, PatientMedication, etc.) and returns results to LWC components without enforcing field-level security.

**Why it happens:** Many Apex LWC tutorials omit FLS enforcement. LLMs often generate Apex controllers without FLS checks, especially when the focus is on getting the data query correct rather than security.

**Correct pattern:**
All Apex controllers that return PHI to LWC components must enforce FLS. Use `WITH SECURITY_ENFORCED` on SOQL queries, or use the `Schema.SObjectType.HealthCondition.isAccessible()` pattern for FLS validation before querying. Clinical data is PHI — HIPAA minimum necessary access must be enforced at the code level.

**Detection hint:** If the Apex controller queries clinical objects (HealthCondition, PatientMedication, ClinicalEncounter) in a SOQL statement without `WITH SECURITY_ENFORCED` or explicit FLS checks, security enforcement is missing.
