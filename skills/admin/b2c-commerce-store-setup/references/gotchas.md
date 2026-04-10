# Gotchas — B2C Commerce Store Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Cartridge Path Order Is Silent — Wrong Order Never Throws an Error

**What happens:** If a custom cartridge is placed to the right of `app_storefront_base` in the site's cartridge path, none of its overrides are ever applied. The storefront continues to load normally using the base cartridge's templates and scripts. There is no error message, no 404, no log warning.

**When it occurs:** Any time a developer adds a new cartridge via Business Manager and either appends it to the end of the path or pastes it in the wrong position. Also common when copying a path from documentation or another system and placing the custom cartridge without checking direction.

**How to avoid:** Treat the cartridge path rule as a non-negotiable convention: all custom and integration cartridges go to the LEFT of `app_storefront_base`. After configuring, verify by adding a unique marker (e.g., a comment in an ISML template) and confirming it renders on the storefront. Use the SFCC Request Log (`Administration > Debugging > Request Log`) to trace template resolution in development environments.

---

## Gotcha 2: Search Index Is Never Auto-Rebuilt After Catalog or Preference Changes

**What happens:** After a catalog import, product attribute update, category restructure, or search preference change, the storefront search index continues to serve the old data. New products are invisible in search, removed products still appear, and facets reflect the old attribute set.

**When it occurs:** Every catalog deployment, price book update, or search preference save. This affects both development sandboxes and production. Development teams often discover the issue only after a customer reports missing products.

**How to avoid:** Add a mandatory "rebuild search index" step to every catalog deployment runbook. After import jobs complete, navigate to `Merchant Tools > Search > Search Indexes`, select the site's product index, and click `Full Rebuild`. For price-only changes a partial rebuild is sufficient; for structural changes (attributes, categories, visibility) always use Full. Monitor via `Administration > Operations > Jobs`.

---

## Gotcha 3: Active Promotion Count Degrades Performance Before Hitting the Hard Cap

**What happens:** When the number of active promotions exceeds approximately 1,000, basket evaluation time increases non-linearly. Checkout slows by seconds. There is no warning in Business Manager, no quota alert, and no error in logs — the site simply gets slower.

**When it occurs:** Long-running stores that accumulate promotions over time without archiving expired ones. A single holiday sale adding 200 promotions on top of an existing 900 can cross the threshold overnight.

**How to avoid:** Schedule a quarterly promotion hygiene review. Archive or deactivate all promotions with past end dates. Target fewer than 800 active promotions to maintain headroom. Use `Merchant Tools > Marketing > Promotions` with date-range filters to identify stale records. Set a BM custom report or periodic job to alert when the active count exceeds 700.

---

## Gotcha 4: Session Data Is Capped at 10 KB — Overflow Is Silent Data Loss

**What happens:** SFCC enforces a 10 KB session size limit. When custom code stores large serialized objects in the session (product arrays, user preference maps, cart state), the session data silently truncates or fails to persist once the cap is hit. Symptom: user loses saved data mid-browse or sees inconsistent state across pages.

**When it occurs:** Integrations that store complex objects in session (loyalty points, recently viewed products, personalization tokens) are the most common cause. The issue is environment-specific — development sandboxes may show different behavior than production if session handling configuration differs.

**How to avoid:** Store only identifiers (IDs, SKUs) in session, not full objects. Fetch full data from APIs or cache on page render. Profile session size during load testing using the SFCC Request Log. Limit each session attribute to a minimal payload.

---

## Gotcha 5: Replication Does Not Rebuild the Search Index on the Target Instance

**What happens:** After a staging-to-production replication job completes successfully, the production storefront still serves stale search results — the index on production was not updated by the replication.

**When it occurs:** Every replication that includes catalog or product data. Teams assume replication is a full synchronization that includes index state. It is not — it copies content objects (products, content assets, preferences) but leaves the search index on the target instance unchanged.

**How to avoid:** Always include a production search index full rebuild as the final step in any replication runbook. Run the rebuild on the production instance specifically (not staging) after replication completes. Do not sign off a release until the production index status shows `FINISHED` for the post-replication rebuild job.

---

## Gotcha 6: Site ID Cannot Be Changed After Creation

**What happens:** Once a site is created in Business Manager with a given ID, the ID is permanent. It is used in storefront URLs, replication job configurations, log file naming, and API calls. Renaming requires deleting and recreating the site — losing all associated data.

**When it occurs:** Teams that use placeholder or test IDs (`test`, `site1`, `demo`) during initial setup and later want to rebrand or restructure.

**How to avoid:** Agree on production site IDs before creation. Use a naming convention that reflects geography and brand (e.g., `us-brand-en`, `uk-brand-gb`). Apply the 32-character alphanumeric constraint during planning, not after launch.
