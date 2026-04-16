# Gotchas — Deployment Data Dependencies

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: RecordType ID Is Org-Specific — DeveloperName Is Portable

**What happens:** A data file exported from sandbox includes a `RecordTypeId` column with 18-character IDs. When loaded into production, every record with a non-null RecordTypeId fails with `INVALID_CROSS_REFERENCE_KEY`.

**Impact:** The entire load fails or partially succeeds, leaving records in an inconsistent state. The error message does not say "wrong org" — it says "invalid cross reference," which is cryptic without knowing the cause.

**How to avoid:** Never use raw RecordType IDs in cross-org data files. Use `RecordType.DeveloperName` as the reference column in SFDMU mappings. For Apex scripts, always resolve via `getRecordTypeInfosByDeveloperName()`. For SOQL export/import scripts, join to the RecordType object and use DeveloperName.

---

## Gotcha 2: Custom Settings Data Is Not Deployed by the Metadata API

**What happens:** A deployment package includes a Custom Settings sObject type with new fields and default values set in the source org. The target org receives the schema changes but all records in the Custom Setting are empty for the new fields. Downstream logic reading those fields silently fails (null reference or wrong behavior).

**Impact:** Post-deployment, features that depend on Custom Setting data produce incorrect results. The failure may not surface immediately if the code handles null gracefully.

**How to avoid:** Treat Custom Settings records as data, not metadata. Add a data migration step to every deployment runbook that exports Custom Setting records from source and loads them into target. This applies even for Hierarchy Custom Settings with org-level defaults.

---

## Gotcha 3: Queue IDs Are Org-Specific — Resolve by Name at Runtime

**What happens:** A Flow or Apex class assigns records to a queue using a hardcoded Group ID. The code works in sandbox and fails in production with `INVALID_CROSS_REFERENCE_KEY` on OwnerId.

**Impact:** Record assignment fails silently or throws an unhandled exception, leaving records unassigned. In Flow, uncaught errors send a generic email notification with no clear diagnosis.

**How to avoid:** Never hardcode Queue IDs. Always resolve queue IDs dynamically using `SELECT Id FROM Group WHERE Type = 'Queue' AND Name = '...'`. This query is safe to run at runtime and always returns the target-org-correct ID.

---

## Gotcha 4: @sf_reference_id in SFDMU Does Not Work for All Object Types

**What happens:** A team uses SFDMU's `@sf_reference_id` syntax to resolve cross-object references during a load, but some objects do not support external ID-based upsert. The load fails with `NOT_FOUND` or `CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY`.

**Impact:** The SFDMU job partially completes. Records that could be resolved load successfully; records with unresolvable `@sf_reference_id` values fail without a clear error about the root cause.

**How to avoid:** `@sf_reference_id` works only for objects that support `externalIdFieldName` on the Bulk API upsert. Not all standard objects support all external ID fields. Review the sObject metadata to confirm `externalIdFieldName` capability before designing an `@sf_reference_id` mapping. Fall back to explicit ID lookup queries for unsupported objects.
