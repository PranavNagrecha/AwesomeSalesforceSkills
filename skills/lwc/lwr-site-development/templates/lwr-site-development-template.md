# LWR Site Development Checklist

Use this template when building or modifying components, themes, or layouts for an LWR-based Experience Cloud site.

---

## Site Context

| Item | Value |
|---|---|
| Site template | Build Your Own (LWR) / Microsite (LWR) |
| Org version | e.g. Spring '26 |
| Enhanced LWR site? (Winter '23+) | Yes / No |
| Auth model | Authenticated / Public / Mixed |
| Guest users need data access? | Yes / No |
| CDN enabled? | Yes / No |

---

## Component Inventory

| Component Name | Role | Target(s) | Exposes Properties? |
|---|---|---|---|
| (component name) | Page content / Theme layout / Page layout / Navigation | `lightningCommunity__Page` / `__Theme_Layout` / `__Page_Layout` | Yes / No |

---

## Pre-Build Checklist

- [ ] Confirmed no Aura components in scope — all components will be LWC
- [ ] Confirmed all Aura navigation API patterns replaced with `lightning/navigation` and `NavigationMixin`
- [ ] Identified which `@salesforce` modules are needed and whether any require republishing on change
- [ ] Guest user preferences configured if any public pages exist (Allow guest users to access public APIs; Let guest users view asset files)

---

## Component Build Checklist

For each LWC component:

- [ ] `isExposed` set to `true` in js-meta.xml (required for Experience Builder Components panel)
- [ ] Correct `lightningCommunity__*` target declared in `<targets>`
- [ ] If editable properties needed: `lightningCommunity__Default` added to `<targets>` and `<targetConfig>` defined
- [ ] All property names use camelCase (never PascalCase)
- [ ] Theme layout: default unnamed `<slot></slot>` present in template for main content
- [ ] Theme layout: named slots for header and footer regions
- [ ] Page/Theme layout: `@slot` JSDoc annotations placed directly before `export default class` (no intervening code)
- [ ] `data-f6-region` attributes on major layout regions (header, main, footer) for keyboard accessibility
- [ ] No `document.domain`, `document.location`, `window.location`, or `window.top` in component JS
- [ ] No hardcoded hex brand colors in component CSS — `--dxp` hooks used instead
- [ ] Dynamic imports (if any) use literal string paths — no template literals or variables in import path

---

## Theming Checklist

- [ ] Brand colors reference `var(--dxp-g-brand)` and `var(--dxp-g-brand-contrast)`
- [ ] Page/section backgrounds reference `var(--dxp-g-root)` and `var(--dxp-g-root-contrast)`
- [ ] Section-specific color palette resets `--dxp-g-root` scoped to the section element
- [ ] Custom fonts added via Head Markup if design system requires non-SLDS fonts
- [ ] SLDS removed from Head Markup if site uses a completely custom design system
- [ ] DXP branding stylesheets present in Head Markup for sites created before Summer '21

---

## Screen-Responsive Properties (if applicable)

- [ ] Properties needing screen-specific values declare `screenResponsive="true"` and `exposedTo="css"` in js-meta.xml
- [ ] Component CSS uses `--dxp-c-{l/m/s}-{property-kebab-case}` CSS variables
- [ ] Media query breakpoints match platform standard: tablet ≤64em, mobile ≤47.9375em

---

## Navigation Checklist

- [ ] All in-site navigation uses `NavigationMixin` from `lightning/navigation`
- [ ] `comm__namedPage` references use `name` attribute (not deprecated `pageName`)
- [ ] `standard__namedPage` is not used (unsupported in LWR — use `comm__namedPage`)
- [ ] `objectApiName` included for `standard__recordPage` and `standard__recordRelationshipPage` navigations
- [ ] No `comm__loginPage` navigation type used (navigate to login as a regular `comm__namedPage` instead)

---

## Publish and Deploy Checklist

- [ ] All component changes deployed to the org before publish
- [ ] Site republished in Experience Builder after all component / label / Apex signature changes
- [ ] Live site URL (not preview URL) verified after publish
- [ ] Publish scheduled during off-peak hours if CDN HTML cache overlap is a concern
- [ ] Route count checked — under 250 for optimal performance, hard limit is 500

---

## Post-Deploy Verification

- [ ] Component appears in Experience Builder Components panel (drag-and-drop roles)
- [ ] Theme layout available under Settings > Theme and assignable to pages
- [ ] Page layout appears in page layout selector
- [ ] Editable properties appear in the component property panel with correct types and defaults
- [ ] Brand color changes in Theme panel propagate to all `--dxp`-hooked components
- [ ] Guest user public pages load without authentication prompts (if applicable)
- [ ] Screen reader and F6 keyboard navigation works on theme layout regions

---

## Notes

Record any deviations from the standard pattern and the reason:

-
