# Commerce Product Catalog — Work Template

Use this template when working on tasks involving B2B/B2C Commerce product catalog configuration,
category hierarchy setup, entitlement policy wiring, or product variant modeling.

## Scope

**Skill:** `commerce-product-catalog`

**Request summary:** (describe what the user asked for — e.g., "set up category hierarchy for new store", "configure entitlement policies for two buyer tiers", "add product variants with Color and Size attributes")

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md:

- **Target WebStore name and Id:**
- **Active ProductCatalog name and Id (from WebStoreCatalog):**
- **Number of buyer segments / BuyerGroups:**
- **CommerceEntitlementPolicy records in place (names and linked BuyerGroups):**
- **Does the catalog use product variants?** [ ] Yes [ ] No
- **Search index type:** [ ] Salesforce Search [ ] Einstein Search [ ] Unknown
- **Approximate total Product2 SKU count:**
- **Approximate total entitlement policy count:**
- **Known constraints or limits in play:**

---

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] **Pattern A — Single Catalog, Flat Category Hierarchy** (small catalog, one buyer segment)
- [ ] **Pattern B — Single Catalog, Segmented Entitlement Policies** (multiple buyer tiers)
- [ ] **Pattern C — Variant Products with Attribute Sets** (products with multiple configurations)
- [ ] **Combination of B + C**

Rationale: (explain the selection based on the context gathered above)

---

## Design Decisions

### Category Hierarchy

Document the planned category structure:

```
ProductCatalog: [Catalog Name]
  └── ProductCategory: [Top-Level Category 1]
        └── ProductCategory: [Sub-Category 1.1]
        └── ProductCategory: [Sub-Category 1.2]
  └── ProductCategory: [Top-Level Category 2]
        └── ...
```

Maximum nesting depth planned: ___ levels (recommend ≤ 3)

### Entitlement Policy Design

| BuyerGroup Name | CommerceEntitlementPolicy Name | Products Covered |
|---|---|---|
| (e.g., Distributor Group) | (e.g., Distributor Policy) | (all SKUs / restricted set) |
| | | |

Max estimated entitlement policies per product: ___ (must stay under 2,000)

### Variant Configuration (if applicable)

| Attribute Set Name | Attributes | Parent Product | Number of Variants |
|---|---|---|---|
| | | | |

---

## Implementation Checklist

Work through these steps in order:

### Phase 1: Catalog and Category Setup
- [ ] Confirm `WebStoreCatalog` has exactly one record for the target store
- [ ] Create `ProductCatalog` record if not already present (Name, ExternalReference)
- [ ] Create top-level `ProductCategory` records with `CatalogId` set
- [ ] Create sub-category `ProductCategory` records with `ParentCategoryId` set
- [ ] Create `ProductCategoryProduct` junction records for all products

### Phase 2: Entitlement Policy Configuration
- [ ] Create `BuyerGroup` records for each buyer segment (if not already present)
- [ ] Create `CommerceEntitlementPolicy` records (one per buyer tier, `IsActive = true`)
- [ ] Create `CommerceEntitlementPolicyGroup` junction records (policy → buyer group)
- [ ] Create `CommerceEntitlementProduct` records for each product per policy
- [ ] Verify no product exceeds the entitlement policy count warning threshold

### Phase 3: Variant Setup (if applicable)
- [ ] Create `ProductAttributeSet` record
- [ ] Create `ProductAttribute` records linked to the set
- [ ] Assign attribute set to parent `Product2` record
- [ ] Create child variant `Product2` records with `VariantParentId` set
- [ ] Set attribute values via `ProductAttributeSetProduct` records

### Phase 4: Search Index and Validation
- [ ] Rebuild search index from Setup > B2B Commerce > [Store Name] > Search Index
- [ ] Confirm index rebuild job completed successfully (check job status)
- [ ] Log in as a buyer user in each BuyerGroup and verify expected products appear in search
- [ ] Confirm products outside each buyer's entitlement policy do not appear in search
- [ ] Confirm variant selector displays correctly on the product detail page (if variants configured)

---

## Validation Queries

Run these SOQL queries to spot common configuration gaps:

```soql
-- Check: how many catalogs are linked to each store?
SELECT WebStoreId, COUNT(Id) numCatalogs
FROM WebStoreCatalog
GROUP BY WebStoreId
HAVING COUNT(Id) > 1

-- Check: products in categories but with no entitlement coverage
SELECT p.Id, p.Name
FROM Product2 p
WHERE Id IN (SELECT ProductId FROM ProductCategoryProduct)
AND Id NOT IN (SELECT ProductId FROM CommerceEntitlementProduct)
AND IsActive = true

-- Check: products approaching the 2,000 buyer group cap (adjust threshold as needed)
SELECT ProductId, COUNT(Id) numPolicies
FROM CommerceEntitlementProduct
GROUP BY ProductId
HAVING COUNT(Id) >= 1800

-- Check: inactive products still assigned to categories
SELECT pc.ProductId, p.Name, p.IsActive
FROM ProductCategoryProduct pc
JOIN Product2 p ON p.Id = pc.ProductId
WHERE p.IsActive = false
```

---

## Notes and Deviations

Record any deviations from the standard pattern and why:

- (e.g., "Used three levels of category nesting instead of two because the taxonomy requires it for the Industrial Equipment domain — accepted with catalog team sign-off")
- (e.g., "Skipped variant configuration — all products are single-SKU for this phase")
- (e.g., "Search index rebuild scheduled for off-peak hours; buyers may see stale results until then — communicated to catalog team")
