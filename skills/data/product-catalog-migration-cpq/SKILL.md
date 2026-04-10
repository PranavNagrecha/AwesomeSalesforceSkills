---
name: product-catalog-migration-cpq
description: "Use when bulk-loading or migrating Salesforce CPQ product catalog configuration data — SBQQ-namespaced objects including Product2, ProductOption, PriceRule, PriceAction, DiscountSchedule, DiscountCategory, ConfigurationAttribute, and OptionConstraint — across orgs or from an external source system. Trigger keywords: CPQ bulk load, SBQQ product migration, ProductOption insert order, CPQ trigger disable, price rule migration, CPQ sandbox refresh catalog, bundle migration. NOT for standard product import or CRM product migration (use product-catalog-data-model). NOT for CPQ quote or subscription data migration. NOT for Industries CPQ (Vlocity) catalog migration."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Performance
triggers:
  - "I need to migrate CPQ product bundles and options from one org to another and my inserts are failing with foreign key errors"
  - "How do I disable CPQ triggers before a bulk load so I don't hit CPU limits or unexpected automation?"
  - "My price actions loaded successfully but quote calculation fails silently — there are no errors on insert but prices are wrong at runtime"
  - "What is the correct dependency sequence for loading SBQQ objects: product options, discount schedules, price rules, configuration attributes?"
  - "ProductOption insert fails because the parent or child product does not exist yet — how do I handle bundle self-references in CPQ?"
  - "How do I load CPQ configuration attributes and option constraints after migrating the base product catalog?"
tags:
  - cpq
  - sbqq
  - product-migration
  - bulk-load
  - product-option
  - price-rule
  - discount-schedule
  - bundle-migration
  - data-loading
  - configuration-attribute
inputs:
  - "Source org or system containing the CPQ product catalog to be migrated"
  - "List of SBQQ-namespaced objects in scope: which bundles, options, price rules, discount schedules, configuration attributes, option constraints"
  - "Tooling choice: Data Loader, Bulk API 2.0, or custom Apex/REST import scripts"
  - "External ID strategy: whether source org record IDs or external identifiers are used for FK resolution"
  - "CPQ managed package version in both source and target orgs"
outputs:
  - "Ordered load plan with SBQQ object dependency sequence and per-wave file list"
  - "Pre-load checklist: CPQ trigger disable steps, Additional Settings configuration, external ID field mapping"
  - "Two-pass insert strategy for Product2 self-referencing bundle parent/child relationships"
  - "Price action validation query to detect orphaned actions before go-live"
  - "Completed product-catalog-migration-cpq-template.md with migration scope, wave plan, and rollback approach"
dependencies:
  - product-catalog-data-model
  - cpq-data-model
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Product Catalog Migration CPQ

