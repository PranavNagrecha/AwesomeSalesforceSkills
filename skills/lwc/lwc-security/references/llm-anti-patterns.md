# LLM Anti-Patterns — LWC Security

Common mistakes AI coding assistants make when generating or advising on LWC security.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using innerHTML to render dynamic content

**What the LLM generates:**

```javascript
renderedCallback() {
    this.template.querySelector('.container').innerHTML =
        `<p>${this.userProvidedHtml}</p>`;
}
```

**Why it happens:** LLMs use `innerHTML` because it is the simplest way to render dynamic HTML in vanilla JS. In LWC, this bypasses the template compiler's sanitization and opens XSS attack surface.

**Correct pattern:**

Use `lwc:dom="manual"` for controlled DOM insertion, and sanitize any external content:

```html
<div lwc:dom="manual" class="container"></div>
```

```javascript
renderedCallback() {
    const el = this.template.querySelector('.container');
    const textNode = document.createTextNode(this.userProvidedText);
    el.appendChild(textNode);
}
```

For rich content, use `lightning-formatted-rich-text` which sanitizes HTML.

**Detection hint:** `innerHTML` assignment anywhere in LWC JavaScript files.

---

## Anti-Pattern 2: Using document.querySelector to reach outside the shadow DOM

**What the LLM generates:**

```javascript
handleClick() {
    const header = document.querySelector('.global-header');
    header.style.display = 'none';
}
```

**Why it happens:** LLMs use `document.querySelector` from general web development. In LWC, components should not reach outside their own shadow boundary — this breaks encapsulation and can be blocked by Lightning Web Security.

**Correct pattern:**

```javascript
// Only query within the component's own shadow DOM
const myElement = this.template.querySelector('.my-element');
```

If cross-component communication is needed, use events, LMS, or `@api` methods.

**Detection hint:** `document.querySelector` or `document.getElementById` in LWC JavaScript files.

---

## Anti-Pattern 3: Exposing Apex methods without proper security checks

**What the LLM generates:**

```java
@AuraEnabled
public static List<Account> getAllAccounts() {
    return [SELECT Id, Name, Revenue__c FROM Account];
}
```

**Why it happens:** LLMs generate Apex methods that query data without considering FLS, sharing rules, or CRUD checks. Any `@AuraEnabled` method is callable from LWC regardless of page context.

**Correct pattern:**

```java
@AuraEnabled(cacheable=true)
public static List<Account> getAllAccounts() {
    // Class should declare 'with sharing'
    // Use Security.stripInaccessible for FLS enforcement
    SObjectAccessDecision decision = Security.stripInaccessible(
        AccessType.READABLE,
        [SELECT Id, Name, Revenue__c FROM Account]
    );
    return decision.getRecords();
}
```

Ensure the class uses `with sharing` and enforces FLS.

**Detection hint:** `@AuraEnabled` on a method in a class declared `without sharing`, or SOQL queries without `Security.stripInaccessible` or `WITH SECURITY_ENFORCED`.

---

## Anti-Pattern 4: Using light DOM without understanding the security implications

**What the LLM generates:**

```javascript
static renderMode = 'light';
```

```html
<template>
    <div class="my-component">
        <!-- Content now in the parent's DOM — no shadow boundary -->
    </div>
</template>
```

**Why it happens:** LLMs suggest light DOM for styling flexibility. But light DOM components lose shadow DOM encapsulation — parent components and global scripts can query and modify their internals.

**Correct pattern:**

Only use light DOM when required (e.g., Experience Cloud themes, specific CSS sharing needs). Never for components that handle sensitive data:

```javascript
// Default shadow DOM — keep unless there is a documented reason for light DOM
// static renderMode = 'light';  // Do not set
```

**Detection hint:** `static renderMode = 'light'` in components that display or handle PII, financial data, or authentication-related content.

---

## Anti-Pattern 5: Hardcoding record IDs or Salesforce instance URLs

**What the LLM generates:**

```javascript
const ADMIN_PROFILE_ID = '00e000000000001';
const ENDPOINT = 'https://mycompany.my.salesforce.com/services/data/v59.0/';
```

**Why it happens:** LLMs hardcode IDs and URLs from training examples. These break across orgs and sandboxes and expose org-specific information in source code.

**Correct pattern:**

```javascript
// Use custom labels, custom metadata, or runtime APIs
import ADMIN_PROFILE_LABEL from '@salesforce/label/c.Admin_Profile_Name';

// For API endpoints, use relative paths or platform APIs
import { getRecord } from 'lightning/uiRecordApi';
```

**Detection hint:** 15 or 18-character Salesforce ID literals or `*.my.salesforce.com` URLs in JavaScript source.

---

## Anti-Pattern 6: Loading third-party scripts without CSP consideration

**What the LLM generates:**

```javascript
connectedCallback() {
    const script = document.createElement('script');
    script.src = 'https://cdn.example.com/library.js';
    document.head.appendChild(script);
}
```

**Why it happens:** LLMs use the standard web pattern for loading scripts. In Salesforce, Content Security Policy blocks inline script creation, and Lightning Web Security further restricts dynamic script loading.

**Correct pattern:**

```javascript
import { loadScript } from 'lightning/platformResourceLoader';
import MY_LIB from '@salesforce/resourceUrl/myLibrary';

async renderedCallback() {
    if (this._libLoaded) return;
    try {
        await loadScript(this, MY_LIB + '/myLibrary.min.js');
        this._libLoaded = true;
    } catch (error) {
        this.error = 'Failed to load library';
    }
}
```

Upload the library as a static resource and load it through `platformResourceLoader`.

**Detection hint:** `document.createElement('script')` or direct CDN URLs in LWC JavaScript.
