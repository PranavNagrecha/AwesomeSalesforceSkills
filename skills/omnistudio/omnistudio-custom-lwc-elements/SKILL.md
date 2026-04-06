---
name: omnistudio-custom-lwc-elements
description: "Creating and integrating custom Lightning Web Components within OmniScripts: LWC override patterns, pubsub event handling, custom validation, OmniStudio data passing conventions. Use when a standard OmniScript element cannot meet a UX requirement. NOT for standalone LWC development (use lwc/* skills). NOT for Integration Procedures (use integration-procedures). NOT for embedding an OmniScript inside an LWC (use omnistudio-lwc-integration)."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Reliability
triggers:
  - "how do I add a custom LWC component inside an OmniScript"
  - "LWC not receiving data from OmniScript context"
  - "custom validation in OmniScript using LWC"
  - "OmniScript pubsub event handling in LWC"
  - "override a standard OmniScript element with a custom LWC"
  - "omniJsonData not updating when user navigates back in OmniScript"
  - "how to fire omniupdatebyfield from a custom LWC element"
tags:
  - omnistudio
  - omniscript
  - lwc
  - custom-component
  - override
  - pubsub
  - omniupdatebyfield
  - omniJsonData
inputs:
  - "OmniStudio runtime type: native (omnistudio namespace) or managed package (vlocity_cmt / vlocity_ins / vlocity_ps)"
  - "The OmniScript type and subtype that will host the custom LWC element"
  - "UX requirements that the standard OmniScript element cannot satisfy"
  - "Input field names the OmniScript passes to the LWC (from OmniScript data model to LWC properties)"
  - "Output field names the LWC must push back into the OmniScript data model"
  - "Whether custom validation is required (blocking step navigation until criteria are met)"
outputs:
  - "Custom LWC element component with correct OmniStudio lifecycle hooks (connectedCallback, disconnectedCallback)"
  - "Pubsub event dispatch pattern for pushing values back into the OmniScript data model"
  - "Custom validation implementation that blocks or allows OmniScript step navigation"
  - "OmniScript designer configuration JSON for the custom element step (input/output field mapping)"
  - "Checker script results identifying lifecycle, pubsub, and namespace issues in the LWC metadata"
dependencies:
  - omnistudio/omnistudio-lwc-integration
  - omnistudio/omniscript-design-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# OmniStudio Custom LWC Elements

This skill activates when the work requires authoring a Lightning Web Component to be embedded as a custom element inside an OmniScript screen. Use it when a standard OmniScript element (Text, Date, Select, etc.) cannot meet a UX or validation requirement, and a custom LWC override is needed. The skill covers the full lifecycle of a custom element: receiving OmniScript context data, communicating values back through the pubsub event system, implementing custom validation, and configuring the element in the OmniScript designer. NOT for standalone LWC development, Integration Procedure design, or the reverse direction (embedding an OmniScript inside an LWC — see `omnistudio-lwc-integration` for that).

---

## Before Starting

Gather this context before working on anything in this domain:

- **Identify the OmniStudio runtime.** Check the org's `OmniStudioSettings` metadata or the Setup > OmniStudio page to confirm whether native OmniStudio is active (`enableOaForCore = true`) or whether the org runs a managed package (vlocity_cmt, vlocity_ins, vlocity_ps). The pubsub module import path differs: `omnistudio/pubsub` for native, `vlocity_cmt/pubsub` for managed package. Using the wrong import causes a silent runtime failure where the LWC renders but never updates the OmniScript data model.
- **Define the input/output field contract before writing any code.** The OmniScript designer custom element step requires explicit field mappings. Input fields are OmniScript data keys mapped to LWC `@api` properties. Output fields are LWC event keys that the OmniScript listens for via pubsub. These names must match exactly — case-sensitively — in both the OmniScript configuration and the LWC JavaScript.
- **Determine whether the element needs custom validation.** If the OmniScript step should block navigation until the LWC component confirms valid state, the LWC must dispatch the `omnivalidate` pubsub event in response to the OmniScript's step navigation attempt. If no validation is needed, only `omniupdatebyfield` dispatch is required.
- **Wire adapters are not reliable inside custom OmniScript elements.** The OmniScript runtime does not guarantee that wire service subscriptions re-resolve correctly across step navigation. Use imperative Apex calls (`@salesforce/apex` import called in `connectedCallback`) for any server-side data needs within the element.

