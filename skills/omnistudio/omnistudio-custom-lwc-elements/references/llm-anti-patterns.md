# LLM Anti-Patterns — OmniStudio Custom LWC Elements

Common mistakes AI coding assistants make when generating or advising on OmniStudio custom LWC elements.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using `dispatchEvent` Instead of Pubsub to Update OmniScript Data

**What the LLM generates:** The AI generates a custom event dispatch to communicate from the LWC back to the OmniScript, applying standard LWC parent-child event patterns:

```javascript
// Wrong: dispatching a DOM custom event — OmniScript does not listen for this
handleChange(evt) {
  this.dispatchEvent(new CustomEvent('valuechange', {
    detail: { selectedDate: evt.target.value },
    bubbles: true
  }));
}
```

**Why it happens:** `dispatchEvent` with `bubbles: true` is the standard LWC pattern for communicating from a child to a parent. LLMs apply it broadly. They do not know that custom OmniScript elements are not in a direct parent-child component hierarchy with the OmniScript runtime — they communicate through a pubsub event bus, not DOM events.

**Correct pattern:**

```javascript
import pubsub from 'omnistudio/pubsub'; // or 'vlocity_cmt/pubsub' for managed package

handleChange(evt) {
  pubsub.fireEvent(this.omniOutputMap, 'omniupdatebyfield', {
    SelectedDate: evt.target.value  // Key must match OmniScript designer output field name
  });
}
```

**Detection hint:** Look for `dispatchEvent` or `CustomEvent` in any LWC that also declares `@api omniJsonData` or `@api omniOutputMap`. If present, the AI has applied the wrong communication pattern.

---

## Anti-Pattern 2: Mutating `omniJsonData` Directly to Update OmniScript State

**What the LLM generates:** The AI directly assigns to properties of `omniJsonData` to update the OmniScript data model, treating it as a shared mutable state object:

```javascript
// Wrong: mutating omniJsonData does not update the OmniScript data model
handleChange(evt) {
  this.omniJsonData.SelectedDate = evt.target.value;
  this.omniJsonData = { ...this.omniJsonData }; // attempt to force reactivity
}
```

**Why it happens:** LLMs recognize `omniJsonData` as the data container for the OmniScript context and assume writing to it propagates changes back. They apply standard JavaScript object mutation patterns without knowing that `omniJsonData` is a one-way input: changes to it in the LWC are local only and do not flow back to the OmniScript runtime.

**Correct pattern:**

```javascript
// Correct: push changes back via omniupdatebyfield pubsub event
import pubsub from 'omnistudio/pubsub';

handleChange(evt) {
  pubsub.fireEvent(this.omniOutputMap, 'omniupdatebyfield', {
    SelectedDate: evt.target.value
  });
}
```

**Detection hint:** Look for assignments to `this.omniJsonData` or its nested properties (`this.omniJsonData.SomeField = ...`). Any mutation of `omniJsonData` inside the LWC is an anti-pattern.

---

## Anti-Pattern 3: Omitting `omniOutputMap` from `fireEvent` Calls

**What the LLM generates:** The AI fires pubsub events without passing `omniOutputMap` as the first argument, using a channel string literal or no channel argument:

```javascript
// Wrong: using a string channel — not scoped to this OmniScript instance
pubsub.fireEvent('omniOutputChannel', 'omniupdatebyfield', { SelectedDate: value });

// Also wrong: no channel argument — fires to all subscribers globally
pubsub.fireEvent('omniupdatebyfield', { SelectedDate: value });
```

**Why it happens:** LLMs see pubsub examples that use string channel names in standard LWC pubsub patterns. They apply the same pattern to OmniStudio pubsub without knowing that `omniOutputMap` is a channel reference injected by the OmniScript runtime to scope events to the specific OmniScript instance hosting this element.

**Correct pattern:**

```javascript
// Correct: always use this.omniOutputMap as the first argument
pubsub.fireEvent(this.omniOutputMap, 'omniupdatebyfield', {
  SelectedDate: value
});
```

**Detection hint:** In any `pubsub.fireEvent` call, the first argument should be `this.omniOutputMap`. If the first argument is a string literal, it is wrong.

