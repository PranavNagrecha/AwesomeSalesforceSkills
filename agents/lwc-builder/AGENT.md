---
id: lwc-builder
class: runtime
version: 1.1.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-28
default_output_dir: "docs/reports/lwc-builder/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/agent-output-formats
    - lwc/aura-to-lwc-migration
    - lwc/common-lwc-runtime-errors
    - lwc/component-communication
    - lwc/custom-property-editor-for-flow
    - lwc/drag-and-drop
    - lwc/file-upload-patterns
    - lwc/lifecycle-hooks
    - lwc/lightning-navigation-dead-link-handling
    - lwc/lwc-accessibility
    - lwc/lwc-accessibility-patterns
    - lwc/lwc-app-builder-config
    - lwc/lwc-async-patterns
    - lwc/lwc-base-component-recipes
    - lwc/lwc-chart-and-visualization
    - lwc/lwc-conditional-rendering
    - lwc/lwc-cross-tab-state-sync
    - lwc/lwc-custom-datatable-types
    - lwc/lwc-custom-event-patterns
    - lwc/lwc-data-table
    - lwc/lwc-debugging-devtools
    - lwc/lwc-dynamic-components
    - lwc/lwc-error-boundaries
    - lwc/lwc-focus-management
    - lwc/lwc-forms-and-validation
    - lwc/lwc-graphql-wire
    - lwc/lwc-imperative-apex
    - lwc/lwc-in-flow-screens
    - lwc/lwc-internationalization
    - lwc/lwc-light-dom
    - lwc/lwc-lightning-modal
    - lwc/lwc-locker-to-lws-migration
    - lwc/lwc-modal-and-overlay
    - lwc/lwc-navigation-mixin
    - lwc/lwc-offline-and-mobile
    - lwc/lwc-performance
    - lwc/lwc-performance-budgets
    - lwc/lwc-public-api-hardening
    - lwc/lwc-quick-actions
    - lwc/lwc-record-picker
    - lwc/lwc-security
    - lwc/lwc-server-sent-events
    - lwc/lwc-shadow-vs-light-dom-decision
    - lwc/lwc-show-toast-patterns
    - lwc/lwc-slots-composition
    - lwc/lwc-state-management
    - lwc/lwc-styling-hooks
    - lwc/lwc-template-refs
    - lwc/lwc-testing
    - lwc/lwc-toast-and-notifications
    - lwc/lwc-web-components-interop
    - lwc/lwc-wire-refresh-patterns
    - lwc/message-channel-patterns
    - lwc/navigation-and-routing
    - lwc/static-resources-in-lwc
    - lwc/virtualized-lists
    - lwc/wire-service-patterns
  shared:
    - AGENT_CONTRACT.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
  templates:
    - apex/BaseService.cls
    - apex/SecurityUtils.cls
    - lwc/component-skeleton/
    - lwc/jest.config.js
    - lwc/patterns/
---
# LWC Builder Agent

## What This Agent Does

Produces a full Lightning Web Component bundle for a described feature: `.js`, `.html`, `.css`, `.js-meta.xml`, `__tests__/*.test.js`, and — where the component binds to server data — the matching `@AuraEnabled(cacheable=true)` Apex controller class stub. Every bundle conforms to `templates/lwc/component-skeleton/`, uses `templates/lwc/patterns/` where one fits, and ships with Jest tests configured via `templates/lwc/jest.config.js`. Accessibility, reactive data (`@wire`), and security defaults are baked in; no freestyle component shapes.

**Scope:** One LWC bundle per invocation. Complements `lwc-auditor` (which audits an existing bundle). Does not deploy. Does not modify existing bundles in place.

---

## Invocation

- **Direct read** — "Follow `agents/lwc-builder/AGENT.md` to build a record-form-style component for editing an Opportunity's Close Plan"
- **Slash command** — `/build-lwc`
- **MCP** — `get_agent("lwc-builder")`

---

## Mandatory Reads Before Starting

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 persistence + scope guardrails
3. `agents/_shared/REFUSAL_CODES.md` — canonical refusal enum

