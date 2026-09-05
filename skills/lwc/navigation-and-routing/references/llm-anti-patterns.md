# LLM Anti-Patterns — Navigation and Routing

Common mistakes AI coding assistants make when generating or advising on LWC navigation with NavigationMixin.
These patterns help the consuming agent self-check its own output.
Each detection hint corresponds to a rule in `scripts/check_navigation_and_routing.py`.

## Anti-Pattern 1: Using window.location instead of NavigationMixin

**What the LLM generates:**

```javascript
handleViewRecord() {
    window.location.href = `/lightning/r/Account/${this.recordId}/view`;
}
```

**Why it happens:** `window.location` is the most common JavaScript navigation pattern. LLMs default to it because it appears in generic web training data. On the platform, the supported way to navigate in Lightning Experience, Experience Builder sites and the Salesforce mobile app is the navigation service, `lightning/navigation` (`use-navigate`, L10077). A hand-built path also gives up the URL-format insulation a PageReference provides (`use-navigate-basic`, L10089), and in an LWR site under Lightning Locker the global `window` object cannot be referenced at all — the guide's own language-picker sample carries that warning (`create-community-info`, L3910–3911).

**Correct pattern:**

```javascript
import { NavigationMixin } from 'lightning/navigation';

export default class MyComponent extends NavigationMixin(LightningElement) {
    handleViewRecord() {
        this[NavigationMixin.Navigate]({
            type: 'standard__recordPage',
            attributes: {
                recordId: this.recordId,
                objectApiName: 'Account',
                actionName: 'view'
            }
        });
    }
}
```

**Detection hint:** `window.location`, `location.assign`, `window.open`, or hardcoded `/lightning/` URLs in LWC JavaScript.

---

## Anti-Pattern 2: Forgetting to extend NavigationMixin before using Navigate

**What the LLM generates:**

```javascript
import { LightningElement } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';

export default class MyComponent extends LightningElement {
    handleNav() {
        this[NavigationMixin.Navigate]({ /* ... */ });
        // Nothing to call — Navigate was never added to this class
    }
}
```

**Why it happens:** LLMs import `NavigationMixin` but forget to apply it in the `extends` clause. The navigation service adds `Navigate` and `GenerateUrl` as APIs *on the component's class*, and the documented sequence is: import the function, then apply it to the component's base class (`use-navigate-basic`, L10100, L10105–10106). The import alone adds nothing.

**Correct pattern:**

```javascript
export default class MyComponent extends NavigationMixin(LightningElement) {
    handleNav() {
        this[NavigationMixin.Navigate]({
            type: 'standard__recordPage',
            attributes: {
                recordId: this.recordId,
                objectApiName: 'Account',
                actionName: 'view'
            }
        });
    }
}
```

Note the sibling constraint the same fix does *not* cover: `NavigationMixin` may be used only with a component that extends `LightningElement`, and cannot be applied to a component that extends `LightningModal` (`use-navigate-modal`, L10258–10259). From a modal, dispatch the PageReference to the opening parent instead.

**Detection hint:** `NavigationMixin.Navigate` used in a class that extends `LightningElement` without wrapping it in `NavigationMixin()`.

---

## Anti-Pattern 3: Using the wrong PageReference type for the unit of navigation

**What the LLM generates:**

```javascript
// "Edit this row" — but pointed at the object, with a record id bolted on
this[NavigationMixin.Navigate]({
    type: 'standard__objectPage',
    attributes: {
        objectApiName: 'Case',
        actionName: 'edit',
        recordId: row.Id
    }
});
```

**Why it happens:** The code already has `objectApiName` in scope, so `standard__objectPage` looks like the natural home for anything about that object. The reference tables say otherwise: `standard__objectPage` takes `actionName` values `home`, `list` and `new` and does not list `recordId` among its attributes, while record-level actions (`clone`, `edit`, `view`) plus `recordId` belong to `standard__recordPage` (`reference-page-reference-type`, L22171–22179, L22189–22195). A `lightning-datatable` sample inside the guide itself uses the mixed shape above (`data-table-tree-grid`, L5637–5643), so it is well represented in training data.

