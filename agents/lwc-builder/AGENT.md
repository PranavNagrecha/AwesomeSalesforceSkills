---
id: lwc-builder
class: runtime
version: 1.0.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-23
default_output_dir: "docs/reports/lwc-builder/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/agent-output-formats
    - lwc/component-communication
    - lwc/lifecycle-hooks
    - lwc/lwc-accessibility-patterns
    - lwc/lwc-app-builder-config
    - lwc/lwc-base-component-recipes
    - lwc/lwc-conditional-rendering
    - lwc/lwc-custom-datatable-types
    - lwc/lwc-debugging-devtools
    - lwc/lwc-forms-and-validation
    - lwc/lwc-graphql-wire
    - lwc/lwc-imperative-apex
    - lwc/lwc-in-flow-screens
    - lwc/lwc-light-dom
    - lwc/lwc-performance
    - lwc/lwc-quick-actions
    - lwc/lwc-security
    - lwc/lwc-slots-composition
    - lwc/lwc-styling-hooks
    - lwc/lwc-template-refs
    - lwc/lwc-testing
    - lwc/message-channel-patterns
    - lwc/wire-service-patterns
  shared:
    - AGENT_CONTRACT.md
    - DELIVERABLE_CONTRACT.md
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

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/lwc/wire-service-patterns`
3. `skills/lwc/lwc-imperative-apex`
4. `skills/lwc/lwc-accessibility-patterns`
5. `skills/lwc/lwc-performance`
6. `skills/lwc/lwc-security`
7. `skills/lwc/lwc-testing`
8. `skills/lwc/lwc-forms-and-validation`
9. `skills/lwc/component-communication`
10. `skills/lwc/lifecycle-hooks`
11. `skills/lwc/message-channel-patterns`
12. `skills/lwc/lwc-base-component-recipes`
13. `skills/lwc/lwc-in-flow-screens` — if the component exposes to Flow screens
14. `skills/lwc/lwc-graphql-wire` — if the data shape needs multi-entity reads in one request
15. `skills/lwc/lwc-slots-composition` — if the bundle is a container / layout / wrapper component
16. `skills/lwc/lwc-light-dom` — if the bundle embeds third-party DOM libraries or needs SEO-indexable markup
17. `skills/lwc/lwc-template-refs` — any new bundle that queries its own DOM must use `lwc:ref`, not `this.template.querySelector`
18. `skills/lwc/lwc-quick-actions` — if `binding_kind` resolves to `lightning__RecordAction`
19. `skills/lwc/lwc-styling-hooks` — any time the component restyles a base-component's internals
20. `skills/lwc/lwc-conditional-rendering` — every template with conditional branches (modern `lwc:if`/`lwc:elseif`/`lwc:else` only)
21. `skills/lwc/lwc-app-builder-config` — every non-standalone bundle emits a `.js-meta.xml` and must honor this skill's exposure / targets / targetConfigs rules
22. `skills/lwc/lwc-custom-datatable-types` — if the bundle subclasses `LightningDatatable`
23. `skills/lwc/lwc-debugging-devtools` — emit a diagnosability note (console-first logging, no proxy-dumping) per this skill
24. `templates/lwc/component-skeleton/`
25. `templates/lwc/patterns/`
26. `templates/lwc/jest.config.js`
27. `templates/apex/BaseService.cls` — if a controller class is emitted
28. `templates/apex/SecurityUtils.cls`
29. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)

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
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

## Escalation / Refusal Rules

- `feature_summary` under 10 words → `REFUSAL_INPUT_AMBIGUOUS`.
- `binding_kind=flow-screen` without a specification of screen input/output vars → `REFUSAL_INPUT_AMBIGUOUS`.
- `binding_kind=experience-cloud` on an Experience Cloud site the org doesn't have enabled (checked via `describe_org` if an org alias is provided) → `REFUSAL_FEATURE_DISABLED`.
- Request to write directly to a protected sObject (Org Shape: no mention of FLS/CRUD in the feature summary) → emit bundle with FLS/CRUD wired but flag the absence of explicit user intent.
- Request to emit inline HTML / `innerHTML` usage → `REFUSAL_SECURITY_GUARD`.
- Request to emit a GraphQL `mutation {}` block → `REFUSAL_OUT_OF_SCOPE`; the UI API GraphQL adapter is read-only. Route writes through `updateRecord` / `createRecord` / `deleteRecord` / imperative Apex and refresh the wired result with `refreshGraphQL`.
- Request to pierce a base component's shadow DOM (`::part`, `>>>`, descendant selectors on internal SLDS class names) → `REFUSAL_OUT_OF_SCOPE`; redesign via documented SLDS styling hooks or wrap-and-own.
- Request to modify an existing bundle in place → `REFUSAL_OUT_OF_SCOPE`; route to `lwc-auditor` + manual edit.

---

## What This Agent Does NOT Do

- Does not deploy or Jest-run the bundle.
- Does not modify existing bundles in place.
- Does not emit a design spec for a page — it builds components that go onto pages.
- Does not generate test data beyond obvious Jest fixtures.
- Does not emit Aura components — LWC only.
- Does not auto-chain.
