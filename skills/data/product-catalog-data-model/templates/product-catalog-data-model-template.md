# Product Catalog Data Model — Work Template

Use this template when planning or reviewing a product catalog load or pricebook configuration task.

## Scope

**Skill:** `product-catalog-data-model`

**Request summary:** (fill in what the practitioner asked for)

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

| Question | Answer |
|---|---|
| Number of Product2 records to load | |
| Number of custom pricebooks | |
| Standard Pricebook ID (queried from target org) | |
| Load tool (Data Loader / Bulk API 2.0 / Apex / REST API) | |
| UseStandardPrice strategy (inherit / explicit per pricebook) | |
| External ID field for Product2 upsert matching | |
| Any products already exist in the org? | Yes / No |
| Any existing PricebookEntry records that would conflict? | Yes / No |

---

## Load Sequence Plan

Confirm the sequence is correct before any data is loaded:

| Step | Operation | Object | Tool | Prerequisite |
|---|---|---|---|---|
| 1 | Upsert | Product2 | | None |
| 2 | Insert / Upsert | PricebookEntry (Standard PB) | | Step 1 complete + verified |
| 3 | Insert / Upsert | Pricebook2 (custom — if new) | | None |
| 4 | Insert / Upsert | PricebookEntry (custom pricebooks) | | Step 2 complete + verified |

---

## Field Mapping: Product2

| Source Field | Target Salesforce Field | Notes |
|---|---|---|
| | Name | Required |
| | ProductCode | Recommended external ID |
| | Description | |
| | Family | Must match picklist values |
| | IsActive | Default: true |
| | (custom external ID field) | e.g., Legacy_Product_Id__c |

---

## Field Mapping: Standard PricebookEntry

| Source Field | Target Salesforce Field | Notes |
|---|---|---|
| (Standard Pricebook ID — queried) | Pricebook2Id | Required; query `WHERE IsStandard = true` |
| | Product2Id | From Product2 load success file |
| | UnitPrice | Required; must be numeric |
| | IsActive | Default: true |
| | UseStandardPrice | Must be false (or omit) for Standard PBE |

---

## Field Mapping: Custom PricebookEntry

| Source Field | Target Salesforce Field | Notes |
|---|---|---|
| | Pricebook2Id | Custom Pricebook2 ID |
| | Product2Id | From Product2 load success file |
| | UseStandardPrice | true = inherit standard price; false = explicit price |
| | UnitPrice | Required if UseStandardPrice = false; omit if true |
| | IsActive | Default: true |

---

## Validation Plan

Record verification steps to run after each load phase.

| After Step | Verification Query / Check | Expected Result |
|---|---|---|
| After Product2 load | `SELECT COUNT() FROM Product2 WHERE IsActive = true` | Matches source count |
| After Standard PBE load | `SELECT COUNT() FROM PricebookEntry WHERE Pricebook2.IsStandard = true AND IsActive = true` | One row per active product |
| After custom PBE load | `SELECT COUNT() FROM PricebookEntry WHERE Pricebook2.IsStandard = false AND IsActive = true` | One row per product per custom pricebook |
| Orphan check | `SELECT COUNT() FROM Product2 WHERE Id NOT IN (SELECT Product2Id FROM PricebookEntry WHERE Pricebook2.IsStandard = true)` | 0 (every product has a Standard PBE) |
| UseStandardPrice audit | `SELECT COUNT() FROM PricebookEntry WHERE UseStandardPrice = true AND UnitPrice != null` | 0 (these rows would have failed on insert) |

---

## Checklist

Copy this from SKILL.md Review Checklist and tick items as you complete them:

- [ ] Load sequence is Product2 → Standard PBE → custom Pricebook2 → custom PBE
- [ ] Standard Pricebook ID was queried from the target org at runtime (not hardcoded)
- [ ] Every Product2 record has a corresponding active PricebookEntry in the Standard Pricebook
- [ ] Custom PBEs with `UseStandardPrice = true` have no UnitPrice in the load file
- [ ] Custom PBEs with `UseStandardPrice = false` have an explicit UnitPrice
- [ ] Product2Id + Pricebook2Id combination is unique per PricebookEntry row
- [ ] Upsert (not insert) was used for all load jobs
- [ ] Inactive products have both Product2.IsActive = false and PricebookEntry.IsActive = false

---

## Notes

Record any deviations from the standard pattern and the reason for each deviation.

- Deviation 1:
- Deviation 2:
