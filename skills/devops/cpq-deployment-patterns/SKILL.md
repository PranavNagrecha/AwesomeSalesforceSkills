---
name: cpq-deployment-patterns
description: "Use when deploying Salesforce CPQ configuration between environments in a CI/CD pipeline — covers the required data record dependency order (Price Books > Products > Price Rules > Product Rules > Quote Templates), External ID-based cross-org matching, multi-pass deployment for self-referential lookups, and the distinction between CPQ metadata deployment and CPQ data deployment. NOT for generic SFDX metadata deployment, CPQ implementation configuration, or Salesforce Billing deployment."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "How do I deploy CPQ configuration between Salesforce environments in CI/CD?"
  - "CPQ product rules and price rules not deploying correctly with change sets"
  - "What is the correct load order for CPQ data deployment between orgs?"
  - "CPQ External IDs for cross-org matching during data migration"
  - "How to handle self-referential CPQ record lookups in deployment scripts"
tags:
  - CPQ
  - deployment
  - data-deployment
  - devops
  - External-ID
  - price-rules
inputs:
  - "CPQ configuration scope: Price Books, Products, Price Rules, Product Rules, Quote Templates, Discount Categories"
  - "Source and target org access for data extraction and load"
  - "External ID field availability on CPQ objects for cross-org matching"
outputs:
  - "CPQ data deployment load order plan with dependency documentation"
  - "External ID strategy for cross-org record matching"
  - "Multi-pass deployment script for self-referential CPQ records"
  - "Validation SOQL set to confirm CPQ configuration post-deployment"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# CPQ Deployment Patterns

This skill activates when a practitioner needs to deploy Salesforce CPQ configuration between environments (sandbox to production, or sandbox to sandbox) as part of a CI/CD pipeline. CPQ configuration lives primarily as data records — not as metadata — and cannot be deployed with standard change sets or the Salesforce CLI Metadata API alone. This skill covers the required record load order, External ID strategy for cross-org matching, and multi-pass patterns for self-referential lookups.

---

## Before Starting

Gather this context before working on anything in this domain:

- CPQ configuration (Price Books, Products, Price Rules, Product Rules, Quote Templates, Option Constraints) exists as data records in standard and custom objects, not as deployable Salesforce metadata. SFDX deploy and change sets cannot move CPQ configuration data.
- CPQ data deployment requires a separate data deployment step using SFDMU (Salesforce Data Move Utility), Copado Data Deploy, Prodly, or Data Loader with External IDs as cross-org matching keys.
- The CPQ Quote Calculation Sequence determines the order in which configuration records are evaluated — the deployment must respect dependencies in the same way.
- Objects with self-referential lookups (e.g., Option Groups referencing parent Option Groups) require a multi-pass deployment: insert base records first with the self-reference field null, then update the self-reference field in a second pass.

---

## Core Concepts

### CPQ Configuration Lives as Data, Not Metadata

Standard Salesforce deployment tools (Change Sets, sf deploy, Metadata API) move Salesforce metadata (Apex classes, custom fields, page layouts). CPQ configuration records — the actual products, pricing rules, and quote templates — live in the Salesforce data layer (standard objects like `Product2`, `Pricebook2`, `PricebookEntry`, and CPQ custom objects like `SBQQ__PricingRule__c`, `SBQQ__ProductRule__c`).

These records must be moved using data migration tools, not metadata deployment tools. A release pipeline for CPQ orgs requires two distinct steps:
1. **Metadata deployment** (Apex, LWC, custom objects, fields) — standard sf CLI or change sets
2. **Data deployment** (CPQ configuration records) — SFDMU, Copado Data Deploy, Prodly, or Data Loader with External IDs

### Required CPQ Data Load Order

The CPQ Quote Calculation Sequence drives the required deployment dependency order:

1. **Pricebook2 and Discount Category** — No dependencies. Load first.
2. **Product2** — References Pricebook2 via PricebookEntry. Load Product2 first, then PricebookEntry.
3. **PricebookEntry** — References Product2 and Pricebook2. Both must exist.
4. **SBQQ__PricingRule__c (Price Rules)** — May reference Products and Price Books. Load after Products.
5. **SBQQ__ProductRule__c (Product Rules)** — References Products and may reference Pricing Rules. Load after both.
6. **SBQQ__QuoteTemplate__c (Quote Templates)** — May reference Product Records and Line Item fields. Load last.

Loading in any other order produces INVALID_CROSS_REFERENCE_KEY errors for records with unresolved foreign keys.

### External IDs for Cross-Org Record Matching

Record IDs (18-character Salesforce IDs) are org-specific — the same logical CPQ Product has a different ID in sandbox vs. production. Cross-org data deployment requires an External ID field as the cross-org matching key:

- Add a custom External ID field (`CPQ_External_Id__c`) to each CPQ object in both source and target orgs
- Populate External ID values in the source org before extraction
- Use the External ID field as the matching key in SFDMU or Data Loader upsert operations
- Reference External IDs in parent lookup fields during load: `Product2.CPQ_External_Id__c`

### Multi-Pass Deployment for Self-Referential Lookups

