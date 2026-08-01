# Well-Architected Notes — Flow Reactive Screen Components

**User Experience:** reactivity removes the navigate-to-see-the-result round trip, which
is the main reason screen flows feel slower than a purpose-built page. The cost is that
formulas are now evaluated against half-entered screens, a state a non-reactive screen
never had to handle — so every reactive formula needs a defined result for null and
partial input.

**Reliability:** the failure mode is silence. Referencing a screen's stored output instead
of the component, or omitting the `FlowAttributeChangeEvent` dispatch in a custom
component, produces a flow that saves, activates and runs while quietly showing a stale
value. Both are valid constructions that no validation catches, so they have to be caught
by review and by testing on a real device rather than in the builder's preview.

## Official Sources Used

- Flow screen component reference — which attributes support reactive values — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_screencmp.htm
- Build reactive screens in Flow Builder — referencing a component's attribute rather than the screen's output — https://help.salesforce.com/s/articleView?id=platform.flow_build_screen_reactive.htm
- lightning/flowSupport module — FlowAttributeChangeEvent and FlowNavigationNextEvent — https://developer.salesforce.com/docs/component-library/bundle/lightning-flow-support/documentation
- Configure a Lightning Web Component for Flow Screens — targetConfig, role="inputAndOutput" and the validate() contract — https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-screens.html
- LightningComponentBundle metadata — targets, targetConfigs and property roles — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_lightningcomponentbundle.htm
