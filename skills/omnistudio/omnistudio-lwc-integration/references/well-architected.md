# Well-Architected Notes — OmniStudio LWC Integration

## Relevant Pillars

- **User Experience** — The primary pillar for this skill. Embedding OmniScripts in LWC and registering custom LWC elements are fundamentally user experience decisions. OmniScript provides guided, multi-step journey UX that LWC alone does not replicate efficiently. The integration layer must not degrade the guided experience by introducing blank renders, lost data on back-navigation, or mismatched seed data.
- **Scalability** — Relevant when Integration Procedures are called from LWC. Routing Integration Procedure calls through `@AuraEnabled` Apex preserves governor limit controls and Apex transaction scoping. Direct REST calls from LWC bypass those boundaries and create unpredictable scaling behavior under concurrent load.
- **Reliability** — Custom LWC elements that do not implement `connectedCallback`/`disconnectedCallback` correctly introduce reliability gaps: state is not restored on back navigation, events may fire into destroyed component contexts, and output values may silently fail to be captured. The integration contract (field name casing, seed data timing, namespace selection) must be correct for the component to behave consistently.
- **Operational Excellence** — Namespace management is an operational concern. Orgs that have migrated from managed package to native OmniStudio must audit all LWC metadata for stale `c-omni-script` tags. The checker script (`check_omnistudio_lwc.py`) operationalizes this audit and can be added to a CI pipeline.

## Architectural Tradeoffs

- **Embedded OmniScript vs standalone Lightning page:** Embedding an OmniScript in an LWC on a record page keeps context in one place (the agent does not leave the record) but adds a wrapper LWC layer to maintain. If the guided experience stands alone and doesn't need record-page context, a standalone Lightning app page with the OmniScript placed directly is simpler.
- **Custom LWC element vs built-in OmniScript element:** Every custom LWC element inside an OmniScript increases the operational surface area (separate deployment, separate testing, separate failure modes). Use built-in OmniScript elements where they cover the UX requirement. Reserve custom LWC elements for genuine gaps — custom validation logic, third-party widget integration, or non-standard input controls.
- **Integration Procedure via Apex vs direct REST:** The Apex bridge introduces an additional layer but preserves sharing enforcement, governor limits, and testability. The REST approach is faster to implement but is not recommended for production workloads where field-level security and record visibility matter.

## Anti-Patterns

1. **Using `c-omni-script` in a native OmniStudio org** — The managed package component tag is not registered in the native runtime and causes silent render failures. Confirm the runtime before writing markup; use the checker script to catch stale tags in the codebase.
2. **Setting seed data imperatively after component mount** — The OmniScript initializes its data model at connection time. Post-mount seed injection is ignored. Bind seed data reactively as a template expression so it is evaluated before the child component connects to the DOM.
3. **Building stateful wire-dependent custom LWC elements for OmniScript screens** — Wire adapters may not re-resolve correctly across OmniScript step navigations. Use imperative Apex calls and derive state from `omniJsonData` to maintain reliability across step transitions.

## Official Sources Used

- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm
  Used for: OmniScript component attributes, custom element configuration, seedDataJSON behavior, namespace details, `enableOaForCore` setting
- OmniStudio Help — OmniScript Custom LWC Elements — https://help.salesforce.com/s/articleView?id=sf.os_omniscript_custom_lwc.htm&type=5
  Used for: custom element registration, input/output field mapping, pubsub event pattern
- OmniStudio Help — Integration Procedures — https://help.salesforce.com/s/articleView?id=sf.os_integration_procedures.htm&type=5
  Used for: Integration Procedure invocation from LWC context, service API patterns
- Salesforce Well-Architected Framework — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
  Used for: User Experience and Scalability pillar framing, anti-pattern identification
- LWC Best Practices for Development — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
  Used for: LWC lifecycle conventions, wire vs imperative call guidance
- Industries Common Resources — Salesforce Industries Developer Guide (local import: `knowledge/imports/salesforce-industries-dev-guide.md`)
  Used for: `seedDataJSON` property confirmation, `isOmniScriptEmbeddable` metadata field, `enableOaForCore` managed package namespace requirements