---

## Core Concepts

### Custom LWC Element Types in OmniScript

OmniScript supports two custom element mechanisms:

**Custom LWC Element** is the primary mechanism. The LWC is registered in the OmniScript designer by API name. The OmniScript passes the current script data to the LWC via the `omniJsonData` property and passes the output field mapping configuration via `omniOutputMap`. The LWC pushes values back into the OmniScript data model by dispatching a pubsub event with the `omniupdatebyfield` key.

**Custom Merge Map Element** is a secondary mechanism where a JSON object produced by the LWC is merged wholesale into the OmniScript data model at a specific path. This is less common and is used when the LWC produces a structured object rather than individual field values. The element type is configured in the OmniScript designer as a Merge Map custom element.

For the vast majority of custom UX overrides (date pickers, address lookups, multi-select widgets), the Custom LWC Element pattern using `omniupdatebyfield` is the correct choice.

### OmniScript Lifecycle Conventions for Custom Elements

A custom LWC element has a tighter lifecycle contract with the OmniScript runtime than a standalone LWC:

- **`connectedCallback`** is called when the OmniScript step containing the element is rendered. At this point, `omniJsonData` is populated with the current script data. Use this to restore previously entered values so the user's input is preserved when navigating back to the step.
- **`disconnectedCallback`** is called when the user navigates away from the step. Use this to clean up any pubsub subscriptions or local state that should not persist across step navigation.
- **`omniJsonData`** must be declared as `@api omniJsonData`. Do not declare it as a tracked property. Mutations to `omniJsonData` inside the LWC do not propagate back to the OmniScript — only pubsub events do.
- **`omniOutputMap`** must be declared as `@api omniOutputMap`. This is the channel reference the OmniScript runtime sets up for the LWC's pubsub output. Pass this reference to `pubsub.fireEvent` so the event reaches the correct OmniScript instance.

### Pubsub Event Architecture for OmniScript–LWC Communication

Custom elements communicate with OmniScript through the OmniStudio pubsub module, not through DOM events or `dispatchEvent`. This is different from standard LWC parent-child communication:

1. Import the pubsub module: `import pubsub from 'omnistudio/pubsub'` (native) or `import pubsub from 'vlocity_cmt/pubsub'` (managed package).
2. When the user changes a value in the LWC, call `pubsub.fireEvent(this.omniOutputMap, 'omniupdatebyfield', { FieldName: value })`. The first argument (`this.omniOutputMap`) scopes the event to the specific OmniScript instance hosting this element, preventing cross-instance contamination.
3. The field name key in the event payload must match the output field mapping configured in the OmniScript designer custom element step.

For custom validation, the OmniScript fires a `omniscriptvalidate` event on the element when the user attempts to navigate to the next step. The LWC can listen for this event and respond with a pass/fail signal by calling `pubsub.fireEvent(this.omniOutputMap, 'omnivalidate', { valid: true/false, errorMessage: '...' })`.

### Custom Validation Implementation

To block OmniScript step navigation until the custom element validates its state:

1. In `connectedCallback`, subscribe to the `omniscriptvalidate` event: `pubsub.registerListener('omniscriptvalidate', this.handleValidate, this)`.
2. Implement `handleValidate` to check the LWC's local state and call `pubsub.fireEvent(this.omniOutputMap, 'omnivalidate', { valid: <boolean>, errorMessage: '<message if invalid>' })`.
3. In `disconnectedCallback`, unregister the listener: `pubsub.unregisterListener('omniscriptvalidate', this.handleValidate, this)`.

