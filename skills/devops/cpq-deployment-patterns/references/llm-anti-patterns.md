# LLM Anti-Patterns — CPQ Deployment Patterns

Common mistakes AI coding assistants make when generating or advising on Salesforce CPQ deployment between environments.

---

## Anti-Pattern 1: Treating CPQ Configuration as Metadata Deployable via sf CLI

**What the LLM generates:** A deployment pipeline that runs `sf project deploy start --source-dir force-app --target-org production` to deploy CPQ configuration, or instructs the team to include CPQ Quote Templates in a Change Set.

**Why it happens:** LLMs associate Salesforce deployment with metadata deployment tools, not knowing that CPQ configuration lives in the data layer.

**Correct pattern:** CPQ configuration records are data, not metadata. A complete CPQ release pipeline has two steps: (1) metadata deployment via sf CLI for custom fields/Apex/LWC and (2) data deployment via SFDMU, Copado Data Deploy, or Data Loader for CPQ records. Metadata deployment alone leaves CPQ configuration missing in the target org.

**Detection hint:** If a CPQ deployment plan mentions only Change Sets or sf deploy with no separate data migration step, CPQ configuration will not be deployed.

---

## Anti-Pattern 2: Using Org-Specific Record IDs as Cross-Org References

**What the LLM generates:** A data export CSV with sandbox-specific Product2 IDs as values in the SBQQ__PricingRule__c product lookup field.

**Why it happens:** LLMs extract records with their current ID values without modeling that IDs are org-specific.

**Correct pattern:** All cross-org record references must use External ID fields as the cross-org matching key. Add `CPQ_External_Id__c` to Product2 and reference it as `Product2.CPQ_External_Id__c` in SFDMU configuration. Org-specific IDs produce INVALID_CROSS_REFERENCE_KEY errors at load time in the target org.

**Detection hint:** If a CPQ data plan extracts records with raw Salesforce ID values in parent lookup fields (rather than External IDs), cross-org loads will fail.

---

## Anti-Pattern 3: Loading CPQ Data in the Wrong Order

**What the LLM generates:** A data load script that loads SBQQ__ProductRule__c before SBQQ__PricingRule__c, or loads PricebookEntry before Product2.

**Why it happens:** LLMs generate load orders based on alphabetical sort or the order records were queried, not on the CPQ dependency chain.

**Correct pattern:** The required CPQ data load order is: Pricebook2/DiscountCategory → Product2 → PricebookEntry → SBQQ__PricingRule__c → SBQQ__ProductRule__c → SBQQ__QuoteTemplate__c. Loading out of order produces foreign key constraint failures.

**Detection hint:** If a deployment plan loads Quote Templates before Price Rules, or Price Rules before Products, foreign key errors will occur.

---

## Anti-Pattern 4: Single-Pass Load for Self-Referential CPQ Objects

**What the LLM generates:** A single SFDMU or Data Loader job that loads CPQ Option Groups with parent Group references in one pass.

**Why it happens:** LLMs model data loads as single-pass operations and do not model the circular dependency in self-referential objects.

**Correct pattern:** Self-referential CPQ objects require a two-pass approach: insert all records with the self-reference field null, then update the field in a second pass. SFDMU `selfParentExternalIdFieldName` automates this.

**Detection hint:** If Option Group or similar self-referential CPQ objects are loaded in a single pass with parent references populated, foreign key failures will occur for any record whose parent comes later in the file.

---

## Anti-Pattern 5: Skipping Post-Deployment CPQ Quote Validation

**What the LLM generates:** A deployment pipeline that marks the CPQ deployment as complete after the data load job exits with code 0, without any test quote validation step.

**Why it happens:** LLMs treat exit code 0 as deployment success. They do not model the business logic validation step that confirms CPQ pricing rules produce correct results.

**Correct pattern:** After CPQ data deployment, run test CPQ quotes for each major pricing scenario in the target org. Compare results to expected pricing from the source org. Structurally correct deployment (all records present) does not guarantee logically correct pricing (rules produce the right prices).

**Detection hint:** If the deployment validation plan includes only SOQL record count checks and no live quote generation tests, pricing logic correctness is unverified.
