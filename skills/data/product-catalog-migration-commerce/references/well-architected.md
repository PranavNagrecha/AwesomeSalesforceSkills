# Well-Architected Notes — Product Catalog Migration Commerce

## Relevant Pillars

### Operational Excellence

A catalog migration must be repeatable and auditable. Using the Commerce Import API's async job model provides job status tracking, error reporting at the record level, and the ability to re-run failed jobs. This is operationally superior to ad-hoc Data Loader scripts where failure attribution is lost.

### Reliability

The strict object load order (Catalog > Category > Product2 > CategoryProduct > WebStoreCatalog > Pricebook) must be enforced as a deployment dependency, not treated as optional. Skipping or reordering steps produces partially imported catalogs that are visible in SOQL but broken in the storefront.

---

## WAF Mapping

| WAF Area | Guidance |
|---|---|
| Operational Excellence | Use Commerce Import API async jobs for auditability; validate counts post-import |
| Reliability | Enforce load order as hard dependency; validate WebStoreCatalog and ProductCategoryProduct records |
| Performance | Catalog reindex required after large imports; schedule imports during low-traffic windows |
| Security | Product pricing data may be sensitive; apply FLS on PricebookEntry Amount fields |

---

## Cross-Skill References

- `data/product-catalog-migration-cpq` — For CPQ-specific SBQQ product catalog migration
- `admin/commerce-product-catalog` — Post-migration catalog configuration and store assignment
- `admin/commerce-catalog-strategy` — Taxonomy planning and category hierarchy design before migration

---

## Official Sources Used

- B2B Commerce Import APIs Developer Guide — https://developer.salesforce.com/docs/commerce/b2b-commerce/guide/import-api.html
- Product Data Limits — B2B Commerce Developer Guide — https://developer.salesforce.com/docs/commerce/b2b-commerce/guide/product-data-limits.html
- B2B Commerce Product Import API Reference — https://developer.salesforce.com/docs/commerce/b2b-commerce/references/b2b-comm-product-import-api
