---
name: flow-screen-lwc-components
description: "Design custom Lightning Web Components that render inside Screen Flow steps — covers the lightning__FlowScreen target, @api properties as Flow inputs/outputs, FlowAttributeChangeEvent propagation, FlowNavigationNext/Back/Finish/Pause events, the @api validate() hook, and design-time targetConfig wiring. NOT for custom property editors that configure flow elements at design time — see flow-custom-property-editors. NOT for the LWC implementation deep-dive — see lwc/lwc-in-flow-screens."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
triggers:
  - "build LWC for screen flow"
  - "FlowAttributeChangeEvent in screen component"
  - "validate hook in flow LWC"
  - "expose lwc property as flow input output"
  - "flow screen component not visible in flow builder"
  - "fire FlowNavigationNextEvent from lwc"
tags:
  - flow-screen-lwc-components
  - lwc
  - screen-flow
  - flow-builder
  - flow-attribute-change-event
  - flow-navigation
  - validate-hook
  - target-config
inputs:
  - "Component requirement (UI shape, inputs/outputs, validation behavior)"
  - "Target Flow API version (reactive support requires 59+)"
  - "Whether the screen needs to participate in screen-level Next-button validation"
  - "Whether the component needs to drive navigation programmatically (e.g. auto-advance after barcode scan)"
  - "Mobile / form-factor support requirement"
outputs:
  - "LWC bundle (.html / .js / .js-meta.xml) wired for Flow Screen with proper inputs, outputs, validation, and reactivity"
  - "targetConfig declaration with typed properties (String / Boolean / Integer / sObject / Apex) and outputOnly roles"
  - "Decision on stock-component-vs-custom-LWC for the screen requirement"
  - "Validation contract documented (synchronous validate() return shape)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-27
---

# Flow Screen LWC Components

Activate this skill when a Screen Flow needs UI behavior that the stock screen components cannot deliver — and you are deciding the shape of a custom Lightning Web Component that will render at runtime inside a screen step. The skill covers the Flow-side contract: which `@api` properties become Flow inputs and outputs, how `FlowAttributeChangeEvent` propagates user input back to Flow variables, when to fire `FlowNavigationNextEvent`, and how the `@api validate()` hook participates in the Next-button validation cycle. It does NOT cover custom property editors (the design-time admin UX — see `flow-custom-property-editors`) and is the Flow-domain framing of the LWC implementation deep-dive in `lwc/lwc-in-flow-screens`.

---

## Before Starting

Gather this context before touching the LWC bundle or the Flow:

- **What does the stock component NOT do?** Salesforce ships rich screen components — `lightning-input`, `lightning-input-address`, `lightning-record-form`, `lightning-record-edit-form`, `lightning-radio-group`, `lightning-input-rich-text`, plus Reactive Screen Components since Winter '24. Most "I need a custom screen LWC" requests can be solved with stock + a Flow formula. Confirm the gap is real before generating code.
- **Is reactivity needed?** Reactive Screen Components (Flow API version 59 / Winter '24 +) let one component's output update another component's input on the same screen with no Next click. If the requirement is "field B should update when field A changes," you may not need a custom LWC at all.
- **Mobile?** Flow Screen LWCs render in the Salesforce mobile app only when `<supportedFormFactors>` in the targetConfig declares `Small`. Default is `Large` only. If the flow runs on mobile, declare both, and test on a real device — not all base components behave identically on mobile.
- **Who configures the flow?** Admins in Flow Builder will set the `@api` property values from the property panel. Anything you don't expose in `<targetConfig>` cannot be set by an admin even if it's `@api`. Decide which props are admin-tunable vs hardcoded contract.
- **What is the validation contract?** If the LWC must block the Next button on invalid input, the `@api validate()` method must return a synchronous `{ isValid: boolean, errorMessage?: string }`. The Flow runtime ignores Promises returned from `validate()`.

---

## Core Concepts

### Concept 1 — Targeting `lightning__FlowScreen`

A component is only available in Flow Builder's screen-component palette if its `componentName.js-meta.xml` declares `<target>lightning__FlowScreen</target>`. Without this target, the component does not appear in the palette at all — even if it exists, is deployed, and works perfectly on a Lightning page. The two most common authoring mistakes are: (1) forgetting the target entirely, (2) declaring only `lightning__AppPage` / `lightning__RecordPage` and assuming Flow Builder will pick it up.

```xml
<targets>
  <target>lightning__FlowScreen</target>
</targets>
```

If the component should ALSO be usable on a Lightning page, list both targets and gate target-specific behavior with `<targetConfig>` blocks.

### Concept 2 — `@api` properties become Flow inputs and outputs

Every `@api` property on the component class becomes a candidate Flow variable. Whether it acts as an input, an output, or both depends on the `<targetConfig>` declaration:

- **Default (input):** any `@api` property listed in `<targetConfig>` `<property>` is admin-settable in Flow Builder. The Flow assigns the value into the LWC at render time.
- **Output-only:** add `role="outputOnly"` to mark the property as a Flow output. The admin can map it to a Flow variable to receive the value. The LWC must dispatch `FlowAttributeChangeEvent` to actually push the new value back.
- **Input + output:** omit `role`. Admin can both seed the value and map it to a Flow variable that receives updates.

Property `type` must be one of `String`, `Boolean`, `Integer`, `sObject`, `apex` (with `extensionName="Namespace.ApexClassName"` for Apex-defined types). String is the default if omitted.

### Concept 3 — `FlowAttributeChangeEvent` propagation

The Flow runtime does NOT detect changes to `@api` properties via setter mutation. To push a new value back to a Flow variable, the LWC must dispatch a `FlowAttributeChangeEvent`:

```js
import { FlowAttributeChangeEvent } from 'lightning/flowSupport';
// ...
this.dispatchEvent(new FlowAttributeChangeEvent('outputValue', newValue));
```

The first constructor argument MUST match the `@api` property's API name exactly (case-sensitive). The second is the new value. Without this dispatch, the Flow variable mapped to the output stays at its initial value, no matter how many times the user types into the field.

### Concept 4 — Navigation and validation hooks

Two related hooks let the LWC participate in screen flow execution:

- **`@api validate()`** — Flow calls this on every screen LWC when the user clicks Next, Pause, or Finish. The LWC returns `{ isValid: true }` or `{ isValid: false, errorMessage: 'Reason shown to the user' }`. Must be synchronous. If any LWC returns `isValid: false`, navigation is blocked and the message renders at the top of the screen.
- **`FlowNavigationNextEvent` / `FlowNavigationBackEvent` / `FlowNavigationFinishEvent` / `FlowNavigationPauseEvent`** — fire one of these to programmatically advance, retreat, finish, or pause the flow without a user click. Common pattern: a barcode-scanner LWC fires `Next` automatically after a successful scan. Imported from the same `lightning/flowSupport` module. The screen must have the matching navigation action available (e.g. `Next` is unavailable on the last screen — fire `Finish` instead, or it does nothing).

---

## Common Patterns

### Pattern 1 — Output via `FlowAttributeChangeEvent`

**When to use:** the user types or selects something inside the LWC and a Flow variable on a downstream element needs the value.

**How it works:**

1. Declare the property `@api outputValue;` on the class.
2. Declare it in `<targetConfig>` with `role="outputOnly"` (or omit `role` if it's also an input).
3. On every relevant user event, dispatch `new FlowAttributeChangeEvent('outputValue', this.draftValue)`.
4. The admin maps `{!outputValue}` to a Flow variable in Flow Builder.

**Why not the alternative:** mutating `this.outputValue = newValue` without dispatching the event leaves the Flow variable stale. This is the #1 cause of "my flow always sees the empty value."

### Pattern 2 — Programmatic Next on validation success

**When to use:** scanner / kiosk / single-question screens where you want the flow to advance the moment a valid value is captured, with no Next button click.

**How it works:**

1. Capture the user input (scan, key press, OAuth callback).
2. Validate inline. On failure, render an inline error and do nothing.
3. On success, dispatch `new FlowAttributeChangeEvent(...)` for every output property.
4. Then dispatch `new FlowNavigationNextEvent()`.

The order matters. If you fire Next before the attribute-change events propagate, the next screen may render before the Flow runtime sees the new variable values. Dispatch attribute changes first, await `Promise.resolve()` (microtask flush), then fire Next if you've seen ordering issues.

**Why not the alternative:** auto-firing Next without `validate()` participation means a manual Next click later in the flow could replay this screen's bad state. Always also implement `@api validate()` so the same gating runs on a manual click.

### Pattern 3 — Reactive component pair

**When to use:** the value of one custom LWC's output should update another custom LWC's input on the same screen, with no Next click.

**How it works:**

1. Both LWCs target `lightning__FlowScreen`.
2. The "source" LWC dispatches `FlowAttributeChangeEvent` for its output property.
3. The admin in Flow Builder wires the source's output → a Flow variable → the target LWC's input. This is just the normal Flow Builder property panel mapping — there is no LWC-to-LWC direct binding.
4. The Flow's API version must be 59.0 or higher. Older flows ignore reactive updates.
5. The target LWC sees the new input as a property assignment; if it needs to react, implement a setter or `renderedCallback` that responds to the change.

**Why not the alternative:** older `aura:attribute`-style cross-component messaging does not exist for Flow screens. Do not try to use `pubsub`, `lightning/messageService`, or DOM querying to share state across screen LWCs — Flow's variable model is the contract.

---

## Decision Guidance

Use this table to decide whether a screen requirement justifies a custom LWC at all, and which Flow-side mechanic fits.

| Situation | Recommended Approach | Reason |
|---|---|---|
| User needs to enter a value into a typed field | **Stock `Display Text` + `Text` / `Number` screen component** | No LWC. Stock components ship with Flow validation and accessibility. |
| Field B should react to field A on the same screen | **Reactive Screen Component (stock) — Flow API 59+** | No custom LWC needed. Reactive formula references update without Next. |
| Visual layout that stock components can't render (e.g. card grid, chart, custom datatable) | **Custom LWC targeting `lightning__FlowScreen`** | Use this skill. Output via `FlowAttributeChangeEvent`. |
| User must scan a barcode and auto-advance | **Custom LWC + `FlowNavigationNextEvent`** | Stock has no scanner. Fire Next after dispatch of the scanned value. |
| Must block Next on a complex cross-field rule | **Custom LWC + `@api validate()` hook** | Validation rules on the object don't run pre-DML. Use `validate()` for screen-level gating. |
| Configure how an LWC behaves at design time in Flow Builder | **Custom Property Editor — separate skill** | This is `flow-custom-property-editors`, not this skill. |
| Need to render a flow inside an existing LWC | **`lightning-flow` base component** | Different direction; not a screen LWC at all. |

---

## Recommended Workflow

1. **Confirm the gap.** Search the stock screen-component palette and reactive-formula docs. If a stock combination satisfies the requirement, do not author an LWC. Cite the gap in the design notes.
2. **Decide the I/O contract.** List every `@api` property and label it `input`, `output`, or `both`. Pick the type for each (`String`, `Boolean`, `Integer`, `sObject`, `apex`). Write the contract down before writing code.
3. **Author the meta.xml first.** Declare `<target>lightning__FlowScreen</target>`, then `<targetConfig targets="lightning__FlowScreen">` with one `<property>` per admin-configurable `@api` field. Mark outputs `role="outputOnly"`. Set `<supportedFormFactors>` if mobile is in scope.
4. **Implement the LWC class.** Match every `@api` property to a `<property>` in meta.xml. Wire user-input handlers to dispatch `FlowAttributeChangeEvent` for every output. Implement `@api validate()` synchronously and return the documented shape.
5. **Wire navigation events only if needed.** Most components do not need to fire `FlowNavigationNextEvent` — let the user click Next. Auto-advance is justified only for scanner / kiosk / single-question patterns.
6. **Test in Flow Builder + at runtime.** Add the component to a throwaway Screen Flow. Verify (a) the component appears in the palette, (b) configurable properties show in the property panel with correct types, (c) outputs propagate to Flow variables, (d) `validate()` blocks Next when expected, (e) reactivity works on Flow API 59+.
7. **Document the contract** in the LWC's README or skill-local examples. Future admins will reuse this component without reading the source — make the input/output table discoverable.

---

## Review Checklist

- [ ] `lightning__FlowScreen` target is declared in meta.xml.
- [ ] Every `@api` property exposed to admins has a matching `<property>` entry in `<targetConfig>` with the correct type.
- [ ] Every output property has `role="outputOnly"` AND a `FlowAttributeChangeEvent` dispatch on user input.
- [ ] `@api validate()` is synchronous (no `async`, no `await`, no Promise return) and returns `{ isValid, errorMessage? }`.
- [ ] Navigation events (`Next`/`Back`/`Finish`/`Pause`) are only fired when the screen actually has that action available.
- [ ] Reactive cross-component dependencies are documented and the consuming Flow is at API version 59+.
- [ ] Mobile support is either explicit (`<supportedFormFactors>` includes `Small` and tested on device) or explicitly out of scope.
- [ ] No usage of `pubsub`, `lightning/messageService`, or DOM cross-querying to share state with other screen LWCs.
- [ ] No `lwc/wire` data fetch is gated by `validate()` — `validate()` cannot wait on a Promise.

---

## Salesforce-Specific Gotchas

1. **Missing `lightning__FlowScreen` target → invisible in Flow Builder.** The component deploys cleanly, shows up under Setup → Lightning Components, but the screen-component palette in Flow Builder never lists it. There is no error message — the absence is silent. Always grep the meta.xml for the target string before debugging anything else.
2. **`@api validate()` must be synchronous.** If you write `async validate()` or return a Promise, Flow ignores the return value entirely and treats the screen as valid. Users sail past invalid input. Detect this by reading the method signature: any `async` keyword or `.then(` inside the function is a defect.
3. **Reactive screen components require Flow API version 59+.** Building a perfectly correct LWC pair and dropping them into a Flow created on an older API version produces a screen where outputs propagate only on Next, not in real time. The Flow's API version is set at flow creation; admins frequently clone old flows and never update it.
4. **`FlowNavigationFinishEvent` from a non-final screen ends the flow abruptly.** The runtime treats Finish as terminal regardless of where it fires. If the LWC is on screen 2 of 5, firing Finish skips screens 3-5 entirely, including any post-screen DML actions. Use `FlowNavigationNextEvent` unless the LWC actually knows it is on the last screen.
5. **`role="outputOnly"` does not auto-emit value changes.** Declaring the role in meta.xml makes Flow Builder show the property in the output mapping panel, but the runtime still requires an explicit `FlowAttributeChangeEvent` dispatch. Outputs that "don't update" almost always have the role set correctly but no event dispatch in the JS.
6. **`FlowAttributeChangeEvent` attribute name is case-sensitive.** Dispatching `new FlowAttributeChangeEvent('OutputValue', v)` for an `@api outputValue` property silently fails — the Flow runtime cannot match the names. Always copy the property name exactly.
7. **`@api` properties are typed by what JS assigns at runtime, not what meta.xml says.** If meta.xml declares `type="Integer"` but the LWC dispatches a string, Flow may coerce or warn at design time — but at runtime, downstream Flow elements may receive the wrong type. Validate types in the dispatch site.
8. **Importing from `lightning/uiRecordApi` or other base modules inside `validate()` does not work.** `validate()` is called synchronously during Next-click handling; any async data fetch initiated there returns a Promise the runtime ignores. Pre-fetch in `connectedCallback` or via `@wire`, store on the instance, and validate against the cached value.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `componentName.js-meta.xml` | Includes `<target>lightning__FlowScreen</target>` and a `<targetConfig>` declaring every admin-configurable `@api` property with type and (where relevant) `role="outputOnly"`. |
| `componentName.js` | Implements `@api` inputs/outputs, dispatches `FlowAttributeChangeEvent` on every user-input mutation of an output property, and implements synchronous `@api validate()` returning `{ isValid, errorMessage? }`. |
| `componentName.html` | Renders the screen UI; uses base components (`lightning-input`, etc.) for accessibility. |
| Flow Builder integration notes | A short admin-facing readme describing each input, each output, the validation behavior, and the minimum Flow API version (59+ if reactive). |

---

## Related Skills

- `skills/flow/flow-screen-flows` — design framing for Screen Flow as a whole, before deciding to drop in a custom LWC.
- `skills/flow/flow-reactive-screen-components` — reactivity rules for stock components; check this before authoring a custom LWC for a reactivity-only requirement.
- `skills/flow/flow-screen-input-validation-patterns` — stock validation rule patterns; preferred when the validation can be expressed declaratively.
- `skills/flow/flow-screen-flow-accessibility` — accessibility requirements for screen flows, applies equally to custom LWC screens.
- `skills/flow/flow-custom-property-editors` — the OTHER LWC-in-flow scenario: design-time configuration UX, not runtime rendering.
- `skills/lwc/lwc-in-flow-screens` — the LWC-domain implementation deep-dive (the component-author's view of the same contract).
- `skills/lwc/lwc-component-skeleton` (template `templates/lwc/component-skeleton/`) — the canonical LWC bundle starting point.
- `skills/lwc/lwc-flow-properties` — typed input/output declaration patterns in `<targetConfig>`.

---

## Official Sources Used

- Lightning Web Components Dev Guide — Build Components for Flow Screens: https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-builder-screen.html
- Lightning Web Components Dev Guide — `lightning/flowSupport` Module: https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-flow-support.html
- Lightning Web Components Dev Guide — Configure a Component for Flow Screens (`targetConfig`): https://developer.salesforce.com/docs/platform/lwc/guide/reference-targets.html
- Salesforce Help — Reactive Screen Components: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_screen_reactive.htm
- Winter '24 Release Notes — Reactive Screens: https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_builder_reactive_screens.htm
- Lightning Web Components Dev Guide — Custom Property Editors (for distinguishing scope): https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-custom-property-editor.html
