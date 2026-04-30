---
name: lwc-cross-tab-state-sync
description: "Use when an LWC needs to react to events that happen in another browser tab — record updates, login state, draft autosave, console-tab navigation. Triggers: 'sync data across tabs', 'BroadcastChannel LWC', 'storage event LWC', 'one tab updates the other', 'console workspace tab close detection'. NOT for state sync within the same Lightning page (use Lightning Message Service) or for server-pushed updates (use CometD or refreshApex)."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Reliability
triggers:
  - "two browser tabs of the same record need to stay in sync"
  - "LWC react when user logs out in another tab"
  - "share data between LWCs in different windows"
  - "BroadcastChannel pattern in Salesforce LWC"
  - "service console subtab close not refreshing parent"
tags:
  - lwc
  - cross-tab
  - browser-api
  - state-sync
inputs:
  - "the event triggering the sync (record save, logout, draft change)"
  - "scope (same origin always, single user always, console workspace boundaries)"
  - "fallback behavior when the browser API is unavailable"
outputs:
  - "BroadcastChannel or storage-event implementation"
  - "subscription / cleanup pattern wired to LWC lifecycle"
  - "platform-cache-aware refresh strategy when applicable"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-30
---

# LWC Cross-Tab State Sync

Activate when a Lightning Web Component must react to something that happens in *another browser tab* — for example, the user updates a record in tab A and tab B has a stale view. The skill produces a same-origin sync implementation using `BroadcastChannel` (preferred) or the `storage` event (fallback), wired into LWC lifecycle hooks with proper cleanup.

---

## Before Starting

Gather this context before working on anything in this domain:

- Whether the sync needs to be cross-window (different browser tabs) or cross-component (same Lightning page). Lightning Message Service (LMS) handles same-page; cross-tab needs browser APIs.
- Whether the data is sensitive. Anything written to `localStorage` is readable by any LWC on the same origin. PII should not flow through this channel.
- The user's likely browsers. `BroadcastChannel` is supported in Chrome, Edge, Firefox, Safari. Older corporate IE/legacy Edge environments fall back to `storage` events.
- Whether the LWC runs inside the Service Console. Console workspace tabs are separate `<iframe>` documents — same-origin but distinct windows. Both APIs work but the receiver count differs.

---

## Core Concepts

### `BroadcastChannel` vs. `storage` event

| API | Direction | Cleanup | Fallback |
|---|---|---|---|
| `BroadcastChannel('name')` | Same-origin pub-sub across tabs | Explicit `.close()` in `disconnectedCallback` | None — must polyfill via storage |
| `window.addEventListener('storage', ...)` | Fires when *another* tab writes to localStorage / sessionStorage | `removeEventListener` in `disconnectedCallback` | Universal browser support |

`BroadcastChannel` is the modern, structured-clone-aware API. The `storage` event fires only when *another* tab modifies storage (your own tab does not receive its own writes), making it a workable fallback for browsers without `BroadcastChannel`.

### LWC lifecycle integration

Subscribe in `connectedCallback`. Unsubscribe in `disconnectedCallback`. Failing to unsubscribe leaks the channel reference; over a long-lived workspace tab, that's a memory leak that compounds.

### Salesforce same-origin behavior

All Lightning experience tabs share the same origin (`*.lightning.force.com`). `BroadcastChannel` and `storage` events flow freely between them. Console workspace subtabs run inside their own iframes but on the same origin; the channel reaches them too.

---

## Common Patterns

### Pattern: post-save invalidation

**When to use:** Tab A saves a Case. Tab B is showing the same Case from a stale wire.

**How it works:** On save success in tab A, post `{type:'record-updated', recordId:'500...'}` to a `BroadcastChannel('record-updates')`. Tab B's component subscribes to the channel, filters on the recordId it cares about, and calls `refreshApex(this.wiredCase)` to re-fetch.

**Why not the alternative:** Polling every 30 seconds wastes API calls for records that didn't change.

