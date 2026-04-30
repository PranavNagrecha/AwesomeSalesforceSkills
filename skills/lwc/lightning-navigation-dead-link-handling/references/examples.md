# Examples — Lightning Navigation Dead-Link Handling

## Example 1: Pre-flight check before record navigation

**Context:** "Open Related Account" button on a Case detail. The Case record may persist after the related Account is deleted.

**Problem:** Clicking the button navigates to the deleted Account; user lands on "Insufficient privileges" with no context.

**Solution:**

```javascript
// openRelatedAccountButton.js
import { LightningElement, api, wire } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';
import { NavigationMixin } from 'lightning/navigation';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class OpenRelatedAccountButton extends NavigationMixin(LightningElement) {
    @api accountId;
    accountAccessible = false;

    @wire(getRecord, { recordId: '$accountId', fields: ['Account.Id'] })
    handle({ data, error }) {
        if (data) {
            this.accountAccessible = true;
        } else if (error) {
            this.accountAccessible = false;
        }
    }

    handleClick() {
        if (!this.accountAccessible) {
            this.dispatchEvent(new ShowToastEvent({
                title: 'Account unavailable',
                message: 'The related account no longer exists or you no longer have access. Search for it from the Accounts tab.',
                variant: 'warning'
            }));
            return;
        }
        this[NavigationMixin.Navigate]({
            type: 'standard__recordPage',
            attributes: { recordId: this.accountId, objectApiName: 'Account', actionName: 'view' }
        });
    }
}
```

**Why it works:** The wire's success path enables the button; the failure path provides a usable next action ("search for it") instead of a dead end.

---

## Example 2: Console subtab fallback to a search

**Context:** Service Console subtab with a record link from an email template. The email is two days old; the record has been deleted in the meantime.

**Problem:** Opening the subtab shows a blank tab and the user has no way to find a replacement.

**Solution:**

```javascript
import { LightningElement, api, wire } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';
import { NavigationMixin } from 'lightning/navigation';
import { IsConsoleNavigation, openSubtab } from 'lightning/platformWorkspaceApi';

export default class CaseDeepLink extends NavigationMixin(LightningElement) {
    @api recordId;
    @api caseSubject;

    @wire(IsConsoleNavigation) isConsole;

    @wire(getRecord, { recordId: '$recordId', fields: ['Case.Id'] })
    record;

    async connectedCallback() {
        // Wait one tick for the wire
        await Promise.resolve();
        if (this.record?.error) {
            if (this.isConsole) {
                openSubtab({
                    pageReference: {
                        type: 'standard__objectPage',
                        attributes: { objectApiName: 'Case', actionName: 'home' },
                        state: { searchTerm: this.caseSubject }
                    }
                });
            } else {
                this[NavigationMixin.Navigate]({
                    type: 'standard__objectPage',
                    attributes: { objectApiName: 'Case', actionName: 'home' }
                });
            }
            return;
        }
        if (this.record?.data) {
            this[NavigationMixin.Navigate]({
                type: 'standard__recordPage',
                attributes: { recordId: this.recordId, objectApiName: 'Case', actionName: 'view' }
            });
        }
    }
}
```

**Why it works:** Failure mode produces a *useful* alternative — opening the Case home with the original subject pre-filled in search — rather than a blank console subtab.

---

## Anti-Pattern: catching `.catch()` on Navigate as the only failure path

**What practitioners do:**

```javascript
this[NavigationMixin.Navigate](pageRef).catch(() => {
    this.showToast('Could not open');
});
```

**What goes wrong:** `Navigate` resolves successfully as soon as the framework dispatches the navigation; the destination's render-time error is in a different async boundary. The `.catch` block essentially never fires for the failures users actually hit.

**Correct approach:** Validate the target *before* calling `Navigate`. Treat the `.catch` only as defense-in-depth for transport-level failures.
