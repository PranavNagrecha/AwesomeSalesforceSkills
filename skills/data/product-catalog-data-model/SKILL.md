---
name: product-catalog-data-model
description: "Use when modeling, loading, or troubleshooting Salesforce product and pricebook data — covering the Product2 → Pricebook2 → PricebookEntry three-object chain, standard pricebook constraints, bulk load sequencing (Product2 → Standard PBE → custom Pricebook2 → custom PBE), UseStandardPrice inheritance, and product hierarchy strategies. NOT for Salesforce CPQ product and pricing model (use cpq-vs-standard-products-decision). NOT for Industries CPQ catalog-item model (use industries-cpq-vs-salesforce-cpq). NOT for Opportunity Line Item mechanics."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Performance
triggers:
  - "how do I load products and price books into Salesforce in the right order using Data Loader"
  - "my PricebookEntry insert is failing because it says a standard price book entry is required first"
  - "what is the relationship between Product2, Pricebook2, and PricebookEntry and how do I set them up"
  - "bulk loading custom pricebook entries fails with a platform error about standard price"
  - "how do I model a product catalog with multiple price books for different regions or customer segments"
  - "UseStandardPrice on PricebookEntry — when should I set it to true vs false"
tags:
  - product-catalog
  - pricebook
  - pricebook-entry
  - product2
  - bulk-load
  - data-loading
  - price-book
  - standard-pricebook
  - data-model
inputs:
  - "Product list with names, SKUs, and active/inactive status"
  - "Pricebook list — which pricebooks exist, which are standard vs custom"
  - "Pricing structure — does each product have a single price or segment/region-specific pricing"
  - "Volume and tool choice — how many products/entries, and which loading tool (Data Loader, Bulk API 2.0, SOAP API)"
  - "Whether custom pricebook entries should inherit the standard price (UseStandardPrice)"
outputs:
  - "Correct bulk load sequence: Product2 → Standard PBE → custom Pricebook2 → custom PBE"
  - "PricebookEntry relationship diagram showing the three-object chain"
  - "Completed product-catalog-data-model-template.md with load plan and field mapping"
  - "Validation checklist confirming standard PBE prerequisite is satisfied before custom PBEs"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Product Catalog Data Model

This skill activates when a practitioner needs to model, load, or troubleshoot Salesforce product and pricebook data. It covers the mandatory three-object chain (Product2 → Pricebook2 → PricebookEntry), the platform constraint that a Standard Pricebook Entry must exist before any custom Pricebook Entry for the same product, the correct bulk load sequence for Data Loader and Bulk API 2.0, and the `UseStandardPrice` inheritance flag behavior.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Pricebook inventory**: Does the org have a Standard Pricebook already? Are there existing custom pricebooks? What is the IsStandard flag value on each Pricebook2 record?
- **Load tool and volume**: How many Product2 records? How many PricebookEntry records across all pricebooks? Data Loader (Bulk API mode) handles millions of rows; the SOAP API (Bulk API disabled) is suitable only for low volumes.
- **UseStandardPrice requirement**: For each custom pricebook, determine whether entries should inherit the standard price (`UseStandardPrice = true`) or have an explicit unit price (`UseStandardPrice = false`, `UnitPrice` required).
- **Most common wrong assumption**: Practitioners assume they can insert a custom PricebookEntry directly after inserting a Product2. They cannot — Salesforce requires a PricebookEntry in the Standard Pricebook to exist first for that product. Skipping the Standard PBE step causes an immediate DML error.
- **Key platform constraint**: The Standard Pricebook is a singleton per org. Its ID is org-specific and cannot be hardcoded across orgs. Always query `SELECT Id FROM Pricebook2 WHERE IsStandard = true` at runtime.
- **Key limits**: No documented hard limit on total PricebookEntry records per org; practical limits come from Salesforce storage. Products can belong to multiple pricebooks via multiple PricebookEntry records. A product can have only one PricebookEntry per pricebook (the combination of Product2Id + Pricebook2Id must be unique).

---

## Core Concepts

### The Three-Object Chain: Product2 → Pricebook2 → PricebookEntry

Salesforce models products and pricing through three distinct objects:

**Product2** is the product master. It holds product attributes — name, product code, description, family, and whether the product is active (`IsActive`). Product2 has no price. It is a catalog entry only.

**Pricebook2** is a price list. The org always has one Standard Pricebook (`IsStandard = true`). Admins can create additional custom pricebooks for segments, regions, channels, or customer tiers. Pricebook2 records define the list of price lists; they do not hold prices themselves.

**PricebookEntry** is the junction between a product and a price list. It holds the actual price (`UnitPrice`) for a specific product in a specific pricebook. Every PricebookEntry links exactly one Product2 to exactly one Pricebook2. An Opportunity's price book determines which PricebookEntry records are available as Opportunity Line Items.

The chain is: Product2 defines what exists. Pricebook2 defines which list applies. PricebookEntry defines what it costs in that list.

### The Standard Pricebook Prerequisite — Hard Platform Constraint

This is the most operationally critical behavior in this domain. Salesforce **requires** that a PricebookEntry exist in the Standard Pricebook for a given Product2 before any custom PricebookEntry can be created for that product.

