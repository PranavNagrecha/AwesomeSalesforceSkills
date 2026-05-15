---
name: lwc-console-workspace-api
description: "Use when an LWC needs to programmatically manipulate Service Console workspace tabs and the utility bar — opening tabs and subtabs, refreshing or closing tabs, setting tab labels and icons, detecting console context, and integrating with the utility bar — via the `lightning/platformWorkspaceApi` and `lightning/platformUtilityBarApi` modules. Triggers: 'openSubtab in LWC', 'refresh console tab from LWC', 'IsConsoleNavigation context detection', 'set tab label dynamically'. NOT for declarative Console App setup (use admin/service-console-configuration), navigation to records outside a console (use lwc/lwc-navigation-mixin or lwc/lightning-navigation-dead-link-handling), or Aura `lightning:workspaceAPI` migration (the LWC modules supersede it for new development)."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Reliability
triggers:
  - "open a subtab programmatically from LWC in Service Console"
  - "refresh the current console tab after a record update"
  - "detect if my LWC is running inside Service Console or a standard app"
  - "set the workspace tab label and icon dynamically based on record state"
  - "close a console tab after the user finishes a multi-step action"
  - "lightning/platformWorkspaceApi getFocusedTabInfo not returning the right tab"
  - "utility bar minimize and open from LWC inside Service Console"
tags:
  - lwc
  - service-console
  - workspace-api
  - utility-bar
  - tab-management
  - console-developer
inputs:
  - "the LWC bundle that runs inside (or alongside) a Service Console workspace"
  - "the action the component needs to take (open, refresh, close, label, focus)"
  - "whether the component must run in both console and non-console hosts"
outputs:
  - "console-aware LWC that branches on IsConsoleNavigation"
  - "tab lifecycle handlers (open / refresh / close / set-label) wired to user actions"
  - "graceful fallback when the host is not a console app"
  - "utility bar integration if the LWC sits in the utility bar tray"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-15
---

# LWC Console Workspace API

Activate when an LWC needs to manipulate Service Console tabs or the utility bar programmatically — opening a new subtab in response to a button click, refreshing a tab after an external update, setting the tab label to a dynamic record name, closing the current tab when a multi-step action completes, or behaving differently when running inside a console vs. a standard Lightning app. The modern surface is the `lightning/platformWorkspaceApi` and `lightning/platformUtilityBarApi` modules, which replace the Aura-only `lightning:workspaceAPI` and `lightning:utilityBarAPI` for new development.

This skill is the runtime-API counterpart to `admin/service-console-configuration` (which covers declarative Service Console setup) and complements `lwc/lightning-navigation-dead-link-handling` (which handles navigation failures) and `lwc/lwc-cross-tab-state-sync` (which coordinates between browser tabs, not console subtabs).

---

## Before Starting

Gather this context before writing tab-manipulation code:

- **Host app type.** Is the LWC guaranteed to run inside a console app (Service Console, custom console-navigation app), or can it also run in a standard Lightning app (App Builder Home page, Record Page in a non-console app, Experience Cloud)? Console-only callsites can call the workspace API directly; mixed callsites must detect console context first.
- **Where the LWC is mounted.** A workspace tab (primary), a subtab, the utility bar, an overlay/modal, or an Experience Cloud site? `getFocusedTabInfo()` and `getEnclosingTabId()` behave differently for each.
- **The action's transactional boundary.** Tab manipulation after an Apex DML call has subtle ordering issues — `refreshTab()` invalidates the LDS cache but does not re-run wires synchronously. Plan for the user-perceived latency.
- **Aura coexistence.** If the surrounding workspace contains Aura components also using `lightning:workspaceAPI`, the LWC API and the Aura API share the same underlying state but use different module identities. Cross-framework refreshes work, but cross-framework event subscriptions don't.

---

## Core Concepts

### `lightning/platformWorkspaceApi` Surface

The module exports tab-lifecycle and tab-metadata functions, plus a context-detection wire adapter.

```javascript
import {
    openTab,             // open a new primary workspace tab
    openSubtab,          // open a subtab under a specified primary tab
    closeTab,            // close by tabId
    refreshTab,          // re-fetch the tab's underlying record / page; invalidates LDS for that tab
    focusTab,            // bring a tab to the foreground
    getFocusedTabInfo,   // info about the currently focused workspace tab
    getAllTabInfo,       // info about every open tab
    getTabInfo,          // info about a specific tabId
    setTabLabel,         // change the displayed label on the tab
    setTabIcon,          // change the tab icon (SLDS icon path)
    setTabHighlighted,   // visually emphasize the tab (e.g. unread badge)
    getEnclosingTabId,   // tabId of the tab containing the currently-running LWC
    IsConsoleNavigation, // wire adapter that emits true if host is console
    EnclosingTabId       // wire adapter exposing the enclosing tabId
} from 'lightning/platformWorkspaceApi';
```

