# LLM Anti-Patterns — Custom Property Editor for Flow

Common mistakes AI coding assistants make when generating or advising on LWC Custom Property Editors for Flow Builder.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating inputVariables as a simple key-value map

**What the LLM generates:**

```javascript
// Wrong: treating inputVariables as an object
get recordId() {
    return this.inputVariables.recordId;
}
```

**Why it happens:** LLMs model `inputVariables` as a flat object because that is how most JavaScript config objects work. In reality, `inputVariables` is an array of `{ name, value, dataType }` objects.

**Correct pattern:**

```javascript
@api inputVariables;

get recordId() {
    const param = this.inputVariables.find(v => v.name === 'recordId');
    return param ? param.value : undefined;
}
```

**Detection hint:** `this.inputVariables.` followed by a direct property name that is not `find`, `filter`, `map`, or array methods.

---

## Anti-Pattern 2: Forgetting to fire configuration_editor_input_value_changed on every change

**What the LLM generates:**

```javascript
handleChange(event) {
    this.selectedValue = event.detail.value;
    // Missing: does not notify Flow Builder of the change
}
```

**Why it happens:** In normal LWC development, local state changes are sufficient. LLMs forget that in a property editor context, Flow Builder is the consumer and must be explicitly notified via the custom event.

**Correct pattern:**

```javascript
handleChange(event) {
    this.selectedValue = event.detail.value;
    this.dispatchEvent(new CustomEvent('configuration_editor_input_value_changed', {
        bubbles: true,
        cancelable: false,
        composed: true,
        detail: {
            name: 'selectedValue',
            newValue: event.detail.value,
            newValueDataType: 'String'
        }
    }));
}
```

**Detection hint:** Handler methods that update local state without dispatching `configuration_editor_input_value_changed`.

---

## Anti-Pattern 3: Using the wrong event name or missing required event properties

**What the LLM generates:**

```javascript
this.dispatchEvent(new CustomEvent('valuechange', {
    detail: { name: 'myProp', newValue: val }
}));
```

**Why it happens:** LLMs substitute generic event names or omit `bubbles: true` and `composed: true`, which are required for the event to reach Flow Builder across the shadow boundary.

**Correct pattern:**

```javascript
this.dispatchEvent(new CustomEvent('configuration_editor_input_value_changed', {
    bubbles: true,
    cancelable: false,
    composed: true,
    detail: {
        name: 'myProp',
        newValue: val,
        newValueDataType: 'String'
    }
}));
```

**Detection hint:** Regex for `CustomEvent\(` in a property editor file where the event name is not exactly `configuration_editor_input_value_changed`.

---

## Anti-Pattern 4: Not implementing the validate() method for builder-time validation

**What the LLM generates:**

```javascript
// Property editor with no validate() method — Flow Builder cannot block save
export default class MyEditor extends LightningElement {
    @api inputVariables;
    @api builderContext;
    // ... handlers only
}
```

**Why it happens:** The `validate()` method is a lesser-known part of the property editor contract. Most training examples focus on eventing and skip validation entirely.

**Correct pattern:**

```javascript
@api
validate() {
    const param = this.inputVariables.find(v => v.name === 'requiredField');
    if (!param || !param.value) {
        return {
            isValid: false,
            errorMessage: 'Required Field must be configured.'
        };
    }
    return { isValid: true };
}
```

**Detection hint:** Property editor class with `@api inputVariables` but no `validate()` method.

---

## Anti-Pattern 5: Confusing the property editor component with the runtime screen component

**What the LLM generates:**

```xml
<!-- js-meta.xml for the runtime component -->
<LightningComponentBundle>
    <targetConfigs>
        <targetConfig targets="lightning__FlowScreen">
            <property name="label" type="String"/>
            <configurationEditor>c-my-runtime-component</configurationEditor>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

**Why it happens:** LLMs conflate the two components because the property editor is conceptually related. They sometimes reference the runtime component as its own editor, or place runtime logic inside the editor.

**Correct pattern:**

The `configurationEditor` must reference a separate, dedicated LWC component built specifically for the builder context:

```xml
<configurationEditor>c-my-property-editor</configurationEditor>
```

The editor component receives `inputVariables` and `builderContext`. The runtime component receives the actual `@api` properties set by the admin.

**Detection hint:** `configurationEditor` value that matches the parent component's own name, or editor component files that import runtime-only modules like `lightning/navigation`.

---

## Anti-Pattern 6: Ignoring builderContext for context-aware configuration

**What the LLM generates:**

```javascript
// Editor ignores builderContext entirely
@api inputVariables;
// No @api builderContext;
```

**Why it happens:** Many training examples omit `builderContext` because it is optional. But when the editor needs to know the Flow's available variables, record context, or action type, `builderContext` is essential.

**Correct pattern:**

```javascript
@api inputVariables;
@api builderContext;

get availableVariables() {
    return this.builderContext?.variables || [];
}
```

**Detection hint:** Property editor that builds dynamic picklists or variable references but does not declare `@api builderContext`.
