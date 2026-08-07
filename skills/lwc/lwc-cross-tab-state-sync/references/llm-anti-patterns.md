# LLM Anti-Patterns — LWC Cross-Tab State Sync

Common mistakes AI coding assistants make when generating cross-tab sync in LWC.

## Anti-Pattern 1: No `disconnectedCallback` cleanup

**What the LLM generates:**

```javascript
connectedCallback() {
    new BroadcastChannel('x').addEventListener('message', this.handle);
}
```

**Why it happens:** Treats subscribe as a one-time setup.

**Correct pattern:** Always pair subscribe + unsubscribe:

```javascript
connectedCallback() {
    this.channel = new BroadcastChannel('x');
    this.channel.addEventListener('message', this.handle);
}
disconnectedCallback() {
    this.channel?.close();
    this.channel = null;
}
```

**Detection hint:** Any `BroadcastChannel`, `addEventListener`, or `subscribe` call with no matching cleanup in `disconnectedCallback`.

---

## Anti-Pattern 2: Recommending Lightning Message Service for cross-tab

**What the LLM generates:** "Use Lightning Message Service to communicate between tabs."

**Why it happens:** Conflates same-page LMS with cross-window sync.

**Correct pattern:** LMS is scoped to a single Lightning page (one tab). Cross-tab requires browser APIs (`BroadcastChannel` / `storage` event).

**Detection hint:** Any LMS recommendation for a "different tab" / "second window" use case.

---

## Anti-Pattern 3: Writing PII to localStorage

**What the LLM generates:** "Save the form data to localStorage so it survives across tabs."

**Why it happens:** Ignores the security boundary; localStorage is not encrypted and is readable by every LWC on the same origin.

**Correct pattern:** Save only an opaque draft ID; fetch the body from the server. Or use `BroadcastChannel` for ephemeral cross-tab signals that don't persist.

**Detection hint:** `localStorage.setItem(..., JSON.stringify(<object containing fields>))` for any fields that look like names, emails, IDs, financial values.

---

## Anti-Pattern 4: Self-listening assumption

**What the LLM generates:**

```javascript
this.channel.postMessage(...);
// Expect own listener to fire
```

**Why it happens:** Treats `BroadcastChannel` like an in-process EventEmitter.

**Correct pattern:** `BroadcastChannel` does not echo to the sender. Update local state directly when publishing; rely on the channel only for *other* tabs.

**Detection hint:** Code that posts to a channel and expects its own listener to update local state.

---

## Anti-Pattern 5: No feature detection

**What the LLM generates:** Uses `BroadcastChannel` directly without a fallback.

**Why it happens:** Assumes universal modern-browser support.

**Correct pattern:** `typeof BroadcastChannel !== 'undefined'` guard with a storage-event polyfill or graceful degradation.

**Detection hint:** Direct construction `new BroadcastChannel(...)` without a surrounding feature check.


---

## Anti-Pattern: Importing `refreshApex` from `lightning/uiRecordApi` (and calling it on an LDS wire)

**What the LLM generates:**

```javascript
import { getRecord, refreshApex } from 'lightning/uiRecordApi';
...
@wire(getRecord, { recordId: '$recordId', fields: FIELDS })
handle(result) { this.wired = result; }
...
refreshApex(this.wired);
```

**Why it happens:** Two errors compound. (1) `refreshApex` and `getRecord` co-occur constantly in refresh discussions, so the model merges them into one import statement; `lightning/uiRecordApi` is the more memorable module name, so it wins. (2) `refreshApex` is treated as the generic "re-run my wire" function, when it is specifically the Apex-wire refresh primitive — it reads the internal Apex cache key off the provisioned result, which an LDS-provisioned result does not carry. In a cross-tab sync bus this is especially easy to miss: the code *looks* like it works because the tab often re-renders for unrelated reasons.

**Correct version:**

```javascript
import { getRecord, notifyRecordUpdateAvailable } from 'lightning/uiRecordApi';
// refreshApex, when you actually need it, comes from '@salesforce/apex'
notifyRecordUpdateAvailable([{ recordId: this.recordId }]);
```

Rule of thumb: **Apex `@wire` → `refreshApex` from `@salesforce/apex`. LDS wire (`getRecord`, `getRecords`, `getRelatedListRecords`, GraphQL) → `notifyRecordUpdateAvailable`, or a view-scoped `RefreshEvent` from `lightning/refresh`.**

**Detection hint:** two mechanical greps. First, `refreshApex` appearing in the same `import { … } from 'lightning/uiRecordApi'` statement — `lightning/uiRecordApi` never exports it, so this fails at compile time. Second, `refreshApex(x)` where `x` is assigned from a `@wire` whose adapter is not an `@salesforce/apex/...` import — that one compiles and silently does nothing.
