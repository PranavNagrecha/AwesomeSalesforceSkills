# LWC in Flow Screens — Work Template

Use this template when building or reviewing a custom LWC component intended for a Flow screen element.

---

## Scope

**Skill:** `lwc-in-flow-screens`

**Component name:** `<!-- e.g. myAddressEntry -->`

**Request summary:** <!-- What does this component do in the flow? -->

---

## Context Gathered

Answer these before writing or reviewing any code:

| Question | Answer |
|---|---|
| Flow type | Screen Flow / (confirm it is NOT auto-launched) |
| Component role | New build / Review existing / Troubleshoot data-flow |
| Input @api properties | <!-- list: propName (FlowType) --> |
| Output @api properties | <!-- list: propName (FlowType) --> |
| Bidirectional properties | <!-- list: propName (input + output) --> |
| Custom validation needed? | Yes / No |
| Programmatic navigation needed? | Yes / No — if yes, which actions: NEXT / BACK / FINISH |
| Known data-flow symptoms | <!-- e.g. output always blank, validate never called --> |

---

## Checklist

Work through these in order. Check each item before marking the work done.

### .js-meta.xml Configuration

- [ ] `lightning__FlowScreen` is listed in `<targets>`.
- [ ] Each `@api` property that Flow Builder should see has a `<property>` entry in `<targetConfig>`.
- [ ] `role="inputOnly"` / `role="outputOnly"` / `role="inputOutput"` is correct for each property.
- [ ] Data types match Flow variable types (`String`, `Integer`, `Boolean`, `Apex-defined`).

```xml
<!-- Template snippet -->
<targets>
  <target>lightning__FlowScreen</target>
</targets>
<targetConfigs>
  <targetConfig targets="lightning__FlowScreen">
    <property name="INPUT_PROP" type="String" role="inputOnly" label="Label" />
    <property name="OUTPUT_PROP" type="String" role="outputOnly" label="Label" />
  </targetConfig>
</targetConfigs>
```

### Output Properties — FlowAttributeChangeEvent

- [ ] No `@api` output property is mutated directly (`this.outputProp = value`).
- [ ] Every output update dispatches `FlowAttributeChangeEvent`.
- [ ] `FlowAttributeChangeEvent` value type matches the declared Flow datatype.

```js
// Import at top of component JS
import { FlowAttributeChangeEvent } from 'lightning/flowSupport';

// In handler
this.dispatchEvent(new FlowAttributeChangeEvent('OUTPUT_PROP', newValue));
```

### Derived Outputs — Back-Navigation Safety

- [ ] All derived outputs are fired in `connectedCallback` (initializes on every mount).
- [ ] All derived outputs are fired in the `set` accessor of any input that drives them.
- [ ] All derived outputs are fired in every user-interaction handler that changes them.

```js
connectedCallback() {
  this._emitDerivedOutput(); // Re-fires on every back+forward navigation
}

@api
get inputProp() { return this._inputProp; }
set inputProp(val) {
  this._inputProp = val;
  this._emitDerivedOutput(); // Re-fires when Flow pushes a new input value
}

_emitDerivedOutput() {
  const computed = /* derive from this._inputProp */;
  this.dispatchEvent(new FlowAttributeChangeEvent('outputProp', computed));
}
```

### Validation (if applicable)

- [ ] Validation method is named exactly `validate` (case-sensitive).
- [ ] `validate()` is decorated with `@api` so the Flow runtime can call it.
- [ ] Returns `{ isValid: boolean, errorMessage: string }`.
- [ ] Returns `{ isValid: true, errorMessage: '' }` when valid (no null/undefined).

```js
@api validate() {
  const isValid = /* your rule */;
  return {
    isValid: Boolean(isValid),
    errorMessage: isValid ? '' : 'Descriptive error message for the user.'
  };
}
```

### Navigation Events (if applicable)

- [ ] `availableActions` is declared as `@api availableActions = []`.
- [ ] Every navigation dispatch checks `availableActions.includes('ACTION')` first.
- [ ] No navigation event and `FlowAttributeChangeEvent` are dispatched in the same synchronous call.

```js
import { FlowNavigationNextEvent, FlowNavigationBackEvent } from 'lightning/flowSupport';

@api availableActions = [];

handleNext() {
  if (this.availableActions.includes('NEXT')) {
    this.dispatchEvent(new FlowNavigationNextEvent());
  }
}
```

---

## Data-Flow Issue Diagnosis

If the component is exhibiting a data-flow problem, use this table to identify root cause:

| Symptom | Most Likely Root Cause | Fix |
|---|---|---|
| Output Flow variable always blank | Direct `@api` mutation instead of `FlowAttributeChangeEvent` | Replace `this.prop = val` with `FlowAttributeChangeEvent` |
| Output blank after Back navigation | Derived output not fired in `connectedCallback` | Add `_emitDerivedOutput()` call to `connectedCallback` |
| `validate()` never blocks navigation | Method not named exactly `validate` | Rename method to `validate` |
| Navigation event fires but flow does not advance | `availableActions` not checked or `NEXT` not in the list | Add `availableActions.includes('NEXT')` guard |
| Output stale after programmatic navigation | `FlowAttributeChangeEvent` and nav event fired together | Separate: emit change eagerly, navigate separately |

---

## Notes

<!-- Record any deviations from the standard patterns above and the reason why. -->