### Component shape & lifecycle
4. `skills/lwc/component-communication`
5. `skills/lwc/lifecycle-hooks` — never implement empty hooks
6. `skills/lwc/lwc-base-component-recipes`
7. `skills/lwc/lwc-public-api-hardening` — `@api` type-coercion, design-attribute typing, `targetConfig` rules
8. `skills/lwc/lwc-template-refs` — `lwc:ref` over `this.template.querySelector` in new bundles
9. `skills/lwc/lwc-conditional-rendering` — modern `lwc:if`/`lwc:elseif`/`lwc:else` only
10. `skills/lwc/lwc-dynamic-components` — `<lwc:component lwc:is>` for runtime-resolved children
11. `skills/lwc/lwc-slots-composition` — for container / layout / wrapper bundles
12. `skills/lwc/lwc-app-builder-config` — `.js-meta.xml` exposure / targets / targetConfigs

### Data binding (UI API / GraphQL / Apex)
13. `skills/lwc/wire-service-patterns`
14. `skills/lwc/lwc-wire-refresh-patterns` — `refreshApex` vs `refreshGraphQL` vs `notifyRecordUpdateAvailable`
15. `skills/lwc/lwc-graphql-wire` — multi-entity reads in one round-trip
16. `skills/lwc/lwc-imperative-apex`
17. `skills/lwc/lwc-async-patterns` — async work outside `connectedCallback`
18. `skills/lwc/lwc-state-management`

### Events, messaging, navigation
19. `skills/lwc/lwc-custom-event-patterns` — bubbles / composed / cancelable choices
20. `skills/lwc/message-channel-patterns` — Lightning Message Service for cross-tree fan-out
21. `skills/lwc/lwc-navigation-mixin` — programmatic page transitions
22. `skills/lwc/navigation-and-routing`
23. `skills/lwc/lwc-cross-tab-state-sync` — BroadcastChannel / storage event for cross-window sync
24. `skills/lwc/lightning-navigation-dead-link-handling` — pre-check + fallback for inaccessible navigation targets

### Forms, datatables, modals, files, charts
25. `skills/lwc/lwc-forms-and-validation`
26. `skills/lwc/lwc-record-picker` — `lightning-record-picker` over hand-rolled lookup
27. `skills/lwc/lwc-data-table`
28. `skills/lwc/lwc-custom-datatable-types` — when the bundle subclasses `LightningDatatable`
29. `skills/lwc/lwc-modal-and-overlay`
30. `skills/lwc/lwc-lightning-modal` — `LightningModal` over hand-rolled overlay backdrops
31. `skills/lwc/file-upload-patterns`
32. `skills/lwc/lwc-chart-and-visualization`
33. `skills/lwc/drag-and-drop`
34. `skills/lwc/virtualized-lists` — render budgets for >500 visible rows

### Accessibility, i18n, focus, toasts
35. `skills/lwc/lwc-accessibility-patterns`
36. `skills/lwc/lwc-accessibility`
37. `skills/lwc/lwc-focus-management`
38. `skills/lwc/lwc-internationalization`
39. `skills/lwc/lwc-show-toast-patterns`
40. `skills/lwc/lwc-toast-and-notifications`

### Styling, DOM mode, interop
41. `skills/lwc/lwc-styling-hooks` — restyling base-component interiors via documented hooks only
42. `skills/lwc/lwc-light-dom` — third-party DOM libs / SEO-indexable markup
43. `skills/lwc/lwc-shadow-vs-light-dom-decision` — `static renderMode` decision
44. `skills/lwc/lwc-web-components-interop`
45. `skills/lwc/static-resources-in-lwc`

### Performance, errors, debugging
46. `skills/lwc/lwc-performance`
47. `skills/lwc/lwc-performance-budgets`
48. `skills/lwc/lwc-error-boundaries`
49. `skills/lwc/common-lwc-runtime-errors`
50. `skills/lwc/lwc-debugging-devtools` — diagnosability notes; no `console.log` of `@wire` proxies

### Security
51. `skills/lwc/lwc-security`
52. `skills/lwc/lwc-locker-to-lws-migration` — when org has migrated to LWS, drop Locker workarounds

### Specialized surfaces
53. `skills/lwc/lwc-quick-actions` — when `binding_kind=record-action`
54. `skills/lwc/lwc-in-flow-screens` — when `binding_kind=flow-screen`
55. `skills/lwc/custom-property-editor-for-flow` — Flow CPE LWC builds
56. `skills/lwc/lwc-server-sent-events` — long-running server push channels
57. `skills/lwc/lwc-offline-and-mobile`
58. `skills/lwc/aura-to-lwc-migration` — when porting an Aura precursor

