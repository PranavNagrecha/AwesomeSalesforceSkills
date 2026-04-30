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
