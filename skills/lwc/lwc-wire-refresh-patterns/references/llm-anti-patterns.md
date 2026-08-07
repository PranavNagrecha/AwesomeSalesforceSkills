# LLM Anti-Patterns — LWC Wire Refresh Patterns

Common mistakes AI coding assistants make when refreshing wired data.

## Anti-Pattern 1: Calling refreshApex on the destructured data

**What the LLM generates:**

```
@wire(getAccounts) accounts;
// ...
await refreshApex(this.accounts.data);  // wrong
```

**Why it happens:** Model sees `.data` in use elsewhere.

**Correct pattern:**

```
refreshApex takes the RAW wired value (the whole @wire receiver):
@wire(getAccounts) wiredAccounts;
// ...
await refreshApex(this.wiredAccounts);

Or, when using the function-form wire:
@wire(getAccounts)
handle(value) { this._wired = value; this.accounts = value.data; }
// ...
await refreshApex(this._wired);
```

**Detection hint:** `refreshApex(this.<name>.data)` or `refreshApex(someArray)`.

---

## Anti-Pattern 2: Param-null-then-restore hack

**What the LLM generates:**

```
this.filter = null;
setTimeout(() => { this.filter = savedFilter; }, 0);
```

**Why it happens:** Model tries to force a wire rerun without knowing about refreshApex.

**Correct pattern:**

```
For custom Apex wires, use refreshApex(rawWiredValue). For UI API,
dispatch RefreshEvent or call notifyRecordUpdateAvailable. Param
tricks are fragile and trigger extra re-renders.
```

**Detection hint:** LWC assigning a reactive wire param to null, falsy, or sentinel and restoring moments later.

---

## Anti-Pattern 3: Using getRecordNotifyChange for new code

**What the LLM generates:**

```
import { getRecordNotifyChange } from 'lightning/uiRecordApi';
getRecordNotifyChange([{ recordId }]);
```

**Why it happens:** Model uses deprecated patterns from older training data.

**Correct pattern:**

```
RefreshView API (Spring '23+):
import { RefreshEvent } from 'lightning/refresh';
this.dispatchEvent(new RefreshEvent());

Or for targeted LDS refresh:
import { notifyRecordUpdateAvailable } from 'lightning/uiRecordApi';
notifyRecordUpdateAvailable([{ recordId }]);
```

**Detection hint:** Import of `getRecordNotifyChange` from `lightning/uiRecordApi`.

---

## Anti-Pattern 4: Forgetting to return the refreshApex promise

**What the LLM generates:**

```
handleRefresh() {
    refreshApex(this.wiredData);  // no return
}
```

**Why it happens:** Model treats it as fire-and-forget.

**Correct pattern:**

```
handleRefresh() {
    return refreshApex(this.wiredData);
}

Returning the promise lets Jest await it and downstream callers
chain follow-up logic after data arrives.
```

**Detection hint:** LWC method calling `refreshApex(...)` or `notifyRecordUpdateAvailable(...)` without returning the promise.

---

## Anti-Pattern 5: Refreshing before the imperative DML resolves

**What the LLM generates:**

```
updateAccount({ acc });
refreshApex(this.wiredAccounts);  // fires parallel, race
```

**Why it happens:** Model misses that updateAccount is a Promise.

**Correct pattern:**

```
await updateAccount({ acc });
await refreshApex(this.wiredAccounts);

Without await, the refresh fires while DML is still in flight —
wires may see pre-update data.
```

**Detection hint:** Sequential calls to an imperative Apex method and a refresh call with no `await` or `.then` chaining.


---

## Anti-Pattern: Treating `RefreshView` as a wire adapter

**What the LLM generates:**

```javascript
import { RefreshView } from 'lightning/refresh';

export default class Child extends LightningElement {
    @wire(RefreshView)
    handleRefresh() { ... }
}
```

…or prose variants: "components in the view listen via `@wire(RefreshView)` or by implementing a `refresh()` method."

**Why it happens:** The feature is documented under the name "RefreshView API," and almost every other `lightning/*` data module the model has seen (`lightning/uiRecordApi`, `lightning/uiObjectInfoApi`, `lightning/apex`) exposes wire adapters. Pattern-matching on the module family produces `@wire(RefreshView)`. The Aura predecessor `force:refreshView` was also declarative (an `<aura:handler>`), which reinforces the guess. But `RefreshView` is the *name of the API*, not an exported symbol — importing it yields `undefined`, and `@wire(undefined)` fails at compile time. There is likewise no lifecycle hook or convention named `refresh()`; LWC's only lifecycle hooks are `constructor`, `connectedCallback`, `renderedCallback`, `disconnectedCallback`, `errorCallback`, and `render`.

**Correct version:**

```javascript
import { registerRefreshHandler, unregisterRefreshHandler } from 'lightning/refresh';

connectedCallback() {
    this.refreshHandlerID = registerRefreshHandler(this, this.refreshHandler);
}
disconnectedCallback() {
    unregisterRefreshHandler(this.refreshHandlerID);
}
refreshHandler() {
    return refreshApex(this.wiredResult);   // return a Promise
}
```

The module exports exactly `registerRefreshContainer`, `registerRefreshHandler`, `unregisterRefreshContainer`, `unregisterRefreshHandler`, `RefreshEvent`, and the `REFRESH_COMPLETE` / `REFRESH_COMPLETE_WITH_ERRORS` / `REFRESH_ERROR` status constants. Publishing (`dispatchEvent(new RefreshEvent())`) is the only half of the API that is event-based.

**Detection hint:** grep for `@wire(RefreshView)`, `import { RefreshView }`, or `RefreshView` used as anything other than the prose name of the API. Mechanical rule: if a file mentions RefreshView but contains none of `registerRefreshHandler|registerRefreshContainer|unregisterRefresh`, its subscriber-side guidance is almost certainly invented. Second hint: `unregisterRefreshHandler(this)` — the function takes the ID returned by `registerRefreshHandler`, not the component.

---

## Anti-Pattern: Dating the RefreshView API to Summer '24

**What the LLM generates:** "RefreshView, introduced Summer '24, replaces `getRecordNotifyChange`."

**Why it happens:** `getRecordNotifyChange`'s deprecation and the `notifyRecordUpdateAvailable` rename are more recent than the RefreshView launch, and the model collapses the two events into one date. There is also a genuine Winter '24 (release 246) release note, "Use RefreshView API with Lightning Locker," which is a Locker-compatibility follow-up, not the introduction.

**Correct version:** The `lightning/refresh` module and the RefreshView API shipped in **Spring '23** (beta at launch). The separate, correct claim in this skill — that `getRecordNotifyChange` is deprecated in favour of `notifyRecordUpdateAvailable` — is unaffected.

**Detection hint:** any release attribution for `lightning/refresh` later than Spring '23. Cross-check: the Learn MOAR Spring '23 developer blog announces the module.
