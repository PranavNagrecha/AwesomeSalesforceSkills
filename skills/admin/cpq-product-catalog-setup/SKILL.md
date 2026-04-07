---
name: cpq-product-catalog-setup
description: "Use this skill when setting up or modifying product bundles, product options, product rules, configuration attributes, and product features in Salesforce CPQ. Trigger keywords: CPQ product bundle, product rule, option constraint, feature configuration, dynamic bundle, filter rule, configuration attribute, bundle nesting. NOT for standard Salesforce Products & Pricebooks (use the products-and-pricebooks skill), CPQ pricing rules or discount schedules, or quote template/document configuration."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Performance
triggers:
  - "set up CPQ product bundles with required and optional components"
  - "configure product rules in CPQ to auto-select or block options"
  - "CPQ bundle nesting options and feature grouping configuration"
  - "add configuration attributes to drive dynamic bundle behavior"
  - "filter rules to limit which product options appear in the CPQ configurator"
tags:
  - cpq
  - product-catalog
  - bundles
  - product-rules
  - configuration-attributes
  - option-constraints
inputs:
  - "List of products to bundle, including which are required vs. optional"
  - "Business rules governing which options can or cannot coexist"
  - "Feature grouping requirements for the CPQ configurator UI"
  - "Whether dynamic filtering (filter rules) is needed based on header attributes"
  - "Desired nesting depth for multi-level bundles"
outputs:
  - "CPQ product bundle with features and product options configured"
  - "Product rules (Validation, Alert, Selection, Filter) with conditions and actions"
  - "Configuration attributes scoped to the bundle"
  - "Completed CPQ product catalog checklist documenting all setup decisions"
dependencies:
  - products-and-pricebooks
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# CPQ Product Catalog Setup

Use this skill when configuring the Salesforce CPQ product catalog: building product bundles, defining product options and features, creating product rules (Validation, Alert, Selection, Filter), and setting up configuration attributes that drive dynamic bundle behavior. This skill does not cover standard Salesforce Products & Pricebooks, CPQ pricing rules, discount schedules, or quote document templates.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the Salesforce CPQ managed package (`SBQQ__`) is installed and licensed in the org. CPQ product objects (`SBQQ__Product2__c`, `SBQQ__ProductOption__c`, `SBQQ__ProductRule__c`) will not exist without it.
- Identify the bundle parent product and all child products that will appear as options. Determine which options are Required, Optional, or Default-selected.
- Understand the nesting depth planned. Salesforce CPQ supports bundle nesting up to 4 levels, but each level multiplies configurator load time — deep nesting is a performance risk.
- Clarify whether the bundle needs dynamic filtering. Filter rules and configuration attributes add setup complexity but are the correct mechanism for attribute-driven option visibility.
- Understand rule ordering requirements early. Product Rules fire in sequence number order, and Selection rules can interfere with one another if sequenced incorrectly.

---

## Core Concepts

### Product Bundles and Product Options

A CPQ product bundle consists of a parent product and one or more child products registered as `SBQQ__ProductOption__c` records linked to the parent. Options are organized into `SBQQ__Feature__c` records, which control how they are grouped and displayed in the CPQ configurator UI.

Each Product Option carries key configuration fields:
- **SBQQ__Type__c** — Component (priced individually), Bundle (nested bundle), or null. Drives how the option is quoted.
- **SBQQ__Required__c** — Boolean. When true, the option is always included and cannot be removed.
- **SBQQ__Selected__c** / **SBQQ__Default__c** — Controls whether the option is pre-selected when the configurator opens.
- **SBQQ__MinQuantity__c** / **SBQQ__MaxQuantity__c** — Enforces minimum and maximum selection counts per option.
- **SBQQ__Number__c** — Sort order within the feature.

Bundles can be nested: a Product Option can itself be a bundle product. The CPQ configurator supports up to 4 nesting levels, but each nested level triggers additional SOQL queries at configurator open, meaning 4-level nesting on large catalogs can exceed governor limits or cause multi-second page loads.

### Product Rules

Product Rules (`SBQQ__ProductRule__c`) enforce business logic in the CPQ configurator. There are four types, each with distinct behavior:

