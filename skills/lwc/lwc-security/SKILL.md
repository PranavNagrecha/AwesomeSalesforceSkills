---
name: lwc-security
description: "Use when designing or reviewing Lightning Web Components for DOM safety, Lightning Web Security boundaries, third-party library handling, and secure server-side data access from LWC. Triggers: 'innerHTML in lwc', 'Lightning Web Security', 'document.querySelector', 'light DOM security', 'secure apex class for lwc'. NOT for org-wide sharing architecture or Apex-only security reviews when no LWC surface is involved."
category: lwc
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Security
  - Reliability
  - User Experience
tags:
  - lwc-security
  - lightning-web-security
  - xss
  - light-dom
  - secure-apex
triggers:
  - "is innerhtml safe in lwc"
  - "document queryselector in lightning web components"
  - "lightning web security vs locker"
  - "guest user can call auraenabled apex from lwc"
  - "light dom security risk in lwc"
inputs:
  - "whether the component uses ui api, apex, or third-party libraries"
  - "whether it runs in lightning experience, experience cloud, or mobile"
  - "whether it uses light dom, manual dom, or direct html rendering"
outputs:
  - "security review findings for lwc and supporting apex"
  - "recommended safe rendering and data-access pattern"
  - "remediation plan for dom or server-side exposure risks"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when the security question crosses the LWC boundary between browser behavior and Salesforce data access. The component may look harmless in markup, but the real risk often lives in direct DOM access, unsafe third-party library integration, or Apex controllers that expose more data than the UI should ever receive.

## Before Starting

- Does the component rely on Lightning Data Service, custom Apex, third-party libraries, or all three?
- Is it using `innerHTML`, `lwc:dom="manual"`, light DOM, or direct DOM queries?
- Will the component run in Experience Cloud, guest-user contexts, or any surface where relaxed assumptions become dangerous?

## Core Concepts

### Template Rendering Is Safer Than Manual DOM Work

Standard LWC template bindings are the safest default because the framework handles rendering and escaping for you. Risk rises sharply when the component bypasses declarative rendering through `innerHTML`, manual DOM insertion, or broad DOM queries.

### Lightning Web Security Protects Isolation, Not Business Logic

LWS exists to isolate namespaces and reduce unsafe access to DOM and globals, but it does not replace application security design. Data exposure can still happen if the component calls Apex that ignores sharing, CRUD, or FLS, or if the app deliberately exposes too much information to the client.

### Light DOM Is A Conscious Security Tradeoff

Light DOM can be appropriate for very specific use cases, but it relaxes encapsulation. Top-level light DOM components are not protected by Lightning Locker or LWS in the same way shadow DOM components are, so the placement and hierarchy of light DOM components matter.

### Secure Apex Is Part Of LWC Security

LWC security is not only about the browser. Apex called by the component must still enforce sharing and object/field access intentionally. Salesforce recommends Lightning Data Service for standard record access because it handles sharing, CRUD, and FLS for you; when Apex is required, the controller must enforce security explicitly.

## Common Patterns

### Pattern 1: Unsafe innerHTML vs Safe Template Rendering

**When to use:** Any time the component needs to display dynamic content — especially content from Apex, user input, or API responses.

**Vulnerable code:**

```javascript
// WRONG — XSS risk: unsanitized HTML injected into DOM
renderedCallback() {
    this.template.querySelector('.output').innerHTML =
        `<div>${this.recordDescription}</div>`;
}
```

**Fixed code:**

```html
<!-- CORRECT — template binding handles escaping automatically -->
<template>
    <div class="output">{recordDescription}</div>
</template>
```

If rich HTML rendering is genuinely required (e.g., Knowledge article bodies), use `lightning-formatted-rich-text` which sanitizes HTML:

```html
<lightning-formatted-rich-text value={articleBody}>
</lightning-formatted-rich-text>
```

**Why not innerHTML:** The LWC template compiler escapes content automatically. `innerHTML` bypasses this entirely. Even if the data looks safe today, a future change to the data source could introduce XSS.

---

### Pattern 2: Secure Apex Controller for LWC

**When to use:** The component needs server-side data that LDS cannot provide (aggregations, cross-object logic, external callouts).

**Vulnerable code:**

```java
// WRONG — no sharing enforcement, no FLS check, exposes all fields
public without sharing class AccountController {
    @AuraEnabled
    public static List<Account> getAccounts(String searchTerm) {
        return [SELECT Id, Name, AnnualRevenue, OwnerId
                FROM Account
                WHERE Name LIKE :('%' + searchTerm + '%')];
    }
}
```

Three problems: `without sharing` ignores record-level access, no FLS check on `AnnualRevenue`, and the `searchTerm` is safe here (bind variable) but the pattern invites SOQL injection if ever refactored to dynamic SOQL.

**Fixed code:**

