# Well-Architected Mapping: LWC Lifecycle Hooks

---

## Pillars Addressed

### Reliability
Memory leaks from uncleaned event listeners cause component failures on long-running sessions and in Experience Cloud. Proper cleanup prevents the component from behaving unexpectedly after navigation.

- WAF check: All `addEventListener` calls have matching `removeEventListener` in `disconnectedCallback`?
- WAF check: All wire adapters handle both `data` and `error` branches?
- WAF check: Every `connectedCallback` subscription is behind an existence guard, because the hook can fire more than once?
- WAF check: No lifecycle hook is declared `async`, so teardown completes before the element detaches?

### Security
Lightning Locker Service / LWS enforces shadow DOM isolation. External scripts loaded inline violate CSP. `@api` property immutability enforces one-way data flow and prevents parent data corruption.

- WAF check: No inline `<script>` tags (CSP violation)?
- WAF check: No cross-component DOM access (LWS violation)?
- WAF check: `@api` properties cloned before modification?

### Performance
`renderedCallback` without a guard runs on every re-render — potentially dozens of times per user interaction. Guards prevent redundant DOM work and third-party library re-initialization.

- WAF check: `renderedCallback` has guard for one-time operations?
- WAF check: Wire service used for reads (more efficient than imperative Apex for reactive data)?
- WAF check: `renderedCallback` writes to no wire-configuration property and no `@api` property?

### User Experience
`NavigationMixin` works across all Salesforce deployment contexts. `ShowToastEvent` is the expected feedback mechanism in Lightning. Proper error state display prevents blank components that confuse users.

- WAF check: Navigation uses `NavigationMixin`, not `window.location`?
- WAF check: User feedback uses `ShowToastEvent`, not `alert()`?
- WAF check: All async states (loading, data, error) have visible UI representation?
- WAF check: An `errorCallback` boundary exists at the level where a descendant failure should stop, with a fallback template that does not include the failed child?

### Operational Excellence
Lifecycle defects are invisible in a demo and expensive in a console session. They have to be caught by a check that runs without an org.

- WAF check: `scripts/check_lwc_lifecycle.py --manifest-dir <lwc dir>` returns zero ERRORs, and runs with `--strict` in CI?
- WAF check: A Jest test removes the element with `document.body.removeChild` and asserts the teardown ran?

## Official Sources Used

- Lightning Web Components Developer Guide — [connectedCallback() and disconnectedCallback()](https://developer.salesforce.com/docs/platform/lwc/guide/create-lifecycle-hooks-dom.html) (both hooks flow parent → child; `connectedCallback` can fire more than once; both are synchronous and a returned promise is not awaited — the Reliability checks and the `async`-hook gotcha)
- Lightning Web Components Developer Guide — [renderedCallback()](https://developer.salesforce.com/docs/platform/lwc/guide/create-lifecycle-hooks-rendered.html) (flows child → parent; runs after every render; use a `hasRendered` boolean for one-time work; do not update a wire config object or a public property here — the Performance checks and the guard pattern)
- Lightning Web Components Developer Guide — [constructor()](https://developer.salesforce.com/docs/platform/lwc/guide/create-lifecycle-hooks-created.html) (`super()` must be the first statement with no parameters; children and public properties do not exist yet — checker rules L1 and L2)
- Lightning Web Components Developer Guide — [errorCallback()](https://developer.salesforce.com/docs/platform/lwc/guide/create-lifecycle-hooks-error.html) (captures descendant errors in lifecycle hooks and template-declared handlers, not programmatically attached ones; the throwing child is unmounted — the UX boundary check)
- Lightning Web Components Developer Guide — [render()](https://developer.salesforce.com/docs/platform/lwc/guide/create-lifecycle-hooks-render.html) and [Render Multiple Templates](https://developer.salesforce.com/docs/platform/lwc/guide/create-render.html) (not technically a hook; must return a template reference; extra templates resolve CSS only from a matching filename; `lwc:if` is preferred over a fork)
- Lightning Web Components Developer Guide — [Understand the Wire Service](https://developer.salesforce.com/docs/platform/lwc/guide/data-wire-service-about.html) (the documented order constructor → connectedCallback → render → renderedCallback; the wire property is seeded before any other lifecycle event; LDS emits are not tied to the component lifecycle)
- Lightning Web Components Developer Guide — [Handle Events](https://developer.salesforce.com/docs/platform/lwc/guide/events-handling.html) (the framework cleans up listeners it owns from the template; listeners added to `window` or `document` are the developer's responsibility — the Reliability cleanup check)
- Lightning Web Components Developer Guide — [Subscribe and Unsubscribe from a Message Channel](https://developer.salesforce.com/docs/platform/lwc/guide/use-message-channel-subscribe.html) (the `if (!this.subscription)` guard in `connectedCallback` and `unsubscribe` + reset in `disconnectedCallback` — the subscription pattern in `references/code-examples.md`)
- Lightning Web Components Developer Guide — [Write Jest Tests](https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-jest-create-tests.html) (`appendChild` fires `connectedCallback` and `renderedCallback`; `document.body.removeChild` in `afterEach`; `await Promise.resolve()` for asynchronous DOM updates; `element.shadowRoot` is a test-only API — the Operational Excellence checks)
- Lightning Web Components Developer Guide — [Use Third-Party JavaScript Libraries](https://developer.salesforce.com/docs/platform/lwc/guide/js-third-party-library.html) (static resources are a CSP requirement; `loadScript`/`loadStyle` are invoked in `renderedCallback` on the first render — the Security check on inline scripts)
- Lightning Web Components Developer Guide — [Data Flow](https://developer.salesforce.com/docs/platform/lwc/guide/create-components-data-flow.html) (values passed to a component are read-only; a nested write throws `Invalid mutation`; make a shallow copy — the Security check on `@api` cloning)
- Lightning Web Components Developer Guide — [XML Configuration File Elements](https://developer.salesforce.com/docs/platform/lwc/guide/reference-configuration-tags.html) and [API Versioning](https://developer.salesforce.com/docs/platform/lwc/guide/get-started-api-versioning.html) (`isExposed` gates builder visibility and requires a `target`; every component must carry an `apiVersion` from Spring '25 — the `.js-meta.xml` in `references/code-examples.md`)
- Salesforce Well-Architected Overview — UX, performance, and reliability framing for LWC design
