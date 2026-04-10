# Product Catalog Migration CPQ — Work Template

Use this template when planning or executing a Salesforce CPQ product catalog migration.

## Scope

**Skill:** `product-catalog-migration-cpq`

**Request summary:** (fill in what was asked — e.g., "Migrate CPQ product catalog from production to UAT sandbox")

**Source org:** _______________
**Target org:** _______________
**CPQ managed package version (source):** _______________
**CPQ managed package version (target):** _______________

---

## Context Gathered

Record answers to the Before Starting questions from SKILL.md before any load activity.

- **CPQ managed package confirmed in target?** Yes / No
- **CPQ triggers disabled in Additional Settings before Wave 1?** Yes / No — confirmed by SOQL:
  `SELECT SBQQ__TriggerAutoRuns__c FROM SBQQ__PackageSettings__c LIMIT 1` → value: ___
- **External ID fields deployed to target org on all SBQQ objects?** Yes / No
  - External ID field name: _______________
  - Objects covered: [ ] Product2 [ ] SBQQ__PriceRule__c [ ] SBQQ__PriceAction__c [ ] SBQQ__ProductOption__c [ ] SBQQ__DiscountSchedule__c [ ] SBQQ__DiscountCategory__c [ ] SBQQ__ConfigurationAttribute__c [ ] SBQQ__OptionConstraint__c
- **Product2 self-references identified?** Yes / No
  - Self-referencing fields in scope: _______________
  - Two-pass strategy required? Yes / No
- **Known constraints or risks:** _______________

---

## Object Inventory

Fill in record counts from the source org export.

| Wave | Object | Source Count | Load File | Notes |
|------|--------|-------------|-----------|-------|
| 1 | Pricebook2 (custom only) | | wave1_pricebook2.csv | Standard pricebook auto-created |
| 1 | SBQQ__DiscountCategory__c | | wave1_discount_category.csv | |
| 2 | Product2 (pass 1 — no self-refs) | | wave2a_product2.csv | |
| 2 | Product2 (pass 2 — self-ref UPDATE) | | wave2b_product2_selfref.csv | Only if self-refs present |
| 2 | SBQQ__PriceRule__c | | wave2c_price_rule.csv | |
| 3 | PricebookEntry (Standard PBE) | | wave3a_std_pbe.csv | Must precede custom PBE |
| 3 | PricebookEntry (custom pricebooks) | | wave3b_custom_pbe.csv | |
| 3 | SBQQ__DiscountSchedule__c | | wave3c_discount_schedule.csv | |
| 3 | SBQQ__DiscountTier__c | | wave3d_discount_tier.csv | |
| 4 | SBQQ__ProductOption__c | | wave4a_product_option.csv | |
| 4 | SBQQ__PriceAction__c | | wave4b_price_action.csv | |
| 5 | SBQQ__ConfigurationAttribute__c | | wave5a_config_attribute.csv | |
| 5 | SBQQ__OptionConstraint__c | | wave5b_option_constraint.csv | |

---

## Wave Execution Log

Record actual outcome for each wave as it completes.

| Wave | Object | Rows Submitted | Rows Succeeded | Rows Failed | Completed? |
|------|--------|---------------|---------------|-------------|-----------|
| 1 | Pricebook2 | | | | |
| 1 | SBQQ__DiscountCategory__c | | | | |
| 2 | Product2 pass 1 | | | | |
| 2 | Product2 pass 2 (self-refs) | | | | |
| 2 | SBQQ__PriceRule__c | | | | |
| 3 | PricebookEntry (Standard) | | | | |
| 3 | PricebookEntry (custom) | | | | |
| 3 | SBQQ__DiscountSchedule__c | | | | |
| 3 | SBQQ__DiscountTier__c | | | | |
| 4 | SBQQ__ProductOption__c | | | | |
| 4 | SBQQ__PriceAction__c | | | | |
| 5 | SBQQ__ConfigurationAttribute__c | | | | |
| 5 | SBQQ__OptionConstraint__c | | | | |

---

## Post-Load Validation Checklist

Run all queries before re-enabling CPQ triggers.

- [ ] **PriceAction orphan check** — zero rows required:
  ```soql
  SELECT Id, Name, SBQQ__PriceRule__c FROM SBQQ__PriceAction__c WHERE SBQQ__PriceRule__c = null
  ```
  Result: ___ rows

- [ ] **ProductOption FK integrity** — compare count to source:
  ```soql
  SELECT COUNT() FROM SBQQ__ProductOption__c WHERE Migration_ExternalId__c != null
  ```
  Result: ___ (should equal source count: ___)

- [ ] **DiscountSchedule count** — compare to source:
  ```soql
  SELECT COUNT() FROM SBQQ__DiscountSchedule__c WHERE Migration_ExternalId__c != null
  ```
  Result: ___ (should equal source count: ___)

- [ ] **OptionConstraint count** — compare to source:
  ```soql
  SELECT COUNT() FROM SBQQ__OptionConstraint__c WHERE Migration_ExternalId__c != null
  ```
  Result: ___ (should equal source count: ___)

- [ ] **ConfigurationAttribute count** — compare to source:
  ```soql
  SELECT COUNT() FROM SBQQ__ConfigurationAttribute__c WHERE Migration_ExternalId__c != null
  ```
  Result: ___ (should equal source count: ___)

---

## CPQ Trigger Re-Enable

- [ ] All validation queries above show zero orphans and correct row counts
- [ ] CPQ triggers re-enabled: navigate to CPQ Additional Settings > set "Triggers Disabled" = false
- [ ] Confirmed re-enable via SOQL:
  `SELECT SBQQ__TriggerAutoRuns__c FROM SBQQ__PackageSettings__c LIMIT 1` → value: ___

---

## Smoke Test Results

Generate at least one test quote in the target org after trigger re-enable.

| Test Scenario | Expected Result | Actual Result | Pass? |
|--------------|----------------|--------------|-------|
| Quote with bundle containing options | Options render, pricing calculates | | |
| Quote with product having a price rule | Price rule fires, adjusts line price | | |
| Quote with product on discount schedule | Volume discount tier applies | | |
| Quote with configuration attribute | Attribute displays and saves | | |

---

## Rollback Plan

If migration fails and rollback is required:

1. Disable CPQ triggers (if not already disabled)
2. Delete all SBQQ-namespaced records loaded in this migration run using the migration external ID field as an identifier: `WHERE Migration_ExternalId__c != null`
3. Delete Product2 records inserted in this migration (identified by external ID field)
4. Confirm target org returns to pre-migration state via row count queries
5. Document failure mode and root cause before retry

**Rollback decision point:** If three or more wave failures occur without resolution, escalate before proceeding. Partial loads with orphaned records in the target are harder to roll back than a clean wipe and retry.

---

## Notes

(Record any deviations from the standard pattern, one-off decisions made during the migration, and why.)

