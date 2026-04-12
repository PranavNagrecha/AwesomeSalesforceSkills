# LLM Anti-Patterns — Commerce Catalog Strategy

Common mistakes AI coding assistants make when generating or advising on Commerce Catalog Strategy.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating the Product Catalog With the Storefront Catalog

**What the LLM generates:** Advice that treats the product catalog and storefront catalog as the same object, such as: "Add the category to your catalog and it will appear in the storefront navigation" or "Rename the category in the catalog to update the buyer-facing name." Recommendations that say to design the category hierarchy for navigation purposes, or that show configuration steps that edit category records as if they serve both purposes simultaneously.

**Why it happens:** LLMs trained on general e-commerce content encounter systems where "catalog" and "storefront" are the same concept (Shopify, Magento in default config, WooCommerce). The Salesforce Commerce architecture separates these into distinct objects with distinct maintenance cycles — an uncommon pattern that does not appear consistently in training data.

**Correct pattern:**

```
Product catalog (ProductCatalog) — system-of-record taxonomy:
  - Not site-assigned
  - Designed for product-nature groupings
  - Changes here do NOT auto-propagate to storefront

Storefront catalog — buyer-facing navigation per site:
  - One per store
  - References product catalog categories but is a separate record
  - Changes require explicit storefront catalog record updates
```

**Detection hint:** Any response that says a product catalog change "will update" or "reflects in" the storefront without a separate update step is demonstrating this anti-pattern.

---

## Anti-Pattern 2: Recommending More Than 50 Searchable Fields Without Flagging the Limit

**What the LLM generates:** An attribute strategy that marks all product attributes as searchable to maximize discoverability, without noting the 50-field platform limit. Statements like "mark all relevant attributes as searchable so buyers can find products by any spec" or attribute plans that list 60, 70, or 80+ searchable fields.

**Why it happens:** LLMs default to maximizing search coverage as the "safe" approach, reasoning that more searchable fields equals better search. The 50-field limit and its silent failure mode are platform-specific constraints that LLMs do not reliably recall.

**Correct pattern:**

```
Attribute classification decision:
- Searchable: HIGH buyer search frequency — budget ≤50 total
- Filterable-only: browse/facet use, not keyword search
- Display-only: PDP rendering, not indexed
- Internal: never exposed to storefront

Always count searchable fields and confirm ≤50 before
recommending any attribute classification scheme.
```

**Detection hint:** Any attribute plan or recommendation that does not mention the 50 searchable field limit, or that lists more than 50 searchable fields, should be flagged. Look for phrases like "mark all X attributes as searchable" without a field count.

---

## Anti-Pattern 3: Claiming Commerce Search Supports Prefix or Partial-Term Matching

**What the LLM generates:** Statements like "buyers can search by partial SKU number and Commerce will return matching products" or "typing the first few letters of a product name will show results." Recommendations to optimize attribute values for partial-term search, or reassurances that search will handle abbreviations and codes naturally.

**Why it happens:** Most modern search systems (Elasticsearch, Algolia, Solr) support prefix and infix matching by default. LLMs assume Commerce search behaves like these general-purpose search platforms. The full-token-only constraint is Salesforce-specific and non-obvious.

**Correct pattern:**

```
Commerce search: FULL-TOKEN MATCHING ONLY

"500"   → will NOT match "V500"
"cab"   → will NOT match "cabinet"
"UL508" → will NOT match "UL508A-IND"

For partial-term search requirements:
- Normalize attribute values to full buyer vocabulary at import time
- OR add a separate searchable field with expanded natural-language values
- Document this constraint in UX requirements; do not promise behavior
  the platform cannot deliver
```

**Detection hint:** Any response that says search "supports partial matching", "prefix search", or "autocomplete on partial input" without an explicit workaround noting the full-token constraint is demonstrating this anti-pattern.

---

## Anti-Pattern 4: Designing a Deep Taxonomy (5+ Levels) and Calling It Best Practice

