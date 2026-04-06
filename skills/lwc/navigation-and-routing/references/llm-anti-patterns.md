# LLM Anti-Patterns — Navigation and Routing

Common mistakes AI coding assistants make when generating or advising on LWC navigation with NavigationMixin.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using window.location instead of NavigationMixin

**What the LLM generates:**

```javascript
handleViewRecord() {
    window.location.href = `/lightning/r/Account/${this.recordId}/view`;
}
```

**Why it happens:** `window.location` is the most common JavaScript navigation pattern. LLMs default to it because it appears in generic web training data. In Salesforce, it causes a full page reload, breaks the SPA shell, and fails in mobile and Experience Cloud.

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

**Detection hint:** `window.location`, `window.open`, or hardcoded `/lightning/` URLs in LWC JavaScript.

---

## Anti-Pattern 2: Forgetting to extend NavigationMixin before using Navigate

**What the LLM generates:**

```javascript
import { LightningElement } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';

export default class MyComponent extends LightningElement {
    handleNav() {
        this[NavigationMixin.Navigate]({ /* ... */ });
        // TypeError — Navigate symbol does not exist on the class
    }
}
```

**Why it happens:** LLMs import `NavigationMixin` but forget to apply it in the `extends` clause. The import alone does not add the navigation methods.

**Correct pattern:**

```javascript
export default class MyComponent extends NavigationMixin(LightningElement) {
    handleNav() {
        this[NavigationMixin.Navigate]({
            type: 'standard__recordPage',
            attributes: { recordId: this.recordId, actionName: 'view' }
        });
    }
}
```

**Detection hint:** `NavigationMixin.Navigate` used in a class that extends `LightningElement` without wrapping it in `NavigationMixin()`.

---

## Anti-Pattern 3: Using the wrong PageReference type

**What the LLM generates:**

```javascript
this[NavigationMixin.Navigate]({
    type: 'standard__recordPage',
    attributes: {
        url: '/lightning/o/Account/list' // URL does not belong in a record page reference
    }
});
```

**Why it happens:** LLMs confuse PageReference types. `standard__recordPage` requires `recordId`, `objectApiName`, and `actionName` attributes — not a URL. For object list views, the type is `standard__objectPage`.

**Correct pattern:**

```javascript
// Navigate to record
this[NavigationMixin.Navigate]({
    type: 'standard__recordPage',
    attributes: { recordId: this.recordId, objectApiName: 'Account', actionName: 'view' }
});

// Navigate to object list view
this[NavigationMixin.Navigate]({
    type: 'standard__objectPage',
    attributes: { objectApiName: 'Account', actionName: 'list' },
    state: { filterName: 'Recent' }
});
```

**Detection hint:** PageReference with `type: 'standard__recordPage'` but missing `recordId`, or `type: 'standard__objectPage'` with a `recordId`.

---

## Anti-Pattern 4: Putting custom state keys that are not prefixed with `c__`

**What the LLM generates:**

```javascript
this[NavigationMixin.Navigate]({
    type: 'standard__component',
    attributes: { componentName: 'c__MyPage' },
    state: {
        recordId: this.recordId,  // Not URL-safe — platform strips it
        mode: 'edit'
    }
});
```

**Why it happens:** LLMs use plain key names. Salesforce requires custom state parameters to be prefixed with the namespace, typically `c__`, to distinguish them from platform-reserved keys.

**Correct pattern:**

```javascript
this[NavigationMixin.Navigate]({
    type: 'standard__component',
    attributes: { componentName: 'c__MyPage' },
    state: {
        c__recordId: this.recordId,
        c__mode: 'edit'
    }
});
```

**Detection hint:** `state:` object with keys that do not start with a namespace prefix (like `c__`) on component page references.

---

## Anti-Pattern 5: Not using GenerateUrl when an href is needed instead of navigation

**What the LLM generates:**

```html
<a href="javascript:void(0)" onclick={handleNav}>View Record</a>
```

```javascript
handleNav() {
    this[NavigationMixin.Navigate]({ /* page reference */ });
}
```

**Why it happens:** LLMs use `javascript:void(0)` as the href and handle navigation in the click handler. This breaks right-click "Open in new tab," accessibility, and SEO in Experience Cloud.

**Correct pattern:**

```javascript
connectedCallback() {
    this[NavigationMixin.GenerateUrl]({
        type: 'standard__recordPage',
        attributes: { recordId: this.recordId, actionName: 'view' }
    }).then(url => { this.recordUrl = url; });
}
```

```html
<a href={recordUrl}>View Record</a>
```

**Detection hint:** `<a` tag with `href="javascript:void(0)"` or `href="#"` combined with an `onclick` that calls `NavigationMixin.Navigate`.

---

## Anti-Pattern 6: Hardcoding Experience Cloud URL paths

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

**Why it happens:** LLMs hardcode site paths because they do not know the site prefix at generation time. Hardcoded paths break when the site URL or community name changes.

**Correct pattern:**

```javascript
// Use standard__recordPage — it works in both LEX and Experience Cloud
this[NavigationMixin.Navigate]({
    type: 'standard__recordPage',
    attributes: {
        recordId: this.recordId,
        objectApiName: 'Account',
        actionName: 'view'
    }
});
```

Use `standard__webPage` only for truly external URLs, not for internal Salesforce navigation.

**Detection hint:** `standard__webPage` with a URL containing `/s/` or a Salesforce site path prefix.