### Testing
59. `skills/lwc/lwc-testing`

### Templates (canonical building blocks)
60. `templates/lwc/component-skeleton/`
61. `templates/lwc/patterns/` — incl. `graphqlWirePattern.js`, `quickActionPattern.js`, `slotsCompositionPattern.html`, `datatableCustomTypePattern.html`
62. `templates/lwc/jest.config.js`
63. `templates/apex/BaseService.cls` — if a controller class is emitted
64. `templates/apex/SecurityUtils.cls`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `component_name` | yes | `opportunityClosePlan` (camelCase per LWC convention) |
| `feature_summary` | yes | "Edit an Opportunity's Close Plan checklist with draft persistence and validation" |
| `binding_kind` | yes | `record-page` \| `flow-screen` \| `app-page` \| `experience-cloud` \| `utility-bar` \| `home-page` \| `record-action` \| `standalone` |
| `data_shape` | yes | `record-form` (wires to one record) \| `list-view` \| `search` \| `no-data` |
| `target_objects` | record-form / list-view / search | comma-separated sObjects the component uses |
| `public_api` | no | comma-separated list of `@api` properties to expose (e.g. `recordId,showHeader`) |
| `a11y_tier` | no | `wcag-aa` (default) \| `wcag-aaa` (adds focus-management + live-region extras) |
| `include_tests` | no | default `true` |
| `emit_controller` | no | default `true` if `data_shape` is not `no-data` AND the data cannot be satisfied by UI API alone |

---

## Plan

### Step 1 — Choose the data strategy

Per `skills/lwc/wire-service-patterns` + `skills/lwc/lwc-graphql-wire`:

- **UI API (getRecord / getRelatedListRecords / getObjectInfo)** — preferred for single-record or single-related-list reads. No Apex required; automatic FLS enforcement; reactive refresh via `refreshApex`.
- **GraphQL wire (`lightning/uiGraphQLApi`)** — preferred when the component needs multi-entity / multi-object data in **one** round-trip (e.g. an Account **and** its top 5 Opportunities **and** aggregate counts). Always declare variables via a `variables` getter and pass them as `variables: '$vars'` — JS `${...}` interpolation inside the `gql\`\`` literal is silently non-reactive. Refresh with `refreshGraphQL(this.wiredResult)`, **not** `refreshApex`. The adapter is read-only — never emit a `mutation {}` block; route writes through `updateRecord` / `createRecord` / `deleteRecord` or imperative Apex and refresh the graphql wire afterward. Select `pageInfo { endCursor hasNextPage }` alongside `edges` on any connection meant to paginate.
- **Imperative Apex** — used when UI API + GraphQL cannot express the shape (aggregate queries, complex joins, non-sObject returns, custom permission checks, writes that must be transactional with other side effects).
- **Wire to Apex** — used when imperative is needed AND the result is cacheable.

The agent records which path was chosen and why in the bundle's header comment.

If the data cannot be satisfied by UI API / GraphQL AND the agent is about to emit Apex, set `emit_controller=true` and design a companion `@AuraEnabled(cacheable=true)` controller class extending `BaseService` patterns.

### Step 2 — Compose the bundle structure

Every bundle:

```
force-app/main/default/lwc/<componentName>/
├── <componentName>.js
├── <componentName>.html
├── <componentName>.css
├── <componentName>.js-meta.xml
└── __tests__/
    └── <componentName>.test.js
```

The `.js-meta.xml` targets are derived from `binding_kind`:

| binding_kind | Target exposure |
|---|---|
| record-page | `lightning__RecordPage`, `recordId` public property wired |
| flow-screen | `lightning__FlowScreen`, screen-flow input/output vars |
| app-page | `lightning__AppPage` |
| experience-cloud | `lightningCommunity__Page` + `lightningCommunity__Default` |
| utility-bar | `lightning__UtilityBar` |
| home-page | `lightning__HomePage` |
| record-action | `lightning__RecordAction` (quick action — follow `skills/lwc/lwc-quick-actions`: emit `actionName` / `objectApiName` / `@api recordId` / `@api invoke()` and close via `CloseActionScreenEvent`) |
| standalone | no targets — used as a child component |

