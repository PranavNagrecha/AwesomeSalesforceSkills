# Gotchas — CPQ Deployment Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: CPQ Configuration Data Cannot Be Deployed via Change Sets or sf CLI

CPQ configuration (Price Books, Products, Price Rules, Product Rules, Quote Templates) exists as data records in Salesforce objects — not as deployable metadata. Change Sets and `sf project deploy` only move metadata. A CI/CD pipeline that deploys only metadata succeeds with exit code 0 but leaves all CPQ configuration missing in the target org.

**Fix:** CPQ release pipelines require a dedicated data deployment step using SFDMU, Copado Data Deploy, Prodly, or Data Loader with External IDs after the metadata deployment step.

---

## Gotcha 2: Record IDs Are Org-Specific — Cross-Org References Must Use External IDs

Every Salesforce record ID (18-character) is unique to the org where the record was created. The same CPQ Product has a different ID in sandbox vs. production. Any data plan that uses org-specific IDs in lookup fields will produce INVALID_CROSS_REFERENCE_KEY errors at load time — with no indication that the root cause is an org-ID mismatch.

**Fix:** Add custom External ID fields to all CPQ objects. Populate them in the source org before extraction. Use External ID fields as upsert keys and parent reference keys in cross-org loads.

---

## Gotcha 3: Self-Referential CPQ Lookups Require Multi-Pass Deployment

CPQ objects with self-referential lookups (child references parent of the same object type) cannot be loaded in a single pass. The parent record doesn't exist when the child is being inserted, causing a foreign key constraint failure.

**Fix:** Use a two-pass approach: insert all records with the self-reference null, then update the self-reference field. SFDMU handles this with `selfParentExternalIdFieldName` configuration.

---

## Gotcha 4: CPQ Price Rule Load Order Depends on Products and Price Books

SBQQ__PricingRule__c records reference Product2 and Pricebook2 records. Loading Price Rules before Products produces foreign key errors. The required CPQ data load order is: Pricebook2/DiscountCategory → Product2 → PricebookEntry → SBQQ__PricingRule__c → SBQQ__ProductRule__c → SBQQ__QuoteTemplate__c.

**Fix:** Enforce this load order explicitly in the deployment script. Do not allow a tool to infer order automatically — CPQ dependency chains are non-trivial and tool inference is often wrong.

---

## Gotcha 5: CPQ Quote Calculation Runs in Target Org After Deployment — Test Before Go-Live

After CPQ data deployment, the target org calculates quotes using the deployed configuration. If Price Rules have incorrect conditions or Product Rules have circular dependencies, test quotes will fail silently with incorrect pricing or no price generated. There is no automatic validation that deployed CPQ configuration is logically correct.

**Fix:** After every CPQ data deployment, run test CPQ quotes in the target org for each major pricing scenario. Compare results to expected pricing from the source org. Fix logic errors before go-live.
