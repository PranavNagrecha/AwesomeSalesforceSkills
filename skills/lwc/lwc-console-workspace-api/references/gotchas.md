# Gotchas — LWC Console Workspace API

Non-obvious Salesforce platform behaviors that cause real production problems when LWCs manipulate console tabs.

## Gotcha 1: Workspace-API calls throw outside a console host

**What happens:** Calling `openSubtab`, `refreshTab`, or any other `lightning/platformWorkspaceApi` lifecycle function outside a console-navigation app rejects with an error. The component appears broken in non-console previews (App Builder canvas, Experience Cloud site, mobile).

**When it occurs:** Any time an LWC built for Service Console is mounted on a non-console surface — admin previews, an App Builder Home page that re-uses the component, or a screenshot tool.

**How to avoid:** Wire `IsConsoleNavigation` and branch on its value. The non-console branch should provide an explicit fallback (usually `NavigationMixin.Navigate` for navigation; a toast or wired-record path for refresh).

---

## Gotcha 2: `IsConsoleNavigation` is asynchronous and unset on first render

**What happens:** Reading `this.isConsole` from `connectedCallback` or the initial render template returns `undefined`, not `false`. Code that assumes "if not true, then non-console" mis-fires in the milliseconds before the wire emits.

**When it occurs:** Any console-gated action invoked synchronously during component construction, before the `IsConsoleNavigation` wire has produced its first value.

**How to avoid:** Defer console-specific actions to user-event handlers or `renderedCallback`. If a `connectedCallback` action must consult console context, treat `this.isConsole === undefined` as "context not yet known — wait" rather than "not in a console."

---

## Gotcha 3: `refreshTab` resolves before wires re-evaluate

**What happens:** `await refreshTab(tabId)` returns, but the surrounding LWCs still show stale data for a few microseconds. A test that asserts post-refresh DOM state immediately after the `await` fails intermittently.

**When it occurs:** Refresh dispatches a signal to LDS; wires that listen for that signal re-fire asynchronously. The wire chain (apex import → wired property → re-render) needs at least one microtask tick.

**How to avoid:** After `await refreshTab(tabId)`, also `await Promise.resolve()` in tests before asserting DOM state. In production code, this is invisible — but be aware that `refreshTab` is not a synchronous data-refresh primitive.

---

## Gotcha 4: `getEnclosingTabId` and `getFocusedTabInfo` are not interchangeable

**What happens:** A subtab LWC calls `getFocusedTabInfo()` expecting "my tab" and gets the focused primary tab (whatever the user is on globally) — which may not be the subtab's host. Wrong tab gets refreshed.

**When it occurs:** Multi-tab workflows where the running LWC's tab isn't currently focused — e.g. a Lightning Message Service subscription triggers a refresh on a background tab.

**How to avoid:** Use `getEnclosingTabId()` for "the tab I'm in" and `getFocusedTabInfo()` for "the tab the user is on." They differ when the LWC's tab is not the foreground tab.

---

## Gotcha 5: Tab IDs do not survive page reload

**What happens:** Component persists a `tabId` to `sessionStorage` or a record field, attempting to "remember" which tab to refresh later. After the user reloads, the saved id refers to a tab that no longer exists; subsequent `refreshTab(savedId)` rejects.

**When it occurs:** Cross-session workflows that try to maintain tab identity across reload, or LWCs that try to share a tab id between unrelated browser tabs via storage.

**How to avoid:** Treat `tabId` as ephemeral and in-memory only. Persist `recordId` (or other domain identifiers) instead; re-resolve to tab id by walking `getAllTabInfo()` after reload.

---

## Gotcha 6: `setTabLabel` is unbatched and causes flicker

**What happens:** Calling `setTabLabel` from an unthrottled source (every keystroke, every wire emission, every `requestAnimationFrame`) makes the tab label visibly flicker as the platform applies each call.

**When it occurs:** Wires that re-emit frequently (a `getRecord` wire on a record being inline-edited), or imperative loops that call `setTabLabel` per change.

**How to avoid:** Debounce updates to one per ~300ms or one per meaningful record change. The wire's `data` reference changes by reference even when the displayed fields haven't, so compare the relevant field values before calling `setTabLabel`.

---

## Gotcha 7: Aura `lightning:workspaceAPI` event subscriptions don't fire for LWC API actions

**What happens:** Aura component subscribes to `lightning:workspaceAPI` events (e.g., `onTabRefresh`); LWC calls `refreshTab` for the same tab; Aura event handler does not fire.

**When it occurs:** Mixed Aura/LWC console implementations where one framework expects to react to the other's tab actions.

**How to avoid:** The underlying tab state IS shared; the *event surface* is not. For cross-framework reactivity, use a Lightning Message Service channel both sides subscribe to, and dispatch a message after the workspace-API action completes.

---

## Gotcha 8: Console iframe stack breaks `window.location.hash` semantics

**What happens:** A component uses `window.location.hash = '#step-2'` for in-page anchor navigation. Inside the Service Console iframe stack, the hash changes but the document does not scroll to the target — or scrolls the wrong document.

**When it occurs:** Multi-step LWC wizards that rely on traditional anchor navigation, embedded inside a subtab.

**How to avoid:** Manage step state in component state, not in URL hash. Use `scrollIntoView()` on a refs-tracked element for jump-to-step behavior.
