# Examples — CPQ Deployment Administration

## Example 1: Migrating Price Rules and Price Actions with SFDMU External IDs

**Context:** A mid-market ISV has 40 Price Rules and over 200 Price Actions managing volume discounts, partner tier adjustments, and promotional pricing. The team uses SFDX-based DevOps for metadata but has never moved CPQ configuration records between their Full Sandbox and production.

**Problem:** The team attempts a Change Set deployment. The Change Set UI allows them to add `SBQQ__PriceRule__c` as a custom object, but when deployed, the target org has zero Price Rule records. CPQ pricing silently uses defaults, and quotes produce incorrect prices in production without any error or alert.

**Solution:**

```bash
# Step 1: Add external ID field to SBQQ__PriceRule__c and SBQQ__PriceAction__c in both orgs
# Deploy metadata (custom field definitions) first — this IS normal metadata
sf project deploy start --source-dir force-app/main/default/objects/SBQQ__PriceRule__c

# Step 2: Populate external IDs in source org via anonymous Apex
# Run in Full Sandbox Developer Console / sf apex run
List<SBQQ__PriceRule__c> rules = [SELECT Id, Name FROM SBQQ__PriceRule__c];
for (SBQQ__PriceRule__c r : rules) {
    r.CPQ_External_Id__c = 'PRICERULE_' + r.Name.replaceAll('[^a-zA-Z0-9]', '_');
}
update rules;

# Step 3: Create SFDMU exportTree plan (exportPlan.json)
# {
#   "objects": [
#     { "query": "SELECT Id, Name, CPQ_External_Id__c, SBQQ__Active__c,
#                         SBQQ__ConditionsMet__c, SBQQ__Currency__c
#                  FROM SBQQ__PriceRule__c WHERE SBQQ__Active__c = true",
#       "operation": "Upsert", "externalId": "CPQ_External_Id__c" },
#     { "query": "SELECT Id, CPQ_External_Id__c, SBQQ__PriceRule__r.CPQ_External_Id__c,
#                         SBQQ__TargetField__c, SBQQ__TargetObject__c, SBQQ__Value__c
#                  FROM SBQQ__PriceAction__c",
#       "operation": "Upsert", "externalId": "CPQ_External_Id__c" }
#   ]
# }

# Step 4: Run SFDMU export from Full Sandbox
sf sfdmu run --sourceusername sandbox_alias --targetusername production_alias \
  --plan exportPlan.json

# Step 5: Validate — create a test Quote in production against a volume product
# Confirm the expected discount tier applies automatically
```

**Why it works:** SFDMU resolves the `SBQQ__PriceRule__r.CPQ_External_Id__c` relationship reference during import, mapping the source org Price Rule record ID to the correct target org record ID. Upsert on external ID means re-running the job is idempotent — existing records are updated rather than duplicated.

---

## Example 2: Identifying and Repairing Broken API-Name String References After Field Rename

**Context:** A CPQ admin renames a custom quote field from `Discount_Override__c` to `Approved_Discount__c` using the Setup UI. After the rename, two Price Rules that apply the override discount silently stop working in production. No error is shown on quotes.

**Problem:** The Price Action records referencing the old field still contain the string `"Discount_Override__c"` in `SBQQ__TargetField__c`. CPQ's runtime engine looks up that field name on the Quote object using dynamic Apex. Since the field no longer exists under that name, CPQ silently skips the action. Because there is no compile-time check, the deployment of the renamed field succeeds cleanly, masking the breakage.

**Solution:**

```soql
-- Step 1: Find all Price Actions referencing the renamed field
SELECT Id, SBQQ__PriceRule__r.Name, SBQQ__TargetField__c, SBQQ__TargetObject__c
FROM SBQQ__PriceAction__c
WHERE SBQQ__TargetField__c = 'Discount_Override__c'

-- Step 2: Find all Price Conditions referencing the renamed field
SELECT Id, SBQQ__PriceRule__r.Name, SBQQ__TestedField__c
FROM SBQQ__PriceCondition__c
WHERE SBQQ__TestedField__c = 'Discount_Override__c'
```

```apex
// Step 3: Bulk-update the stale string references via anonymous Apex in each org
List<SBQQ__PriceAction__c> actions = [
    SELECT Id, SBQQ__TargetField__c FROM SBQQ__PriceAction__c
    WHERE SBQQ__TargetField__c = 'Discount_Override__c'
];
for (SBQQ__PriceAction__c a : actions) {
    a.SBQQ__TargetField__c = 'Approved_Discount__c';
}
update actions;

List<SBQQ__PriceCondition__c> conditions = [
    SELECT Id, SBQQ__TestedField__c FROM SBQQ__PriceCondition__c
    WHERE SBQQ__TestedField__c = 'Discount_Override__c'
];
for (SBQQ__PriceCondition__c c : conditions) {
    c.SBQQ__TestedField__c = 'Approved_Discount__c';
}
update conditions;
```

**Why it works:** Because SBQQ rule fields store API names as text strings, a targeted SOQL query with a string match is the only way to find all affected records. The fix is a simple field update in each affected org — but critically, you must run this in every environment (sandboxes and production) separately, or include it in the migration plan as an additional data patch step after deploying the renamed field metadata.

---

## Anti-Pattern: Using Change Sets to "Deploy" CPQ Configuration

**What practitioners do:** Add SBQQ custom objects or individual SBQQ records to a Change Set, deploy to production, and expect CPQ configuration to appear in the target org.

**What goes wrong:** Change Sets deploy metadata components — object schemas, field definitions, validation rules, Apex classes. They do not deploy sObject record data. The SBQQ objects will be present as schema in the target org but will contain zero configuration records. CPQ will behave as if unconfigured, applying no price rules and no product rules, producing unconstrained quotes. In many orgs this manifests as quotes defaulting to list price with no discounts, which may go undetected until a customer complains about incorrect pricing.

**Correct approach:** Use a data-migration tool (Prodly, SFDMU, Copado Data Deploy, or Salto) to export SBQQ records from the source org and upsert them to the target in the correct parent-before-child order. External ID fields are required for idempotent repeated migrations.