Some CPQ objects have self-referential lookups (e.g., Option Groups with parent Option Group). Single-pass loads fail because the parent record doesn't exist yet when the child record is being inserted. The multi-pass pattern:

1. Insert all records with the self-reference field set to null
2. Update the self-reference field in a second pass once all records exist

SFDMU handles this automatically with its `selfParentExternalIdFieldName` configuration. Manual approaches require two separate load operations.

---

## Common Patterns

### Pattern 1: Full CPQ Configuration Deployment via SFDMU

**When to use:** Moving a full CPQ configuration set (all Price Books, Products, Rules, Templates) from sandbox to production.

**How it works:**
1. Configure SFDMU `export.json` with the CPQ objects in the required load order
2. Set External ID fields as upsert matching keys for each object
3. Set parent reference fields to use External ID resolution (e.g., `"SBQQ__Product__r.CPQ_External_Id__c"`)
4. Run SFDMU: `sf data:export:tree` from source, then `sf data:import:tree` to target
5. Validate with SOQL: confirm record counts and key relationship traversals

### Pattern 2: Incremental CPQ Configuration Update

**When to use:** Adding new products or price rules to an existing production org without re-deploying the full catalog.

**How it works:**
1. Identify new or changed records since last deployment (filter by LastModifiedDate or a deployment flag)
2. Export only the delta records in dependency order
3. Upsert using External IDs — existing records are updated, new records are inserted
4. Validate that new records are correctly associated with existing parent records

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| First-time full CPQ config deployment | SFDMU full export/import with External IDs | Handles all CPQ objects with dependency ordering |
| Incremental product/rule addition | SFDMU incremental upsert with External IDs | Avoids full re-deployment for small changes |
| Self-referential lookup objects | Multi-pass: insert null → update reference | Single-pass fails because parent doesn't exist yet |
| CPQ metadata (custom objects/fields) | Standard sf CLI deploy | Metadata and data are separate deployment steps |
| Using change sets for CPQ config data | Not supported — change sets deploy metadata only | CPQ config is data, not metadata |

---

## Recommended Workflow

1. **Confirm External ID field availability** — Verify a custom External ID field exists on all CPQ objects in both source and target orgs. Populate the External ID in the source org if it is empty.
2. **Document the load order** — Map out all CPQ objects to deploy and their dependencies. Follow: Pricebook2 > Product2 > PricebookEntry > Price Rules > Product Rules > Quote Templates.
3. **Export configuration from source** — Use SFDMU or Data Loader to extract records in dependency order with External ID values included.
4. **Validate extracted data** — Confirm External ID coverage (no blanks), confirm parent IDs reference valid records, confirm the record count matches source.
5. **Deploy to target in load order** — Use SFDMU or Data Loader upsert with External ID matching keys. Process objects one at a time in dependency order.
6. **Handle self-referential records** — For objects with self-references, use SFDMU's `selfParentExternalIdFieldName` or implement a two-pass manual approach.
7. **Validate post-deployment** — Run SOQL to confirm record counts, confirm Price Rule and Product Rule associations to Products, run a test CPQ quote in the target org to confirm calculation behavior.

---

## Review Checklist

- [ ] External ID fields present on all CPQ objects in source and target orgs
- [ ] External IDs populated for all records before extraction
- [ ] Load order follows CPQ dependency sequence
- [ ] Metadata deployment (custom objects, fields) completed before data deployment
- [ ] Self-referential objects use multi-pass approach
- [ ] Post-deployment test quote runs without calculation errors in target org
- [ ] Price Rule and Product Rule associations confirmed via SOQL

---

## Salesforce-Specific Gotchas

1. **Change sets and sf deploy cannot move CPQ configuration data** — These tools deploy metadata. CPQ configuration records are data. A release pipeline that deploys only the metadata artifact succeeds but leaves CPQ configuration missing in the target org. CPQ data deployment is a required separate pipeline step.
2. **Record IDs are org-specific — hardcoded IDs cause INVALID_CROSS_REFERENCE_KEY** — Product IDs, Price Book IDs, and Rule IDs from the source org are different in the target org. Any CPQ data plan that hardcodes source org IDs will fail with INVALID_CROSS_REFERENCE_KEY errors at load time. External ID fields are the only safe cross-org reference mechanism.
3. **Self-referential CPQ lookups fail on single-pass load** — Objects like Option Groups with parent-child self-references cannot be loaded in a single pass because the parent record doesn't exist when the child record is being inserted. Multi-pass is mandatory for these objects.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CPQ data deployment load order plan | Object sequence with dependency documentation |
| SFDMU export.json configuration | SFDMU config file for CPQ objects with External ID and parent resolution |
| External ID population script | Data Loader or SOQL-based script to populate External IDs in source org |
| Validation SOQL set | Queries to confirm record counts and relationship integrity post-deployment |

---

## Related Skills

- `devops/cpq-deployment-administration` — For CPQ sandbox setup and administration between deployments
- `data/deployment-data-dependencies` — For general data record deployment with cross-org ID remapping
- `devops/managed-package-development` — For managed package patterns related to CPQ ISV packages
