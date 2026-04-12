---
name: digital-storefront-requirements
description: "Use when gathering or evaluating requirements for a Salesforce Commerce Cloud digital storefront — including branding strategy, content management approach, personalization, mobile experience, and accessibility compliance. Trigger keywords: SFRA branding, PWA Kit storefront, composable storefront, storefront accessibility, WCAG Commerce Cloud, overlay cartridge branding, mobile storefront, storefront personalization, content slots. NOT for Experience Cloud (Lightning Web Runtime portals, Digital Experiences) requirements — those are covered separately."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Security
  - User Experience
triggers:
  - "how do I brand a Salesforce Commerce Cloud storefront without modifying app_storefront_base"
  - "does SFRA satisfy WCAG 2.1 AA accessibility requirements out of the box for our storefront"
  - "should we build our new Commerce Cloud storefront on SFRA or PWA Kit composable storefront"
  - "how do we manage content and personalization in a B2C Commerce storefront using content slots"
  - "what are the mobile experience requirements for an SFRA storefront versus a PWA Kit storefront"
tags:
  - commerce-cloud
  - SFRA
  - PWA-kit
  - storefront
  - accessibility
  - branding
  - personalization
inputs:
  - "Target storefront architecture (SFRA or PWA Kit / Composable Storefront)"
  - "Brand identity assets (logo, color palette, typography, design tokens)"
  - "Accessibility compliance target (WCAG 2.1 AA or higher)"
  - "Content management approach (Page Designer, content slots, headless CMS)"
  - "Personalization requirements (customer segments, Einstein recommendations)"
  - "Mobile experience expectations (responsive vs. native app vs. PWA installability)"
outputs:
  - "Storefront architecture recommendation (SFRA vs. PWA Kit) with justification"
  - "Branding implementation plan specifying overlay cartridge naming and override scope"
  - "Accessibility gap analysis identifying what SFRA does and does not provide"
  - "Content management decision: Page Designer vs. content slots vs. headless CMS"
  - "Personalization requirements mapped to Einstein Recommenders or segment-based rules"
  - "Mobile experience checklist for the chosen architecture"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Digital Storefront Requirements

This skill activates when a practitioner is gathering, assessing, or implementing requirements for a Salesforce Commerce Cloud (B2C Commerce / SFCC) digital storefront — covering architecture selection, branding, content management, personalization, mobile experience, and accessibility compliance. It is strictly for the proprietary SFCC infrastructure and does not apply to Experience Cloud portals or LWR-based Digital Experiences.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the target platform is B2C Commerce (SFCC), accessed via Business Manager at `*.commercecloud.salesforce.com`. If the user mentions WebStore, Digital Experiences, LWR, or Lightning Community, stop and route to the appropriate Experience Cloud skill.
- Identify whether the merchant is on SFRA (existing implementation) or is evaluating a new build — new builds should default to PWA Kit / Composable Storefront per Salesforce's current architectural guidance.
- Clarify the accessibility compliance target explicitly. Merchants often assume SFRA provides WCAG 2.1 AA compliance by default because it ships with Bootstrap 4. It does not. Accessibility compliance is the merchant's legal responsibility and requires a dedicated audit and remediation effort.
- Determine whether branding changes are cosmetic (CSS/fonts/colors) or structural (template overrides). Structural changes require overlay cartridges and cannot be applied inside `app_storefront_base`.

---

## Core Concepts

### SFRA vs. PWA Kit: Two Distinct Architectures

Salesforce B2C Commerce offers two primary storefront reference architectures:

**SFRA (Storefront Reference Architecture):**
- Server-side rendered, Bootstrap 4 base, cartridge-based extensibility
- Suitable for merchants with existing SFRA investments or teams without React expertise
- Customized exclusively through overlay cartridges positioned left of `app_storefront_base` in the cartridge path
- Page Designer and content slots are the primary CMS tools
- Mobile experience is responsive web (Bootstrap 4 grid) — no PWA installability by default

**PWA Kit / Composable Storefront:**
- React / Node.js frontend, headless, powered by Salesforce Commerce APIs (SCAPI)
- Recommended by Salesforce for new storefront builds as of Spring '25
- Decoupled from the SFCC instance — content and commerce data are fetched via APIs
- Enables PWA installability, offline support, and React-native developer tooling
- Integrates with Headless Commerce Einstein recommendations and Data Cloud personalization

