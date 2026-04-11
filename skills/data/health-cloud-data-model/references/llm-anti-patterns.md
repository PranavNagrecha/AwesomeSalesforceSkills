# LLM Anti-Patterns — Health Cloud Data Model

Common mistakes AI coding assistants make when generating or advising on Health Cloud Data Model.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending HC24__ Objects for New Integrations

**What the LLM generates:** Code or configuration that writes clinical data to `HC24__EhrEncounter__c`, `HC24__EhrCondition__c`, `HC24__EhrCarePlan__c`, or other `HC24__`-prefixed objects in what is described as a new Health Cloud integration.

**Why it happens:** Older Health Cloud documentation, community blog posts, and Trailhead content from before Spring '23 reference HC24__ objects extensively. LLM training data includes these older sources, which causes the model to default to HC24__ object names when generating clinical data code regardless of the integration date or org provisioning context.

**Correct pattern:**

```apex
// WRONG — targets frozen HC24__ object
HC24__EhrEncounter__c enc = new HC24__EhrEncounter__c();
enc.HC24__Patient__c = patientId;
insert enc;

// CORRECT — targets FHIR R4-aligned standard object
ClinicalEncounter enc = new ClinicalEncounter();
enc.AccountId = patientPersonAccountId;
enc.EhrEncounterId__c = externalEncounterId;  // External ID for upsert
enc.StartTime = startTime;
Database.upsert(enc, ClinicalEncounter.EhrEncounterId__c, false);
```

**Detection hint:** Scan generated code and config for the pattern `HC24__Ehr`. Any occurrence in a write operation (insert, update, upsert, DML) targeting a post-Spring '23 context is a flag.

---

## Anti-Pattern 2: Assuming Clinical Objects Are Available Without Confirming the Org Preference

**What the LLM generates:** Apex classes, SOQL queries, or Flow configurations that reference `ClinicalEncounter`, `HealthCondition`, `AllergyIntolerance`, or other FHIR R4-aligned standard objects without noting that the FHIR-Aligned Clinical Data Model org preference must be enabled first.

**Why it happens:** LLMs treat Salesforce standard object names as universally available once the correct license is present. The concept of an org-level schema preference that must be manually toggled before objects exist in the schema is not a common pattern in other Salesforce clouds, so the model does not apply it by default to Health Cloud.

**Correct pattern:**

```
Before referencing ClinicalEncounter, HealthCondition, CarePlan, AllergyIntolerance,
PatientImmunization, MedicationRequest, or ClinicalProcedure in any code or config:

1. Confirm: Setup > FHIR R4 Support Settings > "FHIR-Aligned Clinical Data Model" is ON
2. Verify: Run SELECT Id FROM ClinicalEncounter LIMIT 1 in Developer Console
3. If the query fails with "sObject not supported" — the preference is disabled
```

**Detection hint:** Any response that references FHIR R4-aligned clinical objects without mentioning the org preference setup step is missing a critical prerequisite.

---

## Anti-Pattern 3: Missing the Experience Cloud FHIR R4 Permission Set for Patient Portal Users

**What the LLM generates:** A Health Cloud patient portal implementation plan that assigns only the standard Health Cloud community user license and base Health Cloud permission sets to Experience Cloud users, without mentioning the "FHIR R4 for Experience Cloud" permission set.

**Why it happens:** Most Salesforce clouds have a single permission layer for community users. Health Cloud's FHIR R4 clinical objects have an additional permission set specifically for Experience Cloud access that does not appear in the standard Health Cloud permission set documentation alongside the base license. The LLM does not surface this second gate unless explicitly asked about Experience Cloud clinical data access.

**Correct pattern:**

```
Experience Cloud patient portal user permission configuration:
1. Health Cloud license (community)
2. Health Cloud for Experience Cloud permission set (standard HC access)
3. FHIR R4 for Experience Cloud permission set (REQUIRED for clinical object access)

Assign all three. Missing #3 causes patients to see empty clinical data components
even when the org preference is active and records exist.
```

**Detection hint:** Any portal or community implementation plan that lists Health Cloud permissions without explicitly mentioning "FHIR R4 for Experience Cloud" should be flagged as potentially incomplete.

