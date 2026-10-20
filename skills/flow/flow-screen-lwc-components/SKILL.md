---
name: flow-screen-lwc-components
description: "Design custom Lightning Web Components that render inside Screen Flow steps — covers the lightning__FlowScreen target, @api properties as Flow inputs/outputs, FlowAttributeChangeEvent propagation, FlowNavigationNext/Back/Finish/Pause events, the @api validate() hook, and design-time targetConfig wiring. NOT for the Flow Builder design-time editor that configures it — use flow/flow-custom-property-editors. NOT for the LWC-side implementation deep-dive — use lwc/lwc-in-flow-screens."
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
  - "Target Flow API version (reactivity is built in at 59.0+; 57.0 and 58.0 only with the Process Automation setting, api_meta 264 L120052-120055)"
  - "Whether the screen needs to participate in screen-level Next-button validation"
  - "Whether the component needs to drive navigation programmatically (e.g. auto-advance after barcode scan)"
  - "Mobile / form-factor support requirement"
outputs:
  - "LWC bundle (.html / .js / .js-meta.xml) wired for Flow Screen with proper inputs, outputs, validation, and reactivity"
  - "targetConfig declaration with typed properties (Boolean / Integer / String / Date / DateTime / apex:// / @salesforce/schema) and outputOnly roles"
  - "Decision on stock-component-vs-custom-LWC for the screen requirement"
  - "Validation contract documented (synchronous validate() return shape)"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Flow Screen LWC Components

Activate this skill when a Screen Flow needs UI behavior that the stock screen components cannot deliver — and you are deciding the shape of a custom Lightning Web Component that will render at runtime inside a screen step. The skill covers the Flow-side contract: which `@api` properties become Flow inputs and outputs, how `FlowAttributeChangeEvent` propagates user input back to Flow variables, when to fire `FlowNavigationNextEvent`, and how the `@api validate()` hook participates in the Next-button validation cycle. It does NOT cover custom property editors (the design-time admin UX — see `flow-custom-property-editors`) and is the Flow-domain framing of the LWC implementation deep-dive in `lwc/lwc-in-flow-screens`.

---

## Before Starting

Gather this context before touching the LWC bundle or the Flow:

- **What does the stock component NOT do?** Salesforce ships stock Flow screen components, and reactivity between them is built in for flows on API 59.0 and later (api_meta 264 L120052-120055). UNVERIFIED (2026-10-20): which stock screen components exist is a Help-only list, not in the corpus or the LWC guide. Most "I need a custom screen LWC" requests can be solved with stock + a Flow formula. Confirm the gap is real before generating code.
- **Is reactivity needed?** Reactive screen components (flows on API 59.0 and later; on 57.0 and 58.0 only when `FlowSettings.enableFlowReactiveScreens` is true, default false, api_meta 264 L120052-120055; the corpus is silent below 57.0) let one component's output update another component's input on the same screen with no Next click. If the requirement is "field B should update when field A changes," you may not need a custom LWC at all.
- **Mobile?** UNVERIFIED (2026-10-20): the lightning__FlowScreen target page does not document `<supportedFormFactors>`, and the LWC form-factor page says that for Lightning pages an undeclared tag means the page type's own form factors (lwcguide use-config-form-factors), not "Large only". If the flow runs on mobile, test on a real device — not all base components behave identically on mobile.
- **Who configures the flow?** Admins in Flow Builder will set the `@api` property values from the property panel. Anything you don't expose in `<targetConfig>` cannot be set by an admin even if it's `@api`. Decide which props are admin-tunable vs hardcoded contract.
- **What is the validation contract?** If the LWC must block the Next button on invalid input, the `@api validate()` method returns `{ isValid: boolean, errorMessage?: string }`. UNVERIFIED (2026-10-20): the guide documents only the `{ isValid, errorMessage }` return pair and says arrow-function `validate` does not work (lwcguide use-flow-validate-user-input-for-custom-components); what the runtime does with a returned Promise is not documented, so keep it synchronous and treat "Flow ignores Promises" as observed behaviour.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which stock screen component or reactive formula already covers the gap? | A custom LWC is code the org maintains forever (Decision Guidance). | A named gap (scanner, chart, cross-field rule), or the decision to use stock. |
| Which `@api` properties are inputs, outputs, or both, and what Flow data type is each? | `type` is required in `<targetConfig>` and the XML type wins over the JS type (gotcha 7). | A written I/O table with one declared type per property. |
| What API version will the consuming flow run on? | Reactivity is built in at 59.0+, and only via a setting on 57.0 and 58.0 (gotcha 3). | A minimum flow API version recorded in the component README. |
| Does the screen need to block Next on a rule, and can the rule be checked from cached data? | `validate()` runs when the flow moves to the next screen or finishes, and async fetches inside it are undocumented (gotcha 2, gotcha 8). | A synchronous rule over data pre-fetched in `connectedCallback` or `@wire`. |
| Must the component advance the flow itself? | Navigation events in lifecycle hooks, or fired together with attribute changes, race (gotcha 4, Pattern 2). | A scanner or kiosk justification, or the decision to let the user click Next. |
| Will it run on mobile? | `supportedFormFactors` for FlowScreen is UNVERIFIED, so mobile needs a device test (Before Starting). | An explicit in-scope or out-of-scope statement. |
| Does it take an Apex-defined or sObject input? | The type string is `apex://Class` or `@salesforce/schema/Object`, not `extensionName` (Concept 2). | The exact class or object and its namespace. |