If the LWC fires `omnivalidate` with `{ valid: false }`, the OmniScript halts step navigation and displays the error message. If `{ valid: true }`, navigation proceeds.

### Element Override Pattern

OmniScript also supports element-level overrides, where a standard element type (e.g., a Text element) is replaced entirely by a custom LWC for a specific element within a step. This is configured in the OmniScript designer on the element property panel under "Custom LWC Override." The override inherits the element's property set, meaning the LWC receives the element's configuration (label, required flag, etc.) through `omniJsonData` alongside the step data. This pattern is useful when a standard element's data binding and validation are adequate but its visual rendering needs to be replaced.

---

## Common Patterns

### Pattern 1: Custom Multi-Select Widget Replacing a Standard Checkbox Group

**When to use:** The OmniScript needs a visually enhanced multi-select control (pill-based selection, search-filtered chips, drag-reorder) that the standard Checkbox Group element cannot render.

**How it works:**
1. Build an LWC with `@api omniJsonData`, `@api omniOutputMap`, and a local tracked array for selections.
2. In `connectedCallback`, read `omniJsonData.SelectedItems` (or whatever field is pre-configured) to restore any prior selections.
3. When the user toggles a selection, update the local array and dispatch: `pubsub.fireEvent(this.omniOutputMap, 'omniupdatebyfield', { SelectedItems: this._selections })`.
4. In the OmniScript designer, add a Custom LWC element step with the component API name. Configure input mapping: `SelectedItems` → `omniJsonData.SelectedItems`. Configure output mapping: `SelectedItems` from the LWC event back to the root data node.
5. Activate the OmniScript. The multi-select renders within the step; selected values are captured in the OmniScript data model.

**Why not the alternative:** Using a standard Checkbox Group and relying on CSS overrides does not work because OmniScript elements are Shadow DOM-isolated and cannot be styled from outside. A custom LWC is the only way to control the rendering.

### Pattern 2: Custom Validation on an Address Lookup Element

**When to use:** The OmniScript has an address entry step with a custom LWC providing a USPS/Google address autocomplete. The step must not advance until the user has selected a verified address from the autocomplete suggestions (not just typed free text).

**How it works:**
1. Build a custom address LWC. Track an `_isVerified` boolean that is `false` until the user selects from the autocomplete suggestions.
2. In `connectedCallback`, subscribe to `omniscriptvalidate` and restore any prior verified address from `omniJsonData`.
3. In the `omniscriptvalidate` handler: if `_isVerified`, fire `pubsub.fireEvent(this.omniOutputMap, 'omnivalidate', { valid: true })`. Otherwise fire `{ valid: false, errorMessage: 'Please select a verified address from the suggestions.' }`.
4. When the user selects an address from autocomplete, set `_isVerified = true` and fire `omniupdatebyfield` with the address fields.
5. In `disconnectedCallback`, unregister the `omniscriptvalidate` listener.

**Why not the alternative:** Using the OmniScript's built-in Required flag on a standard Text field does not validate the address is from the verified autocomplete source — it only checks that the field is non-empty. Custom validation via pubsub is the only mechanism to enforce LWC-local business rules before step navigation proceeds.

### Pattern 3: Merge Map Element for Structured Object Output

**When to use:** The custom LWC produces a complex nested object (e.g., a selected product configuration with nested options and pricing) that needs to be stored at a specific path in the OmniScript data model, not as individual field values.

**How it works:**
1. Build a custom LWC that outputs a JavaScript object, e.g. `{ productId: '...', options: [...], basePrice: 99.99 }`.
2. Use the Custom Merge Map element type in the OmniScript designer instead of Custom LWC element.
3. Configure the merge path in the OmniScript designer to point to the destination key in the data model (e.g., `SelectedProduct`).
4. When the user completes their selection, dispatch `pubsub.fireEvent(this.omniOutputMap, 'omnimerge', { SelectedProduct: this._config })` using the `omnimerge` event key instead of `omniupdatebyfield`.
5. The OmniScript merges the entire object under `SelectedProduct` in the data JSON.

