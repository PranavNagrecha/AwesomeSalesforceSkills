# Examples — Deployment Data Dependencies

## Example 1: INVALID_CROSS_REFERENCE_KEY on RecordType During Data Load

**Scenario:** A team migrates Account records from a sandbox to production using SFDMU. The data file references Record Type IDs captured from the source sandbox. The load fails in production with `INVALID_CROSS_REFERENCE_KEY` on the RecordTypeId field for every record.

**Problem:** Record Type IDs are 18-character Salesforce IDs that are unique per org. The IDs in the sandbox do not match the IDs in production even if the Record Type API Name is identical. Hardcoding sandbox IDs into the data file makes the load non-portable.

**Solution:** Replace the `RecordTypeId` column in the data file with a `RecordType.DeveloperName` column. SFDMU resolves the DeveloperName to the correct ID in the target org at load time. For Apex-based data insertion, use `Schema.SObjectType.Account.getRecordTypeInfosByDeveloperName().get('Commercial').getRecordTypeId()` to resolve dynamically at runtime.

**Why it works:** DeveloperName is a human-assigned string that is consistent across orgs if the same managed or unmanaged package created the Record Type. SFDMU's external ID / reference resolution maps DeveloperName to the target-org ID automatically during the load job.

---

## Example 2: Custom Setting Values Not Deployed with Metadata — Data Load Required

**Scenario:** A deployment package includes a Custom Settings object with new fields. In the target org, the fields deploy successfully but all records in the Custom Setting show blank values for the new fields, breaking business logic that reads those values.

**Problem:** Custom Settings are org-specific data, not metadata. Deploying the Custom Setting object type deploys its schema (field definitions) but not the data records. Data values stored in a Custom Setting in the source org must be loaded separately as data, not as metadata.

**Solution:** Export Custom Setting records from the source org as CSV using Data Loader or SOQL query. Load the records into the target org as a data migration step after the metadata deployment completes. Document this step explicitly in the deployment runbook.

**Why it works:** `CustomSettingData` records are sObject rows in the database. The Metadata API handles schema; it does not copy data rows. This is consistent with the platform's metadata/data separation model.

---

## Example 3: Queue ID Lookup in a Multi-Org Deployment

**Scenario:** A Flow is deployed that auto-assigns Cases to a queue via a hardcoded Queue ID. The deployment succeeds but the Flow fails at runtime in production with `INVALID_CROSS_REFERENCE_KEY` on the OwnerId field.

**Problem:** Queue IDs (which are stored as Group IDs on records) are org-specific. The ID of the `Support Tier 1` queue in sandbox is different from its ID in production.

**Solution:** Replace the hardcoded ID with a dynamic lookup: `SELECT Id FROM Group WHERE Type = 'Queue' AND Name = 'Support Tier 1'`. In Flow, use a Get Records element to look up the queue by Name before the assignment. In Apex, run the SOQL at runtime.

**Why it works:** Queue names are human-assigned and typically consistent across orgs. Resolving by Name at runtime eliminates the org-specific ID dependency entirely.
