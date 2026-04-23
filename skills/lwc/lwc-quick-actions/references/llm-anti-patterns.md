# LLM Anti-Patterns — LWC Quick Actions

Common mistakes AI coding assistants make when generating or advising on quick-action LWCs.
These patterns help the consuming agent self-check its own output before shipping.

## Anti-Pattern 1: Dispatching `CloseActionScreenEvent` Before The Save Completes

**What the LLM generates:**

```javascript
handleSave() {
  saveRecord({ recordId: this.recordId, payload: this.payload });
  this.dispatchEvent(new CloseActionScreenEvent());
}
```

**Why it happens:** The LLM treats the close event as a "submit" action and dispatches it synchronously with the Apex call. Training data often omits the `await`.

**Correct pattern:**

```javascript
async handleSave() {
  await saveRecord({ recordId: this.recordId, payload: this.payload });
  this.dispatchEvent(new ShowToastEvent({ title: 'Saved', variant: 'success' }));
  this.dispatchEvent(new CloseActionScreenEvent());
}
```

**Detection hint:** `CloseActionScreenEvent` dispatch on a line before any `await` or `.then(` in the same function.

---

## Anti-Pattern 2: Adding A `<template>` To A Headless Action

**What the LLM generates:** An `actionType="Action"` bundle with a `.html` file containing a spinner or confirmation text, on the assumption it will render during `invoke()`.

**Why it happens:** The LLM blends screen and headless conventions because both share the `lightning__RecordAction` target. It assumes "component = template".

**Correct pattern:**

```text
markCaseRead/
├── markCaseRead.js          // implements @api invoke()
├── markCaseRead.js-meta.xml // actionType="Action"
(no markCaseRead.html)
```

If feedback is needed, use `ShowToastEvent` from inside `invoke()` and `LightningConfirm.open(...)` for confirmations.

**Detection hint:** Bundle contains a `.html` file and a `.js-meta.xml` with `actionType="Action"`.

---

## Anti-Pattern 3: Forgetting `@api recordId`

**What the LLM generates:**

```javascript
export default class EditClosePlan extends LightningElement {
  recordId; // plain property, no @api
  connectedCallback() {
    console.log(this.recordId); // undefined
  }
}
```

**Why it happens:** The LLM treats `recordId` as just state and forgets the decorator that opts it in to the platform's automatic injection contract.

**Correct pattern:**

```javascript
import { LightningElement, api } from 'lwc';
export default class EditClosePlan extends LightningElement {
  @api recordId;
}
```

**Detection hint:** Component imports from `lightning/actions` or declares `lightning__RecordAction` target but JS has no `@api recordId` line.

---

## Anti-Pattern 4: Using `window.location.reload()` To Refresh The Record

**What the LLM generates:**

```javascript
await saveRecord(...);
window.location.reload();
this.dispatchEvent(new CloseActionScreenEvent());
```

**Why it happens:** The LLM reaches for generic web patterns and does not know about `getRecordNotifyChange` or `refreshApex`. Also common: using `location.href = ...` to navigate.

**Correct pattern:**

```javascript
import { getRecordNotifyChange } from 'lightning/uiRecordApi';
await saveRecord(...);
getRecordNotifyChange([{ recordId: this.recordId }]);
this.dispatchEvent(new CloseActionScreenEvent());
```

For navigation, use `NavigationMixin.Navigate({ type: 'standard__recordPage', attributes: { recordId, objectApiName, actionName: 'view' } })`.

**Detection hint:** `window.location` or `location.href` appears in any JS file in a quick-action bundle.

---

## Anti-Pattern 5: Mixing Targets Without Matching `targetConfigs`

**What the LLM generates:**

```xml
<targets>
  <target>lightning__AppPage</target>
  <target>lightning__RecordAction</target>
</targets>
<targetConfigs>
  <targetConfig targets="lightning__RecordAction" actionType="ScreenAction"/>
</targetConfigs>
```

...and the component references `@api recordId` unconditionally, so it breaks on `lightning__AppPage` where `recordId` is not injected. Or the LLM omits `targetConfigs` entirely, which fails deploy because `lightning__RecordAction` requires an `actionType`.

**Why it happens:** The LLM copies a two-target example from training data and does not realize each target typically needs its own `targetConfig` with matching properties and handling.

**Correct pattern:** Keep quick-action bundles focused on `lightning__RecordAction`. If the component must also work on another surface, wire each target explicitly and guard `recordId` usage:

```javascript
if (!this.recordId) {
  // not on a record surface — render a picker or a message
  return;
}
```

**Detection hint:** A bundle declares `lightning__RecordAction` but the `targetConfigs` block is missing, or declares multiple targets without matching `<targetConfig>` entries.
