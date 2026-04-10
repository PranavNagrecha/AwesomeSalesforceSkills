---
name: b2c-commerce-store-setup
description: "Use when configuring or troubleshooting a Salesforce B2C Commerce (SFCC) storefront — including Business Manager site creation, SFRA cartridge path setup, customer groups, search index rebuilding, and key quota limits. Trigger keywords: SFCC, Commerce Cloud, Business Manager, storefront, cartridge, SFRA, site preferences, replication. NOT for B2B Commerce on Lightning platform (WebStore, BuyerGroup, CommerceEntitlementPolicy — see admin/b2b-commerce-store-setup for that)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "how do I create a new storefront site in Business Manager for SFCC"
  - "SFRA cartridge path is not resolving — custom cartridge changes have no effect on storefront"
  - "search results are stale after updating catalog or site preferences in Commerce Cloud"
  - "how to configure customer groups and promotions in Salesforce B2C Commerce"
  - "SFCC site replication or quota limits for custom objects and promotions"
tags:
  - b2c-commerce
  - sfcc
  - business-manager
  - sfra
  - cartridge
  - storefront
  - commerce-cloud
inputs:
  - "Target site ID and intended storefront locale/currency"
  - "List of custom cartridges to include (names, purpose, dependency order)"
  - "Catalog structure (master catalog ID, storefront catalog ID)"
  - "Customer group definitions or promotion scope"
  - "Any existing Business Manager export or site preferences XML"
outputs:
  - "Site creation checklist with validated cartridge path"
  - "SFRA cartridge path string with custom cartridges positioned correctly"
  - "Quota risk assessment for active promotions, product line items, and custom objects"
  - "Search index rebuild procedure and recommended schedule"
  - "Guidance on site preferences, locales, and replication scope"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# B2C Commerce Store Setup

This skill activates when a practitioner needs to configure a Salesforce B2C Commerce (SFCC) storefront from Business Manager site creation through SFRA cartridge path management, quota awareness, and search index operations. It is strictly for the proprietary SFCC infrastructure — not for B2B Commerce on the Salesforce Lightning platform.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the platform is B2C Commerce (SFCC) — Business Manager URL, not a Lightning org. B2B Commerce uses WebStore and lives in a Salesforce org; SFCC does not.
- Identify the target instance type: Development, Staging, or Production. Replication behavior and quota enforcement differ.
- Know the full custom cartridge list and their dependency order before touching the cartridge path — wrong order causes silent fallback to app_storefront_base, which is extremely hard to debug.
- Be aware of the active-promotions performance threshold (1,000 active promotions). Exceeding it degrades basket performance before hitting the hard cap of 10,000.
- Search index is NOT automatically rebuilt after catalog or preference changes — any session that cached old data will see stale results until manual rebuild.

---

## Core Concepts

### Business Manager and Site Architecture

B2C Commerce is managed through Business Manager (BM), a proprietary admin interface. Each storefront is a **site** created at `Administration > Sites > Manage Sites > New`. Site IDs must be 32 characters or fewer, alphanumeric only, no spaces. A site is bound to:

- A **storefront catalog** (subset of the master catalog assigned as the browsable product set)
- A **currency** and one or more **locales**
- A **cartridge path** that controls which code runs for the site

Sites are isolated; preferences, promotions, and catalogs are scoped per-site unless explicitly shared at the organization level.

### SFRA Cartridge Path

Storefront Reference Architecture (SFRA) uses a colon-separated cartridge path evaluated left to right. When SFCC resolves a template, script, or static resource it walks from the leftmost cartridge until it finds the file. The base cartridge `app_storefront_base` must always sit at the **rightmost** position. Custom cartridges and integration cartridges go to its **left**.

Example path:
```
int_custom_payment:plugin_giftcert:app_custom_mystore:app_storefront_base
```

**Never modify `app_storefront_base` directly.** Doing so creates a merge conflict on every SFRA upgrade and voids upgrade compatibility. All overrides must live in a cartridge positioned left of it.

Cartridge path is configured in Business Manager at `Administration > Sites > Manage Sites > [Site] > Settings > Cartridges`.

### Search Index and Catalog Replication

SFCC does not auto-rebuild the search index after catalog, price book, or site preference changes. Practitioners must manually trigger a **Full Search Index** rebuild via `Merchant Tools > Search > Search Indexes > Rebuild`. In production, this can take minutes to hours depending on catalog size.

Replication pushes content from staging to production. It does not replace a search index rebuild — both may be required after a catalog update in production.

### Customer Groups, Promotions, and Quotas

Customer groups segment shoppers for targeted promotions and pricing. They are defined in `Merchant Tools > Customers > Customer Groups`. Promotions are created in `Merchant Tools > Marketing > Promotions` and assigned to campaigns and experiences.

Key quota limits (per-instance, enforced by SFCC infrastructure):
| Resource | Performance Threshold | Hard Limit |
|---|---|---|
| Active promotions | 1,000 | 10,000 |
| Product line items per basket | — | 400 |
| Session size | — | 10 KB |
| HTTPClient calls per page request | — | 16 |
| Replicable custom objects | — | 400,000 per instance |

Exceeding the active-promotions threshold does not throw an error — it silently degrades basket and checkout performance. Monitor and archive inactive promotions regularly.

---

## Common Patterns

### Pattern: Installing a Custom Cartridge on SFRA

**When to use:** Adding a new integration (payment, loyalty, analytics) or a storefront customization cartridge.