**What the LLM generates:** Taxonomy designs with 5, 6, or 7 levels of nesting, often borrowed from general information architecture best practices or large retailer examples. Statements like "a deep taxonomy gives you precise control over product placement" or hierarchies modeled after Amazon's category structure.

**Why it happens:** LLMs synthesize general information architecture guidance that values taxonomic precision and borrows from large-catalog retailers where deep hierarchies have been implemented. The Salesforce Commerce-specific navigation UX degradation from deep hierarchies, and the maintenance cost of maintaining 5+ level storefront catalogs, is not well represented in general training data.

**Correct pattern:**

```
Recommended taxonomy depth: 3–4 levels maximum

Level 1: Top-level category (e.g., Industrial Equipment)
Level 2: Product family (e.g., Motors)
Level 3: Product type (e.g., AC Induction Motors)
Level 4 (optional): Specific variant group if needed

Use faceted filtering to compensate for reduced depth.
Deeper nesting: add a level only when a leaf category
  has 200+ products AND facets cannot adequately discriminate.
```

**Detection hint:** Any taxonomy recommendation with more than 4 levels should be flagged for review. Ask whether the depth serves system-of-record clarity or buyer navigation — if the answer is "navigation," flatten and use facets instead.

---

## Anti-Pattern 5: Treating Product Catalog Visibility as Equivalent to Storefront Catalog Membership

**What the LLM generates:** Recommendations like "to prevent buyers on Store B from seeing Product X, just don't add Product X to Store B's storefront catalog" or "products not in the storefront catalog are invisible to buyers." Instructions that omit entitlement policy configuration because storefront catalog exclusion is treated as sufficient for product visibility control.

**Why it happens:** In many e-commerce platforms, product visibility is controlled exclusively by whether the product appears in the storefront's navigation. LLMs assume Salesforce Commerce works the same way. The Salesforce model — where the product catalog is org-wide and entitlement policies are a separate required layer for access control — is a platform-specific architectural decision that LLMs do not reliably reproduce.

**Correct pattern:**

```
Storefront catalog membership: controls navigation display only
Entitlement policies: controls product access and visibility

A product NOT in the storefront catalog:
  - Does NOT appear in navigation
  - IS still accessible via direct URL or API call
  - IS still returnable in search results if indexed

To restrict product access across storefronts:
  - Configure entitlement policies (BuyerGroupPricebook, etc.)
  - Assign buyer groups to storefronts with appropriate scope
  - Do not rely on storefront catalog exclusion as a security boundary
```

**Detection hint:** Any advice that says omitting a product from a storefront catalog "hides" or "restricts access to" the product without mentioning entitlement policies is demonstrating this anti-pattern. Especially watch for B2B multi-storefront scenarios.

---

## Anti-Pattern 6: Recommending the Same Taxonomy Serves Multiple Storefronts With Different Buyer Intents

**What the LLM generates:** Advice like "design one master taxonomy that all your storefronts share to reduce maintenance overhead" or "use a single category hierarchy that works for both your B2B buyers and your consumer storefront." Taxonomy designs that try to embed navigation vocabulary (buyer-facing terms) and system-of-record structure into the same category tree.

**Why it happens:** LLMs optimize for "don't repeat yourself" principles from software design. The Salesforce architecture specifically provides the product catalog / storefront catalog separation to allow multiple navigation views over a single product catalog — LLMs recommend collapsing this separation because they reason it reduces maintenance effort.

**Correct pattern:**

```
Product catalog taxonomy: stable, system-of-record terms
  → used by all storefronts as the product record backbone
  → NOT redesigned for buyer vocabulary

Storefront Catalog A (B2B buyers):
  → maps product catalog categories to B2B buyer vocabulary
  → independent navigation structure

Storefront Catalog B (consumer buyers):
  → maps same product catalog categories to consumer vocabulary
  → different navigation structure

Product catalog is stable. Storefront catalogs absorb
  navigation changes without touching product records.
```

**Detection hint:** Recommendations to "share a taxonomy across storefronts" or to design a taxonomy that "works for all your buyer types" without mentioning the storefront catalog as a separate layer should be flagged.
