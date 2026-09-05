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
    const validity = [];
    const param = this.inputVariables.find((v) => v.name === 'requiredField');
    if (!param || !param.value) {
        const cmp = this.template.querySelector('[data-id="requiredField"]');
        if (cmp) {
            cmp.setCustomValidity('Required Field must be configured.');
            cmp.reportValidity();
        }
        validity.push({
            key: 'RequiredField',
            errorString: 'Required Field must be configured.'
        });
    }
    return validity;
}
```

`validate()` returns an **array of `{ key, errorString }`** objects — empty array for valid.
An `{ isValid, errorMessage }` object, a boolean, or a `{ message, severity }` object is not
the documented contract, and Flow Builder will not block the save (lwc_guide
`use-flow-custom-property-editor-interface` L9731–9735; worked examples L9091–9099,
L9231–9238). Flow Builder renders only the error **count**; call `setCustomValidity()` and
`reportValidity()` yourself to show the strings (lwc_guide L9235–9238, L9744–9752).

**Detection hint:** Property editor class with `@api inputVariables` but no `validate()`
method; or a `validate()` whose `return` is not an array literal or array variable —
grep for `return {` and `return true` / `return false` inside a `validate()` body.

---

## Anti-Pattern 5: Confusing the property editor component with the runtime screen component

**What the LLM generates:**

```xml
<!-- js-meta.xml for the runtime component -->
<LightningComponentBundle>
    <targetConfigs>
        <targetConfig targets="lightning__FlowScreen">
            <property name="label" type="String"/>
            <!-- Wrong twice: configurationEditor is an ATTRIBUTE of targetConfig, not a
                 child element, and the value points at the component's own bundle. -->
            <configurationEditor>c-my-runtime-component</configurationEditor>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

**Why it happens:** LLMs conflate the two components because the property editor is conceptually related. They sometimes reference the runtime component as its own editor, or place runtime logic inside the editor.

**Correct pattern:**

The `configurationEditor` must reference a separate, dedicated LWC component built specifically for the builder context:

```xml
<targetConfig targets="lightning__FlowScreen" configurationEditor="c-my-property-editor">
    <property name="label" type="String"/>
</targetConfig>
```

For an invocable action there is no XML at all — the registration is the
`configurationEditor` modifier on `@InvocableMethod` (apexdev L5413):

```apex
@InvocableMethod(label='Send HTML Email' configurationEditor='c-html-email-editor')
public static List<Result> sendEmails(List<Request> requests) { /* ... */ }
```

The editor component receives `inputVariables` and `builderContext`. The runtime component receives the actual `@api` properties set by the admin.

**Detection hint:** a `<configurationEditor>` child element instead of a `targetConfig`
attribute; a `configurationEditor` value that matches the parent component's own name, or editor component files that import runtime-only modules like `lightning/navigation`.

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

---

## Anti-Pattern 7: Mutating inputVariables in place instead of dispatching an event

**What the LLM generates:**

```javascript
handleChange(event) {
    const param = this.inputVariables.find(v => v.name === 'volume');
    param.value = event.detail.value;   // writes straight into the builder's copy
}
```

**Why it happens:** The array is right there and assignment reads like the obvious update.
LLMs also carry over the two-way-binding habit from other frameworks.

**Why it is wrong:** `inputVariables` is described as "a copy of the flow metadata from Flow
Builder" (lwc_guide L9089, L9214). Flow Builder is not watching the array; the only channel
back is an event. Worse, writing through an `@api` property is an illegal mutation in LWC,
so the same line can throw instead of silently doing nothing.

**Correct pattern:**

```javascript
handleChange(event) {
    this.dispatchEvent(new CustomEvent('configuration_editor_input_value_changed', {
        bubbles: true,
        cancelable: false,
        composed: true,
        detail: { name: 'volume', newValue: event.detail.value, newValueDataType: 'Number' }
    }));
}
```

**Detection hint:** assignment into a `find()` result or an index of `inputVariables` /
`genericTypeMappings` — grep for `inputVariables[` followed by `]` and `=`, `param.value =`,
`.value =` on a variable derived from `inputVariables`, and any `this.inputVariables.push(`
or `.splice(`.
