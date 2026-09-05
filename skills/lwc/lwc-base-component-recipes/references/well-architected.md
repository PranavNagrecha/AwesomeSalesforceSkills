# Well-Architected Notes — LWC Base Component Recipes

## Relevant Pillars

### Performance

`lightning-record-form`, `lightning-record-edit-form`, and `lightning-record-view-form` all use the UI API under the hood, which batches field reads into a single server call and benefits from platform-level caching. This is significantly more efficient than separate Apex calls per field. Salesforce testing shows `lightning-datatable` performs best with a maximum of 1,000 rows and 5 columns; adding more of either can degrade performance, so paginate, load on infinite scroll, use smaller datasets, and reserve inline editing for critical fields (`lwc_guide data-table-performance` L6309–L6311). Neither `lightning-datatable` nor `lightning-tree-grid` runs on mobile devices at all (`data-table-vs-tree-grid` L5600).

### Reliability

Base components handle their own loading states, error display, and FLS enforcement. This reduces the surface area for reliability issues compared to custom Apex-backed forms that must manually implement each of these concerns. The primary reliability risk is developer-introduced: not wiring `draft-values` reset, using `if:true` to hide forms, or not handling the `onsuccess` / `onerror` events.

### Security

All base form components route through the UI API, which enforces CRUD and FLS at the platform level. A field the running user cannot read or write will be silently omitted or made read-only. This is the correct security posture and should not be bypassed. Developers must not mix base components with unprotected Apex methods that re-expose the same fields without FLS checks.

## Architectural Tradeoffs

**lightning-record-form vs custom Apex form:** Base components give up extensibility (custom field logic, cross-field calculations, conditional required fields) in exchange for automatic FLS, loading state management, and platform caching. For most standard CRUD scenarios, the base component wins. When business logic is complex, invest in a proper Apex-backed form using `@wire(getRecord)` and `updateRecord` — but only after confirming base components cannot meet the requirement.

**lightning-datatable inline editing vs row-level navigation:** Inline editing in `lightning-datatable` is convenient for bulk field updates, but it bypasses record validation rules that only fire on explicit save through the UI API. Validation rules, duplicate rules, and before-save flows still run, but the feedback surface is the generic `lightning-datatable` error column rather than field-level messages. For high-stakes data (financial records, regulated fields), prefer row-level navigation to a full edit form where validation is surfaced clearly.

**lightning-record-view-form vs read-only lightning-record-form:** Both render record fields in read-only mode. `lightning-record-view-form` with `lightning-output-field` gives full layout control and is preferred when field placement matters. `lightning-record-form mode="readonly"` uses the page layout and is faster to scaffold but less predictable across profiles.

## Anti-Patterns

1. **Bypassing FLS with Apex in the same component** — Using `lightning-record-edit-form` alongside a `with sharing` Apex method that reads fields the running user cannot see defeats the security posture. All data paths for a form must respect the same access model. If custom Apex is needed, it must also enforce CRUD/FLS explicitly.

2. **Rebuilding table chrome manually instead of using lightning-datatable** — Developers who use `<template for:each>` with `<input>` elements to create a manually editable table reimplement keyboard navigation, dirty state tracking, accessibility labels, and mobile responsiveness that `lightning-datatable` provides. This is a maintenance burden and an accessibility risk.

3. **Over-fetching fields in the columns array** — Passing every available field through `lightning-datatable` as columns increases payload size and degrades rendering performance. Restrict columns to the minimum required for the use case and use row actions or navigation to expose the full record detail.

## Base-Component-First as an Architecture Position

The choice between a base component, blueprint-derived markup, a custom component and a third-party
web component is an architecture decision with a maintenance cost attached, not a styling preference.
The Developer Guide states the asymmetry plainly: when SLDS updates a blueprint, a component you
built from that blueprint is **not** updated — you must update it by hand — while Salesforce updates
the base components automatically (`lwc_guide create-components-css-slds-blueprint` L1737). Every
blueprint-derived component is therefore a standing liability against future SLDS releases, and the
SLDS 1 → SLDS 2 transition introduced in Spring '25 is the first large bill
(`create-components-css-slds` L1601, `create-components-css-slds1-slds2` L1656–L1668).