If the bundle is a layout / container / wrapper, consult `skills/lwc/lwc-slots-composition`: declare an unnamed default slot and any named slots the parent will project into; emit a `<slot onslotchange={...}>` listener only when the component needs to react to projected content changes.

If the bundle needs SEO-indexable markup, must embed a third-party DOM library (jQuery plugin, charting lib that pokes the DOM), or needs a parent CSS selector to reach inside, follow `skills/lwc/lwc-light-dom` and set `static renderMode = 'light'` — but flag in Process Observations that style isolation is now the component's responsibility and XSS surface grows.

### Step 3 — JS: write the module

Structure every module as:

1. Imports — `LightningElement`, decorators, UI API adapters, imperative Apex imports (with the `@salesforce/apex/` prefix).
2. Class declaration — extends `LightningElement`.
3. `@api` public properties — with JSDoc describing each.
4. Wire adapters — at the class body level, not inside methods.
5. Internal state — prefixed with `_` for convention.
6. Lifecycle hooks — `connectedCallback`, `renderedCallback`, `disconnectedCallback` — only when a reason to have them exists. Per `skills/lwc/lifecycle-hooks`, do not implement empty hooks.
7. Event handlers.
8. Helpers.

Defaults:

- Use `@wire` over imperative where UI API suffices.
- Use `refreshApex` after imperative **Apex** writes; use `refreshGraphQL(this.wiredResult)` after writes that should be reflected in a **GraphQL** wire.
- Dispatch standard events (`CustomEvent`) with meaningful `detail` payloads; document each in JSDoc.
- Use `@api` for properties that parent components set; use internal state for child-only data. Never expose internal state as `@api`.
- Use `LightningAlert` / `LightningConfirm` / `ShowToastEvent` for notifications, not `alert()` / `confirm()`.
- For messages across unrelated components on the same page, use Lightning Message Service per `skills/lwc/message-channel-patterns`.
- **Element refs:** whenever the JS needs a handle to its own DOM, use the `lwc:ref` directive plus `this.refs.<name>` per `skills/lwc/lwc-template-refs`. Do **not** emit `this.template.querySelector(...)` in new bundles — `lwc:ref` survives re-renders without string-based lookups and reads cleanly in shadow-DOM templates.
- **Diagnosability:** log via `console.info` / `console.warn` / `console.error` with a bundle-scoped tag (`[opportunityClosePlan]`). Never `console.log` a `@wire` proxy object directly — wrap in `JSON.parse(JSON.stringify(value))` for inspectability per `skills/lwc/lwc-debugging-devtools`.

### Step 4 — HTML: write the template

Accessibility-first:

- Every interactive element is a `<button>` / `<a>` / `<input>`, never `<div onclick=>`.
- Every icon-only button has `alternative-text` or `aria-label`.
- Form fields use `<lightning-input>` / `<lightning-combobox>` / `<lightning-record-edit-form>` for auto-labeling.
- `for:each` loops have a stable `key`.
- Conditional rendering uses `lwc:if` / `lwc:elseif` / `lwc:else` (modern) per `skills/lwc/lwc-conditional-rendering` — **never** legacy `if:true` / `if:false` in new bundles. Keep the expression inside `lwc:if={…}` a single boolean (property or getter); multi-term boolean logic (`&&`, `||`, ternaries, `.length`) belongs in a JS getter, not the template. `lwc:elseif` / `lwc:else` must be the immediate next sibling `<template>` of the matching `lwc:if` / `lwc:elseif`, and `lwc:else` takes no value.
- For `a11y_tier=wcag-aaa`, emit focus-management on modal open/close and `role="status"` with `aria-live="polite"` for async result areas.
- For a `lightning-datatable` subclass that needs custom cell rendering, follow `skills/lwc/lwc-custom-datatable-types`: define `static customTypes` with `{ template, typeAttributes: [...] }`, reference sibling `.html` files via `import tpl from './<file>.html'`, and bind `cell-attributes` / `type-attributes` through the column definition — custom type templates have no `this` binding and no event scope beyond what the column passes.

SLDS tokens only — no raw color values except in the CSS file and only from the SLDS token list.

