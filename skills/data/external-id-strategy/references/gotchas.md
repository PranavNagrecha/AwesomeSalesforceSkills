# Gotchas — External ID Strategy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Default Text External ID Uniqueness Is Case-Insensitive

**What happens:** When you create a Text external ID field and check Unique without also checking the "Treat 'ABC' and 'abc' as different values (case-sensitive)" option, Salesforce enforces case-insensitive uniqueness. Two attempts to insert records with external ID values `ORDER-001` and `order-001` will result in the second insert failing with a uniqueness violation, even though most source systems would treat these as distinct keys.

**When it occurs:** Any time the source system generates alphanumeric keys where the same base characters appear in different cases for different logical records (e.g., order systems that allow user-defined IDs, SKU codes that vary by locale, or migrations from case-sensitive databases). It also affects migrations from systems that store IDs with mixed case and rely on case distinction for identity.

**How to avoid:** During field creation, explicitly check the case-sensitive option if the source system distinguishes case. Regardless of the setting, normalize all external ID values to a consistent case (all uppercase is the most common convention) in the ETL layer before staging data. Documenting the normalization rule in the integration spec prevents future maintainers from loading case variants that break upsert idempotency.

---

## Gotcha 2: Upsert Errors on Duplicate External ID Values Are Per-Row — Easy to Miss in Bulk Jobs

**What happens:** If two or more Salesforce records already share the same external ID value (possible when the Unique constraint was not set at field creation, or was temporarily removed), a Bulk API 2.0 upsert job processing a row with that value returns an error for that specific row. All other rows in the batch continue processing normally. The job completes with status `JobComplete` but has a non-zero `numberRecordsFailed`. The overall job does not fail — it reports partial success.

**When it occurs:** This most often appears after an initial migration where the Unique constraint was accidentally omitted, the UI was used to insert duplicate values during testing, or a data quality issue in the source system was not caught before loading. It also appears when the External ID field existed before the Unique constraint was added (legacy records can violate a constraint added after their creation).

**How to avoid:** Before enabling an external ID field as an upsert key on an object with existing data, run a SOQL query to confirm no duplicates exist:

```soql
SELECT ERP_Customer_Number__c, COUNT(Id)
FROM Account
WHERE ERP_Customer_Number__c != null
GROUP BY ERP_Customer_Number__c
HAVING COUNT(Id) > 1
```

Always inspect the Bulk API 2.0 job error file after every upsert run — not just the job status code. Automate error file retrieval and alert on any non-zero `numberRecordsFailed`.

---

## Gotcha 3: External ID Without Unique Does Not Prevent Duplicates

**What happens:** Marking a field as External ID creates an index and exposes it as an upsert key, but it does not enforce uniqueness by itself. The `Unique` checkbox is a completely separate setting. If Unique is not checked, users can insert records with duplicate external ID values through the Salesforce UI, Data Import Wizard, or any non-upsert DML. Once duplicates exist, every subsequent upsert attempt on that value returns an error rather than performing an update.

**When it occurs:** Most commonly during initial field setup where the developer marks External ID but forgets Unique, or intentionally omits Unique because they believe they might need non-unique external IDs for reference (not upsert) purposes, then later switches the field to upsert without cleaning up duplicates first.

**How to avoid:** Always set both External ID and Unique together when the field will be used as an upsert key. If the field is used only for cross-system correlation (not upsert), document this explicitly and never pass it as the `externalIdFieldName` in a Bulk API job.

---

## Gotcha 4: Relationship Resolution Errors Are Per-Row and Fail Silently in Partial Success Jobs

**What happens:** When using relationship column syntax (`Account.ERP_Customer_Number__c`) in a child CSV, if a parent record with the specified external ID value does not exist, the child row fails with an error. The Bulk API 2.0 job still completes with partial success status — it does not abort. Child records whose parent cannot be resolved are silently skipped from the org's perspective (they appear only in the job error file).

**When it occurs:** This happens when the parent load did not complete before the child load was started, when the parent external ID value in the child file contains a typo or trailing space, or when the parent record was not included in the parent load for any reason (filtered out, errored during parent job).

**How to avoid:** Always enforce parent-before-child load ordering in the integration pipeline. After the parent job completes, retrieve and validate the parent error file before submitting the child job. Include a row count reconciliation step: the number of successfully loaded parents should match the number of distinct parent reference values in the child file before the child job is submitted.

---

## Gotcha 5: External ID Fields Are Not Portable Across Metadata Deployments Without the `externalId` Flag

**What happens:** When deploying a custom field via Salesforce DX metadata, the `<externalId>true</externalId>` element must be explicitly set in the CustomField XML. If this element is omitted or set to `false`, the field is created as a regular indexed Text/Number field without external ID or upsert key capabilities. Deployments that promote a field from sandbox to production without this element set correctly will silently create a regular field — upsert jobs that reference it will fail with an error indicating the field is not an external ID.

**When it occurs:** When field metadata is exported from an org using `sf project retrieve start` and the field was configured correctly in the UI, the XML should have the flag. However, if the XML was hand-authored or copied from another field definition and the element was missed, the deployment will not produce an external ID field.

**How to avoid:** After deploying external ID fields, verify them in Setup > Object Manager > Fields and check the "External ID" column. In the metadata XML, confirm both `<externalId>true</externalId>` and `<unique>true</unique>` are present before promoting through environments.
