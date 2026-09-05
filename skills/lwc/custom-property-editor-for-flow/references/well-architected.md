# Well-Architected Notes - Custom Property Editor For Flow

## Relevant Pillars

- **User Experience** - the whole point of a custom editor is a clearer, safer builder experience.
- **Operational Excellence** - reusable components and clear contracts reduce admin support burden.

## Architectural Tradeoffs

| Choice | You gain | You pay |
|---|---|---|
| Default property pane vs custom editor | zero code, zero maintenance, no packaging surface | text boxes and combo boxes for every input (lwc_guide L9037–9039) |
| Custom editor | labels, sliders, filtered pickers, and a save-blocking `validate()` | a second LWC bundle with its own lifecycle, tests, and `isExposed` decision |
| Rich `builderContext`-driven UI | the editor offers only resources that exist in this flow | a null-guard burden and a dependency on undocumented context shape |
| Generic sObject (`{T}` / `T__`) inputs | one component serves every object | two spellings of `typeName`, and screen-component persistence the Metadata API guide does not document (api_meta L71632) |
| Sharing one editor across a screen component and an action | one bundle to maintain | branching on `elementInfo.type` for every generic-type read and write (lwc_guide L9729–9733) |

## Where The Complexity Actually Lands

A custom property editor moves work from the admin to the developer permanently. The
`validate()` contract in particular is a design-time gate: it blocks the admin from clicking
**Done**, which is exactly the behaviour you want for a required object mapping and exactly
the behaviour that makes a buggy editor unfixable from Setup. Budget for the editor being
deployed and tested on the same cadence as the component it configures — a runtime component
can be hotfixed without its editor, but an editor that rejects valid configuration blocks
every admin in the org from editing that screen.

## Anti-Patterns

1. **Custom editor for a trivial case** - complexity without value.
2. **Broken metadata hookup** - editor exists but never runs.
3. **Visual editor with no value-change event** - looks finished, behaves incorrectly.
4. **`validate()` returning a boolean or an `{ isValid }` object** - Flow Builder expects an array of `{ key, errorString }`, so nothing is blocked and nothing is reported.
5. **A CPE bundle with page targets** - a custom property editor is not a page component; the guide's CPE configuration files carry `apiVersion` and `isExposed` only.

## Official Sources Used

- Lightning Web Components Developer Guide, *Custom Property Editor JavaScript Interface* — https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-custom-property-editor-interface.html (the `inputVariables` / `builderContext` / `elementInfo` / `genericTypeMappings` / `validate` contract; the three event names and their `detail` keys; `bubbles` and `composed` must be true — lwc_guide L9672–9762)
- Lightning Web Components Developer Guide, *Example: Custom Property Editor for a Screen Component* — https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-custom-property-editor-lwc-example.html (`configurationEditor` as a `targetConfig` attribute; `validate()` returning `{ key, errorString }` with `setCustomValidity` / `reportValidity`; the CPE bundle's `apiVersion` + `isExposed`-only configuration file — lwc_guide L9177–9245)
- Lightning Web Components Developer Guide, *Example: Custom Property Editor for an Invocable Action* — https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-custom-property-editor-action-example.html (registration through the `configurationEditor` modifier rather than XML; the `c` namespace rule — lwc_guide L9041–9176)
- Lightning Web Components Developer Guide, *Example: Generic SObject Input for Invocable Actions* and *for Screen Components* — https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-custom-property-editor-sobject-action-example.html (the `T__` / `U__` prefixes for actions versus the bare `propertyType` name for screen components; `builderContext.variables` as the source of resource options — lwc_guide L9246–9480)
- Lightning Web Components Developer Guide, *lightning__FlowScreen Target* and *lightning__FlowAction Target* — https://developer.salesforce.com/docs/platform/lwc/guide/targets-lightning-flow-screen.html (the `configurationEditor` attribute row; `role="outputOnly"` hiding a property from the custom property editor; the `propertyType` `name` / `extends` attributes — lwc_guide L19059–19180)
- Lightning Web Components Developer Guide, *Write Jest Tests* — https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-jest-create-tests.html (`createElement`, the `__tests__` folder, the `afterEach` DOM reset, `shadowRoot` as the test-only query root — lwc_guide L12322–12365)
- Metadata API Developer Guide (v62 / Summer '26 PDF) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`FlowActionCall.dataTypeMappings` available in API 48.0 and later, api_meta L68470–68472; `FlowDataTypeMapping.typeName` requiring the `T__` / `U__` prefixes, L70177–70199; `FlowScreenField.dataTypeMappings` marked "Reserved for future use", L71632; `LightningComponentBundle` package.xml and bundle layout, L84110–84165)
- Apex Developer Guide (v62 / Summer '26 PDF) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf (`configurationEditor` in the `@InvocableMethod` "Supported Modifiers" list, and the statement that Flow Builder falls back to the standard property editor when it is omitted — apexdev L5413–5414)
- Lightning Web Components Developer Guide, *XML Configuration File Elements* — https://developer.salesforce.com/docs/platform/lwc/guide/reference-configuration-tags.html (every component must specify `apiVersion` from Spring '25 — lwc_guide L18699)
