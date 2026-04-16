# Product Catalog Migration Commerce — Work Template

Use this template when planning or executing a B2B Commerce product catalog migration.

## Scope

- Total products to migrate: ___________
- Total categories: ___________
- Maximum variants per parent: ___________ (must be ≤ 200)
- Maximum images per product: ___________ (must be ≤ 9)
- Pricing in scope: [ ] Yes  [ ] No
- Source system: ___________

---

## Pre-Migration Checklist

- [ ] Variant count per parent confirmed ≤ 200 for all product families
- [ ] Image count per product confirmed ≤ 9
- [ ] Category hierarchy documented (parent categories before child categories)
- [ ] Target catalog ID and WebStore ID confirmed
- [ ] Commerce Import API access confirmed (Connected App with Commerce scopes)
- [ ] Deprecated sync endpoint (`/commerce/sale/product`) not in use

---

## Load Order Plan

| Step | Object | Dependency | Status |
|---|---|---|---|
| 1 | ProductCatalog | None | |
| 2 | ProductCategory | ProductCatalog | |
| 3 | Product2 | None | |
| 4 | ProductCategoryProduct | ProductCategory + Product2 | |
| 5 | WebStoreCatalog | ProductCatalog + WebStore | |
| 6 | Pricebook2 | None | |
| 7 | PricebookEntry | Product2 + Pricebook2 | |

---

## Commerce Import API Job Specification

- API endpoint: `POST /services/data/v{version}/commerce/management/import/product/jobs`
- Authorization: Bearer token (OAuth 2.0 Connected App)
- Catalog ID: ___________
- WebStore ID: ___________
- CSV file per object: [ ] ProductCatalog  [ ] ProductCategory  [ ] Product2  [ ] ProductCategoryProduct  [ ] WebStoreCatalog  [ ] PricebookEntry

---

## Post-Import Validation SOQL

```sql
-- Product count
SELECT COUNT() FROM Product2 WHERE IsActive = true

-- Category count
SELECT COUNT() FROM ProductCategory WHERE CatalogId = '<catalog_id>'

-- Category assignments
SELECT COUNT() FROM ProductCategoryProduct WHERE ProductCategoryId IN 
  (SELECT Id FROM ProductCategory WHERE CatalogId = '<catalog_id>')

-- WebStoreCatalog association
SELECT Id FROM WebStoreCatalog WHERE WebStoreId = '<store_id>' AND ProductCatalogId = '<catalog_id>'

-- Pricing
SELECT COUNT() FROM PricebookEntry WHERE IsActive = true AND Pricebook2Id = '<pricebook_id>'
```

---

## Notes

_Capture any variant redesign decisions, image mapping decisions, or open questions._
