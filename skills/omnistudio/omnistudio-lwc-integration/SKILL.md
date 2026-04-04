---
name: omnistudio-lwc-integration
description: "Use when embedding OmniScripts in Lightning Web Components, registering custom LWC elements inside OmniScript screens, or calling OmniScript/Integration Procedures from LWC. Triggers: embed omniscript in LWC, custom LWC element in OmniScript, call OmniScript from Lightning page, omnistudio-omni-script tag, seed data JSON, OmniScript launch from LWC. NOT for standalone LWC development, standard Flow embedding, or OmniScript-to-OmniScript embedding."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Scalability
triggers:
  - "how to embed an OmniScript in a Lightning record page as a component"
  - "use a custom LWC component inside an OmniScript screen as a custom element"
  - "call an OmniScript from a Lightning Web Component using seed data"
  - "passing input data from LWC to OmniScript using omnistudio-omni-script tag"
  - "register a custom LWC element in OmniScript with input and output field mapping"
  - "difference between omnistudio-omni-script and c-omni-script component tags"
  - "call an Integration Procedure from a Lightning Web Component"
tags:
  - omnistudio
  - lwc
  - omniscript
  - integration-procedure
  - custom-element
  - embed
  - seed-data
  - native-omnistudio
  - managed-package
inputs:
  - "OmniScript type and subtype (used to identify the component to embed or launch)"
  - "OmniStudio runtime type: native (omnistudio namespace) or managed package (vlocity_cmt/vlocity_ins/vlocity_ps)"
  - "Direction of integration: LWC embedding OmniScript, OmniScript using custom LWC, or LWC calling Integration Procedure"
  - "Seed data JSON structure (if pre-populating OmniScript fields from LWC)"
  - "Custom LWC element input/output field mapping requirements"
outputs:
  - LWC component markup and JavaScript for embedding or launching an OmniScript
  - Custom LWC element boilerplate with OmniStudio interface conventions
  - Integration Procedure invocation pattern from LWC
  - Decision guidance on namespace selection and activation requirements
  - Checker script results identifying mixed-namespace issues in metadata files
dependencies:
  - omnistudio/omniscript-design-patterns
  - omnistudio/integration-procedures
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# OmniStudio LWC Integration

This skill activates when the work involves crossing the boundary between OmniStudio components and Lightning Web Components. Use it when embedding an OmniScript on a Lightning page, registering a custom LWC as an OmniScript element, calling an OmniScript programmatically from LWC, or invoking an Integration Procedure from a Lightning component. NOT for standalone LWC development, standard Screen Flow embedding, or OmniScript-to-OmniScript nesting.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Determine the OmniStudio runtime in use.** Native OmniStudio (enabled via the `enableOaForCore` org setting) uses the `omnistudio` namespace and the `omnistudio-omni-script` component tag. Managed package installations (vlocity_cmt, vlocity_ins, vlocity_ps) use the `c-omni-script` tag. Mixing the two in a single component causes silent render failures that are hard to diagnose.
- **Identify the OmniScript type and subtype.** These two fields form the identity of the OmniScript and must match the `type` and `subtype` attributes passed to the host component.
- **Confirm whether seed data is required.** If the calling page or component knows context (record Id, account data, user selections), it must be serialized as a JSON object and passed as `omni-seed-json` before the component mounts.
- **Check platform constraints.** OmniStudio custom LWC elements must follow specific lifecycle conventions (`connectedCallback`, `disconnectedCallback`, and OmniScript pubsub event conventions). Standard Lightning wire adapters and `@salesforce/apex` imports do not work as expected inside the OmniScript runtime context for custom elements.

---

## Core Concepts

### Native OmniStudio vs Managed Package Namespaces

