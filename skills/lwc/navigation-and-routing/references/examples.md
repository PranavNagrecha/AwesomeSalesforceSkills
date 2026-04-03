# Examples - Navigation And Routing

## Example 1: Navigate To A Saved Record With A PageReference

**Context:** A create form component saves a Contact and should send the user to the new record after success.

**Problem:** The original component concatenates `/lightning/r/Contact/` plus the returned ID. It works in desktop testing but the team wants a container-safe pattern.

**Solution:**

```js
import { NavigationMixin } from 'lightning/navigation';

export default class ContactCreate extends NavigationMixin(LightningElement) {
    handleSuccess(event) {
        this[NavigationMixin.Navigate]({
            type: 'standard__recordPage',
            attributes: {
                recordId: event.detail.id,
                objectApiName: 'Contact',
                actionName: 'view'
            }
        });
    }
}
```

**Why it works:** The component expresses intent rather than owning URL shape, which is exactly what the navigation service is for.

---

## Example 2: Deep-Linkable Filter State

**Context:** A dashboard helper component needs a URL-driven view mode so users can bookmark `open`, `mine`, or `escalated`.

**Problem:** The first draft reads `window.location.search` directly and breaks when URL handling changes.

**Solution:**

```js
import { LightningElement, wire } from 'lwc';
import { CurrentPageReference, NavigationMixin } from 'lightning/navigation';

export default class CaseDashboardState extends NavigationMixin(LightningElement) {
    currentView = 'open';

    @wire(CurrentPageReference)
    setPageReference(pageRef) {
        this.currentView = pageRef?.state?.c__view || 'open';
    }

    navigateToView(viewName) {
        this[NavigationMixin.Navigate]({
            type: 'standard__component',
            attributes: {
                componentName: 'c__CaseDashboardHost'
            },
            state: {
                c__view: viewName
            }
        });
    }
}
```

**Why it works:** URL state becomes an explicit contract and remains readable through the supported wire adapter.

---

## Anti-Pattern: Mixing `window.location` With NavigationMixin

**What practitioners do:** One handler uses `NavigationMixin.Navigate`, another uses `window.location`, and a third builds an anchor manually.

**What goes wrong:** The component now has multiple routing contracts. They drift, behave differently across containers, and are hard to test.

**Correct approach:** Build one PageReference model and use it for both navigation and generated URLs.
