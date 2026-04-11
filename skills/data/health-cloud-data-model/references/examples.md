# Examples — Health Cloud Data Model

## Example 1: Choosing Between Legacy HC24__ and FHIR R4-Aligned Objects for a New Integration

**Context:** A health system is building a new bidirectional integration between Salesforce Health Cloud and an Epic EHR system. The integration will push patient encounters, conditions, and care plans from Epic into Health Cloud when patients are admitted or discharged. The org was provisioned in Summer '23.

**Problem:** The integration architect initially plans to write records to `HC24__EhrEncounter__c` and `HC24__EhrCondition__c` because these appear in published Health Cloud documentation and older code examples. After deploying to a sandbox, all insert operations fail with a DML error.

**Solution:**

Since the org was provisioned after Spring '23, HC24__ EHR objects are frozen for new writes where standard counterparts exist. The correct approach is to write to the FHIR R4-aligned standard objects instead.

Step 1: Enable the org preference (if not already active):
```
Setup > FHIR R4 Support Settings > Enable "FHIR-Aligned Clinical Data Model"
```

Step 2: Map Epic FHIR R4 resources to Salesforce standard objects:
```
Epic Encounter     → ClinicalEncounter
Epic Condition     → HealthCondition
Epic CarePlan      → CarePlan
Epic AllergyIntol. → AllergyIntolerance
```

Step 3: Use Apex Data Loader or Integration API to upsert via an External ID field:
```apex
// Example: Upsert a ClinicalEncounter from an Epic FHIR Encounter payload
ClinicalEncounter enc = new ClinicalEncounter();
enc.AccountId = patientPersonAccountId;
enc.EhrExternalId__c = fhirEncounterId;    // External ID for idempotent upsert
enc.StartTime = encounterStartDateTime;
enc.EndTime = encounterEndDateTime;
enc.Status = 'finished';

Database.upsert(enc, ClinicalEncounter.EhrExternalId__c, false);
```

**Why it works:** Standard objects are not frozen and are the supported target for new clinical data. Upsert on External ID ensures that re-running the integration from Epic does not create duplicate records in Salesforce.

---

## Example 2: Enabling the FHIR-Aligned Clinical Data Model Org Preference and Verifying Object Availability

**Context:** A developer joins a Health Cloud implementation mid-project and attempts to write SOQL queries against `ClinicalEncounter` and `HealthCondition` in the Developer Console. Both queries return "sObject type 'ClinicalEncounter' is not supported" errors.

**Problem:** The developer assumes this is a permissions issue and spends time reviewing user profiles and permission sets. The root cause is that the FHIR-Aligned Clinical Data Model org preference is disabled — the objects do not exist in the schema at all.

**Solution:**

Step 1: Check the org preference status:
```
Setup > Quick Find: "FHIR R4 Support Settings"
Verify: "FHIR-Aligned Clinical Data Model" toggle is ON
If OFF: enable the toggle and save
```

Step 2: Verify object availability after enabling:
```sql
-- Run in Developer Console Query Editor
SELECT Id, AccountId, StartTime, Status
FROM ClinicalEncounter
LIMIT 1
```

If the query executes (even returning 0 rows), the schema is active and objects are available.

Step 3: If Experience Cloud users also need access, assign the permission set:
```
Setup > Permission Sets > "FHIR R4 for Experience Cloud"
Manage Assignments > Add the affected community user profiles or individual users
```

Step 4: Confirm object visibility in Object Manager:
```
Setup > Object Manager > Search "Clinical" — ClinicalEncounter, ClinicalProcedure, 
ClinicalObservation should all appear in the list
```

**Why it works:** The org preference is the schema gate. Until it is enabled, standard clinical objects do not exist and no amount of permission set configuration will make them accessible. Enabling the preference activates the objects org-wide for all users with appropriate Health Cloud licenses.

---

## Anti-Pattern: Using HC24__ Objects for a New Health Cloud Integration

**What practitioners do:** Reference `HC24__EhrEncounter__c`, `HC24__EhrCondition__c`, `HC24__EhrMedication__c`, and related packaged objects in new Apex classes, Flows, or integration payloads because older documentation, community articles, or prior project code uses these object names.

**What goes wrong:** In orgs provisioned after Spring '23, DML operations against HC24__ objects that have standard-object counterparts fail. Apex code that references these objects may compile but throw runtime exceptions. In older orgs that are migrating, data written to HC24__ will not be visible through the FHIR R4 API surface that the standard clinical objects expose. The two layers are not automatically synchronized — data in HC24__ is not mirrored to standard objects and vice versa.

**Correct approach:** Always target FHIR R4-aligned standard objects for new data writes. Confirm the FHIR-Aligned Clinical Data Model org preference is enabled first. Use the decision table in SKILL.md to confirm which layer to use before writing any code.
