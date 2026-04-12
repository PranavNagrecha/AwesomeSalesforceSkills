# Examples — Digital Storefront Requirements

## Example 1: SFRA Brand Overlay Cartridge for a Retail Merchant

**Context:** A fashion retailer has an existing SFRA storefront running `app_storefront_base` v6.3.0. They need to apply a new brand refresh — updated color palette, new typography (Google Fonts), logo swap, and custom header layout — without disrupting their SFRA upgrade path.

**Problem:** The development team initially proposed modifying `app_storefront_base` templates directly. This would have worked for the initial launch but would have made every future SFRA security patch or feature update a multi-day merge effort, since the base cartridge is a Salesforce-maintained reference that receives regular updates.

**Solution:**

The correct approach is to create an overlay cartridge named `app_custom_retailerstore` containing only the files that deviate from the base:

```
app_custom_retailerstore/
├── cartridge/
│   ├── static/
│   │   └── default/
│   │       └── css/
│   │           └── brand.css          ← compiled brand CSS (colors, fonts, spacing)
│   ├── templates/
│   │   └── default/
│   │       └── components/
│   │           └── header/
│   │               └── pageHeader.isml  ← header template override only
│   └── package.json
```

Business Manager cartridge path:

```
app_custom_retailerstore:app_storefront_base
```

Brand CSS imports the Google Font and overrides Bootstrap 4 CSS custom properties:

```css
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&display=swap');

:root {
    --color-primary: #1a1a2e;
    --color-secondary: #e94560;
    --font-family-base: 'Playfair Display', Georgia, serif;
}
```

**Why it works:** Only the files that differ from the base are present in `app_custom_retailerstore`. All other pages and components continue to resolve from `app_storefront_base`, which remains unmodified and upgradeable. When Salesforce releases a new SFRA version, the overlay cartridge requires minimal or no changes.

---

## Example 2: Accessibility Gap Analysis Before Launch

**Context:** A healthcare accessories merchant is launching an SFRA storefront. Their legal team has flagged WCAG 2.1 AA compliance as a launch requirement due to the risk of ADA-related complaints. The development team claims Bootstrap 4 "handles accessibility."

**Problem:** The team has not run any accessibility testing. SFRA's Bootstrap 4 scaffold passes some automated checks but fails several WCAG 2.1 AA criteria out of the box, particularly around color contrast, focus indicators, and dynamic ARIA in the cart drawer.

**Solution:**

Run axe DevTools against the five critical page types and produce a gap inventory:

```
Page: Product Listing Page (PLP)
Criterion: 1.4.3 Contrast (Minimum) — FAIL
  Element: .product-tile .price (color #999 on #fff, ratio 2.85:1, minimum 4.5:1)
  Fix: Override --color-price in app_custom_healthstore/cartridge/static/default/css/brand.css

Criterion: 2.4.7 Focus Visible — FAIL
  Element: .add-to-wishlist button (no visible focus ring)
  Fix: Add :focus-visible outline in overlay cartridge CSS

Page: Cart (cart.isml)
Criterion: 4.1.3 Status Messages — FAIL
  Element: Cart quantity update success toast has no aria-live region
  Fix: Override cart.isml in app_custom_healthstore to add role="status" aria-live="polite"
```

Remediation is applied entirely in `app_custom_healthstore`, keeping fixes isolated and testable. After remediation, the team re-runs axe and adds a Lighthouse CI step to the deployment pipeline to catch regressions.

**Why it works:** The gap analysis prevents the team from shipping a legally non-compliant storefront by treating accessibility as a verifiable engineering requirement, not an assumed default of the framework.

---

## Anti-Pattern: Assuming PWA Kit Deploys via WebDAV

**What practitioners do:** A developer new to PWA Kit has an SFRA deployment background. They build the PWA Kit storefront locally, compile the bundle, and attempt to upload it to the SFCC instance via WebDAV at `/cartridges/` — the same method used for SFRA cartridges.

**What goes wrong:** The upload succeeds without error (WebDAV accepts the files) but nothing changes on the storefront. PWA Kit code does not run from the SFCC instance cartridge path — it runs on Salesforce Managed Runtime (a separate Node.js hosting environment). The WebDAV upload is ignored entirely.

**Correct approach:** Deploy PWA Kit to Managed Runtime using the `sfcc-ci` CLI:

```bash
# Deploy to Managed Runtime
sfcc-ci code:deploy --code-version pwa-kit-v1.2.0 --instance example.dx.commercecloud.salesforce.com

# Push to Managed Runtime environment
sfcc-ci sandbox:realm:list  # confirm Managed Runtime environment ID
# Then deploy via Managed Runtime dashboard or REST API
```

Or use the Managed Runtime dashboard at `runtime.commercecloud.salesforce.com` to upload the built bundle directly. Never treat a PWA Kit project like a cartridge deployment.