**Correct pattern:**

```javascript
// A record → standard__recordPage
this[NavigationMixin.Navigate]({
    type: 'standard__recordPage',
    attributes: { recordId: row.Id, objectApiName: 'Case', actionName: 'edit' }
});

// An object's list view → standard__objectPage, filterName in state
this[NavigationMixin.Navigate]({
    type: 'standard__objectPage',
    attributes: { objectApiName: 'Case', actionName: 'list' },
    state: { filterName: 'My_Open_Cases' }
});
```

**Detection hint:** `type: 'standard__recordPage'` missing `recordId` or `actionName`; `type: 'standard__objectPage'` carrying a `recordId` or a record-level `actionName`.

---

## Anti-Pattern 4: Custom state keys without a namespace prefix

**What the LLM generates:**

```javascript
this[NavigationMixin.Navigate]({
    type: 'standard__component',
    attributes: { componentName: 'c__myPage' },
    state: {
        mode: 'edit',
        page: 2
    }
});
```

**Why it happens:** LLMs use plain key names and native JavaScript types. Two documented rules are broken. First, `state` properties must use a namespace prefix followed by two underscores — `c__` outside a managed package, the package namespace inside one (`use-navigate-add-params-url`, L10139; `reference-page-reference-type`, L22127). Second, because the key-value pairs are serialized to URL query parameters, every value must be a string, and consuming code is responsible for parsing it back into its proper format (L10140–10141).

**Correct pattern:**

```javascript
this[NavigationMixin.Navigate]({
    type: 'standard__component',
    attributes: { componentName: 'c__myPage' },
    state: {
        c__mode: 'edit',
        c__page: '2'   // string, not number
    }
});
```

Un-namespaced keys are legal only where the platform defines them — `filterName` and `defaultFieldValues` on `standard__objectPage`, `nooverride` on record and object pages, `uid` on `standard__component`, `recordId` on `standard__quickAction` (`reference-page-reference-type`, L22177–22179, L22186–22187, L22198; `use-navigate-url-addressable`, L10249).

**Detection hint:** a `state:` object with keys that do not start with a namespace prefix and are not on the platform list, or values that are not string literals.

---

## Anti-Pattern 5: Treating the GenerateUrl result as a synchronous string

**What the LLM generates:**

```javascript
connectedCallback() {
    this.recordUrl = this[NavigationMixin.GenerateUrl]({
        type: 'standard__recordPage',
        attributes: { recordId: this.recordId, actionName: 'view' }
    });
}
```

```html
<a href="javascript:void(0)" onclick={handleNav}>View Record</a>
```

**Why it happens:** Two failures usually travel together. `GenerateUrl` returns a *promise* that resolves to the URL, so the assignment above binds a Promise object into the template (`use-navigate-basic`, L10103–10104). And when the href turns out useless, the LLM falls back to `javascript:void(0)` with an onclick — which throws away the copy-link and open-in-new-window behaviour the guide's own anchor example exists to provide (L10104, L10109).

**Correct pattern:**

```javascript
connectedCallback() {
    this[NavigationMixin.GenerateUrl](this.recordPageRef).then((url) => {
        this.recordUrl = url;
    });
}

handleNav(evt) {
    evt.preventDefault();
    evt.stopPropagation();
    this[NavigationMixin.Navigate](this.recordPageRef);
}
```

```html
<a href={recordUrl} onclick={handleNav}>View Record</a>
```

**Detection hint:** a `GenerateUrl` call whose result is assigned or returned without `.then(...)` or `await`; an `<a>` with `href="javascript:void(0)"` or `href="#"` next to an onclick that calls `Navigate`.

---

## Anti-Pattern 6: Hardcoding Experience Cloud site paths into standard__webPage

**What the LLM generates:**

```javascript
handleNavigate() {
    this[NavigationMixin.Navigate]({
        type: 'standard__webPage',
        attributes: {
            url: '/mysite/s/account/' + this.recordId
        }
    });
}
```

