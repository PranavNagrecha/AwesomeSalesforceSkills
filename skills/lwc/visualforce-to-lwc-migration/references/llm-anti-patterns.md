# LLM Anti-Patterns — Visualforce to LWC Migration

Common mistakes AI coding assistants make when generating or advising on Visualforce-to-LWC migrations. These patterns help the consuming agent self-check its output before shipping.

## Anti-Pattern 1: Translating Viewstate to a "Hidden Reactive Property"

**What the LLM generates:** A `@track` private property on the LWC named `_viewState` that holds a JSON blob meant to mirror the Visualforce viewstate. Updates to UI fields write into `_viewState`, and on save the whole blob is sent to Apex.

**Why it happens:** The model recognizes "viewstate carries data across postbacks" and tries to recreate the abstraction.

**Correct pattern:** Eliminate viewstate as an abstraction. Each user input becomes its own reactive property; on save, build an explicit DTO from the properties. If the workflow is a multi-step wizard, persist intermediate state to a draft database record (preferred) or pass it forward via URL or LMS — not as a synthetic blob.

## Anti-Pattern 2: Returning `PageReference` from `@AuraEnabled` Apex

**What the LLM generates:**

```apex
@AuraEnabled
public static PageReference saveAndRedirect(Case c) {
    update c;
    return new PageReference('/' + c.Id);
}
```

**Why it happens:** The model sees "VF returned PageReference; the new method should also return navigation intent" and copies the pattern.

**Correct pattern:** Apex returns data only. Navigation is a client concern.

```apex
@AuraEnabled
public static Id save(Case c) {
    update c;
    return c.Id;
}
```

LWC then calls `this[NavigationMixin.Navigate]({ type: 'standard__recordPage', attributes: { recordId, actionName: 'view' }})` after `await save(...)` resolves.

## Anti-Pattern 3: Using `lwc:dom="manual"` and `innerHTML` to Preserve `escape="false"`

**What the LLM generates:** A template with `<div lwc:dom="manual" class="rich-text"></div>` and a `renderedCallback` that sets `this.template.querySelector('.rich-text').innerHTML = this.userText` to preserve the behavior of `<apex:outputText escape="false">`.

**Why it happens:** The model identifies the escaping difference and finds the LWC API for unsanitized DOM injection.

**Correct pattern:** Use `<lightning-formatted-text>` for text-with-line-breaks, `<lightning-formatted-rich-text>` for trusted-source HTML, or sanitize explicitly with an allow-list before rendering. Setting `innerHTML` from user-controlled content is a vulnerability — and the migration is the moment to close it, not preserve it.

## Anti-Pattern 4: Rebuilding `<apex:repeat>` with Manual `for` Loops in JS

**What the LLM generates:** JavaScript that iterates over a list, builds HTML strings, and assigns them to a container's `innerHTML` — recreating the imperative DOM manipulation pattern of older JS frameworks.

**Why it happens:** The model has seen many "render a list" examples that use string-templated HTML.

**Correct pattern:** Use the `for:each` template directive with stable `key` attributes:

```html
<template for:each={items} for:item="item">
    <li key={item.id}>{item.name}</li>
</template>
```

Or, for tabular data, `<lightning-datatable>` — which provides sorting, inline edit, and pagination for free.

## Anti-Pattern 5: Adding `cacheable=true` to the Save Method to "Match the Read"

**What the LLM generates:** A new `@AuraEnabled(cacheable=true)` save method, parallel to the cacheable getter, on the assumption that all wired-style methods need caching.

**Why it happens:** The model sees the read method has `cacheable=true` and applies the modifier symmetrically.

**Correct pattern:** `cacheable=true` requires no DML, no callouts, no side effects. Save methods MUST be `cacheable=false` (or omit the cacheable parameter entirely). The runtime throws `cacheable=true methods cannot perform DML` on the first call. Read methods are wired; write methods are imperative — they are not parallel.

## Anti-Pattern 6: Migrating `renderAs="pdf"` Pages to LWC + a JS PDF Library

**What the LLM generates:** An LWC that imports `jsPDF` from a static resource and rebuilds the invoice layout in JavaScript to "fully migrate" the PDF page.

**Why it happens:** The model treats the migration as a goal of "no remaining VF" and seeks a JS equivalent for PDF rendering.

**Correct pattern:** Keep the VF page. Server-side `Page.X.getContentAsPDF()` is the right primitive. Client-side PDF libraries lose Salesforce's render fidelity, inflate bundles, fail under Lightning Web Security if they touch `eval` / cross-origin iframes, and re-implement features (font embedding, page-break control) the platform already provides. The migration goal is "modernize the user-facing surfaces", not "delete every `.page` file".

## Anti-Pattern 7: Reusing the VF Controller as the LWC's `@AuraEnabled` Class

**What the LLM generates:** Adds `@AuraEnabled` annotations to the existing VF controller's `get` properties and action methods, leaving the controller's instance state and constructor in place.

**Why it happens:** The model wants to minimize code changes and views the controller as the natural home for the new methods.

**Correct pattern:** The VF controller is an instance class (per-page-session lifetime); `@AuraEnabled` methods MUST be `static`. Construct a new service class (`AccountSummaryService`, not `AccountSummaryController`) with stateless static methods. Extract the SOQL/business logic; discard the controller's instance fields. Annotate `with sharing` and add explicit FLS checks (the VF controller may have inherited `with sharing` from the page and gained automatic FLS — your service class must declare both explicitly).

## Anti-Pattern 8: Skipping the `c__` Prefix on App Builder Page URL Parameters

**What the LLM generates:** Reads `pageRef.state.id` and assumes the value will arrive when an external caller hits `/lightning/n/MyTab?id=001abc`.

**Why it happens:** Standard URL parameter convention; the `c__` prefix requirement is a Salesforce-specific quirk.

**Correct pattern:** On App Builder pages, the LWC reads `pageRef.state.c__id`. Document this in the migration log; either update external callers to use `?c__id=...` or accept both with `pageRef.state.c__id || pageRef.state.id` for a transition window. Quick Action and community page surfaces have different rules — verify per surface.
