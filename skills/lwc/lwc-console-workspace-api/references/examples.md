# Examples — LWC Console Workspace API

## Example 1: Refresh-after-write in a console-aware action button

**Context:** A `CaseResolveButton` LWC sits on a Case record page that may render inside Service Console (most of the time) or inside an App Builder Home Page preview (during admin configuration). The button calls imperative Apex to set `Case.Status = 'Resolved'` and needs the surrounding record-page components to reflect the change immediately.

**Problem:** Imperative Apex calls don't notify LDS. Without an explicit refresh, the page-layout component, the related-list LWC, and any neighboring custom LWCs continue to show `Status = 'New'` until the agent clicks the platform refresh icon. The agent doesn't trust the button.

**Solution:**

```javascript
// caseResolveButton.js
import { LightningElement, wire, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import {
    IsConsoleNavigation,
    getEnclosingTabId,
    refreshTab
} from 'lightning/platformWorkspaceApi';
import markResolved from '@salesforce/apex/CaseController.markResolved';

export default class CaseResolveButton extends LightningElement {
    @api recordId;
    @wire(IsConsoleNavigation) isConsole;

    async handleClick() {
        try {
            await markResolved({ caseId: this.recordId });

            if (this.isConsole) {
                const tabId = await getEnclosingTabId();
                await refreshTab(tabId);
            }

            this.dispatchEvent(new ShowToastEvent({
                title: 'Resolved',
                message: 'Case marked as resolved.',
                variant: 'success'
            }));
        } catch (e) {
            this.dispatchEvent(new ShowToastEvent({
                title: 'Could not resolve',
                message: e?.body?.message ?? e?.message ?? 'Unknown error',
                variant: 'error'
            }));
        }
    }
}
```

**Why it works:** `IsConsoleNavigation` is wired, so when the component renders outside a console (App Builder preview, Experience Cloud), the workspace-API call is skipped — preventing the `lightning/platformWorkspaceApi` throw that would occur in non-console hosts. Inside a console, `refreshTab(getEnclosingTabId())` re-runs the tab's LDS-backed wires, refreshing the record-page neighborhood without forcing a full page reload.

---

## Example 2: Opening a subtab from a custom list in the focused primary

**Context:** A custom list LWC (`PendingApprovalsList`) sits in the Service Console utility bar. The user is working on Case primary tabs throughout the day. When they click a pending approval, the related record should open as a subtab under whichever Case is currently focused.

**Problem:** Calling `NavigationMixin.Navigate` from the utility bar opens a new *primary* tab — losing the user's place on their current Case. The agent doesn't want a primary-tab explosion; they want the approval record as a subtab under the Case they're on.

**Solution:**

```javascript
// pendingApprovalsList.js
import { LightningElement } from 'lwc';
import {
    getFocusedTabInfo,
    openSubtab,
    openTab
} from 'lightning/platformWorkspaceApi';
import { minimizeUtility } from 'lightning/platformUtilityBarApi';

export default class PendingApprovalsList extends LightningElement {
    async handleRowClick(event) {
        const recordId = event.currentTarget.dataset.recordId;
        const pageReference = {
            type: 'standard__recordPage',
            attributes: {
                recordId,
                objectApiName: 'Approval_Request__c',
                actionName: 'view'
            }
        };

        try {
            const focused = await getFocusedTabInfo();
            if (focused?.tabId && !focused.isSubtab) {
                await openSubtab(focused.tabId, { pageReference, focus: true });
            } else if (focused?.parentTabId) {
                // Already focused inside a subtab — attach to its parent primary
                await openSubtab(focused.parentTabId, { pageReference, focus: true });
            } else {
                // No primary in focus — open as new primary
                await openTab({ pageReference, focus: true });
            }
            await minimizeUtility();
        } catch (e) {
            // Console may be in an interim state during agent shift change
            // Fall back to a toast prompting manual navigation.
            console.error('PendingApprovalsList.handleRowClick failed', e);
        }
    }
}
```