Each lifecycle function returns a `Promise`. Discovery functions (`getFocusedTabInfo`, etc.) also return promises and resolve to plain JS objects.

### Console Context Detection

`IsConsoleNavigation` is the canonical detection mechanism for "am I in a console?":

```javascript
import { LightningElement, wire } from 'lwc';
import { IsConsoleNavigation } from 'lightning/platformWorkspaceApi';

export default class RecordActions extends LightningElement {
    @wire(IsConsoleNavigation) isConsole;

    handleRowAction() {
        if (this.isConsole) {
            // call openSubtab / refreshTab
        } else {
            // fall back to NavigationMixin.Navigate or imperative action
        }
    }
}
```

`IsConsoleNavigation` is a wire adapter, not a synchronous property. The first render may not have it set; defer console-specific actions to user-triggered handlers or `renderedCallback`.

### Tab Identity

The `tabId` is an opaque string the platform issues per tab open. It is stable across the tab's lifetime but does not survive page reload. Cache it in component state only; do not persist it to record data or URL parameters.

`getEnclosingTabId()` returns the tab containing the calling LWC. From a subtab's LWC, this returns the subtab's id, not the primary tab's id — to get the primary, walk via `getTabInfo(subtabId).parentTabId`.

### Utility Bar API

`lightning/platformUtilityBarApi` mirrors the workspace API for utility-bar-mounted LWCs:

```javascript
import {
    openUtility,
    minimizeUtility,
    getEnclosingUtilityId,
    getUtilityInfo,
    setUtilityIcon,
    setUtilityLabel,
    setUtilityHighlighted,
    EnclosingUtilityId,
    IsUtilityOpen
} from 'lightning/platformUtilityBarApi';
```

A utility-bar LWC can open or minimize itself, change its own icon/label, and subscribe to its own open/closed state. It cannot directly manipulate workspace tabs — to bridge to the workspace, import `lightning/platformWorkspaceApi` alongside.

### Refresh Semantics

`refreshTab(tabId)` invalidates the LDS cache for records visible in that tab and triggers re-render. It does not return a promise that resolves "when re-render is complete" — it returns a promise that resolves "when the refresh signal has been dispatched." Wires reactivate asynchronously after.

For "refresh THIS tab", a record-page LWC commonly calls:

```javascript
refreshTab(await getEnclosingTabId());
```

For "refresh a sibling subtab" (e.g., subtab A updates an Account; subtab B for that same Account should re-render), iterate `getAllTabInfo()` and refresh matching subtabs by `recordId`.

---

## Common Patterns

### Pattern: Open subtab from a row action

**When to use:** A list LWC on a console primary tab; clicking a row should open the record in a subtab without leaving the current primary.

**How it works:**

```javascript
import { LightningElement, wire } from 'lwc';
import {
    IsConsoleNavigation,
    openSubtab,
    getFocusedTabInfo
} from 'lightning/platformWorkspaceApi';
import { NavigationMixin } from 'lightning/navigation';

export default class CaseList extends NavigationMixin(LightningElement) {
    @wire(IsConsoleNavigation) isConsole;

    async handleRowClick(event) {
        const recordId = event.detail.row.Id;
        if (this.isConsole) {
            const focused = await getFocusedTabInfo();
            await openSubtab(focused.tabId, {
                pageReference: {
                    type: 'standard__recordPage',
                    attributes: { recordId, objectApiName: 'Case', actionName: 'view' }
                },
                focus: true
            });
        } else {
            this[NavigationMixin.Navigate]({
                type: 'standard__recordPage',
                attributes: { recordId, objectApiName: 'Case', actionName: 'view' }
            });
        }
    }
}
```

**Why not the alternative:** Calling `NavigationMixin.Navigate` in a console primary tab opens a *new* primary tab, not a subtab — which loses the user's place. The workspace API gives the correct subtab placement.

### Pattern: Dynamic tab label from record data

**When to use:** A record page LWC where the tab label should show meaningful record context (e.g., "Case 00001234 — High Priority").

**How it works:**

