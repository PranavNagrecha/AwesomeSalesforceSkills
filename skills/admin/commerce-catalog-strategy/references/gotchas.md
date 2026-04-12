# Gotchas — Commerce Catalog Strategy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Product Catalog and Storefront Catalog Are Separate Objects With No Automatic Sync

**What happens:** Changes made to the product catalog taxonomy — renaming a category, restructuring the hierarchy, moving a subcategory — do not propagate to any storefront catalog. The storefront catalog holds its own category records that reference but are not automatically updated from the product catalog. A team that reorganizes the product catalog hierarchy after storefront launch will find that storefront navigation silently continues to reflect the old structure until the storefront catalog records are manually updated.

**When it occurs:** Any time product catalog categories are renamed, merged, split, or restructured post-launch. Also triggered when teams assume the two catalogs are the same object and update only one.

**How to avoid:** Design the product catalog taxonomy to be stable at the system-of-record level before storefront catalog design begins. Treat storefront catalog maintenance as a separate downstream task. When a product catalog taxonomy change is necessary, include a corresponding storefront catalog update in the same change ticket. Never assume a product catalog change is "done" until the storefront catalog has been audited.

---

## Gotcha 2: Exceeding 50 Searchable Fields Fails Silently at Index Rebuild Time

**What happens:** When the number of searchable fields on a product exceeds 50, the search index rebuild job does not throw a visible runtime error. It completes with a "success" status, but the index either stops updating or drops field coverage beyond the limit. Buyers receive no error — they simply see no search results for terms that should match products. The failure is only visible in the search index job execution logs, which practitioners rarely monitor proactively.

**When it occurs:** Most commonly encountered during or after a product catalog migration when attribute-heavy products from a PIM or ERP are imported without an upfront field count audit. Also occurs incrementally when custom product attributes are added over time without tracking the running searchable field total.

**How to avoid:** Count all searchable fields before any product import or custom attribute creation. Maintain a running attribute classification document. Set an internal warning threshold at 45 searchable fields to leave a buffer. When approaching the limit, reclassify lower-priority attributes from searchable to filterable-only or display-only.

---

## Gotcha 3: Full-Token Search Only — No Prefix or Infix Matching

**What happens:** Commerce search uses full-token matching exclusively. A search query must match a complete indexed token to return results. Typing "cab" does not return products with "cabinet" in their name. Typing "500" does not return products with "V500" as an attribute value. This is not a misconfiguration — it is a fundamental platform behavior.

**When it occurs:** Affects any attribute value or product name that uses compound strings, codes, abbreviations, or terms that buyers naturally search by partial input. Common in industrial, technical, healthcare, and manufacturing catalogs where product codes, spec values, and certification strings are the primary search terms.

**How to avoid:** At taxonomy and attribute design time, test planned attribute values and product names against the full-token constraint. For any term where partial-input search is a realistic buyer expectation, either normalize the value to the full natural-language form or add a parallel searchable field containing the expanded form. Document this constraint explicitly in buyer-facing search UX requirements so that the UX design does not promise search behavior the platform cannot deliver.

---

## Gotcha 4: One Storefront Catalog Per Store — Multiple Storefronts Cannot Share a Navigation Structure

**What happens:** Each B2B or B2C store site is associated with exactly one storefront catalog. There is no mechanism to assign a single storefront catalog record to multiple storefronts. Teams designing a shared navigation structure and expecting it to serve two brand sites without duplication will find the platform requires separate storefront catalog records for each site.

**When it occurs:** Multi-brand, multi-region, or multi-channel Commerce deployments where the org hosts more than one storefront. A common scenario is a B2B and B2C storefront in the same org with overlapping product lines.

**How to avoid:** Design storefront catalogs as site-specific artifacts from the beginning. Plan for the overhead of maintaining one storefront catalog per site. Use the shared product catalog as the stable backbone, and accept that navigation structure duplication across storefronts is a design reality, not a problem to solve through a shared record.

---

## Gotcha 5: Product Catalog Is Not Site-Assigned — Products Are Always Available Across Storefronts Until Restricted

**What happens:** The product catalog is org-wide and not scoped to a specific storefront. All products in the product catalog are technically accessible from any storefront in the org until explicitly restricted through entitlement policies or storefront catalog category exclusion. Teams that expect product isolation between storefronts by default are surprised when products intended for one brand site are discoverable through direct URL access on another site.

**When it occurs:** Multi-storefront orgs where different storefronts are intended to carry distinct product assortments. Also encountered in B2B setups where account-specific product visibility is expected but not explicitly configured.

**How to avoid:** Do not assume that omitting a product from a storefront catalog prevents buyer access. Design entitlement policies and product visibility rules as a deliberate configuration layer, separate from the taxonomy design. Raise this as a security and scope requirement in the catalog strategy phase so that it is addressed before storefront catalog configuration begins.
