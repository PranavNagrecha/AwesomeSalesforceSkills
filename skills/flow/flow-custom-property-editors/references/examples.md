# Examples — Flow Custom Property Editors

## Example 1: Screen Component With Guided Object Configuration

**Context:** A screen component lets admins pick an object API name, a field set, and a display mode for a reusable lookup widget.

**Problem:** The default property pane exposes three free-text fields, which leads to typos and invalid combinations.

**Solution:**

```xml
<targetConfigs>
    <targetConfig targets="lightning__FlowScreen" configurationEditor="c:lookupFlowEditor">
        <property name="objectApiName" type="String" />
        <property name="fieldSetName" type="String" />
        <property name="displayMode" type="String" />
    </targetConfig>
</targetConfigs>
```

**Why it works:** The editor gives admins a controlled design-time experience while the runtime screen component still receives the same three well-defined values.

---

## Example 2: Generic SObject Action Editor

**Context:** A Flow action needs admins to map a generic input object and select which record variable to pass.

**Problem:** Free-form configuration creates incompatible inputs across Flows.

**Solution:**

```js
this.dispatchEvent(
    new CustomEvent('configuration_editor_input_value_changed', {
        detail: {
            name: 'recordVariableName',
            newValue: selectedValue,
            newValueDataType: 'String'
        }
    })
);
```

**Why it works:** The builder contract stays explicit, and the editor can validate the selected variable before Flow admins save the configuration.

---

## Anti-Pattern: Builder UI That No Longer Matches Runtime Inputs

**What practitioners do:** They rename runtime component properties but leave the custom editor and metadata definitions untouched.

**What goes wrong:** Flow admins keep configuring values that the runtime component no longer reads, and failures surface only after the Flow is executed.

**Correct approach:** Version the design-time and runtime contract together. Treat `.js-meta.xml`, the custom editor, and the runtime component API as one unit.