```javascript
import { LightningElement, wire, api } from 'lwc';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';
import {
    getEnclosingTabId,
    setTabLabel,
    setTabIcon,
    IsConsoleNavigation
} from 'lightning/platformWorkspaceApi';
import CASE_NUMBER from '@salesforce/schema/Case.CaseNumber';
import CASE_PRIORITY from '@salesforce/schema/Case.Priority';

export default class CaseTabLabel extends LightningElement {
    @api recordId;
    @wire(IsConsoleNavigation) isConsole;

    @wire(getRecord, { recordId: '$recordId', fields: [CASE_NUMBER, CASE_PRIORITY] })
    async wiredCase({ data }) {
        if (!data || !this.isConsole) return;
        const number = getFieldValue(data, CASE_NUMBER);
        const priority = getFieldValue(data, CASE_PRIORITY);
        const tabId = await getEnclosingTabId();
        await setTabLabel(tabId, `Case ${number} — ${priority}`);
        if (priority === 'High') {
            await setTabIcon(tabId, 'standard:case', { iconAlt: 'High priority' });
        }
    }
}
```

**Why not the alternative:** Letting the platform default tab label (which uses the record's Name field) misses contextual signals like priority. Dynamic labels reduce agent cognitive load when switching between many tabs.

### Pattern: Refresh tab after an Apex DML call

**When to use:** An LWC button updates a record via imperative Apex; the workspace tab should re-fetch to reflect the change.

**How it works:**

```javascript
import { LightningElement, wire, api } from 'lwc';
import {
    getEnclosingTabId,
    refreshTab,
    IsConsoleNavigation
} from 'lightning/platformWorkspaceApi';
import updateCase from '@salesforce/apex/CaseController.markResolved';

export default class CaseResolveButton extends LightningElement {
    @api recordId;
    @wire(IsConsoleNavigation) isConsole;

    async handleResolve() {
        await updateCase({ caseId: this.recordId });
        if (this.isConsole) {
            const tabId = await getEnclosingTabId();
            await refreshTab(tabId);
        }
        // Outside console: rely on a wired record + refreshApex pattern instead.
    }
}
```

**Why not the alternative:** Mutating a record via imperative Apex bypasses LDS notification. Without `refreshTab` (in console) or `refreshApex` (outside), the surrounding components show stale values until the user clicks the platform refresh icon.

### Pattern: Utility-bar quick-action launcher

**When to use:** A utility-bar LWC offers quick actions; clicking one should open the affected record in a workspace subtab.

**How it works:**

```javascript
import { LightningElement } from 'lwc';
import { openTab, getFocusedTabInfo, openSubtab } from 'lightning/platformWorkspaceApi';
import { minimizeUtility } from 'lightning/platformUtilityBarApi';

export default class QuickRecordOpener extends LightningElement {
    async handleOpenAsSubtab(event) {
        const recordId = event.target.dataset.recordId;
        const focused = await getFocusedTabInfo();
        const pageReference = {
            type: 'standard__recordPage',
            attributes: { recordId, objectApiName: 'Account', actionName: 'view' }
        };
        if (focused && focused.tabId) {
            await openSubtab(focused.tabId, { pageReference, focus: true });
        } else {
            await openTab({ pageReference, focus: true });
        }
        await minimizeUtility();
    }
}
```

**Why not the alternative:** Always opening a new primary tab clutters the workspace; respecting the focused-tab context places the record where the agent is already working.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Component runs in both console and non-console hosts | Wire `IsConsoleNavigation` and branch on its boolean | Avoids `lightning/platformWorkspaceApi` throw when running outside console |
| Need the tab containing the running LWC | `getEnclosingTabId()` | The tab id is stable for the tab's lifetime |
| Need the currently-focused tab (may differ from enclosing) | `getFocusedTabInfo()` | Use when opening subtabs from a utility bar or modal |
| Open a record in the same workspace context | `openSubtab(focusedTabId, ...)` | Preserves the agent's primary tab |
| Open a new primary | `openTab(...)` | When the new record is a separate work unit |
| Refresh "this" tab after a write | `refreshTab(await getEnclosingTabId())` | LDS-aware invalidation; sibling components re-wire |
| Refresh a sibling tab showing the same record | Iterate `getAllTabInfo()`, match `recordId`, refresh | No built-in "refresh all tabs for record X" |
| Dynamic tab labels | `setTabLabel(tabId, ...)` from a record wire | Decreases cognitive switching cost for agents |
| LWC sits in the utility bar | `lightning/platformUtilityBarApi` for self-state, `lightning/platformWorkspaceApi` for tab actions | Two modules cover the two surfaces |
| Aura component coexists in the same workspace | Both APIs share state; refresh and label changes cross frameworks | Don't mix event subscriptions across frameworks |

---

## Recommended Workflow

1. **Confirm host posture.** Will the LWC run only inside a console app? Add `IsConsoleNavigation` even if so — non-console preview surfaces (App Builder, Experience Cloud staging) will exercise the no-console path.
2. **Choose tab actions.** From the user story, list the precise tab actions (open, focus, refresh, close, label, icon, highlight) the component must perform. Each maps to one workspace-API call.
3. **Import only what you use.** `import { openSubtab, refreshTab } from 'lightning/platformWorkspaceApi';` is preferable to a namespace import — it keeps the bundle's static-analysis dependencies clean.
4. **Wire `IsConsoleNavigation` and branch.** Every console-specific action sits behind `if (this.isConsole) { ... } else { ...fallback... }`. The fallback is usually `NavigationMixin.Navigate`, `refreshApex`, or a toast.
5. **Test in App Builder preview** (non-console) AND in the actual Service Console. App Builder catches the no-console fallback; the Service Console catches subtab parentage and focus state.
6. **Handle promise rejections.** Every workspace-API call returns a promise; wrap in `try { ... } catch (e) { ... }` and degrade gracefully — Service Console upgrades and edge cases can reject calls that worked yesterday.
7. **Document tab lifecycle in the component header.** A reader should know which calls the component makes (open / refresh / close / label) without grepping the JS.

---

## Review Checklist

- [ ] `IsConsoleNavigation` wired and used to gate every workspace-API call
- [ ] Non-console fallback path explicit (no silent no-op)
- [ ] Each workspace-API promise has rejection handling
- [ ] `getEnclosingTabId` / `getFocusedTabInfo` used correctly for the lifecycle action (enclosing for "this tab"; focused for "wherever the user is")
- [ ] `refreshTab` paired with the DML/imperative-Apex write it should reflect
- [ ] Dynamic labels source from a wire (not from imperative call results that won't re-evaluate)
- [ ] Tab id never persisted across page reload
- [ ] Jest test covers both `isConsole === true` and `isConsole === false` branches
- [ ] Component header documents which tab lifecycle calls it makes
- [ ] No Aura-only `lightning:workspaceAPI` event subscriptions left in the bundle (use module imports)

---

## Salesforce-Specific Gotchas

1. **`lightning/platformWorkspaceApi` throws outside a console.** Calling `openSubtab` from a standard Lightning app surface raises an error. Always gate on `IsConsoleNavigation` or a try/catch.
2. **`IsConsoleNavigation` is a wire adapter, not a property.** First render may have `this.isConsole === undefined`. Defer console-only actions to user handlers or `renderedCallback`, not `connectedCallback`.
3. **`refreshTab` doesn't await re-render.** It resolves when the refresh has been dispatched, not when wires have re-evaluated. Tests that assert post-refresh DOM state must await one microtask tick after.
4. **`getEnclosingTabId` and `getFocusedTabInfo` can differ.** A subtab LWC's enclosing is the subtab; the focused tab is whatever the user is on (could be a different primary). Pick the right one for the action.
5. **Tab IDs are opaque and ephemeral.** Persisting a tab id to record data, URL params, or browser storage is a bug — it does not survive reload.
6. **Aura and LWC workspace APIs share state but are different module identities.** Refresh and label changes work cross-framework; subscribing to Aura `lightning:workspaceAPI` events from LWC does not.
7. **`refreshTab` invalidates LDS for the tab's host record but not for unrelated records the tab also displays.** A subtab showing Case AND its parent Account may refresh Case but show stale Account. Pair with `refreshApex` on imperative-Apex wires when needed.
8. **`setTabLabel` is not throttled.** Setting it on every keystroke causes flicker; debounce to one update per record change.
9. **Console-related URL hash navigation differs in Lightning Experience.** `window.location.hash` changes do not behave like a normal SPA inside the console iframe stack — rely on the workspace API for tab placement.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Console-aware LWC bundle | JS, HTML, meta-xml with `IsConsoleNavigation` gating and fallback path |
| Jest test pair | One test asserting console-path behavior, one asserting non-console-path |
| Tab lifecycle documentation | Component header listing which workspace-API calls the component makes |
| Refresh/wire ordering note | Comment on each `refreshTab` documenting which wired records will re-evaluate |

---

## Related Skills

- `admin/service-console-configuration` — Declarative setup of the Service Console app (workspace tabs, utility bar, navigation rules)
- `lwc/lightning-navigation-dead-link-handling` — Handling navigation failures (deleted records, missing pages) that interact with console subtab fallbacks
- `lwc/lwc-cross-tab-state-sync` — BroadcastChannel between browser tabs (different surface from console subtabs)
- `lwc/lwc-navigation-mixin` — `NavigationMixin.Navigate` patterns for non-console hosts; the typical fallback when `IsConsoleNavigation` is false
- `lwc/lwc-wire-refresh-patterns` — `refreshApex` and wire-reactivity patterns that complement `refreshTab` after imperative writes
