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
RefreshView API (Summer '24+):
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