This skill activates when a practitioner must bulk-load or migrate Salesforce CPQ product catalog configuration data — SBQQ-namespaced objects including Product2 bundles, ProductOption, PriceRule, PriceAction, DiscountSchedule, DiscountCategory, ConfigurationAttribute, and OptionConstraint — across orgs or from an external system. It defines the mandatory dependency sequence, explains why CPQ automation must be suspended before bulk loads, and covers the two-pass insert pattern for self-referencing Product2 bundle hierarchies. It does NOT cover CPQ quote or subscription data migration, standard (non-CPQ) product import, or Industries CPQ (Vlocity) catalog migration.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Installed package version**: Confirm the Salesforce CPQ managed package (namespace `SBQQ`) is installed in the target org. Check Setup > Installed Packages. Note the version — field availability on SBQQ objects can differ between releases. Source and target versions should be the same major release wherever possible.
- **CPQ Additional Settings**: Before any bulk DML, navigate to CPQ Setup > Additional Settings and enable the "Triggers Disabled" flag. Failure to do this causes CPQ pricing triggers to fire on every record insert, consuming CPU time at scale and potentially corrupting intermediate states.
- **External ID strategy**: Determine how FK relationships between SBQQ objects will be resolved across orgs. Source org record IDs are not valid in the target org. Every parent record must be inserted first and its new target ID captured before child records can reference it. Alternatively, set an External ID field (e.g., a custom `ExternalId__c`) on each object and use upsert operations.
- **Most common wrong assumption**: Practitioners assume CPQ objects can be loaded in any order as long as parent records precede children. In CPQ, this is not sufficient. ProductOption depends on both the parent product (the bundle) AND the child product (the option product) both existing as Product2 records before the ProductOption row can be inserted. Partial ordering causes FK failures that are not always surfaced at insert time.
- **Silent FK failures on PriceAction**: PriceAction records reference a parent SBQQ__PriceRule__c. If a PriceAction is inserted without its parent PriceRule existing in the target org, the insert may succeed (the FK constraint is enforced at the managed-package layer, not always at the platform DML layer) but the action is orphaned. The failure only surfaces when a quote is calculated — price rule logic silently does nothing, producing incorrect pricing with no insert-time error.
- **Product2 self-references for bundles**: CPQ bundles are standard Product2 records. The bundle parent/child relationship is expressed through SBQQ__ProductOption__c, which has both `SBQQ__ConfiguredSKU__c` (the bundle/parent product) and `SBQQ__Product__c` (the option/child product). When migrating bundles where the same product is both a bundle and an option in another bundle, all Product2 records must be inserted first, then ProductOption records in a second pass.

---

## Core Concepts

### Strict Dependency Sequence for SBQQ Objects

CPQ configuration data has a strict load sequence driven by FK dependencies across managed-package objects. Loading out of order produces either immediate DML errors (hard FK violations) or silent runtime failures (soft dependency violations caught only during quote calculation).

The canonical sequence is:

**Wave 1 — Foundation (no SBQQ dependencies):**
- `Pricebook2` — custom pricebooks must exist before PricebookEntry
- `SBQQ__DiscountCategory__c` — referenced by DiscountSchedule; has no SBQQ parent

**Wave 2 — Core product and pricing rules (depends on Wave 1):**
- `Product2` — all products including bundle parents and option products; self-references handled via two-pass
- `SBQQ__PriceRule__c` — price rules have no SBQQ parent; they are referenced by PriceAction

**Wave 3 — Product pricing and discount structures (depends on Wave 2):**
- `PricebookEntry` — requires Product2 and Pricebook2; standard PBE must precede custom PBE for each product
- `SBQQ__DiscountSchedule__c` — references DiscountCategory; contains discount tiers

**Wave 4 — Bundle structure and pricing actions (depends on Wave 2 and Wave 3):**
- `SBQQ__ProductOption__c` — requires both bundle parent Product2 AND option Product2 to already exist
- `SBQQ__PriceAction__c` — requires parent SBQQ__PriceRule__c; load after all price rules are confirmed in target

**Wave 5 — Bundle configuration (depends on Wave 4):**
- `SBQQ__ConfigurationAttribute__c` — references ProductOption and Product2
- `SBQQ__OptionConstraint__c` — references ProductOption records; both constrained and constraining options must exist

### Product2 Self-References and the Two-Pass Pattern

CPQ bundles are standard Product2 records. A product can be a bundle parent in one configuration and a standalone option product in another. Because ProductOption holds FKs to both parent and child Product2 records, all Product2 rows must exist in the target before any ProductOption rows are inserted.

When the source contains products that are simultaneously bundles (they appear as `SBQQ__ConfiguredSKU__c` in ProductOption) and option products (they appear as `SBQQ__Product__c` in ProductOption for other bundles), there is a circular reference at the Product2 level that cannot be resolved in a single insert pass.