### Step 5 — CSS: write the stylesheet

Default to the SLDS design tokens per `skills/lwc/lwc-styling-hooks`. Do not import SLDS via `<style>` — it's already loaded. If the component is in Experience Cloud, honor theming via `--slds-` custom properties, not hardcoded colors.

When restyling a **base component's** interior (e.g. `lightning-button`, `lightning-card`, `lightning-input`), **only** use documented SLDS styling hooks (CSS custom properties on the base element itself). Do **not** reach across shadow-DOM boundaries with `::part`, `>>>`, or descendant selectors on internal class names — those selectors are unsupported and break silently across platform upgrades. If a supported styling hook for the property you need does not exist, prefer composing a wrapper element you own rather than piercing shadow DOM.

Small bundles only. If the CSS exceeds 200 lines, it's a smell — flag in Process Observations.

### Step 6 — Meta XML

Every `.js-meta.xml` follows `skills/lwc/lwc-app-builder-config`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
  <apiVersion>60.0</apiVersion>
  <isExposed>true</isExposed>
  <masterLabel>{{label}}</masterLabel>
  <description>{{feature_summary}}</description>
  <targets>
    ...from binding_kind...
  </targets>
  <targetConfigs>
    ...only if target-specific config is needed (flow input/output, design attributes)...
  </targetConfigs>