```java
public with sharing class AccountController {
    @AuraEnabled(cacheable=true)
    public static List<Account> getAccounts(String searchTerm) {
        String safeTerm = '%' + String.escapeSingleQuotes(searchTerm) + '%';
        List<Account> results = [
            SELECT Id, Name, AnnualRevenue, OwnerId
            FROM Account
            WHERE Name LIKE :safeTerm
        ];
        // Strip fields the running user cannot see
        SObjectAccessDecision decision = Security.stripInaccessible(
            AccessType.READABLE, results
        );
        return decision.getRecords();
    }
}
```

**Why this matters:** Every `@AuraEnabled` method is callable by any user who has access to the component's namespace — including Experience Cloud guest users if the component is exposed. The Apex class is the last line of defense.

---

### Pattern 3: DOM Access — Component-Scoped Only

**When to use:** The component needs to read or manipulate DOM elements (focus, scroll, measure).

**Vulnerable code:**

```javascript
// WRONG — reaches outside the component's shadow boundary
handleClick() {
    document.querySelector('.slds-page-header').classList.add('hidden');
    document.getElementById('globalSearch').value = '';
}
```

**Fixed code:**

```javascript
// CORRECT — queries only within the component's own shadow DOM
handleClick() {
    const myHeader = this.template.querySelector('.my-header');
    if (myHeader) {
        myHeader.classList.add('hidden');
    }
}
```

**Why not document.querySelector:** LWS blocks cross-namespace DOM access. Even if it works today in a development org, it will break silently in production when LWS is enforced. Components should only touch elements they own.

---

### Pattern 4: Third-Party Library Loading

**When to use:** A business requirement needs a library (Chart.js, PDF.js, a rich text editor) that is not available as a base component.

**Vulnerable code:**

```javascript
// WRONG — dynamic script injection blocked by CSP; no integrity check
connectedCallback() {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
    document.head.appendChild(script);
}
```

**Fixed code:**

```javascript
import { loadScript, loadStyle } from 'lightning/platformResourceLoader';
import CHARTJS from '@salesforce/resourceUrl/ChartJS';

export default class SalesChart extends LightningElement {
    _chartInitialized = false;

    async renderedCallback() {
        if (this._chartInitialized) return;
        this._chartInitialized = true;
        try {
            await loadScript(this, CHARTJS + '/chart.min.js');
            this.initializeChart();
        } catch (error) {
            this.dispatchEvent(new ShowToastEvent({
                title: 'Error', message: 'Chart library failed to load',
                variant: 'error'
            }));
        }
    }
}
```

**Why static resources:** Salesforce Content Security Policy blocks inline script creation and external CDN loading. Static resources are scanned during upload and served from the Salesforce domain.

---

### Pattern 5: Apex with `WITH SECURITY_ENFORCED` vs `Security.stripInaccessible`

**When to use:** Choosing between the two FLS enforcement mechanisms.

```java
// Option A: WITH SECURITY_ENFORCED — throws exception if ANY field is inaccessible
@AuraEnabled(cacheable=true)
public static List<Contact> getContacts(Id accountId) {
    return [SELECT Id, Name, Email, Phone
            FROM Contact
            WHERE AccountId = :accountId
            WITH SECURITY_ENFORCED];
    // If user lacks access to Phone, the ENTIRE query fails with InsufficientAccessException
}

// Option B: stripInaccessible — silently removes inaccessible fields, returns the rest
@AuraEnabled(cacheable=true)
public static List<Contact> getContacts(Id accountId) {
    SObjectAccessDecision decision = Security.stripInaccessible(
        AccessType.READABLE,
        [SELECT Id, Name, Email, Phone
         FROM Contact WHERE AccountId = :accountId]
    );
    return decision.getRecords();
    // If user lacks access to Phone, results are returned without Phone — no exception
}
```

Use `WITH SECURITY_ENFORCED` when all queried fields are required for the feature to work. Use `stripInaccessible` when the component should gracefully degrade (show fewer columns).

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard record access for forms or detail views | LDS or UI API | Platform-managed sharing, CRUD, and FLS — zero custom security code needed |
| Custom Apex for LWC — all fields required | `with sharing` + `WITH SECURITY_ENFORCED` | Fail-fast; no partial data that confuses users |
| Custom Apex for LWC — graceful degradation | `with sharing` + `Security.stripInaccessible` | Returns what the user can see; component hides missing columns |
| Dynamic content display | Template bindings or `lightning-formatted-rich-text` | Auto-escaping; `innerHTML` is never the answer |
| DOM interaction needed | `this.template.querySelector` only | Scoped to shadow DOM; future-proof for LWS enforcement |
| Third-party library required | Static resource + `platformResourceLoader` | CSP-compliant; version-controlled; auditable |
| Light DOM for Experience Cloud theming | Nest inside a shadow DOM parent; never top-level for sensitive data | Limits exposure surface while enabling CSS penetration |

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Inventory the component surface** — list every data source (LDS, Apex, API callout, static data), every DOM manipulation method used, and whether the component runs in Lightning Experience, Experience Cloud, or both. Flag any `innerHTML`, `lwc:dom="manual"`, `document.querySelector`, or `static renderMode = 'light'` usage.
2. **Audit Apex controllers** — for every `@AuraEnabled` method called by this component, verify: (a) the class declares `with sharing`, (b) FLS is enforced via `WITH SECURITY_ENFORCED` or `Security.stripInaccessible`, (c) dynamic SOQL uses bind variables or `String.escapeSingleQuotes`. If the component is exposed to Experience Cloud, verify guest user access assumptions.
3. **Replace unsafe DOM patterns** — convert any `innerHTML` usage to template bindings or `lightning-formatted-rich-text`. Replace `document.querySelector` / `document.getElementById` with `this.template.querySelector`. Ensure third-party libraries load via `platformResourceLoader` from static resources.
4. **Evaluate light DOM usage** — if `static renderMode = 'light'` is set, confirm it is required (Experience Cloud CSS interop is the main valid reason). Ensure the component does not handle PII, auth tokens, or financial data. Nest light DOM components inside shadow DOM parents.
5. **Test in the deployment context** — verify the component in the actual deployment surface (Lightning app page, Experience Cloud site, mobile). Guest user contexts and community pages have different security boundaries than internal Lightning pages.
6. **Run the checker script** — execute `python3 skills/lwc/lwc-security/scripts/check_security.py` against the component source. Review any flagged patterns.
7. **Cross-check against llm-anti-patterns.md** — before marking complete, verify your output does not match any of the 6 documented anti-patterns in this skill's references.

---

## Review Checklist

- [ ] No `innerHTML` assignments exist outside of a justified, sanitized `lwc:dom="manual"` container.
- [ ] No `document.querySelector` or `document.getElementById` — only `this.template.querySelector`.
- [ ] All `@AuraEnabled` Apex classes declare `with sharing`.
- [ ] All `@AuraEnabled` Apex methods enforce FLS via `WITH SECURITY_ENFORCED` or `Security.stripInaccessible`.
- [ ] No dynamic SOQL without bind variables or `String.escapeSingleQuotes`.
- [ ] Third-party libraries loaded from static resources via `platformResourceLoader`, not CDN/script injection.
- [ ] Light DOM usage is documented, justified, nested inside shadow DOM parent, and does not handle sensitive data.
- [ ] Component tested in actual deployment surface (Lightning, Experience Cloud, mobile) — not just dev org preview.
- [ ] Experience Cloud / guest-user access paths reviewed: Apex methods are not exposing data beyond intent.

## Salesforce-Specific Gotchas

1. **`@AuraEnabled` methods are callable by any user with namespace access, including Experience Cloud guest users** — the Apex class is the security boundary, not the component placement. A component removed from a page layout is still callable if the Apex class is accessible. Use `with sharing` and explicit FLS enforcement in every `@AuraEnabled` method.

2. **`WITH SECURITY_ENFORCED` throws an exception if ANY queried field is inaccessible** — this is fail-fast behavior. If your component should gracefully hide columns the user cannot see, use `Security.stripInaccessible` instead. Mixing them up causes either silent data exposure or broken pages.

3. **`document.querySelector()` may work in dev but break under Lightning Web Security** — LWS enforces namespace-scoped DOM access. Code that reaches outside the component boundary may work today in sandboxes with LWS disabled but will fail when LWS is enforced in production. Always use `this.template.querySelector`.

4. **Light DOM components in Experience Cloud are in the page DOM with no shadow boundary** — any JavaScript on the page (other components, analytics scripts, browser extensions) can read and modify the component's markup. Never use light DOM for components that display or collect PII, authentication tokens, or financial data.

5. **`innerHTML` is not blocked by Locker Service or LWS — it just bypasses sanitization** — unlike `eval()` which Locker blocks outright, `innerHTML` works silently. This makes it more dangerous: code reviews can miss it because there is no runtime error. Grep for `innerHTML` in all LWC JavaScript as a mandatory review step.

6. **Static resources are not automatically updated when you update the library** — uploading a new version of Chart.js as a static resource with the same name replaces the file, but browser and CDN caches may serve the old version. Use versioned filenames or cache-busting strategies.

## Output Artifacts

| Artifact | Description |
|---|---|
| LWC security review | Findings on DOM access, light DOM, third-party libraries, and Apex exposure |
| Safe rendering recommendation | Guidance on template-first rendering and secure alternatives to manual DOM work |
| Server-boundary remediation plan | Changes needed in Apex or LDS usage to reduce data-exposure risk |

## Related Skills

- `apex/soql-security` — use when the supporting Apex data-access layer is the main risk.
- `security/injection-prevention` — use when the question expands into SOQL, SOSL, formula, or broader XSS prevention beyond the component surface.
- `lwc/lifecycle-hooks` — use when the issue is primarily lifecycle misuse rather than security.
