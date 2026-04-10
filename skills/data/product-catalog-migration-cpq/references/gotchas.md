# Gotchas — Product Catalog Migration CPQ

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: CPQ Triggers Must Be Disabled Before Bulk Loads — and the Setting Can Reset Without Warning

**What happens:** CPQ installs managed-package triggers on Product2, SBQQ__Quote__c, SBQQ__QuoteLine__c, and related objects. When these triggers are active during a bulk insert of ProductOption or PriceRule records, the CPQ pricing engine fires on each batch. At scale (thousands of records), this pushes transactions toward or past the 10-second CPU governor limit, causing bulk jobs to fail partway through. Even at lower volumes, the pricing engine validates bundle completeness and fires recalculations against any existing quotes that reference the products being loaded — creating unexpected side effects in non-empty target orgs.

**When it occurs:** Any bulk DML operation against SBQQ-namespaced objects when "Triggers Disabled" is not set to `true` in CPQ Additional Settings. Also occurs when a sandbox refresh resets the Additional Settings record to its default state (triggers enabled), mid-migration.

**How to avoid:** Before every load wave, query the CPQ Additional Settings record and confirm the trigger disable flag is active:

```soql
SELECT SBQQ__TriggerAutoRuns__c
FROM SBQQ__PackageSettings__c
WHERE SetupOwnerId = '<org_id>'
LIMIT 1
```

If `SBQQ__TriggerAutoRuns__c` is `false`, triggers are disabled (the field name is inverted — `false` = triggers disabled). Re-confirm before each wave, not just at migration start.

---

## Gotcha 2: Product2 Self-Referencing Fields Require a Two-Pass Load — Single-Pass Always Fails

**What happens:** Product2 records in CPQ orgs can reference other Product2 records via lookup fields such as `SBQQ__UpgradeTarget__c` (the product this product upgrades to). When all Product2 records are being inserted for the first time in a target org, none of them exist yet when the insert job runs. Any row with a populated self-referencing field fails with a FK error because the target product it references does not yet exist in the target org.

**When it occurs:** Any CPQ catalog migration where products have upgrade path relationships, replacement product relationships, or any other Product2-to-Product2 lookup fields. This is common in SaaS product catalogs where product tiers are linked.

**How to avoid:** Use a two-pass strategy:
1. **Pass 1 (INSERT):** Insert all Product2 records with self-referencing fields left blank (`null`).
2. **Pass 2 (UPDATE):** After all Product2 records are confirmed in the target and their new Salesforce IDs are captured (via post-insert query on the external ID field), run a separate UPDATE file that populates the self-referencing fields using the new target IDs.

This guarantees every referenced product exists before its FK is populated.

---

## Gotcha 3: PriceAction FK to PriceRule Is Not Enforced at the DML Layer — Orphans Insert Silently

**What happens:** `SBQQ__PriceAction__c` has a lookup to `SBQQ__PriceRule__c`. Unlike standard Salesforce lookup fields (which enforce referential integrity at the platform layer and return a FIELD_INTEGRITY_EXCEPTION on bad FK values), this managed-package relationship is validated by the CPQ pricing engine at quote calculation time, not at DML time. A PriceAction can be inserted with a null or stale SBQQ__PriceRule__c value and the Bulk API job reports success. The orphaned PriceAction is stored in the database but silently ignored when the pricing engine evaluates rules — the rule never fires, prices are wrong, and no error is surfaced in any log visible to the migration tooling.

**When it occurs:** When PriceAction records are loaded before their parent PriceRule records exist in the target, or when external ID FK resolution fails silently (e.g., the relationship notation column is mis-named or the external ID field is not indexed).

**How to avoid:** Always load SBQQ__PriceRule__c records as a complete wave before loading SBQQ__PriceAction__c records. After the PriceAction load, run the orphan detection SOQL before re-enabling CPQ triggers:

```soql
SELECT Id, Name, SBQQ__PriceRule__c
FROM SBQQ__PriceAction__c
WHERE SBQQ__PriceRule__c = null
```

Zero rows is the required gate. If any rows are returned, diagnose and re-load before proceeding.

---

## Gotcha 4: OptionConstraint References Two ProductOption Records — Both Must Exist Before Insert

**What happens:** `SBQQ__OptionConstraint__c` has two required ProductOption lookups: `SBQQ__ConstrainedOption__c` (the option that is hidden or disabled) and `SBQQ__ConstrainingOption__c` (the option that triggers the constraint). Both referenced ProductOption records must exist in the target org before the OptionConstraint row can be inserted. Practitioners who load OptionConstraint in the same wave as ProductOption — relying on row ordering within a file — encounter sporadic FK failures because Bulk API batch boundaries do not guarantee row-level commit sequencing within a job.

**When it occurs:** When OptionConstraint records are included in Wave 4 alongside ProductOption records, or when the ProductOption wave has not fully committed before the OptionConstraint job starts.

**How to avoid:** Place OptionConstraint in Wave 5, strictly after the Wave 4 ProductOption job is confirmed complete. Confirm completion by querying `SELECT COUNT() FROM SBQQ__ProductOption__c WHERE Migration_ExternalId__c != null` and comparing to source row count before starting Wave 5.

---

## Gotcha 5: DiscountSchedule Tiers Require DiscountCategory to Exist First — and Category Is Often Overlooked

**What happens:** `SBQQ__DiscountSchedule__c` references `SBQQ__DiscountCategory__c` via a lookup field. DiscountCategory is a small, often overlooked object — practitioners commonly export it as an afterthought or skip it assuming it is a standard object. If DiscountCategory records are not loaded in Wave 1 (before DiscountSchedule), the DiscountSchedule insert fails with FK errors. Because DiscountCategory records are few (typically under 20), practitioners may not notice them in a source export and load the schedules without them.

**When it occurs:** When DiscountCategory is not included in the Wave 1 export, or when the migration scope document omits it.

**How to avoid:** Always include `SELECT Id, Name, SBQQ__Code__c FROM SBQQ__DiscountCategory__c` in the source export and confirm DiscountCategory rows are in Wave 1 before DiscountSchedule rows appear in Wave 3. The category count in the target must equal the category count in the source before the DiscountSchedule job starts.