| Rule Type | When it fires | Effect |
|---|---|---|
| Validation | On save attempt | Blocks quote save and shows an error message if conditions are met |
| Alert | On save attempt | Shows a warning but allows the quote to save |
| Selection | On option selection or deselection | Automatically adds or removes related options |
| Filter | On configurator open and re-render | Hides or shows product options based on conditions |

Rules are composed of:
- **Conditions** (`SBQQ__ErrorCondition__c`) — evaluated against quote line fields or product option fields
- **Actions** (`SBQQ__ProductAction__c`) — what to do when all conditions are true (for Selection and Filter rules)

Product Rules fire in ascending order of their `SBQQ__Sequence__c` field. For Selection rules that chain (rule A's action triggers rule B's conditions), sequence order is the only control mechanism. Misconfigured sequences cause infinite loops or missed selections.

### Configuration Attributes

Configuration Attributes (`SBQQ__ConfigurationAttribute__c`) are header-level fields displayed at the top of the CPQ configurator, outside of individual product lines. They allow bundle-level choices — such as "Service Tier" or "Region" — to drive Product Rule conditions without being tied to a specific option.

Configuration Attributes are scoped to a specific bundle product. When an attribute value changes, CPQ re-evaluates Filter rules and Selection rules that reference that attribute. This is the correct mechanism for attribute-driven dynamic bundles; attempting to replicate this with custom fields on the product record is not supported and will not trigger rule re-evaluation.

---

## Common Patterns

### Pattern: Simple Required/Optional Bundle

**When to use:** The bundle has a fixed set of required components (always included, always priced) and a set of optional add-ons the customer can select.

**How it works:**
1. Create the parent product record. Mark it as a Bundle in CPQ (`SBQQ__Component__c = false`, `SBQQ__QuantityEditable__c` as needed).
2. Create a Feature for each logical grouping (e.g., "Hardware", "Software", "Services").
3. Create Product Option records linking each child product to the parent, setting `SBQQ__Required__c = true` for mandatory components and `SBQQ__Selected__c = true` for default-selected optionals.
4. Set `SBQQ__MinQuantity__c` and `SBQQ__MaxQuantity__c` on options where selection limits apply.
5. Test in the CPQ configurator by adding the bundle to a quote.

**Why not the alternative:** Using Validation rules to block deselection of required components is fragile — a required option should be marked Required at the Product Option level, not blocked post-hoc by a rule. Validation rules add page load and save overhead unnecessarily.

### Pattern: Dynamic Bundle with Filter Rules and Configuration Attributes

**When to use:** The set of visible options should change based on a header-level choice the rep makes at bundle configuration time (e.g., choosing "Enterprise" service tier reveals premium add-ons not shown for "Standard" tier).

**How it works:**
1. Create the parent bundle product and all possible options as Product Option records (including options that will initially be hidden).
2. Create a Configuration Attribute linked to the parent bundle, mapping it to a custom field on the Quote Line (`SBQQ__QuoteLine__c`) or Product Option that will hold the attribute value.
3. Create a Filter Product Rule with conditions that evaluate the Configuration Attribute field value and actions that include or exclude specific options.
4. Set the Filter rule's `SBQQ__Scope__c` to "Product" to target options within the bundle.
5. Test by opening the configurator, changing the attribute value, and confirming the option list re-renders correctly.

