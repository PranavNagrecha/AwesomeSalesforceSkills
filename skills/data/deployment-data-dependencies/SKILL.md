---
name: deployment-data-dependencies
description: "Use this skill when managing data record dependencies during deployments: resolving org-specific record type IDs that differ between source and target orgs, remapping queue IDs and user IDs in data plans, seeding Custom Settings values post-deployment, and using external IDs or DeveloperName references to avoid hardcoded org-specific IDs. Trigger keywords: INVALID_CROSS_REFERENCE_KEY Record Type ID, hardcoded record type IDs deployment, deployment data record org-specific IDs, Custom Settings not deployed, queue ID remap after sandbox refresh. NOT for metadata deployment (use metadata deployment guides), individual Apex test data setup, or FSC-specific deployment sequencing."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "INVALID_CROSS_REFERENCE_KEY error on RecordTypeId during data load"
  - "my data migration works in sandbox but fails in production with cross reference errors"
  - "how do I remap record type IDs when migrating data between Salesforce orgs"
  - "Custom Settings values are empty after deployment — how do I populate them"
  - "queue ID is different in production and sandbox causing data load failures"
  - "how do I avoid hardcoded Salesforce IDs in cross-org data migration scripts"
tags:
  - deployment
  - data-records
  - record-types
  - custom-settings
  - org-specific-ids
  - data-migration
inputs:
  - "List of data record sets being deployed (CSV files, data plans, SFDMU configurations)"
  - "Record type DeveloperNames for all referenced record types"
  - "Custom Settings objects that require post-deploy seeding"
  - "Queue names that must be resolved in target org"
outputs:
  - "Remapping strategy for org-specific IDs (record type, queue, user)"
  - "Post-deploy Custom Settings seeding script"
  - "SFDMU configuration using external IDs instead of hardcoded Salesforce IDs"
  - "Apex dynamic RecordType resolution pattern"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Deployment Data Dependencies

Use this skill when deploying data records (not metadata) across Salesforce orgs and the deployment fails because org-specific IDs — record type IDs, queue IDs, user IDs — differ between the source and target org. Also covers Custom Settings, which are org-specific data that do not deploy with metadata packages and must be seeded post-deployment.

---

## Before Starting

Gather this context before working on anything in this domain:

- What data records are being deployed? CSV files, SFDMU data plan, Salesforce CLI `data import tree`, or a third-party tool like Prodly?
- Which fields contain org-specific IDs that will be different in the target org? Common culprits: `RecordTypeId`, `QueueId` (OwnerId pointing to a queue), `OwnerId` (pointing to a specific user).
- What Custom Settings objects does the application depend on? Custom Settings are org-specific data — they do not deploy with metadata and must be seeded separately.
- Are external IDs defined on the target objects to support upsert-based deployment?

---

## Core Concepts

### Record Type IDs Are Org-Specific

Record type IDs (18-character Salesforce IDs) are assigned when the record type is created in each org. The same record type "Customer Account" will have ID `0123000000000001` in Production but `0127000000000002` in a sandbox. They are never portable across orgs.

The **canonical deployment data error** is:
```
INVALID_CROSS_REFERENCE_KEY: Record Type ID
```
This error occurs when a CSV or data plan hardcodes a record type ID from the source org as a field value in a target org load.

**The safe cross-org reference pattern:**
1. In **Apex**: `Schema.SObjectType.Account.getRecordTypeInfosByDeveloperName().get('Customer_Account').getRecordTypeId()` — resolves the target org's ID dynamically at insert time.
2. In **SFDMU / Bulk API jobs**: Use `RecordType.DeveloperName` as an external ID reference in the relationship field mapping, not `RecordTypeId` as a literal ID column.
3. In **sf data import tree** (`@sf_reference_id` mechanism): Reference records by their `@sf_reference_id` node attribute — this creates relative references resolved at import time, not org-specific IDs.

### Custom Settings Are Org-Specific Data — They Do Not Deploy

Custom Settings (both Hierarchy and List types) are **org-specific data records**, not metadata. When you deploy a metadata package or change set:
- The Custom Setting **object definition** (fields, API name) deploys as metadata
- The Custom Setting **data records** (the actual values) do NOT deploy

The only way to transfer Custom Settings data is:
1. A **post-deploy Apex script** that reads a configuration and inserts the Custom Setting records
2. A **SandboxPostCopy implementation** that seeds Custom Settings when the sandbox is refreshed
3. A **data deploy step** in the CI/CD pipeline (SFDMU, Copado Data Deploy, Prodly) that treats Custom Settings as deployable data objects

Failing to seed Custom Settings after deployment causes silent failures — features controlled by Custom Settings simply do not work without throwing a clear error.

### Queue IDs and User IDs Are Also Org-Specific

Like record type IDs, Queue IDs (OwnerId values pointing to Group records of type `Queue`) and User IDs are org-specific. When loading records where `OwnerId` should be a queue, the approach is:
- Query the target org's `Group` object: `SELECT Id, Name FROM Group WHERE Type = 'Queue' AND Name = 'Case Queue'` — use the resulting ID in the import.
- In SFDMU, use the `Group.Name` or `Group.DeveloperName` as an external ID reference rather than the hardcoded Queue ID.

---

## Common Patterns