Operability follows the same line. Base components implement SLDS blueprint markup that follows the
W3C ARIA Authoring Practices Guide, update their own ARIA attributes as state changes, and conform to
SLDS colour guidelines that meet or exceed WCAG 2.1 AA contrast
(`base-components-accessibility` L4953–L4957). A hand-rolled equivalent inherits none of that and is
audited as your code.

The counterweight is honest: base components make calls to Salesforce APIs such as UI API, Connect
REST API and GraphQL API and are subject to those APIs' end-of-life policies
(`base-components-considerations` L4726), they are platform-dependent (`base-components-containers`
L4709–L4713), and their public surface is only what the Component Reference documents — anything
marked *Reserved for internal use* can change in any release (L4727).

## Composition Cost

Composition is the recommended default because slots produce maintainable, intuitive code
(`base-components-slot` L4914), but it is not free at scale. The guide's own guidance: consider a
flat structure when rendering large numbers of elements through composed components; if you end up
with a heavily composed structure, move logic back up to a parent so it can inline elements, because
*"the number of elements, functions, and event handlers increase component size and has performance
implications especially when you are working with large numbers of such components on a page"*
(`base-components-compose` L4886–L4888). Move expensive operations up the tree, avoid deep copies of
large objects, and avoid forced rerendering (L4888, L4893–L4895).

## Official Sources Used

- LWC Developer Guide — *Base Components Categories* (`base-components-all` L4546–L4690) — the
  catalogue by family, the `lightning-component-name` / `lightning/moduleName` naming split, first-
  available API versions (most 45.0), and the note that base components are not versioned (L4545).
  Backs the catalogue table in SKILL.md and the toast/notification list.
- LWC Developer Guide — *Base Component Composition* (`base-components-compose` L4850–L4895) —
  composition-versus-flat-structure, the parent/child table (L4857–L4866), the flat-structure table
  including `lightning-combobox` `options` and `lightning-datatable` `columns`/`data` (L4873–L4882),
  and the composition performance guidance (L4886–L4888). Backs the "Composition versus flat
  structure" concept and the Composition Cost section above.
- LWC Developer Guide — *Base Components Considerations* and *Global Attributes Support*
  (`base-components-considerations` L4723–L4741; `base-components-patterns-global` L4789–L4812) —
  that the Component Reference is the authority for public attributes, that "Reserved for internal
  use" attributes must be avoided, that `lwc:ref` is the supported way to locate an element, and the
  `lightning-badge` `title` versus `icon-alternative-text` worked example. Backs the package's
  authority notice, the Contract Mistakes table, and Gotcha 11.
- LWC Developer Guide — *Style with Lightning Design System*, *Base Component Design Variations*,
  *SLDS Blueprints* and *Anti-Patterns for Component Styling* (`create-components-css-slds` L1617–L1625;
  `create-components-css-variants` L1680–L1691; `create-components-css-slds-blueprint` L1733–L1748;
  `create-components-css-antipatterns` L1889–L1920) — the base-first argument (L1737), the exact
  `lightning-button` variant list and default (L1620, L1683), the mobile caveat for datatable and
  tabset (L1740–L1741), the styling escalation order, and the obfuscated CSS scope tokens from API
  59.0. Backs the base-component-first decision table and anti-patterns 7, 9 and 10.
- LWC Developer Guide — *Base Components Accessibility* and *Accessibility Attributes*
  (`base-components-accessibility` L4953–L4964; `create-components-accessibility-attributes` L3987–L4010)
  — that base components follow the W3C ARIA APG and update ARIA state automatically, that they meet
  or exceed WCAG 2.1 AA contrast, that the `label` you supply is automatically associated with the
  input, and that rendered `id` values are transformed so `id` selectors must not be used. Backs the
  `label`-required checker rule and the a11y claims in this file.
- LWC Developer Guide — *Compare Base Components*, *Load a Record*, *Edit a Record*,
  *Change the Form Display Density* and *Usage Considerations*
  (`data-get-user-input` L5414–L5431; `data-load-record` L5439–L5450; `data-edit-record` L5489–L5513;
  `data-display-density` L6329–L6347; `data-considerations` L6362–L6376) — the capability matrix
  across the three record\*form components, the four custom events, the absence of built-in Save and
  Cancel on the edit form, the `density` values (`auto`/`compact`/`comfy`; `cozy` unsupported), the
  `lightning-output-field` variants, the record-type-Id requirement, and that the record Id is not
  available on the `submit` event. Backs the Decision Guidance rows and the read-only summary recipe.
