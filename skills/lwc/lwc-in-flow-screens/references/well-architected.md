# Well-Architected Notes — LWC in Flow Screens

## Relevant Pillars

### User Experience

The primary architectural concern for LWC flow screen components is user experience. The component must integrate cleanly with Flow's navigation and validation cycle — blocking navigation on invalid input, providing useful error messages, and keeping output variables current so downstream screens and decisions behave predictably. A component that silently drops output values or ignores the `validate()` contract creates confusing, unpredictable flows for end users.

Key UX commitments:
- Fire `FlowAttributeChangeEvent` eagerly (on each change, not only on "Save") so the user never gets ahead of the data.
- Use `validate()` to surface errors at the right moment — when the user attempts to navigate — rather than hiding errors until a later screen.
- Always provide a meaningful `errorMessage` when `isValid` is false.

### Reliability

Reliability concerns center on the correctness of data written back to Flow variables and the determinism of validation behavior.

- Direct `@api` mutation creates unreliable output — it works locally but fails at runtime.
- Derived outputs must be re-fired in `connectedCallback` to survive back-navigation without data loss.
- Racing `FlowAttributeChangeEvent` with `FlowNavigationXxxEvent` in the same synchronous call introduces non-deterministic behavior.
- Navigation event guards (`availableActions` check) prevent silent no-ops that are hard to diagnose in production.

### Performance

Screen components are part of the Flow screen rendering cycle. Keep them lightweight:
- Avoid unnecessary Apex calls inside the component for data that can be passed in as Flow input variables.
- Prefer Lightning Data Service wire adapters over imperative Apex for record reads where caching is appropriate.
- Do not block `connectedCallback` with synchronous heavy computation.

---

## Architectural Tradeoffs

**Standard screen components vs. custom LWC screen components:** Standard Flow screen components cover many input patterns without code. A custom LWC is justified only when the interaction model, composite validation behavior, or domain-specific UX cannot be expressed with standard components. Every custom component is a maintenance commitment. ([Salesforce LWC Best Practices](https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html))

**Single-purpose vs. multi-purpose components:** A component that is tightly scoped to one flow use case is easier to reason about but cannot be reused. A more generic component (e.g. a reusable date-range picker) requires the `availableActions` guard and careful handling of `connectedCallback` re-firing, but pays dividends when the pattern appears in multiple flows.

**Validation inside the component vs. Apex-backed validation:** The `validate()` method is synchronous. Complex server-side validation (e.g. duplicate checking) cannot be done inside `validate()`. For async validation, perform the check in a user-interaction handler before navigation is attempted and surface results in the component's own UI.

---

## Anti-Patterns

1. **Mutating `@api` output properties directly** — `this.outputProp = value` does not communicate the change to Flow. The pattern appears correct in unit tests but fails at runtime because the Flow runtime is the legitimate owner of `@api` properties and does not observe writes from within the component. Use `FlowAttributeChangeEvent` instead.

2. **Omitting `connectedCallback` re-emission for derived outputs** — Derived outputs that are only emitted in event handlers will be lost when the user navigates back to the screen. The component remounts on each revisit, and without `connectedCallback` emission, the Flow variable starts blank again. This causes downstream decisions and screens to behave inconsistently depending on the user's navigation path.

3. **Implementing validation under a non-standard method name** — Methods named `validateForm`, `validateInput`, or any variant are never called by the Flow runtime. The user can navigate forward regardless of component state, defeating the validation contract entirely.

---

## Official Sources Used

- Configure a Component for Flow Screens — https://developer.salesforce.com/docs/platform/lwc/guide/use-config-for-flow-screens.html
- Set Up Your Screen Flow Components for Reactivity — https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-screen-reactivity.html
- Best Practices for Reactivity in Screen Flows — https://developer.salesforce.com/docs/platform/lwc/guide/use-best-practices-reactivity.html
- Validate Flow User Input — https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-validate-user-input-for-custom-components.html
- Validation Methods for Screen Components — https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-validate-external-internal-methods.html
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- lightning-flow-support component reference — https://developer.salesforce.com/docs/component-library/bundle/lightning-flow-support
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
