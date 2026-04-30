# Gotchas — LWC Cross-Tab State Sync

Non-obvious behaviors that cause real production problems in this domain.

## Gotcha 1: BroadcastChannel does not echo to sender

**What happens:** Developer tests `postMessage` and the listener fires, then discovers in production that "sometimes the listener doesn't fire."

**When it occurs:** Tests that use the same tab to publish and subscribe see no events; testing must use two distinct browser tabs.

**How to avoid:** Test with two tabs (or a Jest mock that simulates the cross-tab boundary). Document the no-self-echo behavior so future maintainers don't try to "fix" it by adding self-listeners.

---

## Gotcha 2: Storage event payload is the new value, not your message

**What happens:** Subscriber receives the storage event but `e.newValue` is `null` because the publisher cleared the key after setting it.

**When it occurs:** The set-and-clear trick used for one-shot signals.

**How to avoid:** Read `e.newValue` *only when not null*. The set-and-clear pattern fires the event once with the new value, then again with null when cleared — handle the null case as a no-op.

---

## Gotcha 3: Locker / Lightning Web Security divergence

**What happens:** `BroadcastChannel` works in one org but throws in another.

**When it occurs:** Older Lightning Locker sandboxed several browser APIs; modern Lightning Web Security (LWS) permits more. Org-by-org policy differs.

**How to avoid:** Feature-detect (`typeof BroadcastChannel !== 'undefined'`). Provide a storage-event fallback. Test in the actual target org's security mode.

---

## Gotcha 4: Service Console subtab close doesn't auto-broadcast

**What happens:** User closes a workspace subtab; sibling tabs don't notice.

**When it occurs:** The close itself emits no cross-tab event.

**How to avoid:** In the workspace API's tab-close hook, explicitly post a "subtab-closed" message before close. Otherwise siblings have no signal.

---

## Gotcha 5: PII through localStorage is observable to any LWC on the same origin

**What happens:** A draft form's content includes SSN; written to localStorage for cross-tab restore. Another LWC on the page can read it.

**When it occurs:** Any time PII is written to localStorage or sessionStorage.

**How to avoid:** Never write PII to storage. Use BroadcastChannel for ephemeral signals (which are not persisted). For draft restore, store only a draft ID and fetch the draft body from the server.