**Decision rule:** For new projects, default to PWA Kit unless the merchant has existing SFRA customizations that would be prohibitively expensive to migrate, or if the development team lacks React/Node.js capability.

### SFRA Branding via Overlay Cartridges

SFRA branding is implemented exclusively through overlay cartridges. The naming convention mandated by Salesforce is `app_custom_*` (e.g., `app_custom_mystore`). This cartridge sits to the LEFT of `app_storefront_base` in the cartridge path, overriding only the specific templates, stylesheets, and scripts that differ from the base.

Files you override in `app_custom_*`:
- `cartridge/static/default/css/` — compiled SCSS or CSS overrides
- `cartridge/templates/default/` — ISML template overrides for layout and components
- `cartridge/client/default/js/` — JavaScript overrides for storefront behavior

You must never modify `app_storefront_base` directly. Direct modification breaks upgrade compatibility and creates merge conflicts on every SFRA release upgrade.

### Accessibility Compliance (WCAG 2.1 AA)

SFRA ships with Bootstrap 4, which implements some semantic HTML and ARIA patterns, but SFRA does not certify or guarantee WCAG 2.1 AA compliance for any storefront. The areas SFRA partially addresses include basic keyboard focus order and some ARIA landmark roles. The areas it does NOT address include:

- Sufficient color contrast for all default theme colors
- Focus visibility for all interactive elements
- Complete screen reader support for dynamic cart and checkout interactions
- Accessible error identification and suggestion in checkout forms
- Accessible session timeout warnings

**Accessibility compliance is the merchant's sole legal responsibility.** SFRA provides partial scaffolding. Full AA compliance requires a dedicated third-party audit (e.g., Deque, Level Access), a remediation backlog in the custom overlay cartridge, and ongoing regression testing after every release.

PWA Kit has the same posture — the React component library provides some accessible patterns, but full WCAG compliance still requires merchant-side audit and testing.

### Content Management: Page Designer and Content Slots

SFRA storefronts use two primary content mechanisms:

**Content Slots** — merchandiser-controlled regions bound to a context (global, category, product, folder, or content page). They accept content assets and product sets. Content slots are configured in Business Manager under `Merchant Tools > Content > Slot Configurations`.

**Page Designer** — a drag-and-drop page builder available in Business Manager (`Merchant Tools > Content > Page Designer`). It allows non-technical users to compose pages using pre-built components and custom components registered in a page designer-enabled cartridge.

**Headless CMS (PWA Kit):** For composable storefronts, the Page Designer can still serve as the authoring tool if the merchant uses the Storefront Preview feature and Managed Runtime. Alternatively, an external headless CMS (Contentful, Contentstack) can serve content via API.

### Personalization

SFRA personalization relies on:
- **Customer Groups** — segment-based rules for promotions, pricing, and content slot assignments
- **Einstein Recommendations** — product recommendation carousels powered by ML (requires Einstein Recommenders license); configured per-zone in Business Manager
- **Geolocation and session context** — used in content slot conditions

PWA Kit / Composable Storefront adds:
- **Data Cloud audience activation** — real-time segment membership from Data Cloud can drive personalized components
- **Einstein Recommenders via SCAPI** — same recommendation engine exposed through the commerce API

---

## Common Patterns

### Pattern: SFRA Brand Overlay Cartridge Setup

**When to use:** A merchant on SFRA needs to apply custom branding (logo, color palette, typography, component layout changes) without modifying the base cartridge.

**How it works:**
1. Create a new cartridge named `app_custom_[brand]` following the `app_custom_*` convention.
2. Copy only the files that need to change from `app_storefront_base` into the equivalent path in `app_custom_[brand]`. Do not copy the entire base — only override what differs.
3. Place `app_custom_[brand]` to the LEFT of `app_storefront_base` in the Business Manager cartridge path for the site.
4. Compile SCSS overrides in `cartridge/static/default/css/` using the brand's design tokens.
5. Validate that the base cartridge renders unchanged pages correctly (pages with no overridden templates should still resolve from `app_storefront_base`).

**Why not the alternative:** Forking `app_storefront_base` creates a permanent deviation from the SFRA upgrade path. Every Salesforce SFRA release requires a painful manual merge.

