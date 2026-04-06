# Gotchas — OmniStudio Custom LWC Elements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Wrong Pubsub Import Path Causes Silent Data Model Failure

**What happens:** The custom LWC element renders correctly inside the OmniScript step. The user interacts with it and selects values. But when the user advances to the next step, all downstream fields that depend on the custom element's output are empty. No JavaScript error appears in the browser console.

**When it occurs:** This happens when the pubsub module is imported from the wrong namespace — `omnistudio/pubsub` in a managed package org, or `vlocity_cmt/pubsub` in a native OmniStudio org. In some org configurations the incorrect import resolves to a stub module rather than failing at deploy, making the LWC appear functional but disconnected from the OmniScript event bus.

**How to avoid:** Before writing any pubsub code, confirm the runtime by checking `OmniStudioSettings` metadata (`enableOaForCore` attribute) or the Setup > OmniStudio page. Use `omnistudio/pubsub` for native and `vlocity_cmt/pubsub` for managed package. Run the checker script after authoring to catch the mismatch before deployment.

---

## Gotcha 2: Output Field Name Case Mismatch Silently Drops Data

**What happens:** The LWC fires `omniupdatebyfield` and execution completes without error. But the OmniScript data model never reflects the value. Downstream steps that read the field evaluate it as empty or undefined, and dependent Integration Procedure actions receive a null input.

**When it occurs:** This occurs when the key name in the `omniupdatebyfield` event payload does not match the output field name declared in the OmniScript designer custom element step configuration exactly, including case. For example, the OmniScript designer declares `SelectedDate` but the LWC fires `{ selectedDate: value }`.

**How to avoid:** Write down the exact field names (with casing) in the field contract before building either the LWC or the OmniScript configuration. Treat output field names as constants in the LWC code rather than string literals that can drift. The checker script flags cases where `omniupdatebyfield` keys contain mixed casing that commonly indicates a mismatch.

---

## Gotcha 3: Validation Listener Accumulates on Repeated Step Navigation

**What happens:** Custom validation starts behaving erratically — the OmniScript fires `omnivalidate` multiple times per navigation attempt, causing validation to pass then fail in the same event cycle. In some cases, the OmniScript navigation hangs entirely.

**When it occurs:** This occurs when `pubsub.registerListener('omniscriptvalidate', handler, this)` is called in `connectedCallback` but the matching `pubsub.unregisterListener('omniscriptvalidate', handler, this)` is not called in `disconnectedCallback`. Every time the user navigates to and from the step, a new listener is added. After three navigations, there are three active listeners, and the OmniScript receives three `omnivalidate` responses per navigation event.

**How to avoid:** Always implement both `connectedCallback` (register) and `disconnectedCallback` (unregister) as a pair. Never register a pubsub listener without its corresponding cleanup.

---

## Gotcha 4: `omniJsonData` Does Not Update Reactively During a Step

**What happens:** The LWC initializes from `omniJsonData` in `connectedCallback`, but if another element on the same OmniScript step updates the data model (via a formula element or conditional logic), the LWC does not re-render with the new value. The LWC continues to display the stale value from the initial render.

**When it occurs:** This occurs when practitioners expect `@api omniJsonData` to behave like a reactive `@track` property that triggers re-renders when the OmniScript updates the data model. `omniJsonData` is set once by the OmniScript runtime when the step renders. It does not update reactively.

**How to avoid:** If the LWC must respond to data model changes from other elements on the same step, subscribe to the appropriate OmniScript pubsub change event. For most use cases, relying on `connectedCallback` initialization and `omniupdatebyfield` output is sufficient. If cross-element reactivity is required, document it as an explicit requirement and design the OmniScript step structure to minimize cross-element dependencies.

---

## Gotcha 5: Component API Name Resolution Differs Between Native and Managed Package

**What happens:** After configuring the custom element step in the OmniScript designer with the component API name, the step renders blank at runtime. No error appears. The OmniScript simply skips the custom element rendering and shows an empty step body.

**When it occurs:** In native OmniStudio orgs, the component API name in the OmniScript designer should use the org's namespace prefix or `c/` (for the default namespace). In managed package orgs, the namespace may differ. A mismatch between the entered component name and the actual deployed namespace causes the OmniScript runtime to silently fail to resolve the component.

**How to avoid:** Verify the deployed component namespace before entering the API name in the OmniScript designer. Use Developer Console or Workbench to confirm the exact namespace prefix of the LWC. If the org has a custom namespace (e.g., `myorg`), the designer entry should be `myorg/componentName`, not `c/componentName`.

---

## Gotcha 6: Custom Merge Map Elements Require `omnimerge`, Not `omniupdatebyfield`

**What happens:** The LWC fires `omniupdatebyfield` with a nested object value. The OmniScript receives the event but stores the entire nested object as a serialized string (or drops it entirely) rather than merging it at the configured path. Downstream elements that reference nested paths within the merged object evaluate as empty.

**When it occurs:** When the element type in the OmniScript designer is configured as a Custom Merge Map Element but the LWC code fires the `omniupdatebyfield` event instead of `omnimerge`. The two element types use different event keys and have different merge semantics.

**How to avoid:** For Custom LWC Element type: use `omniupdatebyfield` for scalar or flat key-value output. For Custom Merge Map Element type: use `omnimerge` with the object payload matching the configured merge path key. The element type and the event key must be consistent.
