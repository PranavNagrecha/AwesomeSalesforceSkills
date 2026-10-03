# Examples: FHIR Integration Patterns

## Example 1: Normalize a FHIR R4 Condition into HealthCondition, CodeSetBundle, and CodeSet

**Context:** Middleware delivers FHIR R4 Condition resources and the patient Account Id to an Apex service.

**Approach:** Upsert CodeSet records by `SourceSystem` and `Code`, build a CodeSetBundle with up to 15 references (reporting any dropped codings), flatten `onsetPeriod`, and insert HealthCondition with the required `ConditionCodeId`. The class, its test, and package.xml are in `code-examples.md`.

---

## Example 2: Read and batch-write through the Salesforce Healthcare API

**Read a patient's conditions (sandbox, US region):**

```http
GET https://api.healthcloud.salesforce.com/sandBox/clinical-summary/fhir-r4/v1/Condition?patient=001xx000003GYk1AAG
Authorization: Bearer [REDACTED]
Accept: application/fhir+json
```

The client app requests the custom scope `user_condition_read` (or `user_all_read`). The URL shape, module name, sandbox path, and scope names are from the Salesforce Healthcare API guide ("Call the API," "Authorization"). UNVERIFIED (2026-10-03): which FHIR search parameters (such as `patient`) each resource supports.

**Batch write with an internal reference:**

```json
{
  "resourceType": "Bundle",
  "type": "batch",
  "entry": [
    {
      "fullUrl": "urn:uuid:4f6c2a1e-8d3b-4c1f-9a2e-1b7d5c3e9f00",
      "resource": { "resourceType": "Patient", "name": [ { "family": "Rivera", "given": [ "Ana" ] } ] },
      "request": { "method": "POST", "url": "Patient" }
    },
    {
      "resource": {
        "resourceType": "Condition",
        "subject": { "reference": "urn:uuid:4f6c2a1e-8d3b-4c1f-9a2e-1b7d5c3e9f00" },
        "code": { "coding": [ { "system": "http://snomed.info/sct", "code": "44054006", "display": "Diabetes mellitus type 2" } ] }
      },
      "request": { "method": "POST", "url": "Condition" }
    }
  ]
}
```

The guide supports only `batch` Bundles, allows up to 30 entries per call with up to 10 reads or searches, supports `urn:uuid:` placeholders in `fullUrl` and references, and returns 424 for entries whose dependency failed. Keep concurrent calls at five or fewer. UNVERIFIED (2026-10-03): the exact URL path for posting to the `bundle` module.

---

## Example 3: CDS Hooks through MuleSoft

**Context:** A health system wants care-gap cards in Epic when a care coordinator opens a patient chart.

**Solution:**
1. Deploy the MuleSoft CDS Hooks Direct Integration app (or a custom MuleSoft API) as the CDS service, for example `https://api.example-health.org/cds-services/care-gap-alerts`.
2. Register that endpoint in the EHR's CDS Hooks configuration for the `patient-view` hook.
3. On each call, MuleSoft maps the FHIR patient ID to the Salesforce Account (through Identifier records) and reads open care gaps and alerts from Health Cloud.
4. MuleSoft returns CDS Hooks cards to the EHR.

**Why it works:** The Healthcare API guide documents CDS Hooks as a MuleSoft integration that connects EMR workflows to clinical decision support from Health Cloud. Salesforce stays the data store; MuleSoft is the CDS service.

---

## Anti-Pattern: Writing HC24 EHR objects for a new integration

**What practitioners do:** Create `HC24__EhrCondition__c` records because older documentation shows them.

**What goes wrong:** Starting with Spring '23, new customers can't create records in packaged EHR objects that have counterpart standard objects.

**Correct approach:** Target HealthCondition and the other FHIR R4-aligned objects, and map with the current "Mapping FHIR v4.0 to Salesforce Standard Objects" tables.