**Two-pass strategy:**
1. **Pass 1 (INSERT):** Insert all Product2 records without the `SBQQ__NewQuoteProcess__c` or any self-referencing field. Capture the new target IDs via External ID upsert or post-insert query.
2. **Pass 2 (UPDATE):** For any Product2 field that references another Product2 (e.g., `SBQQ__UpgradeTarget__c`, which links a product to its upgrade-path product), run a separate update file after all Product2 records exist. This resolves self-references without needing a second full insert.

### CPQ Trigger Architecture and the Disable Requirement

Salesforce CPQ installs managed-package triggers on Product2, SBQQ__Quote__c, SBQQ__QuoteLine__c, and related objects. These triggers run the CPQ pricing engine, validate bundle configurations, and maintain denormalized pricing fields. During a bulk load of catalog data — where records are inserted in controlled waves and pricing integrity is intentionally deferred — these triggers cause three categories of problems:

1. **CPU time limit errors**: CPQ pricing triggers are expensive. At bulk scale (thousands of Product2 or ProductOption records), triggers push individual transactions toward or past the 10-second CPU limit.
2. **False validation failures**: CPQ trigger validations check for bundle completeness and price consistency. Intermediate states during a multi-wave load are intentionally incomplete — triggering validation at each wave fires false errors.
3. **Cascading recalculations**: Inserting a ProductOption triggers a recalculation cascade that attempts to reprice any existing quotes referencing the parent bundle. In non-empty target orgs, this causes unexpected side effects.

**To disable CPQ triggers before a bulk load:** Navigate to CPQ Setup (the "Salesforce CPQ" app, then Configure > Additional Settings). Set "Triggers Disabled" to `true`. Re-enable after the load completes and after running a post-load validation query.

### Price Action and Price Rule Dependency (Silent FK Failure)

`SBQQ__PriceAction__c` records define the pricing modifications applied when a price rule condition is met. Each PriceAction has a mandatory lookup to its parent `SBQQ__PriceRule__c`. Unlike standard Salesforce lookup fields, this relationship is managed and validated by the CPQ package at quote-calculation time, not at the platform DML layer.

This means: a PriceAction can be inserted into the database with a null or stale `SBQQ__PriceRule__c` lookup value and the insert will not fail with a platform error. The FK is not enforced as a hard database constraint visible to the Bulk API or Data Loader. The orphaned PriceAction is silently ignored during quote calculation — the price rule never fires, pricing is wrong, and there is no error in the CPQ log visible to the loading tool.

**Prevention:** Always load all `SBQQ__PriceRule__c` records and confirm their target IDs before loading any `SBQQ__PriceAction__c` records. After the load, run a validation SOQL query to detect orphans (see Decision Guidance below).

### Bundle Option Constraints and Configuration Attribute Dependencies

`SBQQ__OptionConstraint__c` enforces conditional visibility or selectability rules between two ProductOption records within a bundle — the "constraining option" and the "constrained option". Both referenced ProductOption records must exist before the OptionConstraint row can be inserted.

`SBQQ__ConfigurationAttribute__c` maps a custom attribute to a product or product option within a bundle configuration. It references both the bundle Product2 and a specific ProductOption. It must be loaded after both the Product2 and ProductOption waves are complete.

Both objects are Wave 5 and must not be batched into Wave 4 even if their parent ProductOption records were inserted in the same job.

---

## Common Patterns

### Pattern: External ID Upsert for Cross-Org FK Resolution

**When to use:** Any migration between two Salesforce orgs where source record IDs are meaningless in the target.

**How it works:**
1. Add a custom text field (e.g., `Migration_ExternalId__c`, or use an existing external system key) to each SBQQ object being migrated. Mark it as External ID and Unique.
2. Export source records with the source record ID captured in the external ID field.
3. In each load file, replace the FK columns (e.g., `SBQQ__PriceRule__c`) with relationship notation pointing to the external ID: `SBQQ__PriceRule__r.Migration_ExternalId__c`. This allows Data Loader and Bulk API 2.0 to resolve FKs using the external ID rather than the org-specific Salesforce ID.
4. Upsert each wave using the external ID field as the upsert key.

