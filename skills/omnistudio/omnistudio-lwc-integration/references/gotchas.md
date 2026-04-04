# Gotchas — OmniStudio LWC Integration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Native OmniStudio Uses `omnistudio-omni-script`; Managed Package Uses `c-omni-script` — Mixing Causes Silent Render Failures

**What happens:** The OmniScript component does not render. The containing LWC appears to load, but the area where the OmniScript should appear is blank or empty. No JavaScript console error is thrown in many runtime versions.

**When it occurs:** A developer copies markup from documentation or another project that uses a different OmniStudio runtime. For example, using `c-omni-script` in an org with native OmniStudio enabled (`enableOaForCore = true`), or using `omnistudio-omni-script` in a managed package org (vlocity_cmt, vlocity_ins, vlocity_ps). This also occurs during migrations from managed package to native OmniStudio when not all LWC files are updated.

**How to avoid:** Before writing any component tag, verify the org's runtime. Check Setup > OmniStudio Settings or inspect the `OmniStudioSettings` metadata record for `enableOaForCore`. Use the `check_omnistudio_lwc.py` script to scan for mixed namespace usage across the project's HTML and XML files.

---

## Gotcha 2: Custom LWC Elements Must Implement `connectedCallback`/`disconnectedCallback` for OmniScript Lifecycle

**What happens:** The custom LWC element renders but does not restore previously entered values when the user navigates back to the step, or it retains stale event listeners that fire after the step is unmounted. In some cases, the pubsub events fire into a destroyed component context and throw uncaught errors.

**When it occurs:** A developer builds a custom LWC element without implementing `connectedCallback` to restore state from `omniJsonData` and without implementing `disconnectedCallback` to clean up subscriptions. The OmniScript runtime destroys and recreates custom elements when the user navigates between steps.

**How to avoid:** Always implement `connectedCallback` to read the current value from `omniJsonData` and restore the component's internal state. Implement `disconnectedCallback` to remove any pubsub subscriptions or event listeners registered during `connectedCallback`. Treat the custom element as stateless at mount time — all state must come from `omniJsonData`.

---

## Gotcha 3: Output Variable Names in OmniScript JSON Must Match LWC Property Attribute Names Exactly (Case-Sensitive)

**What happens:** The user fills in the custom LWC element and navigates to the next step, but downstream steps that reference the output field see an empty value. No error appears in the OmniScript interface. The Integration Procedure or DataRaptor at the end of the script receives an empty or null value for the field.

**When it occurs:** The output field name declared in the OmniScript designer's custom element configuration uses a different capitalization than the key used in the `pubsub.fireEvent` call in the LWC. For example, the designer config declares `selectedDate` but the LWC fires `SelectedDate`.

**How to avoid:** Treat output field names as case-sensitive string literals. Write them down before implementing either side. Keep a single source of truth (the OmniScript designer configuration) and copy the exact string into the LWC `fireEvent` call. Use the checker script output and OmniScript debug mode (append `?debug=true` to the OmniScript preview URL) to inspect the data model in real time.

---

## Gotcha 4: Seed Data Must Be Set Before the OmniScript Component Connects to the DOM

**What happens:** OmniScript fields are not pre-populated despite the parent LWC having the correct record data. The OmniScript launches with all fields at default (empty) values.

**When it occurs:** The parent LWC computes the seed JSON asynchronously (e.g., in a `connectedCallback` after a wire call resolves) and attempts to set it on the OmniScript component reference imperatively after the component has already mounted. The OmniScript has already initialized its data model by that point and ignores the late assignment.

**How to avoid:** Bind the seed JSON as a reactive template expression (`omni-seed-json={seedJson}`) using a getter that derives from `@wire` data or `@api` properties. Do not use `connectedCallback` or `renderedCallback` to set seed data imperatively after mount. If the seed data requires an asynchronous fetch, use a conditional render (`if:true={isDataReady}`) to delay mounting the OmniScript component until the data is available.

---

## Gotcha 5: Wire Adapters Inside Custom OmniScript LWC Elements May Not Resolve Correctly

**What happens:** The `@wire` decorator in a custom LWC element never delivers data, or it delivers data only on the first render and not on subsequent step navigations. The component renders with empty fields that should be populated.

**When it occurs:** The OmniScript runtime renders custom elements in a context where the standard LWC wire service lifecycle may not align with the OmniScript step lifecycle. Components destroyed and recreated during step navigation may not have their wire subscriptions properly re-established.

**How to avoid:** Use imperative Apex calls (`import apexMethod from '@salesforce/apex/...'` called inside `connectedCallback`) rather than `@wire` inside custom OmniScript elements. Pull the needed record or data context from `omniJsonData` where possible, since the OmniScript runtime populates it with current script data at step render time. Reserve wire adapters for wrapper LWC components that exist outside the OmniScript boundary.

---

## Gotcha 6: `hide-nav-bar` and OmniScript Navigation Button Conflicts in Embedded Context

**What happens:** When an OmniScript is embedded in an LWC on a record page, the standard OmniScript "Previous" and "Next" navigation buttons conflict with the host page's own navigation or appear duplicated if the parent LWC also renders nav controls.

**When it occurs:** The parent LWC does not specify `hide-nav-bar="true"` and also renders its own navigation buttons that call into the OmniScript. Both sets of buttons are rendered, leading to duplicate controls or conflicting state transitions.

**How to avoid:** Decide up front whether the OmniScript's built-in navigation bar or the parent LWC's navigation controls should drive step progression. If the parent LWC controls navigation, set `hide-nav-bar="true"` on the OmniScript component. If the OmniScript's built-in nav is used, remove any duplicate controls from the parent LWC.