- LWC Developer Guide — *Display Data in a Table with Inline Editing*, *Compare lightning-datatable
  and lightning-tree-grid*, *Datatable Accessibility* and *Improve Datatable Performance*
  (`data-table-inline-edit` L5675–L5712; `data-table-vs-tree-grid` L5586–L5600; `data-table-a11y`
  L6215–L6233; `data-table-performance` L6311) — that `key-field` is required, that edits land in
  `draft-values` and clearing `draftValues` hides the footer, that neither datatable nor tree-grid is
  supported on mobile devices, the two-mode keyboard model, and the 1,000-row / 5-column performance
  guidance. Backs Gotchas 2, 5 and 8 and the mobile checker rule.
- LWC Developer Guide — *getPicklistValues*, *getObjectInfo* and *getPicklistValuesByRecordType*
  (`reference-wire-adapters-picklist-values` L14946–L14966; `reference-wire-adapters-object-info`
  L14905–L14915; `reference-wire-adapters-picklist-values-record` L14979–L14991) — that both
  `recordTypeId` and `fieldApiName` are required, that `objectApiName` is not supported on the
  adapter, the `012000000000000AAA` master record type, that picklist values are record-type scoped,
  and that `label` is translated while `value` is the untranslated API name. Backs the combobox
  recipe and Gotcha 7.
- LWC Developer Guide — *Jest Test Patterns and Mock Dependencies* and *Write Jest Tests for Wire
  Service* (`unit-testing-using-jest-patterns` L12622–L12648; `unit-testing-using-wire-utility`
  L12520–L12556) — that the `lightning-stubs` match the API but fire no events, that not all
  properties are reflected as attributes, that slot order must not be assumed, the `moduleNameMapper`
  mechanism, and the emit-after-appendChild rule. Backs the Jest suite in
  `references/code-examples.md`, Gotcha 9 and anti-pattern 8.
- LWC Developer Guide — *Base Components Usage Patterns*, *App Containers Support* and
  *lightning__RecordPage Target* (`base-components-patterns` L4761–L4781; `base-components-containers`
  L4709–L4714; `targets-lightning-record-page` L19335–L19376) — that `lightning/platformShowToastEvent`
  is event-based and unsupported on LWR, that only `lightning/modal` and `lightning/datatable` may be
  extended, that only a subset of base components server-side render on LWR, and the
  `supportedFormFactor` `Large`/`Small` values. Backs Gotcha 10, the container question, and the
  `.js-meta.xml` in `references/code-examples.md`.
- LWC Developer Guide — *Base Components: Aura Vs Lightning Web Components*
  (`migrate-map-aura-lwc-components` L11660–L11740) — the per-component divergence table, including
  `lightning-output-field` never nested outside its form (L11727), `lightning-card` text-only `title`
  and `footer` (L11674), `lightning-accordion-section` `title` reserved for internal use (L11663),
  and `lightning-layout` allowing no components between its items (L11707). Backs Gotcha 6, Gotcha 11
  and the Contract Mistakes table.
- LWC Developer Guide — *Use Third-Party Web Components in LWC* (`create-use-third-party-components`
  L4184–L4219) — that Salesforce does not support third-party web components, that AppExchange and
  base components should be checked first, and the `lwc:external` / LWS / npm / `getElementById`
  limitations. Backs the fourth row of the base-component-first decision table.
- Lightning Component Reference (Component Library) —
  https://developer.salesforce.com/docs/platform/lightning-component-reference/overview/components —
  the authority for every per-component attribute, event, method, slot and target. Named as the
  authority for all `UNVERIFIED (2026-09-05)` markers in this package, because the Developer Guide
  does not publish attribute tables (`base-components-considerations` L4727).

All `lwc_guide` line citations refer to the crawled Lightning Web Components Developer Guide corpus
(676 pages, crawled 2026-09-05); each page's canonical URL is
`https://developer.salesforce.com/docs/platform/lwc/guide/<page-slug>.html`.
