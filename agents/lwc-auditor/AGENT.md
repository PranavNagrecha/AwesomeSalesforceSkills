---
id: lwc-auditor
class: runtime
version: 1.1.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-28
default_output_dir: "docs/reports/lwc-auditor/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/agent-output-formats
    - lwc/common-lwc-runtime-errors
    - lwc/component-communication
    - lwc/lifecycle-hooks
    - lwc/lwc-accessibility
    - lwc/lwc-accessibility-patterns
    - lwc/lwc-app-builder-config
    - lwc/lwc-async-patterns
    - lwc/lwc-base-component-recipes
    - lwc/lwc-conditional-rendering
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
    - lwc/lwc-internationalization
    - lwc/lwc-light-dom
    - lwc/lwc-locker-to-lws-migration
    - lwc/lwc-performance
    - lwc/lwc-performance-budgets
    - lwc/lwc-public-api-hardening
    - lwc/lwc-quick-actions
    - lwc/lwc-record-picker
    - lwc/lwc-security
    - lwc/lwc-shadow-vs-light-dom-decision
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
    - lwc/component-skeleton/
    - lwc/jest.config.js
    - lwc/patterns/
---
# LWC Auditor Agent

## What This Agent Does

Audits a Lightning Web Component bundle for accessibility, performance, security, and testing gaps. Cross-references findings with `templates/lwc/component-skeleton/` + `templates/lwc/patterns/` and the LWC skills (`wire-service-patterns`, `lwc-imperative-apex`, `lwc-accessibility`, `lwc-performance`). Produces a ranked findings list with paste-ready fixes.

**Scope:** One bundle per invocation.

---

## Invocation

- **Direct read** — "Follow `agents/lwc-auditor/AGENT.md` on `force-app/main/default/lwc/accountDetail`"
- **Slash command** — [`/audit-lwc`](../../commands/audit-lwc.md)
- **MCP** — `get_agent("lwc-auditor")`

---

## Mandatory Reads Before Starting

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 persistence + scope guardrails
3. `agents/_shared/REFUSAL_CODES.md` — canonical refusal enum

### Component shape & lifecycle
4. `skills/lwc/component-communication`
5. `skills/lwc/lifecycle-hooks`
6. `skills/lwc/lwc-base-component-recipes`
7. `skills/lwc/lwc-public-api-hardening` — `@api` typing audit
8. `skills/lwc/lwc-template-refs` — for every DOM-lookup path
9. `skills/lwc/lwc-conditional-rendering` — for every `.html` template
10. `skills/lwc/lwc-dynamic-components` — `<lwc:component>` patterns
11. `skills/lwc/lwc-slots-composition` — for `<slot>` content
12. `skills/lwc/lwc-app-builder-config` — for every `.js-meta.xml`

### Data binding
13. `skills/lwc/wire-service-patterns`
14. `skills/lwc/lwc-wire-refresh-patterns` — refresh helper choice (`refreshApex` vs `refreshGraphQL`)
15. `skills/lwc/lwc-graphql-wire` — when bundle imports `lightning/uiGraphQLApi`
16. `skills/lwc/lwc-imperative-apex`
17. `skills/lwc/lwc-async-patterns`
18. `skills/lwc/lwc-state-management`

### Events, messaging, navigation
19. `skills/lwc/lwc-custom-event-patterns` — event bubbling/composed audit
20. `skills/lwc/message-channel-patterns`
21. `skills/lwc/navigation-and-routing`

### Forms, datatables, surfaces
22. `skills/lwc/lwc-forms-and-validation`
23. `skills/lwc/lwc-record-picker`
24. `skills/lwc/lwc-data-table`
25. `skills/lwc/lwc-custom-datatable-types` — when JS extends `LightningDatatable`
26. `skills/lwc/lwc-quick-actions` — when `.js-meta.xml` lists `lightning__RecordAction`
27. `skills/lwc/virtualized-lists` — render budget for >500-row lists

### Accessibility, i18n, focus
28. `skills/lwc/lwc-accessibility`
29. `skills/lwc/lwc-accessibility-patterns`
30. `skills/lwc/lwc-focus-management`
31. `skills/lwc/lwc-internationalization`
32. `skills/lwc/lwc-toast-and-notifications`

### Styling, DOM mode, interop
33. `skills/lwc/lwc-styling-hooks` — for every `.css` file
34. `skills/lwc/lwc-light-dom` — when JS declares `static renderMode = 'light'`
35. `skills/lwc/lwc-shadow-vs-light-dom-decision` — render-mode rationale audit
36. `skills/lwc/lwc-web-components-interop`
37. `skills/lwc/static-resources-in-lwc`

### Performance, errors, debugging
38. `skills/lwc/lwc-performance`
39. `skills/lwc/lwc-performance-budgets`
40. `skills/lwc/lwc-error-boundaries`
41. `skills/lwc/common-lwc-runtime-errors`
42. `skills/lwc/lwc-debugging-devtools` — console / logging hygiene