### Pattern: logout fan-out

**When to use:** User clicks logout in tab A; tab B should redirect to the login page instead of showing a stale dashboard.

**How it works:** On logout, post `{type:'session-ended'}`. Every component subscribed handles the message by clearing local state and navigating away.

### Pattern: draft-state coordination

**When to use:** User has a long form half-filled in tab A; opens tab B to do something else; comes back.

**How it works:** On every form change (debounced), write `{recordId, draft, timestamp}` to localStorage. On tab focus, read storage; if a draft exists newer than the page-load timestamp, prompt the user to restore.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Modern browsers only, structured payload | `BroadcastChannel` | Cleanest API; no storage residue |
| Need IE11 / very old corporate browser | `storage` event | Universal support |
| Need persistence across reload | localStorage + storage event | Channel data is ephemeral |
| Within same Lightning page only | Lightning Message Service | LMS is the supported same-page mechanism |
| Need server-pushed updates from other users | CometD / Pub-Sub gRPC / Streaming API | Cross-tab solves only same-user, same-browser |

---

## Recommended Workflow

1. Confirm the sync is genuinely cross-tab. If it's cross-component on the same page, switch to LMS. If it's cross-user, switch to a server-side event channel.
2. Pick the API: `BroadcastChannel` if browser support permits; otherwise `storage` event.
3. Define the message schema. Always include a `type` discriminator and a timestamp. Never include PII.
4. Wire subscribe in `connectedCallback`, unsubscribe in `disconnectedCallback`. Tests must cover both.
5. Ignore your own messages. `BroadcastChannel` does not echo to the sender; the `storage` event does not fire for the writing tab. Either way, design the handler to be idempotent in case the platform changes.
6. Add a feature-detection fallback. Wrap `typeof BroadcastChannel !== 'undefined'`; on environments without it, drop to a no-op or storage-based polyfill.
7. Test in Service Console with multiple subtabs open — that's where most cross-tab bugs surface.

---

## Review Checklist

- [ ] Subscribe/unsubscribe paired across `connectedCallback` / `disconnectedCallback`
- [ ] Message schema versioned and PII-free
- [ ] Feature detection for `BroadcastChannel` with a defined fallback
- [ ] Idempotent handler — receiving the same message twice doesn't break state
- [ ] Tested in at least two browser tabs and (if applicable) Service Console subtabs
- [ ] No business logic that *requires* the sync to fire — treat as best-effort enhancement

---

## Salesforce-Specific Gotchas

1. **`BroadcastChannel` does not echo to sender** — Tab A posting and reading from the same channel will not receive its own message. Test with two distinct tabs always.
2. **`storage` event payload is the *new value*, not a structured message** — If you write the entire object as JSON, parse it; if you write only a key, the value won't tell you what changed.
3. **Service Console subtab close is invisible to siblings** — A subtab closing does not fire any cross-tab event by itself; you must explicitly post a message before close in the workspace API hook.
4. **`localStorage` is shared across browser profiles only when same Chrome profile** — Cross-profile users see independent storage; cross-tab sync within a single user's session is the only guaranteed scope.
5. **Locker Service / Lightning Locker restrictions** — Older Locker versions sandboxed `BroadcastChannel`; the modern Lightning Web Security policy permits it but verify in the org's actual security context.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Channel implementation module | The wrapper around `BroadcastChannel` with feature-detection fallback |
| Message schema | TypeScript-style JSDoc describing the discriminator + payload |
| Test scaffolding | Jest with a mocked `BroadcastChannel` that fires across simulated tabs |

---

## Related Skills

- lwc/message-channel-patterns — for *same-page* component communication via Lightning Message Service
- lwc/lwc-imperative-apex — for the `refreshApex` pattern usually triggered by the cross-tab event
- lwc/lifecycle-hooks — for the connectedCallback/disconnectedCallback discipline that prevents leaks
