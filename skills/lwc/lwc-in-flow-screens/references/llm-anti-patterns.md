# LLM Anti-Patterns — LWC in Flow Screens

Common mistakes AI coding assistants make when generating or advising on custom LWC components inside Flow screens.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Not firing FlowAttributeChangeEvent when output values change

**What the LLM generates:**

```javascript
@api selectedRecordId;

handleSelect(event) {
    this.selectedRecordId = event.detail.id;
    // Flow never sees the updated value
}
```

**Why it happens:** In standalone LWC, setting an `@api` property from inside the component is unusual but works for local display. In a Flow screen, the runtime reads output variables only if `FlowAttributeChangeEvent` was dispatched.

**Correct pattern:**

```javascript
@api selectedRecordId;

handleSelect(event) {
    this.selectedRecordId = event.detail.id;
    this.dispatchEvent(new FlowAttributeChangeEvent(
        'selectedRecordId', this.selectedRecordId
    ));
}
```

**Detection hint:** `@api` output property assigned without a corresponding `FlowAttributeChangeEvent` dispatch.

---

## Anti-Pattern 2: Returning the wrong shape from validate()

**What the LLM generates:**

```javascript
@api
validate() {
    if (!this.selectedRecordId) {
        return false; // Wrong — Flow expects an object, not a boolean
    }
    return true;
}
```

**Why it happens:** LLMs model validation as a boolean gate. Flow's validate contract requires an object with `isValid` and optionally `errorMessage`.

**Correct pattern:**

```javascript
@api
validate() {
    if (!this.selectedRecordId) {
        return {
            isValid: false,
            errorMessage: 'Please select a record before proceeding.'
        };
    }
    return { isValid: true };
}
```

**Detection hint:** `validate()` method that returns a boolean or a string instead of an object with `isValid`.

---

## Anti-Pattern 3: Not declaring @api on the validate method

**What the LLM generates:**

```javascript
validate() {
    // Missing @api — Flow runtime cannot call this method
    return { isValid: !!this.value };
}
```

**Why it happens:** LLMs sometimes omit the `@api` decorator because `validate` looks like an internal method. Without `@api`, Flow cannot invoke it.

**Correct pattern:**

```javascript
@api
validate() {
    return { isValid: !!this.value };
}
```

**Detection hint:** `validate()` method definition without `@api` decorator on the line above.

---

## Anti-Pattern 4: Using FlowNavigationNextEvent without checking availableActions

**What the LLM generates:**

```javascript
import { FlowNavigationNextEvent } from 'lightning/flowSupport';

handleNext() {
    this.dispatchEvent(new FlowNavigationNextEvent());
}
```

**Why it happens:** LLMs generate navigation events directly without checking whether the action is available. On the last screen of a Flow, `NEXT` may not be in `availableActions`, causing a silent failure.

**Correct pattern:**

```javascript
@api availableActions;

handleNext() {
    if (this.availableActions.find(a => a === 'NEXT')) {
        this.dispatchEvent(new FlowNavigationNextEvent());
    }
}
```

**Detection hint:** `FlowNavigationNextEvent` or `FlowNavigationBackEvent` dispatched without checking `this.availableActions`.

---

## Anti-Pattern 5: Treating @api input properties as writable local state

**What the LLM generates:**

```javascript
@api recordName;

handleEdit(event) {
    this.recordName = event.target.value; // Mutating @api property
}
```

**Why it happens:** LLMs treat `@api` like regular class properties. While LWC technically allows setting an `@api` property internally, it breaks the parent-to-child contract and causes reactivity confusion when Flow re-provisions the value.

**Correct pattern:**

```javascript
@api recordName;
_localName;

connectedCallback() {
    this._localName = this.recordName;
}

handleEdit(event) {
    this._localName = event.target.value;
    this.dispatchEvent(new FlowAttributeChangeEvent('recordName', this._localName));
}
```

**Detection hint:** Direct assignment to an `@api` property inside an event handler in a Flow screen component.

---

## Anti-Pattern 6: Forgetting to import FlowAttributeChangeEvent

**What the LLM generates:**

```javascript
// No import statement
handleChange(event) {
    this.dispatchEvent(new FlowAttributeChangeEvent('myProp', event.detail.value));
    // ReferenceError: FlowAttributeChangeEvent is not defined
}
```

**Why it happens:** LLMs sometimes omit imports for platform classes they consider "built-in," especially when generating partial code snippets.

**Correct pattern:**

```javascript
import { FlowAttributeChangeEvent } from 'lightning/flowSupport';

handleChange(event) {
    this.dispatchEvent(new FlowAttributeChangeEvent('myProp', event.detail.value));
}
```

**Detection hint:** `FlowAttributeChangeEvent` or `FlowNavigationNextEvent` used without a corresponding import from `lightning/flowSupport`.
