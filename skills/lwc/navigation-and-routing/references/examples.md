# Examples - Navigation And Routing

Full deployable bundles, the Jest mock and `package.xml` live in
[`code-examples.md`](./code-examples.md). The examples here are the decision moments.

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

**Why it works:** The component expresses intent rather than owning URL shape, which is exactly what the navigation service is for. `objectApiName` is optional in Lightning Experience but required on record page references in Experience Builder LWR sites, so sending it unconditionally is what makes this same handler survive a move into a site (`reference-page-reference-type`, L22193–22194).

---

## Example 2: Deep-Linkable Filter State

**Context:** A dashboard helper component needs a URL-driven view mode so users can bookmark `open`, `mine`, or `escalated`.

**Problem:** The first draft reads `window.location.search` directly and breaks when URL handling changes.

**Solution:**

```js
import { LightningElement, wire } from 'lwc';
import { CurrentPageReference, NavigationMixin } from 'lightning/navigation';

export default class CaseDashboardState extends NavigationMixin(LightningElement) {
    currentPageReference;

    @wire(CurrentPageReference)
    setPageReference(pageRef) {
        this.currentPageReference = pageRef;
    }

    get currentView() {
        return this.currentPageReference?.state?.c__view ?? 'open';
    }

    navigateToView(viewName) {
        this[NavigationMixin.Navigate](
            {
                type: 'standard__component',
                attributes: {
                    // matches the bundle name; case-sensitive
                    componentName: 'c__caseDashboardHost'
                },
                state: {
                    c__view: viewName // string, always
                }
            },
            true // replace: a view toggle is not a new history entry
        );
    }
}
```

**Why it works:** URL state becomes an explicit contract and remains readable through the supported wire adapter. Reading through a getter over `currentPageReference` rather than caching into a field on the wire callback is what makes the component react to a bookmark, a Back button and its own navigation identically — the view is not rerendered by a query-string change alone (`use-navigate-add-params-url`, L10144).

**Prerequisite this example depends on:** `standard__component` only resolves if `caseDashboardHost` declares the `lightning__UrlAddressable` target in its own `.js-meta.xml`. Without it there is no destination, and that target is unsupported in Experience Builder sites (`targets-lightning-url-addressable`, L19402–19406).

---

## Example 3: Picking The Page Type Before Writing Any Attributes

**Context:** A row-action menu on a Case list has five destinations, and the author is filling in PageReference objects one at a time.

**Problem:** Type selection is being driven by whichever attributes happen to be in scope, so `objectApiName` in a variable pulls everything toward `standard__objectPage`.

**Solution:** Resolve the *unit of navigation* first, then fill attributes from the type's own table. Each row below is a complete, valid PageReference.

```json
[
  {
    "unit": "one record",
    "type": "standard__recordPage",
    "attributes": { "recordId": "500xx0000000001AAA", "objectApiName": "Case", "actionName": "view" }
  },
  {
    "unit": "an object's list view",
    "type": "standard__objectPage",
    "attributes": { "objectApiName": "Case", "actionName": "list" },
    "state": { "filterName": "My_Open_Cases" }
  },
  {
    "unit": "a related list on one record",
    "type": "standard__recordRelationshipPage",
    "attributes": {
      "recordId": "500xx0000000001AAA",
      "objectApiName": "Case",
      "relationshipApiName": "CaseComments",
      "actionName": "view"
    }
  },
  {
    "unit": "a custom tab",
    "type": "standard__navItemPage",
    "attributes": { "apiName": "Case_Console" }
  },
  {
    "unit": "somewhere off-platform",
    "type": "standard__webPage",
    "attributes": { "url": "https://status.salesforce.com" }
  }
]
```

**Why it works:** Every attribute above comes from the per-type table rather than from what the calling code already had in hand. Note the two that catch people: `standard__recordRelationshipPage` supports only `actionName: "view"` and needs `relationshipApiName`; `standard__navItemPage` takes the tab *name*, so a tab labelled "Case Console" is `Case_Console` (`reference-page-reference-type`, L22166–22208; `use-config-custom-tab`, L7989).

**UNVERIFIED (2026-09-05):** the literal type token `standard__recordRelationshipPage` is not printed in the extracted guide text — the reference page documents the "Record Relationship Page" type and its attribute table, but the code sample carrying the token string was stripped during extraction. The attributes are grounded; confirm the exact token before deploying.

---

## Anti-Pattern: Mixing `window.location` With NavigationMixin

**What practitioners do:** One handler uses `NavigationMixin.Navigate`, another uses `window.location`, and a third builds an anchor manually.

**What goes wrong:** The component now has multiple routing contracts. They drift, behave differently across containers, and are hard to test — `getNavigateCalledWith()` sees only the calls that went through the navigation service, so the `window.location` path has no assertion covering it at all.

**Correct approach:** Build one PageReference model and use it for both navigation and generated URLs. `scripts/check_navigation_and_routing.py` flags the mixed shape directly.
