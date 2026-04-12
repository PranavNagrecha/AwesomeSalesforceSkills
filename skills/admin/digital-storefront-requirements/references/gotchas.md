# Gotchas — Digital Storefront Requirements

Non-obvious Salesforce B2C Commerce platform behaviors that cause real production problems in digital storefront requirements and implementation.

## Gotcha 1: SFRA Bootstrap 4 Does NOT Satisfy WCAG 2.1 AA by Default

**What happens:** Teams cite Bootstrap 4's semantic HTML and ARIA usage as evidence that their SFRA storefront is WCAG 2.1 AA compliant. They launch without running a professional accessibility audit. Post-launch automated scans or third-party audits reveal multiple Level AA failures — typically insufficient color contrast (criterion 1.4.3), missing focus indicators (criterion 2.4.7), incomplete ARIA in dynamic cart/checkout interactions (criterion 4.1.3), and inaccessible error messages in checkout forms (criterion 3.3.1).

**When it occurs:** Any SFRA storefront launched without an independent accessibility audit. The Bootstrap 4 grid and some ARIA landmark roles give a misleadingly high Lighthouse accessibility score (Lighthouse does not test color contrast in full context, dynamic ARIA, or keyboard trap scenarios).

**How to avoid:** Treat accessibility compliance as an explicit engineering deliverable with its own backlog. Run axe DevTools or equivalent against all key page types (homepage, PLP, PDP, cart, checkout, account) before launch. Assign all failures to the `app_custom_*` overlay cartridge for remediation. Establish Lighthouse CI in the deployment pipeline for ongoing regression protection. Note in project documentation that WCAG AA compliance is the merchant's legal responsibility — not Salesforce's.

---

## Gotcha 2: SFRA Branding Must Use app_custom_* Overlay Cartridges — Direct Edits to app_storefront_base Break the Upgrade Path

**What happens:** A developer edits templates or SCSS directly in `app_storefront_base` to apply brand styling quickly. The initial launch works correctly. When Salesforce publishes a new SFRA minor version (which happens multiple times per year, often including security fixes), upgrading requires merging the SFRA diff against a forked base cartridge. The merge is error-prone and time-consuming. Teams that fork the base often get stuck on old SFRA versions and cannot take security patches — a direct security risk.

**When it occurs:** Any time a developer edits a file inside `app_storefront_base` rather than creating an equivalent override in an `app_custom_*` cartridge positioned to the left in the cartridge path.

**How to avoid:** Enforce a code review rule: any pull request that modifies a file under `app_storefront_base/` is rejected. All customizations live in a cartridge named `app_custom_[brand]`. Only the files that differ from the base are included in the overlay cartridge — do not wholesale copy the base. Document the overlay cartridge naming convention and cartridge path order in the project README and onboarding guide.

---

## Gotcha 3: Page Designer Custom Components Require Explicit JSON Descriptor Registration

**What happens:** A developer builds a custom Page Designer component (an ISML template with data attributes) and deploys it via the overlay cartridge. The merchandising team reports the component never appears in the Page Designer drag-and-drop palette. The component exists in Business Manager's component list (accessible via direct URL) but is invisible to non-technical users.

**When it occurs:** When the developer creates the ISML template and JavaScript but omits or misconfigures the JSON descriptor file at `cartridge/experience/components/[componentType]/[componentId].json`. Page Designer scans registered descriptors to populate the palette — without a valid descriptor the component is not surfaced.

**How to avoid:** For every Page Designer component, create both the ISML rendering template AND the companion JSON descriptor. The descriptor must declare `name`, `description`, `group`, and the `attribute` definitions that map to Page Designer input fields. Test by logging into Business Manager as a non-admin merchandiser user and confirming the component appears in the visual palette before marking the component done.

---

## Gotcha 4: Einstein Recommenders Require a Separate License and a Behavioral Data Warm-Up Period

**What happens:** A project plan includes Einstein product recommendations on the homepage, PDP, and cart as day-1 features. Development completes the integration (API calls and rendering components). On launch day, all recommendation zones render empty carousels. The Einstein Recommenders service has no behavioral data to drive recommendations because the storefront only just launched.

**When it occurs:** When Einstein Recommenders are scoped as launch features without accounting for (a) the separate Einstein Recommenders add-on license procurement, and (b) the 2–4 week behavioral data ingestion warm-up period required before the ML model produces meaningful recommendations.

**How to avoid:** Confirm Einstein Recommenders license status during requirements gathering, not during implementation. Scope the recommender zones as a post-launch feature that goes live 3–4 weeks after the storefront opens to traffic. During the warm-up period, render fallback content (manually curated product sets, new arrivals, bestsellers from catalog data) in the recommendation zones. Do not promise personalized recommendations as a day-1 feature for a new storefront.

---

## Gotcha 5: Mobile "Responsive" Does Not Mean PWA-Installable — SFRA Cannot Deliver PWA Capabilities

**What happens:** A merchant requests a "mobile-first, app-like experience" with offline browsing and an Add to Home Screen prompt. The development team builds an SFRA storefront with responsive Bootstrap 4 CSS and claims the mobile requirements are met. Post-launch, the merchant reports that their storefront cannot be installed as a PWA, has no offline capability, and does not appear in the browser's install prompt.

**When it occurs:** When requirements use the phrase "mobile-first" or "app-like" without specifying whether they mean responsive web design (achievable in SFRA) or true PWA capabilities (only achievable in PWA Kit / Composable Storefront). SFRA is a server-side rendered architecture — it cannot serve a service worker or web app manifest in the way required for PWA installability.

**How to avoid:** During requirements gathering, explicitly distinguish between: (a) responsive web design — SFRA with Bootstrap 4 satisfies this, (b) PWA installability (Add to Home Screen, service worker, offline support) — requires PWA Kit. If (b) is a confirmed business requirement, the architecture decision must resolve to PWA Kit before any implementation work begins. Do not attempt to retrofit PWA capabilities onto an SFRA storefront.
