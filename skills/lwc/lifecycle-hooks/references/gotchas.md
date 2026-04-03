# Gotchas: LWC Lifecycle Hooks

---

## Event Listeners Without Cleanup Accumulate in Experience Cloud

**What happens:** A FlexCard or LWC on an Experience Cloud site adds a `window.addEventListener('resize', ...)` in `connectedCallback`. In Experience Cloud, users navigate between pages without full page reloads (client-side routing). The component is destroyed (`disconnectedCallback` called) but the listener was never removed. The user navigates back to the page — a new instance adds another listener. After 5 page visits: 5 identical listeners firing on every resize event. Memory grows. The destroyed components' `this` references are held alive by the listeners, preventing garbage collection. On low-memory mobile devices, the browser tab crashes.

**When it bites you:** Any LWC with `window.addEventListener` or `document.addEventListener` deployed in Experience Cloud. Internal org Lightning pages also affected but less severely (full page reloads are more common).

**How to avoid it:**
- Always store the bound handler: `this._handler = this.myMethod.bind(this)`
- Always remove it: `window.removeEventListener('resize', this._handler)` in `disconnectedCallback`
- The bound reference must be the SAME object — calling `.bind(this)` twice creates two different function objects; `removeEventListener` won't find the second one

---

## `renderedCallback` Without a Guard Causes Infinite Re-render

**What happens:** A developer uses `renderedCallback` to set a reactive property (`@track` or any reactive state). Setting the property triggers a re-render. Re-render calls `renderedCallback` again. Another state update. Infinite loop. The component locks up the browser tab. The error in the console is something like "Maximum update depth exceeded" or the tab just hangs.

**The specific pattern that burns people:**
```javascript
renderedCallback() {
    this.componentHeight = this.template.querySelector('.container').offsetHeight;
    // componentHeight is reactive → triggers re-render → renderedCallback fires again → loop
}
```

**How to avoid it:**
```javascript
renderedCallback() {
    if (this._heightMeasured) return;
    this._heightMeasured = true;
    this.componentHeight = this.template.querySelector('.container').offsetHeight;
}
```

---

## `window.location.href` Breaks in Three Deployment Contexts

**What happens:** A developer navigates using `window.location.href = '/lightning/r/Account/' + id + '/view'`. Works perfectly in the developer console. Works in a full desktop browser on Lightning Experience. Breaks in: (1) Salesforce mobile app — the mobile shell has its own navigation stack; direct URL manipulation bypasses it and opens a web view instead of the native record page. (2) Experience Cloud — community URLs have different base paths (`/s/` prefix); hardcoded `/lightning/r/` paths 404. (3) Lightning Out / embedded components — the host page's routing is bypassed.

**How to avoid it:**
- `NavigationMixin.Navigate()` handles all three deployment contexts transparently
- For record pages: `type: 'standard__recordPage'`
- For list views: `type: 'standard__objectPage'`
- For custom pages: `type: 'standard__navItemPage'`
- For external URLs: `type: 'standard__webPage'`

---

## Cross-Component DOM Access Breaks Under Lightning Locker Service

**What happens:** A developer uses `this.template.querySelector('c-child-component').shadowRoot.querySelector('.submit-button')` to click a button in a child component. Works in local development. Breaks in production. Lightning Locker Service / Lightning Web Security enforces strict shadow DOM isolation. `shadowRoot` access across component boundaries throws a permission error.

**When it bites you:** Any time you try to "reach into" another component's DOM from a parent or sibling — even for something simple like setting focus.

**How to avoid it:**
- Parent → Child communication: `@api` property on the child
- Child → Parent communication: `CustomEvent` dispatch from child
- Programmatic actions on child (focus, click): expose an `@api` method on the child: `@api focus() { this.template.querySelector('input').focus(); }`
- Sibling → Sibling: Lightning Message Service (LMS) or shared parent state

---

## Inline `<script>` Tags Are Silently Blocked by CSP

**What happens:** A developer adds `<script src="https://cdn.example.com/library.min.js"></script>` to an LWC template, following standard HTML practice. The component renders but the library doesn't work. No visible error. The browser console shows: `Refused to load the script 'https://cdn...' because it violates the following Content Security Policy directive...`. The developer spends an hour debugging the library before checking CSP.

**How to avoid it:**
1. Upload the library to Salesforce Static Resources
2. Import `loadScript` from `lightning/platformResourceLoader`
3. Load it in `connectedCallback` with `.then()` / `.catch()`

This is one of the most commonly missed LWC setup steps for developers coming from traditional web development.