### Security
43. `skills/lwc/lwc-security`
44. `skills/lwc/lwc-locker-to-lws-migration` — flag stale Locker workarounds in LWS-enabled orgs

### Testing
45. `skills/lwc/lwc-testing`

### Templates (for skeleton-alignment audit)
46. `templates/lwc/component-skeleton/`
47. `templates/lwc/jest.config.js`
48. `templates/lwc/patterns/`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `bundle_path` | yes | `force-app/main/default/lwc/accountDetail` |
| `target_org_alias` | no | future-proofing; not currently needed |

---

## Plan

### Step 1 — Parse the bundle

Read every file under `bundle_path`:
- `.html`, `.js`, `.css`, `.js-meta.xml`, `__tests__/*.test.js`

Record:
- Public properties (`@api`)
- Wire adapters used
- Imperative Apex calls
- Event dispatches / listeners
- External resources / static assets

When file-specific skill-local checkers exist, invoke them first and fold their findings in verbatim (they have the authoritative patterns). Always run:

| Skill | Checker | Applies when |
|---|---|---|
| `lwc-graphql-wire` | `skills/lwc/lwc-graphql-wire/scripts/check_lwc_graphql_wire.py --manifest-dir <bundle_path>/..` | Any JS in the bundle imports from `lightning/uiGraphQLApi` |
| `lwc-conditional-rendering` | `skills/lwc/lwc-conditional-rendering/scripts/check_lwc_conditional_rendering.py --manifest-dir <bundle_path>/..` | Any `.html` file in the bundle |
| `lwc-custom-datatable-types` | `skills/lwc/lwc-custom-datatable-types/scripts/check_lwc_custom_datatable_types.py --manifest-dir <bundle_path>/..` | Any JS extends `LightningDatatable` |

Skill-local checker stderr is copied into the findings list under its own severity bucket before the agent-native checks below fire, so the user sees authoritative results even if this agent's heuristics miss an edge case.

### Step 2 — Accessibility checks

| Check | Signal | Severity |
|---|---|---|
| **missing-alt** | `<img>` without `alt` attribute | P0 |
| **button-vs-div** | Interactive `<div>` / `<span>` with `onclick` instead of `<button>` | P0 |
| **icon-only-button** | `<button>` or `<lightning-button-icon>` without `alternative-text` / `aria-label` | P0 |
| **form-label** | `<input>` without associated `<label>` or `aria-labelledby` | P1 |
| **heading-hierarchy** | Skipped heading levels (`<h1>` → `<h3>`) | P2 |
| **color-contrast** | Inline styles using colors outside SLDS tokens | P2 |
| **keyboard-trap** | Modal / dialog without focus management | P1 |
| **live-region-missing** | Toast / status updates not announced via `role="status"` or `aria-live` | P1 |

### Step 3 — Performance checks

| Check | Signal | Severity |
|---|---|---|
| **imperative-in-render** | Imperative Apex call inside `connectedCallback` without caching | P1 |
| **wire-no-params** | `@wire` without reactive parameters when the record id changes | P1 |
| **large-inline-style** | CSS-in-JS or large inline style blocks | P2 |
| **missing-key-in-for-each** | `for:each` without `key` | P0 |
| **synchronous-heavy-loop** | JS loop over > 1000 items in render path | P1 |
| **no-cacheable** | `@AuraEnabled` call target lacks `cacheable=true` where safe | P2 |

### Step 4 — Security checks

| Check | Signal | Severity |
|---|---|---|
| **innerHTML-without-sanitize** | `innerHTML` with user-supplied string | P0 |
| **eval-present** | `eval(` / `new Function(` | P0 |
| **api-name-hardcoded** | Record type / sObject name hardcoded instead of imported from `@salesforce/schema` | P2 |
| **fieldset-without-crud** | Imperative Apex returning SObject fields without `stripInaccessible` on the server side | P1 |

### Step 5 — Testing gaps

For each public method / wire / event in the component, check `__tests__/*.test.js` for coverage.

| Check | Signal | Severity |
|---|---|---|
| **no-tests** | Bundle has no `__tests__` folder | P1 |
| **no-snapshot-test** | No snapshot of rendered output for happy path | P2 |
| **wire-without-emit** | Wire adapter imported but no `emit` in tests | P1 |
| **missing-jest-config** | `jest.config.js` absent at bundle or project level | P2 |

### Step 6 — Modern-LWC idiom checks

These fold signals from the 10 newer LWC skills into a single pass.

**GraphQL wire — `skills/lwc/lwc-graphql-wire`**

