# Gotchas — LWC in Flow Screens

Non-obvious Salesforce platform behaviors that cause real production problems when building custom LWC screen components.

---

## Gotcha 1: Direct @api Mutation Is Silently Ignored by the Flow Runtime

**What happens:** The component sets `this.outputProp = value` inside a change handler. The assignment succeeds in JavaScript — the local property now holds the value — but the corresponding Flow variable remains blank or unchanged. Any downstream Decision element or the next screen that references the Flow variable sees the old value.

**When it occurs:** Any time a developer writes to an `@api` property from within the component that owns it. The LWC framework allows this operation and does not throw an error, so the bug is invisible during development. It only surfaces when the Flow variable is inspected or used downstream.

**Why:** The `@api` decorator signals that the property is owned by the parent (in this case the Flow runtime). Writes from inside the component are not observed by the runtime's variable store. `FlowAttributeChangeEvent` is the only mechanism the Flow runtime listens to.

**How to avoid:** Replace every `this.<outputProp> = value` with:
```js
this.dispatchEvent(new FlowAttributeChangeEvent('<outputProp>', value));
```
Treat `@api` output properties as write-through channels to Flow, not as local state.

---

## Gotcha 2: `validate()` Must Be Named Exactly `validate` — Any Other Name Is Ignored

**What happens:** A component implements `validateForm()` or `runValidation()` expecting Flow to call it before navigation. The Flow runtime does not call the method. Users can proceed with invalid input.

**When it occurs:** Teams rename the method to be more descriptive, or they add a prefix/suffix to avoid name collisions when the component has multiple internal validation functions.

**Why:** The Flow runtime uses duck-typing to find the validation method — it calls `component.validate()` by name. There is no interface registration or decorator. Any other name is simply not invoked.

**How to avoid:** Name the public validation method exactly `validate`. Internal helper methods can have any name. Keep the public contract minimal:
```js
@api validate() {
  const isValid = this._checkRules();
  return { isValid, errorMessage: isValid ? '' : 'Fix the highlighted errors.' };
}
```
The return object must have exactly the shape `{ isValid: boolean, errorMessage: string }`. Missing either key can cause unpredictable behavior in how Flow handles the result.

([Salesforce Developers: Validation Methods for Screen Components](https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-validate-external-internal-methods.html))

---

## Gotcha 3: Derived Outputs Reset to Blank on Back Navigation

**What happens:** A component computes an output value (e.g. a formatted string derived from two input properties). On first load, the output is correct. When the user clicks Back and returns to the screen, the derived output Flow variable is blank again. The next screen or a Decision element that reads it sees an empty value.

**When it occurs:** The `FlowAttributeChangeEvent` for the derived output is fired only in a user-interaction handler (`handleChange`, `handleSelect`, etc.) but not in `connectedCallback`. When the user navigates back to the screen, the component remounts and `connectedCallback` runs, but no event is dispatched, so the Flow variable is not repopulated.

**Why:** The component remounts fully on each forward navigation back to that screen. The Flow runtime does not cache output values that were set during a previous visit; it waits for the component to re-emit them.

**How to avoid:** For any derived output, fire `FlowAttributeChangeEvent` in three places:
1. `connectedCallback` — initializes the output on mount.
2. The `set` accessor of every input that drives the derivation — handles Flow pushing a new input value reactively.
3. Any user interaction handler that changes local state — handles user-driven changes.

([Salesforce Developers: Best Practices for Reactivity in Screen Flows](https://developer.salesforce.com/docs/platform/lwc/guide/use-best-practices-reactivity.html))

---

## Gotcha 4: Navigation Events Are Silently Dropped When the Action Is Not Available

**What happens:** A component fires `FlowNavigationNextEvent` programmatically but nothing happens. The flow does not advance. There is no console error.

**When it occurs:** The component fires the navigation event without checking `availableActions` first. This is most common when the component is reused in multiple flows, some of which suppress the Next button or use Finish instead.

**Why:** The Flow runtime only honors navigation events that correspond to actions declared in `availableActions`. If `NEXT` is not in the list, the event is consumed silently.

**How to avoid:** Always guard navigation dispatches:
```js
@api availableActions = [];

handleNext() {
  if (this.availableActions.includes('NEXT')) {
    this.dispatchEvent(new FlowNavigationNextEvent());
  }
}
```
(`availableActions` is an `@api` array that Flow populates automatically; declare it as shown.)

([Salesforce Developers: Configure a Component for Flow Screens](https://developer.salesforce.com/docs/platform/lwc/guide/use-config-for-flow-screens.html))

---

## Gotcha 5: Simultaneously Firing FlowAttributeChangeEvent and a Navigation Event Causes Race Conditions

**What happens:** A "Save and Go" button handler fires `FlowAttributeChangeEvent` to commit the final value and immediately fires `FlowNavigationNextEvent` in the same synchronous function. The next screen or Decision element occasionally sees the old value for the output variable.

**When it occurs:** Any handler that tries to write output and navigate in the same synchronous call.

**Why:** The Flow runtime processes these events asynchronously and does not guarantee attribute-change resolution before navigation when both are dispatched synchronously. The timing is non-deterministic.

**How to avoid:** Update output values via `FlowAttributeChangeEvent` in the user's input handlers (as the user types or selects), so the output is always current before any navigation. Do not batch the write and the navigation in the same handler.

([Salesforce Developers: Best Practices for Reactivity in Screen Flows](https://developer.salesforce.com/docs/platform/lwc/guide/use-best-practices-reactivity.html))
