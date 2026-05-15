# LLM Anti-Patterns — LWC Console Workspace API

Common mistakes AI coding assistants make when generating LWCs that manipulate Service Console tabs.

## Anti-Pattern 1: Calling `openSubtab` / `refreshTab` without `IsConsoleNavigation` gate

**What the LLM generates:**

```javascript
import { openSubtab, getFocusedTabInfo } from 'lightning/platformWorkspaceApi';

async handleClick() {
    const focused = await getFocusedTabInfo();
    await openSubtab(focused.tabId, { pageReference: this.pageRef });
}
```

**Why it happens:** Training data weights workspace-API examples toward console-only callsites. The LLM does not generate the host-detection guard because the example it learned from didn't include one.

**Correct pattern:**

```javascript
import { IsConsoleNavigation, openSubtab, getFocusedTabInfo } from 'lightning/platformWorkspaceApi';
import { NavigationMixin } from 'lightning/navigation';
import { LightningElement, wire } from 'lwc';

export default class C extends NavigationMixin(LightningElement) {
    @wire(IsConsoleNavigation) isConsole;

    async handleClick() {
        if (this.isConsole) {
            const focused = await getFocusedTabInfo();
            await openSubtab(focused.tabId, { pageReference: this.pageRef });
        } else {
            this[NavigationMixin.Navigate](this.pageRef);
        }
    }
}
```

**Detection hint:** Search bundles for `from 'lightning/platformWorkspaceApi'` imports without a co-occurring `IsConsoleNavigation` wire. Any such bundle is broken outside the console.

---

## Anti-Pattern 2: Reading `this.isConsole` synchronously in `connectedCallback`

**What the LLM generates:**

```javascript
connectedCallback() {
    if (this.isConsole) {
        // do console setup
    } else {
        // do non-console setup
    }
}
```

**Why it happens:** LLM treats wire-adapter results as synchronously available properties (which they aren't on first render).

**Correct pattern:**

```javascript
@wire(IsConsoleNavigation) isConsole;

renderedCallback() {
    if (this.isConsole === undefined) return; // wire hasn't emitted yet
    if (this.consoleSetupDone) return;
    this.consoleSetupDone = true;
    // ... one-time setup
}
```

Or defer to a user-event handler that fires after the wire has resolved.

**Detection hint:** Any `connectedCallback` referencing `this.isConsole` is a bug. `IsConsoleNavigation` emits asynchronously.

---

## Anti-Pattern 3: Persisting `tabId` to durable storage

**What the LLM generates:**

```javascript
sessionStorage.setItem('myTabId', tabId);
// ... later, after a reload:
await refreshTab(sessionStorage.getItem('myTabId'));
```

**Why it happens:** Tab id "looks like" a stable handle that could survive a reload. LLM treats it like a recordId.

**Correct pattern:**

```javascript
// Persist a domain identifier (recordId), not the tab handle:
sessionStorage.setItem('lastRecordId', this.recordId);
// After reload, walk the tab list to re-resolve:
const tabs = await getAllTabInfo();
const target = tabs.find(t => t.recordId === sessionStorage.getItem('lastRecordId'));
if (target) await refreshTab(target.tabId);
```

**Detection hint:** Any code that writes `tabId` to `sessionStorage`, `localStorage`, a custom field, or URL params is a bug.

---

## Anti-Pattern 4: Asserting DOM state synchronously after `refreshTab` in tests

**What the LLM generates:**

```javascript
it('refreshes after save', async () => {
    await element.save();
    expect(element.shadowRoot.querySelector('.status').textContent).toBe('Resolved');
});
```

**Why it happens:** LLM treats `refreshTab` like a synchronous DOM update.

**Correct pattern:**

```javascript
it('refreshes after save', async () => {
    await element.save();
    await Promise.resolve(); // wait for refresh signal → wire re-evaluation
    await Promise.resolve(); // and one more tick for the DOM mutation
    expect(element.shadowRoot.querySelector('.status').textContent).toBe('Resolved');
});
```

**Detection hint:** Test files with `await refreshTab(...)` immediately followed by a `shadowRoot.querySelector(...).textContent` assertion — flaky in CI.

---

## Anti-Pattern 5: Aura `lightning:workspaceAPI.openSubtab` syntax mixed into LWC code

**What the LLM generates:**

```javascript
const workspace = this.template.querySelector('lightning-workspace-api');
workspace.openSubtab({ ... });
```

**Why it happens:** Aura's `lightning:workspaceAPI` was used via a child component with a method-style API; LLM transposes that pattern to LWC.

**Correct pattern:** `lightning/platformWorkspaceApi` is a module, not an embedded component. Import functions directly:

```javascript
import { openSubtab } from 'lightning/platformWorkspaceApi';
await openSubtab(...);
```

**Detection hint:** Any LWC template containing `<lightning-workspace-api>` or any JS that calls `.openSubtab(...)` on a `template.querySelector(...)` result. The Aura interface is not exposed as a child element in LWC.
