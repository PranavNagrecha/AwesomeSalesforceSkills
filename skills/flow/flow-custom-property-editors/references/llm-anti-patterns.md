# LLM Anti-Patterns — Flow Custom Property Editors

Common mistakes AI coding assistants make when generating or advising on Flow custom property editors.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating inputVariables as a flat object instead of an array

**What the LLM generates:**

```javascript
get objectApiName() {
    return this.inputVariables.objectApiName;
}
```

**Why it happens:** LLMs model configuration properties as key-value objects. The `inputVariables` API provides an array of `{ name, value, dataType }` objects that must be searched.

**Correct pattern:**

```javascript
@api inputVariables;

get objectApiName() {
    const variable = this.inputVariables.find(v => v.name === 'objectApiName');
    return variable ? variable.value : undefined;
}
```

**Detection hint:** Direct property access on `this.inputVariables` that is not an array method (`find`, `filter`, `map`).

---

## Anti-Pattern 2: Forgetting to dispatch configuration_editor_input_value_changed

**What the LLM generates:**

```javascript
handleObjectChange(event) {
    this._objectApiName = event.detail.value;
    // Flow Builder never receives the update
}
```

**Why it happens:** In standard LWC, setting local state is sufficient. Property editors must explicitly notify Flow Builder of every change via the specific custom event.

**Correct pattern:**

```javascript
handleObjectChange(event) {
    this._objectApiName = event.detail.value;
    this.dispatchEvent(new CustomEvent('configuration_editor_input_value_changed', {
        bubbles: true,
        cancelable: false,
        composed: true,
        detail: {
            name: 'objectApiName',
            newValue: event.detail.value,
            newValueDataType: 'String'
        }
    }));
}
```

**Detection hint:** Handler methods in a property editor that update local state without dispatching `configuration_editor_input_value_changed`.

---

## Anti-Pattern 3: Using the wrong event name

**What the LLM generates:**

```javascript
this.dispatchEvent(new CustomEvent('configurationchange', {
    detail: { name: 'myField', newValue: val }
}));
```

**Why it happens:** LLMs invent event names that sound reasonable. The exact event name must be `configuration_editor_input_value_changed` with underscores, and it must include `bubbles: true` and `composed: true`.

**Correct pattern:**

```javascript
this.dispatchEvent(new CustomEvent('configuration_editor_input_value_changed', {
    bubbles: true,
    cancelable: false,
    composed: true,
    detail: {
        name: 'myField',
        newValue: val,
        newValueDataType: 'String'
    }
}));
```

**Detection hint:** Any `CustomEvent` in a property editor file whose name is not exactly `configuration_editor_input_value_changed`.

---

## Anti-Pattern 4: Not implementing the validate() method

**What the LLM generates:**

```javascript
export default class MyPropertyEditor extends LightningElement {
    @api inputVariables;
    @api builderContext;
    // No validate method — Flow Builder cannot prevent saving invalid config
}
```

**Why it happens:** `validate()` is an optional part of the property editor contract that most training examples skip. Without it, admins can save incomplete or invalid configuration.

**Correct pattern:**

```javascript
@api
validate() {
    const objectVar = this.inputVariables.find(v => v.name === 'objectApiName');
    if (!objectVar || !objectVar.value) {
        return {
            isValid: false,
            errorMessage: 'Object API Name is required.'
        };
    }
    return { isValid: true };
}
```

**Detection hint:** Property editor class with `@api inputVariables` but no `validate()` method.

---

## Anti-Pattern 5: Confusing the property editor with the runtime screen component

**What the LLM generates:**

```javascript
// Property editor file imports runtime modules
import { NavigationMixin } from 'lightning/navigation';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
```

**Why it happens:** LLMs do not clearly separate the builder-time editor from the runtime component. The property editor runs inside Flow Builder, not in the runtime, so navigation, toasts, and data operations are inappropriate.

**Correct pattern:**

The property editor should only:
- Read `@api inputVariables` and `@api builderContext`
- Render configuration UI
- Dispatch `configuration_editor_input_value_changed` events
- Implement `validate()`

No runtime behavior belongs in the editor.

**Detection hint:** Property editor importing `lightning/navigation`, `lightning/platformShowToastEvent`, or `@salesforce/apex/*`.

---

## Anti-Pattern 6: Not using builderContext when building dynamic configuration options

**What the LLM generates:**

```javascript
// Hardcodes available options instead of reading from builderContext
options = [
    { label: 'Account', value: 'Account' },
    { label: 'Contact', value: 'Contact' }
];
```

**Why it happens:** LLMs hardcode options because they do not know the org's schema. `builderContext` provides information about the Flow's available variables, record context, and API version.

**Correct pattern:**

```javascript
@api builderContext;

get flowVariables() {
    return (this.builderContext?.variables || []).map(v => ({
        label: v.name,
        value: v.name
    }));
}
```

**Detection hint:** Property editor with hardcoded picklist options that should be dynamically derived from Flow context.
