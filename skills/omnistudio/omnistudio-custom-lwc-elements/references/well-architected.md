# Well-Architected Notes — OmniStudio Custom LWC Elements

## Relevant Pillars

- **User Experience** — This skill is primarily User Experience-driven. Custom LWC elements exist specifically to overcome UX limitations of standard OmniScript elements. The quality of the result depends on how well the lifecycle hooks and pubsub integration preserve user state across navigation, and how reliably custom validation surfaces actionable error messages.
- **Reliability** — Reliability is the second critical pillar. Custom elements introduce additional failure modes: pubsub namespace mismatches, output field name mismatches, and accumulated validation listeners are all production-grade reliability risks that can silently degrade the OmniScript experience without triggering visible errors. The checker script and review checklist are the primary reliability controls.
- **Security** — Security applies at the Apex layer, not the LWC element layer directly. If the custom element calls Apex to load data, those Apex methods must enforce `with sharing` and CRUD/FLS. The OmniScript runtime does not inject sharing enforcement into custom element Apex calls.
- **Operational Excellence** — Custom elements increase the operational surface area of an OmniScript. When a deployed OmniScript breaks, diagnosing whether the failure is in the OmniScript configuration, the LWC element code, or the pubsub channel requires specific knowledge of this integration pattern. Keeping custom elements focused (one concern per element) and using the checker script reduces debugging time.

## Architectural Tradeoffs

**Custom element vs standard element extension:** Standard OmniScript elements support formula-based conditional display, built-in validation flags, and accessibility handling. Custom LWC elements replace all of these with code the team must maintain. Before choosing a custom element, verify that the standard element's built-in customization points (custom formula, visibility rules, CSS class overrides at the step level) cannot satisfy the requirement.

**Validation in LWC vs validation in OmniScript formula element:** OmniScript provides built-in formula-based validation that does not require a custom LWC. A custom LWC validation via `omniscriptvalidate` pubsub is appropriate only when the validation logic requires JavaScript execution (async data lookups, complex date math, client-side business rules) that cannot be expressed as an OmniScript formula. Over-using LWC validation when a formula would work adds unnecessary complexity.

**Single-element focus vs multi-element LWC:** A custom LWC element should cover one logical step interaction. Combining multiple step concerns into a single large LWC (because it seems more efficient) makes the OmniScript harder to restructure, harder to debug, and harder to test. Prefer smaller, focused elements that align with OmniScript step boundaries.

## Anti-Patterns

1. **Treating `omniJsonData` as a reactive two-way binding** — Mutating `omniJsonData` directly in the LWC and expecting the OmniScript to reflect the change inverts the communication contract. The correct flow is always: OmniScript pushes data to LWC via `omniJsonData` on step render; LWC pushes data to OmniScript via `omniupdatebyfield` pubsub event. Direct mutation of `omniJsonData` is ignored by the runtime and creates local state inconsistencies.

2. **Skipping `disconnectedCallback` cleanup** — Registering pubsub listeners in `connectedCallback` without the corresponding `unregisterListener` call in `disconnectedCallback` is the most common source of unreproducible validation bugs. It violates the Reliability pillar and makes the component non-idempotent across navigation cycles.

3. **Building overly large custom elements that replicate OmniScript step logic** — A custom LWC that contains multi-step branching logic, local storage of transient state, and complex server orchestration effectively rebuilds an OmniScript inside an OmniScript step. This anti-pattern defeats the purpose of OmniScript's declarative runtime and makes the solution unmaintainable. If the business process is complex enough to require this, the OmniScript structure should be redesigned instead.

## Official Sources Used

- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm
  Used for: Custom LWC element lifecycle conventions, `omniJsonData`/`omniOutputMap` property semantics, pubsub event keys (`omniupdatebyfield`, `omnimerge`, `omniscriptvalidate`, `omnivalidate`), OmniStudio runtime detection
- OmniStudio Help — https://help.salesforce.com/s/articleView?id=sf.os_omniscript.htm&type=5
  Used for: Custom element configuration in the OmniScript designer (component name, input/output field mapping), Custom Merge Map element type
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
  Used for: User Experience and Reliability pillar framing, operational surface area tradeoffs
- Best Practices for Development with Lightning Web Components — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
  Used for: LWC lifecycle conventions (`connectedCallback`, `disconnectedCallback`), `@api` property semantics, imperative vs wire-based data access guidance