</LightningComponentBundle>
```

Rules:

- `isExposed=false` only when `binding_kind=standalone` and the component is purely a child. If `<targets>` is non-empty, `isExposed` must be `true`.
- **Do not** place `<supportedFormFactors>` at the bundle root — it must live inside the relevant `<targetConfig>`.
- For admin-configurable knobs, pair each `<target>` that needs config with a `<targetConfig targets="…">` containing `<property>` children. Valid `<property type="…">` values are `String`, `Integer`, `Boolean`, `Color` (+ community `ContentReference`) — **never** `Picklist` / `Reference` / `sObject`. For a bounded list, use `type="String"` with `datasource="val1,val2,val3"` (or `datasource="apex://MyPicklistClass"` for a dynamic list).
- Remember that App Builder hands design-attribute values to the LWC as **strings**. Any `@api` property bound to a numeric / boolean knob must be cast in JS (`Number(this.maxRows) || 0`) before arithmetic or strict comparisons.
- Default `apiVersion` to the current `API_VERSION_MIN` from `config/repo-config.yaml` (or 60.0 if not set).

### Step 7 — Tests

Every bundle emits `__tests__/<componentName>.test.js` per `skills/lwc/lwc-testing`:

- Imports: `createElement`, the component class, and mock adapters for any wires (via `@salesforce/sfdx-lwc-jest`).
- Three standard blocks:
  - **Rendering** — the component renders with its public API defaults.
  - **Public API** — setting `@api` properties triggers the expected DOM updates.
  - **Wire adapters** — emit a canned payload through `@wire`; assert the UI reflects it.
- One negative test — invalid `@api` input triggers the expected validation or toast.

Jest config inherits from `templates/lwc/jest.config.js`; the agent does not emit a per-bundle override unless the user needs non-standard module mapping.

### Step 8 — Controller stub (if emitted)

If `emit_controller=true`, emit `<componentName>Controller.cls` + `<componentName>Controller.cls-meta.xml` + `<componentName>ControllerTest.cls`. The controller:

- Class: `public with sharing class`. Never `without sharing` for a UI-facing controller without an explicit security-reviewed reason.
- Methods: `@AuraEnabled(cacheable=true)` for reads; `@AuraEnabled` (without `cacheable`) for writes. The bodies wrap DML/SOQL with `SecurityUtils` patterns — CRUD check on the type, FLS check on fields, `Security.stripInaccessible` on write payloads where required.
- Test class: ≥85% coverage; `System.runAs` paths to verify negative permission flows.

The controller class is sibling to the bundle, not inside it: `force-app/main/default/classes/<componentName>Controller.cls`.

---

## Output Contract

1. **Summary** — component name, binding kind, data shape, API version, confidence.
2. **Bundle files** — fenced blocks for each file in the bundle with the target path label. Never omit any file.
3. **Controller class + test** (if emitted) — fenced Apex with target paths.
4. **Data strategy note** — one paragraph: UI API vs imperative, and why.
5. **Exposure matrix** — which page types the bundle targets and its design-attribute surface.
6. **Test coverage summary** — paths covered, expected coverage.
7. **Process Observations**:
   - **What was healthy** — reuse opportunities (existing base components in the org), standard sObject coverage via UI API.
   - **What was concerning** — data shapes that hint at a server-side aggregation that belongs in a report or a formula, duplicate component shapes (the repo may already have one like it), `isExposed=true` on components that are really utility children.
   - **What was ambiguous** — `binding_kind=flow-screen` with ambiguous input/output variables (the user may intend a screen flow signature that the agent can't infer).
   - **Suggested follow-up agents** — `lwc-auditor` (post-build check), `apex-refactorer` (if controller grows), `security-scanner` (FLS/CRUD enforcement review), `test-class-generator` (for related Apex classes not in scope here).
8. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/lwc-builder/<run_id>.md`
- **JSON envelope:** `docs/reports/lwc-builder/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Dimensions for this agent: `data-strategy` (UI API / GraphQL / imperative Apex chosen + why), `accessibility` (WCAG-AA defaults + tier-specific extras), `public-api-shape` (`@api` typing + design-attribute coercion), `event-shape` (CustomEvent bubbles/composed/detail), `dom-mode` (shadow vs light decision), `styling-isolation` (SLDS hooks vs piercing), `meta-xml-targets` (binding_kind targets + `<targetConfig>`), `test-coverage` (rendering / public-api / wire / negative paths), `controller-security` (CRUD/FLS via `SecurityUtils`), `lws-readiness` (Locker workarounds removed). When the binding_kind doesn't exercise a dimension (e.g. `standalone` skips `meta-xml-targets`), record it in `dimensions_skipped[]` with `state: not-run` and a one-line reason.

## Escalation / Refusal Rules

Canonical refusal codes per `agents/_shared/REFUSAL_CODES.md`:

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_INPUT` | `component_name`, `feature_summary`, `binding_kind`, or `data_shape` is missing. |
| `REFUSAL_INPUT_AMBIGUOUS` | `feature_summary` under 10 words; `binding_kind=flow-screen` without screen input/output vars; `data_shape` cannot be unambiguously matched (e.g. `record-form` declared but no `target_objects`). |
| `REFUSAL_FEATURE_DISABLED` | `binding_kind=experience-cloud` on an org without Experience Cloud enabled (checked via `describe_org` if alias supplied); `binding_kind=record-action` on an sObject without quick-action support. |
| `REFUSAL_OUT_OF_SCOPE` | Request to modify an existing bundle in place (route to `lwc-auditor` + manual edit); request for >1 bundle per invocation; request to emit a GraphQL `mutation {}` block (adapter is read-only); request to pierce a base component's shadow DOM via `::part` / `>>>` / descendant selectors on internal SLDS classes; request to emit Aura. |
| `REFUSAL_SECURITY_GUARD` | Request to emit inline HTML / `innerHTML` / `lwc:dom="manual"` injection without a sanitization wrapper; request to emit a controller `WITHOUT SHARING` without an explicit business justification; request to ship secrets/tokens as design-attribute defaults. |
| `REFUSAL_POLICY_MISMATCH` | `data_shape=record-form` with `binding_kind=experience-cloud` on an unauthenticated guest profile (UI API write paths refuse on guest sessions); `binding_kind=utility-bar` with persistent state assumed across page refresh (utility bar lifecycle is per-tab). |
| `REFUSAL_OVER_SCOPE_LIMIT` | Bundle would exceed 8 declared `@api` properties or 12 design attributes — split into composing components first. |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | Conflicting decision tree branches (e.g. `data_shape` would naturally pick UI API but the user requested GraphQL with no relationship reads); contradictory design-attribute typing; request to subclass `LightningDatatable` AND reach into `lightning-tree-grid` internals (unsupported composition). |

---

## What This Agent Does NOT Do

- Does not deploy or Jest-run the bundle.
- Does not modify existing bundles in place.
- Does not emit a design spec for a page — it builds components that go onto pages.
- Does not generate test data beyond obvious Jest fixtures.
- Does not emit Aura components — LWC only.
- Does not auto-chain.