**Why it happens:** LLMs hardcode site paths because they do not know the site prefix at generation time. Beyond the brittleness, `standard__webPage` in an Aura-based Experience Builder site applies site-specific processing to certain Salesforce URLs — `/apex/` URLs are translated to `/sfdcpage/` and the page is embedded in an iframe (`reference-page-reference-type`, L22216).

**Correct pattern:**

```javascript
// Internal record in a site → standard__recordPage, with objectApiName
// always supplied (it is required in LWR sites, optional elsewhere).
this[NavigationMixin.Navigate]({
    type: 'standard__recordPage',
    attributes: {
        recordId: this.recordId,
        objectApiName: 'Account',
        actionName: 'view'   // clone and edit are not supported in sites
    }
});
```

Reserve `standard__webPage` for URLs the platform does not own. If you genuinely need to reach a Salesforce URL without site processing, the guide points at `window.open` for that specific case rather than a rewritten page reference (L22216).

**Detection hint:** `standard__webPage` with a URL containing `/s/`, `/apex/`, or a relative Salesforce site path prefix.

---

## Anti-Pattern 7: Navigating to a component page without the URL-addressable target

**What the LLM generates:**

```javascript
this[NavigationMixin.Navigate]({
    type: 'standard__component',
    attributes: { componentName: 'c__CaseDashboard' }
});
```

…paired with a target component whose `.js-meta.xml` lists only `lightning__AppPage`.

**Why it happens:** `standard__component` reads like it can address any component. It cannot: the target bundle must declare the `lightning__UrlAddressable` target with `<isExposed>true</isExposed>` (`use-navigate-url-addressable`, L10226–10230). LLMs also get the casing wrong — `componentName` uses the `namespace__componentName` format and is case-sensitive, so `c__CaseDashboard` does not resolve a bundle named `caseDashboard` (`reference-page-reference-type`, L22126–22127). And the target is unsupported in Experience Builder sites entirely, because it interferes with custom domain and CDN support (`targets-lightning-url-addressable`, L19403).

**Correct pattern:**

```xml
<!-- caseDashboard.js-meta.xml on the TARGET component -->
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__UrlAddressable</target>
        <target>lightning__AppPage</target>
    </targets>
</LightningComponentBundle>
```

```javascript
this[NavigationMixin.Navigate]({
    type: 'standard__component',
    attributes: { componentName: 'c__caseDashboard' },  // matches the bundle name
    state: { c__view: 'open' }
});
```

**Detection hint:** `standard__component` whose `componentName` does not match a bundle in the source tree that declares `lightning__UrlAddressable`.

---

## Anti-Pattern 8: Expecting a state change to rerender the page

**What the LLM generates:**

```javascript
handleFilterChange(evt) {
    this.filter = evt.detail.value;
    this[NavigationMixin.Navigate]({
        type: 'standard__component',
        attributes: { componentName: 'c__caseDashboard' },
        state: { c__filter: this.filter }
    });
    // ...and assumes the component re-reads the URL on its own
}
```

**Why it happens:** In a single-page-app mental model, pushing a new URL re-runs the route. On the platform it does not: in Lightning Experience and in Experience Builder sites built with Aura or LWR templates, the view is not rerendered when only the URL query string changes. The documented approach is to observe `CurrentPageReference` and compare against the page reference's `state` (`use-navigate-add-params-url`, L10144). LLMs also mutate the current page reference in place, which fails because the PageReference object is frozen — the documented move is `Object.assign({}, pageReference)` on a copy (L10138).

**Correct pattern:**

```javascript
@wire(CurrentPageReference)
setPageRef(pageRef) {
    this.currentPageReference = pageRef;
}

get filter() {
    return this.currentPageReference?.state?.c__filter ?? 'all';
}

handleFilterChange(evt) {
    const next = Object.assign({}, this.currentPageReference, {
        state: Object.assign({}, this.currentPageReference.state, {
            c__filter: evt.detail.value
        })
    });
    // replace: true, so a filter toggle does not add a history entry
    this[NavigationMixin.Navigate](next, true);
}
```

**Detection hint:** a `Navigate` call that only changes `state`, in a component that has no `@wire(CurrentPageReference)`; or direct assignment into `currentPageReference.state`.
