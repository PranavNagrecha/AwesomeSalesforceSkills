# IP Cacheable Patterns — Examples

## Example 1: Product Catalog (Org-Wide, 30 min TTL)

**IP:** `GetProductCatalog` → Apex Selector → 12k records.

**Key:** `ip:catalog:v2:region={region}:currency={currency}`.

**TTL:** 1800s.

**Invalidation:** Product record-triggered flow publishes
`CatalogInvalidated__e`; subscriber Apex clears partition keys matching
the prefix.

---

## Example 2: Per-User Entitlement (Session, 10 min TTL)

**IP:** `GetUserEntitlements` → SOQL + external call.

**Key:** `ip:ent:v1:user={userId}:sku={sku}`.

**Partition:** Session.

**TTL:** 600s.

**Fallback:** On cache miss, live fetch; on live fetch error, return an
empty entitlement list with a warning flag.

---

## Example 3: Cached Response With Stale-While-Revalidate Hint

IP returns `{payload, cachedAt, freshUntil}`. Consumer LWC uses
`freshUntil` to decide if a background re-fetch is warranted. Keeps the
UI responsive while data refreshes.

---

## Anti-Pattern: Org-Wide Cache Of User-Specific Data

A team cached "personalized recommendations" in the org-wide partition
keyed by SKU only. Two users saw each other's recommendations after
seconds. Fix: session partition, include userId in the key.