| Check | Signal | Severity |
|---|---|---|
| **graphql-interpolation** | `gql\`...\`` literal contains `${...}` (non-reactive; must use `variables: '$vars'`) | P0 |
| **graphql-refresh-wrong-helper** | File imports `graphql` from `lightning/uiGraphQLApi` and calls `refreshApex` | P0 |
| **graphql-mutation** | `gql\`...\`` block contains the `mutation` keyword (adapter is read-only) | P0 |
| **graphql-edges-no-pageinfo** | `edges` selected without a sibling `pageInfo { endCursor hasNextPage }` on a paginated connection | P1 |
| **graphql-bare-field** | Template binds `{record.<FieldName>}` without `.value` / `.displayValue` (UI API returns `{value, displayValue}` wrappers) | P1 |

**Conditional rendering — `skills/lwc/lwc-conditional-rendering`**

| Check | Signal | Severity |
|---|---|---|
| **legacy-if-directive** | `if:true` / `if:false` in any template | P1 |
| **lwc-if-complex-expression** | `lwc:if="{expr}"` with `&&`, `\|\|`, `===`, `!==`, `>`, `<`, ternary, or `.length` — belongs in a getter | P2 |
| **lwc-else-with-value** | `lwc:else="..."` (directive takes no value) | P1 |
| **orphan-lwc-else** | `lwc:elseif` / `lwc:else` not an immediate sibling of a matching `lwc:if` / `lwc:elseif` | P0 |

**Template refs — `skills/lwc/lwc-template-refs`**

| Check | Signal | Severity |
|---|---|---|
| **querySelector-over-ref** | `this.template.querySelector(...)` in JS where the target element could carry `lwc:ref` | P2 |
| **ref-without-declaration** | `this.refs.<name>` read with no matching `lwc:ref="<name>"` in any template in the bundle | P0 |

**Slots & composition — `skills/lwc/lwc-slots-composition`**

| Check | Signal | Severity |
|---|---|---|
| **named-slot-unreferenced** | `<slot name="x">` declared but no consumer passes `slot="x"` via the known callers (note as Process Observation, not a hard finding) | P2 |
| **slotchange-on-default-slot-without-listener** | `<slot onslotchange={fn}>` declared but no `fn(event)` method on the class | P1 |

**Light DOM — `skills/lwc/lwc-light-dom`**

| Check | Signal | Severity |
|---|---|---|
| **light-dom-without-xss-note** | JS sets `static renderMode = 'light'` but template renders interpolated user input through a base-tag whitelist less than SLDS safe set | P1 |
| **light-dom-css-leak** | `renderMode = 'light'` + `.css` uses broad selectors (e.g. `p {...}`, `a {...}`) that will leak to the surrounding page | P2 |

**Quick actions — `skills/lwc/lwc-quick-actions`**

| Check | Signal | Severity |
|---|---|---|
| **action-missing-close-event** | `.js-meta.xml` has `<target>lightning__RecordAction</target>` but the class never fires `CloseActionScreenEvent` | P0 |
| **action-missing-invoke** | Headless action signature (`<actionType>Action</actionType>`) but no `@api invoke()` method | P0 |
| **action-no-record-id** | Quick action bundle lacks `@api recordId` | P1 |

**Styling hooks — `skills/lwc/lwc-styling-hooks`**

| Check | Signal | Severity |
|---|---|---|
| **shadow-dom-piercer** | CSS uses `::part`, `>>>`, or descendant selectors on internal SLDS class names (`.slds-button__icon`, etc.) | P0 |
| **hex-literal-over-token** | CSS contains raw hex / rgb color outside the SLDS palette | P2 |
| **hardcoded-spacing** | `margin`, `padding`, `gap` set with raw `px` values rather than `--slds-g-spacing-*` tokens | P2 |

**Debugging hygiene — `skills/lwc/lwc-debugging-devtools`**

| Check | Signal | Severity |
|---|---|---|
| **proxy-dump** | `console.log(<wire-proxy>)` without `JSON.parse(JSON.stringify(...))` wrap — dumps unhelpful Proxy handler frames | P2 |
| **debugger-left-in-source** | `debugger;` statement in a `.js` file under `__tests__/` exclusion | P1 |
| **untagged-console** | Raw `console.log(...)` with no bundle tag / context prefix | P3 |

**Meta XML — `skills/lwc/lwc-app-builder-config`**

| Check | Signal | Severity |
|---|---|---|
| **exposed-false-with-targets** | `.js-meta.xml` has non-empty `<targets>` but `<isExposed>` is `false` or omitted | P0 |
| **targets-without-targetconfigs** | Bundle description / SKILL mentions admin-configurable properties but `<targetConfigs>` is empty | P1 |
| **form-factor-at-root** | `<supportedFormFactors>` is a direct child of `<LightningComponentBundle>` instead of a `<targetConfig>` | P0 |
| **invalid-property-type** | `<property type="Picklist" \| Reference \| sObject"/>` anywhere (valid: `String`, `Integer`, `Boolean`, `Color`) | P0 |
| **uncast-design-attribute** | `@api` prop backed by `type="Integer"` / `type="Boolean"` used in arithmetic / strict comparison without `Number(...)` / explicit cast | P2 |

