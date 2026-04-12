---
name: commerce-catalog-strategy
description: "Use this skill when designing a product catalog taxonomy, planning attribute strategy, or determining search and navigation structure for a B2B or B2C/D2C Commerce store. Triggers on: taxonomy design questions, attribute planning, search index strategy, category navigation structure, or merchandising hierarchy decisions. NOT for catalog configuration — object creation, WebStoreCatalog wiring, entitlement policies, or product assignment steps are covered by admin/commerce-product-catalog."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Scalability
  - Operational Excellence
triggers:
  - "How should I design my product category taxonomy for a B2B commerce store?"
  - "We are hitting search performance issues and need to restructure product attributes"
  - "What is the difference between a product catalog and a storefront catalog in Salesforce Commerce?"
  - "How many searchable fields can I have on a product before search breaks?"
  - "Our navigation categories are getting out of sync with how products are actually organized in the system"
  - "How should I plan attribute sets for product variants across multiple storefronts?"
tags:
  - commerce-catalog-strategy
  - b2b-commerce
  - b2c-commerce
  - d2c-commerce
  - taxonomy
  - product-attributes
  - search-strategy
  - catalog-design
  - merchandising
inputs:
  - "Commerce store type (B2B, B2C, or D2C)"
  - "Number of distinct product types and variant dimensions"
  - "Estimated product catalog size and growth trajectory"
  - "Search and navigation UX requirements from stakeholders"
  - "List of attributes buyers use to filter and compare products"
  - "Existing category hierarchy or taxonomy draft (if available)"
outputs:
  - "Taxonomy design recommendation: depth, breadth, and naming conventions"
  - "Attribute strategy: which attributes are searchable vs filterable vs display-only"
  - "Search index plan: field count audit against the 50-field limit"
  - "Storefront catalog structure recommendation: category navigation design"
  - "Merchandising strategy: product assignment rules, manual vs rule-based"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Commerce Catalog Strategy

This skill activates when a practitioner needs to design — not configure — a product catalog for Salesforce B2B or B2C/D2C Commerce. It covers taxonomy design, attribute planning, search index strategy, storefront navigation structure, and merchandising hierarchy. For hands-on configuration tasks (creating WebStoreCatalog records, assigning products to categories, configuring entitlement policies), use the companion skill `admin/commerce-product-catalog`.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Store type:** B2B and B2C/D2C stores use the same underlying product catalog data model but have different storefront catalog structures, search behaviors, and attribute visibility rules. Confirm which platform is in scope.
- **Most common wrong assumption:** Practitioners conflate the *product catalog* (the system-of-record for all products, not site-assigned, shared across orgs) with the *storefront catalog* (the navigation structure visible to buyers, one per site). These are separate objects with different design concerns.
- **50 searchable field limit:** D2C and B2C stores support a maximum of 50 searchable fields per product. Exceeding this limit silently breaks the next search index rebuild. This constraint must be resolved at taxonomy design time, not after catalog migration.
- **Full-token search only:** Commerce search uses full-token matching. There is no prefix search or infix (substring) search. This constrains attribute naming conventions and significantly impacts how buyers can locate products by partial term.

---

## Core Concepts

Understanding these four concepts is mandatory before making any taxonomy or attribute recommendation.

### Product Catalog vs. Storefront Catalog

Salesforce Commerce uses two distinct catalog constructs that serve different purposes:

- The **product catalog** (`ProductCatalog` object) is the system-of-record repository for all products and their attributes. It is not assigned to a storefront. Products exist in the product catalog independent of any store. This is where taxonomy (category hierarchy), product variants, and attribute definitions live as data.
- The **storefront catalog** is the navigation structure used by a specific B2B or B2C site. It determines which categories buyers see, in what order, and which products appear in which category pages. A store has exactly one active storefront catalog.

Design mistake: planning the storefront navigation hierarchy first and then trying to force it into the product catalog. The product catalog taxonomy must be designed for system-of-record integrity and reuse across storefronts. The storefront catalog is a filtered, ordered view layered on top.

### Search Index Architecture and the 50-Field Limit

