# Examples — B2C Commerce Store Setup

## Example 1: Custom Payment Cartridge Not Applying on Checkout

**Context:** A development team integrated a third-party payment provider by uploading their cartridge (`int_payment_acme`) and adding it to the site's cartridge path. On staging, the standard checkout page still shows the SFRA default payment form instead of the custom one.

**Problem:** The cartridge was appended to the RIGHT of `app_storefront_base` in the path, so SFCC resolves the base cartridge's checkout template first and never reaches the override in `int_payment_acme`.

**Solution:**

```
# Wrong — int_payment_acme is unreachable
app_storefront_base:int_payment_acme

# Correct — custom cartridge evaluated first
int_payment_acme:app_storefront_base
```

In Business Manager: `Administration > Sites > Manage Sites > [Site] > Settings > Cartridges`

Set the path to: `int_payment_acme:app_storefront_base`

If there are additional cartridges (e.g., a plugin), the rule is consistent — all custom and integration cartridges go left of the base:

```
int_payment_acme:plugin_giftcert:app_storefront_base
```

**Why it works:** SFCC's cartridge resolution walks the path left to right. The first cartridge that contains the requested template, script, or resource wins. Placing custom cartridges left ensures they intercept the request before the base cartridge.

---

## Example 2: Stale Search Results After Catalog Import

**Context:** A merchandising team imported an updated product catalog (new attributes, revised category assignments) via BM Data Import. The storefront search still returns old category facets and missing new products 24 hours after the import completed successfully.

**Problem:** Catalog imports do not trigger a search index rebuild. The SFCC search index is an independent artifact that must be manually rebuilt after any structural catalog change.

**Solution:**

1. In Business Manager navigate to `Merchant Tools > Search > Search Indexes`.
2. Identify the site's product search index (typically named `[siteid]-product`).
3. Click `Full Rebuild` — not Partial, because category and attribute data changed structurally.
4. Monitor progress via `Administration > Operations > Jobs` — look for the `SearchIndex` job entry.
5. Once status shows `FINISHED`, test the storefront search for the new products and facets.

No code or configuration change is required — this is a purely operational step that must be part of every catalog deployment runbook.

**Why it works:** The search index is a pre-built read-optimized data structure separate from the catalog object store. SFCC never invalidates or rebuilds it automatically; doing so on every write would make imports prohibitively slow at scale.

---

## Example 3: Promotion Performance Degradation at Scale

**Context:** A retailer with an active marketing program has accumulated 1,400 active promotions over several years (including abandoned seasonal campaigns never deactivated). Checkout response time has increased by 3–5 seconds compared to six months ago, but no code changes were deployed.

**Problem:** SFCC evaluates all active promotions against the basket on every checkout step. At 1,000 active promotions the platform crosses a performance threshold — basket evaluation time increases non-linearly. This is not surfaced as a quota warning or error in logs.

**Solution:**

1. In BM navigate to `Merchant Tools > Marketing > Promotions`.
2. Filter for promotions with an end date in the past and status = Active.
3. Export the list, confirm with the marketing team which are safe to deactivate.
4. Bulk-deactivate or archive them — target fewer than 800 active promotions to leave headroom.
5. After deactivation, run a storefront performance test against checkout to confirm baseline is restored.

**Why it works:** Reducing the active promotion set shrinks the evaluation work per basket. The 1,000 threshold is a documented performance boundary in the SFCC Quota Survival Guide; staying below it keeps checkout response times predictable.

---

## Anti-Pattern: Modifying app_storefront_base Directly

**What practitioners do:** Edit templates or scripts inside `app_storefront_base` to make a quick fix — for example, directly patching `checkout.isml` in the base cartridge instead of overriding it in a custom cartridge.

**What goes wrong:** Every SFRA version upgrade ships a new `app_storefront_base`. Direct modifications create merge conflicts on upgrade, require manual re-patching each time, and break the cartridge path model. The modification is also invisible to other developers who assume the base cartridge is stock.

**Correct approach:** Create a custom cartridge (e.g., `app_custom_mystore`), place the overriding file at the same relative path (`cartridge/templates/default/checkout/checkout.isml`), and position the custom cartridge to the left of `app_storefront_base` in the site's cartridge path. The override is isolated, versioned separately, and survives base cartridge upgrades.