**Why not the alternative:** Using `omniupdatebyfield` with nested objects requires flattening the output into individual top-level keys and mapping each one separately. The Merge Map pattern avoids this when the output structure is inherently hierarchical and managed as a unit.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard OmniScript element rendering is insufficient but data binding and validation are adequate | Element Override (Custom LWC Override in element properties) | Preserves element configuration and native validation; only replaces rendering |
| Custom element needs to write one or more scalar values back to OmniScript | Custom LWC Element with `omniupdatebyfield` | The standard mechanism for field-level updates from custom elements |
| Custom element produces a structured nested object for the OmniScript data model | Custom Merge Map Element with `omnimerge` | Avoids flattening and keeps the object hierarchy intact |
| Step navigation must be blocked until LWC state is valid | Subscribe to `omniscriptvalidate` and respond with `omnivalidate` | The OmniScript pubsub validation channel is the only supported mechanism |
| LWC needs server data inside the OmniScript step | Imperative Apex call in `connectedCallback` | Wire adapters are unreliable inside the OmniScript step lifecycle; imperative calls are stable |
| Org is on native OmniStudio (`enableOaForCore = true`) | Import pubsub from `omnistudio/pubsub` | Native namespace; managed package import path causes module-not-found error at deploy time |
| Org is on managed package (vlocity_cmt, vlocity_ins, vlocity_ps) | Import pubsub from `vlocity_cmt/pubsub` | Native pubsub module is not deployed in managed package orgs |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm the OmniStudio runtime.** Check `OmniStudioSettings` metadata or the Setup > OmniStudio page for `enableOaForCore`. Record whether the org is native or managed package — this determines the pubsub import path for all code in this task.
2. **Define the field contract.** List every input field the OmniScript will pass to the LWC (from the OmniScript data model to `omniJsonData`) and every output field the LWC will push back. Name them explicitly, case-sensitively, before writing any code. This contract is shared between the LWC JavaScript and the OmniScript designer configuration.
3. **Build the custom LWC.** Declare `@api omniJsonData` and `@api omniOutputMap`. Implement `connectedCallback` to restore state from `omniJsonData`. Implement `disconnectedCallback` to clean up listeners. For each user action that produces output, call `pubsub.fireEvent(this.omniOutputMap, 'omniupdatebyfield', { FieldName: value })`. For custom validation, subscribe to `omniscriptvalidate` in `connectedCallback` and unsubscribe in `disconnectedCallback`.
4. **Deploy and verify the LWC.** Push the LWC to the org using SFDX. Confirm there are no deploy errors — namespace resolution errors for the pubsub module will surface at this stage, not at runtime.
5. **Configure the custom element step in the OmniScript designer.** Open the OmniScript, add a Custom LWC Element step (or Custom Merge Map step). Enter the component API name. Configure input mappings from the OmniScript data model to the LWC, using the exact field names from the contract defined in step 2. Configure output mappings from the LWC event to the OmniScript data model using the same names.
6. **Activate and test.** Activate the OmniScript version. Test the full forward and backward navigation flow: navigate to the step, enter a value, navigate away, navigate back, and confirm the value is restored. Test validation rejection if custom validation is implemented.
7. **Run the checker script.** Execute `python3 skills/omnistudio/omnistudio-custom-lwc-elements/scripts/check_omnistudio_custom_lwc_elements.py --manifest-dir force-app/main/default` to detect pubsub import mismatches, missing lifecycle hooks, and missing `@api` property declarations.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Pubsub module import path matches the org's OmniStudio runtime (`omnistudio/pubsub` for native, `vlocity_cmt/pubsub` for managed package)
- [ ] `@api omniJsonData` and `@api omniOutputMap` are declared (not tracked properties)
- [ ] `connectedCallback` restores prior values from `omniJsonData` to support backward navigation
- [ ] `disconnectedCallback` unregisters all pubsub listeners subscribed in `connectedCallback`
- [ ] Output field names in `omniupdatebyfield` payload match OmniScript designer output mapping exactly (case-sensitive)
- [ ] If custom validation is required: `omniscriptvalidate` is subscribed and `omnivalidate` response is fired with `valid` boolean and `errorMessage`
- [ ] No `@wire` adapters are used inside the custom element LWC; server data loads use imperative Apex in `connectedCallback`
- [ ] OmniScript designer step is configured with correct component API name, input mapping, and output mapping
- [ ] Checker script passes with no issues

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Wrong pubsub import path causes silent data model failure** — Importing `omnistudio/pubsub` in a managed package org (or `vlocity_cmt/pubsub` in a native org) results in the import failing at deploy time or the module resolving to a stub that does not connect to the OmniScript runtime. The LWC renders normally, but firing `omniupdatebyfield` does nothing — the OmniScript data model never updates. Always verify the runtime before writing any pubsub code.
2. **Output field name case mismatch silently drops data** — OmniScript output field mapping is case-sensitive. If the OmniScript designer output configuration declares `SelectedDate` and the LWC fires `{ selectedDate: value }` (lowercase `s`), the OmniScript does not capture the value. There is no runtime error. Downstream steps that reference `SelectedDate` evaluate as empty. Agree on exact field names before building either the LWC or the OmniScript configuration.
3. **`omniJsonData` does not update reactively** — `omniJsonData` is set once when the step renders via `connectedCallback`. It does not update reactively if the OmniScript data model changes while the step is displayed. If the LWC needs to react to data changes during the step, it must subscribe to additional pubsub events — it cannot rely on `@track omniJsonData` watching for changes.
4. **Validation listener must be unregistered or duplicate events fire** — If `omniscriptvalidate` is registered in `connectedCallback` and the user navigates back to the same step multiple times without the listener being cleaned up in `disconnectedCallback`, the validation handler fires multiple times for a single navigation event. This causes unpredictable validation behavior and potential double-response errors in the pubsub channel.
5. **Wire adapters do not re-resolve after step navigation** — A `@wire` adapter declared in a custom element LWC may resolve correctly on the first render but return stale or empty data when the user navigates back to the step. The OmniScript step lifecycle does not guarantee that the wire service re-evaluates reactive source properties on reconnection. Use imperative Apex called from `connectedCallback` for reliable data loading inside custom elements.
6. **Custom Merge Map elements require the `omnimerge` event, not `omniupdatebyfield`** — Attempting to push a nested object using `omniupdatebyfield` with a nested key path does not merge the object — it stores the value as a string or drops it depending on the OmniScript version. The `omnimerge` event must be used with the Merge Map element type.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Custom LWC element component | LWC with OmniStudio lifecycle hooks, `omniupdatebyfield` dispatch, and optional `omniscriptvalidate` subscription |
| OmniScript designer step config | Input/output field mapping JSON for the custom element step in the OmniScript designer |
| Validation handler | `handleValidate` method with `omnivalidate` response firing for custom step navigation control |
| Checker script results | Output of `check_omnistudio_custom_lwc_elements.py` identifying lifecycle, pubsub, and namespace issues |

---

## Related Skills

- `omnistudio/omnistudio-lwc-integration` — use when the direction is reversed: embedding an OmniScript inside an LWC, or calling an Integration Procedure from LWC
- `omnistudio/omniscript-design-patterns` — use when the structural design of the OmniScript (step count, branching, save/resume) is the primary concern, not the custom element implementation
- `omnistudio/integration-procedures` — use when the server-side data orchestration logic needs to be designed or reviewed, separate from the LWC element authoring
- `lwc/custom-property-editor-for-flow` — use when the custom component context is a Screen Flow, not an OmniScript