### Pattern: Accessibility Gap Analysis for SFRA Storefronts

**When to use:** A merchant needs to determine their WCAG 2.1 AA compliance gap before launch or after a regulatory demand.

**How it works:**
1. Document the WCAG 2.1 AA success criteria (50 criteria at AA level) in a tracking spreadsheet.
2. For each criterion, run an automated scan (axe DevTools, Lighthouse) against key storefront pages: homepage, PLP, PDP, cart, checkout.
3. Mark criteria as Pass, Fail, or Manual Review Required.
4. Triage Fail items: categorize as fixable in `app_custom_*` (CSS, ARIA, template changes) vs. requiring core ISML override.
5. Remediate all Fail items in the overlay cartridge. Re-run automated scans, then perform manual keyboard and screen reader testing (NVDA + Firefox, VoiceOver + Safari).
6. Establish ongoing accessibility regression tests in the CI pipeline (axe-core integration).

**Why not the alternative:** Relying on Bootstrap 4's semantic HTML alone leaves color contrast, dynamic ARIA, and form error association gaps that will fail a professional audit.

### Pattern: Architecture Selection for a New Storefront Build

**When to use:** A merchant is starting a new B2C Commerce storefront and has not committed to SFRA or PWA Kit.

**How it works:**
1. Assess team capabilities: does the development team have React/Node.js expertise? If no, SFRA is lower risk.
2. Assess integration complexity: does the merchant need a native app, PWA installability, or third-party headless CMS? If yes, PWA Kit is the better fit.
3. Assess time horizon: is this a short-term project (< 1 year)? SFRA has faster onboarding. Long-term investment? PWA Kit is the Salesforce-recommended architecture for the future.
4. Assess existing cartridge investments: if the merchant has 50+ cartridges of SFRA customization, a PWA Kit migration is a multi-year effort.
5. Document the decision in an Architecture Decision Record (ADR) with the chosen architecture, rationale, and constraints.