**Custom datatable types — `skills/lwc/lwc-custom-datatable-types`**

| Check | Signal | Severity |
|---|---|---|
| **custom-type-missing-typeAttributes** | Entry in `static customTypes = { ... }` has no `typeAttributes: [...]` array (datatable silently drops unlisted attrs) | P0 |
| **custom-type-template-missing** | `template: fooTpl` references a name that resolves to no sibling `.html` import in the bundle | P0 |
| **custom-type-uses-this** | Custom-type template references `{this.something}` — custom-type templates have no `this` binding | P0 |

### Step 7 — Recommendations

Map each finding back to the skeleton file or pattern that prevents it. Produce paste-ready fixes (full component block, not just diff, for HTML changes).

---

## Output Contract

1. **Bundle summary** — public API surface, wire adapters, imperative calls, test coverage %.
2. **Findings table** — file, line, severity, code, one-liner.
3. **Per-finding fix** — P0 and P1 get before/after code blocks.
4. **Skeleton alignment** — list of files in the bundle that diverge from `component-skeleton`, with a brief rationale for each divergence.
5. **Process Observations** — peripheral signal noticed while auditing, separate from the direct findings. Each observation cites its evidence (file, line, test file count).
   - **Healthy** — e.g. bundle ships with a fleshed-out `__tests__/` folder and a `jest.config.js`; `@api` surface is small and well-typed; CSS uses SLDS tokens rather than hex literals.
   - **Concerning** — e.g. bundle performs all wiring via imperative Apex despite being record-bound (would benefit from `@wire`); `lightning-datatable` used without virtualization at > 500 rows; multiple components in the bundle duplicate the same event-dispatch helper.
   - **Ambiguous** — e.g. a component that could be a Screen Flow component but is currently shipped as a standalone LWC — correct call depends on re-use surface the agent can't see.
   - **Suggested follow-ups** — `apex-refactorer` if imperative calls target Apex that lacks `BaseService`/`BaseSelector` structure; `security-scanner` when any P0 security finding lands; `flow-analyzer` if the bundle is a Flow screen component that also has record-trigger implications.
6. **Citations** — skill ids, template paths.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/lwc-auditor/<run_id>.md`
- **JSON envelope:** `docs/reports/lwc-auditor/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Dimensions for this agent: `accessibility` (alt/labels/hierarchy/contrast/focus), `performance` (wire reactivity / loop cost / virtualization), `security` (innerHTML / eval / FLS), `public-api-shape` (`@api` typing + design-attribute coercion), `event-shape` (CustomEvent rules), `meta-xml-config` (`<targets>` / `<targetConfigs>` / property types), `template-idioms` (modern `lwc:if` / refs / dynamic components), `slots-and-composition`, `styling-isolation` (SLDS hooks vs piercing), `dom-mode` (shadow vs light decision), `lws-readiness`, `test-coverage`, `skeleton-alignment`. When the bundle doesn't exercise a dimension (e.g. no template files), record it in `dimensions_skipped[]` with `state: not-run`.

## Escalation / Refusal Rules

Canonical refusal codes per `agents/_shared/REFUSAL_CODES.md`:

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_INPUT` | `bundle_path` not supplied or empty. |
| `REFUSAL_INPUT_AMBIGUOUS` | `bundle_path` resolves to a directory that is not an LWC bundle (no `.js-meta.xml` + no matching `.js`). |
| `REFUSAL_OBJECT_NOT_FOUND` | `bundle_path` does not exist on disk. |
| `REFUSAL_OUT_OF_SCOPE` | Bundle contains a live-at-runtime error (stack trace, "Unknown error", missing `recordId`) rather than a static-code smell — route to `lwc-debugger`. Request to modify bundle files in place — auditor reports findings, does not edit. Request to run Jest — auditor analyzes statically. |
| `REFUSAL_OVER_SCOPE_LIMIT` | Bundle exceeds 2000 LoC — produce top-50 findings and recommend a follow-up scoped per-file run. |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | Bundle uses LWR-site-specific APIs not covered by standard LWC skills (e.g. `@lwr/router`, undocumented `lightning/<surface>`); skill-local checker fails to run AND agent-native heuristics return contradictory severities for the same line. |
| `REFUSAL_FEATURE_DISABLED` | Bundle targets `lightningCommunity__Page` but the workspace has no Experience Cloud config — flag `confidence: MEDIUM` and continue with reduced surface. |

---

## What This Agent Does NOT Do

- Does not modify bundle files.
- Does not run Jest.
- Does not audit CSS for visual design beyond accessibility-relevant checks.
