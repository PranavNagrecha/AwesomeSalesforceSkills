# CPQ Product Catalog Setup — Work Template

Use this template when configuring or reviewing CPQ product bundles, product options, product rules, and configuration attributes.

## Scope

**Skill:** `cpq-product-catalog-setup`

**Request summary:** (fill in what was asked — e.g., "Set up Cloud Platform bundle with tiered service options")

---

## Pre-Flight Checks

Before starting catalog configuration, confirm:

- [ ] Salesforce CPQ managed package (`SBQQ__`) is installed and CPQ objects are present in the org schema
- [ ] User/profile has CPQ product configuration permissions (read/write on `SBQQ__ProductOption__c`, `SBQQ__Feature__c`, `SBQQ__ProductRule__c`, `SBQQ__ConfigurationAttribute__c`)
- [ ] All child products to be bundled exist as `Product2` records with active `PricebookEntry` records
- [ ] Planned nesting depth documented and confirmed as 2 levels or fewer (or performance exception approved)

---

## Bundle Structure

**Parent product name:** _______________

**Bundle nesting depth:** _____ levels

### Feature Groups

| Feature Name | Min Options | Max Options | Description |
|---|---|---|---|
| | | | |
| | | | |
| | | | |

### Product Options

| Child Product | Feature | Type | Required | Selected | Min Qty | Max Qty | Sort Order |
|---|---|---|---|---|---|---|---|
| | | Component | | | | | |
| | | Component | | | | | |
| | | Component | | | | | |
| | | Component | | | | | |

---

## Product Rules

### Rule Inventory

| Rule Name | Type | Sequence | Purpose |
|---|---|---|---|
| | Validation | | |
| | Alert | | |
| | Selection | | |
| | Filter | | |

### Rule Details (one block per rule)

**Rule name:** _______________
**Type:** Validation / Alert / Selection / Filter
**Sequence:** _____
**Eval Event:** Always / Edit / Save
**Error Message (for Validation/Alert):** _______________

Conditions:
| Field | Operator | Value |
|---|---|---|
| | | |

Actions (for Selection/Filter rules):
| Action Type | Target Option | Value |
|---|---|---|
| | | |

---

## Configuration Attributes

| Attribute Label | Bundle Product | Mapped Field | Default Value | Purpose |
|---|---|---|---|---|
| | | | | |
| | | | | |

---

## Test Matrix

Document all branches to be tested before sign-off:

| Test Scenario | Expected Behavior | Pass/Fail |
|---|---|---|
| Open configurator — required options locked | Required options cannot be deselected | |
| Open configurator — default-selected options pre-checked | Optional defaults appear checked | |
| Change Configuration Attribute — filter rules re-render | Hidden options appear/disappear correctly | |
| Attempt to save quote with Validation rule violation | Save blocked, error message shown | |
| Attempt to save quote passing all Validation rules | Save succeeds | |
| Selection rule: select trigger option | Target options auto-selected | |
| Selection rule: deselect trigger option | Auto-selected options removed | |
| API-driven quote add of filtered option | Validation rule blocks if data-level constraint exists | |

---

## Documentation Record

**Rule sequence documented in:** (link to internal wiki / Confluence / this file)

**Bundle nesting diagram:** (attach or link)

**Known performance test results:** (configurator load time at representative catalog size)

---

## Notes

Record any deviations from the standard pattern and why:

(notes here)

---

## Review Checklist (from SKILL.md)

- [ ] All Product Option records have correct Type, Required, Selected, and Min/Max Quantity values
- [ ] Feature records are created and options are assigned to the correct feature with correct sort order
- [ ] Product Rules have explicit sequence numbers and the sequence order is documented
- [ ] Each Product Rule has at least one Condition and (for Selection/Filter rules) at least one Action
- [ ] Configuration Attributes are scoped to the correct bundle product and linked to the correct field
- [ ] Filter rules have been tested with attribute value changes in the configurator
- [ ] Bundle nesting depth is 3 levels or fewer, or a performance exception has been documented
- [ ] Validation rules have been tested by attempting to save a quote that violates each condition
