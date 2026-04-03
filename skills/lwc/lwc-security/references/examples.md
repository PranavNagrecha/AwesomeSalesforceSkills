# Examples — LWC Security

## Example 1: Prefer LDS Over Custom Apex For Record Reads

**Context:** A component displays Account fields and edit controls on a record page.

**Problem:** The first implementation uses custom Apex even though no special server logic is required.

**Solution:**

```js
import { getRecord } from 'lightning/uiRecordApi';
import NAME_FIELD from '@salesforce/schema/Account.Name';

@wire(getRecord, { recordId: '$recordId', fields: [NAME_FIELD] })
account;
```

**Why it works:** The component relies on platform-managed sharing, CRUD, and FLS behavior instead of expanding the attack surface with unnecessary Apex.

---

## Example 2: Safe DOM Access Through Component-Owned Elements

**Context:** A component needs to focus an input after rendering.

**Problem:** The original code uses `document.querySelector()` and can reach outside the component boundary.

**Solution:**

```js
renderedCallback() {
    const input = this.template.querySelector('lightning-input');
    if (input) {
        input.focus();
    }
}
```

**Why it works:** The component accesses only elements it owns and stays aligned with LWC DOM containment rules.

---

## Anti-Pattern: Rendering Untrusted HTML With `innerHTML`

**What practitioners do:** They take server-provided text and push it into the DOM with `innerHTML` because it looks easier than using template bindings.

**What goes wrong:** The component bypasses the safer declarative rendering path and increases XSS and DOM-manipulation risk.

**Correct approach:** Prefer template bindings, or redesign the content model so the component does not need to inject raw HTML.
