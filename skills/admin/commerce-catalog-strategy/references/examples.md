# Examples — Commerce Catalog Strategy

## Example 1: Industrial Equipment Manufacturer — Attribute Budget Overrun at Migration

**Context:** A manufacturer migrating 12,000 SKUs from an ERP into a D2C Commerce store. The ERP tracked 80+ attributes per product including engineering specs, certifications, internal codes, and supplier references. The project team began product import before auditing which attributes needed to be searchable.

**Problem:** After import, the search index rebuild job started returning stale results. Buyers searching for products by spec value (e.g., "500V" for voltage rating) received no results even when matching products existed. Investigation revealed 73 attributes had been marked as searchable — 23 over the platform limit of 50. The rebuild job was silently failing and the index had stopped updating after the 50th field was processed.

**Solution:**

```
Attribute Classification Exercise:

SEARCHABLE (≤50 budget consumed: 31 fields)
- product_name
- short_description
- voltage_rating          # high buyer search frequency
- current_rating          # high buyer search frequency
- ip_rating               # regulatory searches common
- certifications          # UL, CE, ATEX — typed directly by buyers
- mounting_type
- [24 more confirmed high-search-value attributes]

FILTERABLE ONLY (facets, not keyword-indexed: 18 fields)
- weight_kg
- dimensions_mm
- color
- [15 more browse/filter attributes]

DISPLAY-ONLY (rendered on PDP, not indexed: 34 fields)
- internal_part_number    # ERP reference — buyers don't know this code
- supplier_id
- cost_center
- [31 more internal/display attributes]
```

Run a field count audit before any product import:
```
Total attributes: 83
Searchable candidates initially: 73
After classification: 31 searchable (within limit)
Risk eliminated before first product was imported.
```

**Why it works:** The 50-field searchable limit is enforced at index rebuild time, not at data import time. Auditing attribute classifications before migration prevents a scenario where fixing the overrun requires re-importing or bulk-updating thousands of product records after go-live.

---

## Example 2: Multi-Brand Retailer — Product Catalog vs. Storefront Catalog Separation

**Context:** A retailer running two B2C storefronts under different brand names — one selling premium products, one selling value-tier products. Both storefronts share a single Salesforce org and a single product catalog containing all 3,000 products. The team designed one "unified" category hierarchy intended to serve both storefronts.

**Problem:** The premium storefront needed categories organized by lifestyle and use case (e.g., "Outdoor Living", "Home Entertaining"). The value storefront needed categories organized by product type (e.g., "Chairs", "Tables", "Lighting"). The single unified hierarchy satisfied neither. Attempts to make one taxonomy serve both buyer intents produced a structure 5 levels deep with inconsistent naming, broken facet filtering, and category names that confused buyers on both sites.

**Solution:**

```
Product Catalog Taxonomy (system-of-record — product nature):
  Furniture
    └─ Seating
        └─ Chairs
        └─ Sofas
    └─ Tables
        └─ Dining Tables
        └─ Coffee Tables
  Lighting
    └─ Indoor
    └─ Outdoor

Storefront Catalog A — Premium Brand (lifestyle navigation):
  Outdoor Living
    └─ [maps to: Furniture > Seating > Chairs (outdoor only)]
    └─ [maps to: Lighting > Outdoor]
  Home Entertaining
    └─ [maps to: Furniture > Tables > Dining Tables]

Storefront Catalog B — Value Brand (product-type navigation):
  Chairs          [maps to: Furniture > Seating > Chairs]
  Tables          [maps to: Furniture > Tables]
  Lighting        [maps to: Lighting > Indoor + Outdoor]
```

**Why it works:** The product catalog taxonomy remains stable because it reflects product nature, not buyer intent. Each storefront catalog is an independent view that maps categories to its own buyer vocabulary and navigation structure. When the premium brand redesigns its navigation, the product catalog is untouched and the value storefront is unaffected.

---

## Anti-Pattern: Naming Attributes With Internal Codes That Buyers Must Search By

**What practitioners do:** Import attribute values from ERP or legacy PIM in their raw internal format: part numbers like "AX-2241-C", voltage codes like "V500", certification strings like "UL508A-IND". Mark these fields as searchable assuming buyers will type them.

**What goes wrong:** Commerce search uses full-token matching only. A buyer typing "500" to find 500V products receives zero results because the indexed value is "V500" — a different token. A buyer typing "UL508" receives zero results because the indexed value is "UL508A-IND". This is not a configuration issue; it is a platform constraint that cannot be resolved after the fact without re-normalizing attribute data and re-indexing.

**Correct approach:** At taxonomy and attribute design time, decide whether buyers search by code or by natural language. If codes must be supported, add a separate searchable field containing the full natural-language expansion alongside the code. If natural language is preferred, normalize the attribute values during import before marking the field as searchable.
