---
id: lwc-builder
class: runtime
version: 1.0.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  skills:
    - lwc/component-communication
    - lwc/lifecycle-hooks
    - lwc/lwc-accessibility-patterns
    - lwc/lwc-base-component-recipes
    - lwc/lwc-forms-and-validation
    - lwc/lwc-imperative-apex
    - lwc/lwc-in-flow-screens
    - lwc/lwc-performance
    - lwc/lwc-security
    - lwc/lwc-testing
    - lwc/message-channel-patterns
    - lwc/wire-service-patterns
  shared:
    - AGENT_CONTRACT.md
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
14. `templates/lwc/component-skeleton/`
15. `templates/lwc/patterns/`
16. `templates/lwc/jest.config.js`
17. `templates/apex/BaseService.cls` — if a controller class is emitted
18. `templates/apex/SecurityUtils.cls`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `component_name` | yes | `opportunityClosePlan` (camelCase per LWC convention) |
| `feature_summary` | yes | "Edit an Opportunity's Close Plan checklist with draft persistence and validation" |
| `binding_kind` | yes | `record-page` \| `flow-screen` \| `app-page` \| `experience-cloud` \| `utility-bar` \| `home-page` \| `standalone` |
| `data_shape` | yes | `record-form` (wires to one record) \| `list-view` \| `search` \| `no-data` |
| `target_objects` | record-form / list-view / search | comma-separated sObjects the component uses |
| `public_api` | no | comma-separated list of `@api` properties to expose (e.g. `recordId,showHeader`) |
| `a11y_tier` | no | `wcag-aa` (default) \| `wcag-aaa` (adds focus-management + live-region extras) |
| `include_tests` | no | default `true` |
| `emit_controller` | no | default `true` if `data_shape` is not `no-data` AND the data cannot be satisfied by UI API alone |

---

## Plan

### Step 1 — Choose the data strategy

Per `skills/lwc/wire-service-patterns`:

- **UI API (getRecord / getRelatedListRecords / getObjectInfo)** — preferred. No Apex required; automatic FLS enforcement; reactive refresh via `refreshApex`.
- **Imperative Apex** — used when UI API cannot express the shape (aggregate queries, complex joins, non-sObject returns, custom permission checks).
- **Wire to Apex** — used when imperative is needed AND the result is cacheable.

The agent records which path was chosen and why in the bundle's header comment.

If the data cannot be satisfied by UI API AND the agent is about to emit Apex, set `emit_controller=true` and design a companion `@AuraEnabled(cacheable=true)` controller class extending `BaseService` patterns.

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
| standalone | no targets — used as a child component |

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
- Use `refreshApex` after imperative writes.
- Dispatch standard events (`CustomEvent`) with meaningful `detail` payloads; document each in JSDoc.
- Use `@api` for properties that parent components set; use internal state for child-only data. Never expose internal state as `@api`.
- Use `LightningAlert` / `LightningConfirm` / `ShowToastEvent` for notifications, not `alert()` / `confirm()`.
- For messages across unrelated components on the same page, use Lightning Message Service per `skills/lwc/message-channel-patterns`.

### Step 4 — HTML: write the template

Accessibility-first:

- Every interactive element is a `<button>` / `<a>` / `<input>`, never `<div onclick=>`.
- Every icon-only button has `alternative-text` or `aria-label`.
- Form fields use `<lightning-input>` / `<lightning-combobox>` / `<lightning-record-edit-form>` for auto-labeling.
- `for:each` loops have a stable `key`.
- Conditional rendering uses `lwc:if` / `lwc:else` (modern) rather than legacy `if:true` / `if:false`. The agent defaults to the modern syntax for any API version ≥ 55.0.
- For `a11y_tier=wcag-aaa`, emit focus-management on modal open/close and `role="status"` with `aria-live="polite"` for async result areas.

SLDS tokens only — no raw color values except in the CSS file and only from the SLDS token list.

### Step 5 — CSS: write the stylesheet

Default to the SLDS design tokens. Do not import SLDS via `<style>` — it's already loaded. If the component is in Experience Cloud, honor theming via `--slds-` custom properties, not hardcoded colors.

Small bundles only. If the CSS exceeds 200 lines, it's a smell — flag in Process Observations.

### Step 6 — Meta XML

Every `.js-meta.xml`:

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

`isExposed=false` only when `binding_kind=standalone` and the component is purely a child.

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

## Escalation / Refusal Rules

- `feature_summary` under 10 words → `REFUSAL_INPUT_AMBIGUOUS`.
- `binding_kind=flow-screen` without a specification of screen input/output vars → `REFUSAL_INPUT_AMBIGUOUS`.
- `binding_kind=experience-cloud` on an Experience Cloud site the org doesn't have enabled (checked via `describe_org` if an org alias is provided) → `REFUSAL_FEATURE_DISABLED`.
- Request to write directly to a protected sObject (Org Shape: no mention of FLS/CRUD in the feature summary) → emit bundle with FLS/CRUD wired but flag the absence of explicit user intent.
- Request to emit inline HTML / `innerHTML` usage → `REFUSAL_SECURITY_GUARD`.
- Request to modify an existing bundle in place → `REFUSAL_OUT_OF_SCOPE`; route to `lwc-auditor` + manual edit.

---

## What This Agent Does NOT Do

- Does not deploy or Jest-run the bundle.
- Does not modify existing bundles in place.
- Does not emit a design spec for a page — it builds components that go onto pages.
- Does not generate test data beyond obvious Jest fixtures.
- Does not emit Aura components — LWC only.
- Does not auto-chain.