OmniStudio ships in two deployment modes. The native mode (generally available from Winter '23) uses the `omnistudio` namespace. Components are referenced as `omnistudio-omni-script`, `omnistudio-flex-card`, etc. Managed package installations tied to Vlocity industries clouds use a namespace such as `vlocity_cmt`, `vlocity_ins`, or `vlocity_ps`, and the OmniScript component tag is `c-omni-script`. The activation setting `enableOaForCore` controls whether the native builder is active in the org.

The choice of tag is not cosmetic. Using `c-omni-script` in a native org causes the component to not be found at runtime. Using `omnistudio-omni-script` in a managed package org that has not activated native OmniStudio will also fail silently. A project that inherits legacy managed package code and later migrates to native OmniStudio must sweep all LWC markup for the old tag.

### Embedding OmniScript in LWC

An LWC component can render an OmniScript directly in its template by declaring the OmniScript component tag as a child element. The two required attributes are `omni-script-type` and `omni-script-sub-type`. Optional attributes include `omni-language` (defaults to `English`), `omni-seed-json` (a serialized JSON string of pre-population data), and `hide-nav-bar` (boolean to suppress the built-in navigation bar when the LWC host provides its own).

Output data from the OmniScript is surfaced to the parent LWC through a `complete` DOM event fired on the OmniScript component when the user submits the final step. The parent LWC listens via `addEventListener('complete', handler)` on the element reference or declaratively via `oncomplete` in the template. The event `detail` carries the full OmniScript data JSON.

The `seedDataJSON` property in the OmniScript definition (from `propertySetConfig`) controls the initial data shape. When passing seed data from the parent LWC, the JSON must match the field name hierarchy that the OmniScript internal data model expects. Passing a flat object where the OmniScript expects a nested path will silently fail to populate the fields.

### Custom LWC Elements in OmniScript

OmniScript supports embedding custom LWC components as screen elements. The LWC must be registered as a custom element in the OmniScript designer by providing the component API name and a JSON configuration for input and output field mappings.

The LWC used as a custom element must follow OmniStudio lifecycle conventions. It must use `connectedCallback` to receive data from the OmniScript context and `disconnectedCallback` to clean up listeners. The component communicates back to the OmniScript by dispatching a pubsub message using the OmniScript pubsub module (`omnistudio/pubsub` in native, `vlocity_cmt/pubsub` in managed package). Output variable names declared in the OmniScript JSON configuration must match the JavaScript property names exactly, including case. A mismatch means the OmniScript will not capture the output, and downstream elements that reference those fields will evaluate as empty.

The custom LWC element also receives input data via the `omniJsonData` property, which contains the current OmniScript data JSON at the time the step is rendered.

### Calling OmniScript and Integration Procedures from LWC

An LWC can launch an OmniScript in a navigation modal or inline container using the NavigationMixin and the `standard__component` page reference, or by programmatically rendering the OmniScript component tag. For programmatic launch with seed data, the component attributes must be set before the component is connected to the DOM; setting them after connection does not re-initialize the script state.

For Integration Procedures, the OmniStudio SDK exposes an `OmniRemoteController` (native) or equivalent managed package controller. From LWC, the recommended pattern is to use the `@salesforce/apex` wire or imperative call to an Apex class that delegates to `vlocity_cmt.IntegrationProcedureService` (managed) or the equivalent native Integration Procedure Apex service. Direct client-side REST calls to the Integration Procedure endpoint bypass Apex sharing enforcement and should be avoided.

---

## Common Patterns

### Pattern 1: Embed OmniScript in a Record Page Tab

**When to use:** A service or intake process is built as an OmniScript, and the business wants it to appear as a tab on a Lightning record page without building a separate app page.

**How it works:**
1. Create a container LWC with the OmniScript tag in the template.
2. In the LWC JavaScript, use `@api recordId` to receive the record context from the page.
3. Serialize the record Id and any prefill data into a JSON string and bind it to `omni-seed-json`.
4. Listen for the `complete` event to handle navigation or confirmation display after script submission.
5. Add the container LWC to the Lightning record page using App Builder.

**Why not the alternative:** Placing the OmniScript component tag directly on the App Builder page without a wrapper LWC prevents you from passing dynamic seed data derived from the record context. The App Builder static property panel cannot execute JavaScript to build the seed JSON.

### Pattern 2: Custom LWC Date Picker as OmniScript Element

**When to use:** The OmniScript needs a date selection UX that the built-in date element does not support (e.g., blocked-out dates, inline calendar display).

**How it works:**
1. Build a standard LWC with a `@api omniJsonData` property to receive OmniScript context.
2. Add a `connectedCallback` that reads the relevant field from `omniJsonData` to restore any previously selected value.
3. When the user selects a date, dispatch the value back to the OmniScript using the pubsub `fireEvent` pattern with the output field name matching the OmniScript configuration.
4. In the OmniScript designer, add a Custom LWC element step, provide the component API name, and configure input mapping (from OmniScript data to the LWC) and output mapping (from LWC event to OmniScript data).
5. Activate the OmniScript; the LWC renders inside the OmniScript step at runtime.

**Why not the alternative:** Using a standard LWC without the OmniScript pubsub integration means the date value is isolated in the LWC and the OmniScript data model never updates. Downstream Integration Procedure actions will see an empty date field.

### Pattern 3: Invoke Integration Procedure from LWC

**When to use:** An LWC needs to execute server-side data orchestration logic (multi-source aggregation, conditional callouts) that is already implemented as an Integration Procedure.

**How it works:**
1. Create an Apex class that takes the input map and calls the Integration Procedure by name via `omnistudio.IntegrationProcedureService.runIntegrationService` (native) or `vlocity_cmt.IntegrationProcedureService.runIntegrationService` (managed).
2. Expose the Apex method with `@AuraEnabled`.
3. Call the Apex method from LWC using `@wire` or imperatively using `import { callApexMethod }`.
4. Handle the returned output map in the LWC component logic.

**Why not the alternative:** Calling the Integration Procedure REST endpoint directly from LWC JavaScript (fetch/XMLHttpRequest) bypasses Apex sharing rules, exposes the endpoint to CSRF risks, and makes the component fail in stricter Lightning Security contexts.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to pre-populate OmniScript fields from record context | Pass serialized seed data via `omni-seed-json` before component mounts | Seed data set before DOM connection initializes the OmniScript data model correctly |
| User wants to launch OmniScript from a button click on a FlexCard action | Use FlexCard OmniScript Launch action type | FlexCard has native OmniScript launch support; no custom LWC needed |
| Server-side logic exists as Integration Procedure and LWC needs the result | Wrap in Apex with `@AuraEnabled` | Preserves sharing enforcement and avoids direct REST exposure |
| Custom UX control needed on OmniScript step | Custom LWC element registered in OmniScript designer | Allows bidirectional data exchange through pubsub and field mapping |
| Org uses native OmniStudio (enableOaForCore = true) | Use `omnistudio-omni-script` tag | Managed package tag `c-omni-script` is not resolved in native runtime |
| Org is on managed package (vlocity_cmt, vlocity_ins) | Use `c-omni-script` tag | Native tag is not registered in managed package runtime |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the OmniStudio runtime.** Check the org's `OmniStudioSettings` metadata or the Setup page to confirm whether native OmniStudio is active (`enableOaForCore = true`) or whether the org is running a managed package. Choose component tags accordingly.
2. **Determine the integration direction.** Decide whether you are embedding an OmniScript inside LWC, registering a custom LWC inside OmniScript, or calling an OmniScript/Integration Procedure from LWC. Each direction has a distinct implementation pattern.
3. **Design the data contract.** For embedding, define the seed data JSON structure that maps from the calling LWC's available data to the OmniScript's expected field hierarchy. For custom elements, define input and output field names that will be referenced in both the OmniScript designer and the LWC JavaScript.
4. **Implement the component.** Write the LWC using the correct namespace tags. For custom elements, implement `connectedCallback`, `disconnectedCallback`, and pubsub event dispatch. For embedding, wire the `omni-seed-json` attribute and attach a `complete` event listener.
5. **Configure the OmniScript.** For custom LWC elements, open the OmniScript designer, add the Custom LWC element type, enter the component API name, and set up input and output field mappings. Verify field name casing matches the LWC property names exactly.
6. **Test both directions.** Verify that seed data correctly pre-populates OmniScript fields, and that OmniScript output data is captured by the parent LWC on the `complete` event. For custom elements, verify that selecting a value in the LWC updates the OmniScript data model before navigating to the next step.
7. **Run the checker script.** Execute `python3 scripts/check_omnistudio_lwc.py --manifest-dir force-app/main/default` to detect mixed namespace usage in HTML and XML metadata files.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Component tag namespace matches the org's OmniStudio runtime (native vs managed package)
- [ ] Seed data JSON structure matches the OmniScript's expected field name hierarchy and nesting depth
- [ ] Custom LWC elements implement `connectedCallback` and `disconnectedCallback` per OmniStudio conventions
- [ ] Output variable names in OmniScript JSON configuration match LWC JavaScript property names exactly (case-sensitive)
- [ ] `complete` event listener is attached on the OmniScript component reference in the parent LWC
- [ ] Integration Procedure calls from LWC are routed through `@AuraEnabled` Apex, not direct REST
- [ ] Checker script passes with no mixed-namespace findings

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Mixed namespace tags cause silent render failure** — Using `omnistudio-omni-script` in a managed package org or `c-omni-script` in a native OmniStudio org results in the component not rendering. There is no console error in some runtime versions; the page simply renders blank where the OmniScript should appear. Always confirm the runtime before writing markup.
2. **Seed data set after DOM connection is ignored** — Setting the `omni-seed-json` attribute after the OmniScript component is already connected to the DOM does not re-initialize the script state. The seed data must be fully prepared and bound before the component mounts. In LWC, this means computing the seed JSON in the JavaScript and binding it as an expression in the template, not updating it imperatively in `connectedCallback`.
3. **Output field name case mismatch silently drops data** — OmniScript field mapping is case-sensitive. If the OmniScript designer configuration declares an output field as `selectedDate` and the LWC dispatches the value under `SelectedDate`, the OmniScript data model never captures it. Downstream steps referencing `selectedDate` evaluate as empty without any error.
4. **Wire adapters and `@salesforce/apex` do not behave as expected inside OmniScript custom elements** — The OmniScript runtime renders custom LWC elements in a context that does not always correctly resolve wire service subscriptions. Imperative Apex calls are the safe pattern inside custom elements. Wire-based data loading should be done in a wrapper LWC outside the OmniScript.
5. **Integration Procedure REST calls bypass sharing rules** — Calling the Integration Procedure REST endpoint directly from LWC JavaScript bypasses Apex sharing enforcement. The correct pattern is an `@AuraEnabled` Apex method that invokes the Integration Procedure service on the server side.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| LWC host component | Container LWC that embeds OmniScript with seed data wiring and complete event handling |
| Custom OmniScript LWC element | LWC implementing OmniStudio lifecycle conventions for use inside OmniScript screens |
| Apex Integration Procedure bridge | `@AuraEnabled` Apex class routing LWC calls to Integration Procedure service |
| Namespace audit results | Output of `check_omnistudio_lwc.py` identifying mixed-namespace issues |
| OmniScript element JSON config | Input/output field mapping JSON for the OmniScript designer custom element step |

---

## Related Skills

- `omnistudio/omniscript-design-patterns` — use when the structural design of the OmniScript itself (step count, branching, save/resume) is the primary concern, not the LWC integration layer
- `omnistudio/integration-procedures` — use when the focus is the server-side Integration Procedure design, not the LWC invocation pattern
- `omnistudio/flexcard-design-patterns` — use when the OmniScript launch should be triggered from a FlexCard action rather than an LWC button
- `lwc/custom-property-editor-for-flow` — use when the custom component context is Flow, not OmniScript