**Why it works:** `getFocusedTabInfo()` returns the current focused tab including a `parentTabId` field when the focus is on a subtab. The component walks from focus → enclosing primary, and opens the new approval as a subtab under that primary — preserving the agent's place in the workspace. The fall-through to `openTab` covers the cold-start case where no primary is open yet. `minimizeUtility()` returns the utility bar to its minimized state so the new subtab is visible.

---

## Example 3: Dynamic tab label and icon synced to record priority

**Context:** A `CaseTabBadge` LWC is placed on the Case record page in Service Console. As soon as the record loads — or its priority changes via inline edit — the workspace tab label should update to include the priority, and a high-priority case should get a red badge icon.

**Problem:** Default tab labels show only `Case Number`. Agents triaging 8–12 open cases can't quickly tell which is High vs. Medium without clicking each tab. Inline edits don't propagate to the tab label.

**Solution:**

```javascript
// caseTabBadge.js
import { LightningElement, wire, api } from 'lwc';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';
import {
    IsConsoleNavigation,
    getEnclosingTabId,
    setTabLabel,
    setTabIcon,
    setTabHighlighted
} from 'lightning/platformWorkspaceApi';
import CASE_NUMBER from '@salesforce/schema/Case.CaseNumber';
import CASE_PRIORITY from '@salesforce/schema/Case.Priority';
import CASE_STATUS from '@salesforce/schema/Case.Status';

const ICON_BY_PRIORITY = {
    'High': 'standard:case',
    'Medium': 'standard:case',
    'Low': 'standard:case'
};

export default class CaseTabBadge extends LightningElement {
    @api recordId;
    @wire(IsConsoleNavigation) isConsole;

    @wire(getRecord, {
        recordId: '$recordId',
        fields: [CASE_NUMBER, CASE_PRIORITY, CASE_STATUS]
    })
    wiredCase({ data, error }) {
        if (error || !data || !this.isConsole) return;
        const number = getFieldValue(data, CASE_NUMBER);
        const priority = getFieldValue(data, CASE_PRIORITY);
        const status = getFieldValue(data, CASE_STATUS);

        // Defer to next tick to avoid a re-entrant wire/dom-update collision
        Promise.resolve().then(async () => {
            try {
                const tabId = await getEnclosingTabId();
                await setTabLabel(tabId, `Case ${number} — ${priority}`);
                await setTabIcon(tabId, ICON_BY_PRIORITY[priority] ?? 'standard:case', {
                    iconAlt: `${priority} priority`
                });
                await setTabHighlighted(tabId, priority === 'High' && status !== 'Closed', {
                    pulse: priority === 'High',
                    state: 'error'
                });
            } catch (e) {
                // Non-console preview / utility-bar host — silently skip
            }
        });
    }
}
```

**Why it works:** The wire re-fires whenever `Priority` or `Status` changes (inline edit, related update, Apex DML followed by `refreshTab`). The `Promise.resolve().then(...)` defers tab mutation by one microtask, avoiding a re-entrant collision with the wire reactivity cycle. The `setTabHighlighted` call uses the High-priority Open state as a "pulse-red" signal that agents can spot from across the workspace. Outside a console, the workspace-API calls throw — the `try/catch` keeps the wire callback silent.

---

## Anti-Pattern: Calling `openSubtab` without checking `IsConsoleNavigation`

**What practitioners do:**

```javascript
import { openSubtab } from 'lightning/platformWorkspaceApi';

handleClick() {
    openSubtab(this.someTabId, { pageReference });
}
```

**What goes wrong:** Inside a console it works. Inside App Builder preview, an Experience Cloud site, or a standard Lightning app, `openSubtab` rejects with a "not running inside a console app" error. The component silently fails (if the promise rejection is unhandled) or surfaces a console error the agent can't act on. Worse, the component appears to work for the admin (who develops in console) but is broken for any user on a non-console surface.

**Correct approach:** Wire `IsConsoleNavigation` and gate every workspace-API call behind it. Provide an explicit fallback — usually `NavigationMixin.Navigate` to the same `pageReference`. Test both branches via Jest.