Attempting to insert a custom PricebookEntry without a corresponding Standard PricebookEntry produces a DML error:

```
FIELD_INTEGRITY_EXCEPTION: field integrity exception: unknown (pricebook entry in standard price book required before this entry can be created)
```

This constraint is enforced at the platform level, regardless of whether the insert is done via the UI, Data Loader, Bulk API 2.0, or Apex. There is no way to bypass it.

The mandatory sequence is:
1. Insert `Product2` records.
2. Insert `PricebookEntry` records in the **Standard Pricebook** for each product.
3. (Optionally) Insert `Pricebook2` records for custom pricebooks.
4. Insert `PricebookEntry` records in custom pricebooks.

Reversing steps 2 and 4 is the single most common failure mode when loading product catalogs in bulk.

### UseStandardPrice — Inheriting the Standard Price in Custom Pricebooks

`UseStandardPrice` is a Boolean field on PricebookEntry that applies only to custom pricebook entries (not to Standard Pricebook entries). When set to `true`, the custom pricebook entry inherits its `UnitPrice` from the corresponding Standard Pricebook entry for the same product. When set to `false`, the `UnitPrice` field on the custom entry must be explicitly provided.

Behavior specifics:
- If `UseStandardPrice = true`, Salesforce dynamically reads the Standard Pricebook entry's `UnitPrice`. If the standard price is later updated, the custom entry reflects the new price automatically.
- If `UseStandardPrice = true`, you must not provide an explicit `UnitPrice` value on the custom entry — doing so causes a field error.
- Standard Pricebook entries always have `UseStandardPrice = false`. The field is not applicable to them.
- `UseStandardPrice` cannot be set to `true` if no Standard Pricebook entry exists for the product — which reinforces why the Standard PBE prerequisite constraint exists.

### The Standard Pricebook ID Is Org-Specific

There is no constant ID for the Standard Pricebook. Its record ID differs across production orgs, sandboxes, scratch orgs, and Developer Edition orgs. Always query it:

```soql
SELECT Id FROM Pricebook2 WHERE IsStandard = true LIMIT 1
```

In Apex test classes, use `Test.getStandardPricebookId()` instead of querying. Running tests against a queried Standard Pricebook ID (instead of `Test.getStandardPricebookId()`) is a common Apex test failure mode.

---

## Common Patterns

### Pattern: Full Catalog Bulk Load (Product2 + Standard PBE + Custom PBEs)

**When to use:** Loading a net-new product catalog with one or more custom pricebooks using Data Loader or Bulk API 2.0.

**How it works:**

1. Prepare Product2 CSV — columns: `Name`, `ProductCode`, `Description`, `Family`, `IsActive`. No price fields.
2. Load Product2 — upsert using `ProductCode` as the external ID. Capture Product2 IDs from the success file.
3. Query the Standard Pricebook ID: `SELECT Id FROM Pricebook2 WHERE IsStandard = true LIMIT 1`.
4. Prepare Standard PBE CSV — `Pricebook2Id` (Standard PB ID), `Product2Id`, `UnitPrice`, `IsActive`.
5. Load Standard PBEs in a separate job. Verify all rows succeeded before proceeding.
6. Prepare custom Pricebook2 records and load if new.
7. Prepare custom PBE CSV — `Pricebook2Id` (custom), `Product2Id`, `UseStandardPrice`, `UnitPrice` (if applicable), `IsActive`.
8. Load custom PBEs in a separate job after Standard PBE job is confirmed complete.

**Why not load all PBEs in one pass:** Bulk API 2.0 does not guarantee row processing order within a job. A custom PBE row may be processed before its corresponding Standard PBE row is committed. Always use separate sequential jobs with a verification step between them.

### Pattern: UseStandardPrice = True for Consistent Pricing Across Pricebooks

**When to use:** A company maintains one canonical price (the standard price) and wants all pricebooks to reflect that price without managing duplicate price records.

**How it works:**
1. Load Product2 and Standard PBEs with actual `UnitPrice` values.
2. When loading custom PBEs, set `UseStandardPrice = true`. Leave `UnitPrice` blank.
3. When the standard price changes, update only the Standard PBE `UnitPrice`. All custom entries with `UseStandardPrice = true` for that product reflect the updated price automatically.

**Why not always use this:** If different pricebooks require different prices for the same product (e.g., a wholesale pricebook with 20% discount), `UseStandardPrice = true` cannot be used. Each custom PBE requires an explicit `UnitPrice`.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Loading products for the first time with no existing catalog | Product2 → Standard PBE → custom PBE sequence | Hard platform constraint — Standard PBE must precede custom PBE |
| All pricebooks should show the same price as the standard price | Set `UseStandardPrice = true` on custom PBEs | Price updates to Standard PBE propagate automatically |
| Custom pricebooks need product-specific discounts or different prices | Set `UseStandardPrice = false`; provide explicit `UnitPrice` per custom PBE | `UseStandardPrice = true` does not allow a different price |
| Standard Pricebook ID needed in a load job | Query `SELECT Id FROM Pricebook2 WHERE IsStandard = true` | Standard Pricebook ID is org-specific; never hardcode it |
| Standard Pricebook ID needed in Apex test | Use `Test.getStandardPricebookId()` | SOQL query in Apex test context returns no results without SeeAllData |
| Product exists in source but needs multiple pricebooks | One PricebookEntry per product per pricebook | The Product2Id + Pricebook2Id combination must be unique per PBE row |
| Re-loading a catalog after a partial failure | Upsert using Product2 external ID and check for existing PBEs | Prevents duplicates; safe to re-run |
| Retiring a product | Set `Product2.IsActive = false` and `PricebookEntry.IsActive = false` for all PBEs | Inactive products cannot be added to new Opportunities but existing OLIs are preserved |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on product catalog data model tasks:

1. **Confirm org state** — query whether the Standard Pricebook exists, whether Product2 records already exist, and whether any existing PricebookEntry records would conflict with the load.
2. **Design the object load sequence** — explicitly order: Product2 → Standard PBE → custom Pricebook2 (if new) → custom PBE. Never deviate from this sequence.
3. **Prepare CSVs with correct fields** — Product2 (no price), Standard PBE (Pricebook2Id = Standard PB ID, UnitPrice required, UseStandardPrice false), custom PBE (explicit UnitPrice or UseStandardPrice = true, never both).
4. **Load Product2 records** — upsert with ProductCode or a custom external ID. Capture Salesforce Product2 IDs from the success file.
5. **Load Standard PricebookEntries** — use the Standard Pricebook ID queried from the org. Confirm all products have a Standard PBE before continuing.
6. **Load custom Pricebook2 and custom PricebookEntries** — load custom pricebooks first if they are new, then load custom PBEs referencing both the product ID and the custom pricebook ID.
7. **Validate** — run `scripts/check_product_catalog_data_model.py` against the metadata or CSV directory; verify record counts, confirm no products are missing Standard PBEs, confirm UseStandardPrice is set correctly per the load plan.

---

## Review Checklist

Run through these before marking product catalog data model work complete:

- [ ] Load sequence is explicitly Product2 → Standard PBE → custom Pricebook2 → custom PBE with no steps reordered
- [ ] Standard Pricebook ID was queried from the org (`WHERE IsStandard = true`), not hardcoded
- [ ] Every Product2 record has a corresponding active PricebookEntry in the Standard Pricebook
- [ ] Custom PBEs with `UseStandardPrice = true` have no explicit `UnitPrice` value in the load file
- [ ] Custom PBEs with `UseStandardPrice = false` have an explicit `UnitPrice` in the load file
- [ ] Product2Id + Pricebook2Id combination is unique per PricebookEntry row (no duplicates)
- [ ] Upsert was used (not insert) with a meaningful external ID or ProductCode to enable safe re-runs
- [ ] Inactive products have both `Product2.IsActive = false` and `PricebookEntry.IsActive = false`

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Standard PBE required before custom PBE — hard constraint with no bypass** — Inserting a custom PricebookEntry for a product that has no Standard PricebookEntry immediately fails with `FIELD_INTEGRITY_EXCEPTION`. There is no way to suppress this constraint. The Standard PBE load step is mandatory, not optional.

2. **UseStandardPrice = true and explicit UnitPrice cannot coexist** — If you set `UseStandardPrice = true` on a custom PBE and also provide a `UnitPrice` value, the insert fails. Remove the `UnitPrice` column (or leave it blank) whenever `UseStandardPrice = true`.

3. **Standard Pricebook ID varies across every org** — The Standard Pricebook2 record ID is generated at org creation. It differs between production, sandbox, scratch org, and Developer Edition. Any hardcoded Pricebook2 ID in a CSV, Apex class, or metadata record is wrong when deployed to a different org.

4. **Apex tests cannot query the Standard Pricebook without `@isTest(SeeAllData=true)`** — In an Apex test, `SELECT Id FROM Pricebook2 WHERE IsStandard = true` returns no rows unless `SeeAllData=true` is set. Use `Test.getStandardPricebookId()` instead. Tests that use queried Standard PBE IDs fail unpredictably in CI.

5. **Inactive PricebookEntry records are still visible to Apex but not selectable in the UI** — Setting `PricebookEntry.IsActive = false` removes the entry from the Opportunity Line Item product selector, but SOQL queries without a `WHERE IsActive = true` filter still return the record.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `product-catalog-data-model-template.md` | Fill-in-the-blank template for planning a product catalog load — covers load sequence, field mapping, pricebook configuration, and validation checklist |
| `check_product_catalog_data_model.py` | stdlib Python checker that validates CSV load files and Apex classes for product catalog anti-patterns |

---

## Related Skills

- `data-migration-planning` — use when the product catalog load is part of a broader multi-object migration; covers dependency sequencing, validation bypass, and rollback planning
- `cpq-vs-standard-products-decision` — use when deciding whether to use Salesforce CPQ or standard Products/Pricebooks; this skill covers the standard Products model only
- `industries-cpq-vs-salesforce-cpq` — use for Industries CPQ (Vlocity) catalog-item model; completely different data model from Product2/PricebookEntry