---

## Anti-Pattern 4: Conflating HC24__ and Standard Object API Names in Queries and Code

**What the LLM generates:** Mixed code that queries `HC24__EhrCondition__c` for historical data and `HealthCondition` for new data but treats them as containing the same records, or code that assumes a relationship field like `HC24__Patient__c` maps directly to `AccountId` without transformation.

**Why it happens:** LLMs understand that the two layers exist and may attempt to write "compatibility" code that reads from both, but fail to account for the fact that the two layers have entirely different field API names, relationship structures, and data types. A field named `HC24__OnsetDate__c` on `HC24__EhrCondition__c` has no automatic relationship to `OnsetDate` on `HealthCondition` — they must be mapped explicitly.

**Correct pattern:**

```
The two layers are separate storage tables with different field API names.
Treat any migration from HC24__ to standard objects as a full ETL operation:

HC24__EhrCondition__c.HC24__Patient__c    → HealthCondition.AccountId
HC24__EhrCondition__c.HC24__Code__c       → HealthCondition.Code (CodeableConcept)
HC24__EhrCondition__c.HC24__OnsetDate__c  → HealthCondition.OnsetDate
HC24__EhrCondition__c.HC24__Status__c     → HealthCondition.ClinicalStatus

Each field must be explicitly extracted, transformed, and loaded.
```

**Detection hint:** Look for code that uses both `HC24__Ehr*` and standard FHIR object names in the same DML or SOQL statement without an explicit mapping step. Also flag code that assigns HC24__ record IDs directly to standard object lookup fields.

---

## Anti-Pattern 5: Treating the Two Data Layers as Synchronized or Live-Mirrored

**What the LLM generates:** Implementation guidance or code comments stating that "existing HC24__ records will be visible through the standard clinical objects once the org preference is enabled" or that enabling the preference "migrates" existing data to the new model.

**Why it happens:** The LLM draws an analogy to other Salesforce feature toggles that activate views or representations of existing data. The HC24__-to-standard-object transition is categorically different: it is a separate schema with no live synchronization. Enabling the org preference activates new empty objects; it does not populate them from HC24__ data.

**Correct pattern:**

```
Enabling the FHIR-Aligned Clinical Data Model org preference:
- Creates the standard object schema (ClinicalEncounter, HealthCondition, etc.)
- Does NOT migrate or sync existing HC24__ records to standard objects
- Does NOT create any link between HC24__ data and standard object data

To access existing HC24__ data after enabling the preference:
- Query HC24__ objects directly (read access still works)
- Perform an explicit ETL migration to load HC24__ records into standard objects
- During the migration window, queries against both layers are necessary for completeness
```

**Detection hint:** Any statement claiming that enabling the org preference "migrates," "upgrades," or "converts" existing HC24__ data to standard objects is incorrect and should be flagged.

---

## Anti-Pattern 6: Hardcoding Salesforce Record IDs as Cross-System Keys for Clinical Objects

**What the LLM generates:** Integration code that stores the Salesforce `ClinicalEncounter.Id` (18-character Salesforce record ID) in the EHR system as the cross-system reference key, with no External ID field on the Salesforce side.

**Why it happens:** Using the Salesforce record ID as the primary key is common in simpler integrations and the LLM defaults to it. For clinical data with high resync and correction frequencies, this creates a fragile pattern where records cannot be idempotently upserted.

**Correct pattern:**

```apex
// Create an External ID field on ClinicalEncounter: EhrEncounterId__c (External ID, Unique)
// Use upsert with the external ID as the key

ClinicalEncounter enc = new ClinicalEncounter();
enc.EhrEncounterId__c = epicEncounterId;  // EHR-native ID as the stable key
enc.AccountId = patientAccountId;
enc.StartTime = startDateTime;

Database.upsert(enc, ClinicalEncounter.EhrEncounterId__c, false);
// Subsequent calls with the same epicEncounterId update, not create new records
```

**Detection hint:** Integration code that does not reference an External ID field for clinical object upserts, or that stores Salesforce record IDs in external EHR systems as the primary cross-system reference.
