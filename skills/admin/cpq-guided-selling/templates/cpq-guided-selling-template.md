# CPQ Guided Selling — Work Template

Use this template when configuring or troubleshooting a CPQ Guided Selling wizard setup.

## Scope

**Skill:** `cpq-guided-selling`

**Request summary:** (fill in what the user asked for — e.g., "Configure a guided selling wizard that filters products by industry and service tier" or "Debug why guided selling returns all products regardless of answers")

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **CPQ managed package installed?** (yes / no — confirm `SBQQ__QuoteProcess__c` and `SBQQ__ProcessInput__c` exist)
- **Classification fields to filter on:** (list each field: API name, object, data type)
  - Example: `Industry_Vertical__c` on Product2, Picklist
  - Example: `Service_Tier__c` on Product2, Picklist
- **Mirror fields needed on SBQQ__ProcessInput__c:** (list fields not yet created)
- **Search type required:** Standard / Enhanced / Custom (reason: __________)
- **Auto Select Product needed?** (yes / no — if yes, confirm pricebook coverage for all potential single-match products)
- **Quote Process scope:** org-wide default / pricebook-specific (which pricebook: __________)
- **If troubleshooting — current symptom:** (e.g., "all products return regardless of answers", "wizard does not launch", "specific product missing from results")

## Classification Field Inventory

| Field API Name | Object | Data Type | Mirror Field on ProcessInput Exists? |
|---|---|---|---|
| | Product2 | | yes / no |
| | Product2 | | yes / no |
| | Product2 | | yes / no |

## Quote Process Configuration

| Setting | Value |
|---|---|
| Record Name | |
| SBQQ__GuidedProductSelection__c | true |
| SBQQ__SearchType__c | Standard / Enhanced / Custom |
| SBQQ__AutoSelectProduct__c | true / false |
| Activated via | CPQ Settings default / Pricebook2 SBQQ__GuidedSelling__c |

## ProcessInput Record Inventory

| Order | Label | SBQQ__SearchField__c | SBQQ__Operator__c | SBQQ__InputType__c | SBQQ__Required__c |
|---|---|---|---|---|---|
| 1 | | | equals / contains / not equals | Picklist / Text | true / false |
| 2 | | | | | |
| 3 | | | | | |

## Mirror Field Checklist

For each custom classification field used in guided selling, confirm both objects have the field:

- [ ] `__c` exists on Product2 with data type: ________
- [ ] `__c` exists on SBQQ__ProcessInput__c with matching data type: ________
- [ ] `SBQQ__SearchField__c` on ProcessInput record is set to the exact API name (no labels, no dot-notation)

## Test Plan

| Test Case | Answers Selected | Expected Result | Actual Result | Pass? |
|---|---|---|---|---|
| Filter to a single product | (specific values) | 1 product in results | | |
| Filter to multiple products | (broad values) | N products in results | | |
| No match | (values with no products) | Empty results, no error | | |
| Optional question blank | (skip optional question) | All products pass that filter | | |
| Auto Select (if enabled) | (answers that match exactly 1 product) | Product added to quote without results screen | | |

## Approach

(Which pattern from SKILL.md applies? Why? — e.g., "Standard guided selling with custom classification fields" or "Enhanced search for multi-value eligibility")

## Checklist

Copy from SKILL.md Review Checklist and tick items as you complete them.

- [ ] `SBQQ__GuidedProductSelection__c = true` is set on the Quote Process record
- [ ] Every custom Product2 classification field used in guided selling has a mirror field with identical API name on `SBQQ__ProcessInput__c`
- [ ] `SBQQ__SearchField__c` on each ProcessInput matches the exact Product2 field API name (case-sensitive)
- [ ] All product records have non-null values on the classification fields they should be filtered by
- [ ] Search type (Standard / Enhanced / Custom) is explicitly set on the Quote Process
- [ ] ProcessInput records have unique, ordered `SBQQ__Order__c` values
- [ ] Required vs. optional questions are correctly marked with `SBQQ__Required__c`
- [ ] The Quote Process is activated (org-wide default or pricebook-level assignment confirmed)
- [ ] Auto Select Product behavior has been tested if enabled
- [ ] End-to-end wizard test completed in sandbox with real CPQ quotes

## Notes

(Record any deviations from the standard pattern and why — e.g., "Custom search Apex required because products are scored by compatibility matrix stored in external system.")