**Why not direct ID mapping:** A manual ID-to-ID mapping table requires maintaining a cross-reference CSV updated after every wave insert. Relationship notation with external IDs delegates resolution to the platform and eliminates the mapping table entirely.

### Pattern: Pre-Load PriceAction Orphan Check

**When to use:** After loading PriceRule and PriceAction waves, before re-enabling CPQ triggers.

**How it works:** Run this SOQL via the Developer Console or a script:

```soql
SELECT Id, Name, SBQQ__PriceRule__c
FROM SBQQ__PriceAction__c
WHERE SBQQ__PriceRule__c = null
```

Any returned records are orphaned PriceActions. Investigate whether the parent PriceRule failed to load or whether the FK was not resolved correctly. Do not re-enable CPQ triggers until this query returns zero rows.

**Why not wait for quote testing:** Silent FK failures in PriceActions only appear during quote calculation, which may not be tested on every product permutation during UAT. A pre-go-live SOQL check finds all orphans in one query, regardless of how many quote tests are run.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Loading ProductOption when some option products are also bundles | Two-pass: insert all Product2 first, then ProductOption | ProductOption requires both ConfiguredSKU and Product FK to resolve; single-pass fails if child product not yet inserted |
| FK resolution for SBQQ objects across orgs | External ID upsert with relationship notation | Avoids manual ID mapping table; platform resolves FKs at upsert time |
| CPQ triggers fire during bulk load and hit CPU limit | Disable triggers in CPQ Additional Settings before any DML | CPQ pricing triggers are expensive at scale; disable is a supported configuration, not a hack |
| PriceAction records load without error but prices are wrong on quotes | Run orphan detection SOQL before go-live | Platform does not enforce PriceRule FK at DML layer; orphan detection must be explicit |
| ConfigurationAttribute insert fails with FK error even though ProductOption exists | Check wave ordering — ConfigurationAttribute must be Wave 5, after ProductOption wave commits | Bulk API jobs are async; next wave must not start until previous job is confirmed complete |
| DiscountSchedule inserts successfully but schedule tiers are not applied | Confirm DiscountCategory was loaded in Wave 1 and tier records reference the correct DiscountSchedule ID | DiscountTier (SBQQ__DiscountTier__c) is a child of DiscountSchedule; load after DiscountSchedule completes |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner migrating a CPQ product catalog:

1. **Audit source catalog and classify objects by wave**: Export all SBQQ-namespaced objects from the source org. Group them by the dependency sequence: Wave 1 (Pricebook2, DiscountCategory), Wave 2 (Product2, PriceRule), Wave 3 (PricebookEntry, DiscountSchedule, DiscountTier), Wave 4 (ProductOption, PriceAction), Wave 5 (ConfigurationAttribute, OptionConstraint). Identify any Product2 records that appear in both ConfiguredSKU and Product columns of ProductOption — these require the two-pass insert strategy.

2. **Prepare the target org and disable CPQ triggers**: Confirm the CPQ managed package is installed at the same version as the source org. Navigate to CPQ Additional Settings and set "Triggers Disabled" to `true`. Add External ID fields to each SBQQ object if not already present. Do not proceed to loading until trigger disable is confirmed.

3. **Execute Wave 1 — foundation objects**: Load Pricebook2 (custom pricebooks only; standard pricebook is auto-created) and SBQQ__DiscountCategory__c. Confirm all rows succeeded before proceeding.

4. **Execute Wave 2 — products and price rules (two-pass for Product2 if needed)**: Insert all Product2 records. If any products have self-referencing fields (e.g., SBQQ__UpgradeTarget__c pointing to another Product2), leave those fields blank in the first insert and execute a second UPDATE pass after all Product2 records are confirmed in the target. Load SBQQ__PriceRule__c records in the same wave after Product2 completes.

5. **Execute Wave 3 — pricing and discount structures**: Load PricebookEntry (Standard PBE before custom PBE for each product), SBQQ__DiscountSchedule__c, and SBQQ__DiscountTier__c. Confirm all rows succeeded and FK resolution is clean.

6. **Execute Wave 4 — bundle structure and price actions**: Load SBQQ__ProductOption__c with both ConfiguredSKU and Product FKs resolved via external ID relationship notation. Load SBQQ__PriceAction__c after all PriceRule records are confirmed. Run the orphan detection SOQL (`WHERE SBQQ__PriceRule__c = null`) on PriceAction records before continuing.

7. **Execute Wave 5, re-enable triggers, and validate**: Load SBQQ__ConfigurationAttribute__c and SBQQ__OptionConstraint__c. After all waves succeed, re-enable CPQ triggers in Additional Settings. Generate a test quote in the target org covering at least one bundle with options, one product with a discount schedule, and one product with an active price rule. Confirm line prices, discounts, and configuration attribute rendering match the source org.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] CPQ triggers were disabled in Additional Settings before any bulk DML and re-enabled only after all waves completed
- [ ] Product2 self-referencing fields (e.g., SBQQ__UpgradeTarget__c) were handled with a two-pass insert + update strategy
- [ ] SBQQ__PriceAction__c orphan detection SOQL returned zero rows before triggers were re-enabled
- [ ] PricebookEntry load included Standard Pricebook entries before custom pricebook entries for each product
- [ ] Wave 5 objects (ConfigurationAttribute, OptionConstraint) were not loaded until Wave 4 jobs were confirmed complete
- [ ] A test quote was generated covering a bundle with options, a discount schedule, and at least one active price rule
- [ ] External ID fields were used for all cross-org FK resolution instead of direct Salesforce ID mapping

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **CPQ trigger disable is not org-wide persistent** — The "Triggers Disabled" flag in CPQ Additional Settings is a managed-package configuration record, not a metadata setting. It is stored in the org's data layer. If a sandbox refresh occurs mid-migration or the setting is changed by another admin, triggers re-enable silently. Confirm the setting immediately before each load wave, not just at the start of the migration.

2. **PriceAction FK failure is invisible at insert time** — The SBQQ__PriceRule__c lookup on PriceAction is not enforced as a hard database constraint by the platform. Orphaned PriceActions insert without error and only fail silently during quote calculation. Standard Bulk API 2.0 success responses do not indicate whether the FK value is valid in the CPQ domain.

3. **ProductOption requires both parent AND child Product2 to exist** — This is the most common single-pass failure. A ProductOption row has two required Product2 FKs: SBQQ__ConfiguredSKU__c (the bundle) and SBQQ__Product__c (the option product). Loading ProductOptions in the same wave as Product2 records (even if the Product2 records are in the same job, earlier in the file) fails because Bulk API processes rows in batches, not sequentially row-by-row.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Wave load plan | Ordered list of SBQQ objects grouped by wave with per-wave row counts and external ID field mapping |
| Pre-load checklist | CPQ trigger disable confirmation, external ID field setup, and source export validation steps |
| Post-load validation queries | SOQL queries for PriceAction orphan detection, ProductOption FK verification, and DiscountSchedule tier count comparison |
| product-catalog-migration-cpq-template.md | Filled work template capturing scope, wave plan, and rollback approach |

---

## Related Skills

- `product-catalog-data-model` — use for standard Salesforce Product2/Pricebook2/PricebookEntry load sequencing when CPQ is not installed
- `cpq-data-model` — use when querying or building against SBQQ__ objects programmatically (quote, subscription, pricing engine)
- `data-migration-planning` — use when this CPQ catalog load is part of a broader multi-object migration with rollback and cutover planning
- `cpq-architecture-patterns` — use when designing the CPQ configuration structure before migration, not during the load itself
