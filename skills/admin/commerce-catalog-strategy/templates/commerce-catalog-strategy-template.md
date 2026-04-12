# Commerce Catalog Strategy — Work Template

Use this template when designing a product catalog taxonomy, attribute strategy, or storefront
navigation structure for a Salesforce B2B or B2C/D2C Commerce store.

This template covers strategy design only. For configuration execution, use the
`admin/commerce-product-catalog` skill and its template.

---

## Scope

**Skill:** `commerce-catalog-strategy`

**Request summary:** (fill in what the stakeholder asked for)

**Store type:** [ ] B2B Commerce  [ ] B2C Commerce  [ ] D2C Commerce  [ ] Multiple storefronts

**Number of storefronts in scope:** ___

**Estimated product count:** ___

**Number of distinct product types / families:** ___

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md before proceeding.

| Question | Answer |
|---|---|
| Store type confirmed | |
| Multiple storefronts sharing one org? | |
| Estimated product count and growth rate | |
| Source system for product data (PIM, ERP, spreadsheet) | |
| Total attribute count from source system | |
| Known buyer search patterns (what do buyers type?) | |
| Existing category hierarchy or taxonomy draft available? | |

---

## Attribute Classification

List all attributes from the source system and classify each.

**Searchable field budget: ___ / 50** (fill in your count before proceeding)

| Attribute Name | Source System Field | Classification | Notes |
|---|---|---|---|
| | | Searchable / Filterable / Display-only / Internal | |
| | | | |
| | | | |

**Classification key:**
- **Searchable** — keyword-indexed; buyer can type this value in search box and return results
- **Filterable** — facet/filter UI only; not keyword-indexed; does not consume searchable field budget
- **Display-only** — shown on product detail page; not indexed at all
- **Internal** — never exposed to storefront (ERP codes, cost fields, supplier references)

**Action required if searchable count > 45:** Review and reclassify before import.

**Action required if searchable count > 50:** STOP. Reclassify to ≤50 before any product import.

---

## Product Catalog Taxonomy

Design the category hierarchy for the product catalog (system-of-record — not buyer navigation).

**Taxonomy depth: ___ levels** (recommended maximum: 4)

```
Level 1: [Top-level category]
  Level 2: [Product family]
    Level 3: [Product type]
      Level 4: [Variant group — only if needed]
```

Repeat for each branch.

**Naming convention:** Use natural-language product-nature terms (not internal codes, not buyer vocabulary). Example: "Industrial Motors" not "IND-MOT" and not "Power Equipment for Factories".

---

## Storefront Catalog Navigation Design

Design one section per storefront. If only one storefront, complete one section.

### Storefront: [Name / URL]

**Buyer persona / buyer intent this storefront serves:** ___

| Storefront Category (buyer-facing name) | Maps to Product Catalog Category | Display Order | Visible? |
|---|---|---|---|
| | | | |
| | | | |

**Total top-level categories for this storefront:** ___

**Navigation depth:** ___ levels (recommended maximum: 3 for buyer navigation)

---

## Search Strategy Notes

| Decision | Outcome |
|---|---|
| Any attribute values that use codes / abbreviations? | [ ] Yes — document normalization plan below  [ ] No |
| Partial-term search expected by buyers for any attribute? | [ ] Yes — document workaround plan below  [ ] No |
| Confirmed full-token-only matching constraint communicated to UX team? | [ ] Yes  [ ] No |

**Normalization plan (if applicable):** Describe how attribute values that require buyer-facing vocabulary will be normalized before import or loaded as a parallel searchable field.

---

## Visibility and Entitlement Plan

| Requirement | Approach |
|---|---|
| Product assortment isolation between storefronts | [ ] Entitlement policies  [ ] Buyer groups  [ ] Not required |
| Account-level product visibility (B2B) | [ ] Buyer group assignments  [ ] Account entitlement policy  [ ] Not required |
| Confirmed: storefront catalog exclusion alone is NOT sufficient for access control | [ ] Yes, understood  [ ] Needs discussion |

---

## Checklist

Work through these before handing off to the configuration team:

- [ ] Searchable field count confirmed at ≤50 (internal threshold: ≤45)
- [ ] Product catalog taxonomy designed independently from storefront navigation structure
- [ ] No category names use internal codes or abbreviations as system-of-record labels
- [ ] Attribute values searched by buyers use full vocabulary terms, not abbreviations
- [ ] Storefront catalog designed as a separate navigation view per site
- [ ] Taxonomy hierarchy depth is 4 levels or fewer
- [ ] Attribute classification (searchable / filterable / display-only) documented and signed off
- [ ] Full-token search constraint communicated to UX and stakeholders
- [ ] Entitlement and visibility requirements identified and included in configuration scope

---

## Notes and Deviations

Record any deviations from the standard patterns and the business justification:

- (e.g., "Searchable field count is 48/50 due to regulatory compliance requirements for 15 certification attributes — approved by stakeholder on 2026-04-12")
- (e.g., "Taxonomy is 5 levels deep for the Fasteners product family due to regulatory ISO classification requirements — accepted risk documented in ADR-003")