**Why not the alternative:** Starting on SFRA for a greenfield project in 2025+ creates future migration debt — Salesforce's product investment is increasingly concentrated in the composable storefront / SCAPI direction.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New storefront build, team has React skills | PWA Kit / Composable Storefront | Salesforce-recommended architecture for new builds; SCAPI-driven, composable |
| New storefront build, team lacks React skills | SFRA with app_custom_* overlay | Lower technical barrier; existing SFRA ecosystem of cartridges and partners |
| Existing SFRA, branding update needed | app_custom_* overlay cartridge only | Preserves upgrade path; never modify app_storefront_base directly |
| WCAG AA compliance required for SFRA | Dedicated audit + remediation in overlay cartridge | SFRA Bootstrap 4 does not satisfy AA by default; merchant owns compliance |
| Content management by non-technical merchandisers | Page Designer (SFRA) or Managed Runtime Preview (PWA Kit) | Both provide visual authoring without code changes |
| Personalization with real-time segments | Data Cloud + PWA Kit | Data Cloud audience activation integrates best with composable architecture |
| PWA installability or offline support required | PWA Kit only | SFRA is server-rendered; no PWA installability capability |
| Mobile optimization for existing SFRA | Responsive CSS overrides in app_custom_* | Bootstrap 4 grid handles responsive layout; customize breakpoints in overlay |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm platform scope** — verify the target is B2C Commerce (SFCC) with a Business Manager URL. If the user mentions Experience Cloud, Digital Experiences, or LWR portals, stop and route to the correct skill. Document the current architecture (SFRA or PWA Kit) or confirm this is a new build decision.
2. **Select or confirm storefront architecture** — for new builds, apply the architecture decision guidance above. Document the decision with rationale. For existing SFRA implementations, confirm the current SFRA version and custom cartridge inventory before scoping any requirements work.
3. **Define branding requirements** — collect the brand's design tokens (colors, typography, spacing scale) and logo assets. Specify which SFRA templates or PWA Kit components need visual overrides. For SFRA, name the overlay cartridge following the `app_custom_*` convention and list files to override.
4. **Define content management requirements** — determine who will author content (developer, merchandiser, or marketing). Map to Page Designer, content slots, or headless CMS. Document the content types and authoring frequency.
5. **Define personalization requirements** — enumerate customer segments that drive content or pricing variations. Identify Einstein Recommender zones (homepage, PDP, cart). For Data Cloud-driven personalization, confirm Data Cloud license and audience activation setup.
6. **Conduct accessibility gap analysis** — run automated scans (Lighthouse, axe) on key storefront pages. Document WCAG 2.1 AA criteria status. For SFRA, do not assume Bootstrap 4 satisfies any criterion without testing. Plan remediation items in the overlay cartridge backlog.
7. **Produce requirements artifacts** — deliver the architecture recommendation, branding implementation plan, content management decision, personalization scope, and accessibility gap analysis before implementation begins.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Storefront architecture (SFRA vs. PWA Kit) is documented with explicit rationale and constraints
- [ ] Branding plan specifies overlay cartridge named app_custom_* and lists only files that deviate from base
- [ ] app_storefront_base is not modified directly — all overrides live in the overlay cartridge
- [ ] Accessibility compliance approach is documented; SFRA Bootstrap 4 assumption is not cited as sufficient for WCAG AA
- [ ] Content management approach (Page Designer / content slots / headless CMS) is matched to authoring persona
- [ ] Personalization requirements are mapped to specific Einstein Recommender zones or customer group rules
- [ ] Mobile experience requirements are addressed: responsive (SFRA) vs. PWA installability (PWA Kit)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **SFRA Bootstrap 4 does NOT satisfy WCAG 2.1 AA by default** — Bootstrap 4's semantic HTML and some ARIA patterns give a false sense of accessibility compliance. SFRA does not certify any WCAG criterion. Common failures include insufficient color contrast on default theme colors, missing focus indicators on custom components, and incomplete ARIA on dynamic cart interactions. Merchants have faced legal exposure (ADA lawsuits) after assuming SFRA was compliant.
2. **SFRA branding must use overlay cartridges with the app_custom_* prefix — no exceptions** — Directly editing `app_storefront_base` works locally but creates permanent divergence from SFRA's upgrade path. Every SFRA release (Salesforce publishes multiple per year) requires a manual merge of all changes made to the base. Teams that fork the base cartridge end up unable to take security or feature updates.
3. **Page Designer components must be explicitly registered — they do not auto-discover** — Custom Page Designer components require a JSON descriptor in the cartridge and registration in BM. A common mistake is building the React/ISML component without the descriptor, leading to components that never appear in the Page Designer UI.
4. **Einstein Recommenders require a separate license and onboarding period** — Einstein product recommendations are not included in a base SFCC license. They require an Einstein Recommenders add-on, a data ingestion period (typically 2–4 weeks of behavioral data), and zone configuration in Business Manager before recommendations are populated. Projects that scope Einstein Recommenders as a day-1 launch feature routinely hit this delay.
5. **PWA Kit Managed Runtime has a separate deployment pipeline from Business Manager** — PWA Kit storefronts deploy to Salesforce Managed Runtime (a Node.js hosting service), not to the SFCC instance. Teams unfamiliar with this architecture mistakenly try to upload PWA Kit code via WebDAV (the SFRA deployment method), which has no effect. PWA Kit deployment uses the `sfcc-ci` CLI or the Managed Runtime dashboard.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Architecture recommendation | SFRA vs. PWA Kit decision with rationale, constraints, and migration considerations |
| Branding implementation plan | Overlay cartridge name, file override list, design token mapping |
| Accessibility gap analysis | WCAG 2.1 AA criterion status (Pass/Fail/Manual), remediation backlog |
| Content management decision | Authoring tool selection with persona mapping |
| Personalization scope | Einstein Recommender zones, customer group rules, Data Cloud audience activation plan |
| Mobile experience checklist | Responsive breakpoint plan (SFRA) or PWA installability requirements (PWA Kit) |

---

## Related Skills

- admin/b2c-commerce-store-setup — use for Business Manager site creation, cartridge path setup, search index operations, and quota management on an SFCC instance
- admin/b2b-vs-b2c-requirements — use to select the correct Salesforce Commerce platform (B2B Commerce on Lightning vs. B2C Commerce / D2C) before committing to a storefront architecture
- admin/commerce-checkout-flow-design — use when requirements extend into checkout UX and payment integration design
