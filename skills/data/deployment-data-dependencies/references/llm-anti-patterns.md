# LLM Anti-Patterns — Deployment Data Dependencies

Common mistakes AI coding assistants make when generating Salesforce data migration and deployment scripts.

---

## Anti-Pattern 1: Hardcoding RecordType IDs in Data Load Scripts

**What the LLM generates:** A data migration script or CSV template with a `RecordTypeId` column populated with 18-character IDs copied from the source org.

**Why it happens:** LLMs generate concrete ID values from examples or from a provided schema without flagging the org-specificity of those IDs.

**The correct pattern:** RecordType IDs are org-specific. Use `RecordType.DeveloperName` in SFDMU mappings. In Apex scripts, use `Schema.SObjectType.<Object>.getRecordTypeInfosByDeveloperName().get('<DeveloperName>').getRecordTypeId()` to resolve at runtime.

**Detection hint:** Any data migration CSV or script that contains a hardcoded 18-character ID in a RecordTypeId column is not portable across orgs.

---

## Anti-Pattern 2: Deploying Custom Settings Data as Metadata

**What the LLM generates:** "Add your Custom Setting default values to the deployment package so they deploy automatically to all orgs."

**Why it happens:** LLMs know that Custom Settings are configured in Setup and assume they deploy with metadata packages like most Setup configuration.

**The correct pattern:** Custom Settings data is org-specific sObject data. The Metadata API deploys the Custom Setting schema (field definitions) but not the data records. Populate Custom Setting values via a separate data load step after metadata deployment.

**Detection hint:** Any recommendation to include Custom Settings "values" or "defaults" in a metadata deployment package (not just the sObject type schema) is incorrect.

---

## Anti-Pattern 3: Hardcoding Queue IDs in Flow or Apex

**What the LLM generates:** An Apex assignment like `newCase.OwnerId = '00G3x000002XXXXX';` or a Flow Assignment node with a hardcoded Queue ID.

**Why it happens:** LLMs generate code with concrete ID values from examples without noting that these IDs are environment-specific.

**The correct pattern:** Queue IDs (Group IDs) are org-specific. Resolve the queue ID at runtime using `SELECT Id FROM Group WHERE Type = 'Queue' AND Name = 'Support Tier 1'`. In Flow, use a Get Records element before the assignment node.

**Detection hint:** Any hardcoded 15- or 18-character Salesforce ID used as a queue owner is an environment-specific reference that will fail in a different org.

---

## Anti-Pattern 4: Using INVALID_CROSS_REFERENCE_KEY Troubleshooting Steps for Metadata Errors

**What the LLM generates:** "INVALID_CROSS_REFERENCE_KEY is a metadata deployment error — check your object API names and field relationships in your deployment package."

**Why it happens:** LLMs associate "invalid cross reference" with metadata dependency errors, which is a different and unrelated error class.

**The correct pattern:** `INVALID_CROSS_REFERENCE_KEY` on a data load is a data error, not a metadata error. It means the ID value in the data file does not exist in the target org. Diagnose by checking whether the referenced ID (RecordType, Queue, User, Account, etc.) was exported from a different org and not re-mapped.

**Detection hint:** If `INVALID_CROSS_REFERENCE_KEY` occurs during a data load (not a metadata deploy), the fix is in the data file — resolve the ID reference dynamically, don't change metadata.

---

## Anti-Pattern 5: Using SFDMU @sf_reference_id for Objects That Don't Support It

**What the LLM generates:** "Use `@sf_reference_id` in your SFDMU configuration to resolve all cross-object references automatically."

**Why it happens:** LLMs apply a pattern broadly without checking which sObjects support external ID-based upsert.

**The correct pattern:** `@sf_reference_id` relies on external ID fields and Bulk API upsert. Not all standard sObjects support external IDs on all fields. Verify the sObject's `externalIdFieldName` capability in the object metadata before using this pattern. Use explicit SOQL ID-lookup steps for unsupported objects.

**Detection hint:** If a SFDMU config uses `@sf_reference_id` on a standard object without verifying external ID support, it may silently fail or produce `NOT_FOUND` errors.

---

## Anti-Pattern 6: Assuming SandboxPostCopy Can Directly Execute Large Data DML

**What the LLM generates:** "In your SandboxPostCopy implementation class, use a DML loop to populate reference data records immediately in the execute() method."

**Why it happens:** LLMs generate straightforward Apex patterns without considering the execution context constraints of SandboxPostCopy.

**The correct pattern:** SandboxPostCopy runs as the `Automated Process` user and is subject to governor limits within a single synchronous transaction. Large DML operations must be delegated to a Queueable Apex job enqueued from within `runApexClass()`, where each Queueable job runs with its own fresh governor limit context.

**Detection hint:** Any SandboxPostCopy implementation that performs more than a few hundred DML rows directly in the `runApexClass()` method is likely to hit governor limits in production sandbox refreshes.