A proper configuration adds a written I/O contract, a declared minimum flow API version, and a validation rule that is checked without a server call, which "just building the LWC" skips.

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

- **Input (`role="inputOnly"`):** the property is admin-settable in Flow Builder and the Flow assigns the value into the LWC at render time. Without a `role` attribute the property is input AND output (lwcguide targets-lightning-flow-screen: "If you don't specify the role attribute, the default value allows input and output").
- **Output-only:** add `role="outputOnly"` to mark the property as a Flow output. The admin can map it to a Flow variable to receive the value. The LWC must dispatch `FlowAttributeChangeEvent` to actually push the new value back.
- **Input + output:** omit `role`. Admin can both seed the value and map it to a Flow variable that receives updates.

Property `type` is required and must be one of `Boolean`, `Integer`, `String`, `Double` (only with `flowRole="flowRuntimeApiVersion"`), `Date`, `DateTime`, `apex://namespace.Classname` for an Apex-defined type (omit the namespace when the class is in the component's own namespace), or `@salesforce/schema/Objectname` for an object (lwcguide targets-lightning-flow-screen). A bare `type="sObject"` and an `extensionName` attribute on `<property>` are not in that list; generic sObject inputs use a `<propertyType>` with `extends="SObject"` and `type="{T}"` (lwcguide use-flow-screen-generic-types). If the XML type and the JS type disagree, the XML value wins.

### Concept 3 — `FlowAttributeChangeEvent` propagation

The guide's pattern is that a component does not modify its own `@api` properties but requests the change by firing `FlowAttributeChangeEvent`; this is what lets reactivity and conditional visibility see the new value. As a fallback the runtime reads each component's current `@api` state when the user clicks Next or Finish, but the guide says to avoid relying on it (lwcguide use-best-practices-reactivity). To push a new value back to a Flow variable, dispatch the event:

```js
import { FlowAttributeChangeEvent } from 'lightning/flowSupport';
// ...
this.dispatchEvent(new FlowAttributeChangeEvent('outputValue', newValue));
```

The first constructor argument must match the `@api` property's name as it appears in the JS and the `.js-meta.xml` (lwcguide use-best-practices-reactivity); UNVERIFIED (2026-10-20): that a wrong-case name fails silently is not documented. The second is the new value, limited to String, number, boolean or JSON for records, and its Flow data type must match the property's. Without the dispatch, reactive targets and conditional visibility on the screen never see the new value.

### Concept 4 — Navigation and validation hooks

Two related hooks let the LWC participate in screen flow execution:

- **`@api validate()`** — Flow calls this when the flow moves to the next screen or finishes (lwcguide use-flow-validate-external-internal-methods; the guide does not list Pause). The LWC returns `{ isValid: true }` or `{ isValid: false, errorMessage: 'Reason shown to the user' }`; arrow-function `validate` does not work. UNVERIFIED (2026-10-20): "must be synchronous", and "the message renders at the top of the screen"; the guide has the component render its own errors in `reportValidity()` and tells you not to render them inside `validate()`.
- **`FlowNavigationNextEvent` / `FlowNavigationBackEvent` / `FlowNavigationFinishEvent` / `FlowNavigationPauseEvent`** — fire one of these to programmatically advance, retreat, finish, or pause the flow without a user click. Common pattern: a barcode-scanner LWC fires `Next` automatically after a successful scan. Imported from the same `lightning/flowSupport` module. The screen must have the matching action in `availableActions` (`Back` is not available on the first screen, `Pause` only where saving is enabled; on the last screen use `Finish`; lwcguide use-flow-screen-navigate). Fire navigation events only in event handlers, never in `connectedCallback` or `renderedCallback`.

---

## Common Patterns

### Pattern 1 — Output via `FlowAttributeChangeEvent`

**When to use:** the user types or selects something inside the LWC and a Flow variable on a downstream element needs the value.

**How it works:**

1. Declare the property `@api outputValue;` on the class.
2. Declare it in `<targetConfig>` with `role="outputOnly"` (or omit `role` if it's also an input).
3. On every relevant user event, dispatch `new FlowAttributeChangeEvent('outputValue', this.draftValue)`.
4. The admin maps `{!outputValue}` to a Flow variable in Flow Builder.

**Why not the alternative:** mutating `this.outputValue = newValue` without dispatching the event hides the change from reactivity and conditional visibility; only the Next/Finish read-back (see Concept 3) can still pick it up.

### Pattern 2 — Programmatic Next on validation success

**When to use:** scanner / kiosk / single-question screens where you want the flow to advance the moment a valid value is captured, with no Next button click.

**How it works:**

1. Capture the user input (scan, key press, OAuth callback).
2. Validate inline. On failure, render an inline error and do nothing.
3. On success, dispatch `new FlowAttributeChangeEvent(...)` for every output property.
4. Then dispatch `new FlowNavigationNextEvent()`.

The guide warns against firing `FlowAttributeChangeEvent` and a navigation event at the same time: there is no guarantee the component has rendered the updated values before navigation begins, which can cause race conditions (lwcguide use-flow-screen-navigate, use-best-practices-reactivity). If auto-advance is unavoidable, dispatch the attribute changes first and test on device. UNVERIFIED (2026-10-20): the earlier advice to `await Promise.resolve()` between them is not in the guide. Write nothing after the Next dispatch: navigation leaves the screen immediately.

**Why not the alternative:** auto-firing Next without `validate()` participation means a manual Next click later in the flow could replay this screen's bad state. Always also implement `@api validate()` so the same gating runs on a manual click.

### Pattern 3 — Reactive component pair

**When to use:** the value of one custom LWC's output should update another custom LWC's input on the same screen, with no Next click.

**How it works:**

1. Both LWCs target `lightning__FlowScreen`.
2. The "source" LWC dispatches `FlowAttributeChangeEvent` for its output property.
3. The admin in Flow Builder wires the source's output → a Flow variable → the target LWC's input. This is just the normal Flow Builder property panel mapping — there is no LWC-to-LWC direct binding.
4. The Flow's API version must be 59.0 or higher (57.0 and 58.0 only with `enableFlowReactiveScreens`, api_meta 264 L120052-120055).
5. The target LWC sees the new input as a property assignment; if it needs to react, implement a setter or `renderedCallback` that responds to the change.

**Why not the alternative:** older `aura:attribute`-style cross-component messaging does not exist for Flow screens. Do not try to use `pubsub`, `lightning/messageService`, or DOM querying to share state across screen LWCs — Flow's variable model is the contract.

---

## Decision Guidance

Use this table to decide whether a screen requirement justifies a custom LWC at all, and which Flow-side mechanic fits.

| Situation | Recommended Approach | Reason |
|---|---|---|
| User needs to enter a value into a typed field | **Stock `Display Text` + `Text` / `Number` screen component** | No LWC. Stock components ship with Flow validation and accessibility. |
| Field B should react to field A on the same screen | **Reactive Screen Component (stock) — flows on API 59.0+** | No custom LWC needed. Reactive formula references update without Next. |
| Visual layout that stock components can't render (e.g. card grid, chart, custom datatable) | **Custom LWC targeting `lightning__FlowScreen`** | Use this skill. Output via `FlowAttributeChangeEvent`. |
| User must scan a barcode and auto-advance | **Custom LWC + `FlowNavigationNextEvent`** | Stock has no scanner. Fire Next after dispatch of the scanned value. |
| Must block Next on a complex cross-field rule | **Custom LWC + `@api validate()` hook** | Validation rules on the object don't run pre-DML. Use `validate()` for screen-level gating. |
| Configure how an LWC behaves at design time in Flow Builder | **Custom Property Editor — separate skill** | This is `flow-custom-property-editors`, not this skill. |
| Need to render a flow inside an existing LWC | **`lightning-flow` base component** | Different direction; not a screen LWC at all. |

---

## Recommended Workflow

1. **Confirm the gap.** Search the stock screen-component palette and reactive-formula docs. If a stock combination satisfies the requirement, do not author an LWC. Cite the gap in the design notes.
2. **Decide the I/O contract.** List every `@api` property and label it `input`, `output`, or `both`. Pick the type for each (`String`, `Boolean`, `Integer`, `apex://Class`, `@salesforce/schema/Object`). Write the contract down before writing code.
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
- [ ] No `lwc/wire` data fetch is gated by `validate()` — the guide documents only a synchronous `{ isValid, errorMessage }` return (UNVERIFIED 2026-10-20: what the runtime does with a Promise is undocumented).

---

## Salesforce-Specific Gotchas

1. **Missing `lightning__FlowScreen` target → invisible in Flow Builder.** The target is what "enables a component to be used on flow screens" (lwcguide targets-lightning-flow-screen); `isExposed` false also hides it from builders (api_meta 264 L86762-86765). UNVERIFIED (2026-10-20): that the absence is silent is observed behaviour. Always grep the meta.xml for the target string before debugging anything else.
2. **`@api validate()`: keep it synchronous and a plain method.** Arrow-function `validate` does not work (lwcguide use-flow-validate-user-input-for-custom-components). UNVERIFIED (2026-10-20): that an `async validate()` is "ignored and the screen treated as valid" is observed, not documented. Detect it by reading the method signature: any `async` keyword or `.then(` inside the function is a defect.
3. **Reactive screen components are built in at Flow API version 59.0+.** For flows on 57.0 and 58.0 the Process Automation setting `enableFlowReactiveScreens` (default false) turns it on; the setting does not apply at 59.0+ (api_meta 264 L120052-120055). UNVERIFIED (2026-10-20): what a flow below 57.0 does is not in the corpus; "outputs propagate only on Next" is observed behaviour. Admins frequently clone old flows and never update the API version.
4. **`FlowNavigationFinishEvent` from a non-final screen ends the flow abruptly.** Finish "finishes the flow interview and triggers any configured post-flow behavior" (lwcguide use-flow-screen-navigate). If the LWC is on screen 2 of 5, firing Finish skips screens 3-5. UNVERIFIED (2026-10-20): that this also skips later DML actions is inferred, not documented. Use `FlowNavigationNextEvent` unless the LWC actually knows it is on the last screen.
5. **`role="outputOnly"` does not auto-emit value changes.** Declaring the role makes the property an output (an `outputOnly` property is not exposed in a custom property editor, lwcguide targets-lightning-flow-screen), but the guide's pattern is an explicit `FlowAttributeChangeEvent` dispatch (lwcguide use-best-practices-reactivity). Outputs that "don't update" in reactive targets usually have the role set but no event dispatch in the JS.
6. **`FlowAttributeChangeEvent` attribute name must match the `@api` name.** The guide says to pass the name as it appears in the JS and the `.js-meta.xml` (lwcguide use-best-practices-reactivity). UNVERIFIED (2026-10-20): case-sensitivity and "silently fails" for `'OutputValue'` vs `outputValue` are not documented. Always copy the property name exactly.
7. **Keep the dispatched value's type equal to the declared type.** The guide says the event's Flow data type must match the `@api` property's, and that when XML and JS types differ the XML value wins (lwcguide use-best-practices-reactivity, targets-lightning-flow-screen). Validate types at the dispatch site.
8. **Do not start async fetches inside `validate()`.** UNVERIFIED (2026-10-20): the guide does not say a returned Promise is ignored (see gotcha 2). Pre-fetch in `connectedCallback` or via `@wire`, store on the instance, and validate against the cached value.

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

- `skills/flow/screen-flows` — design framing for Screen Flow as a whole, before deciding to drop in a custom LWC.
- `skills/flow/flow-reactive-screen-components` — reactivity rules for stock components; check this before authoring a custom LWC for a reactivity-only requirement.
- `skills/flow/flow-screen-input-validation-patterns` — stock validation rule patterns; preferred when the validation can be expressed declaratively.
- `skills/flow/screen-flow-accessibility` — accessibility requirements for screen flows, applies equally to custom LWC screens.
- `skills/flow/flow-custom-property-editors` — the OTHER LWC-in-flow scenario: design-time configuration UX, not runtime rendering.
- `skills/lwc/lwc-in-flow-screens` — the LWC-domain implementation deep-dive (the component-author's view of the same contract).
- `skills/lwc/custom-property-editor-for-flow` — the LWC-side design-time editor for the same components.
- Template `templates/lwc/component-skeleton/` — the canonical LWC bundle starting point.

---

## Official Sources Used

- Lightning Web Components Dev Guide — Build Components for Flow Screens: https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-builder-screen.html
- Lightning Web Components Dev Guide — `lightning/flowSupport` Module: https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-flow-support.html
- Lightning Web Components Dev Guide — Configure a Component for Flow Screens (`targetConfig`): https://developer.salesforce.com/docs/platform/lwc/guide/reference-targets.html
- Salesforce Help — Reactive Screen Components: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_screen_reactive.htm
- Winter '24 Release Notes — Reactive Screens: https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_builder_reactive_screens.htm (UNVERIFIED 2026-10-20: Help is not in the corpus)
- Metadata API Developer Guide 264 L120052-120055 (`FlowSettings.enableFlowReactiveScreens`); L86762-86765 (`LightningComponentBundle.isExposed`)
- LWC guide pages cited as `lwcguide <slug>`: `use-flow-screen-navigate`, `use-best-practices-reactivity`, `use-flow-validate-external-internal-methods`, `use-flow-validate-user-input-for-custom-components`, `targets-lightning-flow-screen`, `use-flow-screen-generic-types`
- Lightning Web Components Dev Guide — Custom Property Editors (for distinguishing scope): https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-custom-property-editor.html