### Pattern: SFDMU External ID Mapping for RecordType

**When to use:** Deploying data records via SFDMU that include RecordTypeId as a lookup field.

**How it works:**
In the SFDMU `export.json` configuration, use the relationship field pattern instead of `RecordTypeId`:
```json
{
  "fields": ["Name", "RecordType.DeveloperName"],
  "externalId": "Name",
  "relationship": {
    "RecordType.DeveloperName": "RecordTypeId"
  }
}
```
SFDMU resolves `RecordType.DeveloperName` in the target org and maps the result to `RecordTypeId` at insert time — no hardcoded IDs required.

**Why not hardcode IDs:** Hardcoded IDs from source org cause INVALID_CROSS_REFERENCE_KEY on every target org where the record type ID differs.

### Pattern: Post-Deploy Custom Settings Seeding Script

**When to use:** After every deployment that depends on Custom Settings values.

**How it works:**
1. Define the required Custom Settings values in a version-controlled JSON or YAML configuration file.
2. Write an Apex script (anonymous Apex or invocable) that reads this configuration and upserts Custom Setting records.
3. Execute this script as a post-deploy step in the CI/CD pipeline (e.g., `sf apex run -f scripts/seed-custom-settings.apex`).

**Why not use change sets:** Change sets deploy the metadata definition but not the data. Manual entry post-deploy is error-prone and untraceable. A script in version control is auditable.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| RecordTypeId in CSV causing INVALID_CROSS_REFERENCE_KEY | Use RecordType.DeveloperName in SFDMU mapping | DeveloperName is portable across orgs; ID is not |
| Custom Settings not working after deployment | Add post-deploy seeding script | Custom Settings data does not deploy with metadata |
| Queue OwnerId in data plan failing in target org | Query Group.Name in target org to get queue ID | Queue IDs are org-specific |
| Apex DML hardcoding a record type ID | Replace with getRecordTypeInfosByDeveloperName() | Dynamic resolution always uses target org's ID |
| sf data import tree with cross-object references | Use @sf_reference_id node attribute | Creates relative references resolved at import time |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Audit the data plan for org-specific IDs** — Review all CSV files and data plan configs for hardcoded 15/18-character Salesforce IDs in lookup fields. Flag `RecordTypeId`, `OwnerId`, `AssignedTo__c`, or any field containing an ID.
2. **Map record type DeveloperNames** — For each hardcoded RecordTypeId, find the corresponding `DeveloperName` in the source org. Verify the same DeveloperName exists in the target org.
3. **Update data plan to use DeveloperName references** — Replace hardcoded RecordTypeId values with `RecordType.DeveloperName` lookups in SFDMU or equivalent tool configuration.
4. **Identify Custom Settings dependencies** — List all Custom Settings objects the application reads. Confirm that post-deploy seeding is in the deployment runbook.
5. **Write or update seeding scripts** — Create/update the post-deploy Custom Settings seeding script and add it to the CI/CD pipeline.
6. **Test in target org** — Execute the data deployment, confirm no INVALID_CROSS_REFERENCE_KEY errors, and verify Custom Settings values are present and correct.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] No hardcoded org-specific Salesforce IDs in data plan or CSV files
- [ ] RecordType references use DeveloperName, not hardcoded ID
- [ ] Queue references use Group.Name or DeveloperName lookup
- [ ] Custom Settings seeding script included in deployment runbook
- [ ] Apex code uses `getRecordTypeInfosByDeveloperName()`, not hardcoded IDs
- [ ] Post-deploy test confirms no INVALID_CROSS_REFERENCE_KEY errors

---

## Salesforce-Specific Gotchas

1. **INVALID_CROSS_REFERENCE_KEY is a data error, not a metadata error** — This error looks like a deployment error but it is a data record DML error caused by hardcoded org-specific ID values in the data being loaded. It is not caught by metadata validation and only appears at data load time.

2. **Custom Settings data is silently missing post-deployment** — Features that read Custom Settings fail without throwing a clear error if Custom Settings are not seeded. The root cause is often only discovered in QA testing when expected behavior does not occur.

3. **getRecordTypeInfosByDeveloperName() requires the DeveloperName, not the Label** — Developers frequently use the record type Label (which may contain spaces) instead of the API DeveloperName. The method accepts only the DeveloperName (no spaces, underscore-separated).

4. **sf data import tree @sf_reference_id does not resolve external IDs for lookup targets not in the same tree** — If the referenced record is not in the same import tree (e.g., a lookup to a User record that already exists in the target org), `@sf_reference_id` does not work. Use an external ID field on the target object for cross-tree references.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| ID audit report | List of data plan fields containing hardcoded org-specific IDs |
| Remapping configuration | Updated SFDMU or data plan config using DeveloperName references |
| Custom Settings seeding script | Apex or CLI script for post-deploy Custom Settings population |

---

## Related Skills

- `devops/deployment-strategies` — Use for overall deployment sequencing and runbook design
- `devops/environment-specific-value-injection` — Use for Named Credential and Custom Metadata (CMT) config value management at deployment time
- `data/sandbox-refresh-data-strategies` — Use for post-sandbox-refresh data seeding which shares many of the same patterns
- `devops/cpq-deployment-patterns` — Use for CPQ-specific data deployment with complex relational data sets