**Why not the alternative:** Custom Lightning Web Components or JavaScript customizations to hide options are fragile across CPQ managed package upgrades. Filter rules are the supported, upgrade-safe mechanism for attribute-driven option visibility.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Option must always be included and priced | Set `SBQQ__Required__c = true` on the Product Option | Prevents removal in configurator UI without rule overhead |
| Option should be pre-selected but removable | Set `SBQQ__Selected__c = true` on the Product Option | Cleaner than a Selection rule that fires on open |
| Block incompatible option combinations | Validation Product Rule with conditions on both options | Only Validation rules block save; Alert rules only warn |
| Auto-add an accessory when a product is selected | Selection Product Rule | Correct mechanism for reactive auto-add behavior |
| Hide options based on a header attribute | Filter Product Rule + Configuration Attribute | Supported upgrade-safe pattern; LWC overrides are fragile |
| Nested bundles deeper than 3 levels | Flatten catalog or redesign grouping | 4-level nesting causes significant configurator load time |
| Large catalog with hundreds of options per bundle | Use Filter rules to reduce visible options | Reduces configurator rendering cost at open |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm CPQ installation and license.** Verify `SBQQ__` objects exist in the org schema. Check that the user has CPQ product configuration permissions. Without the managed package, no CPQ product setup is possible.
2. **Map the bundle structure.** Document the parent product, all child products, their Feature groupings, and which options are Required, Default-selected, or Optional. Identify nesting depth. Flag any planned nesting beyond 2 levels for performance review.
3. **Create Features and Product Options.** Create Feature records for each option group. Create Product Option records for each child product, setting Type, Required, Selected, Min/Max Quantity, and sort order. Do not proceed to rules until the base bundle is tested in the configurator.
4. **Define and sequence Product Rules.** Identify all business constraints. Map each constraint to a rule type (Validation, Alert, Selection, Filter). Assign sequence numbers deliberately — Selection rules that chain must be sequenced so earlier rules do not undo later ones. Create Conditions and Actions for each rule.
5. **Configure Configuration Attributes if needed.** If any product rules depend on header-level choices, create Configuration Attributes linked to the bundle and the relevant field. Validate that changing the attribute value triggers the expected Filter or Selection rule behavior.
6. **Test in the CPQ configurator end to end.** Add the bundle to a test quote. Test all rule branches: required options appear, incompatible options are blocked on save, auto-select fires correctly, and filter rules re-render on attribute change.
7. **Document rule sequences and attribute mappings.** Record the purpose and sequence number of every product rule. Undocumented rule sequences become maintenance liabilities, especially when new rules are added later.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All Product Option records have correct Type, Required, Selected, and Min/Max Quantity values
- [ ] Feature records are created and options are assigned to the correct feature with correct sort order
- [ ] Product Rules have explicit sequence numbers and the sequence order is documented
- [ ] Each Product Rule has at least one Condition and (for Selection/Filter rules) at least one Action
- [ ] Configuration Attributes are scoped to the correct bundle product and linked to the correct field
- [ ] Filter rules have been tested with attribute value changes in the configurator
- [ ] Bundle nesting depth is 3 levels or fewer, or a performance exception has been documented
- [ ] Validation rules have been tested by attempting to save a quote that violates each condition

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Bundle nesting beyond 2 levels multiplies configurator load time** — Each nested level triggers additional SOQL queries when the configurator opens. At 4 levels with a large catalog, page load can exceed 10–15 seconds or hit anonymous apex governor limits. Flatten nested bundles wherever possible.
2. **Product Rules fire in sequence number order — duplicates or gaps cause unpredictable behavior** — If two Selection rules share the same sequence number, CPQ's evaluation order between them is undefined. Always use unique, spaced sequence numbers (10, 20, 30) to allow insertion without renumbering.
3. **Configuration Attributes are bundle-scoped, not product-scoped** — An attribute defined on Bundle A does not carry over when Bundle A is nested inside Bundle B. Each bundle level that needs attribute-driven behavior requires its own Configuration Attribute setup.
4. **Filter rules hide options in the UI but do not prevent API-level additions** — If a record is inserted via the SBQQ API or via a Salesforce Flow outside the configurator, Filter rules are not evaluated. Validation rules are required to enforce constraints that must hold at the data level.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CPQ product bundle configuration | Parent product with Feature and Product Option records |
| Product Rules | Validation, Alert, Selection, and Filter rules with Conditions and Actions |
| Configuration Attributes | Header-level bundle attributes linked to rule conditions |
| CPQ product catalog setup checklist | Completed checklist from this skill documenting all setup decisions |

---

## Related Skills

- products-and-pricebooks — Use for standard Product2 and Pricebook2 setup before adding CPQ-specific configuration
- cpq-vs-standard-products-decision — Use to determine whether CPQ is the right tool before beginning CPQ product setup
- quote-to-cash-requirements — Use during requirements gathering to confirm which CPQ capabilities are needed