D2C Commerce (and Salesforce B2C Commerce) indexes product attributes for search using a flat field mapping. The platform supports a maximum of **50 searchable fields per product**. This limit applies across all attributes, custom fields, and standard fields that are marked as searchable.

Key implications for taxonomy and attribute strategy:
- Budget searchable fields at the attribute planning stage, before any data migration.
- Not every attribute needs to be searchable. Distinguish between: searchable (keyword-indexed), filterable (facet), and display-only (rendered on PDP but not indexed).
- If the total searchable field count exceeds 50, the search index rebuild job will fail silently on the next run, returning stale or incomplete results. There is no runtime error visible to buyers; the failure is visible only in index job logs.

### Full-Token Search and Naming Conventions

Commerce search performs **full-token matching only**. There is no prefix search (typing "cab" will not return "cabinet") and no infix/substring matching. This is a platform constraint, not a configuration option.

Practical impact on attribute and taxonomy design:
- Product names and attribute values that rely on abbreviations or codes (e.g., "SKU-AX-2241") will not surface via partial-term search unless buyers type the complete token.
- Category names used as search facet labels should use the buyer's natural vocabulary, not internal codes.
- If buyers commonly search by partial term, consider denormalizing full descriptive names into a dedicated searchable field rather than relying on the attribute value format.

### Taxonomy Depth, Breadth, and Category Assignment

A well-designed taxonomy balances navigability with maintainability:
- **Depth:** Hierarchies deeper than 3–4 levels cause buyer navigation problems (excessive drilling) and increase the complexity of storefront catalog maintenance. The platform supports deeper nesting, but UX and search facet usability degrade.
- **Breadth:** Categories with more than 20–30 direct children become unwieldy for faceted navigation. Group related subcategories under an intermediate level rather than flattening.
- **Assignment:** A product can belong to multiple categories in the product catalog, but storefront catalog placement is managed separately. Design the category hierarchy to reflect logical groupings, not current navigation UI requirements — those requirements change, but the taxonomy should be stable.

---

## Common Patterns

### Attribute Budget Planning Before Data Migration

**When to use:** When migrating products from a legacy PIM, ERP, or spreadsheet into Commerce and the source system has many attributes per product.

**How it works:**
1. Export the full attribute list from the source system.
2. Classify each attribute as: searchable, filterable-only, display-only, or internal (not exposed to storefront).
3. Count searchable candidates. If count exceeds 50, work with stakeholders to de-prioritize lower-value searchable fields.
4. Document the classification in the catalog strategy document before any product import is attempted.
5. Use the `ProductAttribute` and `ProductAttributeSet` objects to model the agreed attribute structure.

**Why not the alternative:** Waiting until post-migration to audit searchable fields means rework at scale. Changing a field from searchable to non-searchable after products are imported requires a full re-index, which is time-consuming for large catalogs.

### Two-Layer Taxonomy Design

**When to use:** When a single storefront needs to present different navigation structures (e.g., by industry, by product type, or by buyer persona) while all products live in one product catalog.

**How it works:**
1. Design the product catalog taxonomy for system-of-record accuracy: logical category hierarchy based on product nature, not buyer intent.
2. Design the storefront catalog as a curated view: select which product catalog categories to expose, rename them for buyer-facing vocabulary, and set their display order.
3. Use separate category records in the storefront catalog that map back to product catalog categories — do not try to serve two navigation intents with one taxonomy.

