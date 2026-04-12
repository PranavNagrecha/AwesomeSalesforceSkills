# Digital Storefront Requirements — Work Template

Use this template when gathering, evaluating, or documenting requirements for a Salesforce B2C Commerce (SFCC) digital storefront.

**NOT for Experience Cloud (Digital Experiences, LWR portals, Community Cloud) — use the Experience Cloud requirements skill for those.**

---

## Scope

**Skill:** `digital-storefront-requirements`

**Project / Merchant:** _______________________________________________

**Request summary:** (fill in what the user asked for)

**Existing architecture:** [ ] SFRA  [ ] PWA Kit / Composable Storefront  [ ] New build (undecided)

---

## 1. Platform Confirmation

- [ ] Confirmed this is B2C Commerce (SFCC) — Business Manager URL: `*.commercecloud.salesforce.com`
- [ ] Confirmed NOT Experience Cloud, WebStore, or LWR portal
- [ ] SFRA version (if applicable): _______________
- [ ] Custom cartridge inventory (list existing app_custom_* cartridges): _______________

---

## 2. Architecture Decision (New Builds Only)

Skip this section if the merchant already has a running storefront.

| Criterion | Answer | Implication |
|---|---|---|
| Team has React / Node.js skills? | Yes / No | Yes → PWA Kit viable; No → SFRA lower risk |
| PWA installability required? | Yes / No | Yes → PWA Kit required; SFRA cannot do this |
| Existing SFRA cartridge investment? | Yes / No | Large investment → migration cost is high |
| External headless CMS needed? | Yes / No | Yes → PWA Kit composable model preferred |
| Timeline pressure (< 6 months)? | Yes / No | Yes → SFRA has faster onboarding curve |

**Architecture decision:** [ ] SFRA  [ ] PWA Kit / Composable Storefront

**Rationale:** _______________________________________________

**Architecture Decision Record (ADR) location:** _______________________________________________

---

## 3. Branding Requirements

**Brand assets provided:**
- [ ] Logo (SVG preferred): _______________
- [ ] Color palette (hex values): Primary: ___ Secondary: ___ Accent: ___ Background: ___
- [ ] Typography: Heading font: ___ Body font: ___ Source (Google Fonts / licensed): ___
- [ ] Design tokens / style guide: _______________

**Overlay cartridge name (SFRA):** `app_custom_` _______________

**Template overrides required** (list ISML files that differ from app_storefront_base):
- _______________
- _______________

**CSS overrides scope:**
- [ ] Colors and typography only (CSS variables / SCSS overrides)
- [ ] Layout modifications (grid, spacing changes)
- [ ] Component-level redesigns (header, footer, product tile)

**Verification:** [ ] app_storefront_base will NOT be modified directly

---

## 4. Content Management Requirements

**Content authoring persona:**
- [ ] Developer (code-only content updates acceptable)
- [ ] Merchandiser / marketer (needs Business Manager visual tools)
- [ ] External CMS authors (headless CMS required)

**Content management approach:**
- [ ] Page Designer (SFRA / PWA Kit with Managed Runtime Preview)
- [ ] Content Slots (SFRA — global, category, product, folder, content contexts)
- [ ] Headless CMS (specify: _________________)
- [ ] Combination: _______________

**Content slot contexts needed:**
- [ ] Global (all pages)
- [ ] Homepage hero
- [ ] Category (PLP) banners
- [ ] Product (PDP) cross-sell
- [ ] Cart recommendations
- [ ] Other: _______________

**Page Designer components needed (list custom components):**
- _______________ — descriptor location: _______________
- _______________ — descriptor location: _______________

---

## 5. Personalization Requirements

**Personalization approach:**
- [ ] Customer Groups (segment-based promotions and pricing)
- [ ] Einstein Recommenders (ML-driven product recommendations)
- [ ] Data Cloud audience activation (real-time segments → PWA Kit components)
- [ ] None required at launch

**Customer groups needed:**
| Group Name | Segment Definition | Content / Price Impact |
|---|---|---|
| ___ | ___ | ___ |
| ___ | ___ | ___ |

**Einstein Recommender zones (if applicable):**
| Page | Zone Name | Fallback Content (for warm-up period) |
|---|---|---|
| Homepage | ___ | ___ |
| PDP | ___ | ___ |
| Cart | ___ | ___ |

- [ ] Einstein Recommenders license confirmed
- [ ] Warm-up period (2–4 weeks) accounted for in launch plan
- [ ] Fallback content defined for recommendation zones at launch

---

## 6. Mobile Experience Requirements

**Mobile experience type:**
- [ ] Responsive web design (Bootstrap 4 — SFRA default; also supported in PWA Kit)
- [ ] PWA installability (Add to Home Screen, service worker) — requires PWA Kit
- [ ] Offline browsing support — requires PWA Kit
- [ ] Native mobile app (outside SFCC scope — separate project)

**Responsive breakpoints to test (SFRA):**
- [ ] 320px (small mobile)
- [ ] 768px (tablet)
- [ ] 1024px (desktop)
- [ ] Other: _______________

**Core Web Vitals targets:**
- LCP (Largest Contentful Paint): ___ seconds (Google recommendation: < 2.5s)
- FID / INP (Interaction to Next Paint): ___ ms (Google recommendation: < 200ms)
- CLS (Cumulative Layout Shift): ___ (Google recommendation: < 0.1)

---

## 7. Accessibility Requirements

**Compliance target:** [ ] WCAG 2.1 AA  [ ] WCAG 2.1 AAA  [ ] Internal standard: _______________

- [ ] Acknowledged: SFRA Bootstrap 4 does NOT satisfy WCAG AA by default
- [ ] Acknowledged: Accessibility compliance is the merchant's legal responsibility
- [ ] Professional accessibility audit scheduled (vendor: _______________ date: _______________)
- [ ] Automated scan baseline completed (tool: axe / Lighthouse / other: _______________)

**Gap analysis summary** (from baseline scan):

| WCAG Criterion | Status | Remediation Owner | Fix Location |
|---|---|---|---|
| 1.4.3 Contrast (Minimum) | Pass / Fail / Not tested | ___ | app_custom_* CSS |
| 2.4.7 Focus Visible | Pass / Fail / Not tested | ___ | app_custom_* CSS |
| 4.1.3 Status Messages (cart/checkout) | Pass / Fail / Not tested | ___ | ISML template override |
| 3.3.1 Error Identification (forms) | Pass / Fail / Not tested | ___ | ISML template override |
| 2.1.1 Keyboard (all interactions) | Pass / Fail / Not tested | ___ | ___ |

**Accessibility CI integration:** [ ] axe-core in deployment pipeline  [ ] Lighthouse CI  [ ] Manual regression schedule

---

## 8. Requirements Artifacts Delivered

- [ ] Architecture recommendation document / ADR
- [ ] Branding implementation plan (overlay cartridge, file list, design tokens)
- [ ] Content management decision with authoring persona mapping
- [ ] Personalization scope (Einstein zones, customer group definitions)
- [ ] Mobile experience checklist
- [ ] Accessibility gap analysis with remediation backlog

---

## Notes

(Record any deviations from the standard pattern, merchant-specific constraints, or open questions.)