**How it works:**
1. Upload the cartridge code to the SFCC instance via WebDAV (`/cartridges/`) or a CI pipeline (SFCC CI toolkit / `sfcc-ci`).
2. In Business Manager go to `Administration > Sites > Manage Sites > [Site] > Settings`.
3. In the Cartridges field, prepend the new cartridge name to the left of any existing custom cartridges, keeping `app_storefront_base` rightmost.
4. Save and test by verifying the override file is served (check template resolution in the Request Log or add a visible marker to the overriding template).

**Why not the alternative:** Appending a cartridge to the right of `app_storefront_base` means its overrides are never reached — the base cartridge resolves first.

### Pattern: Rebuilding Search Index After Catalog Update

**When to use:** After any catalog import, product attribute change, price book update, or search preference modification.

**How it works:**
1. Navigate to `Merchant Tools > Search > Search Indexes`.
2. Select the affected search index (typically `[siteid]-product`).
3. Click `Full Rebuild` (not `Partial`) if product visibility or attribute data changed.
4. Monitor progress in `Administration > Operations > Jobs`.
5. Verify results on storefront search before marking complete.

**Why not the alternative:** Partial rebuild only reindexes changed price/inventory data. Structural catalog changes (attributes, categories, visibility) require a full rebuild.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Storefront customization needed | Create a custom cartridge positioned left of app_storefront_base | Preserves upgrade path; no merge conflicts on SFRA updates |
| Catalog or search preference changed | Full Search Index rebuild | No auto-index; stale data persists until manual rebuild |
| Active promotions approaching 1,000 | Archive or deactivate expired promotions immediately | Performance degrades silently; no error thrown at threshold |
| New site needed for a new locale/region | Create a new site in BM; assign its own cartridge path and catalog | Sites are isolated by design; shared org-level resources can be reused |
| Staging-to-production content push | Use BM replication jobs, then rebuild search index on production | Replication does not trigger search rebuild automatically |
| Custom objects near 400,000 limit | Migrate historical records out or use external storage | Hard limit is instance-wide; overflow causes write failures |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm platform identity** — verify the target is SFCC (Business Manager URL pattern: `*.commercecloud.salesforce.com/on/demandware.store/Sites-Site/`), not a Salesforce Lightning org. If the user mentions WebStore, BuyerGroup, or CommerceEntitlementPolicy, route to `admin/b2b-commerce-store-setup` instead.
2. **Create or locate the site** — in BM go to `Administration > Sites > Manage Sites`. For a new site, choose `New`, enter a site ID (max 32 alphanumeric chars, no spaces), assign a storefront catalog, currency, and primary locale.
3. **Set the cartridge path** — in `Site Settings > Cartridges`, build the colon-separated path with all custom and integration cartridges to the LEFT of `app_storefront_base`. Verify upload of all cartridge code to WebDAV before saving.
4. **Configure site preferences and locales** — in `Merchant Tools > Site Preferences`, set storefront URLs, default locale, currency, and any feature flags. For additional locales add them under `Merchant Tools > Localization`.
5. **Rebuild search index** — trigger a Full Search Index rebuild for the site under `Merchant Tools > Search > Search Indexes`. Do not skip this step after any catalog or preference change.
6. **Audit quotas** — check active promotion count (target < 1,000), basket line-item count in test scenarios (limit 400), and custom object volume (limit 400,000 replicable per instance). Archive any inactive promotions.
7. **Validate on storefront** — browse the storefront, test search, add items to basket, and confirm customer group-based promotions apply correctly before signing off.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Site ID is alphanumeric, 32 chars or fewer, no spaces
- [ ] Cartridge path places all custom cartridges LEFT of app_storefront_base; base cartridge was not modified directly
- [ ] All custom cartridge code has been uploaded to WebDAV and is visible in BM cartridge list
- [ ] Full Search Index rebuild completed after any catalog or preference change
- [ ] Active promotion count is below 1,000; expired promotions archived
- [ ] Storefront browse, search, and checkout tested end-to-end
- [ ] Replication job scheduled if staging changes need to reach production

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Cartridge path is evaluated left-to-right — wrong order is silent** — If a custom cartridge is placed to the RIGHT of `app_storefront_base`, its templates and scripts are never reached. The storefront loads without error but your customizations are completely ignored. Always verify override resolution explicitly.
2. **Search index is never auto-rebuilt** — Catalog imports, product attribute updates, and price book changes do not trigger a search index rebuild. The storefront will serve stale search results indefinitely until a manual full rebuild is initiated. This is one of the most common post-deployment support tickets.
3. **Active promotions degrade performance silently before the hard cap** — At 1,000 active promotions, basket and checkout performance begins to degrade with no error in logs. The hard cap of 10,000 throws errors, but teams usually encounter the performance cliff first and don't connect it to promotion volume.
4. **Session data is capped at 10 KB** — Storing large objects in session (e.g., serialized product lists or user preferences) causes silent data loss or truncation once the 10 KB limit is hit. Symptom: intermittent data disappearing from session mid-browse.
5. **Replication does not rebuild search index on the target instance** — After pushing staging content to production via a replication job, the production search index still reflects pre-replication data until manually rebuilt on the production instance.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Site configuration summary | Site ID, catalog binding, locale and currency settings |
| Validated cartridge path string | Colon-separated path ready to paste into BM Site Settings |
| Quota risk report | Current counts vs. thresholds for promotions, custom objects |
| Search index rebuild log | Job ID, start/end time, status from BM Operations |

---

## Related Skills

- admin/b2b-commerce-store-setup — use for Salesforce B2B Commerce on the Lightning platform (WebStore, BuyerGroup, entitlement policies); entirely different data model and infrastructure
