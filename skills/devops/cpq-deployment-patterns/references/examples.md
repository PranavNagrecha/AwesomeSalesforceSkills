# Examples — CPQ Deployment Patterns

## Example 1: Change Set Deploys Successfully But CPQ Config Missing in Production

**Scenario:** A CPQ admin deployed a new Quote Template and Product Rules from sandbox to production via Change Set. The deployment succeeded, but the Quote Template did not appear in production.

**Problem:** Change Sets deploy Salesforce metadata. CPQ Quote Templates and Product Rules are data records, not metadata. The Change Set deployed metadata components but not the configuration records.

**Solution:**
1. Export Quote Template and Product Rule records from sandbox using SFDMU or Data Loader
2. Populate External IDs on all records before extraction
3. Import to production using upsert with External ID matching
4. Validate: `SELECT Id FROM SBQQ__QuoteTemplate__c WHERE Name = 'My Template'`

**Prevention:** CPQ release pipelines must include a dedicated data deployment step after the metadata deployment step.

---

## Example 2: INVALID_CROSS_REFERENCE_KEY on Price Rule Import — Hardcoded IDs

**Scenario:** A deployment script loaded SBQQ__PricingRule__c records from sandbox to production. Every record failed with INVALID_CROSS_REFERENCE_KEY on the Product lookup field.

**Problem:** The extracted records contained sandbox Product2 IDs in the product lookup. Product IDs are org-specific — the same product has a different ID in sandbox vs. production.

**Solution:**
1. Add External ID field to Product2 in both orgs: `CPQ_External_Id__c`
2. Populate External IDs in sandbox
3. Re-extract Price Rules with product reference as `Product2.CPQ_External_Id__c`
4. Use SFDMU upsert with External ID resolution for the product lookup

**Why this works:** External IDs are org-agnostic identifiers that translate correctly across org boundaries.

---

## Example 3: Option Group Self-Referential Lookup Fails on Single-Pass Load

**Scenario:** A CPQ deployment script loaded Option Groups where some had parent group references. Every child record failed with foreign key errors because the parent Group didn't exist yet.

**Problem:** Self-referential lookups cannot be resolved in a single-pass load — the parent record hasn't been inserted when the child is being loaded.

**Solution:**
1. First pass: insert all Option Group records with parent reference = null
2. Second pass: update records with the correct parent reference — all records now exist
3. Using SFDMU: configure `selfParentExternalIdFieldName` to automate this pattern

**Why this works:** Two-pass ensures all records exist before self-referential foreign keys are set.