---

## Anti-Pattern 4: Adding `@wire` Adapters Inside Custom OmniScript Elements

**What the LLM generates:** The AI adds wire-based data fetching inside the custom element, using a reactive property from `omniJsonData` as a source:

```javascript
// Wrong: @wire adapter inside an OmniScript custom element
import { wire } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';

@wire(getRecord, { recordId: '$omniJsonData.RecordId', fields: [NAME_FIELD] })
record;
```

**Why it happens:** Wire adapters are the recommended LWC data access pattern in standard Lightning contexts. LLMs apply them universally without knowing that the OmniScript step lifecycle does not guarantee that wire reactive sources re-evaluate when the user navigates back to the step.

**Correct pattern:**

```javascript
// Correct: imperative Apex call in connectedCallback
import getRelatedRecord from '@salesforce/apex/MyController.getRelatedRecord';

async connectedCallback() {
  if (this.omniJsonData?.RecordId) {
    try {
      this._record = await getRelatedRecord({ recordId: this.omniJsonData.RecordId });
    } catch (e) {
      console.error('Record load failed', e);
    }
  }
}
```

**Detection hint:** Look for the `@wire` decorator in any LWC that also declares `@api omniJsonData` or `@api omniOutputMap`. Those two markers together identify a custom OmniScript element, and `@wire` usage in that context is the anti-pattern.

---

## Anti-Pattern 5: Registering `omniscriptvalidate` Listener Without Cleanup

**What the LLM generates:** The AI subscribes to the validation channel in `connectedCallback` but does not implement `disconnectedCallback` to unregister the listener:

```javascript
// Wrong: no disconnectedCallback — listener accumulates on repeated navigation
connectedCallback() {
  pubsub.registerListener('omniscriptvalidate', this.handleValidate, this);
}

// Missing: disconnectedCallback with unregisterListener
```

**Why it happens:** LLMs generate the `connectedCallback` registration because they are told about it, but they do not model the full LWC lifecycle or know that OmniScript step navigation repeatedly fires `connectedCallback` and `disconnectedCallback`. They produce incomplete lifecycle implementations.

**Correct pattern:**

```javascript
connectedCallback() {
  pubsub.registerListener('omniscriptvalidate', this.handleValidate, this);
}

disconnectedCallback() {
  // Required: must mirror connectedCallback registration
  pubsub.unregisterListener('omniscriptvalidate', this.handleValidate, this);
}

handleValidate() {
  pubsub.fireEvent(this.omniOutputMap, 'omnivalidate', {
    valid: this._isValid,
    errorMessage: this._isValid ? '' : 'Please complete the required selection.'
  });
}
```

**Detection hint:** Search for `registerListener` in the generated LWC. If the file does not also contain a `unregisterListener` call with the same event name, the lifecycle cleanup is missing.

---

## Anti-Pattern 6: Using `omniupdatebyfield` for a Merge Map Element

**What the LLM generates:** The AI uses `omniupdatebyfield` to push a nested object back to the OmniScript when the element type should be Custom Merge Map:

```javascript
// Wrong: omniupdatebyfield with a nested object for a Merge Map element type
pubsub.fireEvent(this.omniOutputMap, 'omniupdatebyfield', {
  SelectedProduct: { productId: '001', options: ['A', 'B'], basePrice: 99 }
});
```

**Why it happens:** LLMs know `omniupdatebyfield` is the update event for custom elements and apply it to all output scenarios. They do not distinguish between scalar field updates (which use `omniupdatebyfield`) and structured object merges (which use `omnimerge` with the Custom Merge Map element type).

**Correct pattern:**

```javascript
// Correct: use omnimerge for Custom Merge Map elements
pubsub.fireEvent(this.omniOutputMap, 'omnimerge', {
  SelectedProduct: { productId: '001', options: ['A', 'B'], basePrice: 99 }
});
```

**Detection hint:** If the OmniScript designer step type is Custom Merge Map Element and the LWC code fires `omniupdatebyfield`, the event key is wrong. Check the element type configuration in the OmniScript designer against the event key in the LWC.