**Why not the alternative:** Building a single flat taxonomy that tries to serve both system-of-record integrity and multiple storefront navigation styles creates a category hierarchy that is too broad, hard to maintain, and resistant to change when the storefront UX evolves.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Attribute count in source system exceeds 50 | Classify attributes into searchable / filterable / display-only tiers; reduce searchable to ≤50 | Exceeding 50 searchable fields breaks search index rebuild |
| Multiple storefronts need different navigation | Design product catalog taxonomy for system-of-record; create separate storefront catalogs per site | Storefront catalog is a view layer; product catalog is stable record of truth |
| Buyers search by partial term or code fragment | Add a dedicated full-name searchable field; document the token-matching constraint | Full-token-only search means partial inputs return no results |
| Category hierarchy is deeper than 4 levels | Flatten intermediate levels; use faceted filtering to compensate | Deep hierarchies degrade navigation UX and complicate storefront catalog maintenance |
| Product belongs to multiple logical categories | Allow multi-category assignment in product catalog; manage storefront placement separately | Products can span categories at the product catalog level without storefront navigation conflict |
| Migrating from legacy PIM with inconsistent naming | Normalize attribute values to buyer vocabulary during migration; do not import raw ERP codes | Full-token search makes raw codes unsearchable unless buyers know the exact string |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify store type and catalog scope.** Confirm whether this is B2B, B2C, or D2C. Identify whether there are multiple storefronts sharing a single product catalog. Collect the estimated product count and number of distinct product types.
2. **Audit existing or planned attributes.** List all attributes, custom fields, and standard fields that stakeholders want buyers to search or filter by. Classify each as: searchable, filterable-only, display-only, or internal. Confirm the searchable count is ≤50 before proceeding.
3. **Design the product catalog taxonomy.** Define the category hierarchy with a maximum of 3–4 levels. Ensure category names reflect product nature (system-of-record intent), not buyer navigation intent. Verify each leaf category is specific enough to support faceted filtering.
4. **Design storefront catalog navigation.** Map product catalog categories to the storefront catalog structure. Rename categories using buyer vocabulary. Define display order and which categories are visible on the storefront. If multiple storefronts exist, design a storefront catalog for each separately.
5. **Document attribute naming for search.** Identify any attributes that use codes, abbreviations, or internal terminology. Decide whether to add a parallel descriptive field or normalize values for buyer-facing vocabulary. Document this decision in the catalog strategy artifact.
6. **Validate against platform limits.** Run a final count of searchable fields. Confirm taxonomy depth. Confirm that no category hierarchy design decisions have been baked into the product catalog that should belong in the storefront catalog.
7. **Hand off to configuration.** Produce the catalog strategy document (taxonomy diagram, attribute classification table, storefront navigation plan) and transfer to the configuration workstream using the `admin/commerce-product-catalog` skill.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Searchable field count confirmed at ≤50 per product type
- [ ] Product catalog taxonomy designed independently from storefront navigation structure
- [ ] All attribute values that buyers search by use full vocabulary terms, not codes or abbreviations
- [ ] Storefront catalog designed as a curated view over the product catalog, not merged with it
- [ ] Category hierarchy depth is 4 levels or fewer
- [ ] Attribute classification (searchable / filterable / display-only) is documented and signed off
- [ ] Multi-storefront scenarios have separate storefront catalog designs

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Exceeding 50 searchable fields fails silently** — When the searchable field count exceeds 50, the next search index rebuild job completes without a user-visible error but returns stale or incomplete results. Buyers see no error; the failure is logged only in the index job history. By the time the symptom is noticed, the catalog may have grown significantly beyond the limit.
2. **Product catalog taxonomy changes do not automatically reflect in storefront catalog** — Modifying a category in the product catalog (renaming, restructuring) does not propagate to the storefront catalog. Storefront catalog records must be updated separately. Teams that design these as one object are surprised when navigation breaks after a product catalog reorganization.
3. **Full-token search cannot be made prefix-aware through configuration** — There is no admin setting or search configuration option that enables prefix or infix matching. This is a platform-level constraint. Workarounds require denormalizing data (adding extra searchable fields with expanded values), not configuration changes.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Catalog Strategy Document | Taxonomy diagram, attribute classification table, searchable field count, and storefront catalog navigation plan |
| Attribute Classification Table | Spreadsheet mapping each attribute to its role: searchable, filterable, display-only, or internal |
| Storefront Catalog Navigation Plan | Category tree for each storefront with buyer-facing names, display order, and product catalog category mappings |

---

## Related Skills

- `admin/commerce-product-catalog` — Use for the configuration execution that follows this strategy: creating ProductCatalog records, wiring WebStoreCatalog, assigning products to categories, configuring entitlement policies
- `admin/b2b-vs-b2c-requirements` — Use when the store type has not yet been decided; determines which platform constraints apply before catalog strategy begins
- `admin/commerce-search-customization` — Use after catalog strategy is complete to configure search boosting rules, synonym management, and search result merchandising
